"""
Local Predictor - 100% Offline
===============================
Roda todos os modelos estatisticos localmente.
Nao precisa de internet ou APIs externas.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

from src.local.sample_data import (
    TEAMS, TEAM_FORM, get_team_data, get_team_form, get_h2h,
    get_sample_matches, generate_odds, get_match_odds, FIXED_ODDS
)


class Signal(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    AVOID = "avoid"


@dataclass
class Prediction:
    """Resultado da predicao."""
    match_id: str
    home_team: str
    away_team: str
    league: str
    kickoff: datetime

    # Probabilidades
    home_win: float = 0.0
    draw: float = 0.0
    away_win: float = 0.0
    over_25: float = 0.0
    btts: float = 0.0

    # Expected Goals
    home_xg: float = 0.0
    away_xg: float = 0.0

    # Odds
    odds: dict = field(default_factory=dict)
    fair_odds: dict = field(default_factory=dict)

    # Value Bets
    best_value: Optional[str] = None
    best_edge: float = 0.0
    kelly_stake: float = 0.0
    signal: Signal = Signal.HOLD

    # Detalhes por modelo
    model_predictions: dict = field(default_factory=dict)

    def __str__(self):
        return f"""
{'='*60}
{self.home_team} vs {self.away_team}
{self.league} - {self.kickoff.strftime('%d/%m %H:%M')}
{'='*60}

PROBABILIDADES (Ensemble):
  Casa:   {self.home_win:.1%}  (fair odds: {self.fair_odds.get('home', 0):.2f})
  Empate: {self.draw:.1%}  (fair odds: {self.fair_odds.get('draw', 0):.2f})
  Fora:   {self.away_win:.1%}  (fair odds: {self.fair_odds.get('away', 0):.2f})

EXPECTED GOALS:
  {self.home_team}: {self.home_xg:.2f}
  {self.away_team}: {self.away_xg:.2f}
  Over 2.5: {self.over_25:.1%}
  BTTS: {self.btts:.1%}

ODDS DO MERCADO:
  Casa:   {self.odds.get('home', 0):.2f}
  Empate: {self.odds.get('draw', 0):.2f}
  Fora:   {self.odds.get('away', 0):.2f}

VALUE BET:
  Melhor: {self.best_value or 'Nenhum'}
  Edge: {self.best_edge:.1f}%
  Kelly: {self.kelly_stake:.1f}%
  Signal: {self.signal.value.upper()}
