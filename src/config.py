"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # App
    app_name: str = Field(default="InfoFlow", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./infoflow.db",
        description="Database connection URL",
    )
    
    # X (Twitter) API
    x_api_key: Optional[str] = Field(default=None, description="X API key")
    x_api_secret: Optional[str] = Field(default=None, description="X API secret")
    x_access_token: Optional[str] = Field(default=None, description="X access token")
    x_access_token_secret: Optional[str] = Field(default=None, description="X access token secret")
    x_bearer_token: Optional[str] = Field(default=None, description="X bearer token")
    
    # Reddit API
    reddit_client_id: Optional[str] = Field(default=None, description="Reddit client ID")
    reddit_client_secret: Optional[str] = Field(default=None, description="Reddit client secret")
    reddit_user_agent: str = Field(
        default="InfoFlow/0.1.0",
        description="Reddit user agent",
    )
    
    # Telegram
    telegram_bot_token: Optional[str] = Field(default=None, description="Telegram bot token")
    telegram_chat_id: Optional[str] = Field(default=None, description="Telegram chat ID")
    
    # Scheduler
    fetch_interval_minutes: int = Field(default=240, description="Fetch interval in minutes")
    brief_generation_hour: int = Field(default=8, description="Brief generation hour (0-23)")
    brief_send_hour: int = Field(default=8, description="Brief send hour (0-23)")
    brief_send_minute: int = Field(default=30, description="Brief send minute (0-59)")
    
    # Scoring weights
    heat_score_weight: float = Field(default=0.6, description="Heat score weight (0-1)")
    potential_score_weight: float = Field(default=0.4, description="Potential score weight (0-1)")
    
    # Feature flags
    enable_x_fetcher: bool = Field(default=True, description="Enable X fetcher")
    enable_reddit_fetcher: bool = Field(default=True, description="Enable Reddit fetcher")
    enable_rss_fetcher: bool = Field(default=True, description="Enable RSS fetcher")
    enable_telegram_push: bool = Field(default=True, description="Enable Telegram push")
    enable_email_push: bool = Field(default=False, description="Enable email push")
    
    @property
    def database_async_url(self) -> str:
        """Get async database URL."""
        if self.database_url.startswith("sqlite"):
            return self.database_url.replace("sqlite://", "sqlite+aiosqlite://")
        elif self.database_url.startswith("postgresql"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.database_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
