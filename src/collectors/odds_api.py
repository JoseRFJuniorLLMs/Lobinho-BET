"""
The Odds API Collector
======================
Real-time odds from multiple bookmakers.

API Docs: https://the-odds-api.com/
Free tier: 500 requests/month
"""

from typing import Optional
from datetime import datetime
from loguru import logger

from .base import BaseCollector
from config import get_settings


class OddsAPICollector(BaseCollector):
    """
    Collector for The Odds API.

    Provides:
    - Real-time odds from 40+ bookmakers
    - Multiple sports coverage
    - Historical odds data
    - Line movements
    """

    # Popular soccer leagues/competitions
    SPORTS = {
        "soccer_brazil_serie_a": "Brasileirao Serie A",
        "soccer_brazil_serie_b": "Brasileirao Serie B",
        "soccer_epl": "English Premier League",
        "soccer_spain_la_liga": "La Liga",
        "soccer_germany_bundesliga": "Bundesliga",
        "soccer_italy_serie_a": "Serie A Italy",
        "soccer_france_ligue_one": "Ligue 1",
        "soccer_uefa_champs_league": "Champions League",
        "soccer_uefa_europa_league": "Europa League",
        "soccer_conmebol_libertadores": "Libertadores",
    }

    # Popular bookmakers
    BOOKMAKERS = {
        "bet365": "Bet365",
        "pinnacle": "Pinnacle",
        "betfair": "Betfair Exchange",
        "williamhill": "William Hill",
        "1xbet": "1xBet",
        "betway": "Betway",
    }

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        super().__init__(
            base_url=settings.odds_api_base_url,
            api_key=api_key or settings.odds_api_key,
        )

    def _add_api_key(self, params: dict) -> dict:
        """Add API key to request params."""
        if self.api_key:
            params["apiKey"] = self.api_key
        return params

    async def get_sports(self, all_sports: bool = False) -> list[dict]:
        """
        Get list of available sports.

        Args:
            all_sports: Include out-of-season sports
        """
        params = self._add_api_key({"all": str(all_sports).lower()})
        response = await self.get("sports", params=params)
        return response if isinstance(response, list) else []

    async def get_matches(
        self,
        sport: str = "soccer_brazil_serie_a",
        regions: str = "us,uk,eu",
        markets: str = "h2h",
        odds_format: str = "decimal",
        **kwargs,
    ) -> list[dict]:
        """
        Get upcoming matches with odds.

        Args:
            sport: Sport key (e.g., 'soccer_brazil_serie_a')
            regions: Bookmaker regions (us, uk, eu, au)
            markets: Markets to return (h2h, spreads, totals)
            odds_format: decimal or american
        """
        params = self._add_api_key({
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format,
        })

        response = await self.get(f"sports/{sport}/odds", params=params)
        matches = response if isinstance(response, list) else []
        logger.info(f"Fetched odds for {len(matches)} matches in {sport}")
        return matches

    async def get_team_stats(self, team_id: str) -> dict:
        """Not available in Odds API - use FootyStats instead."""
        raise NotImplementedError("Team stats not available in Odds API")

    async def get_live_odds(
        self,
        sport: str,
        event_id: Optional[str] = None,
    ) -> list[dict]:
        """Get live/in-play odds for matches."""
        params = self._add_api_key({
            "regions": "us,uk,eu",
            "markets": "h2h",
        })

        if event_id:
            response = await self.get(f"sports/{sport}/events/{event_id}/odds", params=params)
        else:
            response = await self.get(f"sports/{sport}/odds", params=params)

        return response if isinstance(response, list) else []

    async def get_historical_odds(
        self,
        sport: str,
        event_id: str,
        date: Optional[str] = None,
    ) -> dict:
        """
        Get historical odds for a specific event.
        Useful for tracking line movements.
        """
        params = self._add_api_key({
            "regions": "us,uk,eu",
            "markets": "h2h,totals",
        })
        if date:
            params["date"] = date

        response = await self.get(
            f"historical/sports/{sport}/events/{event_id}/odds",
            params=params,
        )
        return response if isinstance(response, dict) else {}

    async def get_all_soccer_odds(self, regions: str = "us,uk,eu") -> dict[str, list]:
        """Get odds for all major soccer leagues."""
        all_odds = {}

        for sport_key, sport_name in self.SPORTS.items():
            try:
                matches = await self.get_matches(sport=sport_key, regions=regions)
                if matches:
                    all_odds[sport_key] = matches
                    logger.info(f"Got {len(matches)} matches for {sport_name}")
            except Exception as e:
                logger.warning(f"Failed to get odds for {sport_name}: {e}")

        return all_odds

    def find_best_odds(self, match: dict, market: str = "h2h") -> dict:
        """
        Find best odds across all bookmakers for a match.

        Returns:
            dict with best odds for home, draw, away
        """
        best_odds = {
            "home": {"odds": 0, "bookmaker": None},
            "draw": {"odds": 0, "bookmaker": None},
            "away": {"odds": 0, "bookmaker": None},
        }

        bookmakers = match.get("bookmakers", [])

        for bookmaker in bookmakers:
            bookie_name = bookmaker.get("key")
            markets = bookmaker.get("markets", [])

            for mkt in markets:
                if mkt.get("key") != market:
                    continue

                outcomes = mkt.get("outcomes", [])
                for outcome in outcomes:
                    name = outcome.get("name", "").lower()
                    price = outcome.get("price", 0)

                    if "draw" in name:
                        if price > best_odds["draw"]["odds"]:
                            best_odds["draw"] = {"odds": price, "bookmaker": bookie_name}
                    elif outcome.get("name") == match.get("home_team"):
                        if price > best_odds["home"]["odds"]:
                            best_odds["home"] = {"odds": price, "bookmaker": bookie_name}
                    else:
                        if price > best_odds["away"]["odds"]:
                            best_odds["away"] = {"odds": price, "bookmaker": bookie_name}

        return best_odds

    def calculate_margin(self, odds: dict) -> float:
        """
        Calculate bookmaker margin from odds.

        Lower margin = better value for bettors.
        """
        if not all(odds.get(k, {}).get("odds", 0) > 0 for k in ["home", "draw", "away"]):
            return 0.0

        implied_prob = (
            1 / odds["home"]["odds"]
            + 1 / odds["draw"]["odds"]
            + 1 / odds["away"]["odds"]
        )

        margin = (implied_prob - 1) * 100
        return round(margin, 2)


# Convenience function
async def fetch_brazil_odds() -> list[dict]:
    """Fetch odds for Brazilian leagues."""
    async with OddsAPICollector() as collector:
        serie_a = await collector.get_matches(sport="soccer_brazil_serie_a")
        serie_b = await collector.get_matches(sport="soccer_brazil_serie_b")
        return serie_a + serie_b
