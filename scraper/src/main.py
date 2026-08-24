import os
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"
PAGE_1_URL = urljoin(BASE_URL, "catalogue/page-1.html")

CACHE_DIR = "cache"
CATALOGUE_CACHE_DIR = os.path.join(CACHE_DIR, "catalogue")

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/Talha2503/Backend-AI-Assignments)"
TIMEOUT = 10
DELAY = 0.5


def ensure_directories():
    os.makedirs(CATALOGUE_CACHE_DIR, exist_ok=True)


def fetch_or_cache(url, cache_path):
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as file:
            content = file.read()

        print(f"CACHE HIT: {cache_path}")
        print(f"response_size={len(content.encode('utf-8'))} bytes")
        return content

    print(f"FETCH: {url}")

    headers = {
        "User-Agent": USER_AGENT
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=TIMEOUT
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch {url}: HTTP {response.status_code}"
        )

    content = response.text

    print(f"FETCH SUCCESS: status={response.status_code}")
    print(f"response_size={len(response.content)} bytes")

    with open(cache_path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"cached_to={cache_path}")

    time.sleep(DELAY)

    return content


def get_catalogue_page_url(page_number):
    return urljoin(
        BASE_URL,
        f"catalogue/page-{page_number}.html"
    )


def extract_book_links(html, page_url):
    soup = BeautifulSoup(html, "html.parser")

    book_links = []

    for article in soup.select("article.product_pod"):
        link = article.select_one("h3 a")

        if link and link.get("href"):
            absolute_url = urljoin(
                page_url,
                link["href"]
            )

            book_links.append(absolute_url)

    return book_links


def find_next_page(html, current_url):
    soup = BeautifulSoup(html, "html.parser")

    next_link = soup.select_one("li.next a")

    if not next_link or not next_link.get("href"):
        return None

    return urljoin(
        current_url,
        next_link["href"]
    )


def main():
    ensure_directories()

    all_book_urls = []
    current_url = PAGE_1_URL

    for page_number in range(1, 4):
        cache_path = os.path.join(
            CATALOGUE_CACHE_DIR,
            f"catalogue-page-{page_number}.html"
        )

        html = fetch_or_cache(
            current_url,
            cache_path
        )

        book_links = extract_book_links(
            html,
            current_url
        )

        all_book_urls.extend(book_links)

        print(
            f"page={page_number} "
            f"books_found={len(book_links)}"
        )

        if page_number < 3:
            next_url = find_next_page(
                html,
                current_url
            )

            if not next_url:
                raise RuntimeError(
                    f"Could not find next page after {current_url}"
                )

            current_url = next_url

    unique_urls = list(dict.fromkeys(all_book_urls))

    print()
    print(f"catalogue_pages=3")
    print(f"discovered={len(all_book_urls)}")
    print(f"unique_urls={len(unique_urls)}")


if __name__ == "__main__":
    main()