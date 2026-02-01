"""
Tests for Database Repository - LOBINHO-BET
============================================
Unit tests for CRUD operations and UnitOfWork.
"""

import pytest
from datetime import datetime, timedelta

from src.database.models import (
    League, Team, Match, MatchStatus, ValueBet, BetSignal,
    Bet, BetStatus, OddsHistory
)
from src.database.repository import (
    LeagueRepository, TeamRepository, MatchRepository,
    ValueBetRepository, BetRepository
)


class TestLeagueRepository:
    """Tests for League CRUD operations."""

    def test_create_league(self, db_session):
        """Test creating a new league."""
        repo = LeagueRepository(db_session)
        league = repo.create(
            external_id="test_league",
            name="Test League",
            country="Brazil",
            priority=1
        )

        assert league.id is not None
        assert league.name == "Test League"
        assert league.country == "Brazil"

    def test_get_by_external_id(self, db_session, sample_league):
        """Test fetching league by external ID."""
        repo = LeagueRepository(db_session)
        league = repo.get_by_external_id("brasileirao_a_2025")

        assert league is not None
        assert league.name == "Brasileirao Serie A"

    def test_get_active_leagues(self, db_session, sample_league):
        """Test fetching only active leagues."""
        repo = LeagueRepository(db_session)
        active = repo.get_active()

        assert len(active) >= 1
        assert all(l.is_active for l in active)

    def test_update_league(self, db_session, sample_league):
        """Test updating league."""
        repo = LeagueRepository(db_session)
        repo.update(sample_league, min_edge=7.5)

        assert sample_league.min_edge == 7.5


class TestTeamRepository:
    """Tests for Team CRUD operations."""

    def test_create_team(self, db_session, sample_league):
        """Test creating a new team."""
        repo = TeamRepository(db_session)
        team = repo.create(
            external_id="test_team",
            name="Test FC",
            country="Brazil",
            league_id=sample_league.id,
            elo_rating=1550
        )

        assert team.id is not None
        assert team.name == "Test FC"
        assert team.elo_rating == 1550

    def test_get_by_name(self, db_session, sample_teams):
        """Test fetching team by name."""
        repo = TeamRepository(db_session)
        team = repo.get_by_name("Flamengo")

        assert team is not None
        assert team.external_id == "flamengo_2025"

    def test_get_by_league(self, db_session, sample_league, sample_teams):
        """Test fetching teams by league."""
        repo = TeamRepository(db_session)
        teams = repo.get_by_league(sample_league.id)

        assert len(teams) == 2

    def test_update_elo(self, db_session, sample_teams):
        """Test updating team ELO rating."""
        home_team, _ = sample_teams
        repo = TeamRepository(db_session)

        repo.update(home_team, elo_rating=1700)

        assert home_team.elo_rating == 1700


class TestMatchRepository:
    """Tests for Match CRUD operations."""

    def test_create_match(self, db_session, sample_teams, sample_league):
        """Test creating a new match."""
        home, away = sample_teams
        repo = MatchRepository(db_session)

        match = repo.create(
            external_id="test_match_1",
            home_team_id=home.id,
            away_team_id=away.id,
            league_id=sample_league.id,
            kickoff=datetime.now() + timedelta(hours=3)
        )

        assert match.id is not None
        assert match.status == MatchStatus.SCHEDULED

    def test_get_upcoming(self, db_session, sample_match):
        """Test fetching upcoming matches."""
        repo = MatchRepository(db_session)
        upcoming = repo.get_upcoming(hours=48)

        assert len(upcoming) >= 1

    def test_update_result(self, db_session, sample_match):
        """Test updating match result."""
        repo = MatchRepository(db_session)

        repo.update(
            sample_match,
            home_goals=2,
            away_goals=1,
            status=MatchStatus.FINISHED
        )

        assert sample_match.home_goals == 2
        assert sample_match.away_goals == 1
        assert sample_match.status == MatchStatus.FINISHED

    def test_get_by_status(self, db_session, sample_match):
        """Test fetching matches by status."""
        repo = MatchRepository(db_session)
        scheduled = repo.get_by_status(MatchStatus.SCHEDULED)

        assert len(scheduled) >= 1


