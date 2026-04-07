"""Base async scraper class with error handling and data validation."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timezone
import asyncio

from config import settings


logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers supporting 650+ e-commerce sites.
    
    Provides:
    - Error handling and retry logic
    - Data validation framework
    - Async/await support
    - Logging and monitoring
    - Configuration-driven timeout and retry behavior
    """
    
    def __init__(
        self,
        site_name: str,
        base_url: str,
        max_retries: Optional[int] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize base scraper.
        
        Args:
            site_name: Name of the e-commerce site
            base_url: Base URL for the scraper
            max_retries: Maximum retry attempts on failure (defaults to settings.retry_attempts)
            timeout: Request timeout in seconds (defaults to settings.scraper_timeout_seconds)
        """
        self.site_name = site_name
        self.base_url = base_url
        self.max_retries = max_retries if max_retries is not None else settings.retry_attempts
        self.timeout = timeout if timeout is not None else int(settings.scraper_timeout_seconds)
        self.logger = logging.getLogger(f"scraper.{site_name}")
    
    @abstractmethod
    async def scrape(self, product_url: str) -> Dict[str, Any]:
        """
        Scrape product data from e-commerce site.
        
        Args:
            product_url: URL of the product to scrape
            
        Returns:
            Dictionary containing scraped product data
            
        Raises:
            ScraperException: If scraping fails
        """
        pass
    
    @abstractmethod
    async def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate scraped product data.
        
        Args:
            data: Dictionary of scraped data
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    async def scrape_with_retry(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape product with automatic retry logic.
        
        Args:
            product_url: URL of the product to scrape
            
        Returns:
            Dictionary of scraped data or None if all retries fail
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info(
                    f"Scraping {product_url} (attempt {attempt}/{self.max_retries})"
                )
                data = await self.scrape(product_url)
                
                # Validate scraped data
                if await self.validate_data(data):
                    data["scraped_at"] = datetime.now(timezone.utc).isoformat()
                    data["site_name"] = self.site_name
                    self.logger.info(f"Successfully scraped: {product_url}")
                    return data
                else:
                    self.logger.warning(f"Data validation failed for: {product_url}")
                    
            except Exception as e:
                self.logger.error(
                    f"Attempt {attempt} failed for {product_url}: {str(e)}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        self.logger.error(f"Failed to scrape {product_url} after {self.max_retries} retries")
        return None
    
    async def scrape_batch(
        self,
        product_urls: List[str],
        batch_size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple products with concurrency control.
        
        Args:
            product_urls: List of product URLs to scrape
            batch_size: Maximum concurrent requests
            
        Returns:
            List of successfully scraped product data
        """
        results = []
        
        for i in range(0, len(product_urls), batch_size):
            batch = product_urls[i:i + batch_size]
            tasks = [self.scrape_with_retry(url) for url in batch]
            batch_results = await asyncio.gather(*tasks)
            
            # Filter out None values (failed scrapes)
            results.extend([r for r in batch_results if r is not None])
        
        return results


class ScraperException(Exception):
    """Custom exception for scraper errors."""
    pass
