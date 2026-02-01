"""
Newton Stats - Modelos Estatísticos Avançados
==============================================
Para transformar o LOBINHO-BET em um sistema estatístico de elite.

Modelos Implementados:
1. Dixon-Coles (ajuste para empates e gols baixos)
2. Bradley-Terry (comparação pareada)
3. Bayesian Inference (atualização de crenças)
4. Brier Score (calibração de probabilidades)
5. Kelly Dinâmico (otimização de stake)
6. Backtesting Framework
"""

import numpy as np
from scipy import stats
from scipy.optimize import minimize
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from loguru import logger
import math


# ============================================================================
# 1. DIXON-COLES MODEL
# ============================================================================

class DixonColesModel:
    """
    Modelo Dixon-Coles (1997) - Padrão da indústria para previsão de futebol.

    Melhoria sobre Poisson puro:
    - Ajusta para correlação entre gols (0-0, 1-0, 0-1, 1-1 são mais frequentes)
    - Parâmetro rho (ρ) corrige subdispersão em placares baixos
    - Decay temporal (resultados recentes pesam mais)
    """

    def __init__(self, rho: float = -0.13, time_decay: float = 0.0018):
        """
        Args:
            rho: Parâmetro de dependência (tipicamente -0.1 a -0.2)
            time_decay: Fator de decaimento temporal por dia
        """
        self.rho = rho
        self.time_decay = time_decay
        self.team_attack: dict[str, float] = {}
        self.team_defense: dict[str, float] = {}
        self.home_advantage: float = 0.25
        self.league_avg: float = 1.3  # Média de gols por time

    def tau(self, home_goals: int, away_goals: int, lambda_h: float, lambda_a: float) -> float:
        """
        Fator de ajuste τ para placares baixos.
        Corrige a independência assumida por Poisson.
        """
        if home_goals == 0 and away_goals == 0:
            return 1 - lambda_h * lambda_a * self.rho
        elif home_goals == 0 and away_goals == 1:
            return 1 + lambda_h * self.rho
        elif home_goals == 1 and away_goals == 0:
            return 1 + lambda_a * self.rho
        elif home_goals == 1 and away_goals == 1:
            return 1 - self.rho
        else:
            return 1.0

    def weight(self, days_ago: int) -> float:
        """Peso temporal - jogos recentes pesam mais."""
        return math.exp(-self.time_decay * days_ago)

    def log_likelihood(
        self,
        params: np.ndarray,
        matches: list[dict],
        team_index: dict[str, int],
    ) -> float:
        """
        Log-likelihood para otimização MLE.
        Maximizar isso encontra os melhores parâmetros.
        """
        n_teams = len(team_index)
        attack = params[:n_teams]
        defense = params[n_teams:2*n_teams]
        home_adv = params[-1]

        log_lik = 0

        for match in matches:
            home_idx = team_index[match["home_team"]]
            away_idx = team_index[match["away_team"]]

            lambda_h = math.exp(attack[home_idx] + defense[away_idx] + home_adv)
            lambda_a = math.exp(attack[away_idx] + defense[home_idx])

            home_goals = match["home_goals"]
            away_goals = match["away_goals"]
            days_ago = match.get("days_ago", 0)

            # Probabilidade Poisson
            prob_h = stats.poisson.pmf(home_goals, lambda_h)
            prob_a = stats.poisson.pmf(away_goals, lambda_a)

            # Ajuste Dixon-Coles
            tau = self.tau(home_goals, away_goals, lambda_h, lambda_a)

            # Peso temporal
            weight = self.weight(days_ago)

            log_lik += weight * math.log(prob_h * prob_a * tau + 1e-10)

        return -log_lik  # Negativo porque scipy minimiza

    def fit(self, matches: list[dict]) -> dict:
        """
        Treina modelo com histórico de jogos.

        Args:
            matches: Lista de jogos com home_team, away_team, home_goals, away_goals, days_ago

        Returns:
            Dict com parâmetros otimizados
        """
        # Cria índice de times
        teams = set()
        for m in matches:
            teams.add(m["home_team"])
            teams.add(m["away_team"])
        team_index = {team: i for i, team in enumerate(sorted(teams))}
        n_teams = len(team_index)

        # Parâmetros iniciais
        initial_params = np.zeros(2 * n_teams + 1)

        # Otimiza
        result = minimize(
            self.log_likelihood,
            initial_params,
            args=(matches, team_index),
            method="L-BFGS-B",
        )

        # Extrai parâmetros
        attack = result.x[:n_teams]
        defense = result.x[n_teams:2*n_teams]
        home_adv = result.x[-1]

        # Salva
        for team, idx in team_index.items():
            self.team_attack[team] = attack[idx]
            self.team_defense[team] = defense[idx]
        self.home_advantage = home_adv

        return {
            "teams": len(team_index),
            "matches": len(matches),
            "home_advantage": home_adv,
            "convergence": result.success,
        }

    def predict(self, home_team: str, away_team: str, max_goals: int = 6) -> dict:
        """Prevê resultado usando parâmetros treinados."""
        attack_h = self.team_attack.get(home_team, 0)
        defense_h = self.team_defense.get(home_team, 0)
        attack_a = self.team_attack.get(away_team, 0)
        defense_a = self.team_defense.get(away_team, 0)

        lambda_h = math.exp(attack_h + defense_a + self.home_advantage)
        lambda_a = math.exp(attack_a + defense_h)

        # Matriz de probabilidades
        home_win = draw = away_win = 0
        probs = {}

        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                prob_h = stats.poisson.pmf(h, lambda_h)
                prob_a = stats.poisson.pmf(a, lambda_a)
                tau = self.tau(h, a, lambda_h, lambda_a)

                prob = prob_h * prob_a * tau
                probs[(h, a)] = prob

                if h > a:
                    home_win += prob
                elif h == a:
                    draw += prob
                else:
                    away_win += prob

        return {
            "home_win": round(home_win, 4),
            "draw": round(draw, 4),
            "away_win": round(away_win, 4),
            "expected_home_goals": round(lambda_h, 2),
            "expected_away_goals": round(lambda_a, 2),
            "most_likely_score": max(probs.items(), key=lambda x: x[1]),
        }


