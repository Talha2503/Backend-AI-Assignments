import requests
from pathlib import Path

BASE_URL = "https://books.toscrape.com/catalogue/page-1.html"
CACHE_FILE = Path("cache/catalogue-page-1.html")

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/Talha2503/Backend-AI-Assignments)"
TIMEOUT = 10


def fetch_and_cache():
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    if CACHE_FILE.exists():
        content = CACHE_FILE.read_bytes()
        print(f"CACHE HIT: {CACHE_FILE}")
        print(f"response_size={len(content)} bytes")
        return

    headers = {
        "User-Agent": USER_AGENT
    }

    print(f"FETCH: {BASE_URL}")

    try:
        response = requests.get(
            BASE_URL,
            headers=headers,
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            print(f"FETCH FAILED: status={response.status_code}")
            return

        CACHE_FILE.write_bytes(response.content)

        print(f"FETCH SUCCESS: status={response.status_code}")
        print(f"response_size={len(response.content)} bytes")
        print(f"cached_to={CACHE_FILE}")

    except requests.RequestException as error:
        print(f"FETCH FAILED: {error}")


if __name__ == "__main__":
    fetch_and_cache()