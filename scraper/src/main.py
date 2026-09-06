from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError


BASE_URL = "https://books.toscrape.com/"
START_URL = urljoin(BASE_URL, "catalogue/page-1.html")
BAD_URL = urljoin(BASE_URL, "catalogue/this-page-is-deliberately-missing/index.html")
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/Harshini-priya989/FlyRank_W1_A3_Containerized_Postgres)"
TIMEOUT_SECONDS = 8
DELAY_SECONDS = 0.55

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "cache"
OUTPUT_DIR = ROOT / "output"


class BookRecord(BaseModel):
    model_config = ConfigDict(json_encoders={HttpUrl: str})

    title: str = Field(min_length=1)
    product_url: HttpUrl
    price_text: str = Field(min_length=1)
    price_gbp: float = Field(ge=0)
    availability_text: str = Field(min_length=1)
    rating_text: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)
    description: str | None
    source_page: HttpUrl
    fetched_at: str = Field(min_length=1)


class Stats:
    def __init__(self) -> None:
        self.pages_fetched = 0
        self.cache_hits = 0
        self.failed_pages: list[dict[str, Any]] = []
        self.invalid_records: list[dict[str, Any]] = []


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def cache_path(url: str) -> Path:
    parsed = urlparse(url)
    readable = parsed.path.strip("/").replace("/", "__") or "index"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return CACHE_DIR / f"{readable}-{digest}.html"


def fetch_html(url: str, stats: Stats, *, use_cache: bool = True) -> str:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = cache_path(url)
    if use_cache and path.exists():
        html = path.read_text(encoding="utf-8")
        stats.cache_hits += 1
        print(f"CACHE HIT {url} bytes={len(html)}")
        return html

    headers = {"User-Agent": USER_AGENT}
    last_error: str | None = None
    for attempt in range(1, 3):
        try:
            print(f"FETCH {url} attempt={attempt}")
            response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
            if response.status_code == 200:
                response.encoding = response.encoding or "utf-8"
                html = response.text
                path.write_text(html, encoding="utf-8")
                stats.pages_fetched += 1
                print(f"FETCHED {url} status=200 bytes={len(html)}")
                time.sleep(DELAY_SECONDS)
                return html
            last_error = f"status {response.status_code}"
            if response.status_code not in {500, 502, 503, 504}:
                break
        except requests.RequestException as exc:
            last_error = str(exc)
        if attempt == 1:
            time.sleep(DELAY_SECONDS)

    raise RuntimeError(last_error or "request failed")


def robots_result(stats: Stats) -> str:
    url = urljoin(BASE_URL, "robots.txt")
    try:
        fetch_html(url, stats, use_cache=False)
        return "robots.txt returned 200"
    except RuntimeError as exc:
        return f"no robots file found ({exc})"


def soup_for(url: str, stats: Stats) -> BeautifulSoup:
    return BeautifulSoup(fetch_html(url, stats), "html.parser")


def discover_book_urls(stats: Stats, *, max_pages: int = 3) -> tuple[list[dict[str, str]], list[str]]:
    current_url = START_URL
    catalogue_pages: list[str] = []
    discovered: list[dict[str, str]] = []

    for _ in range(max_pages):
        soup = soup_for(current_url, stats)
        catalogue_pages.append(current_url)
        for article in soup.select("article.product_pod"):
            link = article.select_one("h3 a")
            if not link or not link.get("href"):
                continue
            discovered.append(
                {
                    "product_url": urljoin(current_url, link["href"]),
                    "source_page": current_url,
                }
            )

        next_link = soup.select_one("li.next a")
        if not next_link or not next_link.get("href"):
            break
        current_url = urljoin(current_url, next_link["href"])

    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for item in discovered:
        if item["product_url"] not in seen:
            seen.add(item["product_url"])
            unique.append(item)

    print(
        f"catalogue_pages={len(catalogue_pages)} "
        f"discovered={len(discovered)} unique_urls={len(unique)}"
    )
    return unique, catalogue_pages


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_price(price_text: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)", price_text)
    if not match:
        raise ValueError(f"Could not parse price: {price_text}")
    return float(match.group(1))


