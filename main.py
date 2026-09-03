from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Task API", version="1.0")

class Task(BaseModel):
    id: int
    title: str
    done: bool

tasks = [
    Task(id=1, title="Learn FastAPI", done=False),
    Task(id=2, title="Build CRUD endpoints", done=False),
    Task(id=3, title="Test with Swagger", done=False),
]

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
    task = next((t for t in tasks if t.id == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task
