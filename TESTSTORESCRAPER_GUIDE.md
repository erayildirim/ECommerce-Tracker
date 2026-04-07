"""
TESTSTORESCRAPER - IMPLEMENTATION GUIDE
========================================

A production-ready implementation of a concrete Playwright-based web scraper
demonstrating best practices for e-commerce data extraction.

═══════════════════════════════════════════════════════════════════════════════
TABLE OF CONTENTS
═════════════════

1. Overview
2. Features
3. Usage Examples
4. API Reference
5. Data Flow
6. Error Handling
7. Logging & Debugging
8. Performance Tips
9. Extending the Scraper
10. Troubleshooting

═══════════════════════════════════════════════════════════════════════════════
1. OVERVIEW
═══════════

TestStoreScraper is a concrete implementation that scrapes product data from
webscraper.io's e-commerce test site. It demonstrates:

✓ Playwright integration with async/await
✓ JavaScript evaluation for dynamic content
✓ Professional error handling and logging
✓ Data validation with batch processing
✓ Automatic retry mechanisms
✓ Production-ready architecture

Target URL:
  https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops

═══════════════════════════════════════════════════════════════════════════════
2. FEATURES
═══════════

✓ Async Web Scraping
  - Non-blocking Playwright browser automation
  - Headless mode for performance
  - Configurable timeouts and retries

✓ Data Extraction
  - Intelligent CSS selector handling
  - JavaScript evaluation for dynamic content
  - Price normalization and sanitization
  - Timestamp tracking

✓ Data Validation
  - Product name validation (3-500 characters)
  - Price validation (numeric, positive)
  - URL format validation
  - Batch processing with error reporting

✓ Logging & Monitoring
  - Professional structured logging
  - Debug, info, warning, and error levels
  - Performance metrics (elapsed time)
  - Detailed error tracking

✓ Error Handling
  - Automatic exponential backoff retry
  - Graceful timeout handling
  - Detailed error messages
  - Browser cleanup on failure

═══════════════════════════════════════════════════════════════════════════════
3. USAGE EXAMPLES
═════════════════

EXAMPLE 1: Basic Usage
──────────────────────

import asyncio
from src.scraper import TestStoreScraper

async def main():
    scraper = TestStoreScraper()
    url = "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"
    
    # Scrape with automatic validation
    valid_products, invalid_products = await scraper.scrape_and_validate(url)
    
    print(f"Valid: {len(valid_products)}")
    print(f"Invalid: {len(invalid_products)}")
    
    for product in valid_products:
        print(f"  {product['product_name']}: ${product['price']:.2f}")

asyncio.run(main())


EXAMPLE 2: Manual Control
─────────────────────────

import asyncio
from src.scraper import TestStoreScraper
from src.scraper.validators import DataValidator

async def main():
    scraper = TestStoreScraper()
    url = "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"
    
    # Step 1: Scrape
    data = await scraper.scrape(url)
    
    # Step 2: Validate manually
    if await scraper.validate_data(data):
        products = data.get("products", [])
        
        # Step 3: Batch validation
        valid, invalid = DataValidator.validate_batch(products)
        
        for product in valid:
            print(product["product_name"])

asyncio.run(main())


EXAMPLE 3: With Retry Logic
───────────────────────────

import asyncio
from src.scraper import TestStoreScraper

async def main():
    scraper = TestStoreScraper()
    url = "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"
    
    # scrape_with_retry handles automatic retries with exponential backoff
    result = await scraper.scrape_with_retry(url)
    
    if result:
        print(f"Success: {len(result.get('products', []))} products")
    else:
        print("Failed after all retries")

asyncio.run(main())


EXAMPLE 4: Batch Processing
───────────────────────────

import asyncio
from src.scraper import TestStoreScraper

async def main():
    scraper = TestStoreScraper()
    
    urls = [
        "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops",
        "https://webscraper.io/test-sites/e-commerce/allinone/computers/phones"
    ]
    
    # scrape_batch handles concurrent scraping with rate limiting
    results = await scraper.scrape_batch(urls, batch_size=2)
    
    print(f"Scraped {len(results)} products total")

asyncio.run(main())


EXAMPLE 5: Logging Integration
──────────────────────────────

import logging
from src.scraper import TestStoreScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

scraper = TestStoreScraper()
# Logger accessible via: scraper.logger

═══════════════════════════════════════════════════════════════════════════════
4. API REFERENCE
════════════════

CLASS: TestStoreScraper(BaseScraper)
────────────────────────────────────

INITIALIZATION:
  scraper = TestStoreScraper()

PARAMETERS (inherited from BaseScraper):
  site_name: str = "teststore"
  base_url: str = "https://webscraper.io/test-sites/e-commerce/allinone"
  max_retries: int = 3
  timeout: int = 30 (seconds)


METHODS:

1. async scrape(product_url: str) -> Dict[str, Any]
   ─────────────────────────────────────────────────
   Scrapes product data from a single URL using Playwright.
   
   Returns: Dictionary with keys:
     - products: List[Dict] - Extracted product data
     - url: str - The scraped URL
     - total_products: int - Number of products found
   
   Raises: Exception on scraping failure


2. async validate_data(data: Dict[str, Any]) -> bool
   ─────────────────────────────────────────────────
   Validates scraped data structure and content.
   
   Returns: True if valid, False if invalid


3. async scrape_with_retry(product_url: str) -> Optional[Dict[str, Any]]
   ──────────────────────────────────────────────────────────────────────
   Inherited from BaseScraper. Scrapes with automatic retry.
   Uses exponential backoff: 2^attempt seconds between retries.
   
   Returns: Validated product data or None if all retries fail


4. async scrape_batch(urls: List[str], batch_size: int = 5) -> List[Dict]
   ───────────────────────────────────────────────────────────────────────
   Inherited from BaseScraper. Concurrent batch scraping with rate limiting.
   
   Parameters:
     - urls: List of URLs to scrape
     - batch_size: Maximum concurrent requests (default: 5)


5. async scrape_and_validate(product_url: str) -> Tuple[List[Dict], List[Dict]]
   ──────────────────────────────────────────────────────────────────────────────
   Full pipeline: scrape → validate → batch validate → return results.
   
   Returns: (valid_products, invalid_products)
     - valid_products: List successfully validated
     - invalid_products: List with error details


═══════════════════════════════════════════════════════════════════════════════
5. DATA FLOW
════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ SCRAPING PIPELINE                                                           │
└─────────────────────────────────────────────────────────────────────────────┘

  1. Initialize Scraper
     └─→ TestStoreScraper()

  2. Launch Browser
     └─→ Chromium (headless mode)

  3. Navigate to URL
     └─→ 30 second timeout, wait for network idle

  4. Wait for Elements
     └─→ Wait for "div.product" selector

  5. Extract with JavaScript
     └─→ Evaluate page.evaluate() to extract product data

  6. Sanitize Data
     └─→ DataValidator.sanitize_price() for prices

  7. Validate Records
     └─→ DataValidator.validate_batch()

  8. Add Metadata
     └─→ scraped_at timestamp, site_name

  9. Return Results
     └─→ (valid_products, invalid_products)

 10. Browser Cleanup
     └─→ Close browser, release resources


EXTRACTED FIELDS:
─────────────────

Each product includes:
  ✓ product_name: str       - Product title
  ✓ price: float            - Sanitized numeric price
  ✓ description: str        - Product description
  ✓ url: str                - Product page URL
  ✓ currency: str           - Currency code (default: USD)
  ✓ stock_status: str       - Stock status (default: unknown)
  ✓ scraped_at: str (ISO)   - Extraction timestamp
  ✓ site_name: str          - Source site identifier

═══════════════════════════════════════════════════════════════════════════════
6. ERROR HANDLING
═════════════════

AUTOMATIC RETRIES:
──────────────────

  Attempt 1: Fail → Wait 2 seconds
  Attempt 2: Fail → Wait 4 seconds
  Attempt 3: Fail → Wait 8 seconds
  Result: None (all retries exhausted)

Common failures handled:
  ✓ Network timeouts
  ✓ Page navigation errors
  ✓ Element not found
  ✓ Browser crashes
  ✓ Validation failures


VALIDATION ERRORS:
──────────────────

  Product validation fails on:
  ✗ product_name < 3 or > 500 characters
  ✗ price is negative or non-numeric
  ✗ url format is invalid
  ✗ missing scraped_at timestamp

═══════════════════════════════════════════════════════════════════════════════
7. LOGGING & DEBUGGING
══════════════════════

LOG LEVELS:
───────────

  DEBUG:   Detailed information for diagnostic purposes
           → Page navigation, element discovery
  
  INFO:    General information about operations
           → Scraping start/end, counts, elapsed time
  
  WARNING: Warning messages for issues
           → Invalid data, validation failures
  
  ERROR:   Error messages with tracebacks
           → Scraping failures, exceptions

ENABLE DEBUG LOGGING:
─────────────────────

import logging
logging.basicConfig(level=logging.DEBUG)

Sample output:
  2024-04-07 12:34:56 - scraper.teststore - INFO - Starting scraping...
  2024-04-07 12:34:57 - scraper.teststore - DEBUG - Navigating to: https://...
  2024-04-07 12:35:02 - scraper.teststore - DEBUG - Extracted 12 products
  2024-04-07 12:35:02 - scraper.teststore - INFO - ✓ Scraping completed in 5.23s
  2024-04-07 12:35:02 - scraper.teststore - INFO - Valid: 11, Invalid: 1


═══════════════════════════════════════════════════════════════════════════════
8. PERFORMANCE TIPS
═══════════════════

✓ Use batch_size parameter to control concurrency
  - Higher values = faster but more resource usage
  - Recommended: 3-5 concurrent requests

✓ Enable headless mode (default)
  - ~30% faster than headed mode
  - Requires less memory

✓ Set appropriate timeouts
  - Too short: premature failures
  - Too long: slow scraping
  - Default 30s is balanced

✓ Implement caching
  - Store failed URLs
  - Don't re-scrape unchanged pages
  - Cache results locally

═══════════════════════════════════════════════════════════════════════════════
9. EXTENDING THE SCRAPER
═════════════════════════

CREATE YOUR OWN SCRAPER:
────────────────────────

from src.scraper import BaseScraper
from src.scraper.validators import DataValidator
from playwright.async_api import async_playwright

class AmazonScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            site_name="amazon",
            base_url="https://www.amazon.com",
            max_retries=3,
            timeout=30
        )
    
    async def scrape(self, product_url: str) -> Dict[str, Any]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(product_url, wait_until="networkidle")
            
            # Your custom extraction logic
            products = await self._extract_amazon_products(page)
            
            await browser.close()
            return {"products": products}
    
    async def validate_data(self, data: Dict[str, Any]) -> bool:
        # Your validation logic
        return len(data.get("products", [])) > 0
    
    async def _extract_amazon_products(self, page) -> List[Dict]:
        # Custom extraction for Amazon
        pass

═══════════════════════════════════════════════════════════════════════════════
10. TROUBLESHOOTING
═══════════════════

ISSUE: "Timeout waiting for selector"
SOLUTION:
  • Increase timeout value in __init__
  • Check if CSS selector is correct
  • Verify URL is accessible
  • Check network connectivity

ISSUE: "Playwright browser not found"
SOLUTION:
  • Install browsers: playwright install
  • Or install system dependencies: playwright install-deps

ISSUE: "Empty products list"
SOLUTION:
  • Check CSS selector matches actual HTML
  • Enable debug logging to see extracted HTML
  • Try JavaScript evaluation for dynamic content

ISSUE: "Validation failures"
SOLUTION:
  • Check price format (should be numeric)
  • Verify product_name length (3-500 chars)
  • Check URL format validity

═══════════════════════════════════════════════════════════════════════════════

For more information, see:
  • README.md - Project overview
  • src/scraper/base.py - BaseScraper documentation
  • src/scraper/validators.py - DataValidator reference
  • tests/test_scraper.py - Usage examples in tests
"""
