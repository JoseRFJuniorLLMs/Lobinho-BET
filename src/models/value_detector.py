"""
Value Bet Detector
==================
Detecta apostas com valor (edge positivo).
Compara probabilidades calculadas vs odds oferecidas.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from config import get_settings


@dataclass
class ValueBet:
    """Representa uma aposta com valor detectado."""

    match_id: str
    home_team: str
    away_team: str
    market: str  # home, draw, away, over_2.5, btts_yes, etc.
    selection: str  # Nome da seleção
    odds: float  # Odds oferecidas
    fair_odds: float  # Odds justas calculadas
    probability: float  # Probabilidade calculada (0-1)
    implied_prob: float  # Probabilidade implícita das odds (0-1)
    edge: float  # Vantagem em % (ex: 5.5 = 5.5%)
    confidence: str  # low, medium, high
    kelly_stake: float  # Stake sugerido pelo Kelly Criterion (%)
    ev: float  # Expected Value
    bookmaker: Optional[str] = None
    detected_at: datetime = None

    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "match": f"{self.home_team} vs {self.away_team}",
            "market": self.market,
            "selection": self.selection,
            "odds": self.odds,
            "fair_odds": round(self.fair_odds, 2),
            "probability": f"{self.probability * 100:.1f}%",
            "edge": f"{self.edge:.2f}%",
            "confidence": self.confidence,
            "kelly_stake": f"{self.kelly_stake:.2f}%",
            "ev": f"{self.ev:.3f}",
            "bookmaker": self.bookmaker,
            "detected_at": self.detected_at.isoformat(),
        }

    def to_telegram_message(self) -> str:
        """Formata para mensagem do Telegram."""
        emoji = "🔥" if self.confidence == "high" else "✅" if self.confidence == "medium" else "📊"

        return f"""
{emoji} *VALUE BET DETECTADO*

⚽ *{self.home_team} vs {self.away_team}*
📍 Mercado: `{self.market}`
🎯 Seleção: *{self.selection}*

💰 Odds: *{self.odds}*
📊 Odds Justas: {self.fair_odds:.2f}
📈 Edge: *{self.edge:.2f}%*
🎲 Probabilidade: {self.probability * 100:.1f}%

