"""
Run Analysis Script - LOBINHO-BET
==================================
Manual analysis of specific matches or teams.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from src.processors.team_analysis import TeamAnalyzer, get_pre_match_analysis
from src.models.markov_predictor import MarkovPredictor
from src.models.advanced_predictors import EnsemblePredictor, PoissonPredictor, EloRating
from src.models.newton_stats import ScientificEnsemble


async def analyze_match(home_team: str, away_team: str):
    """
    Run full analysis on a match.
    """
    logger.info(f"Analyzing: {home_team} vs {away_team}")
    print("=" * 60)
    print(f"MATCH ANALYSIS: {home_team} vs {away_team}")
    print("=" * 60)

    # 1. Pre-match analysis (investments, squad, injuries)
    print("\n📊 PRE-MATCH ANALYSIS")
    print("-" * 40)

    pre_analysis = await get_pre_match_analysis(home_team, away_team)

    home_summary = pre_analysis["pre_analysis"]["home"]
    away_summary = pre_analysis["pre_analysis"]["away"]

    print(f"\n{home_team}:")
    print(f"  Squad Value: €{home_summary['squad_value_millions']}M")
    print(f"  Avg Age: {home_summary['avg_age']} years")
    print(f"  Net Spend: €{home_summary['transfers']['net']}M")
    print(f"  Injuries: {home_summary['injuries']['count']} players")

    print(f"\n{away_team}:")
    print(f"  Squad Value: €{away_summary['squad_value_millions']}M")
    print(f"  Avg Age: {away_summary['avg_age']} years")
    print(f"  Net Spend: €{away_summary['transfers']['net']}M")
    print(f"  Injuries: {away_summary['injuries']['count']} players")

    print(f"\n{pre_analysis['recommendation']}")

    # 2. Statistical predictions
    print("\n📈 STATISTICAL PREDICTIONS")
    print("-" * 40)

    # Sample form data (in production, would come from database)
    home_form = "WDWWL"
    away_form = "WWDLW"
    home_xg = 1.5
    away_xg = 1.3

    # Markov prediction
    markov = MarkovPredictor()
    markov_pred = markov._predict_next_state(home_form)
    print(f"\nMarkov (Home Form): W={markov_pred['W']:.1%}, D={markov_pred['D']:.1%}, L={markov_pred['L']:.1%}")

    # Poisson prediction
    poisson = PoissonPredictor()
    poisson_pred = poisson.predict_match(
        home_xg=home_xg,
        away_xg=away_xg,
        home_attack=1.1,
        away_attack=1.0,
        home_defense=1.0,
        away_defense=1.05
    )
    print(f"Poisson: H={poisson_pred['home_win']:.1%}, D={poisson_pred['draw']:.1%}, A={poisson_pred['away_win']:.1%}")
    print(f"  Expected Goals: {poisson_pred['expected_home_goals']:.2f} - {poisson_pred['expected_away_goals']:.2f}")

    # ELO prediction
    elo = EloRating()
    elo_pred = elo.predict_match(
        home_elo=1600,
        away_elo=1550,
        home_advantage=50
    )
    print(f"ELO: H={elo_pred['home_win']:.1%}, D={elo_pred['draw']:.1%}, A={elo_pred['away_win']:.1%}")

    # Ensemble
    ensemble = EnsemblePredictor()
    predictions = [
        {"home_win": markov_pred["W"], "draw": markov_pred["D"], "away_win": markov_pred["L"]},
        poisson_pred,
        elo_pred,
    ]
    final_pred = ensemble.predict(predictions)
    print(f"\n🎯 ENSEMBLE: H={final_pred['home_win']:.1%}, D={final_pred['draw']:.1%}, A={final_pred['away_win']:.1%}")

    # 3. Value bet check
    print("\n💰 VALUE BET ANALYSIS")
    print("-" * 40)

    # Sample odds
    odds = {"home": 2.10, "draw": 3.40, "away": 3.20}

    print(f"Market Odds: H={odds['home']}, D={odds['draw']}, A={odds['away']}")

    for market, prob in [("home", final_pred["home_win"]), ("draw", final_pred["draw"]), ("away", final_pred["away_win"])]:
        fair_odds = 1 / prob if prob > 0 else float("inf")
        market_odds = odds[market]
        edge = ((market_odds / fair_odds) - 1) * 100

        if edge > 5:
            print(f"  ✅ {market.upper()}: Edge={edge:.1f}% (Fair Odds={fair_odds:.2f})")
        else:
            print(f"  ❌ {market.upper()}: Edge={edge:.1f}% (not profitable)")

    print("\n" + "=" * 60)


async def main():
    """Run analysis on sample matches."""
    matches = [
        ("Flamengo", "Palmeiras"),
        ("Manchester City", "Liverpool"),
        ("Real Madrid", "Barcelona"),
    ]

    for home, away in matches:
        await analyze_match(home, away)
        print("\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run match analysis")
    parser.add_argument("--home", type=str, help="Home team name")
    parser.add_argument("--away", type=str, help="Away team name")
    args = parser.parse_args()

    if args.home and args.away:
        asyncio.run(analyze_match(args.home, args.away))
    else:
        asyncio.run(main())
