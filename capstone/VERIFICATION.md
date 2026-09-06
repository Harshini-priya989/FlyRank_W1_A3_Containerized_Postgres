# Capstone verification

Checked on 2026-09-06 with FastAPI `TestClient`.

```text
GET /health -> 200, books=60
GET /books/search?q=history -> 200, 11 records
POST /reports/books without token -> 401
POST /auth/login with demo@example.com/password123 -> 200
POST /ai/tag with bearer token -> 200
POST /reports/books with bearer token -> 200
GET /reports/latest with bearer token -> 200
GET /usage/cost-log with bearer token -> 200
```
