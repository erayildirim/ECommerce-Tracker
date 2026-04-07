"""Concrete scraper implementations for different e-commerce sites."""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timezone
from playwright.async_api import async_playwright, Page

from config import settings
from .base import BaseScraper
from .validators import DataValidator


logger = logging.getLogger(__name__)


class TestStoreScraper(BaseScraper):
    """
    Professional scraper for webscraper.io test e-commerce site.
    
    Demonstrates real-world Playwright integration with:
    - Async page navigation and element handling
    - Professional data extraction
    - Error handling and validation
    - Comprehensive logging
    """
    
    def __init__(self):
        """Initialize TestStore scraper with site configuration."""
        super().__init__(
            site_name="teststore",
            base_url="https://webscraper.io/test-sites/e-commerce/allinone"
            # Uses default max_retries and timeout from settings
        )
    
    async def scrape(self, product_url: str) -> Dict[str, Any]:
        """
        Scrape product data from webscraper.io test site using Playwright.
        
        Args:
            product_url: URL of the products page to scrape
            
        Returns:
            Dictionary with single product data
            
        Raises:
            Exception: If scraping fails
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.playwright_headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            
            try:
                page = await browser.new_page()
                page.set_default_timeout(settings.scraper_timeout)
                
                self.logger.info(f"Navigating to: {product_url}")
                # Explicit timeout for page navigation (30 seconds should be enough)
                try:
                    await page.goto(
                        product_url,
                        wait_until="domcontentloaded",
                        timeout=30000
                    )
                    self.logger.info("✓ Page loaded successfully")
                except Exception as nav_error:
                    self.logger.error(f"Navigation failed: {nav_error}")
                    raise
                
                # Try to wait for product containers (with fallback selectors)
                selectors = [
                    "div.thumbnail",         # webscraper.io test site
                    "div.product",           # Alternative 1
                    ".product-item",         # Alternative 2
                    ".product",              # Alternative 3
                ]
                
                selector_found = False
                for selector in selectors:
                    try:
                        self.logger.debug(f"Trying selector: {selector}")
                        await page.wait_for_selector(selector, timeout=5000)
                        self.logger.info(f"✓ Found elements with selector: {selector}")
                        selector_found = True
                        break
                    except Exception:
                        self.logger.debug(f"✗ Selector '{selector}' not found")
                        continue
                
                if not selector_found:
                    self.logger.warning(
                        "⚠ No product selectors found. Attempting extraction anyway..."
                    )
                
                # Extract product data
                products = await self._extract_products(page)
                
                self.logger.info(f"✓ Extracted {len(products)} products")
                
                return {
                    "products": products,
                    "url": product_url,
                    "total_products": len(products)
                }
                
            except Exception as e:
                self.logger.error(f"Scraping error for {product_url}: {str(e)}", exc_info=True)
                raise
            finally:
                await browser.close()
    
    async def _extract_products(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract product information from the page.
        
        Targets webscraper.io test site HTML structure:
          div.thumbnail > div.caption > h4 > a.title  (product name + link)
          div.thumbnail > div.caption > h4.price       (price)
          div.thumbnail > div.caption > p.description   (description)
        
        Args:
            page: Playwright page object
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        try:
            self.logger.debug("Extracting products with div.thumbnail selector")
            products_data = await page.evaluate("""
                () => {
                    const cards = document.querySelectorAll('div.thumbnail');
                    const products = [];
                    const baseUrl = window.location.origin;
                    
                    cards.forEach((card, index) => {
                        const titleLink = card.querySelector('a.title');
                        const priceEl = card.querySelector('h4.price, .price, .pull-right.price');
                        const descEl = card.querySelector('p.description, .description');
                        
                        let productUrl = null;
                        if (titleLink && titleLink.href) {
                            productUrl = titleLink.href;
                        } else {
                            const anyLink = card.querySelector('a[href]');
                            if (anyLink && anyLink.href) {
                                productUrl = anyLink.href;
                            } else {
                                productUrl = window.location.href + '#product-' + index;
                            }
                        }
                        
                        const title = titleLink
                            ? titleLink.textContent.trim()
                            : (card.querySelector('h4:not(.price), h2, .title')
                                ? card.querySelector('h4:not(.price), h2, .title').textContent.trim()
                                : null);
                        
                        const priceText = priceEl ? priceEl.textContent.trim() : '0';
                        const desc = descEl ? descEl.textContent.trim() : '';
                        
                        if (title && title.length > 1) {
                            products.push({
                                product_name: title,
                                price: priceText,
                                description: desc.substring(0, 500),
                                url: productUrl,
                                currency: 'USD'
                            });
                        }
                    });
                    
                    return products;
                }
            """)
            
            if products_data and len(products_data) > 0:
                self.logger.info(f"Extraction successful: {len(products_data)} products")
                for product in products_data:
                    product["price"] = DataValidator.sanitize_price(product["price"])
                    product["stock_status"] = "unknown"
                    products.append(product)
                return products
            else:
                self.logger.warning("div.thumbnail selector found 0 products")
        
        except Exception as e:
            self.logger.warning(f"Primary extraction failed: {e}")
        
        return products
    
    async def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate scraped product data.
        
        Args:
            data: Dictionary containing products list and metadata
            
        Returns:
            True if validation succeeds, False otherwise
        """
        try:
            if "products" not in data or not isinstance(data["products"], list):
                self.logger.warning("Invalid data structure: missing products list")
                return False
            
            # Validate at least one product exists
            if len(data["products"]) == 0:
                self.logger.warning("No products found in scraped data")
                return False
            
            self.logger.debug(f"Data validation successful: {len(data['products'])} products")
            return True
            
        except Exception as e:
            self.logger.error(f"Data validation failed: {str(e)}")
            return False
    
    async def scrape_and_validate(self, product_url: str) -> tuple[List[Dict], List[Dict]]:
        """
        Scrape products and validate them, separating valid from invalid.
        
        Args:
            product_url: URL of products page to scrape
            
        Returns:
            Tuple of (valid_products, invalid_products)
        """
        self.logger.info(
            f"Starting scraping for {self.site_name} - URL: {product_url}"
        )
        start_time = datetime.now(timezone.utc)
        
        try:
            # Scrape with retry logic
            scraped_data = await self.scrape_with_retry(product_url)
            
            if not scraped_data:
                self.logger.error(f"Failed to scrape {product_url} after retries")
                return [], []
            
            # Extract products and validate
            products = scraped_data.get("products", [])
            
            # ADD TIMESTAMP BEFORE VALIDATION (required by validator)
            for product in products:
                product["scraped_at"] = datetime.now(timezone.utc).isoformat()
                product["site_name"] = self.site_name
            
            # Now validate - all products have scraped_at
            valid_products, invalid_products = DataValidator.validate_batch(products)
            
            # Log results
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.info(
                f"✓ Scraping completed for {self.site_name} in {elapsed:.2f}s\n"
                f"  Total products: {len(products)}\n"
                f"  Valid products: {len(valid_products)}\n"
                f"  Invalid products: {len(invalid_products)}"
            )
            
            if invalid_products:
                self.logger.warning(
                    f"  Invalid products details:\n"
                    f"  {[item['error'] for item in invalid_products]}"
                )
            
            return valid_products, invalid_products
            
        except Exception as e:
            self.logger.error(
                f"✗ Scraping failed for {self.site_name}: {str(e)}",
                exc_info=True
            )
            return [], []


