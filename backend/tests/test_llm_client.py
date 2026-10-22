# tests/test_llm_client.py
"""Tests for LLM Client — Gemini integration with fallback behavior."""
from __future__ import annotations

import json

import pytest

from app.ai_agent.llm_client import LLMClient


class TestLLMClientConfiguration:
    """Test LLMClient configuration and status."""

    def test_not_configured_without_key(self) -> None:
        client = LLMClient(api_key="", model_name="test-model")
        assert not client.is_configured

    def test_configured_with_key(self) -> None:
        client = LLMClient(api_key="test-key-123", model_name="test-model")
        assert client.is_configured

    def test_custom_model_name(self) -> None:
        client = LLMClient(api_key="k", model_name="gemini-2.0-flash")
        assert client.model_name == "gemini-2.0-flash"

    def test_default_model_name(self) -> None:
        client = LLMClient(api_key="k")
        assert client.model_name == "gemini-2.5-flash-lite"


class TestLLMClientGenerate:
    """Test generate methods with missing key (fallback)."""

    @pytest.mark.asyncio
    async def test_generate_returns_empty_without_key(self) -> None:
        client = LLMClient(api_key="")
        result = await client.generate("Hello")
        assert result == ""

    @pytest.mark.asyncio
    async def test_generate_json_returns_none_without_key(self) -> None:
        client = LLMClient(api_key="")
        result = await client.generate_json("Give me JSON")
        assert result is None


class TestLLMClientRequestBody:
    """Test request body construction."""

    def test_build_body_simple(self) -> None:
        body = LLMClient._build_request_body(
            prompt="Test prompt",
            system_prompt="",
            response_json=False,
        )
        assert "contents" in body
        assert len(body["contents"]) == 1
        assert body["contents"][0]["role"] == "user"

    def test_build_body_with_system_prompt(self) -> None:
        body = LLMClient._build_request_body(
            prompt="Test prompt",
            system_prompt="You are helpful",
            response_json=False,
        )
        # System prompt adds 2 entries (user + model acknowledgment)
        assert len(body["contents"]) == 3

    def test_build_body_json_mode(self) -> None:
        body = LLMClient._build_request_body(
            prompt="Give JSON",
            system_prompt="",
            response_json=True,
        )
        config = body["generationConfig"]
        assert config["responseMimeType"] == "application/json"


class TestLLMClientExtractText:
    """Test response text extraction."""

    def test_extract_text_standard(self) -> None:
        data = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Hello world"}],
                },
            }],
        }
        assert LLMClient._extract_text(data) == "Hello world"

    def test_extract_text_empty_candidates(self) -> None:
        assert LLMClient._extract_text({"candidates": []}) == ""

    def test_extract_text_no_candidates(self) -> None:
        assert LLMClient._extract_text({}) == ""


class TestLLMClientParseJson:
    """Test JSON response parsing."""

    def test_parse_clean_json(self) -> None:
        raw = json.dumps({"approved": True, "confidence": 85})
        result = LLMClient._parse_json_response(raw)
        assert result is not None
        assert result["approved"] is True
        assert result["confidence"] == 85

    def test_parse_json_with_markdown_fences(self) -> None:
        raw = '```json\n{"approved": false}\n```'
        result = LLMClient._parse_json_response(raw)
        assert result is not None
        assert result["approved"] is False

    def test_parse_json_embedded_in_text(self) -> None:
        raw = 'Here is the result: {"approved": true, "confidence": 90}'
        result = LLMClient._parse_json_response(raw)
        assert result is not None
        assert result["approved"] is True

    def test_parse_invalid_json_returns_none(self) -> None:
        result = LLMClient._parse_json_response("Not valid JSON at all")
        assert result is None
