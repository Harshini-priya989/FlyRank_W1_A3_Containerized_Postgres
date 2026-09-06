from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[0]
DATA_PATH = REPO_ROOT / "scraper" / "output" / "books.json"
DB_PATH = ROOT / "data" / "book_insights.db"
REPORT_DIR = ROOT / "reports"

app = FastAPI(title="Book Insights API", version="1.0")
tokens: dict[str, str] = {}
cache: dict[str, tuple[float, Any]] = {}
CACHE_TTL_SECONDS = 60


class LoginRequest(BaseModel):
    email: str
    password: str


class TagRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS books (
                product_url TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                price_gbp REAL NOT NULL,
                availability_text TEXT NOT NULL,
                rating INTEGER NOT NULL,
                description TEXT,
                source_page TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                detail TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT
            );
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cost_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                units INTEGER NOT NULL,
                estimated_cost_usd REAL NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        row = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
        if row["count"] == 0:
            salt = secrets.token_hex(12)
            conn.execute(
                "INSERT INTO users (email, password_hash, salt, created_at) VALUES (?, ?, ?, ?)",
                ("demo@example.com", hash_password("password123", salt), salt, now()),
            )


@app.on_event("startup")
def startup() -> None:
    init_db()
    if DATA_PATH.exists():
        import_books()


def require_user(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"error": "Access token required"})
    token = authorization.removeprefix("Bearer ").strip()
    email = tokens.get(token)
    if not email:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})
    return email


def cached(key: str, factory):
    item = cache.get(key)
    if item and time.time() - item[0] < CACHE_TTL_SECONDS:
        return {"cache": "hit", "data": item[1]}
    data = factory()
    cache[key] = (time.time(), data)
    return {"cache": "miss", "data": data}


def classify_book(title: str, description: str | None) -> dict[str, str]:
    text = f"{title} {description or ''}".lower()
    rules = [
        ("business", ["business", "startup", "job", "prosperity", "money"]),
        ("history", ["history", "historical", "war", "country"]),
        ("fiction", ["novel", "story", "fiction", "paris"]),
        ("poetry", ["poem", "poetry", "sonnet"]),
        ("self-help", ["freedom", "alive", "soul", "commitment"]),
    ]
    category = "general"
    for name, words in rules:
        if any(word in text for word in words):
            category = name
            break
    sentence = (description or title).split(".")[0].strip()
    summary = sentence[:180] if sentence else f"A book titled {title}."
    return {"category": category, "summary": summary}


