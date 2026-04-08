# E-Commerce Price Tracker

A production-ready e-commerce price tracking system built with **FastAPI**, **PostgreSQL**, and **Playwright**. It scrapes product listings from multiple sites, records every price change in a dedicated history table, and exposes the data through a fully-documented REST API.

---

## Features

- **Multi-site scraper architecture** — pluggable `BaseScraper` class makes adding new sites straightforward
- **Stealth scraping** — Amazon Turkey scraper uses playwright-stealth, rotating user-agents, scroll simulation, random jitter delays, and captcha detection
- **Price history tracking** — every price change is automatically recorded; unchanged prices are skipped
- **Smart upsert logic** — inserts new products, updates on price change, skips identical records
- **REST API** — FastAPI with auto-generated Swagger UI (`/docs`) and ReDoc (`/redoc`)
- **Paginated endpoints** — filterable product listing, per-product price history with date range
- **Dockerized** — single `docker compose up` starts PostgreSQL and the API server
- **Config-driven** — all settings managed through a `.env` file with Pydantic v2 type validation

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI 0.104, Uvicorn, Pydantic v2 |
| Database | PostgreSQL 15, SQLAlchemy 2.0, psycopg2 |
| Scraping | Playwright 1.40, playwright-stealth, fake-useragent |
| Configuration | pydantic-settings, python-dotenv |
| Containerisation | Docker, Docker Compose |
| Testing | pytest, pytest-asyncio |

---

## Project Structure

```
E-Commerce Tracker/
├── src/
│   ├── api/
│   │   ├── main.py          # FastAPI app, CORS middleware, lifespan hooks
│   │   ├── routes.py        # Endpoint handlers (products, stats, scraping)
│   │   └── models.py        # Pydantic request/response schemas
│   ├── database/
│   │   ├── connection.py    # SQLAlchemy engine & session factory
│   │   ├── models.py        # ORM models: Product, PriceHistory
│   │   └── schema.sql       # SQL schema (auto-applied by Docker on first boot)
│   └── scraper/
│       ├── base.py          # Abstract BaseScraper with retry logic
│       ├── scrapers.py      # TestStoreScraper, AmazonTRScraper
│       └── validators.py    # DataValidator helpers
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_scraper.py
├── save_to_db.py            # CLI scrape-and-save pipeline
├── main.py                  # Local dev entry point
├── config.py                # Pydantic Settings model
├── docker-compose.yml       # PostgreSQL + API services
├── Dockerfile               # API image (Python 3.12-slim + Chromium)
├── requirements.txt
└── .env.example
```

---

## Prerequisites

- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** — recommended; no local Python needed for the API
- **Python 3.12+** — required to run scrapers locally

---

## Quick Start — Docker

```bash
# 1. Clone the repository
git clone <repo-url>
cd "E-Commerce Tracker"

# 2. Create your environment file
copy .env.example .env
#    → open .env and set DB_PASSWORD to something secure

# 3. Build and start all services (PostgreSQL + API)
docker compose up --build -d

# 4. Verify the API is running
curl http://localhost:8000/health

# 5. Open interactive API docs
start http://localhost:8000/docs
```

> PostgreSQL listens on **host port 5433** (mapped to container port 5432).  
> The API listens on **host port 8000**.

---

## Local Development Setup

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install the Playwright Chromium browser
playwright install chromium

# 4. Copy and configure the environment file
copy .env.example .env
#    Set DB_HOST=localhost, DB_PORT=5433 to reach the Docker Postgres

# 5. Start only the database
docker compose up postgres -d

# 6. Run the API with hot-reload
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Running the Scrapers

All scraping is done through the `save_to_db.py` CLI:

```powershell
# Demo store — webscraper.io test site (117 laptops, no anti-bot measures)
python save_to_db.py --site test

# Amazon Turkey — laptop search (default URL)
python save_to_db.py --site amazon_tr

# Amazon Turkey — custom search keyword
python save_to_db.py --site amazon_tr --url "https://www.amazon.com.tr/s?k=telefon"
```

**Upsert behaviour per run:**

| Situation | Action |
|---|---|
| Product URL not in DB | INSERT + create initial price history row |
| URL exists, price changed | UPDATE product + append price history row |
| URL exists, price unchanged | Skip (no write) |

---

## API Reference

Interactive docs at **`/docs`** (Swagger UI) and **`/redoc`** (ReDoc).

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness + DB connectivity check |
| `GET` | `/api/v1/products` | Paginated list (`skip`, `limit`, `site_name` filter) |
| `GET` | `/api/v1/products/{id}` | Single product with full price history |
| `GET` | `/api/v1/products/{id}/price-history` | Price history filtered by `days` look-back |
| `POST` | `/api/v1/products` | Manually insert a product record |
| `GET` | `/api/v1/stats` | Counts: products, sites tracked, price snapshots |

---

## Configuration Reference

Copy `.env.example` → `.env`. Inside Docker, use `DB_HOST=postgres`; for local dev against a Docker Postgres use `DB_HOST=localhost`.

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `localhost` | PostgreSQL hostname |
| `DB_PORT` | `5433` | PostgreSQL port (host-side) |
| `DB_USER` | `ecommerce_user` | Database user |
| `DB_PASSWORD` | — | Database password **(required)** |
| `DB_NAME` | `ecommerce_tracker` | Database name |
| `API_HOST` | `0.0.0.0` | FastAPI bind address |
| `API_PORT` | `8000` | FastAPI port |
| `DEBUG` | `False` | FastAPI debug mode |
| `PLAYWRIGHT_HEADLESS` | `True` | Headless browser (`False` shows the browser window) |
| `SCRAPER_TIMEOUT` | `60000` | Navigation timeout in milliseconds |
| `RETRY_ATTEMPTS` | `3` | Max retries per failed scrape |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FILE` | `logs/app.log` | Log file path |

---

## Running Tests

```powershell
pytest tests/ -v
```

---

## Amazon Turkey Scraper — Anti-Detection Details

The `amazon_tr` scraper stacks multiple evasion layers:

| Layer | Detail |
|---|---|
| **playwright-stealth** | Patches `navigator.webdriver`, WebGL fingerprint, and dozens of other signals |
| **Rotating user-agents** | `fake-useragent` picks a realistic Chrome/Firefox/Edge UA per request |
| **Random jitter** | 2–6 s sleep before navigation; 1–3 s after scroll |
| **Scroll simulation** | Page is scrolled down in 10 increments before extraction |
| **Turkish browser profile** | `Accept-Language: tr-TR`, Google Turkey referer header, `locale=tr-TR`, `timezone=Europe/Istanbul` |
| **Captcha detection** | Title checked for block/survey strings → `CRITICAL` log if triggered |
| **Multi-fallback selectors** | 4–5 CSS selectors tried per field (name, price, URL); first match wins |

If 0 products are extracted despite cards being found, set `LOG_LEVEL=DEBUG` — the scraper logs the first 500 characters of the first card's HTML for diagnosis.