#!/usr/bin/env python3
"""
LOBINHO-BET - Modo 100% Local
==============================
Roda predicoes sem internet usando modelos estatisticos.

Uso:
    python run_local.py              # Analisa todos os jogos
    python run_local.py --top 5      # Mostra top 5 value bets
    python run_local.py --match BR001  # Analisa jogo especifico
    python run_local.py --details    # Mostra detalhes por modelo
"""

import sys
from pathlib import Path

# Adiciona projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.local.predictor import LocalPredictor, Signal
from src.local.sample_data import get_sample_matches


def print_header():
    """Imprime cabecalho."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🐺 LOBINHO-BET - Analise 100% Local                            ║
║                                                                   ║
║   Modelos: Poisson | Dixon-Coles | ELO | Markov | Bradley-Terry  ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")


def print_summary_table(predictions: list):
    """Imprime tabela resumo."""
    print("\n" + "=" * 95)
    print(f"{'JOGO':<35} {'PROB':<20} {'ODDS':<15} {'EDGE':<10} {'SIGNAL':<12}")
    print("=" * 95)

    for p in predictions:
        match_name = f"{p.home_team[:15]} vs {p.away_team[:15]}"

        # Melhor probabilidade
        probs = [(p.home_win, "H"), (p.draw, "D"), (p.away_win, "A")]
        best_prob = max(probs, key=lambda x: x[0])

        prob_str = f"H:{p.home_win:.0%} D:{p.draw:.0%} A:{p.away_win:.0%}"
        odds_str = f"{p.odds.get('home', 0):.2f}/{p.odds.get('draw', 0):.2f}/{p.odds.get('away', 0):.2f}"

        # Signal com emoji
        signal_emoji = {
            Signal.STRONG_BUY: "🔥 STRONG",
            Signal.BUY: "✅ BUY",
            Signal.HOLD: "⏳ HOLD",
            Signal.AVOID: "❌ AVOID",
        }

        edge_str = f"{p.best_edge:+.1f}%" if p.best_value else "---"
        signal_str = signal_emoji.get(p.signal, "---")

        # Cor baseada no signal
        if p.signal == Signal.STRONG_BUY:
            print(f"\033[92m{match_name:<35} {prob_str:<20} {odds_str:<15} {edge_str:<10} {signal_str:<12}\033[0m")
        elif p.signal == Signal.BUY:
            print(f"\033[94m{match_name:<35} {prob_str:<20} {odds_str:<15} {edge_str:<10} {signal_str:<12}\033[0m")
        else:
            print(f"{match_name:<35} {prob_str:<20} {odds_str:<15} {edge_str:<10} {signal_str:<12}")

    print("=" * 95)


def print_value_bets(predictions: list, top_n: int = 5):
    """Imprime melhores value bets."""
    value_bets = [p for p in predictions if p.best_value and p.best_edge >= 3]

    print(f"\n{'='*60}")
    print(f"🎯 TOP {min(top_n, len(value_bets))} VALUE BETS")
    print(f"{'='*60}")

    if not value_bets:
        print("\n❌ Nenhum value bet encontrado com edge >= 3%")
        return

    for i, p in enumerate(value_bets[:top_n], 1):
        print(f"""
#{i} {p.home_team} vs {p.away_team}
   Liga: {p.league}
   Mercado: {p.best_value.upper()}
   Edge: {p.best_edge:.1f}%
   Kelly: {p.kelly_stake:.1f}% da banca
   Signal: {p.signal.value.upper()}
   Odds Mercado: {p.odds.get(p.best_value, 0):.2f}
   Fair Odds: {p.fair_odds.get(p.best_value, 0):.2f}
""")


def print_model_details(prediction):
    """Imprime detalhes de cada modelo."""
    print(f"\n{'='*60}")
    print(f"📊 DETALHES POR MODELO: {prediction.home_team} vs {prediction.away_team}")
    print(f"{'='*60}")

    print(f"\n{'Modelo':<15} {'Casa':<12} {'Empate':<12} {'Fora':<12} {'Peso':<8}")
    print("-" * 60)

    weights = {
        "poisson": 0.25,
        "dixon_coles": 0.30,
        "elo": 0.20,
        "markov": 0.15,
        "bradley_terry": 0.10,
    }

    for model, pred in prediction.model_predictions.items():
        weight = weights.get(model, 0)
        print(f"{model:<15} {pred['home_win']:.1%}{'':>4} {pred['draw']:.1%}{'':>4} {pred['away_win']:.1%}{'':>4} {weight:.0%}")

    print("-" * 60)
    print(f"{'ENSEMBLE':<15} {prediction.home_win:.1%}{'':>4} {prediction.draw:.1%}{'':>4} {prediction.away_win:.1%}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LOBINHO-BET - Analise Local")
    parser.add_argument("--top", type=int, default=5, help="Numero de value bets para mostrar")
    parser.add_argument("--match", type=str, help="ID do jogo especifico")
    parser.add_argument("--details", action="store_true", help="Mostra detalhes por modelo")
    parser.add_argument("--all", action="store_true", help="Mostra todos os jogos detalhados")
    args = parser.parse_args()

    print_header()

    # Inicializa preditor
    predictor = LocalPredictor(min_edge=3.0, kelly_fraction=0.25)

    if args.match:
        # Jogo especifico
        matches = get_sample_matches()
        match = next((m for m in matches if m["id"] == args.match), None)

        if match:
            pred = predictor.predict_match(match)
            print(pred)

            if args.details:
                print_model_details(pred)
        else:
            print(f"❌ Jogo '{args.match}' nao encontrado")
            print("\nJogos disponiveis:")
            for m in matches:
                print(f"  {m['id']}: {m['home_team']} vs {m['away_team']}")

    else:
        # Todos os jogos
        predictions = predictor.predict_all()

        # Tabela resumo
        print_summary_table(predictions)

        # Value bets
        print_value_bets(predictions, args.top)

        # Detalhes completos
        if args.all:
            for pred in predictions:
                print(pred)
                if args.details:
                    print_model_details(pred)

        # Resumo final
        value_count = len([p for p in predictions if p.signal in [Signal.STRONG_BUY, Signal.BUY]])
        print(f"\n📈 RESUMO: {len(predictions)} jogos analisados | {value_count} value bets encontrados")


if __name__ == "__main__":
    main()
