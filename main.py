from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

import repository


class TaskInput(BaseModel):
    title: str
    done: bool = False


class Task(TaskInput):
    id: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository.init_db()
    yield


app = FastAPI(title="Task API", version="1.0", lifespan=lifespan)


@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return []