# ============================================================================
# 2. BRADLEY-TERRY MODEL
# ============================================================================

class BradleyTerryModel:
    """
    Modelo Bradley-Terry para comparação pareada.

    P(A vence B) = strength_A / (strength_A + strength_B)

    Usado para rankings e previsões head-to-head.
    """

    def __init__(self):
        self.strengths: dict[str, float] = {}

    def fit(self, matches: list[dict], iterations: int = 100):
        """
        Treina usando algoritmo iterativo MM (Minorization-Maximization).
        """
        # Coleta times
        teams = set()
        for m in matches:
            teams.add(m["home_team"])
            teams.add(m["away_team"])

        # Inicializa forças iguais
        for team in teams:
            self.strengths[team] = 1.0

        # Conta vitórias
        wins = {team: 0 for team in teams}
        for m in matches:
            if m["home_goals"] > m["away_goals"]:
                wins[m["home_team"]] += 1
            elif m["away_goals"] > m["home_goals"]:
                wins[m["away_team"]] += 1
            else:
                # Empate = 0.5 vitória para cada
                wins[m["home_team"]] += 0.5
                wins[m["away_team"]] += 0.5

        # Iterações MM
        for _ in range(iterations):
            new_strengths = {}

            for team in teams:
                numerator = wins[team]
                denominator = 0

                for m in matches:
                    if m["home_team"] == team:
                        other = m["away_team"]
                    elif m["away_team"] == team:
                        other = m["home_team"]
                    else:
                        continue

                    denominator += 1 / (self.strengths[team] + self.strengths[other])

                new_strengths[team] = numerator / (denominator + 1e-10)

            # Normaliza
            total = sum(new_strengths.values())
            for team in teams:
                self.strengths[team] = new_strengths[team] / total * len(teams)

    def predict(self, team_a: str, team_b: str) -> dict:
        """Probabilidade de A vencer B."""
        s_a = self.strengths.get(team_a, 1.0)
        s_b = self.strengths.get(team_b, 1.0)

        p_a = s_a / (s_a + s_b)
        p_b = s_b / (s_a + s_b)

        return {
            "team_a_win": round(p_a, 4),
            "team_b_win": round(p_b, 4),
            "strength_a": round(s_a, 3),
            "strength_b": round(s_b, 3),
            "strength_ratio": round(s_a / s_b, 3),
        }

    def get_rankings(self, top_n: int = 20) -> list[tuple]:
        """Retorna ranking por força."""
        return sorted(self.strengths.items(), key=lambda x: x[1], reverse=True)[:top_n]


