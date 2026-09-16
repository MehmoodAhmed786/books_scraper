# Polite Web Scraper Pipeline

A resilient, polite Python web scraping pipeline that extracts book data from the Books to Scrape sandbox, normalizes messy HTML, schema-validates every record using Pydantic, and handles failures cleanly without crashing.

---

## 1. Target Classification
- **Target Site**: Books to Scrape (`https://books.toscrape.com/`)
- **Purpose**: Practice sandbox created specifically for web scraping testing.
- **Scope**: First 3 catalogue pages (~60 books).
- **Data Collected**: `title`, `product_url`, `price_text`, `price_gbp`, `availability_text`, `rating_text`, `description`, `source_page`, and `fetched_at`.
- **Robots.txt Result**: `https://books.toscrape.com/robots.txt` returned HTTP 404 / no disallow rules found for catalogue pages.
- **Ethical Commitment**: I will not reuse this code on another site without checking its rules and terms first.

---

## 2. Quickstart (Under 5 Minutes)

### Prerequisites
- Python 3.10+
- Git

### Setup & Execution
```bash
# Clone repository
git clone [https://github.com/your-username/scraper.git](https://github.com/your-username/scraper.git)
cd scraper

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install requests beautifulsoup4 pydantic

# Run pipeline
python src/main.py


3. Pipeline Architecture & Rules
Core Stack
Language: Python 3.10+

HTTP Client: requests

HTML Parser: BeautifulSoup4

Schema Validation: Pydantic

Politeness Rules Implemented
Identifiable User-Agent: Every HTTP request presents an explicit header naming the project (FlyRankInternshipA9/1.0).

Request Delays: A minimum 500 ms pause (time.sleep(0.5)) is enforced between real network calls.

Timeouts: Every request has a 10-second timeout limit.

Caching Layer: HTML files are saved locally under cache/ during initial fetches. Subsequent runs use the cache to avoid hammering the remote host.

4. Record Schema (Pydantic)
Python
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
5. Evidence of Run (output/run-report.json)
JSON
{
  "start_time": "2026-09-16T17:00:00.000000+00:00",
  "end_time": "2026-09-16T17:00:02.500000+00:00",
  "duration_seconds": 2.5,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
6. Engineering Notes
Why No Browser Was Needed (Headless vs Plain HTTP)
Books to Scrape renders all content server-side. The HTML returned by plain HTTP GET requests contains all necessary DOM nodes directly inside the initial body. Using a headless browser engine like Playwright or Selenium would introduce massive CPU, memory, and startup latency overheads with zero operational benefit.

Honest Limitation
The pagination logic relies on discovering the relative li.next a link in the DOM. If the site structure dynamically changed its navigation component or switched to client-side JavaScript rendering, the crawler would fail to discover subsequent pages without updating selector rules.

7. Ethics
Always prefer official APIs when available before scraping web pages.

Never bypass authentication, logins, CAPTCHAs, paywalls, or blocking mechanisms.

Scrape only public data necessary for the workload and adhere strictly to polite request intervals.