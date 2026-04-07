"""Unit tests for scraper module."""

import pytest
import asyncio
from datetime import datetime
from src.scraper import BaseScraper, DataValidator, TestStoreScraper
from src.scraper.validators import ValidationError


class TestDataValidator:
    """Test data validation utilities."""
    
    def test_validate_product_name_valid(self):
        """Test valid product name."""
        assert DataValidator.validate_product_name("iPhone 15 Pro") is True
    
    def test_validate_product_name_too_short(self):
        """Test product name too short."""
        assert DataValidator.validate_product_name("ab") is False
    
    def test_validate_price_valid(self):
        """Test valid price."""
        assert DataValidator.validate_price(99.99) is True
        assert DataValidator.validate_price("99.99") is True
    
    def test_validate_price_negative(self):
        """Test negative price."""
        assert DataValidator.validate_price(-10.0) is False
    
    def test_validate_url_valid(self):
        """Test valid URL."""
        assert DataValidator.validate_url("https://example.com/product/123") is True
    
    def test_validate_url_invalid(self):
        """Test invalid URL."""
        assert DataValidator.validate_url("not-a-url") is False
    
    def test_validate_product_missing_fields(self):
        """Test product validation with missing fields."""
        data = {
            "product_name": "Test Product",
            "price": 99.99
        }
        
        with pytest.raises(ValidationError):
            DataValidator.validate_product(data)
    
    def test_validate_product_invalid_price(self):
        """Test product validation with invalid price."""
        data = {
            "product_name": "Test Product",
            "price": "invalid",
            "url": "https://example.com",
            "scraped_at": "2024-01-01T00:00:00"
        }
        
        with pytest.raises(ValidationError):
            DataValidator.validate_product(data)
    
    def test_sanitize_price(self):
        """Test price sanitization."""
        assert DataValidator.sanitize_price(99.99) == 99.99
        assert DataValidator.sanitize_price("$99.99") == 99.99
        assert DataValidator.sanitize_price("$99,99") == 9999.0
    
    def test_sanitize_price_with_currency_symbols(self):
        """Test price sanitization with various currency symbols."""
        assert DataValidator.sanitize_price("€199.99") == 199.99
        assert DataValidator.sanitize_price("£149.99") == 149.99
        assert DataValidator.sanitize_price("¥10000") == 10000.0
    
    def test_validate_stock_status(self):
        """Test stock status validation."""
        assert DataValidator.validate_stock_status("in_stock") is True
        assert DataValidator.validate_stock_status("out_of_stock") is True
        assert DataValidator.validate_stock_status("invalid") is False
        assert DataValidator.validate_stock_status(None) is True  # Allow None
    
    def test_validate_batch_all_valid(self):
        """Test batch validation with all valid products."""
        products = [
            {
                "product_name": "Product 1",
                "price": 99.99,
                "url": "https://example.com/1",
                "scraped_at": "2024-01-01T00:00:00"
            },
            {
                "product_name": "Product 2",
                "price": 199.99,
                "url": "https://example.com/2",
                "scraped_at": "2024-01-01T00:00:00"
            }
        ]
        
        valid, invalid = DataValidator.validate_batch(products)
        
        assert len(valid) == 2
        assert len(invalid) == 0
    
    def test_validate_batch_mixed(self):
        """Test batch validation with mixed valid and invalid products."""
        products = [
            {
                "product_name": "Valid Product",
                "price": 99.99,
                "url": "https://example.com/1",
                "scraped_at": "2024-01-01T00:00:00"
            },
            {
                "product_name": "X",  # Too short
                "price": 199.99,
                "url": "https://example.com/2",
                "scraped_at": "2024-01-01T00:00:00"
            },
            {
                "product_name": "Another Valid",
                "price": 299.99,
                "url": "https://example.com/3",
                "scraped_at": "2024-01-01T00:00:00"
            }
        ]
        
        valid, invalid = DataValidator.validate_batch(products)
        
        assert len(valid) == 2
        assert len(invalid) == 1
        assert invalid[0]["error"] == "Invalid product name"


class TestTestStoreScraper:
    """Test TestStoreScraper implementation."""
    
    def test_scraper_initialization(self):
        """Test TestStoreScraper initialization."""
        scraper = TestStoreScraper()
        
        assert scraper.site_name == "teststore"
        assert scraper.base_url == "https://webscraper.io/test-sites/e-commerce/allinone"
        assert scraper.max_retries == 3
        assert scraper.timeout == 60  # Updated to match SCRAPER_TIMEOUT=60000ms
    
    def test_scraper_logging(self):
        """Test scraper has proper logging setup."""
        scraper = TestStoreScraper()
        
        assert scraper.logger is not None
        assert scraper.logger.name == "scraper.teststore"
    
    @pytest.mark.asyncio
    async def test_validate_data_valid(self):
        """Test validate_data with valid data."""
        scraper = TestStoreScraper()
        
        valid_data = {
            "products": [
                {
                    "product_name": "Test Product",
                    "price": 99.99,
                    "url": "https://example.com"
                }
            ],
            "url": "https://example.com",
            "total_products": 1
        }
        
        result = await scraper.validate_data(valid_data)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_data_empty_products(self):
        """Test validate_data with empty products list."""
        scraper = TestStoreScraper()
        
        invalid_data = {
            "products": [],
            "url": "https://example.com",
            "total_products": 0
        }
        
        result = await scraper.validate_data(invalid_data)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_data_missing_products_key(self):
        """Test validate_data with missing products key."""
        scraper = TestStoreScraper()
        
        invalid_data = {
            "url": "https://example.com",
            "total_products": 1
        }
        
        result = await scraper.validate_data(invalid_data)
        assert result is False
    
    def test_scraper_inheritance(self):
        """Test TestStoreScraper inherits from BaseScraper."""
        scraper = TestStoreScraper()
        assert isinstance(scraper, BaseScraper)
    
    def test_scraper_has_required_methods(self):
        """Test scraper has all required async methods."""
        scraper = TestStoreScraper()
        
        assert hasattr(scraper, 'scrape')
        assert hasattr(scraper, 'validate_data')
        assert hasattr(scraper, 'scrape_with_retry')
        assert hasattr(scraper, 'scrape_batch')
        assert hasattr(scraper, 'scrape_and_validate')
        assert callable(scraper.scrape)
        assert callable(scraper.validate_data)