# ============================================================================
# 3. BAYESIAN INFERENCE
# ============================================================================

class BayesianPredictor:
    """
    Inferência Bayesiana para atualização de probabilidades.

    Prior → Likelihood → Posterior

    Começa com prior (crença inicial) e atualiza conforme novos dados.
    """

    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0):
        """
        Usa distribuição Beta como prior para probabilidades.

        Args:
            prior_alpha: Parâmetro α da Beta (pseudocontagem de sucessos)
            prior_beta: Parâmetro β da Beta (pseudocontagem de fracassos)
        """
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.team_params: dict[str, tuple[float, float]] = {}

    def update(self, team: str, wins: int, losses: int):
        """
        Atualiza crença sobre um time após observar resultados.

        Posterior = Beta(α + wins, β + losses)
        """
        alpha, beta = self.team_params.get(team, (self.prior_alpha, self.prior_beta))
        self.team_params[team] = (alpha + wins, beta + losses)

    def get_win_probability(self, team: str) -> dict:
        """Retorna distribuição de probabilidade de vitória."""
        alpha, beta = self.team_params.get(team, (self.prior_alpha, self.prior_beta))

        # Média da Beta
        mean = alpha / (alpha + beta)

        # Intervalo de credibilidade 95%
        lower = stats.beta.ppf(0.025, alpha, beta)
        upper = stats.beta.ppf(0.975, alpha, beta)

        # Variância
        variance = (alpha * beta) / ((alpha + beta)**2 * (alpha + beta + 1))

        return {
            "mean": round(mean, 4),
            "std": round(math.sqrt(variance), 4),
            "ci_95_lower": round(lower, 4),
            "ci_95_upper": round(upper, 4),
            "alpha": alpha,
            "beta": beta,
            "confidence": round(1 - (upper - lower), 4),  # Quão "certo" estamos
        }

    def predict_match(self, home: str, away: str) -> dict:
        """Previsão bayesiana de um jogo."""
        home_params = self.get_win_probability(home)
        away_params = self.get_win_probability(away)

        # Simulação Monte Carlo para combinar distribuições
        n_samples = 10000
        home_samples = stats.beta.rvs(
            *self.team_params.get(home, (1, 1)),
            size=n_samples,
        )
        away_samples = stats.beta.rvs(
            *self.team_params.get(away, (1, 1)),
            size=n_samples,
        )

        # Probabilidade de casa vencer
        home_wins = np.sum(home_samples > away_samples) / n_samples

        return {
            "home_win": round(home_wins, 4),
            "away_win": round(1 - home_wins, 4),
            "home_confidence": home_params["confidence"],
            "away_confidence": away_params["confidence"],
        }


# ============================================================================
# 4. MÉTRICAS DE CALIBRAÇÃO
# ============================================================================

@dataclass
class CalibrationMetrics:
    """Métricas para avaliar qualidade das previsões."""

    brier_score: float = 0.0
    log_loss: float = 0.0
    calibration_error: float = 0.0
    sharpness: float = 0.0
    roi: float = 0.0
    hit_rate: float = 0.0


