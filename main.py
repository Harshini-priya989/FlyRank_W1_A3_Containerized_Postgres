from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
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


@app.get("/tasks", response_model=list[Task])
def list_tasks():
    return repository.list_tasks()


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
