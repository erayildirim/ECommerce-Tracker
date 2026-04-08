"""FastAPI application setup."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from config import settings
from .routes import router
from .models import HealthCheck, StatsResponse
from src.database import init_db, get_db, Product
from src.database.models import PriceHistory as DBPriceHistory


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB tables on startup; log shutdown."""
    logger.info("Starting E-Commerce Tracker API")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    yield
    logger.info("Shutting down E-Commerce Tracker API")


# ---------------------------------------------------------------------------
# OpenAPI tag metadata (drives Swagger sidebar order and descriptions)
# ---------------------------------------------------------------------------

TAGS_METADATA = [
    {
        "name": "Products",
        "description": (
            "Operations on tracked products. "
            "Retrieve paginated lists, individual product details with full price history, "
            "or create products manually."
        ),
    },
    {
        "name": "Statistics",
        "description": "Aggregated application-level metrics.",
    },
    {
        "name": "Scraping",
        "description": "Trigger and manage scraping jobs.",
    },
]


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="E-Commerce Price Tracker",
    description=(
        "## E-Commerce Price Tracker API\n\n"
        "Track product prices across e-commerce sites.\n\n"
        "### Key Features\n"
        "- **117+ products** scraped from the webscraper.io test store\n"
        "- Full **price history** per product\n"
        "- Paginated product listing with site filtering\n"
        "- PostgreSQL-backed persistence via SQLAlchemy\n\n"
        "Use the endpoints below to explore the data. "
        "The interactive docs are available at `/docs` (Swagger UI) and `/redoc`."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Core routes (health + root) — not under /api/v1 prefix
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthCheck,
    tags=["Health"],
    summary="Health check",
    description="Returns service health status and database connectivity.",
)
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unavailable"

    return HealthCheck(
        status="healthy" if db_status == "connected" else "degraded",
        database=db_status,
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "E-Commerce Price Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# ---------------------------------------------------------------------------
# Include feature routers
# ---------------------------------------------------------------------------

app.include_router(router)

