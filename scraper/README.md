# The Polite Scraper

## Target Classification

### Target

Books to Scrape:

https://books.toscrape.com/

### Why this target?

Books to Scrape is a public practice sandbox created for learning and practicing web scraping.

### Scope

This project will scrape only the first 3 catalogue pages and discover the 60 books listed across those pages.

### Data collected

For each book, the scraper will collect:

- Title
- Product URL
- Price text
- Availability text
- Rating text
- Description
- Source catalogue page
- Fetch timestamp

### Robots.txt

Robots.txt was checked before writing the scraper.

Result:

No robots file found. Requesting https://books.toscrape.com/robots.txt returned 404 Not Found.

### Responsible scraping

This project uses Books to Scrape because it is specifically provided as a practice sandbox.

The scraper will use:

- An identifying User-Agent
- Request timeouts
- Caching
- A delay of at least 500 ms between real requests

I will not reuse this code on another site without checking its rules and terms first.