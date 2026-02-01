"""
Data Service - LOBINHO-BET
===========================
Centralizes data access from database and APIs.
Connects dashboard to real orchestrator data.
"""

from datetime import datetime, timedelta
from typing import Optional
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings
from src.database.models import (
    Match, MatchStatus, Team, League, ValueBet, BetSignal,
    Bet, BetStatus, BankrollHistory, OddsHistory
)
from src.database.repository import (
    MatchRepository, TeamRepository, LeagueRepository,
    ValueBetRepository, BetRepository, BankrollRepository
)
from src.models.markov_predictor import MarkovPredictor, RankedEvent
from src.models.advanced_predictors import EnsemblePredictor
from src.strategy.bookmakers import BookmakerManager


class DataService:
    """
    Service layer connecting dashboard to real data.
    Aggregates data from database and live APIs.
    """

    def __init__(self, session: Optional[Session] = None):
        if session:
            self.session = session
        else:
            settings = get_settings()
            engine = create_engine(settings.database_url)
            SessionLocal = sessionmaker(bind=engine)
            self.session = SessionLocal()

        self.match_repo = MatchRepository(self.session)
        self.team_repo = TeamRepository(self.session)
        self.league_repo = LeagueRepository(self.session)
        self.value_bet_repo = ValueBetRepository(self.session)
        self.bet_repo = BetRepository(self.session)
        self.bankroll_repo = BankrollRepository(self.session)

        self.markov = MarkovPredictor()
        self.ensemble = EnsemblePredictor()
        self.bookmaker_manager = BookmakerManager()

    async def get_dashboard_data(self) -> dict:
        """
        Get all data needed for dashboard display.
        Returns aggregated data from database and APIs.
        """
        try:
            # Get upcoming matches
            upcoming_matches = self.match_repo.get_upcoming(hours=72)

            # Get live matches
            live_matches = self.match_repo.get_by_status(MatchStatus.LIVE)

            # Get value bets
            value_bets = self.value_bet_repo.get_recent(hours=24)

            # Convert to dashboard format
            events = await self._format_events(upcoming_matches)
            ranked_events = self.markov.rank_events(events, max_events=20)

            # Get statistics
            stats = await self._get_statistics()

            # Bookmakers
            bookmakers = [
                {
                    "id": b.id,
                    "name": b.name,
                    "url": b.base_url,
                    "accepts_pix": b.accepts_pix,
                    "odds_quality": b.odds_quality,
                }
                for b in self.bookmaker_manager.get_brazil_bookmakers()
            ]

            return {
                "total_events": len(upcoming_matches),
                "value_bets_count": len([vb for vb in value_bets if vb.signal in [BetSignal.STRONG_BUY, BetSignal.BUY]]),
                "live_count": len(live_matches),
                "events": [self._ranked_event_to_dict(e) for e in ranked_events],
                "live_matches": await self._format_live_matches(live_matches),
                "bookmakers": bookmakers,
                "statistics": stats,
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return self._get_fallback_data()

    async def _format_events(self, matches: list[Match]) -> list[dict]:
        """Format database matches to event dict format."""
        events = []
        for match in matches:
            # Get latest odds
            odds = self._get_latest_odds(match.id)

            # Get team form from recent matches
            home_form = await self._get_team_form(match.home_team_id)
            away_form = await self._get_team_form(match.away_team_id)

            event = {
                "id": str(match.id),
                "external_id": match.external_id,
                "home_team": {"name": match.home_team.name if match.home_team else "Unknown"},
                "away_team": {"name": match.away_team.name if match.away_team else "Unknown"},
                "league": match.league.name if match.league else "Unknown",
                "kickoff": match.kickoff.isoformat() if match.kickoff else None,
                "home_form": home_form,
                "away_form": away_form,
                "h2h_results": await self._get_h2h(match.home_team_id, match.away_team_id),
                "odds": odds,
                "home_xg": match.home_xg or 1.3,
                "away_xg": match.away_xg or 1.1,
                "is_live": match.status == MatchStatus.LIVE,
            }
            events.append(event)

        return events

    def _get_latest_odds(self, match_id: int) -> dict:
        """Get latest odds for a match."""
        try:
            odds_history = (
                self.session.query(OddsHistory)
                .filter(OddsHistory.match_id == match_id)
                .order_by(OddsHistory.timestamp.desc())
                .first()
            )

            if odds_history:
                return {
                    "home": odds_history.home_odds or 2.0,
                    "draw": odds_history.draw_odds or 3.5,
                    "away": odds_history.away_odds or 3.0,
                    "over_25": odds_history.over_25_odds,
                    "under_25": odds_history.under_25_odds,
                    "btts_yes": odds_history.btts_yes_odds,
                    "btts_no": odds_history.btts_no_odds,
                }
        except Exception as e:
            logger.warning(f"Error getting odds: {e}")

        # Default odds
        return {"home": 2.0, "draw": 3.5, "away": 3.0}

    async def _get_team_form(self, team_id: int, limit: int = 5) -> str:
        """Get team's recent form string (WDLWW format)."""
        try:
            # Get recent finished matches
            recent = (
                self.session.query(Match)
                .filter(
                    ((Match.home_team_id == team_id) | (Match.away_team_id == team_id)),
                    Match.status == MatchStatus.FINISHED
                )
                .order_by(Match.kickoff.desc())
                .limit(limit)
                .all()
            )

            form = []
            for match in recent:
                if match.home_goals is None or match.away_goals is None:
                    continue

                is_home = match.home_team_id == team_id
                team_goals = match.home_goals if is_home else match.away_goals
                opp_goals = match.away_goals if is_home else match.home_goals

                if team_goals > opp_goals:
                    form.append("W")
                elif team_goals < opp_goals:
                    form.append("L")
                else:
                    form.append("D")

            return "".join(form) if form else "DDDDD"
        except Exception as e:
            logger.warning(f"Error getting form: {e}")
            return "DDDDD"

    async def _get_h2h(self, team1_id: int, team2_id: int, limit: int = 5) -> str:
        """Get head-to-head results from team1's perspective."""
        try:
            h2h_matches = (
                self.session.query(Match)
                .filter(
                    (
                        ((Match.home_team_id == team1_id) & (Match.away_team_id == team2_id)) |
                        ((Match.home_team_id == team2_id) & (Match.away_team_id == team1_id))
                    ),
                    Match.status == MatchStatus.FINISHED
                )
                .order_by(Match.kickoff.desc())
                .limit(limit)
                .all()
            )

            form = []
            for match in h2h_matches:
                if match.home_goals is None or match.away_goals is None:
                    continue

                is_home = match.home_team_id == team1_id
                team1_goals = match.home_goals if is_home else match.away_goals
                team2_goals = match.away_goals if is_home else match.home_goals

                if team1_goals > team2_goals:
                    form.append("W")
                elif team1_goals < team2_goals:
                    form.append("L")
                else:
                    form.append("D")

            return "".join(form) if form else "DDDDD"
        except Exception as e:
            logger.warning(f"Error getting H2H: {e}")
            return "DDDDD"

    async def _format_live_matches(self, matches: list[Match]) -> list[dict]:
        """Format live matches for dashboard."""
        live_data = []
        for match in matches:
            live_data.append({
                "id": str(match.id),
                "home_team": match.home_team.short_name if match.home_team else "HOM",
                "away_team": match.away_team.short_name if match.away_team else "AWY",
                "home_goals": match.home_goals or 0,
                "away_goals": match.away_goals or 0,
                "league": match.league.name if match.league else "Unknown",
                "minute": self._calculate_match_minute(match.kickoff),
                "stats": {
                    "possession": {
                        "home": match.home_possession or 50,
                        "away": match.away_possession or 50,
                    },
                    "shots": {
                        "home": match.home_shots or 0,
                        "away": match.away_shots or 0,
                    },
                },
                "momentum": self._calculate_momentum(match),
            })
        return live_data

    def _calculate_match_minute(self, kickoff: datetime) -> int:
        """Calculate current match minute."""
        if not kickoff:
            return 0
        elapsed = datetime.now() - kickoff
        minutes = int(elapsed.total_seconds() / 60)
        return min(max(minutes, 0), 90)

    def _calculate_momentum(self, match: Match) -> int:
        """Calculate momentum score (-100 to 100, positive favors home)."""
        if not match.home_possession or not match.home_shots:
            return 0

        possession_diff = (match.home_possession - 50) * 0.5
        shot_diff = ((match.home_shots or 0) - (match.away_shots or 0)) * 5

        return int(max(-100, min(100, possession_diff + shot_diff)))

    async def _get_statistics(self) -> dict:
        """Get betting statistics for dashboard."""
        try:
            # Get today's bets
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())

            bets_today = (
                self.session.query(Bet)
                .filter(Bet.placed_at >= today_start)
                .all()
            )

            won = len([b for b in bets_today if b.status == BetStatus.WON])
            lost = len([b for b in bets_today if b.status == BetStatus.LOST])
            total_profit = sum(b.profit or 0 for b in bets_today)
            total_stake = sum(b.stake for b in bets_today if b.stake)

            roi = (total_profit / total_stake * 100) if total_stake > 0 else 0

            return {
                "wins": won,
                "losses": lost,
                "roi": round(roi, 1),
                "profit": round(total_profit, 2),
            }
        except Exception as e:
            logger.warning(f"Error getting statistics: {e}")
            return {"wins": 0, "losses": 0, "roi": 0, "profit": 0}

    def _ranked_event_to_dict(self, event: RankedEvent) -> dict:
        """Convert RankedEvent to dict for JSON serialization."""
        return {
            "match_id": event.match_id,
            "home_team": event.home_team,
            "away_team": event.away_team,
            "league": event.league,
            "kickoff": event.kickoff,
            "odds": event.odds,
            "markov_confidence": event.markov_confidence * 100,
            "edge": event.edge,
            "recommended_stake": event.recommended_stake,
            "signal": event.signal.value if event.signal else "hold",
            "best_market": event.best_market,
            "is_live": event.is_live,
            "bookmaker_links": [
                {"name": b.name, "url": b.base_url}
                for b in self.bookmaker_manager.get_brazil_bookmakers()[:4]
            ],
        }

    def _get_fallback_data(self) -> dict:
        """Return fallback data when database is unavailable."""
        bookmakers = [
            {"id": b.id, "name": b.name, "url": b.base_url, "accepts_pix": b.accepts_pix}
            for b in self.bookmaker_manager.get_brazil_bookmakers()
        ]

        return {
            "total_events": 0,
            "value_bets_count": 0,
            "live_count": 0,
            "events": [],
            "live_matches": [],
            "bookmakers": bookmakers,
            "statistics": {"wins": 0, "losses": 0, "roi": 0, "profit": 0},
            "error": "Database connection unavailable",
        }

    # ========================================================================
    # VALUE BET OPERATIONS
    # ========================================================================

    async def get_value_bets(self, signal_filter: Optional[str] = None) -> list[dict]:
        """Get value bets, optionally filtered by signal."""
        try:
            value_bets = self.value_bet_repo.get_recent(hours=48)

            if signal_filter:
                signal_enum = BetSignal(signal_filter)
                value_bets = [vb for vb in value_bets if vb.signal == signal_enum]

            return [
                {
                    "id": vb.id,
                    "match_id": vb.match_id,
                    "market": vb.market,
                    "selection": vb.selection,
                    "odds": vb.odds,
                    "fair_odds": vb.fair_odds,
                    "edge": vb.edge,
                    "confidence": vb.confidence,
                    "kelly_stake": vb.kelly_stake,
                    "signal": vb.signal.value if vb.signal else None,
                    "detected_at": vb.detected_at.isoformat() if vb.detected_at else None,
                }
                for vb in value_bets
            ]
        except Exception as e:
            logger.error(f"Error getting value bets: {e}")
            return []

    # ========================================================================
    # BANKROLL OPERATIONS
    # ========================================================================

    async def get_bankroll_history(self, days: int = 30) -> list[dict]:
        """Get bankroll history for charts."""
        try:
            since = datetime.now() - timedelta(days=days)
            history = (
                self.session.query(BankrollHistory)
                .filter(BankrollHistory.timestamp >= since)
                .order_by(BankrollHistory.timestamp)
                .all()
            )

            return [
                {
                    "timestamp": h.timestamp.isoformat(),
                    "balance": h.balance,
                    "change": h.change,
                    "roi": h.roi,
                }
                for h in history
            ]
        except Exception as e:
            logger.error(f"Error getting bankroll history: {e}")
            return []

    def close(self):
        """Close database session."""
        if self.session:
            self.session.close()


# Singleton instance
_data_service: Optional[DataService] = None


def get_data_service() -> DataService:
    """Get or create DataService singleton."""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service