def parse_rating(rating_text: str) -> int:
    ratings = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    if rating_text not in ratings:
        raise ValueError(f"Could not parse rating: {rating_text}")
    return ratings[rating_text]


def extract_book(item: dict[str, str], stats: Stats) -> dict[str, Any]:
    product_url = item["product_url"]
    soup = soup_for(product_url, stats)
    product = soup.select_one("article.product_page")
    if product is None:
        raise ValueError("Missing product page area")

    title_el = product.select_one(".product_main h1")
    price_el = product.select_one(".product_main .price_color")
    availability_el = product.select_one(".product_main .availability")
    rating_el = product.select_one(".product_main p.star-rating")
    description_el = product.select_one("#product_description + p")

    if title_el is None or price_el is None or availability_el is None or rating_el is None:
        raise ValueError("Missing required product fields")

    rating_classes = [cls for cls in rating_el.get("class", []) if cls != "star-rating"]
    rating_text = rating_classes[0] if rating_classes else ""
    description = clean_text(description_el.get_text(" ")) if description_el else None

    return {
        "title": clean_text(title_el.get_text(" ")),
        "product_url": product_url,
        "price_text": clean_text(price_el.get_text(" ")),
        "availability_text": clean_text(availability_el.get_text(" ")),
        "rating_text": rating_text,
        "description": description or None,
        "source_page": item["source_page"],
        "fetched_at": now_utc(),
    }


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(raw)
    normalized["price_gbp"] = parse_price(raw["price_text"])
    normalized["rating"] = parse_rating(raw["rating_text"])
    return normalized


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def run(include_bad_url: bool = True) -> dict[str, Any]:
    start = time.perf_counter()
    started_at = now_utc()
    stats = Stats()

    robots = robots_result(stats)
    discovered, catalogue_pages = discover_book_urls(stats)
    if include_bad_url:
        discovered.append({"product_url": BAD_URL, "source_page": START_URL})

    by_url: dict[str, dict[str, Any]] = {}
    raw_sample: dict[str, Any] | None = None

    for item in discovered:
        url = item["product_url"]
        try:
            raw = extract_book(item, stats)
            raw_sample = raw_sample or raw
            record = BookRecord.model_validate(normalize(raw))
            by_url[str(record.product_url)] = record.model_dump(mode="json")
        except (RuntimeError, ValueError, ValidationError) as exc:
            failure = {"url": url, "reason": str(exc)}
            stats.failed_pages.append(failure)
            if isinstance(exc, ValidationError):
                stats.invalid_records.append(failure)
            print(f"SKIP {url} reason={exc}")

    records = sorted(by_url.values(), key=lambda row: row["product_url"])
    report = {
        "started_at": started_at,
        "finished_at": now_utc(),
        "duration_seconds": round(time.perf_counter() - start, 3),
        "target": BASE_URL,
        "robots_result": robots,
        "catalogue_pages": len(catalogue_pages),
        "discovered_urls": len({item["product_url"] for item in discovered if item["product_url"] != BAD_URL}),
        "attempted_detail_pages": len(discovered),
        "pages_fetched": stats.pages_fetched,
        "cache_hits": stats.cache_hits,
        "valid_records": len(records),
        "invalid_records": len(stats.invalid_records),
        "failed_pages": len(stats.failed_pages),
        "failed_page_details": stats.failed_pages,
        "user_agent": USER_AGENT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "delay_seconds": DELAY_SECONDS,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "books.json", records)
    write_json(OUTPUT_DIR / "errors.json", stats.failed_pages)
    write_json(OUTPUT_DIR / "run-report.json", report)

    print("raw_record_sample=")
    print(json.dumps(raw_sample, indent=2, ensure_ascii=False))
    print(
        f"detail_pages={len(records)} valid_records={len(records)} "
        f"failed_pages={len(stats.failed_pages)}"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Polite Books to Scrape pipeline")
    parser.add_argument(
        "--no-bad-url",
        action="store_true",
        help="Skip the deliberate broken URL used to prove failure handling.",
    )
    args = parser.parse_args()
    run(include_bad_url=not args.no_bad_url)


if __name__ == "__main__":
    main()
