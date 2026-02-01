"""
Live Market Analyzer - LOBINHO-BET
===================================
Analisa mercados em tempo real e retorna o melhor para apostar.

Funcionalidades:
1. Coleta dados do jogo ao vivo
2. Normaliza e pondera os dados
3. Avalia TODOS os mercados disponiveis
4. Retorna o mercado com maior score de probabilidade
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
import math


class MarketType(Enum):
    """Tipos de mercado disponiveis."""
    # Gols
    OVER_05 = "over_0.5"
    OVER_15 = "over_1.5"
    OVER_25 = "over_2.5"
    OVER_35 = "over_3.5"
    UNDER_05 = "under_0.5"
    UNDER_15 = "under_1.5"
    UNDER_25 = "under_2.5"
    UNDER_35 = "under_3.5"

    # BTTS
    BTTS_YES = "btts_yes"
    BTTS_NO = "btts_no"

    # Resultado
    HOME_WIN = "home_win"
    DRAW = "draw"
    AWAY_WIN = "away_win"

    # Double Chance
    HOME_OR_DRAW = "home_or_draw"
    AWAY_OR_DRAW = "away_or_draw"
    HOME_OR_AWAY = "home_or_away"

    # Proximo Gol
    NEXT_GOAL_HOME = "next_goal_home"
    NEXT_GOAL_AWAY = "next_goal_away"
    NO_MORE_GOALS = "no_more_goals"

    # Escanteios
    CORNERS_OVER_85 = "corners_over_8.5"
    CORNERS_OVER_95 = "corners_over_9.5"
    CORNERS_OVER_105 = "corners_over_10.5"

    # Cartoes
    CARDS_OVER_35 = "cards_over_3.5"
    CARDS_OVER_45 = "cards_over_4.5"


class OddsTrend(Enum):
    """Tendencia das odds."""
    RISING = "rising"      # Subindo (menos provavel)
    STABLE = "stable"      # Estavel
    FALLING = "falling"    # Caindo (mais provavel)
    STEAM = "steam"        # Queda brusca (sharp money)


@dataclass
class LiveMatchData:
    """Dados do jogo ao vivo."""
    # Identificacao
    match_id: str
    home_team: str
    away_team: str
    league: str

    # Tempo
    minute: int
    period: str = "1H"  # 1H, HT, 2H, FT

    # Placar
    home_goals: int = 0
    away_goals: int = 0

    # Estatisticas
    home_possession: float = 50.0
    away_possession: float = 50.0

    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0

    home_dangerous_attacks: int = 0
    away_dangerous_attacks: int = 0

    home_corners: int = 0
    away_corners: int = 0

    home_yellow_cards: int = 0
    away_yellow_cards: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0

    home_fouls: int = 0
    away_fouls: int = 0

    # xG (se disponivel)
    home_xg: Optional[float] = None
    away_xg: Optional[float] = None

    # Momentum e pressao (calculado)
    home_pressure: float = 50.0  # 0-100
    away_pressure: float = 50.0
    momentum: float = 0.0  # -100 a +100 (positivo = home dominando)

    # Eventos recentes (ultimos 10 minutos)
    recent_home_shots: int = 0
    recent_away_shots: int = 0
    recent_home_corners: int = 0
    recent_away_corners: int = 0
    recent_goals: int = 0

    # Odds atuais
    odds: Dict[str, float] = field(default_factory=dict)
    odds_trend: Dict[str, OddsTrend] = field(default_factory=dict)

    @property
    def total_goals(self) -> int:
        return self.home_goals + self.away_goals

    @property
    def total_shots(self) -> int:
        return self.home_shots + self.away_shots

    @property
    def total_shots_on_target(self) -> int:
        return self.home_shots_on_target + self.away_shots_on_target

    @property
    def total_corners(self) -> int:
        return self.home_corners + self.away_corners

    @property
    def total_cards(self) -> int:
        return (self.home_yellow_cards + self.away_yellow_cards +
                self.home_red_cards + self.away_red_cards)

    @property
    def time_remaining(self) -> int:
        """Minutos restantes."""
        return max(0, 90 - self.minute)

    @property
    def is_first_half(self) -> bool:
        return self.minute <= 45

    @property
    def is_late_game(self) -> bool:
        return self.minute >= 70


@dataclass
class MarketAnalysis:
    """Resultado da analise de um mercado."""
    market: MarketType
    score: float  # 0.0 a 1.0
    probability: float  # Probabilidade estimada
    confidence: str  # "low", "medium", "high", "very_high"
    odds: float
    expected_value: float  # EV
    recommendation: str  # "strong_buy", "buy", "hold", "avoid"
    reasons: List[str] = field(default_factory=list)

    def __str__(self):
        return f"""
