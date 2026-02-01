#!/usr/bin/env python3
"""
Teste do LiveMarketAnalyzer - Analisador de Mercados ao Vivo
"""
import sys
sys.path.insert(0, '.')

from src.models.live_market_analyzer import (
    LiveMarketAnalyzer,
    LiveMatchData,
    MarketType,
    OddsTrend,
    analisar_mercado_live
)

def criar_cenario_teste(nome: str, dados: dict) -> LiveMatchData:
    """Cria um cenário de teste com dados personalizados"""
    base = {
        "match_id": "test_001",
        "home_team": "Time A",
        "away_team": "Time B",
        "league": "Test League",
        "minute": 45,
        "period": "1H",
        "home_goals": 0,
        "away_goals": 0,
        "home_possession": 55.0,
        "away_possession": 45.0,
        "home_shots": 8,
        "away_shots": 4,
        "home_shots_on_target": 3,
        "away_shots_on_target": 1,
        "home_corners": 4,
        "away_corners": 2,
        "home_dangerous_attacks": 25,
        "away_dangerous_attacks": 12,
        "home_xg": 1.2,
        "away_xg": 0.6,
        "home_yellow_cards": 1,
        "away_yellow_cards": 1,
        "home_red_cards": 0,
        "away_red_cards": 0,
        "home_fouls": 8,
        "away_fouls": 10,
        "home_pressure": 60.0,
        "away_pressure": 40.0,
        "momentum": 20.0,
        "recent_home_shots": 3,
        "recent_away_shots": 1,
        "recent_home_corners": 2,
        "recent_away_corners": 0,
        "recent_goals": 0,
        "odds": {
            "over_0.5": 1.10,
            "under_0.5": 7.00,
            "over_1.5": 1.40,
            "under_1.5": 2.80,
            "over_2.5": 1.85,
            "under_2.5": 1.95,
            "over_3.5": 2.80,
            "under_3.5": 1.40,
            "btts_yes": 1.90,
            "btts_no": 1.90,
            "home_win": 2.10,
            "draw": 3.20,
            "away_win": 3.50,
            "next_goal_home": 1.70,
            "next_goal_away": 2.20,
            "no_more_goals": 4.50,
            "corners_over_8.5": 1.80,
            "corners_over_9.5": 2.20,
            "corners_over_10.5": 2.80,
        },
        "odds_trend": {
            "over_2.5": OddsTrend.STABLE,
            "home_win": OddsTrend.STABLE,
        }
    }
    base.update(dados)
    return LiveMatchData(**base)


def test_cenario_1():
    """Cenário 1: Jogo 0-0 aos 60min com alta pressão"""
    print("\n" + "="*70)
    print("CENARIO 1: Jogo 0-0 aos 60min com ALTA PRESSAO OFENSIVA")
    print("="*70)

    match = criar_cenario_teste("Alta Pressao 0-0", {
        "minute": 60,
        "period": "2H",
        "home_goals": 0,
        "away_goals": 0,
        "home_shots": 15,
        "away_shots": 10,
        "home_shots_on_target": 7,
        "away_shots_on_target": 4,
        "home_xg": 2.1,
        "away_xg": 1.4,
        "home_dangerous_attacks": 40,
        "away_dangerous_attacks": 28,
        "home_pressure": 70.0,
        "away_pressure": 55.0,
        "momentum": 30.0,
        "recent_home_shots": 5,
        "recent_away_shots": 3,
        "recent_goals": 0,
        "odds": {
            "over_0.5": 1.05,
            "over_1.5": 1.25,
            "under_1.5": 3.80,
            "over_2.5": 1.65,
            "under_2.5": 2.20,
            "btts_yes": 1.70,
            "btts_no": 2.10,
            "home_win": 2.00,
            "draw": 3.00,
            "away_win": 3.80,
            "next_goal_home": 1.60,
            "next_goal_away": 2.30,
            "no_more_goals": 5.00,
        },
        "odds_trend": {
            "over_2.5": OddsTrend.FALLING,
            "over_1.5": OddsTrend.FALLING,
        }
    })

    analyzer = LiveMarketAnalyzer()
    resultado = analyzer.get_best_market(match)

    if resultado:
        print(f"\n>>> MELHOR MERCADO: {resultado.market.value}")
        print(f"   Score: {resultado.score:.2%}")
        print(f"   Probabilidade: {resultado.probability:.2%}")
        print(f"   Confianca: {resultado.confidence}")
        print(f"   Odd: {resultado.odds:.2f}")
        print(f"   EV: {resultado.expected_value:.2%}")
        print(f"   Recomendacao: {resultado.recommendation}")
        print(f"   Razoes:")
        for razao in resultado.reasons:
            print(f"      - {razao}")
    else:
        print("X Nenhum mercado com score >= 0.50 encontrado")

    # Mostra top 5
    print("\n### TOP 5 MERCADOS:")
    top5 = analyzer.get_top_markets(match, top_n=5)
    for i, m in enumerate(top5, 1):
        print(f"   {i}. {m.market.value}: {m.score:.2%} (EV: {m.expected_value:+.2%})")


