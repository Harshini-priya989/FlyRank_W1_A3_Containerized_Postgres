# FlyRank Task API - Auth + Containerized Postgres

This project is the FlyRank Backend Track Assignment A4 continuation of the task API. It keeps the containerized FastAPI + PostgreSQL stack from A3 and adds Supabase Auth for signup, login, logout, protected routes, and Swagger bearer authorization.

## W5 Polite Scraper

The Week 5 A9 polite scraper submission lives in [`scraper/README.md`](scraper/README.md). It collects the first three Books to Scrape catalogue pages, validates 60 unique book records, writes `scraper/output/books.json`, and records the run in `scraper/output/run-report.json`.

## Backend AI Engineering Capstone

The "Your 10x Solution" capstone lives in [`capstone/README.md`](capstone/README.md). The required overview document is [`capstone/My 10x Solution - Harshini Priya.md`](capstone/My%2010x%20Solution%20-%20Harshini%20Priya.md).

## Stack

- Python 3.10+
- FastAPI
- Supabase Auth
- psycopg 3
- PostgreSQL 16
- Docker + Docker Compose

## Configuration

Copy `.env.example` to `.env` and keep `.env` local:

```powershell
Copy-Item .env.example .env
```

Set these values in `.env`:

```text
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dev
POSTGRES_DB=tasks
DATABASE_URL=postgresql://postgres:dev@localhost:5432/tasks
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

Get `SUPABASE_URL` and `SUPABASE_KEY` from Supabase Dashboard -> Project Settings -> API. Use the anon/public key only. Do not use the `service_role` key.

For this practice assignment, turn off email confirmation in Supabase: Authentication -> Sign In / Providers -> Email -> Confirm email off.

## Run Everything

```powershell
docker compose up --build
```

API: http://localhost:8000

Swagger UI: http://localhost:8000/docs

Stop the stack:

```powershell
docker compose down
```

## Auth Endpoints

| Method | Path | Auth required | Purpose | Success / Error |
|---|---|---:|---|---|
| POST | `/auth/signup` | No | Create a Supabase user | 201 / 400 |
| POST | `/auth/login` | No | Log in and return access + refresh tokens | 200 / 400 / 401 |
| POST | `/auth/logout` | Yes | Log out authenticated user | 204 / 401 |
| GET | `/public/info` | No | Public test route | 200 |
| GET | `/protected/profile` | Yes | Return verified user profile | 200 / 401 |
| GET | `/protected/dashboard` | Yes | Second protected route using the same auth dependency | 200 / 401 |

Protected routes require:

```text
Authorization: Bearer <access_token>
```

## Auth curl Checks

Signup:

```powershell
curl -i -X POST http://localhost:8000/auth/signup -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\",\"password\":\"password123\"}"
```

Login:

```powershell
curl -i -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\",\"password\":\"password123\"}"
```

Protected profile:

```powershell
curl -i http://localhost:8000/protected/profile -H "Authorization: Bearer PASTE_ACCESS_TOKEN_HERE"
```

Missing token check:

```powershell
curl -i http://localhost:8000/protected/profile
```

Expected result: `401` with JSON error.

## Swagger UI

FastAPI serves Swagger at:

```text
http://localhost:8000/docs
```

Protected routes use FastAPI's `HTTPBearer` security scheme, so Swagger shows an Authorize padlock. Log in, copy the `access_token`, click Authorize, paste the token, then run `GET /protected/profile`.

Submission evidence: save a screenshot of Swagger with protected-route padlocks as:

```text
docs/swagger-auth.png
```

## Existing Task API

The A3 task API still runs against PostgreSQL.

| Method | Path | Purpose | Success / Error |
|---|---|---|---|
| GET | `/` | API information | 200 |
| GET | `/health` | Health response | 200 |
| GET | `/tasks` | List tasks | 200 |
| GET | `/tasks/{task_id}` | Get one task | 200 / 404 |
| POST | `/tasks` | Create task | 201 / 400 |
| PUT | `/tasks/{task_id}` | Update task | 200 / 400 / 404 |
| DELETE | `/tasks/{task_id}` | Delete task | 204 / 404 |

The `tasks` table is created automatically on startup and seeded only when empty.

## Security Notes

- `.env` is ignored by Git.
- `.env.example` is committed with placeholders only.
- Passwords are never stored or hashed by this API; Supabase Auth handles credentials.
- Protected routes verify the JWT with `supabase.auth.get_user(token)`.
- The app uses the Supabase anon key, never the `service_role` key.

## Submission Checklist

- Public GitHub repo pushed.
- At least six assignment-stage commits in `git log`.
- `.env` not committed.
- `.env.example` committed.
- `POST /auth/signup` works.
- `POST /auth/login` returns an access token.
- `GET /protected/profile` rejects missing or bad tokens with `401`.
- `GET /protected/profile` accepts a valid Supabase access token.
- `POST /auth/logout` is protected and returns `204`.
- `GET /protected/dashboard` reuses the same auth dependency.
- Swagger UI shows bearer auth padlocks.
- `docs/swagger-auth.png` added before final submission.
