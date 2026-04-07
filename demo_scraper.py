#!/usr/bin/env python
"""
Demo script showing TestStoreScraper in action.

This script demonstrates:
- Real Playwright-based web scraping
- Data validation with batch processing
- Professional logging
- Handling valid and invalid products
"""

import asyncio
import logging
from datetime import datetime, UTC
import json

from src.scraper import TestStoreScraper
from src.scraper.validators import DataValidator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def demo_basic_scraping():
    """Demo 1: Basic scraping functionality."""
    logger.info("=" * 80)
    logger.info("DEMO 1: Basic Web Scraping with TestStoreScraper")
    logger.info("=" * 80)
    
    scraper = TestStoreScraper()
    url = "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"
    
    logger.info(f"Target URL: {url}")
    logger.info("Scraping in progress...")
    
    try:
        valid_products, invalid_products = await scraper.scrape_and_validate(url)
        
        logger.info(f"\n✓ Scraping completed successfully!")
        logger.info(f"Valid products: {len(valid_products)}")
        logger.info(f"Invalid products: {len(invalid_products)}")
        
        # Display sample valid products
        if valid_products:
            logger.info("\nSample Valid Products:")
            logger.info("-" * 80)
            for i, product in enumerate(valid_products[:3], 1):
                logger.info(f"\nProduct {i}:")
                logger.info(f"  Name: {product.get('product_name')}")
                price_value = DataValidator.sanitize_price(product.get('price'))
                logger.info(f"  Price: ${price_value:.2f}")
                description = (product.get('description') or '')[:50]
                logger.info(f"  Description: {description}...")
                logger.info(f"  Scraped at: {product.get('scraped_at')}")
        
        # Display invalid products if any
        if invalid_products:
            logger.warning(f"\nInvalid Products ({len(invalid_products)}):")
            logger.warning("-" * 80)
            for item in invalid_products[:3]:
                logger.warning(f"  Error: {item['error']}")
                logger.warning(f"  Data: {item['data']}\n")
        
        return valid_products
        
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}", exc_info=True)
        return []


async def demo_data_validation():
    """Demo 2: Data validation with DataValidator."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 2: Data Validation with DataValidator")
    logger.info("=" * 80)
    
    # Sample test data with mix of valid and invalid products
    test_products = [
        {
            "product_name": "High-Performance Gaming Laptop",
            "price": "$1,299.99",
            "description": "Powerful laptop with RTX 4080",
            "url": "https://example.com/laptop1",
            "scraped_at": datetime.now(UTC).isoformat()
        },
        {
            "product_name": "Budget Ultrabook",
            "price": "649.50",
            "description": "Lightweight and portable",
            "url": "https://example.com/laptop2",
            "scraped_at": datetime.now(UTC).isoformat()
        },
        {
            "product_name": "X",  # Too short name
            "price": "999",
            "description": "Invalid product",
            "url": "https://example.com/laptop3",
            "scraped_at": datetime.now(UTC).isoformat()
        },
        {
            "product_name": "Professional Workstation",
            "price": "invalid",  # Invalid price format
            "description": "For designers and engineers",
            "url": "https://example.com/laptop4",
            "scraped_at": datetime.now(UTC).isoformat()
        },
        {
            "product_name": "Gaming Laptop Pro Max",
            "price": "1899.99",
            "description": "Ultimate gaming experience",
            "url": "https://example.com/laptop5",
            "scraped_at": datetime.now(UTC).isoformat()
        }
    ]
    
    logger.info(f"\nValidating {len(test_products)} test products...")
    
    # Validate batch
    valid, invalid = DataValidator.validate_batch(test_products)
    
    logger.info(f"✓ Validation Results:")
    logger.info(f"  Valid products: {len(valid)}")
    logger.info(f"  Invalid products: {len(invalid)}")
    
    logger.info(f"\nValid Products Details:")
    logger.info("-" * 80)
    for product in valid:
        price_value = DataValidator.sanitize_price(product['price'])
        logger.info(f"  ✓ {product['product_name']} - ${price_value:.2f}")
    
    if invalid:
        logger.warning(f"\nInvalid Products Details:")
        logger.warning("-" * 80)
        for item in invalid:
            logger.warning(f"  ✗ Error: {item['error']}")
            logger.warning(f"    Product: {item['data']['product_name']}")


async def demo_price_sanitization():
    """Demo 3: Price sanitization utility."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 3: Price Sanitization Examples")
    logger.info("=" * 80)
    
    test_prices = [
        "29.99",
        "$99.99",
        "€150.00",
        "£199.99",
        "¥10,000",
        "1,500.50",
        "Price: $349.99",
        "From $99 to $199"
    ]
    
    logger.info("\nPrice Sanitization Results:")
    logger.info("-" * 80)
    
    for price in test_prices:
        sanitized = DataValidator.sanitize_price(price)
        logger.info(f"  Input: '{price}' → Output: {sanitized}")


async def demo_scraper_features():
    """Demo 4: Advanced scraper features."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 4: Scraper Features & Configuration")
    logger.info("=" * 80)
    
    scraper = TestStoreScraper()
    
    logger.info(f"\nScraper Configuration:")
    logger.info(f"  Site Name: {scraper.site_name}")
    logger.info(f"  Base URL: {scraper.base_url}")
    logger.info(f"  Max Retries: {scraper.max_retries}")
    logger.info(f"  Timeout: {scraper.timeout}s")
    logger.info(f"  Logger: {scraper.logger.name}")
    
    logger.info(f"\nAvailable Methods:")
    logger.info(f"  • scrape() - Single product scraping")
    logger.info(f"  • validate_data() - Data validation")
    logger.info(f"  • scrape_with_retry() - With automatic retry")
    logger.info(f"  • scrape_batch() - Batch processing")
    logger.info(f"  • scrape_and_validate() - Full pipeline with validation")


async def main():
    """Run all demos."""
    logger.info("\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 20 + "TestStoreScraper - Demonstration Suite" + " " * 20 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    
    try:
        # Run Demo 1 - Only if you want to actually scrape (takes time)
        # Uncomment the line below to run real scraping
        valid_products = await demo_basic_scraping()
        
        # Run Demos 2-4 (no network required)
        await demo_data_validation()
        await demo_price_sanitization()
        await demo_scraper_features()
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ All demonstrations completed successfully!")
        logger.info("=" * 80)
        logger.info("\nTo run the live scraping demo, uncomment the first demo in main()")
        logger.info("and run: python demo_scraper.py\n")
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
