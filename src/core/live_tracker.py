"""
Live Match Tracker
==================
Acompanha jogos em tempo real com atualizações a cada 30 segundos.
"""

import asyncio
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass, field
from loguru import logger

from src.collectors.footystats import FootyStatsCollector
from src.collectors.odds_api import OddsAPICollector
from src.collectors.live_stats import LiveMatchStats, calculate_live_indicators
from src.models.value_detector import ValueDetector


@dataclass
class LiveMatch:
    """Estado completo de um jogo ao vivo."""

    match_id: str
    home_team: str
    away_team: str
    league: str
    kickoff: datetime

    # Estado atual
    status: str = "not_started"  # not_started, first_half, halftime, second_half, finished
    minute: int = 0
    home_goals: int = 0
    away_goals: int = 0

    # Estatísticas em tempo real
    stats: Optional[LiveMatchStats] = None

    # Odds ao vivo
    live_odds: dict = field(default_factory=dict)

    # Histórico de eventos
    events: list = field(default_factory=list)

    # Análise
    momentum_history: list = field(default_factory=list)
    pressure_history: list = field(default_factory=list)

    def add_event(self, event_type: str, minute: int, description: str):
        """Adiciona evento ao histórico."""
        self.events.append({
            "type": event_type,
            "minute": minute,
            "description": description,
            "timestamp": datetime.now().isoformat(),
        })

    def get_trend(self) -> str:
        """Analisa tendência do jogo."""
        if len(self.momentum_history) < 3:
            return "stable"

        recent = self.momentum_history[-3:]
        trend = recent[-1] - recent[0]

        if trend > 20:
            return "home_improving"
        elif trend < -20:
            return "away_improving"
        return "stable"


