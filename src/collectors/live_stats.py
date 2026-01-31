"""
Live Stats Collector
====================
Coleta dados estatísticos em tempo real durante os jogos.
"""

import asyncio
from typing import Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from loguru import logger

from .footystats import FootyStatsCollector
from .odds_api import OddsAPICollector


@dataclass
class LiveMatchStats:
    """Estatísticas ao vivo de uma partida."""

    match_id: str
    home_team: str
    away_team: str
    minute: int = 0
    status: str = "not_started"  # not_started, live, halftime, finished

    # Placar
    home_goals: int = 0
    away_goals: int = 0

    # Estatísticas ao vivo
    home_possession: float = 50.0
    away_possession: float = 50.0
    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0
    home_corners: int = 0
    away_corners: int = 0
    home_dangerous_attacks: int = 0
    away_dangerous_attacks: int = 0
    home_attacks: int = 0
    away_attacks: int = 0

    # Cards
    home_yellow_cards: int = 0
    away_yellow_cards: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0

    # xG ao vivo (se disponível)
    home_xg_live: float = 0.0
    away_xg_live: float = 0.0

    # Odds atuais
    home_odds: float = 0.0
    draw_odds: float = 0.0
    away_odds: float = 0.0

    # Momentum (calculado)
    momentum_score: float = 0.0  # -100 a +100 (negativo = away, positivo = home)

    # Timestamp
    updated_at: datetime = field(default_factory=datetime.now)

    def calculate_momentum(self) -> float:
        """
        Calcula o momentum do jogo baseado nas estatísticas recentes.
        Retorna valor de -100 (dominância away) a +100 (dominância home).
        """
        factors = []

        # Posse de bola
        possession_diff = self.home_possession - self.away_possession
        factors.append(possession_diff * 0.3)

        # Chutes
        if self.home_shots + self.away_shots > 0:
            shot_ratio = (self.home_shots - self.away_shots) / max(self.home_shots + self.away_shots, 1)
            factors.append(shot_ratio * 100 * 0.25)

        # Chutes no gol
        if self.home_shots_on_target + self.away_shots_on_target > 0:
            sot_ratio = (self.home_shots_on_target - self.away_shots_on_target) / max(
                self.home_shots_on_target + self.away_shots_on_target, 1
            )
            factors.append(sot_ratio * 100 * 0.25)

        # Ataques perigosos
        if self.home_dangerous_attacks + self.away_dangerous_attacks > 0:
            attack_ratio = (self.home_dangerous_attacks - self.away_dangerous_attacks) / max(
                self.home_dangerous_attacks + self.away_dangerous_attacks, 1
            )
            factors.append(attack_ratio * 100 * 0.2)

        self.momentum_score = sum(factors)
        return self.momentum_score

    def get_pressure_index(self, team: str = "home") -> float:
        """
        Índice de pressão de um time (0-100).
        Baseado em ataques, chutes e posse.
        """
        if team == "home":
            attacks = self.home_dangerous_attacks
            shots = self.home_shots
            possession = self.home_possession
        else:
            attacks = self.away_dangerous_attacks
            shots = self.away_shots
            possession = self.away_possession

        # Normaliza para 0-100
        attack_score = min(attacks / 50 * 100, 100) * 0.4
        shot_score = min(shots / 15 * 100, 100) * 0.3
        possession_score = possession * 0.3

        return round(attack_score + shot_score + possession_score, 1)

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "minute": self.minute,
            "status": self.status,
            "score": f"{self.home_goals}-{self.away_goals}",
            "possession": {"home": self.home_possession, "away": self.away_possession},
            "shots": {"home": self.home_shots, "away": self.away_shots},
            "shots_on_target": {"home": self.home_shots_on_target, "away": self.away_shots_on_target},
            "corners": {"home": self.home_corners, "away": self.away_corners},
            "dangerous_attacks": {"home": self.home_dangerous_attacks, "away": self.away_dangerous_attacks},
            "xg_live": {"home": self.home_xg_live, "away": self.away_xg_live},
            "odds": {"home": self.home_odds, "draw": self.draw_odds, "away": self.away_odds},
            "momentum": self.momentum_score,
            "pressure_index": {
                "home": self.get_pressure_index("home"),
                "away": self.get_pressure_index("away"),
            },
            "updated_at": self.updated_at.isoformat(),
        }


