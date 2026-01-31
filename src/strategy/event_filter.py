"""
Event Filter - Filtro de Melhores Eventos
==========================================
Filtra e rankeia os melhores eventos para apostar.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
from loguru import logger


class EventQuality(Enum):
    """Qualidade do evento."""
    PREMIUM = "premium"      # Top eventos (Champions, finais, etc)
    HIGH = "high"            # Ligas principais
    MEDIUM = "medium"        # Ligas secundárias
    LOW = "low"              # Ligas menores


class BetSignal(Enum):
    """Sinal de aposta."""
    STRONG_BUY = "strong_buy"    # Apostar com confiança
    BUY = "buy"                   # Apostar
    HOLD = "hold"                 # Aguardar
    AVOID = "avoid"               # Evitar


@dataclass
class FilteredEvent:
    """Evento filtrado e rankeado."""

    # Identificação
    match_id: str
    home_team: str
    away_team: str
    league: str
    kickoff: datetime

    # Qualidade
    quality: EventQuality = EventQuality.MEDIUM
    quality_score: float = 0.0  # 0-100

    # Análise
    edge: float = 0.0
    confidence: float = 0.0
    value_bet: Optional[dict] = None

    # Odds
    best_odds: dict = field(default_factory=dict)
    best_bookmaker: str = ""

    # Sinal
    signal: BetSignal = BetSignal.HOLD
    recommended_stake: float = 0.0

    # Links
    bookmaker_links: list[dict] = field(default_factory=list)

    # Ranking
    rank_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "match": f"{self.home_team} vs {self.away_team}",
            "league": self.league,
            "kickoff": self.kickoff.isoformat(),
            "quality": self.quality.value,
            "quality_score": round(self.quality_score, 1),
            "edge": round(self.edge, 2),
            "confidence": round(self.confidence, 1),
            "signal": self.signal.value,
            "recommended_stake": round(self.recommended_stake, 2),
            "best_odds": self.best_odds,
            "best_bookmaker": self.best_bookmaker,
            "bookmaker_links": self.bookmaker_links,
            "rank_score": round(self.rank_score, 1),
        }


class EventFilter:
    """
    Filtra e rankeia eventos para encontrar as melhores apostas.

    Critérios de filtragem:
    1. Qualidade da liga (Premier League > Liga desconhecida)
    2. Edge mínimo (probabilidade vs odds)
    3. Confiança do modelo
    4. Horário (jogos próximos primeiro)
    5. Liquidez (ligas com mais dados)
    """

    # Ligas premium (maior peso)
    PREMIUM_LEAGUES = [
        "champions_league",
        "premier_league",
        "la_liga",
        "bundesliga",
        "serie_a_italy",
        "brasileirao_a",
        "libertadores",
    ]

    # Ligas de alta qualidade
    HIGH_QUALITY_LEAGUES = [
        "ligue_1",
        "eredivisie",
        "primeira_liga",
        "brasileirao_b",
        "europa_league",
        "copa_do_brasil",
        "argentina_primera",
    ]

    def __init__(
        self,
        min_edge: float = 3.0,
        min_confidence: float = 50.0,
        min_quality_score: float = 40.0,
        max_events: int = 20,
    ):
        self.min_edge = min_edge
        self.min_confidence = min_confidence
        self.min_quality_score = min_quality_score
        self.max_events = max_events

    def filter_events(
        self,
        events: list[dict],
        value_bets: list[dict],
    ) -> list[FilteredEvent]:
        """
        Filtra e rankeia eventos.

        Args:
            events: Lista de jogos com dados
            value_bets: Lista de value bets detectados

        Returns:
            Lista de FilteredEvent ordenada por ranking
        """
        filtered = []

        # Cria mapa de value bets por match_id
        vb_map = {vb.get("match_id"): vb for vb in value_bets}

        for event in events:
            match_id = str(event.get("id", ""))
            home_team = event.get("home_team", {}).get("name", "")
            away_team = event.get("away_team", {}).get("name", "")
            league = event.get("league", "")
            kickoff = event.get("kickoff", datetime.now())

            if isinstance(kickoff, str):
                try:
                    kickoff = datetime.fromisoformat(kickoff)
                except:
                    kickoff = datetime.now()

            # Determina qualidade da liga
            quality = self._get_league_quality(league)
            quality_score = self._calculate_quality_score(event, quality)

            # Busca value bet associado
            vb = vb_map.get(match_id, {})
            edge = vb.get("edge", 0) if vb else 0
            confidence = vb.get("confidence_score", 0) if vb else 0

            # Aplica filtros mínimos
            if edge < self.min_edge and quality_score < self.min_quality_score:
                continue

            # Determina sinal
            signal = self._determine_signal(edge, confidence, quality_score)

            # Calcula stake recomendado
            stake = self._calculate_stake(edge, confidence, quality_score)

            # Monta links das casas
            bookmaker_links = self._get_bookmaker_links(event)

            # Calcula rank score
            rank_score = self._calculate_rank_score(edge, confidence, quality_score, kickoff)

            filtered_event = FilteredEvent(
                match_id=match_id,
                home_team=home_team,
                away_team=away_team,
                league=league,
                kickoff=kickoff,
                quality=quality,
                quality_score=quality_score,
                edge=edge,
                confidence=confidence,
                value_bet=vb if vb else None,
                best_odds=event.get("odds", {}),
                best_bookmaker=event.get("best_bookmaker", ""),
                signal=signal,
                recommended_stake=stake,
                bookmaker_links=bookmaker_links,
                rank_score=rank_score,
            )

            filtered.append(filtered_event)

        # Ordena por rank_score
        filtered.sort(key=lambda x: x.rank_score, reverse=True)

        # Limita quantidade
        return filtered[:self.max_events]

    def _get_league_quality(self, league: str) -> EventQuality:
        """Determina qualidade da liga."""
        league_lower = league.lower()

        if league_lower in self.PREMIUM_LEAGUES:
            return EventQuality.PREMIUM
        elif league_lower in self.HIGH_QUALITY_LEAGUES:
            return EventQuality.HIGH
        elif "serie_" in league_lower or "division" in league_lower:
            return EventQuality.MEDIUM
        else:
            return EventQuality.LOW

    def _calculate_quality_score(self, event: dict, quality: EventQuality) -> float:
        """Calcula score de qualidade do evento."""
        base_scores = {
            EventQuality.PREMIUM: 80,
            EventQuality.HIGH: 60,
            EventQuality.MEDIUM: 40,
            EventQuality.LOW: 20,
        }

        score = base_scores.get(quality, 30)

        # Bonus por dados disponíveis
        if event.get("stats_available"):
            score += 10
        if event.get("h2h_available"):
            score += 5
        if event.get("odds"):
            score += 5

        return min(100, score)

    def _determine_signal(
        self,
        edge: float,
        confidence: float,
        quality_score: float,
    ) -> BetSignal:
        """Determina sinal de aposta."""

        # Score combinado
        combined = (edge * 2) + (confidence * 0.3) + (quality_score * 0.2)

        if combined >= 30 and edge >= 8:
            return BetSignal.STRONG_BUY
        elif combined >= 20 and edge >= 5:
            return BetSignal.BUY
        elif combined >= 10 or edge >= 3:
            return BetSignal.HOLD
        else:
            return BetSignal.AVOID

    def _calculate_stake(
        self,
        edge: float,
        confidence: float,
        quality_score: float,
    ) -> float:
        """Calcula stake recomendado (% da banca)."""
        if edge <= 0:
            return 0

        # Base: Kelly fracionário (1/4)
        base_stake = edge / 4

        # Ajusta por confiança
        confidence_mult = confidence / 100 if confidence > 0 else 0.5

        # Ajusta por qualidade
        quality_mult = quality_score / 100 if quality_score > 0 else 0.5

        stake = base_stake * confidence_mult * quality_mult

        # Limites
        return max(0.5, min(5.0, stake))

    def _get_bookmaker_links(self, event: dict) -> list[dict]:
        """Gera links para casas de apostas."""
        from src.strategy.bookmakers import BookmakerManager

        manager = BookmakerManager()
        links = []

        # Pega casas com melhores odds
        best_bookmakers = manager.get_best_odds()[:5]

        for bookmaker in best_bookmakers:
            links.append({
                "id": bookmaker.id,
                "name": bookmaker.name,
                "url": bookmaker.get_event_url(),
                "odds_quality": bookmaker.odds_quality,
                "accepts_pix": bookmaker.accepts_pix,
            })

        return links

    def _calculate_rank_score(
        self,
        edge: float,
        confidence: float,
        quality_score: float,
        kickoff: datetime,
    ) -> float:
        """Calcula score de ranking."""

        # Pesos
        edge_weight = 0.40
        confidence_weight = 0.25
        quality_weight = 0.20
        time_weight = 0.15

        # Score de edge (normalizado para 0-100)
        edge_score = min(100, edge * 5)

        # Score de tempo (jogos mais próximos = maior score)
        now = datetime.now()
        hours_until = (kickoff - now).total_seconds() / 3600
        if hours_until < 0:
            time_score = 100  # Jogo ao vivo
        elif hours_until <= 2:
            time_score = 90
        elif hours_until <= 6:
            time_score = 70
        elif hours_until <= 24:
            time_score = 50
        else:
            time_score = 30

        rank = (
            edge_score * edge_weight +
            confidence * confidence_weight +
            quality_score * quality_weight +
            time_score * time_weight
        )

        return rank

    def get_top_picks(
        self,
        events: list[dict],
        value_bets: list[dict],
        count: int = 5,
    ) -> list[FilteredEvent]:
        """Retorna os TOP picks do dia."""
        filtered = self.filter_events(events, value_bets)

        # Filtra apenas STRONG_BUY e BUY
        top_picks = [
            e for e in filtered
            if e.signal in [BetSignal.STRONG_BUY, BetSignal.BUY]
        ]

        return top_picks[:count]

    def get_live_opportunities(
        self,
        live_events: list[dict],
    ) -> list[FilteredEvent]:
        """Retorna oportunidades em jogos ao vivo."""
        opportunities = []

        for event in live_events:
            # Verifica se tem sinal de oportunidade
            indicators = event.get("indicators", {})
            suggestions = indicators.get("suggestions", [])

            if not suggestions:
                continue

            for suggestion in suggestions:
                if suggestion.get("confidence") in ["high", "medium"]:
                    # Cria evento filtrado
                    fe = FilteredEvent(
                        match_id=str(event.get("match_id", "")),
                        home_team=event.get("home_team", ""),
                        away_team=event.get("away_team", ""),
                        league=event.get("league", ""),
                        kickoff=datetime.now(),
                        quality=EventQuality.HIGH,
                        quality_score=70,
                        edge=5.0,  # Estimado
                        confidence=70 if suggestion["confidence"] == "high" else 50,
                        signal=BetSignal.BUY if suggestion["confidence"] == "high" else BetSignal.HOLD,
                        recommended_stake=2.0,
                        bookmaker_links=self._get_bookmaker_links(event),
                        rank_score=75,
                    )
                    opportunities.append(fe)

        return opportunities
