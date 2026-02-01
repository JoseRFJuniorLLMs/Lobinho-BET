"""
Tests for Statistical Models - LOBINHO-BET
===========================================
Unit tests for Markov, Poisson, ELO, Dixon-Coles, and Ensemble.
"""

import pytest
import numpy as np
from datetime import datetime

from src.models.markov_predictor import MarkovPredictor
from src.models.advanced_predictors import PoissonPredictor, EloRating, EnsemblePredictor


class TestMarkovPredictor:
    """Tests for Markov Chain predictor."""

    def test_form_to_states(self):
        """Test form string conversion to states."""
        predictor = MarkovPredictor()
        states = predictor._form_to_states("WDWWL")
        assert states == ["W", "D", "W", "W", "L"]

    def test_transition_matrix_calculation(self):
        """Test transition matrix is valid."""
        predictor = MarkovPredictor()
        form = "WWDLWWDWLW"
        matrix = predictor._calculate_transition_matrix(form)

        # Check rows sum to 1 (with small tolerance)
        for state in matrix:
            row_sum = sum(matrix[state].values())
            assert abs(row_sum - 1.0) < 0.01 or row_sum == 0

    def test_predict_next_state(self):
        """Test prediction returns valid probabilities."""
        predictor = MarkovPredictor()
        form = "WWWDWWWDWW"  # Strong home team form
        probs = predictor._predict_next_state(form)

        assert "W" in probs
        assert "D" in probs
        assert "L" in probs
        assert abs(sum(probs.values()) - 1.0) < 0.01

    def test_strong_form_gives_high_win_prob(self):
        """Strong form should predict high win probability."""
        predictor = MarkovPredictor()
        strong_form = "WWWWW"
        probs = predictor._predict_next_state(strong_form)

        # With perfect form, should have high win probability
        assert probs.get("W", 0) > 0.5

    def test_rank_events(self, sample_events):
        """Test event ranking."""
        predictor = MarkovPredictor()
        ranked = predictor.rank_events(sample_events, max_events=5)

        # Should return RankedEvent objects
        assert len(ranked) > 0
        # Should be sorted by score
        if len(ranked) > 1:
            scores = [e.markov_score for e in ranked]
            assert scores == sorted(scores, reverse=True)


class TestPoissonPredictor:
    """Tests for Poisson distribution predictor."""

    def test_poisson_probability(self):
        """Test Poisson probability calculation."""
        predictor = PoissonPredictor()
        prob = predictor._poisson_prob(1.5, 1)

        # Poisson probability for lambda=1.5, k=1
        expected = np.exp(-1.5) * (1.5 ** 1) / np.math.factorial(1)
        assert abs(prob - expected) < 0.001

    def test_match_prediction_sums_to_one(self):
        """Test that match probabilities sum to ~1."""
        predictor = PoissonPredictor()
        result = predictor.predict_match(
            home_xg=1.5,
            away_xg=1.2,
            home_attack=1.1,
            away_attack=1.0,
            home_defense=0.9,
            away_defense=1.0
        )

        total = result["home_win"] + result["draw"] + result["away_win"]
        assert abs(total - 1.0) < 0.05  # Allow small tolerance

    def test_predict_goals(self):
        """Test expected goals calculation."""
        predictor = PoissonPredictor()
        result = predictor.predict_match(
            home_xg=1.5,
            away_xg=1.2,
            home_attack=1.2,
            away_attack=1.0,
            home_defense=1.0,
            away_defense=1.1
        )

        assert "expected_home_goals" in result
        assert "expected_away_goals" in result
        assert result["expected_home_goals"] > 0
        assert result["expected_away_goals"] > 0


class TestEloRating:
    """Tests for ELO rating system."""

    def test_expected_score(self):
        """Test expected score calculation."""
        elo = EloRating()
        expected = elo._expected_score(1600, 1400)

        # Higher rated team should have > 0.5 expected score
        assert expected > 0.5
        assert expected < 1.0

    def test_rating_update_after_win(self):
        """Test rating increases after win."""
        elo = EloRating()
        new_rating = elo.update_rating(1500, 1500, 1.0)  # Win

        assert new_rating > 1500

    def test_rating_update_after_loss(self):
        """Test rating decreases after loss."""
        elo = EloRating()
        new_rating = elo.update_rating(1500, 1500, 0.0)  # Loss

        assert new_rating < 1500

    def test_predict_match(self):
        """Test match prediction."""
        elo = EloRating()
        result = elo.predict_match(1600, 1400, home_advantage=50)

        assert "home_win" in result
        assert "draw" in result
        assert "away_win" in result
        total = result["home_win"] + result["draw"] + result["away_win"]
        assert abs(total - 1.0) < 0.01


class TestEnsemblePredictor:
    """Tests for ensemble predictions."""

    def test_weighted_average(self):
        """Test weighted average combination."""
        ensemble = EnsemblePredictor()

        predictions = [
            {"home_win": 0.5, "draw": 0.3, "away_win": 0.2},
            {"home_win": 0.4, "draw": 0.35, "away_win": 0.25},
        ]
        weights = [0.6, 0.4]

        result = ensemble._combine_predictions(predictions, weights)

        expected_home = 0.5 * 0.6 + 0.4 * 0.4
        assert abs(result["home_win"] - expected_home) < 0.01

    def test_predictions_sum_to_one(self):
        """Test combined predictions sum to 1."""
        ensemble = EnsemblePredictor()

        predictions = [
            {"home_win": 0.45, "draw": 0.30, "away_win": 0.25},
            {"home_win": 0.50, "draw": 0.28, "away_win": 0.22},
            {"home_win": 0.42, "draw": 0.32, "away_win": 0.26},
        ]

        result = ensemble.predict(predictions)
        total = result["home_win"] + result["draw"] + result["away_win"]
        assert abs(total - 1.0) < 0.02


class TestValueDetection:
    """Tests for value bet detection."""

    def test_edge_calculation(self):
        """Test edge calculation."""
        # Fair probability 50%, odds offering 2.20 (implied 45.45%)
        fair_prob = 0.50
        odds = 2.20
        implied_prob = 1 / odds

        edge = (fair_prob - implied_prob) * 100
        assert edge > 0  # Should be positive edge

    def test_kelly_criterion(self):
        """Test Kelly stake calculation."""
        # Edge = 5%, odds = 2.0
        edge = 0.05
        odds = 2.0

        # Kelly formula: (bp - q) / b
        # where b = odds - 1, p = fair_prob, q = 1 - p
        b = odds - 1
        p = 1 / odds + edge  # fair_prob
        q = 1 - p
        kelly = (b * p - q) / b

        assert kelly > 0
        assert kelly < 0.25  # Should be reasonable stake


class TestProbabilityCalibration:
    """Tests for probability calibration."""

    def test_brier_score(self):
        """Test Brier score calculation."""
        predictions = [0.9, 0.8, 0.7]
        outcomes = [1, 1, 0]

        brier = sum((p - o) ** 2 for p, o in zip(predictions, outcomes)) / len(predictions)

        # Good predictions should have low Brier score
        assert brier < 0.2

    def test_log_loss(self):
        """Test log loss calculation."""
        predictions = [0.9, 0.8, 0.7]
        outcomes = [1, 1, 0]

        eps = 1e-15
        log_loss = -sum(
            o * np.log(max(p, eps)) + (1 - o) * np.log(max(1 - p, eps))
            for p, o in zip(predictions, outcomes)
        ) / len(predictions)

        assert log_loss >= 0
