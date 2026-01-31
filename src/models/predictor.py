"""
Match Prediction Model
======================
Machine Learning model to predict match outcomes.
"""

import pickle
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier
from loguru import logger


class MatchPredictor:
    """
    Predicts match outcomes using ensemble ML models.

    Features used:
    - Team form (last 5 matches)
    - Head-to-head record
    - Home/Away performance
    - Goals scored/conceded averages
    - xG / xGA metrics
    - League position
    - Rest days between matches
    """

    OUTCOMES = {0: "away_win", 1: "draw", 2: "home_win"}

    def __init__(self, model_path: Optional[Path] = None):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_path = model_path or Path("data/models/predictor.pkl")

        if self.model_path.exists():
            self.load_model()

    def create_features(self, match_data: dict) -> np.ndarray:
        """
        Create feature vector from match data.

        Expected keys in match_data:
        - home_form, away_form (last 5 games points)
        - home_goals_avg, away_goals_avg
        - home_conceded_avg, away_conceded_avg
        - home_xg, away_xg
        - home_xga, away_xga
        - home_position, away_position
        - h2h_home_wins, h2h_draws, h2h_away_wins
        - home_rest_days, away_rest_days
        """
        features = [
            # Form
            match_data.get("home_form", 0),
            match_data.get("away_form", 0),
            match_data.get("home_form", 0) - match_data.get("away_form", 0),

            # Goals
            match_data.get("home_goals_avg", 0),
            match_data.get("away_goals_avg", 0),
            match_data.get("home_conceded_avg", 0),
            match_data.get("away_conceded_avg", 0),

            # xG metrics
            match_data.get("home_xg", 0),
            match_data.get("away_xg", 0),
            match_data.get("home_xga", 0),
            match_data.get("away_xga", 0),
            match_data.get("home_xg", 0) - match_data.get("home_xga", 0),  # xG diff home
            match_data.get("away_xg", 0) - match_data.get("away_xga", 0),  # xG diff away

            # League position
            match_data.get("home_position", 10),
            match_data.get("away_position", 10),
            match_data.get("away_position", 10) - match_data.get("home_position", 10),

            # H2H
            match_data.get("h2h_home_wins", 0),
            match_data.get("h2h_draws", 0),
            match_data.get("h2h_away_wins", 0),

            # Rest days
            match_data.get("home_rest_days", 7),
            match_data.get("away_rest_days", 7),
        ]

        return np.array(features).reshape(1, -1)

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_type: str = "xgboost",
    ) -> dict:
        """
        Train the prediction model.

        Args:
            X: Feature DataFrame
            y: Target series (0=away, 1=draw, 2=home)
            model_type: 'xgboost', 'random_forest', or 'gradient_boosting'

        Returns:
            Training metrics
        """
        self.feature_names = X.columns.tolist()

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Select model
        if model_type == "xgboost":
            self.model = XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                objective="multi:softprob",
                num_class=3,
                random_state=42,
                use_label_encoder=False,
                eval_metric="mlogloss",
            )
        elif model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                random_state=42,
            )
        else:
            self.model = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=6,
                random_state=42,
            )

        # Train
        logger.info(f"Training {model_type} model...")
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)

        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)

        metrics = {
            "accuracy": accuracy,
            "cv_mean": cv_scores.mean(),
            "cv_std": cv_scores.std(),
            "report": classification_report(y_test, y_pred, output_dict=True),
        }

        logger.info(f"Model accuracy: {accuracy:.3f}")
        logger.info(f"CV Score: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

        return metrics

    def predict(self, match_data: dict) -> dict:
        """
        Predict match outcome.

        Returns:
            dict with probabilities for each outcome
        """
        if self.model is None:
            raise RuntimeError("Model not trained. Call train() first.")

        features = self.create_features(match_data)
        features_scaled = self.scaler.transform(features)

        # Get probabilities
        probabilities = self.model.predict_proba(features_scaled)[0]

        prediction = {
            "away_win": round(probabilities[0], 4),
            "draw": round(probabilities[1], 4),
            "home_win": round(probabilities[2], 4),
            "predicted_outcome": self.OUTCOMES[np.argmax(probabilities)],
            "confidence": round(max(probabilities), 4),
        }

        return prediction

    def predict_batch(self, matches: list[dict]) -> list[dict]:
        """Predict outcomes for multiple matches."""
        return [self.predict(match) for match in matches]

    def save_model(self, path: Optional[Path] = None):
        """Save model to disk."""
        save_path = path or self.model_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
            }, f)

        logger.info(f"Model saved to {save_path}")

    def load_model(self, path: Optional[Path] = None):
        """Load model from disk."""
        load_path = path or self.model_path

        with open(load_path, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.scaler = data["scaler"]
            self.feature_names = data["feature_names"]

        logger.info(f"Model loaded from {load_path}")

    def get_feature_importance(self) -> dict:
        """Get feature importance from trained model."""
        if not hasattr(self.model, "feature_importances_"):
            return {}

        importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_,
        ))

        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