class TestValueBetRepository:
    """Tests for ValueBet CRUD operations."""

    def test_create_value_bet(self, db_session, sample_match):
        """Test creating a value bet."""
        repo = ValueBetRepository(db_session)

        vb = repo.create(
            match_id=sample_match.id,
            market="1x2",
            selection="home",
            odds=2.15,
            fair_odds=1.90,
            probability=0.526,
            edge=7.5,
            confidence=0.85,
            kelly_stake=2.5,
            signal=BetSignal.STRONG_BUY
        )

        assert vb.id is not None
        assert vb.edge == 7.5
        assert vb.signal == BetSignal.STRONG_BUY

    def test_get_unnotified(self, db_session, sample_match):
        """Test fetching unnotified value bets."""
        repo = ValueBetRepository(db_session)

        # Create unnotified bet
        repo.create(
            match_id=sample_match.id,
            market="over_25",
            selection="over",
            odds=1.85,
            edge=5.0,
            notified=False
        )

        unnotified = repo.get_unnotified()
        assert len(unnotified) >= 1

    def test_mark_notified(self, db_session, sample_match):
        """Test marking bet as notified."""
        repo = ValueBetRepository(db_session)

        vb = repo.create(
            match_id=sample_match.id,
            market="btts",
            selection="yes",
            odds=1.75,
            edge=4.0
        )

        repo.mark_notified(vb.id)

        assert vb.notified is True
        assert vb.notified_at is not None


class TestBetRepository:
    """Tests for Bet CRUD operations."""

    def test_create_bet(self, db_session, sample_match):
        """Test creating a bet."""
        repo = BetRepository(db_session)

        bet = repo.create(
            match_id=sample_match.id,
            bookmaker="pinnacle",
            market="1x2",
            selection="home",
            odds=2.10,
            stake=50.0
        )

        assert bet.id is not None
        assert bet.status == BetStatus.PENDING
        assert bet.potential_return == 105.0

    def test_settle_bet_won(self, db_session, sample_match):
        """Test settling a winning bet."""
        repo = BetRepository(db_session)

        bet = repo.create(
            match_id=sample_match.id,
            bookmaker="bet365",
            market="1x2",
            selection="away",
            odds=3.20,
            stake=30.0
        )

        repo.settle_bet(bet.id, BetStatus.WON)

        assert bet.status == BetStatus.WON
        assert bet.profit == 66.0  # (3.20 * 30) - 30
        assert bet.settled_at is not None

    def test_settle_bet_lost(self, db_session, sample_match):
        """Test settling a losing bet."""
        repo = BetRepository(db_session)

        bet = repo.create(
            match_id=sample_match.id,
            bookmaker="betano",
            market="over_25",
            selection="over",
            odds=1.90,
            stake=25.0
        )

        repo.settle_bet(bet.id, BetStatus.LOST)

        assert bet.status == BetStatus.LOST
        assert bet.profit == -25.0

    def test_get_pending(self, db_session, sample_match):
        """Test fetching pending bets."""
        repo = BetRepository(db_session)

        repo.create(
            match_id=sample_match.id,
            bookmaker="pinnacle",
            market="1x2",
            selection="draw",
            odds=3.50,
            stake=20.0
        )

        pending = repo.get_pending()
        assert len(pending) >= 1
        assert all(b.status == BetStatus.PENDING for b in pending)


class TestOddsHistory:
    """Tests for odds tracking."""

    def test_record_odds(self, db_session, sample_match):
        """Test recording odds history."""
        odds = OddsHistory(
            match_id=sample_match.id,
            bookmaker="pinnacle",
            home_odds=2.10,
            draw_odds=3.40,
            away_odds=3.20,
            over_25_odds=1.85,
            under_25_odds=1.95
        )
        db_session.add(odds)
        db_session.commit()

        assert odds.id is not None
        assert odds.timestamp is not None


class TestUnitOfWork:
    """Tests for transaction management."""

    def test_commit(self, unit_of_work):
        """Test committing transaction."""
        league = League(
            external_id="uow_test",
            name="UOW Test League",
            country="Test"
        )
        unit_of_work.session.add(league)
        unit_of_work.commit()

        assert league.id is not None

    def test_rollback(self, unit_of_work):
        """Test rolling back transaction."""
        initial_count = unit_of_work.session.query(League).count()

        league = League(
            external_id="rollback_test",
            name="Rollback League",
            country="Test"
        )
        unit_of_work.session.add(league)
        unit_of_work.rollback()

        final_count = unit_of_work.session.query(League).count()
        assert final_count == initial_count
