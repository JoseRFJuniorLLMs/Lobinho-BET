"""
LOBINHO-BET - Main Entry Point
==============================

Sistema automático de análise de apostas esportivas.

Uso:
    python main.py              # Executa sistema completo
    python main.py --bot        # Apenas bot Telegram
    python main.py --analyze    # Apenas análise (sem live tracking)
    python main.py --live       # Apenas tracking ao vivo
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_settings
from src.core.orchestrator import LobinhoOrchestrator
from src.core.live_tracker import LiveTracker, format_live_dashboard
from src.notifier.telegram_bot import TelegramNotifier, send_telegram_message
from src.models.value_detector import ValueBet


# ============================================================================
# CONFIGURAÇÃO DE LOGS
# ============================================================================

def setup_logging():
    """Configura sistema de logs."""
    logger.remove()

    # Console
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO",
    )

    # Arquivo
    logger.add(
        "logs/lobinho_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
    )


# ============================================================================
# CALLBACKS
# ============================================================================

async def on_value_bet_found(bet: ValueBet):
    """Callback quando value bet é encontrado."""
    logger.info(f"💰 Value bet: {bet.home_team} vs {bet.away_team} | {bet.selection} @ {bet.odds}")

    # Envia para Telegram
    message = bet.to_telegram_message()
    await send_telegram_message(message)


async def on_live_alert(alert: dict):
    """Callback para alertas de jogos ao vivo."""
    logger.info(f"🔴 Live alert: {alert}")

    message = f"""
🔴 *ALERTA AO VIVO*

⚽ {alert.get('match', 'N/A')}
⏱ {alert.get('minute', 0)}'
📊 {alert.get('score', '0-0')}

💡 {alert.get('suggestion', 'N/A')}
"""
    await send_telegram_message(message)


async def on_goal(match, team: str):
    """Callback quando há gol."""
    team_name = match.home_team if team == "home" else match.away_team

    message = f"""
⚽ *GOOOL!*

{match.home_team} *{match.home_goals}* x *{match.away_goals}* {match.away_team}

🎯 Gol de: {team_name}
⏱ Minuto: {match.minute}'
"""
    await send_telegram_message(message)


async def on_momentum_shift(match, direction: str, change: float):
    """Callback quando há mudança de momentum."""
    dominant = match.home_team if direction == "home" else match.away_team

    message = f"""
📈 *MUDANÇA DE MOMENTUM*

{match.home_team} vs {match.away_team}
⏱ {match.minute}'

🔥 {dominant} está dominando!
📊 Mudança: {change:.1f} pontos

