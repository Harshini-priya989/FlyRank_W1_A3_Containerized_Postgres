import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Task API", version="1.0")
DB_PATH = Path(__file__).resolve().parent / "tasks.db"

class TaskInput(BaseModel):
    title: str
    done: bool = False

class Task(TaskInput):
    id: int


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
        """)
        count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            connection.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                [
                    ("Learn FastAPI", 0),
                    ("Build CRUD endpoints", 0),
                    ("Test with Swagger", 0),
                ],
            )
        connection.commit()


@app.on_event("startup")
def startup():
    init_db()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"error": "Invalid request body"})


def row_to_task(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


def get_task_row(task_id: int):
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()


@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks", response_model=list[Task])
def list_tasks():
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM tasks").fetchall()
    return [row_to_task(row) for row in rows]

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    row = get_task_row(task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row_to_task(row)

@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task_input: TaskInput):
    title = task_input.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title must not be empty")
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (title, int(task_input.done)),
        )
        task_id = cursor.lastrowid
        connection.commit()
        row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return row_to_task(row)

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_input: TaskInput):
    title = task_input.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title must not be empty")
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (title, int(task_input.done), task_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        connection.commit()
        row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return row_to_task(row)

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        connection.commit()
    return None
