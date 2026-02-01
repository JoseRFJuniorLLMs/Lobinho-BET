#!/usr/bin/env python3
"""
LOBINHO-BET - Launcher Principal
=================================
Escolhe entre modo ONLINE (APIs) ou OFFLINE (Local).

Uso:
    python run.py                    # Menu interativo
    python run.py --online           # Modo online com APIs
    python run.py --offline          # Modo offline local
    python run.py --dashboard        # Inicia dashboard web
"""

import sys
import os
from pathlib import Path

# Adiciona projeto ao path
sys.path.insert(0, str(Path(__file__).parent))


def print_banner():
    """Imprime banner do projeto."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🐺 LOBINHO-BET                                                  ║
║   Sistema de Analise de Apostas Esportivas                       ║
║                                                                   ║
║   Modelos: Poisson │ Dixon-Coles │ ELO │ Markov │ Ensemble       ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)


def print_menu():
    """Imprime menu de opcoes."""
    print("""
┌─────────────────────────────────────────────────────────────────┐
│                         ESCOLHA O MODO                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   [1] 🌐 MODO ONLINE                                           │
│       → Usa APIs reais (FootyStats, Odds API, Transfermarkt)   │
│       → Dados ao vivo                                          │
│       → Requer internet e chaves de API                        │
│                                                                 │
│   [2] 💻 MODO OFFLINE                                          │
│       → 100% local, sem internet                               │
│       → Dados de exemplo (24 times, 14 jogos)                  │
│       → Perfeito para teste e estudo                           │
│                                                                 │
│   [3] 🖥️  DASHBOARD WEB                                        │
│       → Interface grafica no navegador                         │
│       → Atualizacao em tempo real                              │
│       → http://localhost:8000                                  │
│                                                                 │
│   [4] 📊 ANALISE ESPECIFICA                                    │
│       → Analisa um jogo especifico                             │
│       → Escolhe times manualmente                              │
│                                                                 │
│   [0] ❌ SAIR                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
    """)


def run_online():
    """Executa modo online com APIs."""
    print("\n🌐 MODO ONLINE")
    print("=" * 50)

    # Verifica chaves de API
    from src.core.config import get_settings

    settings = get_settings()

    missing_keys = []
    if not settings.footystats_api_key or settings.footystats_api_key == "your_footystats_api_key_here":
        missing_keys.append("FOOTYSTATS_API_KEY")
    if not settings.odds_api_key or settings.odds_api_key == "your_odds_api_key_here":
        missing_keys.append("ODDS_API_KEY")

    if missing_keys:
        print("\n⚠️  ATENÇÃO: Chaves de API não configuradas:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\nConfigure no arquivo .env")
        print("\nDeseja continuar mesmo assim? (s/n): ", end="")

        resp = input().strip().lower()
        if resp != "s":
            return

    print("\nIniciando coleta de dados...")
    print("(Pressione Ctrl+C para parar)\n")

    try:
        import asyncio
        from src.core.orchestrator import BettingOrchestrator

        async def run():
            async with BettingOrchestrator() as orchestrator:
                await orchestrator.run_full_cycle()

        asyncio.run(run())

    except KeyboardInterrupt:
        print("\n\n⏹️  Parado pelo usuario")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nTente o modo OFFLINE para testar sem APIs")


def run_offline():
    """Executa modo offline local."""
    print("\n💻 MODO OFFLINE")
    print("=" * 50)

    from src.local.predictor import LocalPredictor, Signal
    from src.local.sample_data import get_sample_matches

    predictor = LocalPredictor(min_edge=3.0, kelly_fraction=0.25)
    predictions = predictor.predict_all()

    # Tabela resumo
    print(f"\n{'JOGO':<35} {'PROB':<20} {'EDGE':<10} {'SIGNAL':<12}")
    print("=" * 80)

    for p in predictions:
        match_name = f"{p.home_team[:15]} vs {p.away_team[:15]}"
        prob_str = f"H:{p.home_win:.0%} D:{p.draw:.0%} A:{p.away_win:.0%}"

        signal_emoji = {
            Signal.STRONG_BUY: "🔥 STRONG",
            Signal.BUY: "✅ BUY",
            Signal.HOLD: "⏳ HOLD",
            Signal.AVOID: "❌ AVOID",
        }

        edge_str = f"{p.best_edge:+.1f}%" if p.best_value else "---"
        signal_str = signal_emoji.get(p.signal, "---")

        print(f"{match_name:<35} {prob_str:<20} {edge_str:<10} {signal_str:<12}")

    # Value bets
    value_bets = [p for p in predictions if p.signal in [Signal.STRONG_BUY, Signal.BUY]]

    print(f"\n{'='*60}")
    print(f"🎯 VALUE BETS ENCONTRADOS: {len(value_bets)}")
    print(f"{'='*60}")

    for p in value_bets:
        print(f"""
  {p.home_team} vs {p.away_team}
  Mercado: {p.best_value.upper()} | Edge: {p.best_edge:.1f}% | Kelly: {p.kelly_stake:.1f}%
  Odds: {p.odds.get(p.best_value, 0):.2f} (Fair: {p.fair_odds.get(p.best_value, 0):.2f})
