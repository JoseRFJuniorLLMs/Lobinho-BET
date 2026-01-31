"""
Data Collectors for LOBINHO-BET
================================

Collectors:
- FootyStatsCollector: Main data source (API)
- OddsAPICollector: Real-time odds (API)
- FBrefScraper: Advanced xG metrics (Scraping)
"""

from .footystats import FootyStatsCollector, fetch_today_matches
from .odds_api import OddsAPICollector, fetch_brazil_odds
from .fbref import FBrefScraper, fetch_league_xg

__all__ = [
    "FootyStatsCollector",
    "OddsAPICollector",
    "FBrefScraper",
    "fetch_today_matches",
    "fetch_brazil_odds",
    "fetch_league_xg",
]
