"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional, List


class ProductCreate(BaseModel):
    """Product creation request model."""

    product_name: str = Field(..., min_length=3, max_length=500, description="Product display name")
    price: float = Field(..., gt=0, description="Current price")
    url: HttpUrl = Field(..., description="Unique product page URL")
    currency: str = Field(default="USD", max_length=3, description="ISO 4217 currency code")
    stock_status: str = Field(default="unknown", description="Stock availability status")
    description: Optional[str] = Field(default=None, description="Product description")

    model_config = {
        "json_schema_extra": {
            "example": {
                "product_name": "iPhone 15 Pro",
                "price": 999.99,
                "url": "https://example.com/product/iphone-15",
                "currency": "USD",
                "stock_status": "in_stock",
            }
        }
    }


class PriceHistoryResponse(BaseModel):
    """Single price-history entry returned by the API."""

    id: int = Field(..., description="Unique record ID")
    product_id: int = Field(..., description="Parent product ID")
    price: float = Field(..., description="Recorded price")
    currency: str = Field(..., description="ISO 4217 currency code")
    recorded_at: datetime = Field(..., description="UTC timestamp of this price snapshot")

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    """Product list-view response (no price history)."""

    id: int = Field(..., description="Unique product ID")
    product_name: str = Field(..., description="Product display name")
    price: float = Field(..., description="Current price")
    url: str = Field(..., description="Product page URL")
    currency: str = Field(..., description="ISO 4217 currency code")
    stock_status: str = Field(..., description="Stock availability status")
    site_name: str = Field(..., description="Source site identifier")
    description: Optional[str] = Field(default=None, description="Product description")
    scraped_at: Optional[datetime] = Field(default=None, description="UTC timestamp of last scrape")
    created_at: datetime = Field(..., description="UTC timestamp of first insert")
    updated_at: datetime = Field(..., description="UTC timestamp of last update")

    model_config = {"from_attributes": True}


class ProductDetailResponse(ProductResponse):
    """Product detail-view response — includes the full price history."""

    price_history: List[PriceHistoryResponse] = Field(
        default_factory=list,
        description="All recorded price snapshots for this product",
    )

    model_config = {"from_attributes": True}


class PaginatedProductResponse(BaseModel):
    """Wrapper for paginated product list responses."""

    total: int = Field(..., description="Total number of matching products")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum records returned in this page")
    items: List[ProductResponse] = Field(..., description="Product records for this page")


class HealthCheck(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service health status")
    database: str = Field(..., description="Database connection status")
    timestamp: datetime = Field(..., description="UTC timestamp of this check")


class StatsResponse(BaseModel):
    """Application statistics response."""

    total_products: int = Field(..., description="Total products tracked")
    total_sites_tracked: int = Field(..., description="Number of distinct sites")
    total_price_records: int = Field(..., description="Total price-history snapshots stored")
    timestamp: datetime = Field(..., description="UTC timestamp of this report")


class ScrapingRequest(BaseModel):
    """Scraping request model."""

    site_name: str = Field(..., description="Target site identifier")
    product_urls: List[str] = Field(..., min_length=1, max_length=100, description="URLs to scrape")

    model_config = {
        "json_schema_extra": {
            "example": {
                "site_name": "teststore",
                "product_urls": [
                    "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"
                ],
            }
        }
    }


class ScrapingResponse(BaseModel):
    """Scraping job response."""

    site_name: str
    total_requested: int
    successfully_scraped: int
    failed_count: int
    results: List[ProductResponse]
    timestamp: datetime
