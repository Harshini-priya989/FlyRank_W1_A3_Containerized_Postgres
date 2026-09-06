# Book Insights API - 10x Solution Capstone

Book Insights API turns the W5 scraped book catalogue into a searchable, categorized, authenticated backend with PDF reporting.

## Problem

Small teams often collect useful public catalogue data, but it stays trapped in static JSON files. Searching, filtering, summarizing, and reporting the data by hand is slow and error-prone. This project makes that workflow faster by importing validated book records into a database and exposing them through a small backend API.

## 10x Claim

Finding affordable relevant books and producing a short report goes from roughly 20 minutes of manual scanning to under 2 minutes through API search, cached recommendations, and one report endpoint.

## Concepts Implemented

| Concept | Where it lives |
|---|---|
| API endpoints | `capstone/src/app.py` exposes `/books`, `/books/search`, `/books/recommendations`, `/ai/tag`, `/jobs/import-books`, and `/reports/books` |
| Database | SQLite database at `capstone/data/book_insights.db` persists users, books, jobs, reports, and cost logs |
| Authentication | `/auth/login` issues bearer tokens; report/job/AI routes require `Authorization: Bearer <token>` |
| Background jobs | `/jobs/import-books` queues import work with FastAPI `BackgroundTasks` |
| Reporting | `/reports/books` generates a PDF report in `capstone/reports/` |
| Caching logic | `/books`, `/books/search`, and `/books/recommendations` reuse cached results for 60 seconds |
| LLM-style integration | `/ai/tag` performs one narrow validated tagging/summarization job and logs estimated cost as `$0.00` |

No swaps were needed because the solution fits more than five concepts from the main table.

## Non-Goal

This project does not build a polished frontend or production user-management system.

## Install

```powershell
cd capstone
python -m pip install -r requirements.txt
```

## Run

```powershell
python -m uvicorn src.app:app --reload --port 8010
```

Open:

```text
http://localhost:8010/docs
```

## Demo Login

```json
{
  "email": "demo@example.com",
  "password": "password123"
}
```

## 5-Minute Demo Path

1. Start the API with `python -m uvicorn src.app:app --reload --port 8010`.
2. Open `http://localhost:8010/docs`.
3. Run `GET /health` and confirm the database has 60 books.
4. Run `GET /books/search?q=history`.
5. Run `POST /auth/login` with the demo login and copy the `access_token`.
6. Click Swagger **Authorize** and paste `Bearer <access_token>`.
7. Run `POST /ai/tag` with a title and description.
8. Run `POST /reports/books`.
9. Run `GET /reports/latest` to download the generated PDF.

## Useful curl Commands

```powershell
curl -i http://localhost:8010/health
curl -i "http://localhost:8010/books/search?q=history"
curl -i -X POST http://localhost:8010/auth/login -H "Content-Type: application/json" -d "{\"email\":\"demo@example.com\",\"password\":\"password123\"}"
curl -i -X POST http://localhost:8010/reports/books -H "Authorization: Bearer PASTE_TOKEN_HERE"
```

## Data

The app imports demo data from:

```text
scraper/output/books.json
```

On startup, the database is initialized and the 60 W5 records are imported.

## Submission

Submit the public GitHub link and the overview document:

```text
My 10x Solution - Harshini Priya.md
```
