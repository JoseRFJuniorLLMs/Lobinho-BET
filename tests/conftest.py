"""
Pytest Configuration - LOBINHO-BET
===================================
Fixtures and configuration for all tests.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.database.models import Base, League, Team, Match, MatchStatus
from src.database.repository import UnitOfWork


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def engine():
    """Create SQLite in-memory engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def unit_of_work(engine) -> Generator[UnitOfWork, None, None]:
    """Create UnitOfWork for testing."""
    SessionLocal = sessionmaker(bind=engine)

    class TestUnitOfWork(UnitOfWork):
        def __init__(self):
            self.session = SessionLocal()
            super().__init__(self.session)

    uow = TestUnitOfWork()
    try:
        yield uow
    finally:
        uow.rollback()


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_league(db_session) -> League:
    """Create a sample league."""
    league = League(
        external_id="brasileirao_a_2025",
        name="Brasileirao Serie A",
        country="Brazil",
        season="2025",
        priority=1,
        is_active=True,
        min_edge=5.0,
        max_stake=3.0
    )
    db_session.add(league)
    db_session.commit()
    return league


@pytest.fixture
def sample_teams(db_session, sample_league) -> tuple[Team, Team]:
    """Create sample teams."""
    team_home = Team(
        external_id="flamengo_2025",
        name="Flamengo",
        short_name="FLA",
        country="Brazil",
        league_id=sample_league.id,
        squad_value=250.0,
        elo_rating=1650,
        attack_strength=1.25,
        defense_strength=1.10
    )
    team_away = Team(
        external_id="palmeiras_2025",
        name="Palmeiras",
        short_name="PAL",
        country="Brazil",
        league_id=sample_league.id,
        squad_value=220.0,
        elo_rating=1620,
        attack_strength=1.18,
        defense_strength=1.15
    )
    db_session.add_all([team_home, team_away])
    db_session.commit()
    return team_home, team_away


@pytest.fixture
def sample_match(db_session, sample_league, sample_teams) -> Match:
    """Create a sample match."""
    home_team, away_team = sample_teams
    match = Match(
        external_id="fla_pal_2025_01",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        league_id=sample_league.id,
        kickoff=datetime.now() + timedelta(days=1),
        status=MatchStatus.SCHEDULED
    )
    db_session.add(match)
    db_session.commit()
    return match


@pytest.fixture
def sample_events() -> list[dict]:
    """Sample events for testing predictors."""
    return [
        {
            "id": "1",
            "home_team": {"name": "Flamengo"},
            "away_team": {"name": "Palmeiras"},
            "league": "brasileirao_a",
            "kickoff": datetime.now().isoformat(),
            "home_form": "WDWWL",
            "away_form": "WWDLW",
            "h2h_results": "WDLWD",
            "odds": {"home": 2.10, "draw": 3.40, "away": 3.20},
        },
        {
            "id": "2",
            "home_team": {"name": "Manchester City"},
            "away_team": {"name": "Liverpool"},
            "league": "premier_league",
            "kickoff": datetime.now().isoformat(),
            "home_form": "WWWWW",
            "away_form": "WDWWW",
            "h2h_results": "DWWLD",
            "odds": {"home": 1.75, "draw": 3.80, "away": 4.50},
        },
    ]


# ============================================================================
# ASYNC FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_odds_response() -> dict:
    """Mock response from The Odds API."""
    return {
        "id": "abc123",
        "sport_key": "soccer_brazil_campeonato",
        "sport_title": "Brazil Campeonato",
        "commence_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "home_team": "Flamengo",
        "away_team": "Palmeiras",
        "bookmakers": [
            {
                "key": "pinnacle",
                "title": "Pinnacle",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Flamengo", "price": 2.10},
                            {"name": "Draw", "price": 3.40},
                            {"name": "Palmeiras", "price": 3.20},
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_footystats_match() -> dict:
    """Mock response from FootyStats."""
    return {
        "id": 12345,
        "homeID": 100,
        "awayID": 200,
        "home_name": "Flamengo",
        "away_name": "Palmeiras",
        "date_unix": int((datetime.now() + timedelta(days=1)).timestamp()),
        "competition_id": 99,
        "homeGoalCount": None,
        "awayGoalCount": None,
        "status": "scheduled",
        "home_ppg": 2.1,
        "away_ppg": 1.9,
        "pre_match_home_xg": 1.5,
        "pre_match_away_xg": 1.2,
    }