"""


class LocalPredictor:
    """
    Preditor 100% local usando modelos estatisticos.
    """

    # Pesos do Ensemble
    WEIGHTS = {
        "poisson": 0.25,
        "dixon_coles": 0.30,
        "elo": 0.20,
        "markov": 0.15,
        "bradley_terry": 0.10,
    }

    # Dixon-Coles rho parameter
    RHO = -0.13

    def __init__(self, min_edge: float = 3.0, kelly_fraction: float = 0.25):
        self.min_edge = min_edge
        self.kelly_fraction = kelly_fraction

    def predict_match(self, match: dict) -> Prediction:
        """
        Gera predicao completa para um jogo.
        """
        home_key = match["home_team"]
        away_key = match["away_team"]

        home_data = get_team_data(home_key) or self._default_team(home_key)
        away_data = get_team_data(away_key) or self._default_team(away_key)

        home_form = get_team_form(home_key)
        away_form = get_team_form(away_key)
        h2h = get_h2h(home_key, away_key)

        # Predicoes individuais
        predictions = {}

        # 1. Poisson
        predictions["poisson"] = self._poisson_predict(home_data, away_data)

        # 2. Dixon-Coles
        predictions["dixon_coles"] = self._dixon_coles_predict(home_data, away_data)

        # 3. ELO
        predictions["elo"] = self._elo_predict(home_data, away_data)

        # 4. Markov
        predictions["markov"] = self._markov_predict(home_form, away_form)

        # 5. Bradley-Terry
        predictions["bradley_terry"] = self._bradley_terry_predict(home_data, away_data)

        # Ensemble
        ensemble = self._combine_predictions(predictions)

        # Expected Goals
        home_xg = (home_data["avg_goals_home"] + away_data["avg_conceded_away"]) / 2
        away_xg = (away_data["avg_goals_away"] + home_data["avg_conceded_home"]) / 2

        # Over 2.5 e BTTS
        over_25 = self._calculate_over_25(home_xg, away_xg)
        btts = self._calculate_btts(home_xg, away_xg)

        # Gera odds de mercado (fixas ou simuladas)
        market_odds = get_match_odds(
            match["id"],
            ensemble["home_win"],
            ensemble["draw"],
            ensemble["away_win"]
        )

        # Fair odds
        fair_odds = {
            "home": round(1 / ensemble["home_win"], 2) if ensemble["home_win"] > 0 else 99,
            "draw": round(1 / ensemble["draw"], 2) if ensemble["draw"] > 0 else 99,
            "away": round(1 / ensemble["away_win"], 2) if ensemble["away_win"] > 0 else 99,
        }

        # Detecta Value Bet
        best_value, best_edge, kelly = self._find_value_bet(ensemble, market_odds)

        # Signal
        signal = self._calculate_signal(best_edge)

        return Prediction(
            match_id=match["id"],
            home_team=home_data["name"],
            away_team=away_data["name"],
            league=match["league"],
            kickoff=match["kickoff"],
            home_win=ensemble["home_win"],
            draw=ensemble["draw"],
            away_win=ensemble["away_win"],
            over_25=over_25,
            btts=btts,
            home_xg=home_xg,
            away_xg=away_xg,
            odds=market_odds,
            fair_odds=fair_odds,
            best_value=best_value,
            best_edge=best_edge,
            kelly_stake=kelly,
            signal=signal,
            model_predictions=predictions,
        )

    def predict_all(self) -> list[Prediction]:
        """Gera predicoes para todos os jogos de exemplo."""
        matches = get_sample_matches()
        predictions = []

        for match in matches:
            pred = self.predict_match(match)
            predictions.append(pred)

        # Ordena por edge (melhores primeiro)
        predictions.sort(key=lambda p: p.best_edge, reverse=True)

        return predictions

    # ========================================================================
    # MODELOS INDIVIDUAIS
    # ========================================================================

    def _poisson_predict(self, home: dict, away: dict) -> dict:
        """Modelo Poisson simples."""
        # Lambda esperado
        home_lambda = (home["avg_goals_home"] + away["avg_conceded_away"]) / 2 * home["attack"]
        away_lambda = (away["avg_goals_away"] + home["avg_conceded_home"]) / 2 * away["attack"]

        # Ajuste de home advantage
        home_lambda *= (1 + home["home_advantage"])

        # Calcula probabilidades
        home_win = 0.0
        draw = 0.0
        away_win = 0.0

        for h in range(8):
            for a in range(8):
                p = self._poisson_prob(home_lambda, h) * self._poisson_prob(away_lambda, a)
                if h > a:
                    home_win += p
                elif h == a:
                    draw += p
                else:
                    away_win += p

        return {"home_win": home_win, "draw": draw, "away_win": away_win}

    def _dixon_coles_predict(self, home: dict, away: dict) -> dict:
        """Modelo Dixon-Coles com correcao para placares baixos."""
        home_lambda = (home["avg_goals_home"] + away["avg_conceded_away"]) / 2 * home["attack"]
        away_lambda = (away["avg_goals_away"] + home["avg_conceded_home"]) / 2 * away["attack"]

        home_lambda *= (1 + home["home_advantage"])

        home_win = 0.0
        draw = 0.0
        away_win = 0.0

        for h in range(8):
            for a in range(8):
                p_base = self._poisson_prob(home_lambda, h) * self._poisson_prob(away_lambda, a)

                # Aplica correcao tau de Dixon-Coles
                tau = self._tau(h, a, home_lambda, away_lambda)
                p = p_base * tau

                if h > a:
                    home_win += p
                elif h == a:
                    draw += p
                else:
                    away_win += p

        # Normaliza
        total = home_win + draw + away_win
        return {
            "home_win": home_win / total,
            "draw": draw / total,
            "away_win": away_win / total
        }

    def _tau(self, h: int, a: int, lh: float, la: float) -> float:
        """Fator de correcao Dixon-Coles para placares baixos."""
        if h == 0 and a == 0:
            return 1 - lh * la * self.RHO
        elif h == 0 and a == 1:
            return 1 + lh * self.RHO
        elif h == 1 and a == 0:
            return 1 + la * self.RHO
        elif h == 1 and a == 1:
            return 1 - self.RHO
        else:
            return 1.0

    def _elo_predict(self, home: dict, away: dict) -> dict:
        """Modelo ELO com home advantage."""
        home_elo = home["elo"] + 65  # Home advantage em pontos ELO
        away_elo = away["elo"]

        # Expected score
        exp_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))

        # Converte para 3-way
        draw_factor = 0.26 - abs(exp_home - 0.5) * 0.2
        home_win = exp_home - draw_factor / 2
        away_win = (1 - exp_home) - draw_factor / 2
        draw = draw_factor

        # Normaliza
        total = home_win + draw + away_win
        return {
            "home_win": max(0, home_win / total),
            "draw": max(0, draw / total),
            "away_win": max(0, away_win / total)
        }

    def _markov_predict(self, home_form: str, away_form: str) -> dict:
        """Modelo Markov baseado em forma recente."""
        home_strength = self._form_to_strength(home_form)
        away_strength = self._form_to_strength(away_form)

        total_strength = home_strength + away_strength

        # Probabilidades baseadas em forma + bonus casa
        home_base = (home_strength / total_strength) * 1.1
        away_base = (away_strength / total_strength) * 0.9

        # Normaliza
        home_win = home_base / (home_base + away_base + 0.5) * 0.8
        away_win = away_base / (home_base + away_base + 0.5) * 0.8
        draw = 1 - home_win - away_win

        return {"home_win": home_win, "draw": draw, "away_win": away_win}

    def _form_to_strength(self, form: str) -> float:
        """Converte forma (WDLWW) em forca numerica."""
        weights = {"W": 3, "D": 1, "L": 0}
        recent = form[-5:]  # Ultimos 5 jogos

        strength = sum(weights.get(r, 1) for r in recent)
        # Bonus para sequencia
        if recent[-3:] == "WWW":
            strength *= 1.2
        elif recent[-3:] == "LLL":
            strength *= 0.8

        return max(1, strength)

    def _bradley_terry_predict(self, home: dict, away: dict) -> dict:
        """Modelo Bradley-Terry."""
        # Usa squad value como proxy de forca
        home_strength = home["squad_value"] * home["attack"]
        away_strength = away["squad_value"] * away["attack"]

        # Home advantage
        home_strength *= (1 + home["home_advantage"])

        p_home = home_strength / (home_strength + away_strength)
        p_away = away_strength / (home_strength + away_strength)

        # Adiciona draw
        draw = 0.25 - abs(p_home - 0.5) * 0.2
        home_win = p_home * (1 - draw)
        away_win = p_away * (1 - draw)

        return {"home_win": home_win, "draw": draw, "away_win": away_win}

    # ========================================================================
    # ENSEMBLE
    # ========================================================================

    def _combine_predictions(self, predictions: dict) -> dict:
        """Combina predicoes com media ponderada."""
        result = {"home_win": 0, "draw": 0, "away_win": 0}

        for model_name, pred in predictions.items():
            weight = self.WEIGHTS.get(model_name, 0.1)
            result["home_win"] += pred["home_win"] * weight
            result["draw"] += pred["draw"] * weight
            result["away_win"] += pred["away_win"] * weight

        # Normaliza para somar 100%
        total = result["home_win"] + result["draw"] + result["away_win"]
        result["home_win"] /= total
        result["draw"] /= total
        result["away_win"] /= total

        return result

    # ========================================================================
    # UTILS
    # ========================================================================

    def _poisson_prob(self, lam: float, k: int) -> float:
        """Probabilidade Poisson P(X=k)."""
        return (math.exp(-lam) * (lam ** k)) / math.factorial(k)

    def _calculate_over_25(self, home_xg: float, away_xg: float) -> float:
        """Calcula probabilidade de Over 2.5 gols."""
        total_lambda = home_xg + away_xg
        under = sum(
            self._poisson_prob(total_lambda, k)
            for k in range(3)
        )
        return 1 - under

    def _calculate_btts(self, home_xg: float, away_xg: float) -> float:
        """Calcula probabilidade de ambos marcarem."""
        p_home_scores = 1 - self._poisson_prob(home_xg, 0)
        p_away_scores = 1 - self._poisson_prob(away_xg, 0)
        return p_home_scores * p_away_scores

    def _find_value_bet(self, probs: dict, odds: dict) -> tuple[Optional[str], float, float]:
        """Encontra o melhor value bet."""
        best_market = None
        best_edge = 0.0
        best_kelly = 0.0

        markets = [
            ("home", probs["home_win"], odds.get("home", 1)),
            ("draw", probs["draw"], odds.get("draw", 1)),
            ("away", probs["away_win"], odds.get("away", 1)),
        ]

        for market, prob, market_odds in markets:
            if market_odds <= 1:
                continue

            implied_prob = 1 / market_odds
            edge = (prob - implied_prob) * 100

            if edge > best_edge:
                best_edge = edge
                best_market = market

                # Kelly Criterion
                b = market_odds - 1
                q = 1 - prob
                kelly = ((b * prob - q) / b) * self.kelly_fraction * 100
                best_kelly = max(0, kelly)

        if best_edge < self.min_edge:
            return None, best_edge, 0.0

        return best_market, best_edge, best_kelly

    def _calculate_signal(self, edge: float) -> Signal:
        """Calcula signal baseado no edge."""
        if edge >= 8:
            return Signal.STRONG_BUY
        elif edge >= 5:
            return Signal.BUY
        elif edge >= 2:
            return Signal.HOLD
        else:
            return Signal.AVOID

    def _default_team(self, name: str) -> dict:
        """Time padrao se nao encontrado."""
        return {
            "name": name.replace("_", " ").title(),
            "country": "Unknown",
            "league": "Unknown",
            "elo": 1500,
            "squad_value": 50.0,
            "attack": 1.0,
            "defense": 1.0,
            "home_advantage": 0.10,
            "avg_goals_home": 1.3,
            "avg_goals_away": 1.0,
            "avg_conceded_home": 1.2,
            "avg_conceded_away": 1.4,
        }
