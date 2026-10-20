# Enterprise Web Scraping Pipeline – Books Data Engineering System

## Project Overview
A modular data engineering pipeline built with Scrapy to extract, clean, validate, and persist book catalog data from [Books to Scrape](https://books.toscrape.com/index.html). The system dynamically discovers product categories, performs two-stage random sampling across paginated catalogs, normalizes records via item pipelines, exports datasets into multiple formats (`JSON`, `CSV`, `XML`), persists records in `SQLite`, and deploys inside a Dockerized `Scrapyd` service.

## Features
- **Zero-Hardcoding Discovery:** Dynamically extracts all category names and URLs from the target site's navigation tree.
- **Two-Stage Random Sampling:** Selects 5–10 random categories per run and crawls all pagination links before randomly sampling 5 books per category.
- **Data Cleaning & Validation Pipeline:** Strips whitespace, normalizes text, parses floating-point prices, and converts stock availability into boolean flags.
- **Multi-Format Exports & DB Persistence:** Outputs identical, cleaned records simultaneously to `books.json`, `books.csv`, `books.xml`, and a relational `SQLite` database (`books.db`).
- **Automated Container Deployment:** Packaged with Docker and an entrypoint workflow that initializes `Scrapyd` and auto-deploys the spider on startup.

## Tech Stack
- **Language:** Python 3.11
- **Scraping Framework:** Scrapy 2.11
- **Database:** SQLite3
- **Deployment & Scheduling:** Scrapyd 1.4 & scrapyd-client 1.2
- **Containerization:** Docker & Docker Compose

## Architecture Diagram

```text
+-------------------------------------------------------------------+
|                        BooksSpider (Scrapy)                       |
|  1. Crawl Homepage -> Discover All Categories Dynamically         |
|  2. Sample 5-10 Categories -> Crawl All Category Pagination Pages |
|  3. Sample 5 Books/Category -> Extract Raw Book Attributes        |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                   CleaningPipeline (Priority 300)                 |
|  - Trim & normalize strings                                       |
|  - Strip currency symbols & cast price to float                   |
|  - Normalize availability ("In stock" -> True, else False)        |
+-------------------------------------------------------------------+
                 |                                 |
                 v                                 v
+---------------------------------+ +-------------------------------+
|  SQLitePipeline (Priority 400)  | |      Scrapy Feed Exports      |
|  - Persist to data/books.db     | |  - data/books.json            |
|  - Enforce schema & uniqueness  | |  - data/books.csv             |
+---------------------------------+ |  - data/books.xml             |
                                    +-------------------------------+
```

## Folder Structure
```text
books_pipeline/
├── books_scraper/
│   ├── __init__.py
│   ├── items.py           # Data model definitions
│   ├── middlewares.py     # Spider/Downloader middlewares
│   ├── pipelines.py       # Cleaning and SQLite storage pipelines
│   ├── selectors.py       # Decoupled CSS selectors
│   ├── settings.py        # Scrapy, Feed Export, and DB configurations
│   └── spiders/
│       ├── __init__.py
│       └── books_spider.py # Core crawling & sampling logic
├── data/                  # Output directory for JSON, CSV, XML, and SQLite DB
├── Dockerfile             # Container image definition
├── docker-compose.yml     # Container orchestration & volume mounting
├── entrypoint.sh          # Automated Scrapyd startup and egg deployment
├── requirements.txt       # Python dependencies
├── scrapyd.conf           # Scrapyd daemon configuration
├── scrapy.cfg             # Project & deployment target configuration
└── README.md              # Documentation
```

## Installation & Environment Setup (Local)

1. **Clone the repository and navigate to the project root:**
   ```bash
   git clone https://github.com/oneakash/web_scrapping_books.git
   cd web_scrapping_books
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Spider Locally
Execute the spider directly via the Scrapy CLI:
```bash
scrapy crawl books
```
Upon completion, inspect the `data/` directory for `books.json`, `books.csv`, `books.xml`, and `books.db`.

## Docker Setup Guide
The application is fully containerized and requires no manual configuration inside the container.

1. **Build and start the container:**
   ```bash
   docker compose up --build -d
   ```
2. **Verify the container and Scrapyd daemon status:**
   ```bash
   curl http://localhost:6800/daemonstatus.json
   ```
   Expected response:
   ```json
   {"node_name": "...", "status": "ok", "pending": 0, "running": 0, "finished": 0}
   ```

## Scrapyd Deployment & Execution Guide

When using Docker, `entrypoint.sh` automatically deploys the project to Scrapyd on container startup.

### Manual Deployment (Local Host without Docker)
If running Scrapyd locally outside Docker:
1. Start Scrapyd in one terminal: `scrapyd`
2. Deploy the project in another terminal:
   ```bash
   scrapyd-deploy local -p books_scraper
   ```

### Triggering the Spider via Scrapyd API
1. **Schedule a spider run:**
   ```bash
   curl http://localhost:6800/schedule.json -d project=books_scraper -d spider=books
   ```
   Response:
   ```json
   {"node_name": "...", "status": "ok", "jobid": "6487ec79947edab326d6db28a2d86511e8247444"}
   ```

2. **Monitor job status:**
   ```bash
   curl http://localhost:6800/listjobs.json?project=books_scraper
   ```
   Or view the web interface at `http://localhost:6800`.

## Output Format Description
All exported files (`data/books.json`, `data/books.csv`, `data/books.xml`) contain the exact same processed fields:

| Field | Type | Example |
| :--- | :--- | :--- |
| `title` | `string` | `"Sharp Objects"` |
| `price` | `float` | `47.82` |
| `availability` | `boolean` | `true` |
| `product_url` | `string` | `"https://books.toscrape.com/catalogue/sharp-objects_997/index.html"` |
| `image_url` | `string` | `"https://books.toscrape.com/media/cache/32/51/3251cf3a3412f53f339e42cac2134093.jpg"` |
| `category` | `string` | `"Mystery"` |

## Database Configuration
By default, the project uses `SQLite` located at `data/books.db` (configurable via the `DATA_DIR` environment variable in `settings.py`).

To verify database contents after a crawl:
```bash
sqlite3 data/books.db "SELECT category, COUNT(*), ROUND(AVG(price), 2) FROM books GROUP BY category;"
```

## Design Decisions
- **Decoupled Selectors (`selectors.py`):** Isolates DOM structure dependencies from crawling logic. If the target website updates its HTML classes, only `selectors.py` requires modification.
- **Full Pagination Traversal Before Sampling:** Several categories span multiple pages. Rather than sampling only from page 1, `parse_category` traverses all pagination links first to ensure uniform random sampling across the entire category catalog.
- **Pipeline Ordering for Data Consistency:** `CleaningPipeline` runs at priority `300` and mutates the item in place before `SQLitePipeline` (`400`) and Scrapy's `FeedExporter` receive it, guaranteeing 100% parity between exported files and database rows.

## Known Limitations
- **Small Categories on Target Website:** Certain categories on `books.toscrape.com` contain fewer than 5 books in total (e.g., *Paranormal* has 1 book, *Adult Fiction* has 1 book). The spider handles this gracefully using `min(5, len(collected_urls))` so `random.sample()` never raises a `ValueError`.
- **Single-Writer SQLite Concurrency:** SQLite locks the database file during writes. While sufficient for single-spider runs, high-concurrency distributed crawls should swap `SQLitePipeline` for a client-server database pipeline (e.g., PostgreSQL or MongoDB).