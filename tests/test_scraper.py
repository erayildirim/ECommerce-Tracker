"""Unit tests for scraper module."""

import pytest
from src.scraper import BaseScraper, DataValidator
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
