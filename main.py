"""Main entry point for E-Commerce Tracker."""

import asyncio
import logging
from datetime import datetime

from config import settings
from src.scraper import BaseScraper
from src.database import init_db


logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main application entry point."""
    logger.info("=" * 60)
    logger.info("E-Commerce Price Tracker - Starting Pipeline")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info("=" * 60)
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        init_db()
        logger.info("✓ Database initialized successfully")
        
        # Run API or scraper based on environment
        logger.info("Configuration loaded:")
        logger.info(f"  - Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
        logger.info(f"  - API Port: {settings.api_port}")
        logger.info(f"  - Concurrent Scrapers: {settings.max_concurrent_scrapers}")
        logger.info(f"  - Retry Attempts: {settings.retry_attempts}")
        
        # To start the API server, run:
        # python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
        
        logger.info("\n" + "=" * 60)
        logger.info("To start the API server, run:")
        logger.info("  python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000")
        logger.info("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
