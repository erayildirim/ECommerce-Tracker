"""
Script to scrape products and save them to the database with upsert logic.

Demonstrates:
- Running TestStoreScraper to get 117 products
- Using SQLAlchemy upsert pattern to avoid duplicates
- Transaction handling and error recovery
- Database statistics reporting
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from dateutil.parser import parse as parse_datetime

from config import settings
from src.scraper.scrapers import TestStoreScraper
from src.database.models import Product, PriceHistory


# Configure logging
logging.basicConfig(
    level='INFO',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductSaver:
    """Handle saving scraped products to database with upsert logic."""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the product saver.
        
        Args:
            db_url: Database URL (uses config if None)
        """
        if db_url is None:
            # Use connection string from config
            db_url = settings.database_url
        
        # Create engine with optimized connection pool settings
        self.engine = create_engine(
            db_url,
            pool_pre_ping=True,      # Verify connections are still alive
            pool_recycle=3600,        # Recycle connections after 1 hour
            pool_size=10,             # Number of persistent connections
            max_overflow=20           # Additional temporary connections
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = SessionLocal()
        self.scraper = TestStoreScraper()
        self.stats = {
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }
    
    async def scrape_products(self, product_url: str) -> tuple[list, list]:
        """
        Scrape products using TestStoreScraper.
        
        Args:
            product_url: URL to scrape
            
        Returns:
            Tuple of (valid_products, invalid_products)
        """
        logger.info(f"🔍 Starting scraping process...")
        logger.info(f"   URL: {product_url}")
        
        valid_products, invalid_products = await self.scraper.scrape_and_validate(product_url)
        
        logger.info(f"✓ Scraping completed:")
        logger.info(f"   Valid products: {len(valid_products)}")
        logger.info(f"   Invalid products: {len(invalid_products)}")
        
        return valid_products, invalid_products
    
    def upsert_product(self, product_data: Dict[str, Any]) -> bool:
        """
        Upsert a product based on URL uniqueness.
        
        Logic:
        - If URL not in database: Insert new product
        - If URL in database and price changed: Update product and log price change to PriceHistory
        - If URL in database and price same: Mark as skipped
        
        Args:
            product_data: Product data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        # Validate required fields before processing
        required_fields = ["url", "product_name", "price", "site_name"]
        if not all(field in product_data for field in required_fields):
            logger.warning(f"⚠ Product data missing required fields: {required_fields}")
            self.stats["errors"] += 1
            return False
        
        product_name = product_data.get("product_name", "Unknown")
        
        # Convert scraped_at from ISO string to datetime if needed
        scraped_at_raw = product_data.get("scraped_at")
        if isinstance(scraped_at_raw, str):
            scraped_at_val = parse_datetime(scraped_at_raw)
        elif isinstance(scraped_at_raw, datetime):
            scraped_at_val = scraped_at_raw
        else:
            scraped_at_val = datetime.now(timezone.utc)
        
        try:
            url = product_data["url"]
            new_price = product_data["price"]
            
            # Use a savepoint so that a constraint violation on this product
            # only rolls back its own changes, not the rest of the batch.
            with self.db.begin_nested():
                # Find existing product by URL (unique identifier)
                existing_product = self.db.query(Product).filter(
                    Product.url == url
                ).first()
                
                if existing_product:
                    # PRODUCT EXISTS: Check if price changed
                    old_price = existing_product.price
                    
                    if old_price != new_price:
                        # UPDATE: Price changed
                        logger.debug(f"⬆ Price changed for {product_name}: ${old_price:.2f} → ${new_price:.2f}")
                        
                        # Update product data
                        existing_product.product_name = product_data.get("product_name", existing_product.product_name)
                        existing_product.price = new_price
                        existing_product.currency = product_data.get("currency", existing_product.currency)
                        existing_product.stock_status = product_data.get("stock_status", existing_product.stock_status)
                        existing_product.description = product_data.get("description", existing_product.description)
                        existing_product.site_name = product_data.get("site_name", existing_product.site_name)
                        existing_product.scraped_at = scraped_at_val
                        existing_product.updated_at = datetime.now(timezone.utc)
                        
                        # Add price history entry for tracking
                        price_entry = PriceHistory(
                            product_id=existing_product.id,
                            price=new_price,
                            currency=existing_product.currency
                        )
                        self.db.add(price_entry)
                        self.stats["updated"] += 1
                    else:
                        # SKIP: Price unchanged
                        logger.debug(f"⊘ Skipped {product_name}: price unchanged")
                        self.stats["skipped"] += 1
                    
                else:
                    # INSERT: New product (URL doesn't exist in database)
                    currency = product_data.get("currency", "USD")
                    new_product = Product(
                        product_name=product_data.get("product_name"),
                        price=new_price,
                        url=url,
                        currency=currency,
                        stock_status=product_data.get("stock_status", "unknown"),
                        description=product_data.get("description"),
                        site_name=product_data.get("site_name"),
                        scraped_at=scraped_at_val,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    self.db.add(new_product)
                    # flush() assigns the DB-generated id without committing,
                    # so we can reference it in the price_history insert below.
                    self.db.flush()
                    price_entry = PriceHistory(
                        product_id=new_product.id,
                        price=new_price,
                        currency=currency
                    )
                    self.db.add(price_entry)
                    self.stats["inserted"] += 1
                    logger.debug(f"✨ Inserted: {product_name}")
            
            return True
            
        except IntegrityError as e:
            # Savepoint already rolled back; outer transaction is intact.
            logger.warning(f"⚠ Integrity error for '{product_name}': {str(e)}")
            self.stats["errors"] += 1
            return False
            
        except Exception as e:
            logger.error(f"✗ Error upserting '{product_name}': {str(e)}")
            self.stats["errors"] += 1
            return False
    
    def save_products(self, products: list) -> int:
        """
        Save/upsert products to database with batch transaction handling.
        
        Uses batch commits for better performance (every 25 products).
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Number of successfully processed products
        """
        logger.info(f"\n📝 Saving {len(products)} products to database...")
        successful = 0
        batch_size = 25
        
        for idx, product in enumerate(products, 1):
            try:
                if self.upsert_product(product):
                    successful += 1
                    
                    # Batch commit every 25 products for better performance
                    if idx % batch_size == 0:
                        try:
                            self.db.commit()
                            logger.info(f"   Progress: {idx}/{len(products)} products saved")
                        except Exception as commit_err:
                            logger.error(f"Batch commit error: {commit_err}")
                            self.db.rollback()
                        
            except Exception as e:
                logger.warning(f"⚠ Error processing product {idx}: {str(e)}")
        
        # Final commit for remaining products
        try:
            self.db.commit()
            logger.info(f"✓ Database save completed (final commit)")
        except Exception as e:
            logger.error(f"Final commit error: {str(e)}")
            self.db.rollback()
        
        return successful
    
    def get_database_stats(self) -> dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database stats
        """
        total_products = self.db.query(func.count(Product.id)).scalar() or 0
        total_by_site = self.db.query(
            Product.site_name,
            func.count(Product.id).label("count")
        ).group_by(Product.site_name).all()
        
        stats = {
            "total_products": total_products,
            "by_site": {row.site_name: row.count for row in total_by_site}
        }
        return stats
    
    def print_summary(self, scrape_stats: dict):
        """
        Print summary of save operation.
        
        Args:
            scrape_stats: Dictionary with insertion/update/error stats
        """
        print("\n" + "="*80)
        print("📊 SAVE OPERATION SUMMARY")
        print("="*80)
        
        print("\n✓ Save Statistics:")
        print(f"  • Inserted (new): {scrape_stats['inserted']}")
        print(f"  • Updated (price change): {scrape_stats['updated']}")
        print(f"  • Skipped (no change): {scrape_stats['skipped']}")
        print(f"  • Errors: {scrape_stats['errors']}")
        total_processed = scrape_stats['inserted'] + scrape_stats['updated'] + scrape_stats['skipped']
        print(f"  • Total processed: {total_processed}")
        
        db_stats = self.get_database_stats()
        print(f"\n📊 Database Statistics After Save:")
        print(f"  • Total products in database: {db_stats['total_products']}")
        
        if db_stats["by_site"]:
            print(f"\n  Products by site:")
            for site, count in db_stats["by_site"].items():
                print(f"    - {site}: {count} products")
        
        print("\n" + "="*80)
    
    def close(self):
        """Close database session."""
        self.db.close()


async def main():
    """Main execution function."""
    saver = None
    
    try:
        # Create saver instance
        saver = ProductSaver()
        
        # Get product URL from config (can also be passed as argument)
        product_url = getattr(settings, 'scraper_url', 
                             "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops")
        valid_products, invalid_products = await saver.scrape_products(product_url)
        
        # Save products with upsert logic
        if valid_products:
            successful = saver.save_products(valid_products)
            
            # Print summary
            saver.print_summary(saver.stats)
            
            logger.info(f"\n✓ Process completed successfully!")
            logger.info(f"   {successful}/{len(valid_products)} products saved/updated")
        else:
            logger.warning("⚠ No valid products to save")
            
    except Exception as e:
        logger.error(f"✗ Fatal error: {str(e)}", exc_info=True)
        raise
    finally:
        if saver:
            try:
                saver.close()
            except Exception as close_err:
                logger.warning(f"Error closing database connection: {close_err}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠ Operation cancelled by user")
    except Exception as e:
        logger.error(f"\n✗ Unhandled error: {str(e)}")
        exit(1)
