"""
LOBINHO-BET - Configuration Settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./data/lobinho.db")
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Neo4j Graph Database
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="lobinho123")

    # API Keys
    footystats_api_key: Optional[str] = None
    odds_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Discord
    discord_webhook_url: Optional[str] = None

    # App Settings
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    timezone: str = Field(default="America/Sao_Paulo")

    # Betting Strategy
    default_stake_percent: float = Field(default=2.0)
    max_stake_percent: float = Field(default=5.0)
    min_value_threshold: float = Field(default=0.05)  # 5% edge minimum
    min_odds: float = Field(default=1.50)
    max_odds: float = Field(default=3.50)

    # API URLs
    footystats_base_url: str = "https://api.footystats.org/v1"
    odds_api_base_url: str = "https://api.the-odds-api.com/v4"
    fbref_base_url: str = "https://fbref.com"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
