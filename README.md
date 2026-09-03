# Task API — FlyRank Week 2 A1

A small FastAPI to-do API implementing Create, Read, Update and Delete (CRUD) operations with in-memory storage. FastAPI provides interactive Swagger UI at `/docs`.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://localhost:8000/docs` for Swagger UI.

## Endpoints

| Method | Endpoint | Purpose | Success / errors |
|---|---|---|---|
| GET | `/` | API information | 200 |
| GET | `/health` | Health check | 200 |
| GET | `/tasks` | List all tasks | 200 |
| GET | `/tasks/{id}` | Get one task | 200 / 404 |
| POST | `/tasks` | Create a task | 201 / 400 |
| PUT | `/tasks/{id}` | Update a task | 200 / 400 / 404 |
| DELETE | `/tasks/{id}` | Delete a task | 204 / 404 |

## Example curl output

```text
$ curl -i http://localhost:8000/tasks/1
HTTP/1.1 200 OK
content-type: application/json

{"id":1,"title":"Learn FastAPI","done":false}
```

## Validation

`POST` and `PUT` reject missing or empty titles with HTTP 400. Unknown task IDs return HTTP 404 with a JSON error message. DELETE returns HTTP 204 on success.

## Storage

Tasks are stored in memory only. Restarting the server resets the example data; no database is used in this assignment.

## Swagger screenshot

Run the API, open `/docs`, and use **Try it out** to complete a create → read → update → delete cycle. Save the real screenshot as `docs/swagger.png` and keep it in the repository.