""")

    print(f"\n📈 Total: {len(predictions)} jogos analisados")


def run_dashboard():
    """Inicia dashboard web."""
    print("\n🖥️  DASHBOARD WEB")
    print("=" * 50)
    print("\nIniciando servidor...")
    print("Acesse: http://localhost:8000")
    print("(Pressione Ctrl+C para parar)\n")

    try:
        import uvicorn
        uvicorn.run(
            "src.api.dashboard:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n⏹️  Dashboard parado")
    except Exception as e:
        print(f"\n❌ Erro: {e}")


def run_specific_analysis():
    """Analisa jogo especifico."""
    print("\n📊 ANALISE ESPECIFICA")
    print("=" * 50)

    from src.local.sample_data import TEAMS

    print("\nTimes disponiveis:")
    teams = list(TEAMS.keys())
    for i, team in enumerate(teams, 1):
        print(f"  [{i:2d}] {TEAMS[team]['name']}")

    print("\nEscolha o time da CASA (numero): ", end="")
    try:
        home_idx = int(input().strip()) - 1
        home_team = teams[home_idx]
    except (ValueError, IndexError):
        print("❌ Opcao invalida")
        return

    print("Escolha o time de FORA (numero): ", end="")
    try:
        away_idx = int(input().strip()) - 1
        away_team = teams[away_idx]
    except (ValueError, IndexError):
        print("❌ Opcao invalida")
        return

    if home_team == away_team:
        print("❌ Times devem ser diferentes")
        return

    # Analisa
    from src.local.predictor import LocalPredictor
    from datetime import datetime, timedelta

    match = {
        "id": "CUSTOM",
        "home_team": home_team,
        "away_team": away_team,
        "league": "Custom Analysis",
        "kickoff": datetime.now() + timedelta(hours=2),
    }

    predictor = LocalPredictor()
    prediction = predictor.predict_match(match)

    print(prediction)

    # Detalhes por modelo
    print(f"\n{'Modelo':<15} {'Casa':<12} {'Empate':<12} {'Fora':<12}")
    print("-" * 55)

    for model, pred in prediction.model_predictions.items():
        print(f"{model:<15} {pred['home_win']:.1%}{'':>4} {pred['draw']:.1%}{'':>4} {pred['away_win']:.1%}")

    print("-" * 55)
    print(f"{'ENSEMBLE':<15} {prediction.home_win:.1%}{'':>4} {prediction.draw:.1%}{'':>4} {prediction.away_win:.1%}")


def main():
    """Funcao principal."""
    import argparse

    parser = argparse.ArgumentParser(description="LOBINHO-BET Launcher")
    parser.add_argument("--online", action="store_true", help="Modo online com APIs")
    parser.add_argument("--offline", action="store_true", help="Modo offline local")
    parser.add_argument("--dashboard", action="store_true", help="Inicia dashboard web")
    args = parser.parse_args()

    print_banner()

    # Modo direto via argumento
    if args.online:
        run_online()
        return
    elif args.offline:
        run_offline()
        return
    elif args.dashboard:
        run_dashboard()
        return

    # Menu interativo
    while True:
        print_menu()
        print("Escolha uma opcao: ", end="")

        try:
            choice = input().strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Ate logo!")
            break

        if choice == "1":
            run_online()
        elif choice == "2":
            run_offline()
        elif choice == "3":
            run_dashboard()
        elif choice == "4":
            run_specific_analysis()
        elif choice == "0":
            print("\n👋 Ate logo!")
            break
        else:
            print("\n❌ Opcao invalida")

        print("\n" + "-" * 50)
        print("Pressione ENTER para voltar ao menu...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
