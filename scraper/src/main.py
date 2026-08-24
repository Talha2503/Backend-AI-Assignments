import json
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

    response.encoding = response.apparent_encoding
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
                f"book={index}/60 "
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

    output_file = (
        Path("output")
        / "raw-books.json"
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file.write_text(
        json.dumps(
            records,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print()
    print(
        f"detail_pages={len(records)}"
    )

    print(
        f"failed_pages={len(failures)}"
    )

    print(
        f"saved_to={output_file}"
    )

    if records:
        print()
        print(
            "SAMPLE RAW RECORD:"
        )

        print(
            json.dumps(
                records[0],
                indent=2,
                ensure_ascii=False
            )
        )


if __name__ == "__main__":
    main()