from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Task API", version="1.0")

class TaskInput(BaseModel):
    title: str

class Task(TaskInput):
    id: int
    done: bool = False

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

@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task_input: TaskInput):
    title = task_input.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title must not be empty")
    next_id = max((task.id for task in tasks), default=0) + 1
    task = Task(id=next_id, title=title)
    tasks.append(task)
    return task
