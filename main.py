from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import repository


class TaskCreate(BaseModel):
    title: str | None = None
    done: bool = False


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


class Task(BaseModel):
    id: int
    title: str
    done: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository.init_db()
    yield


app = FastAPI(title="Task API", version="1.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=400, content={"error": "Invalid request body"})


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


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    if payload.title is None or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    return repository.create_task(payload.title.strip(), payload.done)


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate):
    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=400, detail="At least one field is required")
    current = repository.get_task(task_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Task not found")
    title = current["title"] if payload.title is None else payload.title.strip()
    done = current["done"] if payload.done is None else payload.done
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    return repository.update_task(task_id, title, done)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    if not repository.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
