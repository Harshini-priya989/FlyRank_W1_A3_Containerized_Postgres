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
