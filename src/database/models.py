"""SQLAlchemy models for database."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .connection import Base


class Product(Base):
    """Product data model."""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(500), nullable=False, index=True)
    price = Column(Float, nullable=False)
    url = Column(String(2000), unique=True, nullable=False, index=True)
    currency = Column(String(3), default="USD")
    stock_status = Column(String(50), default="unknown")
    description = Column(Text, nullable=True)
    site_name = Column(String(100), nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scraped_at = Column(DateTime, nullable=True)
    
    # Relationships
    price_history = relationship(
        "PriceHistory",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.product_name}, price={self.price})>"


class PriceHistory(Base):
    """Price history tracking model."""
    
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    product = relationship("Product", back_populates="price_history")
    
    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, price={self.price})>"


class ScrapingJob(Base):
    """Scraping job tracking model."""
    
    __tablename__ = "scraping_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    site_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    total_urls = Column(Integer, nullable=False)
    successful_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ScrapingJob(id={self.id}, site={self.site_name}, status={self.status})>"
