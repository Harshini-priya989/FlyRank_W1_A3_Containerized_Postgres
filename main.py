import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
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


# A1 endpoints remain unchanged here; the storage migration happens in later stages.
tasks = [
    Task(id=1, title="Learn FastAPI", done=False),
    Task(id=2, title="Build CRUD endpoints", done=False),
    Task(id=3, title="Test with Swagger", done=False),
]

def find_task(task_id: int):
    return next((t for t in tasks if t.id == task_id), None)

@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks", response_model=list[Task])
def list_tasks():
    return tasks

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task

@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task_input: TaskInput):
    title = task_input.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title must not be empty")
    next_id = max((task.id for task in tasks), default=0) + 1
    task = Task(id=next_id, title=title, done=task_input.done)
    tasks.append(task)
    return task

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_input: TaskInput):
    title = task_input.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title must not be empty")
    task = find_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    task.title = title
    task.done = task_input.done
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    tasks.remove(task)
