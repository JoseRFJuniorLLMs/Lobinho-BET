"""
Database Initialization Script - LOBINHO-BET
=============================================
Creates tables and seeds initial data.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

from src.core.config import get_settings
from src.database.models import Base, League, Team, SystemConfig
from src.strategy.leagues import LEAGUES


def init_database():
    """Initialize database with tables and seed data."""
    settings = get_settings()
    logger.info(f"Connecting to database: {settings.database_url[:50]}...")

    # Create engine
    engine = create_engine(settings.database_url, echo=False)

    # Create all tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(engine)
    logger.info("Tables created successfully")

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Seed leagues
        logger.info("Seeding leagues...")
        seed_leagues(session)

        # Seed system config
        logger.info("Seeding system config...")
        seed_config(session)

        session.commit()
        logger.info("Database initialization complete!")

    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def seed_leagues(session):
    """Seed initial leagues from config."""
    for league_key, league_config in LEAGUES.items():
        # Check if exists
        existing = session.query(League).filter_by(external_id=league_key).first()
        if existing:
            continue

        league = League(
            external_id=league_key,
            name=league_config.name,
            country=league_config.country,
            priority=league_config.priority.value if hasattr(league_config.priority, 'value') else league_config.priority,
            is_active=league_config.is_active,
            footystats_id=league_config.footystats_id,
            odds_api_key=league_config.odds_api_key,
            min_edge=5.0,
            max_stake=3.0,
        )
        session.add(league)
        logger.debug(f"Added league: {league.name}")

    logger.info(f"Seeded {len(LEAGUES)} leagues")


def seed_config(session):
    """Seed system configuration defaults."""
    defaults = {
        "bankroll": ("1000.0", "float", "Current bankroll balance"),
        "min_edge": ("5.0", "float", "Minimum edge for value bets (%)"),
        "max_stake": ("3.0", "float", "Maximum stake per bet (% of bankroll)"),
        "kelly_fraction": ("0.25", "float", "Kelly criterion fraction"),
        "telegram_enabled": ("false", "bool", "Enable Telegram notifications"),
        "auto_bet": ("false", "bool", "Enable automatic betting"),
        "update_interval": ("60", "int", "Data update interval in seconds"),
    }

    for key, (value, value_type, description) in defaults.items():
        existing = session.query(SystemConfig).filter_by(key=key).first()
        if existing:
            continue

        config = SystemConfig(
            key=key,
            value=value,
            value_type=value_type,
            description=description,
        )
        session.add(config)

    logger.info("Seeded system config")


def reset_database():
    """Drop and recreate all tables (DANGEROUS!)."""
    settings = get_settings()
    logger.warning("RESETTING DATABASE - All data will be lost!")

    engine = create_engine(settings.database_url, echo=False)
    Base.metadata.drop_all(engine)
    logger.info("All tables dropped")

    Base.metadata.create_all(engine)
    logger.info("Tables recreated")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize LOBINHO-BET database")
    parser.add_argument("--reset", action="store_true", help="Reset database (drops all data)")
    args = parser.parse_args()

    if args.reset:
        confirm = input("This will DELETE ALL DATA. Type 'yes' to confirm: ")
        if confirm.lower() == "yes":
            reset_database()
            init_database()
        else:
            print("Cancelled.")
    else:
        init_database()
