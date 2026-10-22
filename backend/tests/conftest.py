# tests/conftest.py
"""
Pytest Fixtures and Environment Setup.
"""
import os

os.environ["TRADING_MODE"] = "PAPER_TRADING"
os.environ["DB_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-testing-32chars"

import pytest


@pytest.fixture
def sample_prices():
    """Generates synthetic trend prices for indicator validation."""
    return [
        100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 106.0, 108.0,
        110.0, 109.0, 111.0, 113.0, 112.0, 114.0, 116.0, 118.0,
        120.0, 119.0, 121.0, 123.0,
    ]
