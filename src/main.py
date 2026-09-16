import os
import sys
import time
import json
import re
import requests
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl, ValidationError, Field

# Paths & Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/your-username/scraper)"
}
TIMEOUT = 10  # Seconds
POLITE_DELAY = 0.5  # Seconds between network fetches


# --- Schema Definition ---
class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float = Field(gt=0, description="Clean numeric price in GBP")
    availability_text: str
    rating_text: str
    description: str | None = None
    source_page: HttpUrl
    fetched_at: str


def fetch_page(url: str, cache_filename: str) -> str:
    """
    Fetches a page with an identifying User-Agent and timeout.
    Caches the response locally; reads from cache on subsequent calls.
    """
    cache_path = CACHE_DIR / cache_filename

    if cache_path.exists():
        html_content = cache_path.read_text(encoding="utf-8")
        size_bytes = len(html_content.encode("utf-8"))
        print(f"CACHE HIT: {cache_filename} ({size_bytes} bytes)")
        return html_content

    time.sleep(POLITE_DELAY)
    print(f"FETCH: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            print(f"FAILED: HTTP {response.status_code} for {url}")
            return ""

        html_content = response.text
        size_bytes = len(html_content.encode("utf-8"))
        
        cache_path.write_text(html_content, encoding="utf-8")
        print(f"SAVED TO CACHE: {cache_filename} ({size_bytes} bytes)")
        return html_content

    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch {url} - {e}")
        return ""


def discover_book_urls(max_pages: int = 3) -> tuple[list[tuple[str, str]], int]:
    """
    Crawls catalogue pages. Returns list of tuples: (book_url, source_catalogue_page_url)
    """
    current_url = "https://books.toscrape.com/catalogue/page-1.html"
    discovered_records = []
    catalogue_pages_visited = 0

    while current_url and catalogue_pages_visited < max_pages:
        catalogue_pages_visited += 1
        cache_name = f"catalogue-page-{catalogue_pages_visited}.html"
        source_url = current_url
        
        html = fetch_page(current_url, cache_name)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")

        book_articles = soup.select("article.product_pod")
        for article in book_articles:
            link_tag = article.select_one("h3 a")
            if link_tag and link_tag.get("href"):
                relative_href = link_tag["href"]
                absolute_url = urljoin(current_url, relative_href)
                discovered_records.append((absolute_url, source_url))

        next_button = soup.select_one("li.next a")
        if next_button and next_button.get("href"):
            current_url = urljoin(current_url, next_button["href"])
        else:
            current_url = None

    seen = set()
    unique_records = []
    for book_url, source_page in discovered_records:
        if book_url not in seen:
            seen.add(book_url)
            unique_records.append((book_url, source_page))

    return unique_records, catalogue_pages_visited


def extract_raw_book_record(book_url: str, source_page: str, idx: int) -> dict | None:
    """
    Extracts raw string fields from a book detail page.
    """
    cache_filename = f"book-detail-{idx}.html"
    fetched_timestamp = datetime.now(timezone.utc).isoformat()
    
    html = fetch_page(book_url, cache_filename)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    main_area = soup.select_one("article.product_page")
    if not main_area:
        return None

    title_el = main_area.select_one("h1")
    title = title_el.text.strip() if title_el else ""

    price_el = main_area.select_one("p.price_color")
    price_text = price_el.text.strip() if price_el else ""

    availability_el = main_area.select_one("p.instock.availability")
    availability_text = " ".join(availability_el.text.split()) if availability_el else ""

    rating_el = main_area.select_one("p.star-rating")
    rating_text = ""
    if rating_el:
        classes = rating_el.get("class", [])
        for c in classes:
            if c != "star-rating":
                rating_text = c
                break

    desc_el = soup.select_one("#product_description ~ p")
    description = desc_el.text.strip() if desc_el else None

    return {
        "title": title,
        "product_url": book_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_timestamp,
    }


def clean_price(price_text: str) -> float:
    """
    Extracts float from string like '£51.77'.
    """
    match = re.search(r"[\d.]+", price_text)
    if match:
        return float(match.group(0))
    return 0.0


def process_and_store():
    book_entries, pages_count = discover_book_urls(max_pages=3)
    valid_records = []
    error_records = []

    print(f"\nProcessing {len(book_entries)} detail pages...")
    for idx, (book_url, source_page) in enumerate(book_entries, start=1):
        raw = extract_raw_book_record(book_url, source_page, idx)
        if not raw:
            error_records.append({"url": book_url, "reason": "Failed to fetch or parse HTML"})
            continue

        # Normalization
        clean_data = dict(raw)
        clean_data["price_gbp"] = clean_price(raw["price_text"])

        # Validation
        try:
            validated = BookRecord(**clean_data)
            # Store serializable dict (handling HttpUrl conversion to str)
            valid_records.append(validated.model_dump(mode="json"))
        except ValidationError as ve:
            error_records.append({
                "record": raw,
                "reason": str(ve)
            })

    # Write output files
    books_file = OUTPUT_DIR / "books.json"
    books_file.write_text(json.dumps(valid_records, indent=2), encoding="utf-8")

    errors_file = OUTPUT_DIR / "errors.json"
    errors_file.write_text(json.dumps(error_records, indent=2), encoding="utf-8")

    print(f"\n--- Stage 4 Checkpoint Results ---")
    print(f"Total valid records stored in books.json: {len(valid_records)}")
    print(f"Total error records stored in errors.json: {len(error_records)}")
    
    if valid_records:
        sample = valid_records[0]
        print(f"Sample price_gbp type: {type(sample['price_gbp']).__name__} = {sample['price_gbp']}")
        print(f"Sample canonical URL: {sample['product_url']}")


if __name__ == "__main__":
    process_and_store()