"""API routes and endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from .models import (
    ProductResponse,
    ProductDetailResponse,
    ProductCreate,
    PriceHistoryResponse,
    PaginatedProductResponse,
    StatsResponse,
    ScrapingRequest,
    ScrapingResponse,
)
from src.database import get_db, Product
from src.database.models import PriceHistory as DBPriceHistory


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

products_router = APIRouter(prefix="/api/v1/products", tags=["Products"])
stats_router = APIRouter(prefix="/api/v1", tags=["Statistics"])
scraping_router = APIRouter(prefix="/api/v1/scraping", tags=["Scraping"])


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@products_router.get(
    "",
    response_model=PaginatedProductResponse,
    summary="List products",
    description=(
        "Returns a paginated list of all tracked products. "
        "Use `skip` and `limit` for pagination and `site_name` to filter by source."
    ),
    response_description="Paginated product list",
)
async def list_products(
    skip: int = Query(0, ge=0, description="Number of records to skip (offset)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return (1–100)"),
    site_name: Optional[str] = Query(None, description="Filter by site identifier, e.g. `teststore`"),
    db: Session = Depends(get_db),
):
    query = db.query(Product)

    if site_name:
        query = query.filter(Product.site_name == site_name)

    total = query.count()
    items = query.order_by(Product.id).offset(skip).limit(limit).all()

    return {"total": total, "skip": skip, "limit": limit, "items": items}


@products_router.get(
    "/{product_id}",
    response_model=ProductDetailResponse,
    summary="Get product with full price history",
    description=(
        "Returns detailed information for a single product including its **complete** "
        "price history from the `price_history` table, ordered from newest to oldest."
    ),
    response_description="Product detail with price history",
    responses={404: {"description": "Product not found"}},
)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .options(selectinload(Product.price_history))
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id={product_id} not found")

    # Sort price history newest-first
    product.price_history.sort(key=lambda ph: ph.recorded_at, reverse=True)
    return product


@products_router.get(
    "/{product_id}/price-history",
    response_model=List[PriceHistoryResponse],
    summary="Get filtered price history",
    description=(
        "Returns price snapshots for a single product within the last `days` days, "
        "ordered from newest to oldest."
    ),
    response_description="List of price-history entries",
    responses={404: {"description": "Product not found"}},
)
async def get_price_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Look-back window in days (1–365)"),
    db: Session = Depends(get_db),
):
    # Verify product exists
    if not db.query(Product).filter(Product.id == product_id).first():
        raise HTTPException(status_code=404, detail=f"Product with id={product_id} not found")

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    history = (
        db.query(DBPriceHistory)
        .filter(
            DBPriceHistory.product_id == product_id,
            DBPriceHistory.recorded_at >= cutoff,
        )
        .order_by(DBPriceHistory.recorded_at.desc())
        .all()
    )
    return history


@products_router.post(
    "",
    response_model=ProductResponse,
    status_code=201,
    summary="Create product",
    description="Manually insert a product record. `site_name` is set to `manual`.",
    response_description="Newly created product",
)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
):
    db_product = Product(
        product_name=product.product_name,
        price=product.price,
        url=str(product.url),
        currency=product.currency,
        stock_status=product.stock_status,
        description=product.description,
        site_name="manual",
        scraped_at=datetime.now(timezone.utc),
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

@stats_router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Application statistics",
    description="Returns product counts, distinct sites tracked and total price-history snapshots.",
    response_description="Aggregated statistics",
)
async def get_statistics(db: Session = Depends(get_db)):
    total_products = db.query(func.count(Product.id)).scalar() or 0
    sites_count = db.query(func.count(func.distinct(Product.site_name))).scalar() or 0
    total_price_records = db.query(func.count(DBPriceHistory.id)).scalar() or 0

    return StatsResponse(
        total_products=total_products,
        total_sites_tracked=sites_count,
        total_price_records=total_price_records,
        timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Scraping (placeholder)
# ---------------------------------------------------------------------------

@scraping_router.post(
    "/batch",
    response_model=ScrapingResponse,
    summary="Trigger a batch scraping job",
    description=(
        "Enqueues a batch scraping job for the given URLs. "
        "In the current implementation this returns an accepted response immediately; "
        "actual processing would be handled by a background worker."
    ),
    response_description="Job acknowledgement",
)
async def start_scraping(request: ScrapingRequest):
    return ScrapingResponse(
        site_name=request.site_name,
        total_requested=len(request.product_urls),
        successfully_scraped=0,
        failed_count=0,
        results=[],
        timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Aggregate router (imported by main.py)
# ---------------------------------------------------------------------------

router = APIRouter()
router.include_router(products_router)
router.include_router(stats_router)
router.include_router(scraping_router)
