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

USER_AGENT = (
    "FlyRankInternshipA9/1.0 "
    "(+https://github.com/Talha2503/Backend-AI-Assignments)"
)

TIMEOUT = 10
DELAY = 0.5

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT
})


def fetch_page(url, cache_file):
    if cache_file.exists():
        html = cache_file.read_text(
            encoding="utf-8"
        )

        print(f"CACHE HIT: {cache_file}")
        print(
            f"response_size="
            f"{len(html.encode('utf-8'))} bytes"
        )

        return html

    print(f"FETCH: {url}")

    response = session.get(
        url,
        timeout=TIMEOUT
    )

    print(
        f"FETCH SUCCESS: status={response.status_code}"
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch {url}: "
            f"HTTP {response.status_code}"
        )

    # Books to Scrape serves UTF-8 HTML.
    # Use UTF-8 explicitly to avoid values such as Â£.
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

    print(f"cached_to={cache_file}")

    return html


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


def normalize_price(price_text):
    if not isinstance(price_text, str):
        return None

    # Handle both the correct pound sign and the
    # previously corrupted Â£ representation.
    cleaned = (
        price_text
        .replace("Â£", "")
        .replace("£", "")
        .strip()
    )

    match = re.search(
        r"\d+(?:\.\d+)?",
        cleaned
    )

    if not match:
        return None

    return float(match.group())


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

    if not isinstance(record["title"], str):
        errors.append(
            "title must be a string"
        )
    elif not record["title"].strip():
        errors.append(
            "title must not be empty"
        )

    if not isinstance(record["product_url"], str):
        errors.append(
            "product_url must be a string"
        )
    elif not record["product_url"].startswith(
        "https://"
    ):
        errors.append(
            "product_url must start with https://"
        )

    if not isinstance(record["price_text"], str):
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


def normalize_record(raw_record):
    price_gbp = normalize_price(
        raw_record.get("price_text")
    )

    normalized_record = {
        "title": raw_record.get("title"),
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

    for index, raw_record in enumerate(
        raw_records,
        start=1
    ):
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

        seen_urls.add(product_url)
        valid_records.append(
            normalized_record
        )

    return (
        valid_records,
        invalid_records
    )


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


def main():
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

            records.append(record)

            print(
                f"book={index}/{len(unique_books)} "
                f"title={record['title']}"
            )

        except Exception as error:
            failures.append({
                "product_url": product_url,
                "error": str(error)
            })

            print(
                f"FAILED: {product_url}"
            )

            print(
                f"error={error}"
            )

    save_json(
        RAW_OUTPUT_FILE,
        records
    )

    print()
    print(
        "Normalizing extracted records..."
    )

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
        f"raw_saved_to={RAW_OUTPUT_FILE}"
    )

    print(
        f"normalized_saved_to={NORMALIZED_OUTPUT_FILE}"
    )

    print(
        f"errors_saved_to={ERROR_OUTPUT_FILE}"
    )

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