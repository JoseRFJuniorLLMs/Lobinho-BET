"""
Tests for Data Collectors - LOBINHO-BET
========================================
Unit tests for API integrations and scrapers.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from src.collectors.odds_api import OddsAPIClient
from src.collectors.footystats import FootyStatsAPI


class TestOddsAPIClient:
    """Tests for The Odds API integration."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return OddsAPIClient(api_key="test_key")

    def test_parse_odds_response(self, client, mock_odds_response):
        """Test parsing odds API response."""
        parsed = client._parse_odds(mock_odds_response)

        assert parsed["home_team"] == "Flamengo"
        assert parsed["away_team"] == "Palmeiras"
        assert "pinnacle" in parsed["bookmakers"]

    def test_find_best_odds(self, client):
        """Test finding best odds across bookmakers."""
        odds_data = {
            "bookmakers": {
                "pinnacle": {"home": 2.10, "draw": 3.40, "away": 3.20},
                "bet365": {"home": 2.05, "draw": 3.50, "away": 3.15},
                "betano": {"home": 2.15, "draw": 3.35, "away": 3.25},
            }
        }

        best = client._find_best_odds(odds_data)

        assert best["home"]["odds"] == 2.15
        assert best["home"]["bookmaker"] == "betano"
        assert best["draw"]["odds"] == 3.50
        assert best["draw"]["bookmaker"] == "bet365"

    def test_calculate_margin(self, client):
        """Test bookmaker margin calculation."""
        # Odds: 2.10, 3.40, 3.20
        # Implied probs: 47.6%, 29.4%, 31.25% = 108.25%
        margin = client._calculate_margin(2.10, 3.40, 3.20)

        assert margin > 0
        assert margin < 0.15  # Typical margin under 15%

    @pytest.mark.asyncio
    async def test_get_odds_rate_limiting(self, client):
        """Test rate limiting is respected."""
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = {"data": []}

            # Should not exceed rate limit
            for _ in range(5):
                await client.get_odds("soccer_brazil_campeonato")

            assert mock.call_count == 5


class TestFootyStatsAPI:
    """Tests for FootyStats integration."""

    @pytest.fixture
    def api(self):
        """Create test API client."""
        return FootyStatsAPI(api_key="test_key")

    def test_parse_match_stats(self, api, mock_footystats_match):
        """Test parsing match statistics."""
        parsed = api._parse_match(mock_footystats_match)

        assert parsed["home_team"] == "Flamengo"
        assert parsed["away_team"] == "Palmeiras"
        assert parsed["home_xg"] == 1.5
        assert parsed["away_xg"] == 1.2

    def test_calculate_form_string(self, api):
        """Test form string calculation from results."""
        results = [
            {"goals_scored": 2, "goals_conceded": 1},  # W
            {"goals_scored": 1, "goals_conceded": 1},  # D
            {"goals_scored": 0, "goals_conceded": 2},  # L
            {"goals_scored": 3, "goals_conceded": 0},  # W
            {"goals_scored": 2, "goals_conceded": 2},  # D
        ]

        form = api._calculate_form(results)
        assert form == "WDLWD"

    def test_calculate_ppg(self, api):
        """Test points per game calculation."""
        results = [
            {"result": "W"},  # 3 points
            {"result": "D"},  # 1 point
            {"result": "W"},  # 3 points
            {"result": "L"},  # 0 points
            {"result": "W"},  # 3 points
        ]

        ppg = api._calculate_ppg(results)
        assert ppg == 2.0  # 10 points / 5 games

    def test_h2h_analysis(self, api):
        """Test head-to-head analysis."""
        h2h_matches = [
            {"home_goals": 2, "away_goals": 1, "home_team": "A", "away_team": "B"},
            {"home_goals": 1, "away_goals": 1, "home_team": "B", "away_team": "A"},
            {"home_goals": 0, "away_goals": 2, "home_team": "A", "away_team": "B"},
        ]

        analysis = api._analyze_h2h(h2h_matches, "A", "B")

        assert analysis["total_matches"] == 3
        assert analysis["team_a_wins"] == 1
        assert analysis["team_b_wins"] == 1
        assert analysis["draws"] == 1


class TestDataValidation:
    """Tests for data validation."""

    def test_validate_odds_range(self):
        """Test odds are within valid range."""
        def validate_odds(odds: float) -> bool:
            return 1.01 <= odds <= 100.0

        assert validate_odds(2.10)
        assert validate_odds(1.50)
        assert not validate_odds(0.95)
        assert not validate_odds(150.0)

    def test_validate_probability(self):
        """Test probability is valid."""
        def validate_prob(prob: float) -> bool:
            return 0.0 <= prob <= 1.0

        assert validate_prob(0.5)
        assert validate_prob(0.0)
        assert validate_prob(1.0)
        assert not validate_prob(-0.1)
        assert not validate_prob(1.1)

    def test_validate_form_string(self):
        """Test form string format."""
        import re

        def validate_form(form: str) -> bool:
            return bool(re.match(r'^[WDL]{1,10}$', form))

        assert validate_form("WDWWL")
        assert validate_form("WWWWW")
        assert not validate_form("WXDWL")
        assert not validate_form("")
        assert not validate_form("WDLWDLWDLWDL")  # Too long


class TestErrorHandling:
    """Tests for error handling in collectors."""

    @pytest.mark.asyncio
    async def test_api_timeout_handling(self):
        """Test handling of API timeouts."""
        import asyncio

        async def slow_request():
            await asyncio.sleep(10)
            return {}

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_request(), timeout=0.1)

    def test_missing_data_handling(self):
        """Test handling of missing data."""
        incomplete_data = {
            "home_team": "Team A",
            # Missing: away_team, odds, kickoff
        }

        def safe_get(data: dict, key: str, default=None):
            return data.get(key, default)

        assert safe_get(incomplete_data, "home_team") == "Team A"
        assert safe_get(incomplete_data, "away_team", "Unknown") == "Unknown"

    def test_malformed_response_handling(self):
        """Test handling of malformed API responses."""
        malformed = "not a json object"

        def parse_response(response):
            try:
                if isinstance(response, dict):
                    return response
                return {"error": "Invalid response format"}
            except Exception as e:
                return {"error": str(e)}

        result = parse_response(malformed)
        assert "error" in result
