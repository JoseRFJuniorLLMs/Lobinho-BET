"""
Advanced Predictors
===================
Múltiplos modelos de previsão para combinar em ensemble:

1. Markov Chain - Transições de estados
2. Poisson - Distribuição de gols
3. ELO Rating - Sistema de ranking
4. Bradley-Terry - Comparação pareada
5. Monte Carlo - Simulação de cenários
6. Neural Network - Deep Learning (opcional)

O Ensemble combina todos para previsão final.
"""

import numpy as np
from scipy import stats
from typing import Optional
from dataclasses import dataclass
from loguru import logger
import math


# ============================================================================
# 1. POISSON MODEL - Previsão de gols
# ============================================================================

@dataclass
class PoissonPrediction:
    """Previsão do modelo Poisson."""
    home_goals_expected: float
    away_goals_expected: float
    home_win: float
    draw: float
    away_win: float
    over_2_5: float
    under_2_5: float
    btts_yes: float
    exact_scores: dict  # {(0,0): prob, (1,0): prob, ...}


class PoissonPredictor:
    """
    Modelo de Poisson para previsão de gols.

    Assume que gols seguem distribuição de Poisson:
    P(k gols) = (λ^k * e^-λ) / k!

    Onde λ é a média de gols esperada.
    """

    def __init__(self):
        # Fatores de ajuste
        self.home_advantage = 1.25  # Casa marca 25% mais
        self.league_avg_goals = 2.6  # Média de gols por jogo

    def calculate_expected_goals(
        self,
        home_attack: float,
        home_defense: float,
        away_attack: float,
        away_defense: float,
    ) -> tuple[float, float]:
        """
        Calcula gols esperados para cada time.

        Args:
            home_attack: Força de ataque do mandante (gols/jogo)
            home_defense: Força defensiva do mandante (gols sofridos/jogo)
            away_attack: Força de ataque do visitante
            away_defense: Força defensiva do visitante

        Returns:
            (home_expected, away_expected)
        """
        # Normaliza para média da liga
        avg = self.league_avg_goals / 2

        home_expected = (home_attack / avg) * (away_defense / avg) * avg * self.home_advantage
        away_expected = (away_attack / avg) * (home_defense / avg) * avg

        return home_expected, away_expected

    def predict(
        self,
        home_attack: float,
        home_defense: float,
        away_attack: float,
        away_defense: float,
        max_goals: int = 6,
    ) -> PoissonPrediction:
        """
        Gera previsão completa usando Poisson.
        """
        home_exp, away_exp = self.calculate_expected_goals(
            home_attack, home_defense, away_attack, away_defense
        )

        # Calcula probabilidades de cada placar
        exact_scores = {}
        home_win = draw = away_win = 0
        over_2_5 = under_2_5 = 0
        btts_yes = 0

        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                # P(home=h) * P(away=a)
                prob = stats.poisson.pmf(h, home_exp) * stats.poisson.pmf(a, away_exp)
                exact_scores[(h, a)] = prob

                # Resultados
                if h > a:
                    home_win += prob
                elif h == a:
                    draw += prob
                else:
                    away_win += prob

                # Over/Under
                if h + a > 2.5:
                    over_2_5 += prob
                else:
                    under_2_5 += prob

                # BTTS
                if h > 0 and a > 0:
                    btts_yes += prob

        return PoissonPrediction(
            home_goals_expected=round(home_exp, 2),
            away_goals_expected=round(away_exp, 2),
            home_win=round(home_win, 4),
            draw=round(draw, 4),
            away_win=round(away_win, 4),
            over_2_5=round(over_2_5, 4),
            under_2_5=round(under_2_5, 4),
            btts_yes=round(btts_yes, 4),
            exact_scores=exact_scores,
        )

    def get_most_likely_scores(self, prediction: PoissonPrediction, top_n: int = 5) -> list[tuple]:
        """Retorna placares mais prováveis."""
        sorted_scores = sorted(
            prediction.exact_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return [(f"{s[0]}-{s[1]}", round(p * 100, 1)) for (s, p) in sorted_scores[:top_n]]


# ============================================================================
# 2. ELO RATING - Sistema de ranking
# ============================================================================

class EloRating:
    """
    Sistema ELO adaptado para futebol.

    Cada time tem um rating que sobe/desce baseado em:
    - Resultado do jogo
    - Diferença de rating dos adversários
    - Margem de vitória
    """

    def __init__(
        self,
        k_factor: float = 32,
        home_advantage: float = 65,
        initial_rating: float = 1500,
    ):
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.initial_rating = initial_rating
        self.ratings: dict[str, float] = {}

    def get_rating(self, team_id: str) -> float:
        """Retorna rating de um time."""
        return self.ratings.get(team_id, self.initial_rating)

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Calcula score esperado (probabilidade de vitória).
        Fórmula ELO: E = 1 / (1 + 10^((Rb - Ra) / 400))
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def predict_match(self, home_id: str, away_id: str) -> dict:
        """
        Prevê resultado baseado nos ratings ELO.
        """
        home_rating = self.get_rating(home_id) + self.home_advantage
        away_rating = self.get_rating(away_id)

        home_expected = self.expected_score(home_rating, away_rating)
        away_expected = 1 - home_expected

        # Ajusta para incluir empate
        draw_prob = 0.25 * (1 - abs(home_expected - 0.5) * 2)
        home_win = home_expected * (1 - draw_prob)
        away_win = away_expected * (1 - draw_prob)

        return {
            "home_rating": round(home_rating, 0),
            "away_rating": round(away_rating, 0),
            "rating_diff": round(home_rating - away_rating, 0),
            "home_win": round(home_win, 4),
            "draw": round(draw_prob, 4),
            "away_win": round(away_win, 4),
        }

    def update_ratings(
        self,
        home_id: str,
        away_id: str,
        home_goals: int,
        away_goals: int,
    ):
        """
        Atualiza ratings após um jogo.
        """
        home_rating = self.get_rating(home_id)
        away_rating = self.get_rating(away_id)

        # Score real (1 = vitória, 0.5 = empate, 0 = derrota)
        if home_goals > away_goals:
            home_score, away_score = 1, 0
        elif home_goals == away_goals:
            home_score, away_score = 0.5, 0.5
        else:
            home_score, away_score = 0, 1

        # Score esperado (com vantagem de casa)
        home_expected = self.expected_score(
            home_rating + self.home_advantage,
            away_rating,
        )
        away_expected = 1 - home_expected

        # Fator de margem (vitórias por muitos gols = mais pontos)
        goal_diff = abs(home_goals - away_goals)
        margin_factor = 1 + 0.1 * min(goal_diff, 3)

        # Atualiza ratings
        home_new = home_rating + self.k_factor * margin_factor * (home_score - home_expected)
        away_new = away_rating + self.k_factor * margin_factor * (away_score - away_expected)

        self.ratings[home_id] = home_new
        self.ratings[away_id] = away_new

        return {
            "home_change": round(home_new - home_rating, 1),
            "away_change": round(away_new - away_rating, 1),
        }

    def get_rankings(self, top_n: int = 20) -> list[tuple[str, float]]:
        """Retorna ranking de times."""
        sorted_teams = sorted(
            self.ratings.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_teams[:top_n]


# ============================================================================
# 3. MONTE CARLO - Simulação
# ============================================================================

class MonteCarloSimulator:
    """
    Simulação Monte Carlo para prever resultados.

    Simula milhares de jogos e conta frequência de resultados.
    """

    def __init__(self, n_simulations: int = 10000):
        self.n_simulations = n_simulations

    def simulate_match(
        self,
        home_attack: float,
        home_defense: float,
        away_attack: float,
        away_defense: float,
    ) -> dict:
        """
        Simula um jogo N vezes e retorna estatísticas.
        """
        home_wins = 0
        draws = 0
        away_wins = 0
        total_goals = []
        btts_count = 0
        score_counts = {}

        for _ in range(self.n_simulations):
            # Simula gols usando Poisson
            home_goals = np.random.poisson(home_attack)
            away_goals = np.random.poisson(away_attack * (home_defense / 1.3))

            # Registra resultado
            if home_goals > away_goals:
                home_wins += 1
            elif home_goals == away_goals:
                draws += 1
            else:
                away_wins += 1

            # Estatísticas
            total_goals.append(home_goals + away_goals)
            if home_goals > 0 and away_goals > 0:
                btts_count += 1

            # Placar
            score = (home_goals, away_goals)
            score_counts[score] = score_counts.get(score, 0) + 1

        n = self.n_simulations
        return {
            "home_win": round(home_wins / n, 4),
            "draw": round(draws / n, 4),
            "away_win": round(away_wins / n, 4),
            "avg_total_goals": round(np.mean(total_goals), 2),
            "over_2_5": round(sum(1 for g in total_goals if g > 2.5) / n, 4),
            "btts": round(btts_count / n, 4),
            "most_likely_score": max(score_counts.items(), key=lambda x: x[1]),
            "simulations": n,
        }


# ============================================================================
# 4. ENSEMBLE - Combina todos os modelos
# ============================================================================

@dataclass
class EnsemblePrediction:
    """Previsão combinada de múltiplos modelos."""
    home_win: float
    draw: float
    away_win: float
    confidence: float
    over_2_5: float
    btts: float
    model_agreement: float  # Quanto os modelos concordam
    individual_predictions: dict


class EnsemblePredictor:
    """
    Combina múltiplos modelos para previsão final.

    Modelos:
    1. Markov (peso: 0.20) - Padrões de forma
    2. Poisson (peso: 0.25) - Distribuição de gols
    3. ELO (peso: 0.25) - Força relativa
    4. Monte Carlo (peso: 0.15) - Simulação
    5. Graph/Neo4j (peso: 0.15) - Relações

    Peso final = média ponderada ajustada por confiança.
    """

    def __init__(self):
        from src.models.markov_predictor import MarkovPredictor

        self.markov = MarkovPredictor()
        self.poisson = PoissonPredictor()
        self.elo = EloRating()
        self.montecarlo = MonteCarloSimulator(n_simulations=5000)

        # Pesos dos modelos
        self.weights = {
            "markov": 0.20,
            "poisson": 0.25,
            "elo": 0.25,
            "montecarlo": 0.15,
            "graph": 0.15,
        }

    def predict(
        self,
        home_team: str,
        away_team: str,
        home_form: list[str],
        away_form: list[str],
        home_attack: float,
        home_defense: float,
        away_attack: float,
        away_defense: float,
        h2h: list[str] = None,
    ) -> EnsemblePrediction:
        """
        Gera previsão ensemble combinando todos os modelos.
        """
        predictions = {}

        # 1. Markov
        markov_pred = self.markov.predict_match(home_form, away_form, h2h)
        predictions["markov"] = {
            "home_win": markov_pred.home_win,
            "draw": markov_pred.draw,
            "away_win": markov_pred.away_win,
            "confidence": markov_pred.confidence,
        }

        # 2. Poisson
        poisson_pred = self.poisson.predict(
            home_attack, home_defense, away_attack, away_defense
        )
        predictions["poisson"] = {
            "home_win": poisson_pred.home_win,
            "draw": poisson_pred.draw,
            "away_win": poisson_pred.away_win,
            "over_2_5": poisson_pred.over_2_5,
            "btts": poisson_pred.btts_yes,
        }

        # 3. ELO
        elo_pred = self.elo.predict_match(home_team, away_team)
        predictions["elo"] = {
            "home_win": elo_pred["home_win"],
            "draw": elo_pred["draw"],
            "away_win": elo_pred["away_win"],
        }

        # 4. Monte Carlo
        mc_pred = self.montecarlo.simulate_match(
            home_attack, home_defense, away_attack, away_defense
        )
        predictions["montecarlo"] = {
            "home_win": mc_pred["home_win"],
            "draw": mc_pred["draw"],
            "away_win": mc_pred["away_win"],
            "over_2_5": mc_pred["over_2_5"],
            "btts": mc_pred["btts"],
        }

        # 5. Graph (placeholder - seria integração com Neo4j)
        predictions["graph"] = {
            "home_win": 0.40,
            "draw": 0.28,
            "away_win": 0.32,
        }

        # Combina previsões
        home_win = draw = away_win = 0
        over_2_5 = btts = 0
        total_weight = 0

        for model, weight in self.weights.items():
            pred = predictions.get(model, {})
            home_win += pred.get("home_win", 0.33) * weight
            draw += pred.get("draw", 0.33) * weight
            away_win += pred.get("away_win", 0.33) * weight

            if "over_2_5" in pred:
                over_2_5 += pred["over_2_5"] * weight
            if "btts" in pred:
                btts += pred["btts"] * weight

            total_weight += weight

        # Normaliza
        total = home_win + draw + away_win
        home_win /= total
        draw /= total
        away_win /= total

        # Calcula concordância entre modelos
        home_probs = [p.get("home_win", 0.33) for p in predictions.values()]
        agreement = 1 - np.std(home_probs) * 3  # Menor desvio = maior concordância
        agreement = max(0, min(1, agreement))

        # Confiança baseada em concordância e clareza da previsão
        max_prob = max(home_win, draw, away_win)
        confidence = (agreement * 0.5 + (max_prob - 0.33) * 1.5 * 0.5) * 100

        return EnsemblePrediction(
            home_win=round(home_win, 4),
            draw=round(draw, 4),
            away_win=round(away_win, 4),
            confidence=round(confidence, 1),
            over_2_5=round(over_2_5 / 0.4, 4) if over_2_5 else 0.5,  # Normaliza
            btts=round(btts / 0.4, 4) if btts else 0.5,
            model_agreement=round(agreement * 100, 1),
            individual_predictions=predictions,
        )


# ============================================================================
# Funções de conveniência
# ============================================================================

def quick_ensemble_predict(
    home_form: str,
    away_form: str,
    home_goals_avg: float = 1.5,
    away_goals_avg: float = 1.2,
) -> dict:
    """
    Previsão rápida usando ensemble.

    Args:
        home_form: Forma do mandante (ex: "WDWWL")
        away_form: Forma do visitante (ex: "LLWDW")
        home_goals_avg: Média de gols do mandante
        away_goals_avg: Média de gols do visitante
    """
    ensemble = EnsemblePredictor()

    prediction = ensemble.predict(
        home_team="home",
        away_team="away",
        home_form=list(home_form.upper()),
        away_form=list(away_form.upper()),
        home_attack=home_goals_avg,
        home_defense=1.2,
        away_attack=away_goals_avg,
        away_defense=1.3,
    )

    return {
        "home_win": f"{prediction.home_win * 100:.1f}%",
        "draw": f"{prediction.draw * 100:.1f}%",
        "away_win": f"{prediction.away_win * 100:.1f}%",
        "confidence": f"{prediction.confidence:.1f}%",
        "model_agreement": f"{prediction.model_agreement:.1f}%",
        "over_2.5": f"{prediction.over_2_5 * 100:.1f}%",
        "btts": f"{prediction.btts * 100:.1f}%",
    }
