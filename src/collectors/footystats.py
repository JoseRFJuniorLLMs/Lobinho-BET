"""
FootyStats API Collector
========================
Main data source for historical stats, league data, and match predictions.

API Docs: https://footystats.org/api/
"""

from typing import Optional
from datetime import datetime, date
from loguru import logger

from .base import BaseCollector
from config import get_settings


class FootyStatsCollector(BaseCollector):
    """
    Collector for FootyStats API.

    Provides:
    - League standings and stats
    - Team statistics (goals, xG, form)
    - Match predictions
    - H2H data
    - Over/Under & BTTS stats
    """

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        super().__init__(
            base_url=settings.footystats_base_url,
            api_key=api_key or settings.footystats_api_key,
        )

    def _get_headers(self) -> dict:
        headers = super()._get_headers()
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def get_leagues(self, country: Optional[str] = None) -> list[dict]:
        """
        Get available leagues.

        Args:
            country: Filter by country name (e.g., "Brazil", "England")
        """
        params = {}
        if country:
            params["country"] = country

        response = await self.get("leagues", params=params)
        logger.info(f"Fetched {len(response.get('data', []))} leagues")
        return response.get("data", [])

    async def get_matches(
        self,
        league_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status: str = "scheduled",  # scheduled, live, finished
    ) -> list[dict]:
        """
        Get matches with optional filters.

        Args:
            league_id: Filter by specific league
            date_from: Start date
            date_to: End date
            status: Match status filter
        """
        params = {"status": status}

        if league_id:
            params["league_id"] = league_id
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()

        response = await self.get("matches", params=params)
        matches = response.get("data", [])
        logger.info(f"Fetched {len(matches)} matches")
        return matches

    async def get_match_details(self, match_id: int) -> dict:
        """Get detailed match information including stats and lineups."""
        response = await self.get(f"matches/{match_id}")
        return response.get("data", {})

    async def get_team_stats(self, team_id: str) -> dict:
        """
        Get comprehensive team statistics.

        Returns:
        - Form (last 5/10 games)
        - Goals scored/conceded averages
        - Over/Under percentages
        - BTTS percentage
        - Home/Away splits
        """
        response = await self.get(f"teams/{team_id}/stats")
        return response.get("data", {})

    async def get_team_form(self, team_id: str, last_n: int = 5) -> list[dict]:
        """Get team's recent form (last N matches)."""
        params = {"limit": last_n}
        response = await self.get(f"teams/{team_id}/form", params=params)
        return response.get("data", [])

    async def get_h2h(self, team1_id: str, team2_id: str) -> dict:
        """
        Get head-to-head statistics between two teams.

        Returns:
        - Previous meetings
        - Win/Draw/Loss record
        - Goals stats
        - Trends
        """
        params = {"team1": team1_id, "team2": team2_id}
        response = await self.get("h2h", params=params)
        return response.get("data", {})

    async def get_league_table(self, league_id: int, season: Optional[str] = None) -> dict:
        """Get league standings/table."""
        params = {}
        if season:
            params["season"] = season

        response = await self.get(f"leagues/{league_id}/table", params=params)
        return response.get("data", {})

    async def get_over_under_stats(
        self,
        league_id: int,
        line: float = 2.5,
    ) -> list[dict]:
        """
        Get Over/Under statistics for teams in a league.

        Args:
            league_id: League to analyze
            line: O/U line (e.g., 2.5, 1.5, 3.5)
        """
        params = {"line": line}
        response = await self.get(f"leagues/{league_id}/over-under", params=params)
        return response.get("data", [])

    async def get_btts_stats(self, league_id: int) -> list[dict]:
        """Get Both Teams To Score statistics for a league."""
        response = await self.get(f"leagues/{league_id}/btts")
        return response.get("data", [])

    async def get_predictions(self, match_id: int) -> dict:
        """
        Get FootyStats predictions for a match.

        Returns predicted probabilities for:
        - Match result (1X2)
        - Over/Under
        - BTTS
        - Correct score
        """
        response = await self.get(f"matches/{match_id}/predictions")
        return response.get("data", {})


# Convenience function
async def fetch_today_matches(league_ids: Optional[list[int]] = None) -> list[dict]:
    """Fetch all matches scheduled for today."""
    today = date.today()
    all_matches = []

    async with FootyStatsCollector() as collector:
        if league_ids:
            for league_id in league_ids:
                matches = await collector.get_matches(
                    league_id=league_id,
                    date_from=today,
                    date_to=today,
                )
                all_matches.extend(matches)
        else:
            all_matches = await collector.get_matches(
                date_from=today,
                date_to=today,
            )

    return all_matches