class LiveStatsMonitor:
    """
    Monitor de estatísticas ao vivo.
    Atualiza dados em tempo real e dispara callbacks quando há mudanças significativas.
    """

    def __init__(
        self,
        update_interval: int = 30,  # segundos
        on_stats_update: Optional[Callable] = None,
        on_goal: Optional[Callable] = None,
        on_momentum_shift: Optional[Callable] = None,
    ):
        self.update_interval = update_interval
        self.on_stats_update = on_stats_update
        self.on_goal = on_goal
        self.on_momentum_shift = on_momentum_shift

        self.active_matches: dict[str, LiveMatchStats] = {}
        self.is_running = False

    async def start_monitoring(self, match_ids: list[str]):
        """Inicia monitoramento de jogos específicos."""
        self.is_running = True
        logger.info(f"Starting live monitoring for {len(match_ids)} matches")

        while self.is_running:
            await self._update_all_matches(match_ids)
            await asyncio.sleep(self.update_interval)

    async def stop_monitoring(self):
        """Para o monitoramento."""
        self.is_running = False
        logger.info("Live monitoring stopped")

    async def _update_all_matches(self, match_ids: list[str]):
        """Atualiza estatísticas de todos os jogos monitorados."""
        for match_id in match_ids:
            try:
                await self._update_match(match_id)
            except Exception as e:
                logger.error(f"Error updating match {match_id}: {e}")

    async def _update_match(self, match_id: str):
        """Atualiza estatísticas de um jogo específico."""
        # Busca dados atualizados
        async with FootyStatsCollector() as collector:
            match_data = await collector.get_match_details(int(match_id))

        if not match_data:
            return

        # Cria ou atualiza stats
        previous_stats = self.active_matches.get(match_id)
        new_stats = self._parse_live_stats(match_id, match_data)

        # Detecta eventos
        if previous_stats:
            self._detect_events(previous_stats, new_stats)

        # Calcula momentum
        new_stats.calculate_momentum()

        # Atualiza cache
        self.active_matches[match_id] = new_stats

        # Callback de atualização
        if self.on_stats_update:
            await self.on_stats_update(new_stats)

    def _parse_live_stats(self, match_id: str, data: dict) -> LiveMatchStats:
        """Converte dados da API para LiveMatchStats."""
        stats = LiveMatchStats(
            match_id=match_id,
            home_team=data.get("home_team", {}).get("name", ""),
            away_team=data.get("away_team", {}).get("name", ""),
            minute=data.get("minute", 0),
            status=data.get("status", "not_started"),
            home_goals=data.get("home_goals", 0),
            away_goals=data.get("away_goals", 0),
        )

        # Parse statistics
        live_stats = data.get("statistics", {})
        if live_stats:
            stats.home_possession = live_stats.get("possession", {}).get("home", 50)
            stats.away_possession = live_stats.get("possession", {}).get("away", 50)
            stats.home_shots = live_stats.get("shots", {}).get("home", 0)
            stats.away_shots = live_stats.get("shots", {}).get("away", 0)
            stats.home_shots_on_target = live_stats.get("shots_on_target", {}).get("home", 0)
            stats.away_shots_on_target = live_stats.get("shots_on_target", {}).get("away", 0)
            stats.home_corners = live_stats.get("corners", {}).get("home", 0)
            stats.away_corners = live_stats.get("corners", {}).get("away", 0)
            stats.home_dangerous_attacks = live_stats.get("dangerous_attacks", {}).get("home", 0)
            stats.away_dangerous_attacks = live_stats.get("dangerous_attacks", {}).get("away", 0)

        return stats

    def _detect_events(self, old: LiveMatchStats, new: LiveMatchStats):
        """Detecta eventos importantes (gols, mudança de momentum)."""
        # Detecta gol
        if new.home_goals > old.home_goals:
            if self.on_goal:
                asyncio.create_task(self.on_goal(new, "home"))
            logger.info(f"GOAL! {new.home_team} scores! {new.home_goals}-{new.away_goals}")

        if new.away_goals > old.away_goals:
            if self.on_goal:
                asyncio.create_task(self.on_goal(new, "away"))
            logger.info(f"GOAL! {new.away_team} scores! {new.home_goals}-{new.away_goals}")

        # Detecta mudança significativa de momentum (>30 pontos)
        momentum_change = abs(new.momentum_score - old.momentum_score)
        if momentum_change > 30:
            if self.on_momentum_shift:
                asyncio.create_task(self.on_momentum_shift(new, momentum_change))
            logger.info(f"Momentum shift detected: {momentum_change:.1f} points")

    def get_match_stats(self, match_id: str) -> Optional[LiveMatchStats]:
        """Retorna estatísticas atuais de um jogo."""
        return self.active_matches.get(match_id)

    def get_all_stats(self) -> dict[str, LiveMatchStats]:
        """Retorna estatísticas de todos os jogos monitorados."""
        return self.active_matches.copy()


# Indicadores calculados para decisão
def calculate_live_indicators(stats: LiveMatchStats) -> dict:
    """
    Calcula indicadores para decisão de aposta ao vivo.

    Retorna:
        dict com indicadores e sugestões
    """
    indicators = {
        "match_id": stats.match_id,
        "minute": stats.minute,
        "score": f"{stats.home_goals}-{stats.away_goals}",
    }

    # Índice de pressão
    home_pressure = stats.get_pressure_index("home")
    away_pressure = stats.get_pressure_index("away")
    indicators["pressure"] = {
        "home": home_pressure,
        "away": away_pressure,
        "dominant": "home" if home_pressure > away_pressure else "away",
    }

    # Momentum
    indicators["momentum"] = {
        "score": stats.momentum_score,
        "direction": "home" if stats.momentum_score > 0 else "away",
        "strength": "strong" if abs(stats.momentum_score) > 50 else "moderate" if abs(stats.momentum_score) > 25 else "weak",
    }

    # Probabilidade de próximo gol (estimativa simples)
    total_shots = stats.home_shots + stats.away_shots
    if total_shots > 0:
        home_shot_share = stats.home_shots_on_target / max(total_shots, 1)
        indicators["next_goal_probability"] = {
            "home": round(home_shot_share * 100, 1),
            "away": round((1 - home_shot_share) * 100, 1),
        }

    # Sugestões baseadas nos dados
    suggestions = []

    # Over/Under
    total_goals = stats.home_goals + stats.away_goals
    if stats.minute < 60 and total_goals == 0 and (home_pressure > 60 or away_pressure > 60):
        suggestions.append({
            "market": "over_0.5",
            "confidence": "medium",
            "reason": "High pressure, no goals yet",
        })

    if stats.minute < 75 and total_goals >= 2:
        suggestions.append({
            "market": "over_2.5",
            "confidence": "high" if home_pressure + away_pressure > 100 else "medium",
            "reason": "Open game with goals",
        })

    # Próximo gol
    if abs(stats.momentum_score) > 40:
        dominant = "home" if stats.momentum_score > 0 else "away"
        suggestions.append({
            "market": f"next_goal_{dominant}",
            "confidence": "medium",
            "reason": f"Strong momentum for {dominant}",
        })

    indicators["suggestions"] = suggestions

    return indicators