class LiveTracker:
    """
    Rastreador de jogos ao vivo.

    Funcionalidades:
    - Atualiza stats a cada 30 segundos
    - Detecta gols, cartões, momentum shifts
    - Calcula indicadores em tempo real
    - Detecta value bets ao vivo
    - Envia alertas quando há oportunidades
    """

    def __init__(
        self,
        update_interval: int = 30,  # segundos
        on_goal: Optional[Callable] = None,
        on_card: Optional[Callable] = None,
        on_momentum_shift: Optional[Callable] = None,
        on_value_bet: Optional[Callable] = None,
        on_stats_update: Optional[Callable] = None,
    ):
        self.update_interval = update_interval
        self.active_matches: dict[str, LiveMatch] = {}
        self.is_running = False

        # Callbacks
        self.on_goal = on_goal
        self.on_card = on_card
        self.on_momentum_shift = on_momentum_shift
        self.on_value_bet = on_value_bet
        self.on_stats_update = on_stats_update

        # Detector de value bets
        self.value_detector = ValueDetector(min_edge=3.0)  # Menos rigoroso para live

    async def start_tracking(self, matches: list[dict]):
        """Inicia rastreamento de jogos."""
        self.is_running = True

        # Inicializa matches
        for match in matches:
            live_match = LiveMatch(
                match_id=str(match.get("id")),
                home_team=match.get("home_team", {}).get("name", ""),
                away_team=match.get("away_team", {}).get("name", ""),
                league=match.get("league", ""),
                kickoff=match.get("kickoff", datetime.now()),
            )
            self.active_matches[live_match.match_id] = live_match

        logger.info(f"🔴 Started tracking {len(matches)} live matches")

        # Loop principal
        while self.is_running and self.active_matches:
            await self._update_all_matches()
            await asyncio.sleep(self.update_interval)

        logger.info("Live tracking stopped")

    async def stop_tracking(self):
        """Para o rastreamento."""
        self.is_running = False

    async def add_match(self, match: dict):
        """Adiciona jogo ao rastreamento."""
        live_match = LiveMatch(
            match_id=str(match.get("id")),
            home_team=match.get("home_team", {}).get("name", ""),
            away_team=match.get("away_team", {}).get("name", ""),
            league=match.get("league", ""),
            kickoff=match.get("kickoff", datetime.now()),
        )
        self.active_matches[live_match.match_id] = live_match
        logger.info(f"Added match to tracking: {live_match.home_team} vs {live_match.away_team}")

    async def remove_match(self, match_id: str):
        """Remove jogo do rastreamento."""
        if match_id in self.active_matches:
            del self.active_matches[match_id]
            logger.info(f"Removed match {match_id} from tracking")

    async def _update_all_matches(self):
        """Atualiza todos os jogos ativos."""
        tasks = []

        for match_id in list(self.active_matches.keys()):
            tasks.append(self._update_match(match_id))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _update_match(self, match_id: str):
        """Atualiza um jogo específico."""
        match = self.active_matches.get(match_id)
        if not match:
            return

        try:
            # Busca dados atualizados
            async with FootyStatsCollector() as collector:
                data = await collector.get_match_details(int(match_id))

            if not data:
                return

            # Salva estado anterior para comparação
            prev_home_goals = match.home_goals
            prev_away_goals = match.away_goals
            prev_momentum = match.stats.momentum_score if match.stats else 0

            # Atualiza estado
            match.status = self._parse_status(data.get("status", ""))
            match.minute = data.get("minute", 0)
            match.home_goals = data.get("home_goals", 0)
            match.away_goals = data.get("away_goals", 0)

            # Atualiza estatísticas
            match.stats = self._parse_stats(match_id, match, data)

            if match.stats:
                match.stats.calculate_momentum()
                match.momentum_history.append(match.stats.momentum_score)
                match.pressure_history.append({
                    "home": match.stats.get_pressure_index("home"),
                    "away": match.stats.get_pressure_index("away"),
                })

            # Detecta eventos
            await self._detect_events(match, prev_home_goals, prev_away_goals, prev_momentum)

            # Busca odds ao vivo
            await self._update_live_odds(match)

            # Detecta value bets ao vivo
            await self._check_live_value(match)

            # Callback de atualização
            if self.on_stats_update:
                await self.on_stats_update(match)

            # Remove jogos finalizados
            if match.status == "finished":
                await self.remove_match(match_id)

        except Exception as e:
            logger.error(f"Error updating match {match_id}: {e}")

    def _parse_status(self, status: str) -> str:
        """Converte status da API para formato interno."""
        status_map = {
            "NS": "not_started",
            "1H": "first_half",
            "HT": "halftime",
            "2H": "second_half",
            "FT": "finished",
            "AET": "finished",
            "PEN": "finished",
        }
        return status_map.get(status.upper(), status.lower())

    def _parse_stats(self, match_id: str, match: LiveMatch, data: dict) -> LiveMatchStats:
        """Converte dados da API para LiveMatchStats."""
        stats_data = data.get("statistics", {})

        return LiveMatchStats(
            match_id=match_id,
            home_team=match.home_team,
            away_team=match.away_team,
            minute=data.get("minute", 0),
            status=match.status,
            home_goals=match.home_goals,
            away_goals=match.away_goals,
            home_possession=stats_data.get("possession", {}).get("home", 50),
            away_possession=stats_data.get("possession", {}).get("away", 50),
            home_shots=stats_data.get("shots", {}).get("home", 0),
            away_shots=stats_data.get("shots", {}).get("away", 0),
            home_shots_on_target=stats_data.get("shots_on_target", {}).get("home", 0),
            away_shots_on_target=stats_data.get("shots_on_target", {}).get("away", 0),
            home_corners=stats_data.get("corners", {}).get("home", 0),
            away_corners=stats_data.get("corners", {}).get("away", 0),
            home_dangerous_attacks=stats_data.get("dangerous_attacks", {}).get("home", 0),
            away_dangerous_attacks=stats_data.get("dangerous_attacks", {}).get("away", 0),
            home_yellow_cards=stats_data.get("yellow_cards", {}).get("home", 0),
            away_yellow_cards=stats_data.get("yellow_cards", {}).get("away", 0),
            home_red_cards=stats_data.get("red_cards", {}).get("home", 0),
            away_red_cards=stats_data.get("red_cards", {}).get("away", 0),
        )

    async def _detect_events(
        self,
        match: LiveMatch,
        prev_home_goals: int,
        prev_away_goals: int,
        prev_momentum: float,
    ):
        """Detecta e notifica eventos."""
        # Gol do time da casa
        if match.home_goals > prev_home_goals:
            match.add_event("goal", match.minute, f"⚽ GOL! {match.home_team}")
            logger.info(f"GOAL! {match.home_team} - {match.home_goals}x{match.away_goals}")

            if self.on_goal:
                await self.on_goal(match, "home")

        # Gol do visitante
        if match.away_goals > prev_away_goals:
            match.add_event("goal", match.minute, f"⚽ GOL! {match.away_team}")
            logger.info(f"GOAL! {match.away_team} - {match.home_goals}x{match.away_goals}")

            if self.on_goal:
                await self.on_goal(match, "away")

        # Mudança de momentum significativa
        if match.stats:
            momentum_change = abs(match.stats.momentum_score - prev_momentum)
            if momentum_change > 25:
                direction = "home" if match.stats.momentum_score > prev_momentum else "away"
                match.add_event(
                    "momentum_shift",
                    match.minute,
                    f"📈 Mudança de momentum para {direction}",
                )

                if self.on_momentum_shift:
                    await self.on_momentum_shift(match, direction, momentum_change)

    async def _update_live_odds(self, match: LiveMatch):
        """Atualiza odds ao vivo."""
        try:
            async with OddsAPICollector() as collector:
                # Nota: Odds API pode não ter odds in-play
                # Aqui seria integração com outra fonte de odds live
                pass
        except Exception as e:
            logger.debug(f"Could not fetch live odds: {e}")

    async def _check_live_value(self, match: LiveMatch):
        """Verifica value bets ao vivo."""
        if not match.stats or not match.live_odds:
            return

        # Calcula probabilidades baseadas nas stats ao vivo
        indicators = calculate_live_indicators(match.stats)

        # Probabilidades estimadas baseadas no momentum e pressão
        home_pressure = match.stats.get_pressure_index("home")
        away_pressure = match.stats.get_pressure_index("away")
        total_pressure = home_pressure + away_pressure

        if total_pressure == 0:
            return

        # Estimativa simples de probabilidade de próximo gol
        live_predictions = {
            "next_goal_home": home_pressure / total_pressure,
            "next_goal_away": away_pressure / total_pressure,
        }

        # Verifica suggestions
        for suggestion in indicators.get("suggestions", []):
            if suggestion.get("confidence") in ["high", "medium"]:
                if self.on_value_bet:
                    await self.on_value_bet(match, suggestion)

    def get_match_summary(self, match_id: str) -> Optional[dict]:
        """Retorna resumo de um jogo."""
        match = self.active_matches.get(match_id)
        if not match:
            return None

        summary = {
            "match": f"{match.home_team} vs {match.away_team}",
            "league": match.league,
            "status": match.status,
            "minute": match.minute,
            "score": f"{match.home_goals}-{match.away_goals}",
            "trend": match.get_trend(),
            "events_count": len(match.events),
            "last_events": match.events[-5:] if match.events else [],
        }

        if match.stats:
            summary["stats"] = {
                "possession": f"{match.stats.home_possession}% - {match.stats.away_possession}%",
                "shots": f"{match.stats.home_shots} - {match.stats.away_shots}",
                "shots_on_target": f"{match.stats.home_shots_on_target} - {match.stats.away_shots_on_target}",
                "corners": f"{match.stats.home_corners} - {match.stats.away_corners}",
                "momentum": match.stats.momentum_score,
                "pressure_home": match.stats.get_pressure_index("home"),
                "pressure_away": match.stats.get_pressure_index("away"),
            }

        return summary

    def get_all_summaries(self) -> list[dict]:
        """Retorna resumo de todos os jogos ativos."""
        return [
            self.get_match_summary(match_id)
            for match_id in self.active_matches.keys()
        ]


