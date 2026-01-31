"""
Telegram Bot Notifier
=====================
Envia alertas de value bets via Telegram.
"""

import asyncio
from typing import Optional
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from loguru import logger

from config import get_settings


class TelegramNotifier:
    """Gerencia notificações via Telegram."""

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        settings = get_settings()
        self.token = token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id
        self.bot: Optional[Bot] = None
        self.app: Optional[Application] = None

        if self.token:
            self.bot = Bot(token=self.token)

    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "Markdown",
    ) -> bool:
        """Envia mensagem para o chat."""
        if not self.bot:
            logger.warning("Telegram bot not configured")
            return False

        target_chat = chat_id or self.chat_id
        if not target_chat:
            logger.warning("No chat_id configured")
            return False

        try:
            await self.bot.send_message(
                chat_id=target_chat,
                text=text,
                parse_mode=parse_mode,
            )
            logger.debug(f"Message sent to {target_chat}")
            return True

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def send_value_bet_alert(self, bet) -> bool:
        """Envia alerta de value bet formatado."""
        message = bet.to_telegram_message()
        return await self.send_message(message)

    async def send_live_alert(
        self,
        match: str,
        minute: int,
        score: str,
        suggestion: str,
        confidence: str,
    ) -> bool:
        """Envia alerta de jogo ao vivo."""
        emoji = "🔥" if confidence == "high" else "⚡" if confidence == "medium" else "📊"

        message = f"""
{emoji} *ALERTA AO VIVO*

⚽ *{match}*
⏱ Minuto: {minute}'
📊 Placar: {score}

💡 *Sugestão:* {suggestion}
🎯 Confiança: {confidence.upper()}
"""
        return await self.send_message(message)

    async def send_daily_summary(self, report: dict) -> bool:
        """Envia resumo diário."""
        message = f"""
📊 *RESUMO DO DIA - {report.get('date', 'N/A')}*

📈 Jogos analisados: {report.get('total_matches_analyzed', 0)}
🎯 Value bets encontrados: {report.get('value_bets_found', 0)}

*Por confiança:*
🔥 Alta: {report.get('bets_by_confidence', {}).get('high', 0)}
✅ Média: {report.get('bets_by_confidence', {}).get('medium', 0)}
📊 Baixa: {report.get('bets_by_confidence', {}).get('low', 0)}

*Top 5 apostas do dia:*
"""
        for i, bet in enumerate(report.get('top_bets', [])[:5], 1):
            message += f"\n{i}. {bet.get('match', 'N/A')} - {bet.get('selection', 'N/A')} @ {bet.get('odds', 0)}"
            message += f"\n   Edge: {bet.get('edge', 'N/A')} | Kelly: {bet.get('kelly_stake', 'N/A')}"

        return await self.send_message(message)

    # =========================================================================
    # BOT COMMANDS
    # =========================================================================

    def setup_commands(self):
        """Configura comandos do bot."""
        if not self.token:
            return

        self.app = Application.builder().token(self.token).build()

        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("bets", self._cmd_today_bets))
        self.app.add_handler(CommandHandler("live", self._cmd_live_matches))
        self.app.add_handler(CommandHandler("leagues", self._cmd_leagues))
        self.app.add_handler(CommandHandler("help", self._cmd_help))

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start."""
        message = """
🐺 *LOBINHO-BET* - Bot de Análise de Apostas

Bem-vindo! Este bot analisa jogos de futebol e detecta value bets automaticamente.

*Comandos disponíveis:*
/status - Status do sistema
/bets - Value bets do dia
/live - Jogos ao vivo
/leagues - Campeonatos monitorados
/help - Ajuda

Configure suas notificações e receba alertas automáticos!
"""
        await update.message.reply_text(message, parse_mode="Markdown")

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status."""
        # Aqui você pode integrar com o orchestrator para status real
        message = """
✅ *Status do Sistema*

🟢 Coleta de dados: Ativo
🟢 Análise ML: Ativo
🟢 Monitoramento live: Ativo
🟢 Notificações: Ativo

📊 Última atualização: Agora
"""
        await update.message.reply_text(message, parse_mode="Markdown")

    async def _cmd_today_bets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /bets."""
        message = """
🎯 *Value Bets de Hoje*

Aguarde... Buscando apostas...

_Use /live para ver jogos ao vivo_
"""
        await update.message.reply_text(message, parse_mode="Markdown")

    async def _cmd_live_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /live."""
        message = """
🔴 *Jogos Ao Vivo*

Nenhum jogo ao vivo no momento.

_Você receberá alertas automáticos durante jogos!_
"""
        await update.message.reply_text(message, parse_mode="Markdown")

    async def _cmd_leagues(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /leagues."""
        from src.strategy.leagues import LeagueManager

        manager = LeagueManager()
        leagues = manager.get_enabled_leagues()

        message = "🏆 *Campeonatos Monitorados*\n\n"

        for league in leagues:
            priority_emoji = "🔥" if league.priority.value == 1 else "⭐" if league.priority.value == 2 else "📊"
            message += f"{priority_emoji} {league.name} ({league.country})\n"

        await update.message.reply_text(message, parse_mode="Markdown")

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help."""
        message = """
📚 *Ajuda - LOBINHO-BET*

*Comandos:*
/start - Iniciar bot
/status - Status do sistema
/bets - Value bets do dia
/live - Jogos ao vivo
/leagues - Campeonatos

*Como funciona:*
1. O sistema coleta dados de jogos
2. Analisa usando Machine Learning
3. Compara probabilidades vs odds
4. Detecta value bets (edge positivo)
5. Envia alertas automáticos

*Entendendo os alertas:*
🔥 Alta confiança (edge > 10%)
✅ Média confiança (edge 5-10%)
📊 Baixa confiança (edge < 5%)

*Gestão de banca:*
O sistema sugere stakes usando Kelly Criterion fracionário (1/4).
Nunca aposte mais do que o sugerido!
"""
        await update.message.reply_text(message, parse_mode="Markdown")

    async def start_polling(self):
        """Inicia o bot em modo polling."""
        if not self.app:
            self.setup_commands()

        if self.app:
            await self.app.run_polling()


# Funções de conveniência
_notifier: Optional[TelegramNotifier] = None


def get_notifier() -> TelegramNotifier:
    """Retorna instância singleton do notifier."""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier


async def send_telegram_message(text: str) -> bool:
    """Envia mensagem pelo Telegram."""
    notifier = get_notifier()
    return await notifier.send_message(text)


async def send_value_bet(bet) -> bool:
    """Envia alerta de value bet."""
    notifier = get_notifier()
    return await notifier.send_value_bet_alert(bet)
