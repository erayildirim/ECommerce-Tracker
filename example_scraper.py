#!/usr/bin/env python
"""
QUICK EXAMPLE: TestStoreScraper Usage
======================================

This is a minimal example showing how to use TestStoreScraper.
Run with: python example_scraper.py
"""

import asyncio
import logging
from src.scraper import TestStoreScraper
from src.scraper.validators import DataValidator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)

logger = logging.getLogger(__name__)


async def example_1_basic_validation():
    """Example 1: Validate product data without scraping."""
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 1: Data Validation (No Scraping)")
    logger.info("=" * 80)
    
    # Sample product data
    products = [
        {
            "product_name": "Professional Laptop",
            "price": "$1,299.99",
            "description": "High performance machine",
            "url": "https://example.com/laptop1",
            "scraped_at": "2024-04-07T10:00:00"
        },
        {
            "product_name": "Gaming PC",
            "price": "1999.50",
            "description": "Ultimate gaming setup",
            "url": "https://example.com/gaming",
            "scraped_at": "2024-04-07T10:00:00"
        }
    ]
    
    logger.info(f"\nValidating {len(products)} products...")
    
    # Validate batch
    valid, invalid = DataValidator.validate_batch(products)
    
    logger.info(f"Results: {len(valid)} valid, {len(invalid)} invalid")
    
    # Sanitize prices
    logger.info("\nPrice Sanitization Examples:")
    test_prices = ["$99.99", "€150.00", "1,500.50"]
    for price in test_prices:
        sanitized = DataValidator.sanitize_price(price)
        logger.info(f"  {price:>10} → {sanitized:>8.2f}")


async def example_2_scraper_config():
    """Example 2: Show scraper configuration."""
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 2: Scraper Configuration")
    logger.info("=" * 80)
    
    scraper = TestStoreScraper()
    
    logger.info(f"\nScraper Details:")
    logger.info(f"  Site Name: {scraper.site_name}")
    logger.info(f"  Base URL: {scraper.base_url}")
    logger.info(f"  Max Retries: {scraper.max_retries}")
    logger.info(f"  Timeout: {scraper.timeout}s")
    logger.info(f"  Logger: {scraper.logger.name}")
    
    logger.info(f"\nAvailable Methods:")
    methods = [
        "scrape(url) - Scrape a single page",
        "validate_data(data) - Validate scraped data",
        "scrape_with_retry(url) - Automatic retry on failure",
        "scrape_batch(urls) - Batch processing",
        "scrape_and_validate(url) - Full pipeline"
    ]
    for method in methods:
        logger.info(f"  • {method}")


async def example_3_live_scraping():
    """Example 3: Live scraping (uncomment to enable)."""
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 3: Live Web Scraping with Playwright")
    logger.info("=" * 80)
    
    scraper = TestStoreScraper()
    url = "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"
    
    logger.info(f"\nTarget URL: {url}")
    logger.info("This example requires network access and takes ~10-15 seconds")
    logger.info("\nTo enable live scraping:")
    logger.info("  1. Uncomment the code in example_3_live_scraping()")
    logger.info("  2. Ensure Playwright is installed: playwright install")
    logger.info("  3. Run: python example_scraper.py")
    
    # UNCOMMENT BELOW TO ENABLE LIVE SCRAPING
    # logger.info("\n⏳ Starting scraper... (this may take a moment)")
    # valid_products, invalid_products = await scraper.scrape_and_validate(url)
    # 
    # logger.info(f"\n✓ Scraping complete!")
    # logger.info(f"  Valid products: {len(valid_products)}")
    # logger.info(f"  Invalid products: {len(invalid_products)}")
    # 
    # if valid_products:
    #     logger.info(f"\nSample Products:")
    #     for product in valid_products[:3]:
    #         logger.info(f"  • {product['product_name']}")
    #         logger.info(f"    Price: ${product['price']:.2f}")
    #         logger.info(f"    Description: {product['description'][:50]}...")


async def main():
    """Run all examples."""
    logger.info("\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 15 + "TestStoreScraper - Quick Examples" + " " * 30 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    
    try:
        # Run examples
        await example_1_basic_validation()
        await example_2_scraper_config()
        await example_3_live_scraping()
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ All examples completed!")
        logger.info("=" * 80)
        logger.info("\nNext Steps:")
        logger.info("  1. Read TESTSTORESCRAPER_GUIDE.md for detailed documentation")
        logger.info("  2. Check tests/test_scraper.py for more usage examples")
        logger.info("  3. Run the demo: python demo_scraper.py")
        logger.info("  4. Implement your own scrapers based on TestStoreScraper")
        
    except Exception as e:
        logger.error(f"Example failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
