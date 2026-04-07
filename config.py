"""Application configuration management using Pydantic Settings v2."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings from environment variables.
    
    All settings are loaded from .env file with type safety.
    Uses Pydantic v2 BaseSettings for professional config management.
    """
    
    # ========================================
    # PostgreSQL Configuration
    # ========================================
    db_host: str = Field(default="postgres", description="PostgreSQL host")
    db_port: int = Field(default=5432, description="PostgreSQL port")
    db_user: str = Field(default="ecommerce_user", description="PostgreSQL user")
    db_password: str = Field(default="secure_password", description="PostgreSQL password")
    db_name: str = Field(default="ecommerce_tracker", description="PostgreSQL database name")
    
    # ========================================
    # API Configuration
    # ========================================
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8000, description="API port number")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # ========================================
    # Scraping Configuration
    # ========================================
    playwright_headless: bool = Field(
        default=True,
        description="Run Playwright in headless mode (no UI)"
    )
    max_concurrent_scrapers: int = Field(
        default=5,
        description="Maximum number of concurrent scraper instances"
    )
    scraper_timeout: int = Field(
        default=30000,
        description="Scraper timeout in milliseconds"
    )
    retry_attempts: int = Field(
        default=3,
        description="Maximum retry attempts for failed scrapes"
    )
    
    # ========================================
    # Logging Configuration
    # ========================================
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")
    log_file: str = Field(default="logs/app.log", description="Log file path")
    
    # ========================================
    # Pydantic v2 Configuration
    # ========================================
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }
    
    # ========================================
    # Properties
    # ========================================
    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection string for SQLAlchemy."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    @property
    def scraper_timeout_seconds(self) -> float:
        """Convert scraper timeout from milliseconds to seconds."""
        return self.scraper_timeout / 1000


# Singleton instance of settings
settings = Settings()
