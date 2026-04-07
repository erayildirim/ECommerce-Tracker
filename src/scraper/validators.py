"""Data validation utilities for scraped content."""

from typing import Dict, Any, List, Optional
import re
import logging
from decimal import Decimal


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


class DataValidator:
    """Validates scraped e-commerce product data for accuracy and completeness."""
    
    # Required fields for product data
    REQUIRED_FIELDS = {
        "product_name",
        "price",
        "url",
        "scraped_at"
    }
    
    # Price validation regex
    PRICE_PATTERN = re.compile(r'^\d+\.?\d*$')
    
    @classmethod
    def validate_product(cls, data: Dict[str, Any]) -> bool:
        """
        Validate product data completeness and format.
        
        Args:
            data: Product data dictionary
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        # Check required fields
        missing_fields = cls.REQUIRED_FIELDS - set(data.keys())
        if missing_fields:
            raise ValidationError(f"Missing required fields: {missing_fields}")
        
        # Validate product name
        if not cls.validate_product_name(data.get("product_name")):
            raise ValidationError("Invalid product name")
        
        # Validate price
        if not cls.validate_price(data.get("price")):
            raise ValidationError("Invalid price format")
        
        # Validate URL
        if not cls.validate_url(data.get("url")):
            raise ValidationError("Invalid URL format")
        
        return True
    
    @staticmethod
    def validate_product_name(name: Optional[str]) -> bool:
        """Validate product name (non-empty string, min 3 chars)."""
        if not isinstance(name, str):
            return False
        return 3 <= len(name.strip()) <= 500
    
    @staticmethod
    def validate_price(price: Any) -> bool:
        """Validate price (numeric, positive value)."""
        try:
            price_float = float(price)
            return price_float >= 0
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def validate_url(url: Optional[str]) -> bool:
        """Validate URL format."""
        if not isinstance(url, str):
            return False
        url_pattern = re.compile(
            r'https?://(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.'
            r'[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        )
        return bool(url_pattern.match(url))
    
    @staticmethod
    def validate_stock_status(status: Optional[str]) -> bool:
        """Validate stock status field."""
        if status is None:
            return True
        
        valid_statuses = {"in_stock", "out_of_stock", "pre_order", "unknown"}
        return status.lower() in valid_statuses
    
    @staticmethod
    def sanitize_price(price: Any) -> float:
        """Convert price to float, stripping currency symbols."""
        if isinstance(price, (int, float)):
            return float(price)
        
        if isinstance(price, str):
            # Remove currency symbols and extract numbers
            cleaned = re.sub(r'[^\d.]', '', price)
            return float(cleaned) if cleaned else 0.0
        
        return 0.0
    
    @classmethod
    def validate_batch(cls, data_list: List[Dict[str, Any]]) -> tuple[List[Dict], List[Dict]]:
        """
        Validate multiple products and separate valid from invalid.
        
        Args:
            data_list: List of product data dictionaries
            
        Returns:
            Tuple of (valid_products, invalid_products)
        """
        valid = []
        invalid = []
        
        for item in data_list:
            try:
                cls.validate_product(item)
                valid.append(item)
            except ValidationError as e:
                invalid.append({
                    "data": item,
                    "error": str(e)
                })
                logger.warning(f"Invalid product data: {str(e)}")
        
        return valid, invalid
