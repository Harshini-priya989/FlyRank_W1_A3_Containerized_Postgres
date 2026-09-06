# W5 stage evidence

## Stage 3: extract book details

- The scraper visits each discovered detail URL.
- Each raw record includes title, product URL, price text, availability text, rating text, description, source page, and fetched_at.
- The latest run printed one full raw record sample and `detail_pages=60`.

## Stage 4: validate normalized records

- `price_text` is converted into numeric `price_gbp`.
- `rating_text` is converted into numeric `rating`.
- Pydantic validates each record before it is written.
- `output/books.json` contains exactly 60 records after repeated runs.

## Stage 5: survive failures, report the run

- A deliberately missing book URL is added during the default run.
- The missing URL returns 404 and is skipped without retrying.
- `output/errors.json` records the failed page.
- `output/run-report.json` records duration, cache hits, valid records, invalid records, and failed pages.

## Stage 6: publish scraper evidence

- `scraper/README.md` documents setup, run command, schema, politeness rules, ethics, limitation, and the real report.
- Cache files are ignored by Git.
- Sample output files are committed.
- Final submission document is `docs/w5-final-submission.pdf`.