# ============================================================================
# DASHBOARD DE TEXTO (para console/telegram)
# ============================================================================

def format_live_dashboard(tracker: LiveTracker) -> str:
    """Formata dashboard de jogos ao vivo."""
    lines = ["🔴 *JOGOS AO VIVO*", "=" * 40, ""]

    for match_id, match in tracker.active_matches.items():
        # Header do jogo
        lines.append(f"⚽ *{match.home_team} vs {match.away_team}*")
        lines.append(f"   {match.league} | {match.minute}'")
        lines.append(f"   📊 Placar: *{match.home_goals} - {match.away_goals}*")

        if match.stats:
            # Stats principais
            lines.append(f"   🎯 Posse: {match.stats.home_possession}% - {match.stats.away_possession}%")
            lines.append(f"   👟 Chutes: {match.stats.home_shots} ({match.stats.home_shots_on_target}) - {match.stats.away_shots} ({match.stats.away_shots_on_target})")
            lines.append(f"   🚩 Escanteios: {match.stats.home_corners} - {match.stats.away_corners}")

            # Momentum
            momentum = match.stats.momentum_score
            if momentum > 30:
                momentum_str = f"🔥 {match.home_team} dominando"
            elif momentum < -30:
                momentum_str = f"🔥 {match.away_team} dominando"
            else:
                momentum_str = "⚖️ Jogo equilibrado"
            lines.append(f"   📈 Momentum: {momentum_str}")

            # Pressão
            lines.append(f"   💪 Pressão: {match.stats.get_pressure_index('home'):.0f} - {match.stats.get_pressure_index('away'):.0f}")

        # Trend
        trend = match.get_trend()
        if trend != "stable":
            lines.append(f"   📊 Tendência: {trend}")

        # Últimos eventos
        if match.events:
            last_event = match.events[-1]
            lines.append(f"   📌 Último: {last_event['description']} ({last_event['minute']}')")

        lines.append("")

    if not tracker.active_matches:
        lines.append("Nenhum jogo ao vivo no momento.")

    return "\n".join(lines)