💵 Stake Kelly: {self.kelly_stake:.2f}%
📉 EV: {self.ev:.3f}
🏆 Confiança: {self.confidence.upper()}
🏦 Casa: {self.bookmaker or 'N/A'}
"""


class ValueDetector:
    """
    Detecta value bets comparando probabilidades vs odds.

    Uma aposta tem valor quando:
    probabilidade_real > probabilidade_implícita
    ou seja: nossa estimativa diz que o evento é mais provável
    do que as odds sugerem.
    """

    def __init__(
        self,
        min_edge: float = None,
        min_odds: float = None,
        max_odds: float = None,
    ):
        settings = get_settings()
        self.min_edge = min_edge or settings.min_value_threshold * 100  # Converter para %
        self.min_odds = min_odds or settings.min_odds
        self.max_odds = max_odds or settings.max_odds

    def odds_to_probability(self, odds: float) -> float:
        """Converte odds decimais para probabilidade implícita."""
        if odds <= 1:
            return 0
        return 1 / odds

    def probability_to_odds(self, prob: float) -> float:
        """Converte probabilidade para odds justas."""
        if prob <= 0:
            return float('inf')
        return 1 / prob

    def calculate_edge(self, probability: float, odds: float) -> float:
        """
        Calcula a vantagem (edge) em percentual.

        Edge = (probabilidade_real * odds) - 1
        Positivo = valor, Negativo = sem valor
        """
        if odds <= 1:
            return -100

        expected_return = probability * odds
        edge = (expected_return - 1) * 100
        return edge

    def calculate_kelly(self, probability: float, odds: float) -> float:
        """
        Calcula stake ótimo usando Kelly Criterion.

        Kelly% = (bp - q) / b
        onde:
            b = odds - 1 (lucro líquido por unidade apostada)
            p = probabilidade de ganhar
            q = probabilidade de perder (1 - p)
        """
        if odds <= 1 or probability <= 0 or probability >= 1:
            return 0

        b = odds - 1
        p = probability
        q = 1 - p

        kelly = (b * p - q) / b

        # Kelly fracionário (1/4) para ser mais conservador
        kelly_fraction = kelly / 4

        return max(0, kelly_fraction * 100)  # Retorna em %

    def calculate_ev(self, probability: float, odds: float, stake: float = 1) -> float:
        """
        Calcula Expected Value.

        EV = (prob_ganhar * lucro) - (prob_perder * stake)
        """
        profit = stake * (odds - 1)
        loss = stake

        ev = (probability * profit) - ((1 - probability) * loss)
        return ev

    def detect_value(
        self,
        match_id: str,
        home_team: str,
        away_team: str,
        predictions: dict,
        odds: dict,
        bookmaker: Optional[str] = None,
    ) -> list[ValueBet]:
        """
        Detecta value bets para uma partida.

        Args:
            match_id: ID da partida
            home_team: Nome do time da casa
            away_team: Nome do visitante
            predictions: Dict com probabilidades previstas
                {"home_win": 0.45, "draw": 0.28, "away_win": 0.27, ...}
            odds: Dict com odds oferecidas
                {"home": 1.90, "draw": 3.40, "away": 4.20, ...}
            bookmaker: Nome da casa de apostas

        Returns:
            Lista de ValueBet detectados
        """
        value_bets = []

        # Mapeia mercados
        markets = [
            ("home", "home_win", home_team, odds.get("home", 0)),
            ("draw", "draw", "Empate", odds.get("draw", 0)),
            ("away", "away_win", away_team, odds.get("away", 0)),
            ("over_2.5", "over_2.5", "Over 2.5 Gols", odds.get("over_2.5", 0)),
            ("under_2.5", "under_2.5", "Under 2.5 Gols", odds.get("under_2.5", 0)),
            ("btts_yes", "btts_yes", "Ambas Marcam - Sim", odds.get("btts_yes", 0)),
            ("btts_no", "btts_no", "Ambas Marcam - Não", odds.get("btts_no", 0)),
        ]

        for market, pred_key, selection, market_odds in markets:
            probability = predictions.get(pred_key, 0)

            if not probability or not market_odds:
                continue

            # Verifica filtros de odds
            if market_odds < self.min_odds or market_odds > self.max_odds:
                continue

            # Calcula métricas
            edge = self.calculate_edge(probability, market_odds)
            implied_prob = self.odds_to_probability(market_odds)
            fair_odds = self.probability_to_odds(probability)
            kelly = self.calculate_kelly(probability, market_odds)
            ev = self.calculate_ev(probability, market_odds)

            # Verifica se tem valor
            if edge < self.min_edge:
                continue

            # Determina confiança
            if edge >= 10:
                confidence = "high"
            elif edge >= 5:
                confidence = "medium"
            else:
                confidence = "low"

            value_bet = ValueBet(
                match_id=match_id,
                home_team=home_team,
                away_team=away_team,
                market=market,
                selection=selection,
                odds=market_odds,
                fair_odds=fair_odds,
                probability=probability,
                implied_prob=implied_prob,
                edge=edge,
                confidence=confidence,
                kelly_stake=kelly,
                ev=ev,
                bookmaker=bookmaker,
            )

            value_bets.append(value_bet)
            logger.info(
                f"Value bet found: {home_team} vs {away_team} | "
                f"{selection} @ {market_odds} | Edge: {edge:.2f}%"
            )

        return value_bets

    def detect_live_value(
        self,
        match_id: str,
        home_team: str,
        away_team: str,
        live_predictions: dict,
        live_odds: dict,
        minute: int,
        score: tuple[int, int],
        bookmaker: Optional[str] = None,
    ) -> list[ValueBet]:
        """
        Detecta value bets em jogos ao vivo.
        Ajusta thresholds baseado no tempo de jogo.
        """
        # Aumenta threshold de edge conforme o jogo avança
        # (menos tempo = mais risco = precisa de mais edge)
        if minute < 30:
            min_edge = self.min_edge * 1.5
        elif minute < 60:
            min_edge = self.min_edge * 1.2
        elif minute < 75:
            min_edge = self.min_edge
        else:
            min_edge = self.min_edge * 0.8  # Aceita menos edge no final

        # Salva threshold original
        original_min_edge = self.min_edge
        self.min_edge = min_edge

        # Detecta value bets
        value_bets = self.detect_value(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            predictions=live_predictions,
            odds=live_odds,
            bookmaker=bookmaker,
        )

        # Restaura threshold
        self.min_edge = original_min_edge

        # Adiciona contexto de jogo ao vivo
        for vb in value_bets:
            vb.market = f"LIVE_{minute}min_{vb.market}"

        return value_bets

    def rank_value_bets(self, value_bets: list[ValueBet]) -> list[ValueBet]:
        """Ordena value bets por qualidade (EV * confiança)."""
        confidence_weight = {"high": 1.5, "medium": 1.0, "low": 0.5}

        def score(vb: ValueBet) -> float:
            return vb.ev * confidence_weight.get(vb.confidence, 1)

        return sorted(value_bets, key=score, reverse=True)

    def filter_best_bets(
        self,
        value_bets: list[ValueBet],
        max_bets: int = 5,
        min_confidence: str = "low",
    ) -> list[ValueBet]:
        """Filtra e retorna os melhores value bets."""
        confidence_levels = {"low": 0, "medium": 1, "high": 2}
        min_level = confidence_levels.get(min_confidence, 0)

        filtered = [
            vb for vb in value_bets
            if confidence_levels.get(vb.confidence, 0) >= min_level
        ]

        ranked = self.rank_value_bets(filtered)
        return ranked[:max_bets]
