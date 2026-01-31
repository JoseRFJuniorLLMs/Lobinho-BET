"""
Markov Chain Predictor
======================
Usa Cadeia de Markov para calcular probabilidades mais precisas
baseado no histórico de resultados dos times.

Estados:
- W (Win) - Vitória
- D (Draw) - Empate
- L (Loss) - Derrota

A matriz de transição modela a probabilidade de mudar de um estado para outro.
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class MarkovPrediction:
    """Previsão baseada em Markov."""
    home_win: float
    draw: float
    away_win: float
    confidence: float  # 0-100
    steady_state_home: list[float]  # Estado estacionário do time da casa
    steady_state_away: list[float]  # Estado estacionário do visitante
    prediction_strength: str  # strong, moderate, weak


class MarkovPredictor:
    """
    Preditor usando Cadeias de Markov.

    Modela a probabilidade de resultados baseado em:
    1. Histórico de forma do time (últimos N jogos)
    2. Matriz de transição entre estados (W→W, W→D, W→L, etc)
    3. Estado estacionário (tendência de longo prazo)

    Quanto mais consistente o time, maior a confiança.
    """

    # Estados
    STATES = ['W', 'D', 'L']  # Win, Draw, Loss
    STATE_INDEX = {'W': 0, 'D': 1, 'L': 2}

    def __init__(self, lookback: int = 10):
        """
        Args:
            lookback: Número de jogos para considerar no histórico
        """
        self.lookback = lookback

    def build_transition_matrix(self, results: list[str]) -> np.ndarray:
        """
        Constrói matriz de transição a partir do histórico.

        Args:
            results: Lista de resultados ['W', 'D', 'L', 'W', ...]

        Returns:
            Matriz 3x3 de probabilidades de transição
        """
        # Inicializa contadores
        transitions = np.zeros((3, 3))

        # Conta transições
        for i in range(len(results) - 1):
            from_state = self.STATE_INDEX.get(results[i], 0)
            to_state = self.STATE_INDEX.get(results[i + 1], 0)
            transitions[from_state][to_state] += 1

        # Normaliza para probabilidades
        row_sums = transitions.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Evita divisão por zero

        transition_matrix = transitions / row_sums

        # Se linha toda for zero, usa distribuição uniforme
        for i in range(3):
            if transitions[i].sum() == 0:
                transition_matrix[i] = [1/3, 1/3, 1/3]

        return transition_matrix

    def calculate_steady_state(self, transition_matrix: np.ndarray) -> np.ndarray:
        """
        Calcula o estado estacionário da cadeia de Markov.

        O estado estacionário representa a distribuição de longo prazo,
        ou seja, a tendência natural do time.

        Returns:
            Vetor [P(W), P(D), P(L)] no estado estacionário
        """
        # Método: encontrar autovetor com autovalor 1
        eigenvalues, eigenvectors = np.linalg.eig(transition_matrix.T)

        # Encontra índice do autovalor ~1
        idx = np.argmin(np.abs(eigenvalues - 1))

        # Pega autovetor correspondente
        steady_state = np.real(eigenvectors[:, idx])

        # Normaliza para somar 1
        steady_state = steady_state / steady_state.sum()

        # Garante valores não-negativos
        steady_state = np.maximum(steady_state, 0)
        steady_state = steady_state / steady_state.sum()

        return steady_state

    def predict_next_state(
        self,
        current_state: str,
        transition_matrix: np.ndarray,
    ) -> np.ndarray:
        """
        Prevê probabilidade do próximo estado.

        Args:
            current_state: Estado atual ('W', 'D', ou 'L')
            transition_matrix: Matriz de transição

        Returns:
            Vetor [P(W), P(D), P(L)] para próximo jogo
        """
        state_idx = self.STATE_INDEX.get(current_state, 0)
        return transition_matrix[state_idx]

    def predict_match(
        self,
        home_results: list[str],
        away_results: list[str],
        home_vs_away_h2h: Optional[list[str]] = None,
    ) -> MarkovPrediction:
        """
        Prevê resultado de uma partida.

        Args:
            home_results: Histórico do time da casa ['W', 'L', 'W', 'D', ...]
            away_results: Histórico do visitante
            home_vs_away_h2h: Histórico de confrontos diretos (perspectiva home)

        Returns:
            MarkovPrediction com probabilidades
        """
        # Limita ao lookback
        home_results = home_results[-self.lookback:] if home_results else ['D']
        away_results = away_results[-self.lookback:] if away_results else ['D']

        # Constrói matrizes de transição
        home_matrix = self.build_transition_matrix(home_results)
        away_matrix = self.build_transition_matrix(away_results)

        # Calcula estados estacionários
        home_steady = self.calculate_steady_state(home_matrix)
        away_steady = self.calculate_steady_state(away_matrix)

        # Prevê próximo estado baseado no último resultado
        home_current = home_results[-1] if home_results else 'D'
        away_current = away_results[-1] if away_results else 'D'

        home_next = self.predict_next_state(home_current, home_matrix)
        away_next = self.predict_next_state(away_current, away_matrix)

        # Combina previsões (média ponderada)
        # Peso maior para estado estacionário (mais estável)
        home_combined = home_steady * 0.6 + home_next * 0.4
        away_combined = away_steady * 0.6 + away_next * 0.4

        # Calcula probabilidades do jogo
        # Home Win: home ganha E away perde
        # Draw: ambos empatam OU forças se anulam
        # Away Win: away ganha E home perde

        # Probabilidade de vitória do mandante
        home_win_prob = (
            home_combined[0] * away_combined[2] * 0.5 +  # Home W, Away L
            home_combined[0] * away_combined[1] * 0.3 +  # Home W, Away D
            home_combined[0] * 0.2                        # Home W qualquer
        )

        # Probabilidade de empate
        draw_prob = (
            home_combined[1] * away_combined[1] * 0.4 +  # Ambos D
            (1 - abs(home_combined[0] - away_combined[0])) * 0.3 +  # Forças equilibradas
            home_combined[1] * 0.15 +
            away_combined[1] * 0.15
        )

        # Probabilidade de vitória visitante
        away_win_prob = (
            away_combined[0] * home_combined[2] * 0.5 +  # Away W, Home L (invertido)
            away_combined[0] * home_combined[1] * 0.3 +
            away_combined[0] * 0.2
        )

        # Incorpora H2H se disponível
        if home_vs_away_h2h and len(home_vs_away_h2h) >= 3:
            h2h_matrix = self.build_transition_matrix(home_vs_away_h2h)
            h2h_steady = self.calculate_steady_state(h2h_matrix)

            # Ajusta com peso do H2H
            h2h_weight = 0.25
            home_win_prob = home_win_prob * (1 - h2h_weight) + h2h_steady[0] * h2h_weight
            draw_prob = draw_prob * (1 - h2h_weight) + h2h_steady[1] * h2h_weight
            away_win_prob = away_win_prob * (1 - h2h_weight) + h2h_steady[2] * h2h_weight

        # Normaliza
        total = home_win_prob + draw_prob + away_win_prob
        if total > 0:
            home_win_prob /= total
            draw_prob /= total
            away_win_prob /= total
        else:
            home_win_prob, draw_prob, away_win_prob = 0.4, 0.3, 0.3

        # Adiciona fator casa (vantagem do mandante)
        home_advantage = 0.08
        home_win_prob += home_advantage
        away_win_prob -= home_advantage * 0.5
        draw_prob -= home_advantage * 0.5

        # Normaliza novamente
        total = home_win_prob + draw_prob + away_win_prob
        home_win_prob /= total
        draw_prob /= total
        away_win_prob /= total

        # Calcula confiança baseada na consistência
        home_consistency = 1 - np.std(home_combined)
        away_consistency = 1 - np.std(away_combined)
        data_quality = min(len(home_results), len(away_results)) / self.lookback

        confidence = (home_consistency + away_consistency) / 2 * 50 + data_quality * 50

        # Determina força da previsão
        max_prob = max(home_win_prob, draw_prob, away_win_prob)
        if max_prob > 0.55:
            strength = "strong"
        elif max_prob > 0.45:
            strength = "moderate"
        else:
            strength = "weak"

        return MarkovPrediction(
            home_win=round(home_win_prob, 4),
            draw=round(draw_prob, 4),
            away_win=round(away_win_prob, 4),
            confidence=round(confidence, 1),
            steady_state_home=home_steady.tolist(),
            steady_state_away=away_steady.tolist(),
            prediction_strength=strength,
        )

    def rank_events(
        self,
        events: list[dict],
        max_events: int = 10,
    ) -> list[dict]:
        """
        Rankeia eventos baseado na precisão das probabilidades Markov.

        Eventos com:
        1. Maior confiança (dados consistentes)
        2. Maior probabilidade máxima (previsão clara)
        3. Histórico mais longo

        Ficam no topo da lista.
        """
        ranked = []

        for event in events:
            # Extrai histórico
            home_results = event.get("home_form", [])
            away_results = event.get("away_form", [])
            h2h = event.get("h2h_results", [])

            # Converte formato se necessário (ex: "WDLWW" -> ['W','D','L','W','W'])
            if isinstance(home_results, str):
                home_results = list(home_results.upper())
            if isinstance(away_results, str):
                away_results = list(away_results.upper())
            if isinstance(h2h, str):
                h2h = list(h2h.upper())

            # Prevê
            prediction = self.predict_match(home_results, away_results, h2h)

            # Calcula score de ranking
            max_prob = max(prediction.home_win, prediction.draw, prediction.away_win)
            data_length = min(len(home_results), len(away_results))

            rank_score = (
                prediction.confidence * 0.4 +
                max_prob * 100 * 0.35 +
                min(data_length / 10, 1) * 25 * 0.25
            )

            ranked.append({
                **event,
                "markov_prediction": {
                    "home_win": prediction.home_win,
                    "draw": prediction.draw,
                    "away_win": prediction.away_win,
                    "confidence": prediction.confidence,
                    "strength": prediction.prediction_strength,
                },
                "rank_score": round(rank_score, 2),
            })

        # Ordena por rank_score
        ranked.sort(key=lambda x: x.get("rank_score", 0), reverse=True)

        return ranked[:max_events]


# Funções de conveniência
def get_markov_rankings(events: list[dict], top_n: int = 10) -> list[dict]:
    """Retorna top N eventos rankeados por Markov."""
    predictor = MarkovPredictor(lookback=10)
    return predictor.rank_events(events, max_events=top_n)


def predict_match_markov(
    home_form: str,
    away_form: str,
    h2h: str = "",
) -> dict:
    """
    Previsão rápida de um jogo.

    Args:
        home_form: Forma do mandante (ex: "WDWLW")
        away_form: Forma do visitante (ex: "LLWDW")
        h2h: Histórico H2H (ex: "WDWLD")

    Returns:
        Dict com probabilidades
    """
    predictor = MarkovPredictor()

    prediction = predictor.predict_match(
        list(home_form.upper()),
        list(away_form.upper()),
        list(h2h.upper()) if h2h else None,
    )

    return {
        "home_win": f"{prediction.home_win * 100:.1f}%",
        "draw": f"{prediction.draw * 100:.1f}%",
        "away_win": f"{prediction.away_win * 100:.1f}%",
        "confidence": f"{prediction.confidence:.1f}%",
        "strength": prediction.prediction_strength,
    }
