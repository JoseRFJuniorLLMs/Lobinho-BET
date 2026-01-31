"""
LOBINHO-BET Orchestrator
========================
Orquestra todo o sistema de forma automática.
Coleta dados, analisa, detecta value bets e notifica.
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import Optional, Callable
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.collectors import FootyStatsCollector, OddsAPICollector, FBrefScraper
from src.collectors.live_stats import LiveStatsMonitor, LiveMatchStats, calculate_live_indicators
from src.models.predictor import MatchPredictor
from src.models.value_detector import ValueDetector, ValueBet
from src.strategy.leagues import LeagueManager, League
from config import get_settings


class LobinhoOrchestrator:
    """
    Orquestrador principal do sistema LOBINHO-BET.

    Automação completa:
    1. Coleta dados de jogos do dia (FootyStats + Odds API)
    2. Enriquece com métricas xG (FBref)
    3. Gera previsões com modelo ML
    4. Detecta value bets
    5. Monitora jogos ao vivo
    6. Envia alertas (Telegram/Discord)
    """

    def __init__(
        self,
        on_value_bet: Optional[Callable[[ValueBet], None]] = None,
        on_live_alert: Optional[Callable[[dict], None]] = None,
    ):
        self.settings = get_settings()
        self.league_manager = LeagueManager()
        self.predictor = MatchPredictor()
        self.value_detector = ValueDetector()
        self.scheduler = AsyncIOScheduler()

        # Callbacks
        self.on_value_bet = on_value_bet
        self.on_live_alert = on_live_alert

        # Estado
        self.today_matches: list[dict] = []
        self.value_bets_found: list[ValueBet] = []
        self.live_monitor: Optional[LiveStatsMonitor] = None
        self.is_running = False

    # =========================================================================
    # AUTOMAÇÃO - SCHEDULE
    # =========================================================================

    def setup_schedule(self):
        """Configura agenda de tarefas automáticas."""

        # Coleta jogos do dia às 06:00
        self.scheduler.add_job(
            self.collect_daily_matches,
            CronTrigger(hour=6, minute=0),
            id="daily_collection",
            name="Coleta diária de jogos",
        )

        # Análise pré-jogo às 08:00
        self.scheduler.add_job(
            self.run_pre_match_analysis,
            CronTrigger(hour=8, minute=0),
            id="pre_match_analysis",
            name="Análise pré-jogo",
        )

        # Atualiza odds a cada 30 minutos (das 10h às 23h)
        self.scheduler.add_job(
            self.update_odds,
            CronTrigger(hour="10-23", minute="*/30"),
            id="odds_update",
            name="Atualização de odds",
        )

        # Verifica jogos ao vivo a cada 5 minutos
        self.scheduler.add_job(
            self.check_live_matches,
            IntervalTrigger(minutes=5),
            id="live_check",
            name="Verificação de jogos ao vivo",
        )

        # Relatório diário às 23:30
        self.scheduler.add_job(
            self.generate_daily_report,
            CronTrigger(hour=23, minute=30),
            id="daily_report",
            name="Relatório diário",
        )

        logger.info("Schedule configured with automatic tasks")

    async def start(self):
        """Inicia o orquestrador."""
        logger.info("🚀 Starting LOBINHO-BET Orchestrator...")

        self.setup_schedule()
        self.scheduler.start()
        self.is_running = True

        # Executa coleta inicial
        await self.collect_daily_matches()
        await self.run_pre_match_analysis()

        logger.info("✅ Orchestrator running!")

    async def stop(self):
        """Para o orquestrador."""
        logger.info("Stopping orchestrator...")
        self.is_running = False
        self.scheduler.shutdown()

        if self.live_monitor:
            await self.live_monitor.stop_monitoring()

        logger.info("Orchestrator stopped")

    # =========================================================================
    # COLETA DE DADOS
    # =========================================================================

    async def collect_daily_matches(self):
        """Coleta todos os jogos do dia."""
        logger.info("📥 Collecting today's matches...")

        today = date.today()
        all_matches = []

        leagues = self.league_manager.get_enabled_leagues()

        async with FootyStatsCollector() as collector:
            for league in leagues:
                if not league.footystats_id:
                    continue

                try:
                    matches = await collector.get_matches(
                        league_id=league.footystats_id,
                        date_from=today,
                        date_to=today,
                    )

                    for match in matches:
                        match["league"] = league.id
                        match["league_config"] = league

                    all_matches.extend(matches)
                    logger.debug(f"Found {len(matches)} matches in {league.name}")

                except Exception as e:
                    logger.error(f"Error fetching {league.name}: {e}")

        self.today_matches = all_matches
        logger.info(f"✅ Collected {len(all_matches)} matches for today")

        return all_matches

    async def update_odds(self):
        """Atualiza odds de todos os jogos."""
        logger.info("💰 Updating odds...")

        leagues = self.league_manager.get_enabled_leagues()

        async with OddsAPICollector() as collector:
            for league in leagues:
                if not league.odds_api_key:
                    continue

                try:
                    odds_data = await collector.get_matches(sport=league.odds_api_key)

                    # Associa odds aos jogos
                    for odds in odds_data:
                        self._match_odds_to_game(odds)

                except Exception as e:
                    logger.error(f"Error fetching odds for {league.name}: {e}")

        logger.info("✅ Odds updated")

    async def fetch_xg_data(self, league_id: str) -> dict:
        """Busca dados de xG do FBref."""
        league = self.league_manager.get_league(league_id)
        if not league or not league.fbref_path:
            return {}

        try:
            async with FBrefScraper() as scraper:
                table = await scraper.get_league_table(league_id)
                return {team["team"]: team for team in table}
        except Exception as e:
            logger.error(f"Error fetching xG for {league_id}: {e}")
            return {}

    # =========================================================================
    # ANÁLISE E PREVISÃO
    # =========================================================================

    async def run_pre_match_analysis(self):
        """Executa análise pré-jogo completa."""
        logger.info("🔬 Running pre-match analysis...")

        self.value_bets_found = []

        for match in self.today_matches:
            try:
                value_bets = await self.analyze_match(match)
                self.value_bets_found.extend(value_bets)

            except Exception as e:
                logger.error(f"Error analyzing match: {e}")

        # Filtra melhores apostas
        best_bets = self.value_detector.filter_best_bets(
            self.value_bets_found,
            max_bets=10,
            min_confidence="medium",
        )

        # Notifica
        for bet in best_bets:
            if self.on_value_bet:
                await self.on_value_bet(bet)

        logger.info(f"✅ Analysis complete. Found {len(best_bets)} value bets")
        return best_bets

    async def analyze_match(self, match: dict) -> list[ValueBet]:
        """Analisa um jogo específico."""
        match_id = match.get("id")
        home_team = match.get("home_team", {}).get("name", "")
        away_team = match.get("away_team", {}).get("name", "")
        league_config: League = match.get("league_config")

        # Coleta dados
        async with FootyStatsCollector() as collector:
            home_stats = await collector.get_team_stats(match.get("home_team", {}).get("id", ""))
            away_stats = await collector.get_team_stats(match.get("away_team", {}).get("id", ""))
            h2h = await collector.get_h2h(
                match.get("home_team", {}).get("id", ""),
                match.get("away_team", {}).get("id", ""),
            )

        # Monta features para previsão
        match_data = self._build_prediction_features(home_stats, away_stats, h2h)

        # Gera previsão
        prediction = self.predictor.predict(match_data)

        # Busca odds
        odds = match.get("odds", {})
        if not odds:
            return []

        # Detecta value bets
        value_detector = ValueDetector(min_edge=league_config.min_edge if league_config else 5.0)

        value_bets = value_detector.detect_value(
            match_id=str(match_id),
            home_team=home_team,
            away_team=away_team,
            predictions=prediction,
            odds=odds,
        )

        return value_bets

    def _build_prediction_features(
        self,
        home_stats: dict,
        away_stats: dict,
        h2h: dict,
    ) -> dict:
        """Constrói features para o modelo de previsão."""
        return {
            # Form
            "home_form": home_stats.get("form_points", 0),
            "away_form": away_stats.get("form_points", 0),

            # Goals
            "home_goals_avg": home_stats.get("goals_scored_avg", 0),
            "away_goals_avg": away_stats.get("goals_scored_avg", 0),
            "home_conceded_avg": home_stats.get("goals_conceded_avg", 0),
            "away_conceded_avg": away_stats.get("goals_conceded_avg", 0),

            # xG
            "home_xg": home_stats.get("xg", 0),
            "away_xg": away_stats.get("xg", 0),
            "home_xga": home_stats.get("xga", 0),
            "away_xga": away_stats.get("xga", 0),

            # Position
            "home_position": home_stats.get("position", 10),
            "away_position": away_stats.get("position", 10),

            # H2H
            "h2h_home_wins": h2h.get("home_wins", 0),
            "h2h_draws": h2h.get("draws", 0),
            "h2h_away_wins": h2h.get("away_wins", 0),

            # Rest
            "home_rest_days": home_stats.get("rest_days", 7),
            "away_rest_days": away_stats.get("rest_days", 7),
        }

    def _match_odds_to_game(self, odds_data: dict):
        """Associa dados de odds a um jogo."""
        home_team = odds_data.get("home_team", "").lower()
        away_team = odds_data.get("away_team", "").lower()

        for match in self.today_matches:
            match_home = match.get("home_team", {}).get("name", "").lower()
            match_away = match.get("away_team", {}).get("name", "").lower()

            # Match fuzzy
            if home_team in match_home or match_home in home_team:
                if away_team in match_away or match_away in away_team:
                    # Encontrou o jogo - extrai melhores odds
                    async with OddsAPICollector() as collector:
                        best_odds = collector.find_best_odds(odds_data)

                    match["odds"] = {
                        "home": best_odds["home"]["odds"],
                        "draw": best_odds["draw"]["odds"],
                        "away": best_odds["away"]["odds"],
                    }
                    break

    # =========================================================================
    # MONITORAMENTO AO VIVO
    # =========================================================================

    async def check_live_matches(self):
        """Verifica jogos que estão ao vivo."""
        now = datetime.now()

        live_matches = [
            m for m in self.today_matches
            if m.get("status") == "live"
        ]

        if not live_matches:
            return

        logger.info(f"🔴 Monitoring {len(live_matches)} live matches")

        for match in live_matches:
            try:
                await self.analyze_live_match(match)
            except Exception as e:
                logger.error(f"Error in live analysis: {e}")

    async def analyze_live_match(self, match: dict):
        """Analisa jogo ao vivo e detecta oportunidades."""
        match_id = match.get("id")

        async with FootyStatsCollector() as collector:
            live_data = await collector.get_match_details(match_id)

        if not live_data:
            return

        # Calcula indicadores
        stats = LiveMatchStats(
            match_id=str(match_id),
            home_team=match.get("home_team", {}).get("name", ""),
            away_team=match.get("away_team", {}).get("name", ""),
            minute=live_data.get("minute", 0),
            home_goals=live_data.get("home_goals", 0),
            away_goals=live_data.get("away_goals", 0),
            home_possession=live_data.get("possession", {}).get("home", 50),
            away_possession=live_data.get("possession", {}).get("away", 50),
            home_shots=live_data.get("shots", {}).get("home", 0),
            away_shots=live_data.get("shots", {}).get("away", 0),
        )

        indicators = calculate_live_indicators(stats)

        # Notifica se há sugestões
        if indicators.get("suggestions") and self.on_live_alert:
            await self.on_live_alert({
                "match": f"{stats.home_team} vs {stats.away_team}",
                "minute": stats.minute,
                "score": f"{stats.home_goals}-{stats.away_goals}",
                "indicators": indicators,
            })

    # =========================================================================
    # RELATÓRIOS
    # =========================================================================

    async def generate_daily_report(self) -> dict:
        """Gera relatório diário de performance."""
        report = {
            "date": date.today().isoformat(),
            "total_matches_analyzed": len(self.today_matches),
            "value_bets_found": len(self.value_bets_found),
            "bets_by_league": {},
            "bets_by_confidence": {"high": 0, "medium": 0, "low": 0},
            "top_bets": [],
        }

        for bet in self.value_bets_found:
            # Por liga
            league = bet.match_id.split("_")[0] if "_" in bet.match_id else "unknown"
            report["bets_by_league"][league] = report["bets_by_league"].get(league, 0) + 1

            # Por confiança
            report["bets_by_confidence"][bet.confidence] += 1

        # Top 5 apostas do dia
        top_bets = self.value_detector.filter_best_bets(self.value_bets_found, max_bets=5)
        report["top_bets"] = [bet.to_dict() for bet in top_bets]

        logger.info(f"📊 Daily report generated: {report}")
        return report


# ============================================================================
# RUNNER
# ============================================================================

async def run_lobinho():
    """Executa o sistema LOBINHO-BET."""
    from src.notifier.telegram_bot import send_telegram_message

    async def on_value_bet(bet: ValueBet):
        """Callback quando value bet é detectado."""
        message = bet.to_telegram_message()
        await send_telegram_message(message)

    async def on_live_alert(alert: dict):
        """Callback para alertas ao vivo."""
        message = f"🔴 LIVE ALERT\n{alert['match']} ({alert['minute']}')\n"
        message += f"Score: {alert['score']}\n"
        for suggestion in alert.get("indicators", {}).get("suggestions", []):
            message += f"💡 {suggestion['market']}: {suggestion['reason']}\n"
        await send_telegram_message(message)

    orchestrator = LobinhoOrchestrator(
        on_value_bet=on_value_bet,
        on_live_alert=on_live_alert,
    )

    try:
        await orchestrator.start()

        # Mantém rodando
        while orchestrator.is_running:
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(run_lobinho())
