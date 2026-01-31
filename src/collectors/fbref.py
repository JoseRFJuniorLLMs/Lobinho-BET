"""
FBref Scraper
=============
Advanced metrics scraper for xG, xGA, and other StatsBomb data.

Source: https://fbref.com
Note: FBref doesn't have a public API, so we scrape the data.
"""

import re
from typing import Optional
from datetime import datetime
from bs4 import BeautifulSoup
import httpx
from loguru import logger

from config import get_settings


class FBrefScraper:
    """
    Scraper for FBref advanced football statistics.

    Provides:
    - Expected Goals (xG)
    - Expected Goals Against (xGA)
    - Shot statistics
    - Possession data
    - Pass completion rates
    - Defensive actions
    """

    # Major league URLs
    LEAGUES = {
        "premier_league": "/en/comps/9/Premier-League-Stats",
        "la_liga": "/en/comps/12/La-Liga-Stats",
        "serie_a": "/en/comps/11/Serie-A-Stats",
        "bundesliga": "/en/comps/20/Bundesliga-Stats",
        "ligue_1": "/en/comps/13/Ligue-1-Stats",
        "brasileirao": "/en/comps/24/Serie-A-Stats",
        "champions_league": "/en/comps/8/Champions-League-Stats",
        "libertadores": "/en/comps/14/Copa-Libertadores-Stats",
    }

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.fbref_base_url
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def _fetch_page(self, path: str) -> BeautifulSoup:
        """Fetch and parse a page."""
        url = f"{self.base_url}{path}"
        logger.debug(f"Fetching: {url}")

        response = await self.client.get(url)
        response.raise_for_status()

        return BeautifulSoup(response.text, "lxml")

    async def get_league_table(self, league: str) -> list[dict]:
        """
        Get league standings with xG data.

        Returns list of teams with:
        - Position, Team, Matches Played
        - Wins, Draws, Losses
        - Goals For/Against
        - xG, xGA, xGD
        - Points
        """
        if league not in self.LEAGUES:
            raise ValueError(f"League '{league}' not supported")

        soup = await self._fetch_page(self.LEAGUES[league])

        # Find the main standings table
        table = soup.find("table", {"id": re.compile(r"results.*overall")})
        if not table:
            logger.warning(f"Could not find standings table for {league}")
            return []

        standings = []
        tbody = table.find("tbody")
        if not tbody:
            return []

        for row in tbody.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) < 10:
                continue

            try:
                team_data = {
                    "position": self._safe_int(cells[0].get_text(strip=True)),
                    "team": cells[1].get_text(strip=True),
                    "matches_played": self._safe_int(cells[2].get_text(strip=True)),
                    "wins": self._safe_int(cells[3].get_text(strip=True)),
                    "draws": self._safe_int(cells[4].get_text(strip=True)),
                    "losses": self._safe_int(cells[5].get_text(strip=True)),
                    "goals_for": self._safe_int(cells[6].get_text(strip=True)),
                    "goals_against": self._safe_int(cells[7].get_text(strip=True)),
                    "goal_diff": self._safe_int(cells[8].get_text(strip=True)),
                    "points": self._safe_int(cells[9].get_text(strip=True)),
                    "xg": self._safe_float(cells[10].get_text(strip=True)) if len(cells) > 10 else None,
                    "xga": self._safe_float(cells[11].get_text(strip=True)) if len(cells) > 11 else None,
                }

                # Calculate xG difference
                if team_data["xg"] and team_data["xga"]:
                    team_data["xg_diff"] = round(team_data["xg"] - team_data["xga"], 2)

                standings.append(team_data)

            except Exception as e:
                logger.debug(f"Error parsing row: {e}")
                continue

        logger.info(f"Parsed {len(standings)} teams from {league}")
        return standings

    async def get_team_stats(self, team_url: str) -> dict:
        """
        Get detailed team statistics.

        Args:
            team_url: Relative URL to team page (e.g., "/en/squads/xxx/Team-Name")
        """
        soup = await self._fetch_page(team_url)

        stats = {
            "team_name": "",
            "league": "",
            "xg": 0.0,
            "xga": 0.0,
            "possession": 0.0,
            "shots_pg": 0.0,
            "shots_on_target_pg": 0.0,
            "pass_completion": 0.0,
        }

        # Extract team name
        header = soup.find("h1")
        if header:
            stats["team_name"] = header.get_text(strip=True).replace(" Stats", "")

        # Find stats tables
        for table in soup.find_all("table"):
            table_id = table.get("id", "")

            if "stats_shooting" in table_id:
                stats.update(self._parse_shooting_stats(table))
            elif "stats_passing" in table_id:
                stats.update(self._parse_passing_stats(table))
            elif "stats_possession" in table_id:
                stats.update(self._parse_possession_stats(table))

        return stats

    async def get_match_xg(self, match_url: str) -> dict:
        """
        Get xG data for a specific match.

        Args:
            match_url: Relative URL to match report
        """
        soup = await self._fetch_page(match_url)

        match_data = {
            "home_team": "",
            "away_team": "",
            "home_goals": 0,
            "away_goals": 0,
            "home_xg": 0.0,
            "away_xg": 0.0,
            "shots_home": 0,
            "shots_away": 0,
        }

        # Find scorebox
        scorebox = soup.find("div", class_="scorebox")
        if scorebox:
            teams = scorebox.find_all("strong")
            if len(teams) >= 2:
                match_data["home_team"] = teams[0].get_text(strip=True)
                match_data["away_team"] = teams[1].get_text(strip=True)

            scores = scorebox.find_all("div", class_="score")
            if len(scores) >= 2:
                match_data["home_goals"] = self._safe_int(scores[0].get_text(strip=True))
                match_data["away_goals"] = self._safe_int(scores[1].get_text(strip=True))

        # Find xG values
        xg_elements = soup.find_all("div", class_=re.compile(r".*xg.*", re.I))
        for elem in xg_elements:
            text = elem.get_text(strip=True)
            xg_val = self._safe_float(text)
            if xg_val:
                if not match_data["home_xg"]:
                    match_data["home_xg"] = xg_val
                else:
                    match_data["away_xg"] = xg_val

        return match_data

    async def get_upcoming_matches(self, league: str) -> list[dict]:
        """Get upcoming fixtures for a league."""
        soup = await self._fetch_page(f"{self.LEAGUES[league]}/schedule")

        matches = []
        table = soup.find("table", {"id": re.compile(r"sched.*")})

        if not table:
            return []

        for row in table.find_all("tr", {"data-row": True}):
            cells = row.find_all("td")
            if len(cells) < 5:
                continue

            try:
                match = {
                    "date": cells[0].get_text(strip=True),
                    "time": cells[1].get_text(strip=True),
                    "home_team": cells[2].get_text(strip=True),
                    "away_team": cells[4].get_text(strip=True),
                    "venue": cells[6].get_text(strip=True) if len(cells) > 6 else "",
                }
                matches.append(match)
            except Exception:
                continue

        return matches

    def _parse_shooting_stats(self, table) -> dict:
        """Parse shooting statistics from table."""
        stats = {}
        tfoot = table.find("tfoot")
        if tfoot:
            row = tfoot.find("tr")
            if row:
                cells = row.find_all("td")
                if len(cells) >= 5:
                    stats["shots_total"] = self._safe_int(cells[2].get_text(strip=True))
                    stats["shots_on_target"] = self._safe_int(cells[3].get_text(strip=True))
                    stats["xg"] = self._safe_float(cells[4].get_text(strip=True))
        return stats

    def _parse_passing_stats(self, table) -> dict:
        """Parse passing statistics from table."""
        stats = {}
        tfoot = table.find("tfoot")
        if tfoot:
            row = tfoot.find("tr")
            if row:
                cells = row.find_all("td")
                if len(cells) >= 4:
                    stats["passes_completed"] = self._safe_int(cells[1].get_text(strip=True))
                    stats["passes_attempted"] = self._safe_int(cells[2].get_text(strip=True))
                    stats["pass_completion"] = self._safe_float(cells[3].get_text(strip=True))
        return stats

    def _parse_possession_stats(self, table) -> dict:
        """Parse possession statistics from table."""
        stats = {}
        tfoot = table.find("tfoot")
        if tfoot:
            row = tfoot.find("tr")
            if row:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    stats["possession"] = self._safe_float(cells[1].get_text(strip=True))
        return stats

    @staticmethod
    def _safe_int(value: str) -> int:
        """Safely convert string to int."""
        try:
            return int(re.sub(r"[^\d-]", "", value))
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _safe_float(value: str) -> float:
        """Safely convert string to float."""
        try:
            return float(re.sub(r"[^\d.-]", "", value))
        except (ValueError, TypeError):
            return 0.0


# Convenience functions
async def fetch_league_xg(league: str) -> list[dict]:
    """Fetch xG stats for a league."""
    async with FBrefScraper() as scraper:
        return await scraper.get_league_table(league)
