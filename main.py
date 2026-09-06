from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

import auth_service
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


class AuthCredentials(BaseModel):
    email: str | None = None
    password: str | None = None


security = HTTPBearer(auto_error=False)


def error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


def require_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Access token required")

    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(status_code=401, detail="Access token required")

    try:
        response = auth_service.get_user(token)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    user = getattr(response, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return auth_service.public_user(user)


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository.init_db()
    yield


app = FastAPI(title="Task API", version="1.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=400, content={"error": "Invalid request body"})


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.get("/")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks", "/auth/signup", "/auth/login", "/auth/logout"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: AuthCredentials):
    if payload.email is None or not payload.email.strip():
        return error_response(400, "Email is required")
    if payload.password is None or not payload.password:
        return error_response(400, "Password is required")

    try:
        response = auth_service.sign_up(payload.email.strip(), payload.password)
    except RuntimeError as exc:
        return error_response(500, str(exc))
    except Exception as exc:
        return error_response(400, str(exc))
    return auth_service.auth_response_payload(response)


@app.post("/auth/login")
def login(payload: AuthCredentials):
    if payload.email is None or not payload.email.strip():
        return error_response(400, "Email is required")
    if payload.password is None or not payload.password:
        return error_response(400, "Password is required")

    try:
        response = auth_service.sign_in(payload.email.strip(), payload.password)
    except RuntimeError as exc:
        return error_response(500, str(exc))
    except Exception:
        return error_response(401, "Invalid login credentials")
    return auth_service.auth_response_payload(response)


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: dict[str, Any] = Depends(require_current_user)):
    try:
        auth_service.sign_out()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception:
        pass
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile")
def protected_profile(current_user: dict[str, Any] = Depends(require_current_user)):
    return {"user": current_user}


@app.get("/protected/dashboard")
def protected_dashboard(current_user: dict[str, Any] = Depends(require_current_user)):
    return {
        "message": "Protected dashboard data",
        "user": current_user,
    }


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
