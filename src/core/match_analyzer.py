"""
Match Analyzer - Análise Completa de Partidas
=============================================
Combina:
1. Pré-análise (histórico, investimentos, elenco)
2. Análise estatística (form, xG, H2H)
3. Análise em tempo real (durante o jogo)

Fluxo:
PRÉ-JOGO → TEMPO REAL → DECISÃO
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
from enum import Enum
from loguru import logger

from src.collectors import FootyStatsCollector, OddsAPICollector, FBrefScraper
from src.collectors.live_stats import LiveMatchStats, calculate_live_indicators
from src.processors.team_analysis import TeamAnalyzer, get_pre_match_analysis
from src.models.predictor import MatchPredictor
from src.models.value_detector import ValueDetector, ValueBet
from src.strategy.leagues import LeagueManager


class AnalysisPhase(Enum):
    """Fase da análise."""
    PRE_MATCH = "pre_match"      # Pré-jogo (horas antes)
    PRE_KICKOFF = "pre_kickoff"  # Antes do início (minutos)
    FIRST_HALF = "first_half"    # Primeiro tempo
    HALFTIME = "halftime"        # Intervalo
    SECOND_HALF = "second_half"  # Segundo tempo
    FINISHED = "finished"        # Finalizado


@dataclass
class MatchAnalysis:
    """Análise completa de uma partida."""

    match_id: str
    home_team: str
    away_team: str
    league: str
    kickoff: datetime
    phase: AnalysisPhase = AnalysisPhase.PRE_MATCH

    # ========================
    # FASE 1: PRÉ-ANÁLISE
    # ========================
    pre_analysis: dict = field(default_factory=dict)
    # Inclui:
    # - Valor de elenco (home vs away)
    # - Investimentos da temporada
    # - Lesões/Suspensões
    # - Vantagem baseada em recursos

    # ========================
    # FASE 2: ANÁLISE ESTATÍSTICA
    # ========================
    stats_analysis: dict = field(default_factory=dict)
    # Inclui:
    # - Forma recente (últimos 5 jogos)
    # - Head-to-head
    # - xG/xGA
    # - Home/Away performance
    # - Tendências de Over/Under
    # - BTTS percentage

    # ========================
    # FASE 3: PREVISÃO ML
    # ========================
    ml_prediction: dict = field(default_factory=dict)
    # Inclui:
    # - Probabilidades (home/draw/away)
    # - Previsão de gols
    # - Confiança do modelo

    # ========================
    # FASE 4: ODDS & VALUE
    # ========================
    odds: dict = field(default_factory=dict)
    value_bets: list[ValueBet] = field(default_factory=list)

    # ========================
    # FASE 5: TEMPO REAL
    # ========================
    live_stats: Optional[LiveMatchStats] = None
    live_indicators: dict = field(default_factory=dict)
    live_value_bets: list[ValueBet] = field(default_factory=list)

    # ========================
    # DECISÃO FINAL
    # ========================
    final_recommendation: dict = field(default_factory=dict)
    confidence_score: float = 0.0  # 0-100

    def to_summary(self) -> dict:
        """Gera resumo da análise."""
        return {
            "match": f"{self.home_team} vs {self.away_team}",
            "league": self.league,
            "kickoff": self.kickoff.isoformat(),
            "phase": self.phase.value,
            "pre_analysis": {
                "advantage": self.pre_analysis.get("advantage_score", {}),
                "concerns": self.pre_analysis.get("concerns", {}),
            },
            "prediction": {
                "home_win": self.ml_prediction.get("home_win", 0),
                "draw": self.ml_prediction.get("draw", 0),
                "away_win": self.ml_prediction.get("away_win", 0),
            },
            "value_bets": len(self.value_bets),
            "recommendation": self.final_recommendation,
            "confidence": self.confidence_score,
        }


class MatchAnalyzer:
    """
    Analisador completo de partidas.

    Executa análise em múltiplas fases:
    1. Pré-análise (investimentos, elenco)
    2. Estatísticas históricas
    3. Previsão ML
    4. Comparação com odds
    5. Monitoramento em tempo real
    """

    def __init__(self):
        self.predictor = MatchPredictor()
        self.value_detector = ValueDetector()
        self.league_manager = LeagueManager()
        self.analyses: dict[str, MatchAnalysis] = {}

    async def full_analysis(
        self,
        match_id: str,
        home_team: str,
        away_team: str,
        league: str,
        kickoff: datetime,
    ) -> MatchAnalysis:
        """
        Executa análise completa de uma partida.
        """
        logger.info(f"Starting full analysis: {home_team} vs {away_team}")

        analysis = MatchAnalysis(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            league=league,
            kickoff=kickoff,
        )

        # Fase 1: Pré-análise (elenco, investimentos)
        await self._run_pre_analysis(analysis)

        # Fase 2: Análise estatística
        await self._run_stats_analysis(analysis)

        # Fase 3: Previsão ML
        await self._run_ml_prediction(analysis)

        # Fase 4: Busca odds e detecta value
        await self._run_odds_analysis(analysis)

        # Fase 5: Gera recomendação final
        self._generate_recommendation(analysis)

        # Salva análise
        self.analyses[match_id] = analysis

        logger.info(f"Analysis complete: {home_team} vs {away_team} | Confidence: {analysis.confidence_score:.1f}%")

        return analysis

    async def _run_pre_analysis(self, analysis: MatchAnalysis):
        """Fase 1: Pré-análise de elencos e investimentos."""
        logger.debug(f"Running pre-analysis for {analysis.home_team} vs {analysis.away_team}")

        try:
            pre_data = await get_pre_match_analysis(
                analysis.home_team,
                analysis.away_team,
            )
            analysis.pre_analysis = pre_data.get("pre_analysis", {})
        except Exception as e:
            logger.error(f"Pre-analysis error: {e}")
            analysis.pre_analysis = {}

    async def _run_stats_analysis(self, analysis: MatchAnalysis):
        """Fase 2: Análise estatística histórica."""
        logger.debug(f"Running stats analysis for {analysis.home_team} vs {analysis.away_team}")

        try:
            async with FootyStatsCollector() as collector:
                # Busca stats dos times (simplificado)
                # Em produção, buscar IDs reais dos times
                home_stats = {}  # await collector.get_team_stats(home_id)
                away_stats = {}  # await collector.get_team_stats(away_id)

            analysis.stats_analysis = {
                "home_form": home_stats.get("form", []),
                "away_form": away_stats.get("form", []),
                "home_goals_avg": home_stats.get("goals_avg", 0),
                "away_goals_avg": away_stats.get("goals_avg", 0),
                "home_xg": home_stats.get("xg", 0),
                "away_xg": away_stats.get("xg", 0),
            }

        except Exception as e:
            logger.error(f"Stats analysis error: {e}")

    async def _run_ml_prediction(self, analysis: MatchAnalysis):
        """Fase 3: Previsão usando modelo ML."""
        logger.debug(f"Running ML prediction for {analysis.home_team} vs {analysis.away_team}")

        try:
            # Monta features do match
            match_data = {
                "home_form": analysis.stats_analysis.get("home_form_points", 8),
                "away_form": analysis.stats_analysis.get("away_form_points", 7),
                "home_goals_avg": analysis.stats_analysis.get("home_goals_avg", 1.5),
                "away_goals_avg": analysis.stats_analysis.get("away_goals_avg", 1.2),
                "home_conceded_avg": analysis.stats_analysis.get("home_conceded_avg", 1.0),
                "away_conceded_avg": analysis.stats_analysis.get("away_conceded_avg", 1.1),
                "home_xg": analysis.stats_analysis.get("home_xg", 1.4),
                "away_xg": analysis.stats_analysis.get("away_xg", 1.2),
                "home_xga": analysis.stats_analysis.get("home_xga", 1.0),
                "away_xga": analysis.stats_analysis.get("away_xga", 1.1),
                "home_position": 5,
                "away_position": 8,
                "h2h_home_wins": 3,
                "h2h_draws": 2,
                "h2h_away_wins": 2,
                "home_rest_days": 7,
                "away_rest_days": 7,
            }

            # Adiciona dados da pré-análise
            if analysis.pre_analysis.get("advantage_score", {}).get("favors") == "home":
                match_data["home_form"] += 2
            elif analysis.pre_analysis.get("advantage_score", {}).get("favors") == "away":
                match_data["away_form"] += 2

            prediction = self.predictor.predict(match_data)
            analysis.ml_prediction = prediction

        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            # Fallback para probabilidades neutras
            analysis.ml_prediction = {
                "home_win": 0.40,
                "draw": 0.28,
                "away_win": 0.32,
            }

    async def _run_odds_analysis(self, analysis: MatchAnalysis):
        """Fase 4: Busca odds e detecta value bets."""
        logger.debug(f"Running odds analysis for {analysis.home_team} vs {analysis.away_team}")

        try:
            # Busca odds
            async with OddsAPICollector() as collector:
                # Simplificado - em produção buscar pela liga
                league_key = self.league_manager.get_league(analysis.league)
                if league_key and league_key.odds_api_key:
                    odds_data = await collector.get_matches(sport=league_key.odds_api_key)

                    # Encontra odds do jogo específico
                    for match_odds in odds_data:
                        if (analysis.home_team.lower() in match_odds.get("home_team", "").lower() or
                            match_odds.get("home_team", "").lower() in analysis.home_team.lower()):
                            best_odds = collector.find_best_odds(match_odds)
                            analysis.odds = {
                                "home": best_odds["home"]["odds"],
                                "draw": best_odds["draw"]["odds"],
                                "away": best_odds["away"]["odds"],
                            }
                            break

            # Detecta value bets
            if analysis.odds and analysis.ml_prediction:
                analysis.value_bets = self.value_detector.detect_value(
                    match_id=analysis.match_id,
                    home_team=analysis.home_team,
                    away_team=analysis.away_team,
                    predictions=analysis.ml_prediction,
                    odds=analysis.odds,
                )

        except Exception as e:
            logger.error(f"Odds analysis error: {e}")

    def _generate_recommendation(self, analysis: MatchAnalysis):
        """Gera recomendação final combinando todas as análises."""

        # Pesos para cada fase
        pre_weight = 0.15     # Pré-análise (investimentos)
        stats_weight = 0.25   # Estatísticas históricas
        ml_weight = 0.35      # Previsão ML
        value_weight = 0.25   # Odds/Value

        confidence = 0.0
        recommendation = {
            "action": "wait",  # bet_home, bet_away, bet_draw, bet_over, wait
            "market": None,
            "odds": None,
            "stake_percent": 0,
            "reasoning": [],
        }

        # Analisa pré-análise
        pre_adv = analysis.pre_analysis.get("advantage_score", {})
        if pre_adv.get("strength") == "strong":
            confidence += 15 * pre_weight
            recommendation["reasoning"].append(
                f"Vantagem de recursos para {pre_adv.get('favors')}"
            )

        # Analisa previsão ML
        pred = analysis.ml_prediction
        best_outcome = max(pred.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0)
        if best_outcome[1] > 0.45:
            confidence += 30 * ml_weight
            recommendation["reasoning"].append(
                f"ML prevê {best_outcome[0]} com {best_outcome[1]*100:.1f}%"
            )

        # Analisa value bets
        if analysis.value_bets:
            best_value = max(analysis.value_bets, key=lambda x: x.edge)
            confidence += min(best_value.edge, 20) * value_weight

            recommendation["action"] = f"bet_{best_value.market}"
            recommendation["market"] = best_value.market
            recommendation["odds"] = best_value.odds
            recommendation["stake_percent"] = best_value.kelly_stake
            recommendation["reasoning"].append(
                f"Value bet: {best_value.selection} @ {best_value.odds} (edge: {best_value.edge:.1f}%)"
            )

        analysis.confidence_score = min(100, confidence)
        analysis.final_recommendation = recommendation

    async def update_live_analysis(
        self,
        match_id: str,
        live_stats: LiveMatchStats,
    ) -> MatchAnalysis:
        """Atualiza análise com dados ao vivo."""
        if match_id not in self.analyses:
            logger.warning(f"No analysis found for match {match_id}")
            return None

        analysis = self.analyses[match_id]
        analysis.phase = AnalysisPhase.FIRST_HALF if live_stats.minute < 45 else AnalysisPhase.SECOND_HALF
        analysis.live_stats = live_stats
        analysis.live_indicators = calculate_live_indicators(live_stats)

        # Detecta value bets ao vivo
        # (ajusta probabilidades baseado no momentum/pressão)
        live_predictions = self._adjust_predictions_live(analysis)

        if analysis.odds:
            analysis.live_value_bets = self.value_detector.detect_live_value(
                match_id=match_id,
                home_team=analysis.home_team,
                away_team=analysis.away_team,
                live_predictions=live_predictions,
                live_odds=analysis.odds,  # Em produção, buscar odds live
                minute=live_stats.minute,
                score=(live_stats.home_goals, live_stats.away_goals),
            )

        return analysis

    def _adjust_predictions_live(self, analysis: MatchAnalysis) -> dict:
        """Ajusta previsões baseado nos dados ao vivo."""
        if not analysis.live_stats:
            return analysis.ml_prediction

        stats = analysis.live_stats
        base_pred = analysis.ml_prediction.copy()

        # Ajusta baseado no momentum
        momentum = stats.momentum_score
        if momentum > 30:
            base_pred["home_win"] = min(0.95, base_pred.get("home_win", 0.33) * 1.15)
        elif momentum < -30:
            base_pred["away_win"] = min(0.95, base_pred.get("away_win", 0.33) * 1.15)

        # Ajusta baseado na pressão
        home_pressure = stats.get_pressure_index("home")
        away_pressure = stats.get_pressure_index("away")

        if home_pressure > 70:
            base_pred["over_2.5"] = min(0.90, base_pred.get("over_2.5", 0.50) * 1.2)
        if away_pressure > 70:
            base_pred["over_2.5"] = min(0.90, base_pred.get("over_2.5", 0.50) * 1.2)

        return base_pred

    def get_analysis(self, match_id: str) -> Optional[MatchAnalysis]:
        """Retorna análise de um jogo."""
        return self.analyses.get(match_id)

    def get_all_recommendations(self) -> list[dict]:
        """Retorna recomendações de todas as análises."""
        return [
            {
                "match": f"{a.home_team} vs {a.away_team}",
                "recommendation": a.final_recommendation,
                "confidence": a.confidence_score,
            }
            for a in self.analyses.values()
            if a.final_recommendation.get("action") != "wait"
        ]
