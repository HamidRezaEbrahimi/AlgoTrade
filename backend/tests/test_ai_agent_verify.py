# tests/test_ai_agent_verify.py
"""Tests for AI Agent trade setup verification and fallback behavior."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.ai_agent.agent_core import AIAgentCore


class TestRuleBasedVerification:
    """Test deterministic rule-based fallback verification."""

    def test_score_7_approved(self) -> None:
        result = AIAgentCore._rule_based_verification(
            "BTCUSDT",
            {"score": 7, "rr": 1.8, "has_bos": True},
        )
        assert result["approved"] is True
        assert result["source"] == "rule_based"
        assert result["sentiment"] == "BULLISH"

    def test_score_8_approved(self) -> None:
        result = AIAgentCore._rule_based_verification(
            "ETHUSDT",
            {"score": 8, "rr": 2.0, "has_bos": True},
        )
        assert result["approved"] is True
        assert result["confidence"] > 90

    def test_score_6_rejected(self) -> None:
        result = AIAgentCore._rule_based_verification(
            "BTCUSDT",
            {"score": 6, "rr": 1.6, "has_bos": False},
        )
        # score < 7 → NOT approved
        assert result["approved"] is False
        assert result["sentiment"] in ("NEUTRAL", "BEARISH")

    def test_score_3_rejected_bearish(self) -> None:
        result = AIAgentCore._rule_based_verification(
            "BTCUSDT",
            {"score": 3, "rr": 0.5, "has_bos": False},
        )
        assert result["approved"] is False
        assert result["sentiment"] == "BEARISH"

    def test_high_score_low_rr_rejected(self) -> None:
        result = AIAgentCore._rule_based_verification(
            "BTCUSDT",
            {"score": 7, "rr": 1.2, "has_bos": True},
        )
        # score >= 7 but rr < 1.5 → NOT approved
        assert result["approved"] is False


class TestVerifyTradeSetup:
    """Test verify_trade_setup with mocked LLM."""

    @pytest.mark.asyncio
    async def test_verify_without_api_key_uses_fallback(self) -> None:
        """When no API key, should use rule-based fallback."""
        agent = AIAgentCore.__new__(AIAgentCore)
        from app.ai_agent.llm_client import LLMClient
        agent.llm = LLMClient(api_key="", model_name="test")
        agent.analyst = None  # type: ignore

        result = await agent.verify_trade_setup(
            "BTCUSDT",
            {"score": 7, "rr": 2.0, "has_bos": True},
        )
        assert result["approved"] is True
        assert result["source"] == "rule_based"

    @pytest.mark.asyncio
    async def test_verify_with_ai_success(self) -> None:
        """When AI returns valid JSON, use AI result."""
        agent = AIAgentCore.__new__(AIAgentCore)
        from app.ai_agent.llm_client import LLMClient
        agent.llm = LLMClient(api_key="fake-key", model_name="test-model")
        agent.analyst = None  # type: ignore

        mock_result = {
            "approved": True,
            "confidence": 88,
            "sentiment": "BULLISH",
            "reasoning": "Strong BOS with FVG mitigation.",
        }

        with patch.object(
            agent.llm, "generate_json", new_callable=AsyncMock,
        ) as mock_gen:
            mock_gen.return_value = mock_result
            result = await agent.verify_trade_setup(
                "BTCUSDT",
                {"score": 7, "rr": 2.0},
            )

        assert result["approved"] is True
        assert result["confidence"] == 88
        assert result["source"] == "ai"
        assert result["model"] == "test-model"

    @pytest.mark.asyncio
    async def test_verify_ai_failure_falls_back(self) -> None:
        """When AI returns None/invalid, fall back to rule-based."""
        agent = AIAgentCore.__new__(AIAgentCore)
        from app.ai_agent.llm_client import LLMClient
        agent.llm = LLMClient(api_key="fake-key", model_name="test-model")
        agent.analyst = None  # type: ignore

        with patch.object(
            agent.llm, "generate_json", new_callable=AsyncMock,
        ) as mock_gen:
            mock_gen.return_value = None  # AI failed
            result = await agent.verify_trade_setup(
                "BTCUSDT",
                {"score": 8, "rr": 1.8, "has_bos": True},
            )

        assert result["source"] == "rule_based"
        assert result["approved"] is True


class TestAgentStatus:
    """Test get_status method."""

    def test_status_without_key(self) -> None:
        agent = AIAgentCore.__new__(AIAgentCore)
        from app.ai_agent.llm_client import LLMClient
        agent.llm = LLMClient(api_key="", model_name="test-model")
        agent.analyst = None  # type: ignore

        status = agent.get_status()
        assert status["llm_configured"] is False
        assert status["model_name"] == "test-model"
        assert len(status["personas"]) == 3

    def test_status_with_key(self) -> None:
        agent = AIAgentCore.__new__(AIAgentCore)
        from app.ai_agent.llm_client import LLMClient
        agent.llm = LLMClient(api_key="real-key", model_name="gemini-pro")
        agent.analyst = None  # type: ignore

        status = agent.get_status()
        assert status["llm_configured"] is True
        assert status["model_name"] == "gemini-pro"


class TestVerificationPrompt:
    """Test prompt construction."""

    def test_build_prompt_includes_all_fields(self) -> None:
        setup = {
            "score": 7,
            "direction": "LONG",
            "current_price": 100000,
            "has_bos": True,
            "has_fvg": True,
            "stop_loss": 97800,
            "take_profit_1": 103300,
            "rr": 1.5,
            "rsi": 55,
            "volume_confirmed": True,
        }
        prompt = AIAgentCore._build_verification_prompt("BTCUSDT", setup)
        assert "BTCUSDT" in prompt
        assert "7/8" in prompt
        assert "LONG" in prompt
        assert "100000" in prompt
        assert "True" in prompt
