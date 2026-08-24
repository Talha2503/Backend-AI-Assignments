import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-{}.html"

CACHE_DIR = Path("cache")
CATALOGUE_CACHE_DIR = CACHE_DIR / "catalogue"
DETAIL_CACHE_DIR = CACHE_DIR / "details"

OUTPUT_DIR = Path("output")
RAW_OUTPUT_FILE = OUTPUT_DIR / "raw-books.json"
NORMALIZED_OUTPUT_FILE = OUTPUT_DIR / "books.json"
ERROR_OUTPUT_FILE = OUTPUT_DIR / "errors.json"
RUN_REPORT_FILE = OUTPUT_DIR / "run-report.json"

USER_AGENT = (
    "FlyRankInternshipA9/1.0 "
    "(+https://github.com/Talha2503/Backend-AI-Assignments)"
)

TIMEOUT = 10
DELAY = 0.5
MAX_RETRIES = 1

# Set to a fake URL only when running the controlled Stage 5
# failure-handling test.
#
# Example:
# TEST_FAILURE_URL = (
#     "https://books.toscrape.com/catalogue/"
#     "this-page-does-not-exist_99999/index.html"
# )
#
# Leave as None for the normal scraper run.
TEST_FAILURE_URL = None


session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT
})


# ---------------------------------------------------------
# Run statistics
# ---------------------------------------------------------

stats = {
    "pages_fetched": 0,
    "cache_hits": 0,
    "retries": 0,
}


# ---------------------------------------------------------
# Fetching
# ---------------------------------------------------------

def fetch_page(url, cache_file):
    """
    Fetch a page while respecting cache, timeout, user-agent,
    retry rules, and request delay.

    Retry rules:
    - Timeout: retry once
    - HTTP 5xx: retry once
    - HTTP 403: do not retry
    - HTTP 404: do not retry
    - Other non-200 responses: do not retry
    """

    if cache_file.exists():
        html = cache_file.read_text(
            encoding="utf-8"
        )

        stats["cache_hits"] += 1

        print(
            f"CACHE HIT: {cache_file}"
        )

        print(
            f"response_size="
            f"{len(html.encode('utf-8'))} bytes"
        )

        return html

    print(
        f"FETCH: {url}"
    )

    attempt = 0

    while True:
        try:
            response = session.get(
                url,
                timeout=TIMEOUT
            )

        except requests.exceptions.Timeout as error:
            if attempt < MAX_RETRIES:
                attempt += 1
                stats["retries"] += 1

                print(
                    f"RETRY {attempt}/{MAX_RETRIES}: "
                    f"timeout for {url}"
                )

                time.sleep(DELAY)
                continue

            raise RuntimeError(
                f"Request timed out after "
                f"{MAX_RETRIES + 1} attempts: {url}"
            ) from error

        except requests.RequestException as error:
            raise RuntimeError(
                f"Request failed for {url}: {error}"
            ) from error

        print(
            f"FETCH RESPONSE: status="
            f"{response.status_code}"
        )

        # -------------------------------------------------
        # Success
        # -------------------------------------------------

        if response.status_code == 200:
            stats["pages_fetched"] += 1

            response.encoding = "utf-8"
            html = response.text

            cache_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            cache_file.write_text(
                html,
                encoding="utf-8"
            )

            print(
                f"response_size="
                f"{len(html.encode('utf-8'))} bytes"
            )

            print(
                f"cached_to={cache_file}"
            )

            return html

        # -------------------------------------------------
        # Retry 5xx once
        # -------------------------------------------------

        if 500 <= response.status_code <= 599:
            if attempt < MAX_RETRIES:
                attempt += 1
                stats["retries"] += 1

                print(
                    f"RETRY {attempt}/{MAX_RETRIES}: "
                    f"HTTP {response.status_code} for {url}"
                )

                time.sleep(DELAY)
                continue

            raise RuntimeError(
                f"Server error after "
                f"{MAX_RETRIES + 1} attempts: "
                f"HTTP {response.status_code} for {url}"
            )

        # -------------------------------------------------
        # Do NOT retry 403 / 404
        # -------------------------------------------------

        if response.status_code == 403:
            raise RuntimeError(
                f"HTTP 403 Forbidden: {url}"
            )

        if response.status_code == 404:
            raise RuntimeError(
                f"HTTP 404 Not Found: {url}"
            )

        # -------------------------------------------------
        # Any other non-200 status
        # -------------------------------------------------

        raise RuntimeError(
            f"Failed to fetch {url}: "
            f"HTTP {response.status_code}"
        )


# ---------------------------------------------------------
# Catalogue discovery
# ---------------------------------------------------------

