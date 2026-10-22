# app/bot/bot_manager.py
"""
Bot Manager and Signal Broadcaster.
"""
from __future__ import annotations

import logging

from app.bot.bale_bot import BaleBotClient
from app.bot.telegram_bot import TelegramBotClient
from app.config import get_settings

logger = logging.getLogger("algotrade.bot.manager")


class BotManager:
    """Coordinates message broadcasts across Telegram and Bale bots."""

    def __init__(self) -> None:
        settings = get_settings()
        self.telegram_bots: dict[str, TelegramBotClient] = {}
        self.bale_bots: dict[str, BaleBotClient] = {}

        # Initialize default bots from settings if configured
        if settings.telegram_bot_token.get_secret_value():
            self.telegram_bots["default"] = TelegramBotClient(
                token=settings.telegram_bot_token.get_secret_value(),
                chat_ids=settings.telegram_chat_ids,
            )

        if settings.bale_bot_token.get_secret_value():
            self.bale_bots["default"] = BaleBotClient(
                token=settings.bale_bot_token.get_secret_value(),
                chat_ids=settings.bale_chat_ids,
            )

    def register_telegram_bot(self, bot_id: str, token: str, chat_ids: list[str] | None = None) -> None:
        self.telegram_bots[bot_id] = TelegramBotClient(token, chat_ids)

    def register_bale_bot(self, bot_id: str, token: str, chat_ids: list[str] | None = None) -> None:
        self.bale_bots[bot_id] = BaleBotClient(token, chat_ids)

    async def broadcast_trade_signal(
        self,
        symbol: str,
        direction: str,
        score: int,
        entry_price: float,
        stop_loss: float,
        take_profit_1: float,
        take_profit_2: float,
        reason: str,
    ) -> None:
        """Broadcast new 8-criteria qualified trade signal to all bots."""
        text = (
            f"🎯 **سیگنال ورود جدید AlgoTrade**\n\n"
            f"🔹 نماد: **{symbol}**\n"
            f"🔹 جهت: **{direction}** (امتیاز: {score}/8)\n"
            f"🔹 قیمت ورود: **${entry_price:,.2f}**\n"
            f"🔹 حد ضرر (SL): **${stop_loss:,.2f}**\n"
            f"🔹 تارگت اول (1.5R): **${take_profit_1:,.2f}**\n"
            f"🔹 تارگت دوم (2.5R): **${take_profit_2:,.2f}**\n\n"
            f"📝 دلیل ستاپ: {reason}\n"
            f"🛡️ مدیریت سرمایه: ۱٪ ریسک کل"
        )

        for bot in self.telegram_bots.values():
            await bot.send_message(text)

        bale_text = text.replace("**", "")  # Clean plain text for Bale
        for bot in self.bale_bots.values():
            await bot.send_message(bale_text)

    async def broadcast_kill_switch_alert(self) -> None:
        """Broadcast emergency kill switch activation."""
        msg = "🚨 **هشدار اضطراری KILL-SWITCH**\nکلیه سفارشات باز لغو و سیستم تریدینگ متوقف شد."
        for bot in self.telegram_bots.values():
            await bot.send_message(msg)
        for bot in self.bale_bots.values():
            await bot.send_message(msg.replace("**", ""))


# Global Bot Manager Singleton
global_bot_manager = BotManager()


def get_bot_manager() -> BotManager:
    return global_bot_manager
