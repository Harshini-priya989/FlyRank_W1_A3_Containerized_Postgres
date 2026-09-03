# FlyRank Task API — Containerized Postgres (A3)

This project is the Week 1 Assignment A3 continuation of the same Task CRUD API from A1/A2. The API now stores tasks in PostgreSQL running in Docker, and the API plus database can be started together with one command.

## Stack
- Python 3.10+
- FastAPI
- psycopg 3
- PostgreSQL (official Docker image)
- Docker + Docker Compose

## Configuration
Copy `.env.example` to `.env` and keep `.env` local. The committed `.env.example` shows the required variables without exposing a secret.

```powershell
Copy-Item .env.example .env
```

For the Compose stack, the API connects to the database by the Compose service name `db`, not `localhost`.

## Run everything

```bash
docker compose up --build
```

API: http://localhost:8000  
Swagger UI: http://localhost:8000/docs

Stop the stack with:

```bash
docker compose down
```

Start it again with `docker compose up --build`. The named volume keeps PostgreSQL rows across the restart.

## Endpoints

| Method | Path | Purpose | Success / Error |
|---|---|---|---|
| GET | `/` | API information | 200 |
| GET | `/health` | Health response | 200 |
| GET | `/tasks` | List tasks | 200 |
| GET | `/tasks/{task_id}` | Get one task | 200 / 404 |
| POST | `/tasks` | Create task | 201 / 400 |
| PUT | `/tasks/{task_id}` | Update task | 200 / 400 / 404 |
| DELETE | `/tasks/{task_id}` | Delete task | 204 / 404 |

## Database

The `tasks` table is created automatically on application startup if it does not exist:

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE
);
```

Three example tasks are inserted only when the table is empty. Restarting the API does not duplicate the seed rows.

All user-controlled values are passed through parameterized psycopg queries using `%s` placeholders.

## Example curl

```bash
curl -i http://localhost:8000/tasks
```

Example successful response:

```text
HTTP/1.1 200 OK
content-type: application/json

[{"id":1,"title":"Learn FastAPI","done":false}, ...]
```

## Database verification

The Postgres database can be inspected directly with:

```bash
docker exec -it taskdb psql -U postgres -d tasks
```

Then:

```sql
\dt
SELECT * FROM tasks;
```

The same rows should be visible through `GET /tasks`.

**Submission evidence:** add a genuine screenshot of the `tasks` table from `psql`, DBeaver, pgAdmin, or TablePlus at `docs/postgres-data.png` after running the stack locally.

## Persistence check

1. Run `docker compose up --build`.
2. Create a task.
3. Run `docker compose down`.
4. Run `docker compose up --build` again.
5. Call `GET /tasks` and confirm the created task is still present.

## Security note

`.env` is ignored by Git. Commit `.env.example`, never the real `.env` file or a real database password.
