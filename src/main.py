import os
import sys
import time
import requests
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Paths & Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/your-username/scraper)"
}
TIMEOUT = 10  # Seconds
POLITE_DELAY = 0.5  # Seconds between network fetches


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

    # Respectful delay only before actual network requests
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


def discover_book_urls(max_pages: int = 3) -> tuple[list[str], int]:
    """
    Crawls up to max_pages catalogue pages, extracting absolute URLs for all books.
    """
    current_url = "https://books.toscrape.com/catalogue/page-1.html"
    discovered_urls = []
    catalogue_pages_visited = 0

    while current_url and catalogue_pages_visited < max_pages:
        catalogue_pages_visited += 1
        cache_name = f"catalogue-page-{catalogue_pages_visited}.html"
        
        html = fetch_page(current_url, cache_name)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")

        # Target only the product articles, not general links
        book_articles = soup.select("article.product_pod")
        for article in book_articles:
            link_tag = article.select_one("h3 a")
            if link_tag and link_tag.get("href"):
                relative_href = link_tag["href"]
                # Convert relative URL to absolute URL cleanly
                absolute_url = urljoin(current_url, relative_href)
                discovered_urls.append(absolute_url)

        # Find "next" page link dynamically
        next_button = soup.select_one("li.next a")
        if next_button and next_button.get("href"):
            current_url = urljoin(current_url, next_button["href"])
        else:
            current_url = None

    # Deduplicate while preserving order
    unique_urls = list(dict.fromkeys(discovered_urls))
    
    return unique_urls, catalogue_pages_visited


if __name__ == "__main__":
    book_urls, pages_count = discover_book_urls(max_pages=3)
    print(f"\ncatalogue_pages={pages_count}, discovered={len(book_urls)}, unique_urls={len(set(book_urls))}")