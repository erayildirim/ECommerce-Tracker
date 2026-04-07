"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional, List


class ProductCreate(BaseModel):
    """Product creation request model."""
    
    product_name: str = Field(..., min_length=3, max_length=500)
    price: float = Field(..., gt=0)
    url: HttpUrl
    currency: str = Field(default="USD", max_length=3)
    stock_status: str = Field(default="unknown")
    description: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "iPhone 15 Pro",
                "price": 999.99,
                "url": "https://example.com/product/iphone-15",
                "currency": "USD",
                "stock_status": "in_stock"
            }
        }


class ProductResponse(BaseModel):
    """Product response model."""
    
    id: int
    product_name: str
    price: float
    url: str
    currency: str
    stock_status: str
    site_name: str
    description: Optional[str]
    scraped_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PriceHistory(BaseModel):
    """Price history entry."""
    
    product_id: int
    price: float
    currency: str
    recorded_at: datetime
    
    class Config:
        from_attributes = True


class HealthCheck(BaseModel):
    """Health check response model."""
    
    status: str
    database: str
    timestamp: datetime


class ScrapingRequest(BaseModel):
    """Scraping request model."""
    
    site_name: str
    product_urls: List[str] = Field(..., min_items=1, max_items=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "site_name": "amazon",
                "product_urls": [
                    "https://amazon.com/dp/B0C5NNJXQZ"
                ]
            }
        }


class ScrapingResponse(BaseModel):
    """Scraping response model."""
    
    site_name: str
    total_requested: int
    successfully_scraped: int
    failed_count: int
    results: List[ProductResponse]
    timestamp: datetime
