# The Polite Scraper

A small, cache-first Python scraper for the public **Books to Scrape** practice website.

## Target Classification

### Target

Books to Scrape:

https://books.toscrape.com/

### Classification

**Public, non-authenticated practice/sandbox website.**

The target was selected because Books to Scrape is specifically intended for practicing web scraping.

### Scope

The scraper processes only the first 3 catalogue pages and discovers 60 books.

It collects only the fields required for the assignment:

- `title`
- `product_url`
- `price_text`
- `price_gbp`
- `availability_text`
- `rating_text`
- `description`
- `source_page`
- `fetched_at`

## Lane

**Lane: Python / requests + BeautifulSoup**

The scraper uses ordinary HTTP requests and parses the HTML returned by the server.

No browser automation is required.

The data is already present in the HTML the server sends, so a browser would only add cost and unnecessary complexity.

## Installation

Clone the repository and enter the scraper directory.

Install the dependencies with:

```bash
pip install -r requirements.txt
One-command run

From the scraper directory:

python src/main.py

The run produces:

output/raw-books.json
output/books.json
output/errors.json
output/run-report.json

A stranger can clone the repository, install the two dependencies, run the command above, and receive the scraper outputs in under 5 minutes.

Record Schema

Each normalized record in output/books.json has this schema:

{
  "title": "string",
  "product_url": "https://...",
  "price_text": "string",
  "price_gbp": 51.77,
  "availability_text": "string",
  "rating_text": "string or null",
  "description": "string or null",
  "source_page": "https://...",
  "fetched_at": "ISO-8601 timestamp"
}

price_gbp is normalized from the displayed price text.

Duplicate product URLs and invalid records are rejected and written to output/errors.json.

Politeness Rules

The scraper follows these rules:

User-Agent: identifies the project with an identifying User-Agent.
Delay: waits at least 500 ms after real network requests.
Timeout: every HTTP request has a 10-second timeout.
Cache: downloaded catalogue and detail HTML is cached locally under cache/.
Cache-first: cached pages are reused instead of making unnecessary network requests.
Retries: timeouts and HTTP 5xx responses may be retried once.
No retry: HTTP 403 and 404 responses are not retried.

The cache/ directory is excluded from Git so hundreds of cached HTML files are not published.

Run Evidence

Real run from this project:

{
  "started_at": "2026-08-24T22:16:45.593827+00:00",
  "finished_at": "2026-08-24T22:16:47.798380+00:00",
  "duration_seconds": 2.205,
  "catalogue_pages": 3,
  "discovered_urls": 60,
  "pages_fetched": 0,
  "cache_hits": 63,
  "retries": 0,
  "detail_pages_processed": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "failures": []
}

This run processed all 60 discovered books successfully, producing 60 valid records with no failed or invalid records.

Evidence Files

The repository includes sample output files:

output/books.json — normalized records
output/run-report.json — execution evidence
output/errors.json — validation errors, if any
output/raw-books.json — raw extracted records

Cached HTML is intentionally not committed.

Honest Limitation

This scraper only processes the first three catalogue pages, so it is not a complete mirror of the Books to Scrape catalogue.

Ethics

Use an official API when one exists.

Never bypass logins, paywalls, robots restrictions, rate limits, or other access controls.

Collect only the data that is necessary for the task.

This project uses Books to Scrape because it is a public scraping practice sandbox.

Project History

The scraper was developed incrementally through meaningful stage commits:

Stage 0 — classify scraping target
Stage 1 — fetch and cache HTML
Stage 2 — discover three catalogue pages
Stage 3 — extract book details
Stage 4 — validate normalized records
Stage 5 — add retries and failure handling
Stage 5.5 — publish dependencies and documentation
Stage 6 — publish scraper evidence