def discover_book_urls():
    book_urls = []
    catalogue_pages = 0

    for page_number in range(1, 4):
        page_url = CATALOGUE_URL.format(
            page_number
        )

        cache_file = (
            CATALOGUE_CACHE_DIR
            / f"catalogue-page-{page_number}.html"
        )

        html = fetch_page(
            page_url,
            cache_file
        )

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        books = soup.select(
            "article.product_pod"
        )

        print(
            f"page={page_number} "
            f"books_found={len(books)}"
        )

        for book in books:
            link = book.select_one(
                "h3 a"
            )

            if link and link.get("href"):
                absolute_url = urljoin(
                    page_url,
                    link["href"]
                )

                book_urls.append(
                    (
                        absolute_url,
                        page_url
                    )
                )

        catalogue_pages += 1

        if page_number < 3:
            time.sleep(DELAY)

    unique = {}

    for product_url, source_page in book_urls:
        if product_url not in unique:
            unique[product_url] = source_page

    # -----------------------------------------------------
    # Controlled Stage 5 failure test
    # -----------------------------------------------------

    if TEST_FAILURE_URL:
        unique[TEST_FAILURE_URL] = CATALOGUE_URL.format(1)

        print()
        print(
            "TEST MODE: added one fake URL "
            "to verify failure handling."
        )

    print()
    print(
        f"catalogue_pages={catalogue_pages}"
    )

    print(
        f"discovered={len(book_urls)}"
    )

    print(
        f"unique_urls={len(unique)}"
    )

    print()

    return unique


# ---------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------

def extract_rating(soup):
    rating_element = soup.select_one(
        "p.star-rating"
    )

    if not rating_element:
        return None

    classes = rating_element.get(
        "class",
        []
    )

    for rating in (
        "One",
        "Two",
        "Three",
        "Four",
        "Five"
    ):
        if rating in classes:
            return rating

    return None


def extract_description(soup):
    description = soup.select_one(
        "#product_description + p"
    )

    if not description:
        return None

    text = description.get_text(
        " ",
        strip=True
    )

    return text if text else None


# ---------------------------------------------------------
# Book extraction
# ---------------------------------------------------------

def extract_book(
    product_url,
    source_page,
    index
):
    filename = f"book-{index:02d}.html"

    cache_file = (
        DETAIL_CACHE_DIR / filename
    )

    was_cached = cache_file.exists()

    html = fetch_page(
        product_url,
        cache_file
    )

    # Only delay after a real network request.
    # Cached pages never leave the computer.
    if not was_cached:
        time.sleep(DELAY)

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    title_element = soup.select_one(
        "div.product_main h1"
    )

    price_element = soup.select_one(
        "div.product_main .price_color"
    )

    availability_element = soup.select_one(
        "div.product_main .availability"
    )

    title = (
        title_element.get_text(
            strip=True
        )
        if title_element
        else None
    )

    price_text = (
        price_element.get_text(
            strip=True
        )
        if price_element
        else None
    )

    availability_text = (
        availability_element.get_text(
            " ",
            strip=True
        )
        if availability_element
        else None
    )

    rating_text = extract_rating(
        soup
    )

    description = extract_description(
        soup
    )

    fetched_at = datetime.now(
        timezone.utc
    ).isoformat()

    record = {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at
    }

    return record


# ---------------------------------------------------------
# Price normalization
# ---------------------------------------------------------

def normalize_price(price_text):
    if not isinstance(price_text, str):
        return None

    cleaned = (
        price_text
        .replace("├é┬ú", "")
        .replace("┬ú", "")
        .strip()
    )

    match = re.search(
        r"\d+(?:\.\d+)?",
        cleaned
    )

    if not match:
        return None

    return float(
        match.group()
    )


# ---------------------------------------------------------
# Record validation
# ---------------------------------------------------------

def validate_record(record):
    errors = []

    required_fields = [
        "title",
        "product_url",
        "price_text",
        "availability_text",
        "rating_text",
        "source_page",
        "fetched_at"
    ]

    for field in required_fields:
        if field not in record:
            errors.append(
                f"Missing required field: {field}"
            )

    if errors:
        return errors

    if not isinstance(
        record["title"],
        str
    ):
        errors.append(
            "title must be a string"
        )

    elif not record["title"].strip():
        errors.append(
            "title must not be empty"
        )

    if not isinstance(
        record["product_url"],
        str
    ):
        errors.append(
            "product_url must be a string"
        )

    elif not record["product_url"].startswith(
        "https://"
    ):
        errors.append(
            "product_url must start with https://"
        )

    if not isinstance(
        record["price_text"],
        str
    ):
        errors.append(
            "price_text must be a string"
        )

    if not isinstance(
        record["price_gbp"],
        (int, float)
    ):
        errors.append(
            "price_gbp must be a number"
        )

    if not isinstance(
        record["availability_text"],
        str
    ):
        errors.append(
            "availability_text must be a string"
        )

    if record["rating_text"] is not None:
        if not isinstance(
            record["rating_text"],
            str
        ):
            errors.append(
                "rating_text must be a string or null"
            )

    if record["description"] is not None:
        if not isinstance(
            record["description"],
            str
        ):
            errors.append(
                "description must be a string or null"
            )

    if not isinstance(
        record["source_page"],
        str
    ):
        errors.append(
            "source_page must be a string"
        )

    elif not record["source_page"].startswith(
        "https://"
    ):
        errors.append(
            "source_page must start with https://"
        )

    if not isinstance(
        record["fetched_at"],
        str
    ):
        errors.append(
            "fetched_at must be a string"
        )

    return errors