class ModelCalibration:
    """
    Avalia calibração e qualidade das previsões.

    Um modelo bem calibrado:
    - Quando diz 70%, acerta ~70% das vezes
    - Brier Score baixo (0 = perfeito)
    - Log Loss baixo
    """

    def __init__(self):
        self.predictions: list[dict] = []
        self.outcomes: list[int] = []

    def add_prediction(self, prob: float, outcome: int):
        """
        Adiciona previsão e resultado.

        Args:
            prob: Probabilidade prevista (0-1)
            outcome: 1 se acertou, 0 se errou
        """
        self.predictions.append({"prob": prob, "outcome": outcome})
        self.outcomes.append(outcome)

    def brier_score(self) -> float:
        """
        Brier Score = média de (prob - outcome)²

        0 = perfeito, 1 = pior possível
        Referência: ~0.25 é random (50/50)
        """
        if not self.predictions:
            return 0

        score = sum(
            (p["prob"] - p["outcome"])**2
            for p in self.predictions
        ) / len(self.predictions)

        return round(score, 4)

    def log_loss(self) -> float:
        """
        Log Loss = -média de [y*log(p) + (1-y)*log(1-p)]

        Penaliza fortemente previsões confiantes e erradas.
        """
        if not self.predictions:
            return 0

        eps = 1e-15  # Evita log(0)
        loss = 0

        for p in self.predictions:
            prob = np.clip(p["prob"], eps, 1 - eps)
            if p["outcome"] == 1:
                loss -= math.log(prob)
            else:
                loss -= math.log(1 - prob)

        return round(loss / len(self.predictions), 4)

    def calibration_curve(self, n_bins: int = 10) -> dict:
        """
        Curva de calibração - compara probabilidade prevista vs frequência real.

        Modelo perfeito: linha diagonal
        """
        if not self.predictions:
            return {}

        bins = {i: {"count": 0, "correct": 0} for i in range(n_bins)}

        for p in self.predictions:
            bin_idx = min(int(p["prob"] * n_bins), n_bins - 1)
            bins[bin_idx]["count"] += 1
            bins[bin_idx]["correct"] += p["outcome"]

        curve = {}
        for i, data in bins.items():
            if data["count"] > 0:
                expected = (i + 0.5) / n_bins
                actual = data["correct"] / data["count"]
                curve[f"{i/n_bins:.1f}-{(i+1)/n_bins:.1f}"] = {
                    "expected": round(expected, 2),
                    "actual": round(actual, 2),
                    "count": data["count"],
                }

        return curve

    def expected_calibration_error(self, n_bins: int = 10) -> float:
        """
        ECE - Erro de Calibração Esperado.

        Média ponderada da diferença entre probabilidade e frequência real.
        """
        curve = self.calibration_curve(n_bins)
        if not curve:
            return 0

        total_samples = len(self.predictions)
        ece = 0

        for bin_data in curve.values():
            weight = bin_data["count"] / total_samples
            error = abs(bin_data["expected"] - bin_data["actual"])
            ece += weight * error

        return round(ece, 4)

    def get_all_metrics(self) -> CalibrationMetrics:
        """Retorna todas as métricas."""
        return CalibrationMetrics(
            brier_score=self.brier_score(),
            log_loss=self.log_loss(),
            calibration_error=self.expected_calibration_error(),
            hit_rate=sum(self.outcomes) / len(self.outcomes) if self.outcomes else 0,
        )


# ============================================================================
# 5. KELLY CRITERION DINÂMICO
# ============================================================================

class DynamicKelly:
    """
    Kelly Criterion adaptativo baseado em:
    - Confiança do modelo
    - Histórico de performance
    - Volatilidade recente
    """

    def __init__(
        self,
        fraction: float = 0.25,  # Kelly fracionário (25%)
        max_stake: float = 5.0,  # Máximo 5% da banca
        min_edge: float = 0.02,  # Mínimo 2% de edge
    ):
        self.fraction = fraction
        self.max_stake = max_stake
        self.min_edge = min_edge
        self.history: list[dict] = []
        self.bankroll: float = 100.0

    def kelly_stake(self, prob: float, odds: float) -> float:
        """
        Calcula stake ótimo.

        Kelly% = (bp - q) / b
        Onde: b = odds-1, p = prob de ganhar, q = 1-p
        """
        if odds <= 1 or prob <= 0:
            return 0

        b = odds - 1
        p = prob
        q = 1 - p

        edge = (p * odds) - 1
        if edge < self.min_edge:
            return 0

        kelly = (b * p - q) / b
        fractional = kelly * self.fraction

        return min(max(0, fractional), self.max_stake)

    def adjust_for_confidence(self, stake: float, confidence: float) -> float:
        """Ajusta stake baseado na confiança do modelo."""
        # confidence: 0-1
        adjustment = 0.5 + (confidence * 0.5)  # 50-100% do stake
        return stake * adjustment

    def adjust_for_drawdown(self, stake: float) -> float:
        """Reduz stake se em drawdown."""
        if len(self.history) < 5:
            return stake

        recent = self.history[-5:]
        wins = sum(1 for h in recent if h.get("won", False))

        if wins <= 1:  # 1 ou menos de 5 = drawdown
            return stake * 0.5  # Reduz pela metade
        elif wins <= 2:
            return stake * 0.75

        return stake

    def calculate_stake(
        self,
        prob: float,
        odds: float,
        confidence: float = 1.0,
    ) -> dict:
        """Calcula stake final com todos os ajustes."""
        base_stake = self.kelly_stake(prob, odds)
        adjusted = self.adjust_for_confidence(base_stake, confidence)
        final = self.adjust_for_drawdown(adjusted)

        edge = (prob * odds) - 1

        return {
            "stake_percent": round(final, 2),
            "stake_units": round(final * self.bankroll / 100, 2),
            "kelly_raw": round(base_stake, 2),
            "edge": round(edge * 100, 2),
            "ev": round(edge * final, 4),
        }

    def record_bet(self, stake: float, odds: float, won: bool):
        """Registra resultado de aposta."""
        profit = stake * (odds - 1) if won else -stake
        self.bankroll += profit

        self.history.append({
            "stake": stake,
            "odds": odds,
            "won": won,
            "profit": profit,
            "bankroll": self.bankroll,
            "timestamp": datetime.now().isoformat(),
        })

    def get_stats(self) -> dict:
        """Estatísticas de performance."""
        if not self.history:
            return {}

        wins = sum(1 for h in self.history if h["won"])
        total_profit = sum(h["profit"] for h in self.history)
        total_staked = sum(h["stake"] for h in self.history)

        return {
            "total_bets": len(self.history),
            "wins": wins,
            "losses": len(self.history) - wins,
            "hit_rate": round(wins / len(self.history) * 100, 1),
            "total_profit": round(total_profit, 2),
            "roi": round(total_profit / total_staked * 100, 2) if total_staked else 0,
            "current_bankroll": round(self.bankroll, 2),
        }


