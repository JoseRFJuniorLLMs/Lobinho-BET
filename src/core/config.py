"""
Configuration - LOBINHO-BET
============================
Centralized settings using Pydantic.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://lobinho:lobinho123@localhost:5432/lobinho_bet",
        alias="DATABASE_URL"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL"
    )

    # Neo4j
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        alias="NEO4J_URI"
    )
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="lobinho123", alias="NEO4J_PASSWORD")

    # API Keys
    footystats_api_key: Optional[str] = Field(default=None, alias="FOOTYSTATS_API_KEY")
    odds_api_key: Optional[str] = Field(default=None, alias="ODDS_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")

    # Telegram
    telegram_bot_token: Optional[str] = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(default=None, alias="TELEGRAM_CHAT_ID")

    # Discord
    discord_webhook_url: Optional[str] = Field(default=None, alias="DISCORD_WEBHOOK_URL")

    # App Settings
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    timezone: str = Field(default="America/Sao_Paulo", alias="TIMEZONE")

    # Betting Strategy
    default_stake_percent: float = Field(default=2.0, alias="DEFAULT_STAKE_PERCENT")
    max_stake_percent: float = Field(default=5.0, alias="MAX_STAKE_PERCENT")
    min_value_threshold: float = Field(default=0.05, alias="MIN_VALUE_THRESHOLD")
    min_odds: float = Field(default=1.50, alias="MIN_ODDS")
    max_odds: float = Field(default=3.50, alias="MAX_ODDS")

    # Dashboard
    dashboard_host: str = Field(default="0.0.0.0")
    dashboard_port: int = Field(default=8000)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def sync_database_url(self) -> str:
        """Convert async URL to sync for Alembic/scripts."""
        return self.database_url.replace("+asyncpg", "")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