Considere apostar em: *{dominant}* ou Over
"""
    await send_telegram_message(message)


# ============================================================================
# MODOS DE EXECUÇÃO
# ============================================================================

async def run_full_system():
    """Executa sistema completo."""
    logger.info("🚀 Starting LOBINHO-BET Full System...")

    orchestrator = LobinhoOrchestrator(
        on_value_bet=on_value_bet_found,
        on_live_alert=on_live_alert,
    )

    try:
        await orchestrator.start()

        # Mantém rodando
        while True:
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
    finally:
        await orchestrator.stop()


async def run_telegram_bot():
    """Executa apenas o bot do Telegram."""
    logger.info("🤖 Starting Telegram Bot...")

    notifier = TelegramNotifier()
    notifier.setup_commands()

    # Envia mensagem de início
    await notifier.send_message("🤖 *LOBINHO-BET* iniciado!\n\nDigite /help para comandos.")

    await notifier.start_polling()


async def run_analysis_only():
    """Executa apenas análise (sem monitoramento live)."""
    logger.info("🔬 Running analysis only...")

    orchestrator = LobinhoOrchestrator(on_value_bet=on_value_bet_found)

    # Coleta e analisa
    await orchestrator.collect_daily_matches()
    value_bets = await orchestrator.run_pre_match_analysis()

    # Mostra resultados
    print("\n" + "=" * 60)
    print("📊 ANÁLISE COMPLETA")
    print("=" * 60)
    print(f"\n✅ Jogos analisados: {len(orchestrator.today_matches)}")
    print(f"💰 Value bets encontrados: {len(value_bets)}")

    if value_bets:
        print("\n🎯 TOP VALUE BETS:")
        for i, bet in enumerate(value_bets[:10], 1):
            print(f"\n{i}. {bet.home_team} vs {bet.away_team}")
            print(f"   Seleção: {bet.selection} @ {bet.odds}")
            print(f"   Edge: {bet.edge:.2f}% | Kelly: {bet.kelly_stake:.2f}%")
            print(f"   Confiança: {bet.confidence}")


async def run_live_tracking():
    """Executa apenas tracking de jogos ao vivo."""
    logger.info("🔴 Starting live tracking...")

    # Primeiro coleta jogos do dia
    from src.collectors import FootyStatsCollector
    from src.strategy.leagues import LeagueManager
    from datetime import date

    league_manager = LeagueManager()
    today = date.today()
    live_matches = []

    async with FootyStatsCollector() as collector:
        for league in league_manager.get_enabled_leagues():
            if league.footystats_id:
                matches = await collector.get_matches(
                    league_id=league.footystats_id,
                    date_from=today,
                    date_to=today,
                    status="live",
                )
                live_matches.extend(matches)

    if not live_matches:
        print("Nenhum jogo ao vivo no momento.")
        return

    # Inicia tracking
    tracker = LiveTracker(
        update_interval=30,
        on_goal=on_goal,
        on_momentum_shift=on_momentum_shift,
    )

    try:
        # Mostra dashboard a cada 30 segundos
        async def show_dashboard():
            while True:
                print("\033[H\033[J")  # Limpa tela
                print(format_live_dashboard(tracker))
                await asyncio.sleep(30)

        await asyncio.gather(
            tracker.start_tracking(live_matches),
            show_dashboard(),
        )

    except KeyboardInterrupt:
        await tracker.stop_tracking()


async def show_status():
    """Mostra status do sistema."""
    settings = get_settings()

    print("\n" + "=" * 60)
    print("🐺 LOBINHO-BET - Status")
    print("=" * 60)

    print("\n📌 Configuração:")
    print(f"   • FootyStats API: {'✅' if settings.footystats_api_key else '❌'}")
    print(f"   • Odds API: {'✅' if settings.odds_api_key else '❌'}")
    print(f"   • Telegram: {'✅' if settings.telegram_bot_token else '❌'}")
    print(f"   • Claude AI: {'✅' if settings.anthropic_api_key else '❌'}")

    print("\n📊 Campeonatos ativos:")
    from src.strategy.leagues import LeagueManager
    manager = LeagueManager()
    for league in manager.get_high_priority():
        print(f"   🔥 {league.name}")
    for league in manager.get_by_priority(manager.leagues["brasileirao_b"].priority):
        print(f"   ⭐ {league.name}")

    print("\n💡 Uso:")
    print("   python main.py              # Sistema completo")
    print("   python main.py --bot        # Apenas Telegram")
    print("   python main.py --analyze    # Apenas análise")
    print("   python main.py --live       # Tracking ao vivo")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Entry point principal."""
    parser = argparse.ArgumentParser(description="LOBINHO-BET - Sistema de Análise de Apostas")
    parser.add_argument("--bot", action="store_true", help="Executa apenas bot Telegram")
    parser.add_argument("--analyze", action="store_true", help="Executa apenas análise")
    parser.add_argument("--live", action="store_true", help="Executa apenas tracking ao vivo")
    parser.add_argument("--status", action="store_true", help="Mostra status do sistema")

    args = parser.parse_args()

    # Setup logs
    setup_logging()

    # Banner
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🐺 LOBINHO-BET                                          ║
    ║   Sistema Automático de Análise de Apostas                ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    # Executa modo apropriado
    if args.status:
        asyncio.run(show_status())
    elif args.bot:
        asyncio.run(run_telegram_bot())
    elif args.analyze:
        asyncio.run(run_analysis_only())
    elif args.live:
        asyncio.run(run_live_tracking())
    else:
        asyncio.run(run_full_system())


if __name__ == "__main__":
    main()