class AmazonScraper(BaseScraper):
    """Amazon product scraper implementation."""
    
    def __init__(self):
        super().__init__(
            site_name="amazon",
            base_url="https://www.amazon.com"
        )
    
    async def scrape(self, product_url: str) -> Dict[str, Any]:
        """
        Implement Amazon-specific scraping logic.
        Note: Replace with actual Playwright logic when ready.
        """
        # Placeholder for Playwright integration
        product = {
            "product_name": "Sample Product",
            "price": 29.99,
            "url": product_url,
            "currency": "USD",
            "stock_status": "in_stock"
        }
        return {
            "products": [product],
            "url": product_url,
            "total_products": 1
        }
    
    async def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate Amazon product data."""
        return (
            "products" in data
            and isinstance(data["products"], list)
            and len(data["products"]) > 0
        )


class EbayScraper(BaseScraper):
    """eBay product scraper implementation."""
    
    def __init__(self):
        super().__init__(
            site_name="ebay",
            base_url="https://www.ebay.com"
        )
    
    async def scrape(self, product_url: str) -> Dict[str, Any]:
        """Implement eBay-specific scraping logic."""
        # Placeholder for Playwright integration
        product = {
            "product_name": "Sample eBay Product",
            "price": 15.99,
            "url": product_url,
            "currency": "USD",
            "stock_status": "in_stock"
        }
        return {
            "products": [product],
            "url": product_url,
            "total_products": 1
        }
    
    async def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate eBay product data."""
        return (
            "products" in data
            and isinstance(data["products"], list)
            and len(data["products"]) > 0
        )
