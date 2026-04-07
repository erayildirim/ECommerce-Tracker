"""Application configuration management."""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # PostgreSQL Configuration
    db_host: str = "postgres"
    db_port: int = 5432
    db_user: str = "ecommerce_user"
    db_password: str = "secure_password"
    db_name: str = "ecommerce_tracker"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    # Scraping Configuration
    playwright_headless: bool = True
    max_concurrent_scrapers: int = 5
    request_timeout: int = 30
    retry_attempts: int = 3
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection string."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
