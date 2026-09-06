# FlyRank W5 A9 - The polite scraper

This scraper collects book data from the public Books to Scrape practice sandbox and writes validated JSON output.

## Target Classification

- Site: Books to Scrape at `https://books.toscrape.com/`
- Sandbox owner page: ToScrape describes Books as a fictional bookstore that wants to be scraped and is safe for beginners learning scraping.
- Scope: first 3 catalogue pages only.
- Expected catalogue records in scope: 60 books.
- Data collected: title, product URL, price text, numeric GBP price, availability text, rating text, numeric rating, description, source page, and fetch timestamp.
- Robots result: `https://books.toscrape.com/robots.txt` returns 404, so no robots file was found.

I will not reuse this code on another site without checking its rules and terms first.

## Install

```powershell
cd scraper
python -m pip install -r requirements.txt
```

## Run

```powershell
python src\main.py
```

The script writes:

```text
output/books.json
output/errors.json
output/run-report.json
```

## Record Schema

```json
{
  "title": "string",
  "product_url": "https URL",
  "price_text": "string",
  "price_gbp": 51.77,
  "availability_text": "string",
  "rating_text": "One | Two | Three | Four | Five",
  "rating": 1,
  "description": "string or null",
  "source_page": "https URL",
  "fetched_at": "ISO timestamp"
}
```

`product_url` is the canonical identity. A rerun produces 60 records, not duplicates.

## Politeness Rules

- User-agent: `FlyRankInternship-A9/1.0 (+https://github.com/Harshini-priya989/FlyRank_W1_A3_Containerized_Postgres)`
- Timeout: 8 seconds.
- Delay: at least 0.55 seconds after real network fetches.
- Cache: saved HTML in `cache/`; development reruns read cached files and do not re-request the same pages.
- Status check: only `200` responses are parsed.
- Retry: timeout and 5xx failures are retried once; 404 and 403 are not retried.

## Failure Handling

The default run includes one deliberately fake book URL to prove that one broken page does not kill the job. The bad page is logged in `output/errors.json` and `output/run-report.json`; the 60 valid book records still survive in `output/books.json`.

## Why No Browser Was Needed

This assignment needed no browser because the book data is already in the HTML returned by the server, so a browser would only add cost.

## Ethics Note

Use an official API when one exists. Never bypass logins, paywalls, captchas, rate limits, or blocks. Collect only the fields needed for the task, identify your scraper honestly, and stop if a site says no.

## Honest Limitation

This scraper is intentionally scoped to the first three catalogue pages of the sandbox and is not a general-purpose crawler for arbitrary websites.

## Run Report

Run `python src\main.py` to refresh this section with the latest `output/run-report.json`.
