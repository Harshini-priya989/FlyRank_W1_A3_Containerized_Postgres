import os
import time

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
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                )
                """
            )
            cur.execute("SELECT COUNT(*) FROM tasks")
            if cur.fetchone()[0] == 0:
                cur.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                    SEED_TASKS,
                )
        conn.commit()
