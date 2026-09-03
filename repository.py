import os
import time
from typing import Any

import psycopg
from dotenv import load_dotenv

load_dotenv()

SEED_TASKS = [
    ("Learn FastAPI", False),
    ("Build CRUD API", False),
    ("Test the API", False),
]


def database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/tasks")


def connect_with_retry(retries: int = 30, delay: float = 1.0):
    last_error = None
    for _ in range(retries):
        try:
            return psycopg.connect(database_url())
        except psycopg.OperationalError as exc:
            last_error = exc
            time.sleep(delay)
    raise last_error


def init_db() -> None:
    with connect_with_retry() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            cur.execute("SELECT COUNT(*) FROM tasks")
            if cur.fetchone()[0] == 0:
                cur.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                    SEED_TASKS,
                )
        conn.commit()


def list_tasks() -> list[dict[str, Any]]:
    with connect_with_retry() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks ORDER BY id")
            return [dict(id=r[0], title=r[1], done=r[2]) for r in cur.fetchall()]


def get_task(task_id: int) -> dict[str, Any] | None:
    with connect_with_retry() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
            row = cur.fetchone()
            return None if row is None else dict(id=row[0], title=row[1], done=row[2])


def create_task(title: str, done: bool = False) -> dict[str, Any]:
    with connect_with_retry() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done",
                (title, done),
            )
            row = cur.fetchone()
        conn.commit()
        return dict(id=row[0], title=row[1], done=row[2])


def update_task(task_id: int, title: str, done: bool) -> dict[str, Any] | None:
    with connect_with_retry() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done",
                (title, done, task_id),
            )
            row = cur.fetchone()
        conn.commit()
        return None if row is None else dict(id=row[0], title=row[1], done=row[2])


def delete_task(task_id: int) -> bool:
    with connect_with_retry() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            deleted = cur.rowcount == 1
        conn.commit()
        return deleted
