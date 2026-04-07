"""API routes and endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from .models import (
    ProductResponse,
    ProductCreate,
    PriceHistory,
    ScrapingRequest,
    ScrapingResponse
)
from src.database import get_db, Product
from src.database.models import PriceHistory as DBPriceHistory


router = APIRouter(prefix="/api/v1", tags=["products"])


@router.post("/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """Create a new product record."""
    db_product = Product(
        product_name=product.product_name,
        price=product.price,
        url=str(product.url),
        currency=product.currency,
        stock_status=product.stock_status,
        description=product.description,
        site_name="manual"
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    site_name: str = Query(None),
    db: Session = Depends(get_db)
):
    """List all products with optional filtering."""
    query = db.query(Product)
    
    if site_name:
        query = query.filter(Product.site_name == site_name)
    
    products = query.offset(skip).limit(limit).all()
    return products


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.get("/products/{product_id}/price-history", response_model=List[PriceHistory])
async def get_price_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get price history for a product in the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    history = (
        db.query(DBPriceHistory)
        .filter(
            DBPriceHistory.product_id == product_id,
            DBPriceHistory.recorded_at >= cutoff
        )
        .order_by(DBPriceHistory.recorded_at.desc())
        .all()
    )
    return history


@router.post("/scraping/batch", response_model=ScrapingResponse)
async def start_scraping(
    request: ScrapingRequest
):
    """Start batch scraping job."""
    # Placeholder for scraping orchestration
    # In production, this would trigger background tasks or queue jobs
    
    response = ScrapingResponse(
        site_name=request.site_name,
        total_requested=len(request.product_urls),
        successfully_scraped=0,
        failed_count=0,
        results=[],
        timestamp=datetime.now(timezone.utc)
    )
    return response


@router.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Get application statistics."""
    total_products = db.query(Product).count()
    sites_count = db.query(Product.site_name).distinct().count()
    
    return {
        "total_products": total_products,
        "total_sites_tracked": sites_count,
        "timestamp": datetime.now(timezone.utc)
    }