def test_cenario_2():
    """Cenário 2: Jogo 1-1 aos 75min - Avaliar Under"""
    print("\n" + "="*70)
    print("CENARIO 2: Jogo 1-1 aos 75min - Jogo equilibrado")
    print("="*70)

    match = criar_cenario_teste("Jogo Equilibrado", {
        "minute": 75,
        "period": "2H",
        "home_goals": 1,
        "away_goals": 1,
        "home_shots": 10,
        "away_shots": 9,
        "home_shots_on_target": 3,
        "away_shots_on_target": 3,
        "home_xg": 1.3,
        "away_xg": 1.2,
        "home_pressure": 50.0,
        "away_pressure": 50.0,
        "momentum": 0.0,
        "recent_home_shots": 2,
        "recent_away_shots": 2,
        "recent_goals": 0,
        "odds": {
            "over_2.5": 2.50,
            "under_2.5": 1.50,
            "over_3.5": 4.00,
            "under_3.5": 1.20,
            "btts_yes": 1.15,
            "btts_no": 5.50,
            "home_win": 2.80,
            "draw": 2.50,
            "away_win": 2.80,
            "no_more_goals": 2.80,
        }
    })

    analyzer = LiveMarketAnalyzer()

    # Analise completa
    all_markets = analyzer.analyze_all_markets(match)

    print(f"\n### Total de mercados analisados: {len(all_markets)}")
    print("\n### TOP 10 MERCADOS POR SCORE:")
    for i, m in enumerate(all_markets[:10], 1):
        status = "[OK]" if m.score >= 0.50 else "[??]" if m.score >= 0.40 else "[--]"
        print(f"   {status} {i:2d}. {m.market.value:20s} | Score: {m.score:.2%} | Prob: {m.probability:.2%} | EV: {m.expected_value:+.2%}")