# ---------------------------------------------------------
# Record normalization
# ---------------------------------------------------------

def normalize_record(raw_record):
    price_gbp = normalize_price(
        raw_record.get(
            "price_text"
        )
    )

    normalized_record = {
        "title": raw_record.get(
            "title"
        ),
        "product_url": raw_record.get(
            "product_url"
        ),
        "price_text": raw_record.get(
            "price_text"
        ),
        "price_gbp": price_gbp,
        "availability_text": raw_record.get(
            "availability_text"
        ),
        "rating_text": raw_record.get(
            "rating_text"
        ),
        "description": raw_record.get(
            "description"
        ),
        "source_page": raw_record.get(
            "source_page"
        ),
        "fetched_at": raw_record.get(
            "fetched_at"
        )
    }

    return normalized_record


def normalize_records(raw_records):
    valid_records = []
    invalid_records = []

    seen_urls = set()

    for raw_record in raw_records:
        normalized_record = normalize_record(
            raw_record
        )

        product_url = normalized_record.get(
            "product_url"
        )

        if product_url in seen_urls:
            invalid_records.append({
                "product_url": product_url,
                "errors": [
                    "Duplicate product_url"
                ]
            })

            continue

        errors = validate_record(
            normalized_record
        )

        if errors:
            invalid_records.append({
                "product_url": product_url,
                "errors": errors,
                "record": normalized_record
            })

            continue

        seen_urls.add(
            product_url
        )

        valid_records.append(
            normalized_record
        )

    return (
        valid_records,
        invalid_records
    )


# ---------------------------------------------------------
# JSON helper
# ---------------------------------------------------------

def save_json(file_path, data):
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    run_started = datetime.now(
        timezone.utc
    )

    start_time = time.perf_counter()

    # Reset statistics for this run.
    stats["pages_fetched"] = 0
    stats["cache_hits"] = 0
    stats["retries"] = 0

    unique_books = discover_book_urls()

    records = []
    failures = []

    print(
        "Extracting book details..."
    )

    print()

    for index, (
        product_url,
        source_page
    ) in enumerate(
        unique_books.items(),
        start=1
    ):
        try:
            record = extract_book(
                product_url,
                source_page,
                index
            )

            records.append(
                record
            )

            print(
                f"book={index}/"
                f"{len(unique_books)} "
                f"title={record['title']}"
            )

        except Exception as error:
            failure = {
                "product_url": product_url,
                "error": str(error)
            }

            failures.append(
                failure
            )

            print()
            print(
                f"FAILED: {product_url}"
            )

            print(
                f"error={error}"
            )

            print()

    # -----------------------------------------------------
    # Save raw records
    # -----------------------------------------------------

    save_json(
        RAW_OUTPUT_FILE,
        records
    )

    print()
    print(
        "Normalizing extracted records..."
    )

    # -----------------------------------------------------
    # Normalize and validate
    # -----------------------------------------------------

    valid_records, invalid_records = (
        normalize_records(records)
    )

    save_json(
        NORMALIZED_OUTPUT_FILE,
        valid_records
    )

    save_json(
        ERROR_OUTPUT_FILE,
        invalid_records
    )

    # -----------------------------------------------------
    # Run statistics
    # -----------------------------------------------------

    run_finished = datetime.now(
        timezone.utc
    )

    duration_seconds = (
        time.perf_counter()
        - start_time
    )

    run_report = {
        "started_at": run_started.isoformat(),
        "finished_at": run_finished.isoformat(),
        "duration_seconds": round(
            duration_seconds,
            3
        ),
        "catalogue_pages": 3,
        "discovered_urls": len(unique_books),
        "pages_fetched": stats["pages_fetched"],
        "cache_hits": stats["cache_hits"],
        "retries": stats["retries"],
        "detail_pages_processed": len(records),
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records),
        "failed_pages": len(failures),
        "failures": failures
    }

    save_json(
        RUN_REPORT_FILE,
        run_report
    )

    # -----------------------------------------------------
    # Console summary
    # -----------------------------------------------------

    print(
        f"detail_pages={len(records)}"
    )

    print(
        f"failed_pages={len(failures)}"
    )

    print(
        f"valid_records={len(valid_records)}"
    )

    print(
        f"invalid_records={len(invalid_records)}"
    )

    print(
        f"pages_fetched={stats['pages_fetched']}"
    )

    print(
        f"cache_hits={stats['cache_hits']}"
    )

    print(
        f"retries={stats['retries']}"
    )

    print(
        f"raw_saved_to={RAW_OUTPUT_FILE}"
    )

    print(
        f"normalized_saved_to={NORMALIZED_OUTPUT_FILE}"
    )

    print(
        f"errors_saved_to={ERROR_OUTPUT_FILE}"
    )

    print(
        f"run_report_saved_to={RUN_REPORT_FILE}"
    )

    # -----------------------------------------------------
    # Sample record
    # -----------------------------------------------------

    if valid_records:
        print()
        print(
            "SAMPLE NORMALIZED RECORD:"
        )

        print(
            json.dumps(
                valid_records[0],
                indent=2,
                ensure_ascii=False
            )
        )


if __name__ == "__main__":
    main()