# ============================================================================
# 6. BACKTESTING FRAMEWORK
# ============================================================================

@dataclass
class BacktestResult:
    """Resultado de backtesting."""
    total_bets: int = 0
    wins: int = 0
    losses: int = 0
    profit: float = 0
    roi: float = 0
    max_drawdown: float = 0
    sharpe_ratio: float = 0
    best_streak: int = 0
    worst_streak: int = 0
    avg_odds: float = 0
    avg_stake: float = 0


class Backtester:
    """
    Framework de backtesting para estratégias de apostas.

    Simula apostas em dados históricos para validar estratégia.
    """

    def __init__(self, initial_bankroll: float = 1000):
        self.initial_bankroll = initial_bankroll
        self.bankroll = initial_bankroll
        self.history: list[dict] = []
        self.peak_bankroll = initial_bankroll

    def run(
        self,
        predictions: list[dict],
        strategy: callable,
    ) -> BacktestResult:
        """
        Executa backtest.

        Args:
            predictions: Lista de {prob, odds, outcome (1/0)}
            strategy: Função que recebe (prob, odds, bankroll) e retorna stake

        Returns:
            BacktestResult com métricas
        """
        self.bankroll = self.initial_bankroll
        self.history = []
        self.peak_bankroll = self.initial_bankroll

        wins = losses = 0
        current_streak = 0
        best_streak = worst_streak = 0
        max_drawdown = 0
        returns = []

        for pred in predictions:
            prob = pred["prob"]
            odds = pred["odds"]
            outcome = pred["outcome"]

            # Calcula stake
            stake = strategy(prob, odds, self.bankroll)
            if stake <= 0:
                continue

            # Resultado
            if outcome == 1:
                profit = stake * (odds - 1)
                wins += 1
                current_streak = max(0, current_streak) + 1
                best_streak = max(best_streak, current_streak)
            else:
                profit = -stake
                losses += 1
                current_streak = min(0, current_streak) - 1
                worst_streak = min(worst_streak, current_streak)

            self.bankroll += profit
            returns.append(profit / stake if stake > 0 else 0)

            # Drawdown
            self.peak_bankroll = max(self.peak_bankroll, self.bankroll)
            drawdown = (self.peak_bankroll - self.bankroll) / self.peak_bankroll
            max_drawdown = max(max_drawdown, drawdown)

            self.history.append({
                "prob": prob,
                "odds": odds,
                "stake": stake,
                "profit": profit,
                "bankroll": self.bankroll,
            })

        # Métricas finais
        total_staked = sum(h["stake"] for h in self.history)
        total_profit = self.bankroll - self.initial_bankroll

        # Sharpe Ratio
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe = (avg_return / std_return * math.sqrt(252)) if std_return > 0 else 0
        else:
            sharpe = 0

        return BacktestResult(
            total_bets=len(self.history),
            wins=wins,
            losses=losses,
            profit=round(total_profit, 2),
            roi=round(total_profit / total_staked * 100, 2) if total_staked else 0,
            max_drawdown=round(max_drawdown * 100, 2),
            sharpe_ratio=round(sharpe, 2),
            best_streak=best_streak,
            worst_streak=abs(worst_streak),
            avg_odds=round(np.mean([h["odds"] for h in self.history]), 2) if self.history else 0,
            avg_stake=round(np.mean([h["stake"] for h in self.history]), 2) if self.history else 0,
        )

    def get_equity_curve(self) -> list[float]:
        """Retorna curva de patrimônio."""
        return [h["bankroll"] for h in self.history]

    def get_monthly_returns(self) -> dict:
        """Retorna retornos mensais."""
        # Simplificado - em produção, usar datas reais
        if not self.history:
            return {}

        chunk_size = 30
        monthly = {}

        for i in range(0, len(self.history), chunk_size):
            chunk = self.history[i:i+chunk_size]
            profit = sum(h["profit"] for h in chunk)
            monthly[f"Month {i//chunk_size + 1}"] = round(profit, 2)

        return monthly


