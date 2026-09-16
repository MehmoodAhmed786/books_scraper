import os
import sys
import time
import requests
from pathlib import Path

# Paths & Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/your-username/scraper)"
}
TIMEOUT = 10  # Seconds


def fetch_page(url: str, cache_filename: str) -> str:
    """
    Fetches a page with an identifying User-Agent and timeout.
    Caches the response locally; reads from cache on subsequent calls.
    """
    cache_path = CACHE_DIR / cache_filename

    # Check cache first
    if cache_path.exists():
        html_content = cache_path.read_text(encoding="utf-8")
        size_bytes = len(html_content.encode("utf-8"))
        print(f"CACHE HIT: {cache_filename} ({size_bytes} bytes)")
        return html_content

    # Fetch over network
    print(f"FETCH: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            print(f"FAILED: HTTP {response.status_code} for {url}")
            return ""

        html_content = response.text
        size_bytes = len(html_content.encode("utf-8"))
        
        # Save to cache
        cache_path.write_text(html_content, encoding="utf-8")
        print(f"SAVED TO CACHE: {cache_filename} ({size_bytes} bytes)")
        return html_content

    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch {url} - {e}")
        return ""


if __name__ == "__main__":
    target_url = "https://books.toscrape.com/catalogue/page-1.html"
    fetch_page(target_url, "catalogue-page-1.html")