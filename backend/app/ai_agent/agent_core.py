# app/ai_agent/agent_core.py
"""
AI Trading Copilot & Agent Core Engine.

Supports conversational trade reasoning, strategy queries, market outlook,
and integrates with external LLMs (Gemini, etc.) with built-in analytical
fallbacks.  Model name and API key are read from Settings — never hardcoded.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from app.ai_agent.llm_client import LLMClient
from app.ai_agent.market_analyst import MarketAnalyst
from app.ai_agent.personas import AGENT_PERSONAS
from app.config import get_settings

logger = logging.getLogger("algotrade.ai_agent")


class AIAgentCore:
    """Core AI Trading Assistant Copilot."""

    PERSONAS = AGENT_PERSONAS

    def __init__(self) -> None:
        settings = get_settings()
        api_key = settings.gemini_api_key.get_secret_value()
        self.llm = LLMClient(
            api_key=api_key,
            model_name=settings.gemini_model_name,
            timeout_seconds=settings.ai_request_timeout_seconds,
        )
        self.analyst = MarketAnalyst()

    # ── Trade Setup Verification ─────────────────────────

    async def verify_trade_setup(
        self,
        symbol: str,
        setup_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Verify a trade setup using AI analysis with rule-based fallback.

        Args:
            symbol: Trading pair (e.g. "BTCUSDT").
            setup_data: Dict containing score, current_price, direction,
                        has_bos, has_fvg, stop_loss, take_profit, rr, etc.

        Returns:
            Dict with approved, confidence, sentiment, reasoning.
        """
        int(setup_data.get("score", 0))

        if not self.llm.is_configured:
            logger.info(
                "AI verification fallback (no API key) for %s", symbol,
            )
            return self._rule_based_verification(symbol, setup_data)

        prompt = self._build_verification_prompt(symbol, setup_data)
        system_prompt = (
            "You are a senior algorithmic trading risk analyst. "
            "Evaluate the proposed trade setup and respond ONLY with "
            "a valid JSON object containing exactly these keys: "
            '"approved" (boolean), "confidence" (integer 0-100), '
            '"sentiment" (string: BULLISH/BEARISH/NEUTRAL), '
            '"reasoning" (string: concise 1-2 sentence justification).'
        )

        result = await self.llm.generate_json(prompt, system_prompt)

        if result and isinstance(result.get("approved"), bool):
            return {
                "approved": result["approved"],
                "confidence": int(result.get("confidence", 50)),
                "sentiment": str(result.get("sentiment", "NEUTRAL")),
                "reasoning": str(result.get("reasoning", "")),
                "source": "ai",
                "model": self.llm.model_name,
            }

        logger.warning(
            "AI verification returned invalid result for %s, "
            "falling back to rule-based",
            symbol,
        )
        return self._rule_based_verification(symbol, setup_data)

    # ── Conversational Chat ──────────────────────────────

    async def chat(
        self,
        user_message: str,
        persona: str = "smc_master",
        active_symbol: str = "BTCUSDT",
        market_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Process user message and return AI analytical response."""
        now = datetime.now(UTC).strftime("%H:%M UTC")
        ctx = market_context or {}
        price = ctx.get("current_price", 0.0)
        score = ctx.get("score", 0)
        msg_lower = user_message.lower()

        # 1. Symbol analysis request
        if self._is_analysis_request(user_message, msg_lower):
            return self._handle_analysis(
                active_symbol, price, score, persona, now,
            )

        # 2. Risk management question
        if self._is_risk_question(user_message, msg_lower):
            return self._handle_risk_question(persona, now)

        # 3. AI-powered chat (if configured)
        if self.llm.is_configured:
            return await self._handle_ai_chat(
                user_message, persona, active_symbol, ctx, now,
            )

        # 4. Default static response (fallback)
        return self._handle_default_response(
            active_symbol, price, score, persona, now,
        )

    # ── Status Info ──────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        """Return current AI agent configuration status."""
        return {
            "llm_configured": self.llm.is_configured,
            "model_name": self.llm.model_name,
            "personas": list(self.PERSONAS.keys()),
            "persona_count": len(self.PERSONAS),
        }

    # ── Private: Verification Helpers ────────────────────

    @staticmethod
    def _build_verification_prompt(
        symbol: str, setup_data: dict[str, Any],
    ) -> str:
        """Build a structured prompt for trade verification."""
        lines = [
            f"Evaluate this {symbol} trade setup:",
            f"- Score: {setup_data.get('score', 0)}/8",
            f"- Direction: {setup_data.get('direction', 'UNKNOWN')}",
            f"- Current Price: {setup_data.get('current_price', 0)}",
            f"- BOS Confirmed: {setup_data.get('has_bos', False)}",
            f"- FVG Mitigated: {setup_data.get('has_fvg', False)}",
            f"- Stop Loss: {setup_data.get('stop_loss', 0)}",
            f"- Take Profit 1: {setup_data.get('take_profit_1', 0)}",
            f"- Risk/Reward: {setup_data.get('rr', 0)}",
            f"- RSI: {setup_data.get('rsi', 50)}",
            f"- Volume Confirmed: {setup_data.get('volume_confirmed', False)}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _rule_based_verification(
        symbol: str, setup_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Deterministic rule-based fallback for trade verification."""
        score = int(setup_data.get("score", 0))
        rr = float(setup_data.get("rr", 0))
        has_bos = bool(setup_data.get("has_bos", False))

        approved = score >= 7 and rr >= 1.5
        confidence = min(100, score * 12 + (10 if has_bos else 0))

        if score >= 7:
            sentiment = "BULLISH"
            reasoning = (
                f"Rule-based: Score {score}/8 meets threshold. "
                f"RR={rr:.1f}."
            )
        elif score >= 5:
            sentiment = "NEUTRAL"
            reasoning = (
                f"Rule-based: Score {score}/8 below threshold (7). "
                "Awaiting more confirmations."
            )
        else:
            sentiment = "BEARISH"
            reasoning = (
                f"Rule-based: Score {score}/8 insufficient. "
                "Setup rejected."
            )

        return {
            "approved": approved,
            "confidence": confidence,
            "sentiment": sentiment,
            "reasoning": reasoning,
            "source": "rule_based",
            "model": "none",
        }

    # ── Private: Chat Helpers ────────────────────────────

    @staticmethod
    def _is_analysis_request(msg: str, msg_lower: str) -> bool:
        keywords = ("تحلیل", "چارت", "وضعیت", "analyze", "analysis")
        return any(k in msg or k in msg_lower for k in keywords)

    @staticmethod
    def _is_risk_question(msg: str, msg_lower: str) -> bool:
        keywords = ("ریسک", "سرمایه", "risk", "capital", "drawdown")
        return any(k in msg or k in msg_lower for k in keywords)

    def _handle_analysis(
        self,
        symbol: str,
        price: float,
        score: int,
        persona: str,
        now: str,
    ) -> dict[str, Any]:
        """Generate analytical briefing for a symbol."""
        brief = self.analyst.generate_symbol_briefing(
            symbol=symbol,
            current_price=price,
            timeframe="1h",
            score=score,
            criteria_details={},
        )
        return {
            "reply": brief["summary_text"],
            "persona": persona,
            "timestamp": now,
            "has_trade_action": brief["is_ready_to_enter"],
            "trade_data": {
                "symbol": symbol,
                "entry_price": price,
                "stop_loss": brief["stop_loss"],
                "take_profit_1": brief["take_profit_1"],
                "take_profit_2": brief["take_profit_2"],
                "risk_reward": 1.5,
            },
        }

    @staticmethod
    def _handle_risk_question(persona: str, now: str) -> dict[str, Any]:
        """Return static risk management guidelines."""
        reply = (
            "🛡️ **راهنمای مدیریت ریسک AlgoTrade:**\n\n"
            "• **سقف ریسک هر معامله:** حداکثر ۱٪ از کل ارزش سبد.\n"
            "• **حداقل نسبت ریوارد به ریسک:** 1:1.50 به بالا.\n"
            "• **سقف پوزیشن همزمان:** حداکثر ۴ معامله و ۱۲٪ سرمایه.\n"
            "• **کلید قطع خودکار:** افت ۸٪ → کاهش ۵۰٪ حجم؛ "
            "افت ۱۲٪ → توقف کامل ورود.\n"
            "• **ترلینگ‌استاپ:** RR ۱.۵ → Risk-Free؛ "
            "RR ۲.۵ → ۵۰٪ سیو سود."
        )
        return {
            "reply": reply,
            "persona": persona,
            "timestamp": now,
            "has_trade_action": False,
        }

    async def _handle_ai_chat(
        self,
        user_message: str,
        persona: str,
        symbol: str,
        ctx: dict[str, Any],
        now: str,
    ) -> dict[str, Any]:
        """Route message to LLM with persona context."""
        persona_info = self.PERSONAS.get(persona, self.PERSONAS["smc_master"])
        system_prompt = (
            f"{persona_info['prompt_prefix']}\n\n"
            f"نماد فعال: {symbol}\n"
            f"قیمت فعلی: {ctx.get('current_price', 'نامشخص')}\n"
            f"امتیاز سیستم: {ctx.get('score', 'نامشخص')}/8\n\n"
            "به فارسی و با لحن حرفه‌ای پاسخ بده. "
            "از ایموجی مناسب استفاده کن."
        )

        response_text = await self.llm.generate(
            prompt=user_message,
            system_prompt=system_prompt,
        )

        if response_text:
            return {
                "reply": response_text,
                "persona": persona,
                "timestamp": now,
                "has_trade_action": False,
                "source": "ai",
                "model": self.llm.model_name,
            }

        # Fallback if AI call failed
        price = ctx.get("current_price", 0.0)
        score = ctx.get("score", 0)
        return self._handle_default_response(
            symbol, price, score, persona, now,
        )

    @staticmethod
    def _handle_default_response(
        symbol: str,
        price: float,
        score: int,
        persona: str,
        now: str,
    ) -> dict[str, Any]:
        """Static fallback response when AI is unavailable."""
        price_str = f"${price:,.2f}" if price else "نامشخص"
        reply = (
            f"سلام! من دستیار هوش مصنوعی AlgoTrade هستم.\n\n"
            f"نماد فعال: **{symbol}** (قیمت: {price_str})\n"
            f"امتیاز پرایس‌اکشن: **{score} از ۸**\n\n"
            f"می‌توانید درباره وضعیت بازار، تحلیل تکنیکال، "
            f"شرایط ورود، یا استراتژی‌های ۸ معیاره بپرسید."
        )
        return {
            "reply": reply,
            "persona": persona,
            "timestamp": now,
            "has_trade_action": False,
            "source": "fallback",
        }


# Global AI Agent Singleton (lazy init)
_global_ai_agent: AIAgentCore | None = None


def get_ai_agent() -> AIAgentCore:
    """Return cached AIAgentCore singleton."""
    global _global_ai_agent
    if _global_ai_agent is None:
        _global_ai_agent = AIAgentCore()
    return _global_ai_agent
