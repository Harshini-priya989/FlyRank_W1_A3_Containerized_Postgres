from __future__ import annotations

import subprocess
from datetime import date
import os
from pathlib import Path
from textwrap import wrap

import fitz


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "final-submission.pdf"


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace").strip()


def command_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"Unavailable: {exc}"


def project_status() -> str:
    raw = command_output(["git", "status", "--short"])
    ignored = {"?? docs/GITHUB_SUBMISSION.md", "?? docs/final-submission.pdf", "?? scripts/"}
    lines = [line for line in raw.splitlines() if line not in ignored]
    return "\n".join(lines) if lines else "Clean worktree, excluding generated submission PDF assets"


def add_wrapped(page: fitz.Page, text: str, x: float, y: float, width_chars: int, size: int = 10) -> float:
    for paragraph in text.splitlines() or [""]:
        if not paragraph:
            y += size * 0.9
            continue
        for line in wrap(paragraph, width=width_chars, replace_whitespace=False):
            page.insert_text((x, y), line, fontsize=size, fontname="helv", color=(0.10, 0.12, 0.16))
            y += size * 1.35
    return y


class PdfBuilder:
    def __init__(self) -> None:
        self.doc = fitz.open()
        self.page = None
        self.y = 0.0
        self.margin = 54.0

    def new_page(self, title: str | None = None) -> None:
        self.page = self.doc.new_page(width=595, height=842)
        self.y = self.margin
        if title:
            self.heading(title)

    def ensure(self, needed: float = 72) -> None:
        if self.page is None or self.y + needed > 790:
            self.new_page()

    def heading(self, text: str) -> None:
        self.ensure(42)
        self.page.insert_text((self.margin, self.y), text, fontsize=18, fontname="helv", color=(0.05, 0.17, 0.30))
        self.y += 30

    def subheading(self, text: str) -> None:
        self.ensure(32)
        self.page.insert_text((self.margin, self.y), text, fontsize=12, fontname="helv", color=(0.05, 0.17, 0.30))
        self.y += 19

    def para(self, text: str, size: int = 10, chars: int = 88) -> None:
        self.ensure(28)
        self.y = add_wrapped(self.page, text, self.margin, self.y, chars, size)
        self.y += 8

    def bullet(self, text: str) -> None:
        self.ensure(24)
        self.page.insert_text((self.margin, self.y), "-", fontsize=10, fontname="helv", color=(0.10, 0.12, 0.16))
        self.y = add_wrapped(self.page, text, self.margin + 14, self.y, 84, 10)
        self.y += 3

    def code(self, text: str, chars: int = 92) -> None:
        self.ensure(42)
        for line in text.splitlines():
            for part in wrap(line, width=chars, replace_whitespace=False) or [""]:
                self.ensure(16)
                self.page.insert_text((self.margin, self.y), part, fontsize=8.5, fontname="cour", color=(0.02, 0.02, 0.02))
                self.y += 12
        self.y += 9


def main() -> None:
    b = PdfBuilder()
    generated_on = os.getenv("SUBMISSION_DATE", date.today().isoformat())
    git_log = command_output(["git", "log", "--oneline", "-6"])
    remote = command_output(["git", "remote", "-v"])
    status = project_status()
    has_db_screenshot = (ROOT / "docs" / "postgres-data.png").exists()

    b.new_page()
    b.page.insert_text((54, 86), "Final Submission", fontsize=26, fontname="helv", color=(0.05, 0.17, 0.30))
    b.page.insert_text((54, 122), "FlyRank Internship - Backend Track - Week 1 Assignment A3", fontsize=12, fontname="helv")
    b.page.insert_text((54, 146), "Containerize your stack", fontsize=12, fontname="helv")
    b.page.insert_text((54, 172), f"Generated: {generated_on}", fontsize=10, fontname="helv")
    b.y = 220
    b.subheading("Project")
    b.para("FlyRank Task API - Containerized Postgres. This submission uses Python, FastAPI, psycopg 3, PostgreSQL 16, Docker, and Docker Compose.")
    b.subheading("Repository State")
    b.bullet(status)
    b.bullet("Git remote: " + (remote if remote else "No remote configured in this local clone. Add the public GitHub URL before submitting if required by the portal."))
    b.subheading("Important Note")
    if has_db_screenshot:
        b.bullet("Database screenshot is present at docs/postgres-data.png.")
    else:
        b.bullet("A genuine database screenshot is not present at docs/postgres-data.png. Docker is also unavailable in this environment, so this PDF does not fabricate psql output.")

    b.new_page("Requirement Evidence")
    checks = [
        ("Dockerfile present", "Dockerfile builds the FastAPI app image and starts uvicorn on port 8000."),
        ("Compose stack", "compose.yaml defines api and db services."),
        ("Postgres container", "db uses the official postgres:16 image."),
        ("Persistence", "compose.yaml defines and mounts the named taskdata volume at /var/lib/postgresql/data."),
        ("Environment config", ".env is git-ignored and .env.example documents POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, and DATABASE_URL."),
        ("Parameterized queries", "repository.py uses psycopg %s placeholders for SELECT, INSERT, UPDATE, and DELETE inputs."),
        ("Startup database setup", "repository.init_db creates the tasks table if missing and seeds three tasks only when the table is empty."),
        ("CRUD endpoints", "main.py exposes GET /tasks, GET /tasks/{id}, POST /tasks, PUT /tasks/{id}, and DELETE /tasks/{id}."),
        ("Status codes", "Successful routes return 200, 201, or 204; invalid input returns 400; missing tasks return 404."),
        ("Documentation", "README.md includes one-command run instructions, endpoint table, curl example, and database verification notes."),
        ("Commits", "git log contains six A3 stage commits."),
    ]
    for title, detail in checks:
        b.bullet(f"{title}: {detail}")

    b.subheading("Latest A3 Commits")
    b.code(git_log)

    b.new_page("Run Instructions")
    b.para("A reviewer can run the project from a clean clone with these commands:")
    b.code("Copy-Item .env.example .env\ndocker compose up --build")
    b.para("API URL: http://localhost:8000")
    b.para("Swagger UI: http://localhost:8000/docs")
    b.subheading("Database Verification")
    b.code("docker exec -it taskdb psql -U postgres -d tasks\n\\dt\nSELECT * FROM tasks;")
    b.subheading("Persistence Check")
    b.para("Create a task, run docker compose down, then run docker compose up --build again. The named taskdata volume should keep the row available through GET /tasks.")

    b.new_page("Key Files")
    b.subheading("compose.yaml")
    b.code(read_text("compose.yaml"))
    b.subheading("Dockerfile")
    b.code(read_text("Dockerfile"))
    b.subheading(".env.example")
    b.code(read_text(".env.example"))

    b.new_page("API And Database Evidence")
    b.subheading("Endpoints From README")
    b.para("GET /, GET /health, GET /tasks, GET /tasks/{task_id}, POST /tasks, PUT /tasks/{task_id}, DELETE /tasks/{task_id}.")
    b.subheading("curl-output.txt")
    b.code(read_text("docs/curl-output.txt"))
    b.subheading("crud-checklist.txt")
    b.code(read_text("docs/crud-checklist.txt"))
    b.subheading("postgres-read-check.txt")
    b.code(read_text("docs/postgres-read-check.txt"))

    b.doc.save(OUT)
    b.doc.close()
    print(OUT)


if __name__ == "__main__":
    main()