def import_books() -> int:
    init_db()
    books = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO jobs (type, status, detail, started_at) VALUES (?, ?, ?, ?)",
            ("import_books", "running", str(DATA_PATH), now()),
        )
        job_id = cur.lastrowid
        count = 0
        for book in books:
            tags = classify_book(book["title"], book.get("description"))
            conn.execute(
                """
                INSERT OR REPLACE INTO books (
                    product_url, title, price_gbp, availability_text, rating,
                    description, source_page, fetched_at, category, summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    book["product_url"],
                    book["title"],
                    book["price_gbp"],
                    book["availability_text"],
                    book["rating"],
                    book.get("description"),
                    book["source_page"],
                    book["fetched_at"],
                    tags["category"],
                    tags["summary"],
                ),
            )
            count += 1
        conn.execute(
            "UPDATE jobs SET status = ?, detail = ?, finished_at = ? WHERE id = ?",
            ("complete", f"imported={count}", now(), job_id),
        )
        conn.execute(
            "INSERT INTO cost_log (endpoint, units, estimated_cost_usd, created_at) VALUES (?, ?, ?, ?)",
            ("import_books_classification", count, 0.0, now()),
        )
    cache.clear()
    return count


def book_rows(where: str = "", params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT product_url, title, price_gbp, availability_text, rating,
                   description, source_page, fetched_at, category, summary
            FROM books {where}
            ORDER BY title
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/")
def root():
    return {
        "name": "Book Insights API",
        "problem": "Make scraped book data searchable, categorized, and reportable in minutes.",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) AS count FROM books").fetchone()["count"]
    return {"status": "ok", "books": count}


@app.post("/auth/login")
def login(payload: LoginRequest):
    with connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (payload.email,)).fetchone()
    if not user or hash_password(payload.password, user["salt"]) != user["password_hash"]:
        raise HTTPException(status_code=401, detail={"error": "Invalid login credentials"})
    token = secrets.token_urlsafe(32)
    tokens[token] = payload.email
    return {"access_token": token, "token_type": "bearer"}


@app.get("/books")
def list_books(limit: int = 20, offset: int = 0):
    if limit < 1 or limit > 60 or offset < 0:
        raise HTTPException(status_code=400, detail={"error": "Invalid pagination"})
    return cached(f"books:{limit}:{offset}", lambda: book_rows("LIMIT ? OFFSET ?", (limit, offset)))


@app.get("/books/search")
def search_books(q: str, max_price: float | None = None):
    if not q.strip():
        raise HTTPException(status_code=400, detail={"error": "Search query required"})

    def factory():
        params: list[Any] = [f"%{q.strip()}%", f"%{q.strip()}%"]
        where = "WHERE (title LIKE ? OR description LIKE ?)"
        if max_price is not None:
            where += " AND price_gbp <= ?"
            params.append(max_price)
        return book_rows(where, tuple(params))

    return cached(f"search:{q}:{max_price}", factory)


@app.get("/books/recommendations")
def recommendations(category: str | None = None, max_price: float = 25):
    where = "WHERE price_gbp <= ?"
    params: list[Any] = [max_price]
    if category:
        where += " AND category = ?"
        params.append(category)
    return cached(f"recommend:{category}:{max_price}", lambda: book_rows(where + " LIMIT 10", tuple(params)))


@app.post("/ai/tag")
def tag_preview(payload: TagRequest, user: str = Depends(require_user)):
    result = classify_book(payload.title, payload.description)
    with connect() as conn:
        conn.execute(
            "INSERT INTO cost_log (endpoint, units, estimated_cost_usd, created_at) VALUES (?, ?, ?, ?)",
            ("/ai/tag", len((payload.description or "") + payload.title), 0.0, now()),
        )
    return {"input": payload.model_dump(), "result": result, "reviewed_by": user}


@app.post("/jobs/import-books", status_code=status.HTTP_202_ACCEPTED)
def queue_import(background_tasks: BackgroundTasks, user: str = Depends(require_user)):
    background_tasks.add_task(import_books)
    return {"status": "queued", "requested_by": user}


@app.get("/jobs")
def list_jobs(user: str = Depends(require_user)):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 20").fetchall()
    return [dict(row) for row in rows]


@app.post("/reports/books")
def create_report(user: str = Depends(require_user)):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    books = book_rows()
    filename = f"book-insights-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"
    path = REPORT_DIR / filename

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((54, 72), "Book Insights Report", fontsize=22, fontname="helv")
    page.insert_text((54, 104), f"Generated: {now()}", fontsize=10, fontname="helv")
    page.insert_text((54, 126), f"Generated by: {user}", fontsize=10, fontname="helv")
    page.insert_text((54, 154), f"Total books: {len(books)}", fontsize=12, fontname="helv")
    if books:
        prices = [row["price_gbp"] for row in books]
        page.insert_text((54, 176), f"Price range: GBP {min(prices):.2f} - GBP {max(prices):.2f}", fontsize=12, fontname="helv")
    y = 214
    for row in books[:18]:
        text = f"- {row['title']} | GBP {row['price_gbp']:.2f} | {row['category']}"
        page.insert_text((54, y), text[:95], fontsize=9, fontname="helv")
        y += 17
    doc.save(path)
    doc.close()

    with connect() as conn:
        conn.execute(
            "INSERT INTO reports (path, created_at) VALUES (?, ?)",
            (str(path.relative_to(ROOT)), now()),
        )
    return {"report": str(path.relative_to(ROOT)), "books": len(books)}


@app.get("/reports/latest")
def latest_report(user: str = Depends(require_user)):
    with connect() as conn:
        row = conn.execute("SELECT path FROM reports ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        raise HTTPException(status_code=404, detail={"error": "No report has been generated"})
    path = ROOT / row["path"]
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@app.get("/usage/cost-log")
def cost_log(user: str = Depends(require_user)):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM cost_log ORDER BY id DESC LIMIT 30").fetchall()
    return [dict(row) for row in rows]