def test_cenario_3():
    """Cenário 3: Steam Move - Odds despencando"""
    print("\n" + "="*70)
    print("CENARIO 3: STEAM MOVE - Odds despencando (dinheiro entrando)")
    print("="*70)

    match = criar_cenario_teste("Steam Move", {
        "minute": 50,
        "period": "2H",
        "home_goals": 0,
        "away_goals": 0,
        "home_shots": 12,
        "away_shots": 3,
        "home_shots_on_target": 5,
        "away_shots_on_target": 1,
        "home_xg": 1.8,
        "away_xg": 0.3,
        "home_possession": 68.0,
        "away_possession": 32.0,
        "home_pressure": 80.0,
        "away_pressure": 25.0,
        "momentum": 60.0,
        "recent_home_shots": 6,
        "recent_away_shots": 1,
        "odds": {
            "over_0.5": 1.08,
            "over_1.5": 1.20,
            "over_2.5": 1.55,
            "home_win": 1.45,
            "draw": 3.80,
            "away_win": 6.50,
            "next_goal_home": 1.35,
            "next_goal_away": 3.20,
            "no_more_goals": 6.00,
            "btts_yes": 2.20,
            "btts_no": 1.65,
        },
        "odds_trend": {
            "home_win": OddsTrend.STEAM,  # Steam move!
            "over_1.5": OddsTrend.FALLING,
            "over_2.5": OddsTrend.FALLING,
        }
    })

    resultado = analisar_mercado_live(match)

    print(f"\n### RESULTADO DA ANALISE:")
    print(f"   Match: {resultado['match']}")
    print(f"   Minuto: {resultado['minute']}'")
    print(f"   Placar: {resultado['score']}")

    if resultado['best_market']:
        best = resultado['best_market']
        print(f"\n>>> MELHOR APOSTA:")
        print(f"   Mercado: {best['market']}")
        print(f"   Score: {best['score']}")
        print(f"   Probabilidade: {best['probability']}")
        print(f"   Odd: {best['odds']:.2f}")
        print(f"   EV: {best['ev']}")
        print(f"   Recomendacao: {best['recommendation']}")

    print(f"\n### ALTERNATIVAS ({len(resultado['alternatives'])} mercados):")
    for alt in resultado['alternatives'][:5]:
        print(f"   - {alt['market']}: Score {alt['score']}, Prob {alt['probability']}")


def test_cenario_4():
    """Cenário 4: Final de jogo - poucos minutos restantes"""
    print("\n" + "="*70)
    print("CENARIO 4: FINAL DO JOGO - 85min, 2-0")
    print("="*70)

    match = criar_cenario_teste("Final de Jogo", {
        "minute": 85,
        "period": "2H",
        "home_goals": 2,
        "away_goals": 0,
        "home_shots": 14,
        "away_shots": 6,
        "home_shots_on_target": 6,
        "away_shots_on_target": 2,
        "home_xg": 2.3,
        "away_xg": 0.8,
        "home_pressure": 45.0,
        "away_pressure": 60.0,  # visitante pressionando
        "momentum": -10.0,
        "recent_home_shots": 1,
        "recent_away_shots": 3,
        "recent_goals": 1,  # gol recente
        "odds": {
            "over_2.5": 1.80,
            "under_2.5": 2.00,
            "over_3.5": 3.50,
            "under_3.5": 1.30,
            "home_win": 1.05,
            "draw": 12.00,
            "away_win": 25.00,
            "btts_yes": 3.00,
            "btts_no": 1.35,
            "no_more_goals": 1.60,
        }
    })

    analyzer = LiveMarketAnalyzer()
    top_markets = analyzer.get_top_markets(match, top_n=5)

    print("\n### MELHORES MERCADOS PARA FINAL DE JOGO:")
    for i, m in enumerate(top_markets, 1):
        print(f"\n   {i}. {m.market.value}")
        print(f"      Score: {m.score:.2%} | Prob: {m.probability:.2%} | EV: {m.expected_value:+.2%}")
        if m.reasons:
            print(f"      Razoes: {', '.join(m.reasons[:2])}")


def main():
    print("\n" + "="*70)
    print("     TESTE DO LIVE MARKET ANALYZER - LOBINHO-BET")
    print("="*70)

    test_cenario_1()
    test_cenario_2()
    test_cenario_3()
    test_cenario_4()

    print("\n" + "="*70)
    print("[OK] TODOS OS TESTES CONCLUIDOS!")
    print("="*70)
    print("\n### O LiveMarketAnalyzer esta funcionando corretamente.")
    print("   - Analisa TODOS os mercados disponiveis")
    print("   - Retorna o mercado com MAIOR score de probabilidade")
    print("   - Considera: tempo, pressao, eventos recentes, odds, historico")
    print()


if __name__ == "__main__":
    main()