Mercado: {self.market.value}
Score: {self.score:.2f}
Probabilidade: {self.probability:.1%}
Confianca: {self.confidence}
Odds: {self.odds:.2f}
EV: {self.expected_value:+.1%}
Recomendacao: {self.recommendation}
Justificativa:
{chr(10).join(f'  - {r}' for r in self.reasons)}
"""


class LiveMarketAnalyzer:
    """
    Analisador de mercados ao vivo.

    Avalia todos os mercados disponiveis e retorna o melhor
    baseado em dados em tempo real do jogo.
    """

    # Pesos para calculo do score
    WEIGHTS = {
        "tempo": 0.20,
        "pressao": 0.25,
        "eventos_recentes": 0.25,
        "movimento_odds": 0.20,
        "historico": 0.10,
    }

    # Thresholds
    SCORE_VERY_HIGH = 0.80
    SCORE_HIGH = 0.65
    SCORE_MEDIUM = 0.50

    def __init__(self):
        self.market_analyzers = {
            # Gols
            MarketType.OVER_05: self._analyze_over_05,
            MarketType.OVER_15: self._analyze_over_15,
            MarketType.OVER_25: self._analyze_over_25,
            MarketType.OVER_35: self._analyze_over_35,
            MarketType.UNDER_15: self._analyze_under_15,
            MarketType.UNDER_25: self._analyze_under_25,
            MarketType.UNDER_35: self._analyze_under_35,

            # BTTS
            MarketType.BTTS_YES: self._analyze_btts_yes,
            MarketType.BTTS_NO: self._analyze_btts_no,

            # Resultado
            MarketType.HOME_WIN: self._analyze_home_win,
            MarketType.DRAW: self._analyze_draw,
            MarketType.AWAY_WIN: self._analyze_away_win,

            # Proximo gol
            MarketType.NEXT_GOAL_HOME: self._analyze_next_goal_home,
            MarketType.NEXT_GOAL_AWAY: self._analyze_next_goal_away,
            MarketType.NO_MORE_GOALS: self._analyze_no_more_goals,

            # Escanteios
            MarketType.CORNERS_OVER_85: self._analyze_corners_over,
            MarketType.CORNERS_OVER_95: self._analyze_corners_over,
            MarketType.CORNERS_OVER_105: self._analyze_corners_over,
        }

    def analyze_all_markets(self, data: LiveMatchData) -> List[MarketAnalysis]:
        """
        Analisa TODOS os mercados disponiveis.

        Returns:
            Lista de MarketAnalysis ordenada por score (maior primeiro)
        """
        results = []

        for market_type, analyzer_func in self.market_analyzers.items():
            try:
                analysis = analyzer_func(data, market_type)
                if analysis:
                    results.append(analysis)
            except Exception as e:
                print(f"Erro analisando {market_type}: {e}")

        # Ordena por score (maior primeiro)
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    def get_best_market(self, data: LiveMatchData) -> Optional[MarketAnalysis]:
        """
        Retorna o MELHOR mercado para apostar.

        Returns:
            MarketAnalysis do melhor mercado ou None se nenhum for bom
        """
        all_markets = self.analyze_all_markets(data)

        if not all_markets:
            return None

        best = all_markets[0]

        # So recomenda se score >= 0.50
        if best.score < self.SCORE_MEDIUM:
            return None

        return best

    def get_top_markets(self, data: LiveMatchData, top_n: int = 3) -> List[MarketAnalysis]:
        """
        Retorna os N melhores mercados.
        """
        all_markets = self.analyze_all_markets(data)
        return [m for m in all_markets[:top_n] if m.score >= self.SCORE_MEDIUM]

    # ========================================================================
    # AVALIADORES DE COMPONENTES
    # ========================================================================

    def _avaliar_tempo(self, data: LiveMatchData, market: MarketType) -> float:
        """
        Avalia componente de tempo (0.0 a 1.0).

        - Over: aumenta com tempo (mais chances de gol)
        - Under: diminui com tempo
        """
        minute = data.minute
        time_factor = minute / 90.0

        # Mercados Over preferem mais tempo jogado
        if "over" in market.value:
            # Bonus apos 60 minutos
            if minute >= 70:
                return min(1.0, time_factor * 1.3)
            elif minute >= 60:
                return min(1.0, time_factor * 1.2)
            return time_factor

        # Mercados Under preferem menos tempo restante
        elif "under" in market.value:
            return 1.0 - time_factor

        # Outros mercados
        return 0.5

    def _avaliar_pressao(self, data: LiveMatchData, team: str = "any") -> float:
        """
        Avalia pressao ofensiva (0.0 a 1.0).
        """
        # Calcula pressao baseada em:
        # - Posse de bola
        # - Ataques perigosos
        # - Finalizacoes recentes
        # - Escanteios recentes

        if team == "home":
            possession_factor = data.home_possession / 100
            attacks = data.home_dangerous_attacks
            recent_shots = data.recent_home_shots
            recent_corners = data.recent_home_corners
        elif team == "away":
            possession_factor = data.away_possession / 100
            attacks = data.away_dangerous_attacks
            recent_shots = data.recent_away_shots
            recent_corners = data.recent_away_corners
        else:
            # Pressao geral do jogo
            possession_factor = 0.5
            attacks = data.home_dangerous_attacks + data.away_dangerous_attacks
            recent_shots = data.recent_home_shots + data.recent_away_shots
            recent_corners = data.recent_home_corners + data.recent_away_corners

        # Normaliza ataques (0-50 -> 0-1)
        attacks_factor = min(1.0, attacks / 50)

        # Normaliza chutes recentes (0-5 -> 0-1)
        shots_factor = min(1.0, recent_shots / 5)

        # Normaliza escanteios recentes (0-3 -> 0-1)
        corners_factor = min(1.0, recent_corners / 3)

        # Media ponderada
        pressure = (
            possession_factor * 0.25 +
            attacks_factor * 0.35 +
            shots_factor * 0.25 +
            corners_factor * 0.15
        )

        return pressure

    def _avaliar_eventos_recentes(self, data: LiveMatchData, market: MarketType) -> float:
        """
        Avalia eventos recentes (ultimos 10 minutos).
        """
        # Total de eventos ofensivos recentes
        recent_activity = (
            data.recent_home_shots + data.recent_away_shots +
            data.recent_home_corners + data.recent_away_corners
        )

        # Normaliza (0-15 eventos -> 0-1)
        activity_factor = min(1.0, recent_activity / 15)

        # Para Over: alta atividade = bom
        if "over" in market.value:
            return activity_factor

        # Para Under: baixa atividade = bom
        elif "under" in market.value:
            return 1.0 - activity_factor

        return 0.5

    def _avaliar_movimento_odds(self, data: LiveMatchData, market: MarketType) -> float:
        """
        Avalia movimento das odds (steam moves).
        """
        trend = data.odds_trend.get(market.value, OddsTrend.STABLE)

        if trend == OddsTrend.STEAM:
            return 1.0  # Queda brusca = sharp money
        elif trend == OddsTrend.FALLING:
            return 0.8  # Caindo = mais provavel
        elif trend == OddsTrend.STABLE:
            return 0.5
        else:  # RISING
            return 0.2  # Subindo = menos provavel

    def _avaliar_historico(self, data: LiveMatchData, market: MarketType) -> float:
        """
        Avalia historico do mercado no jogo atual.
        """
        # Baseado no que ja aconteceu no jogo

        if "over" in market.value:
            # Extrai linha (ex: over_2.5 -> 2.5)
            try:
                line = float(market.value.split("_")[1])
            except:
                line = 2.5

            goals_needed = line - data.total_goals + 0.5
            time_per_goal = data.time_remaining / max(1, goals_needed)

            # Se precisa de muitos gols em pouco tempo
            if time_per_goal < 15:
                return 0.3
            elif time_per_goal < 25:
                return 0.5
            else:
                return 0.7

        elif "under" in market.value:
            try:
                line = float(market.value.split("_")[1])
            except:
                line = 2.5

            goals_margin = line - data.total_goals - 0.5

            if goals_margin <= 0:
                return 0.0  # Ja perdeu
            elif goals_margin <= 1:
                return 0.3  # Margem apertada
            else:
                return 0.8  # Margem confortavel

        return 0.5

    # ========================================================================
    # ANALISADORES DE MERCADOS ESPECIFICOS
    # ========================================================================

    def _analyze_over_15(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Over 1.5 gols."""
        reasons = []

        # Ja bateu?
        if data.total_goals >= 2:
            return MarketAnalysis(
                market=market,
                score=1.0,
                probability=1.0,
                confidence="very_high",
                odds=1.01,
                expected_value=0,
                recommendation="avoid",
                reasons=["Mercado ja bateu (2+ gols)"]
            )

        # Componentes
        tempo_score = self._avaliar_tempo(data, market)
        pressao_score = self._avaliar_pressao(data)
        eventos_score = self._avaliar_eventos_recentes(data, market)
        odds_score = self._avaliar_movimento_odds(data, market)
        historico_score = self._avaliar_historico(data, market)

        # Score final
        score = (
            tempo_score * self.WEIGHTS["tempo"] +
            pressao_score * self.WEIGHTS["pressao"] +
            eventos_score * self.WEIGHTS["eventos_recentes"] +
            odds_score * self.WEIGHTS["movimento_odds"] +
            historico_score * self.WEIGHTS["historico"]
        )

        # Ajustes especificos
        if data.total_goals == 1:
            score *= 1.2  # Ja tem 1 gol, precisa de mais 1
            reasons.append("Ja tem 1 gol, precisa de apenas mais 1")

        if data.minute >= 60 and data.total_shots_on_target >= 8:
            score *= 1.15
            reasons.append(f"Alta finalizacao no alvo ({data.total_shots_on_target})")

        if data.home_dangerous_attacks + data.away_dangerous_attacks >= 40:
            score *= 1.1
            reasons.append("Alto numero de ataques perigosos")

        if data.odds_trend.get(market.value) == OddsTrend.FALLING:
            reasons.append("Odds em queda (mercado aquecendo)")

        # Calcula probabilidade e EV
        odds = data.odds.get(market.value, 1.50)
        probability = min(0.95, score)
        ev = (probability * odds) - 1

        # Confianca e recomendacao
        confidence, recommendation = self._get_confidence_recommendation(score, ev)

        if data.minute >= 70:
            reasons.append(f"Jogo em fase final ({data.minute}')")

        return MarketAnalysis(
            market=market,
            score=min(1.0, score),
            probability=probability,
            confidence=confidence,
            odds=odds,
            expected_value=ev,
            recommendation=recommendation,
            reasons=reasons if reasons else ["Analise padrao"]
        )

    def _analyze_over_05(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Over 0.5 gols."""
        if data.total_goals >= 1:
            return MarketAnalysis(
                market=market, score=1.0, probability=1.0,
                confidence="very_high", odds=1.01, expected_value=0,
                recommendation="avoid", reasons=["Mercado ja bateu"]
            )

        # Similar ao over 1.5 mas mais facil
        score = self._avaliar_pressao(data) * 0.4 + self._avaliar_tempo(data, market) * 0.3 + 0.3
        odds = data.odds.get(market.value, 1.20)
        probability = min(0.98, score * 1.2)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="high" if score > 0.7 else "medium",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="buy" if score > 0.6 else "hold",
            reasons=["Over 0.5 tem alta probabilidade historica"]
        )

    def _analyze_over_25(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Over 2.5 gols."""
        reasons = []

        if data.total_goals >= 3:
            return MarketAnalysis(
                market=market, score=1.0, probability=1.0,
                confidence="very_high", odds=1.01, expected_value=0,
                recommendation="avoid", reasons=["Mercado ja bateu (3+ gols)"]
            )

        # Componentes
        tempo_score = self._avaliar_tempo(data, market)
        pressao_score = self._avaliar_pressao(data)
        eventos_score = self._avaliar_eventos_recentes(data, market)
        odds_score = self._avaliar_movimento_odds(data, market)

        score = (
            tempo_score * 0.25 +
            pressao_score * 0.30 +
            eventos_score * 0.25 +
            odds_score * 0.20
        )

        # Ajustes
        goals_needed = 3 - data.total_goals
        if goals_needed == 1:
            score *= 1.25
            reasons.append(f"Precisa de apenas 1 gol (atual: {data.total_goals})")
        elif goals_needed == 2:
            score *= 1.1
            reasons.append(f"Precisa de 2 gols (atual: {data.total_goals})")

        if data.minute < 60 and data.total_shots_on_target >= 6:
            score *= 1.15
            reasons.append("Jogo aberto com muitas finalizacoes")

        odds = data.odds.get(market.value, 1.85)
        probability = min(0.90, score)
        ev = (probability * odds) - 1
        confidence, recommendation = self._get_confidence_recommendation(score, ev)

        return MarketAnalysis(
            market=market, score=min(1.0, score), probability=probability,
            confidence=confidence, odds=odds, expected_value=ev,
            recommendation=recommendation, reasons=reasons if reasons else ["Analise Over 2.5"]
        )

    def _analyze_over_35(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Over 3.5 gols."""
        if data.total_goals >= 4:
            return MarketAnalysis(
                market=market, score=1.0, probability=1.0,
                confidence="very_high", odds=1.01, expected_value=0,
                recommendation="avoid", reasons=["Mercado ja bateu"]
            )

        goals_needed = 4 - data.total_goals
        time_remaining = data.time_remaining

        # Score mais conservador para over 3.5
        score = 0.3

        if goals_needed <= 2 and time_remaining >= 30:
            score = 0.6
        elif goals_needed == 1:
            score = 0.75

        if data.total_shots_on_target >= 10:
            score *= 1.2

        odds = data.odds.get(market.value, 2.50)
        probability = min(0.85, score)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="medium" if score > 0.5 else "low",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="buy" if score > 0.65 else "hold",
            reasons=[f"Precisa de {goals_needed} gols em {time_remaining} minutos"]
        )

    def _analyze_under_15(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Under 1.5 gols."""
        if data.total_goals >= 2:
            return MarketAnalysis(
                market=market, score=0.0, probability=0.0,
                confidence="very_high", odds=1.0, expected_value=-1,
                recommendation="avoid", reasons=["Mercado ja perdeu (2+ gols)"]
            )

        reasons = []
        score = 0.5

        # Quanto mais tarde e menos gols, melhor
        if data.minute >= 75 and data.total_goals <= 1:
            score = 0.85
            reasons.append(f"Jogo travado ({data.total_goals} gols aos {data.minute}')")

        # Poucas finalizacoes = bom para under
        if data.total_shots_on_target <= 4:
            score *= 1.2
            reasons.append(f"Poucas finalizacoes no alvo ({data.total_shots_on_target})")

        # Muitas faltas = jogo truncado
        if data.home_fouls + data.away_fouls >= 20:
            score *= 1.1
            reasons.append("Jogo com muitas faltas")

        odds = data.odds.get(market.value, 2.20)
        probability = min(0.90, score)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="high" if score > 0.7 else "medium",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="buy" if score > 0.65 else "hold",
            reasons=reasons if reasons else ["Analise Under 1.5"]
        )

    def _analyze_under_25(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Under 2.5 gols."""
        if data.total_goals >= 3:
            return MarketAnalysis(
                market=market, score=0.0, probability=0.0,
                confidence="very_high", odds=1.0, expected_value=-1,
                recommendation="avoid", reasons=["Mercado ja perdeu (3+ gols)"]
            )

        reasons = []
        margin = 2 - data.total_goals  # Quantos gols pode levar

        # Base score
        score = 0.4 + (data.minute / 90) * 0.3

        if margin >= 2:
            score += 0.2
            reasons.append(f"Margem confortavel ({margin} gols)")

        if data.minute >= 70 and data.total_goals <= 1:
            score = 0.80
            reasons.append(f"Fase final com apenas {data.total_goals} gol(s)")

        # Ritmo baixo favorece under
        if data.total_shots <= 10 and data.minute >= 45:
            score *= 1.15
            reasons.append("Ritmo de jogo baixo")

        odds = data.odds.get(market.value, 1.95)
        probability = min(0.88, score)
        confidence, recommendation = self._get_confidence_recommendation(score, (probability * odds) - 1)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence=confidence, odds=odds,
            expected_value=(probability * odds) - 1,
            recommendation=recommendation,
            reasons=reasons if reasons else ["Analise Under 2.5"]
        )

    def _analyze_under_35(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Under 3.5 gols."""
        if data.total_goals >= 4:
            return MarketAnalysis(
                market=market, score=0.0, probability=0.0,
                confidence="very_high", odds=1.0, expected_value=-1,
                recommendation="avoid", reasons=["Mercado ja perdeu"]
            )

        margin = 3 - data.total_goals
        score = 0.5 + (data.minute / 90) * 0.25

        if margin >= 2:
            score += 0.15

        odds = data.odds.get(market.value, 1.45)
        probability = min(0.92, score)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="high" if score > 0.7 else "medium",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="buy" if score > 0.6 else "hold",
            reasons=[f"Margem de {margin} gols, {data.time_remaining}' restantes"]
        )

    def _analyze_btts_yes(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Ambas Marcam - Sim."""
        home_scored = data.home_goals > 0
        away_scored = data.away_goals > 0

        if home_scored and away_scored:
            return MarketAnalysis(
                market=market, score=1.0, probability=1.0,
                confidence="very_high", odds=1.01, expected_value=0,
                recommendation="avoid", reasons=["BTTS ja aconteceu"]
            )

        reasons = []
        score = 0.4

        # Um time ja marcou
        if home_scored or away_scored:
            score = 0.65
            team_missing = "visitante" if home_scored else "mandante"
            reasons.append(f"Falta apenas o {team_missing} marcar")

            # Verifica pressao do time que falta marcar
            if home_scored:
                pressure = self._avaliar_pressao(data, "away")
            else:
                pressure = self._avaliar_pressao(data, "home")

            if pressure > 0.6:
                score *= 1.2
                reasons.append(f"Time pressionando ({pressure:.0%})")

        # Ambos com chutes no alvo
        if data.home_shots_on_target >= 2 and data.away_shots_on_target >= 2:
            score *= 1.15
            reasons.append("Ambos times finalizando no alvo")

        odds = data.odds.get(market.value, 1.75)
        probability = min(0.88, score)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="high" if score > 0.7 else "medium",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="buy" if score > 0.65 else "hold",
            reasons=reasons if reasons else ["Analise BTTS Sim"]
        )

    def _analyze_btts_no(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Ambas Marcam - Nao."""
        home_scored = data.home_goals > 0
        away_scored = data.away_goals > 0

        if home_scored and away_scored:
            return MarketAnalysis(
                market=market, score=0.0, probability=0.0,
                confidence="very_high", odds=1.0, expected_value=-1,
                recommendation="avoid", reasons=["BTTS ja aconteceu - mercado perdido"]
            )

        reasons = []
        score = 0.5

        # Nenhum marcou ainda
        if not home_scored and not away_scored:
            if data.minute >= 60:
                score = 0.70
                reasons.append(f"0-0 aos {data.minute}' - tendencia de under")

        # Um time zerado
        elif not home_scored or not away_scored:
            team_zero = "mandante" if not home_scored else "visitante"
            if data.minute >= 70:
                score = 0.65
                reasons.append(f"{team_zero} sem marcar aos {data.minute}'")

        odds = data.odds.get(market.value, 2.00)
        probability = min(0.85, score)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="medium",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="hold",
            reasons=reasons if reasons else ["Analise BTTS Nao"]
        )

    def _analyze_home_win(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Vitoria Mandante."""
        reasons = []
        diff = data.home_goals - data.away_goals

        if diff > 0:
            # Mandante vencendo
            score = 0.6 + (data.minute / 90) * 0.3
            reasons.append(f"Vencendo por {diff} gol(s)")

            if diff >= 2:
                score = min(0.95, score + 0.15)
                reasons.append("Vantagem confortavel")
        elif diff == 0:
            # Empate
            score = 0.35 + self._avaliar_pressao(data, "home") * 0.3
            reasons.append("Jogo empatado")
        else:
            # Perdendo
            score = 0.2 + self._avaliar_pressao(data, "home") * 0.2
            reasons.append(f"Perdendo por {abs(diff)} gol(s)")

        odds = data.odds.get(market.value, 2.00)
        probability = min(0.92, score)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="high" if score > 0.7 else "medium" if score > 0.5 else "low",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="buy" if score > 0.7 else "hold",
            reasons=reasons
        )

    def _analyze_draw(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Empate."""
        reasons = []
        diff = abs(data.home_goals - data.away_goals)

        if diff == 0:
            # Ja esta empatado
            score = 0.5 + (data.minute / 90) * 0.35
            reasons.append(f"Empate aos {data.minute}'")

            if data.minute >= 80:
                score = min(0.90, score + 0.15)
                reasons.append("Fase final - empate provavel")
        elif diff == 1:
            # Diferenca de 1 gol
            score = 0.25 + self._avaliar_pressao(data) * 0.2
            reasons.append("Diferenca de 1 gol")
        else:
            # Diferenca grande
            score = 0.1
            reasons.append(f"Diferenca de {diff} gols - empate improvavel")

        odds = data.odds.get(market.value, 3.50)
        probability = min(0.85, score)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="high" if score > 0.7 else "medium" if score > 0.4 else "low",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="buy" if score > 0.65 else "hold",
            reasons=reasons
        )

    def _analyze_away_win(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Vitoria Visitante."""
        reasons = []
        diff = data.away_goals - data.home_goals

        if diff > 0:
            score = 0.6 + (data.minute / 90) * 0.3
            reasons.append(f"Vencendo por {diff} gol(s)")
            if diff >= 2:
                score = min(0.95, score + 0.15)
        elif diff == 0:
            score = 0.30 + self._avaliar_pressao(data, "away") * 0.25
            reasons.append("Jogo empatado")
        else:
            score = 0.15 + self._avaliar_pressao(data, "away") * 0.2
            reasons.append(f"Perdendo por {abs(diff)} gol(s)")

        odds = data.odds.get(market.value, 2.50)
        probability = min(0.92, score)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="high" if score > 0.7 else "medium" if score > 0.5 else "low",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="buy" if score > 0.7 else "hold",
            reasons=reasons
        )

    def _analyze_next_goal_home(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Proximo Gol - Mandante."""
        pressure = self._avaliar_pressao(data, "home")
        score = pressure * 0.7 + 0.2

        if data.home_shots_on_target > data.away_shots_on_target:
            score *= 1.15

        odds = data.odds.get(market.value, 2.20)
        probability = min(0.75, score)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="medium",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="buy" if score > 0.6 else "hold",
            reasons=[f"Pressao mandante: {pressure:.0%}"]
        )

    def _analyze_next_goal_away(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Proximo Gol - Visitante."""
        pressure = self._avaliar_pressao(data, "away")
        score = pressure * 0.7 + 0.15

        if data.away_shots_on_target > data.home_shots_on_target:
            score *= 1.15

        odds = data.odds.get(market.value, 2.80)
        probability = min(0.70, score)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="medium",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="buy" if score > 0.55 else "hold",
            reasons=[f"Pressao visitante: {pressure:.0%}"]
        )

    def _analyze_no_more_goals(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercado Sem Mais Gols."""
        score = (data.minute / 90) * 0.5 + 0.2

        if data.total_shots_on_target <= 3 and data.minute >= 60:
            score *= 1.3

        if data.minute >= 80:
            score = min(0.85, score + 0.2)

        odds = data.odds.get(market.value, 3.00)
        probability = min(0.80, score)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="medium" if score > 0.5 else "low",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="hold",
            reasons=[f"Jogo aos {data.minute}', {data.total_shots_on_target} finalizacoes no alvo"]
        )

    def _analyze_corners_over(self, data: LiveMatchData, market: MarketType) -> MarketAnalysis:
        """Analisa mercados de escanteios."""
        try:
            line = float(market.value.split("_")[2])
        except:
            line = 9.5

        corners_needed = line - data.total_corners + 0.5
        time_remaining = data.time_remaining

        # Media de escanteios por minuto ate agora
        if data.minute > 0:
            corners_per_min = data.total_corners / data.minute
            projected = data.total_corners + (corners_per_min * time_remaining)
        else:
            projected = 10  # Media default

        score = 0.5
        if projected > line:
            score = 0.7
        if corners_needed <= 2 and time_remaining >= 20:
            score = 0.75

        odds = data.odds.get(market.value, 1.90)
        probability = min(0.85, score)

        return MarketAnalysis(
            market=market, score=score, probability=probability,
            confidence="medium",
            odds=odds, expected_value=(probability * odds) - 1,
            recommendation="buy" if score > 0.65 else "hold",
            reasons=[f"Atual: {data.total_corners}, Precisa: {corners_needed:.0f}, Projecao: {projected:.1f}"]
        )

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _get_confidence_recommendation(self, score: float, ev: float) -> tuple:
        """Retorna confianca e recomendacao baseado no score e EV."""
        if score >= self.SCORE_VERY_HIGH:
            confidence = "very_high"
            recommendation = "strong_buy" if ev > 0.05 else "buy"
        elif score >= self.SCORE_HIGH:
            confidence = "high"
            recommendation = "buy" if ev > 0 else "hold"
        elif score >= self.SCORE_MEDIUM:
            confidence = "medium"
            recommendation = "hold"
        else:
            confidence = "low"
            recommendation = "avoid"

        return confidence, recommendation


# ============================================================================
# FUNCAO PRINCIPAL
# ============================================================================

def analisar_mercado_live(dados_jogo: LiveMatchData) -> dict:
    """
    Funcao principal para analisar mercados ao vivo.

    Args:
        dados_jogo: LiveMatchData com dados do jogo

    Returns:
        Dict com mercado recomendado e alternativas
    """
    analyzer = LiveMarketAnalyzer()

    best = analyzer.get_best_market(dados_jogo)
    top_3 = analyzer.get_top_markets(dados_jogo, top_n=3)

    result = {
        "match": f"{dados_jogo.home_team} vs {dados_jogo.away_team}",
        "minute": dados_jogo.minute,
        "score": f"{dados_jogo.home_goals}-{dados_jogo.away_goals}",
        "best_market": None,
        "alternatives": [],
        "all_markets": [],
    }

    if best:
        result["best_market"] = {
            "market": best.market.value,
            "probability": f"{best.probability:.1%}",
            "score": f"{best.score:.2f}",
            "odds": best.odds,
            "ev": f"{best.expected_value:+.1%}",
            "confidence": best.confidence,
            "recommendation": best.recommendation,
            "reasons": best.reasons,
        }

    for m in top_3[1:] if len(top_3) > 1 else []:
        result["alternatives"].append({
            "market": m.market.value,
            "probability": f"{m.probability:.1%}",
            "score": f"{m.score:.2f}",
        })

    return result


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Simula dados de um jogo ao vivo
    jogo = LiveMatchData(
        match_id="TEST001",
        home_team="Manchester City",
        away_team="Liverpool",
        league="Premier League",
        minute=67,
        period="2H",
        home_goals=1,
        away_goals=1,
        home_possession=58,
        away_possession=42,
        home_shots=14,
        away_shots=9,
        home_shots_on_target=6,
        away_shots_on_target=4,
        home_dangerous_attacks=45,
        away_dangerous_attacks=32,
        home_corners=6,
        away_corners=4,
        recent_home_shots=3,
        recent_away_shots=1,
        recent_home_corners=2,
        recent_away_corners=0,
        odds={
            "over_1.5": 1.25,
            "over_2.5": 1.85,
            "over_3.5": 2.80,
            "under_2.5": 1.95,
            "under_3.5": 1.45,
            "btts_yes": 1.40,
            "btts_no": 2.75,
            "home_win": 2.10,
            "draw": 3.60,
            "away_win": 3.40,
        },
        odds_trend={
            "over_2.5": OddsTrend.FALLING,
            "under_2.5": OddsTrend.RISING,
        }
    )

    # Analisa
    resultado = analisar_mercado_live(jogo)

    print("=" * 60)
    print(f"ANALISE: {resultado['match']}")
    print(f"Minuto: {resultado['minute']}' | Placar: {resultado['score']}")
    print("=" * 60)

    if resultado["best_market"]:
        best = resultado["best_market"]
        print(f"\n🎯 MERCADO RECOMENDADO: {best['market'].upper()}")
        print(f"   Probabilidade: {best['probability']}")
        print(f"   Score: {best['score']}")
        print(f"   Odds: {best['odds']}")
        print(f"   EV: {best['ev']}")
        print(f"   Confianca: {best['confidence']}")
        print(f"   Recomendacao: {best['recommendation']}")
        print(f"\n   Justificativa:")
        for r in best["reasons"]:
            print(f"   - {r}")

    if resultado["alternatives"]:
        print(f"\n📊 ALTERNATIVAS:")
        for alt in resultado["alternatives"]:
            print(f"   - {alt['market']}: {alt['probability']} (score: {alt['score']})")