# ============================================================================
# 7. ENSEMBLE CIENTÍFICO
# ============================================================================

class ScientificEnsemble:
    """
    Ensemble que combina múltiplos modelos com pesos otimizados.

    Usa validação cruzada para determinar pesos ideais.
    """

    def __init__(self):
        self.models = {
            "dixon_coles": DixonColesModel(),
            "bradley_terry": BradleyTerryModel(),
            "bayesian": BayesianPredictor(),
        }
        self.weights = {name: 1/len(self.models) for name in self.models}
        self.calibration = ModelCalibration()

    def fit_all(self, matches: list[dict]):
        """Treina todos os modelos."""
        self.models["dixon_coles"].fit(matches)
        self.models["bradley_terry"].fit(matches)

        for m in matches:
            winner = m["home_team"] if m["home_goals"] > m["away_goals"] else m["away_team"]
            loser = m["away_team"] if m["home_goals"] > m["away_goals"] else m["home_team"]
            self.models["bayesian"].update(winner, 1, 0)
            self.models["bayesian"].update(loser, 0, 1)

    def optimize_weights(self, validation_matches: list[dict]):
        """Otimiza pesos usando validation set."""
        best_brier = float("inf")
        best_weights = self.weights.copy()

        # Grid search simples
        for w1 in np.arange(0.1, 0.8, 0.1):
            for w2 in np.arange(0.1, 0.8 - w1, 0.1):
                w3 = 1 - w1 - w2
                if w3 < 0.1:
                    continue

                weights = {
                    "dixon_coles": w1,
                    "bradley_terry": w2,
                    "bayesian": w3,
                }

                # Avalia
                calibration = ModelCalibration()
                for m in validation_matches:
                    pred = self._predict_weighted(m["home_team"], m["away_team"], weights)
                    outcome = 1 if m["home_goals"] > m["away_goals"] else 0
                    calibration.add_prediction(pred["home_win"], outcome)

                brier = calibration.brier_score()
                if brier < best_brier:
                    best_brier = brier
                    best_weights = weights

        self.weights = best_weights
        logger.info(f"Optimized weights: {self.weights} (Brier: {best_brier})")

    def _predict_weighted(self, home: str, away: str, weights: dict) -> dict:
        """Previsão com pesos específicos."""
        home_win = 0

        dc = self.models["dixon_coles"].predict(home, away)
        home_win += dc["home_win"] * weights["dixon_coles"]

        bt = self.models["bradley_terry"].predict(home, away)
        home_win += bt["team_a_win"] * weights["bradley_terry"]

        bayes = self.models["bayesian"].predict_match(home, away)
        home_win += bayes["home_win"] * weights["bayesian"]

        return {"home_win": home_win}

    def predict(self, home: str, away: str) -> dict:
        """Previsão ensemble final."""
        return self._predict_weighted(home, away, self.weights)


# ============================================================================
# CONVENIÊNCIA
# ============================================================================

def create_newton_predictor():
    """Cria predictor completo estilo Newton."""
    return ScientificEnsemble()
