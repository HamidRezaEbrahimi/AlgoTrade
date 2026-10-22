# Workspace Development & Architecture Rules for AI Agents (AlgoTrade)

> **MANDATORY DIRECTIVE FOR ALL AI AGENTS & CODING ASSISTANTS**:
> Read and strictly enforce these standards before creating, refactoring, modifying, or testing any code in this codebase.

---

## 1. Clean Code & File Modularity (The 300–350 LOC Rule)
1. **File Size Limit**: Keep individual source files focused, clean, and concise (strictly under **300–350 lines of code**).
2. **Modular Directory Structure**: When a file, strategy, or service grows beyond ~350 lines, split it into dedicated domain submodules within a folder (e.g. `app/market_data/`, `app/strategy/`, `app/oms/`, `app/risk/`, `app/exchange/`, `app/indicators/`, `app/backtest/`) and provide a clean `__init__.py` barrel export (Python) or `index.ts` barrel export (TypeScript).
3. **No Hardcoded Secrets or Endpoints**: Never hardcode exchange API keys, secrets, passphrase tokens, webhook URLs, or host addresses. Always load from validated environment variables (`.env`) with safe schema parsing (Pydantic `BaseSettings` for Python, Zod for TypeScript).
4. **Single Responsibility Principle (SRP)**:
   - **Market Data Feed** (`app/market_data/`): Pure ingestion, candle aggregation, multi-timeframe management, and ring-buffered storage.
   - **Strategy Engine** (`app/strategy/`): Pure signal calculation — structure analysis (HH/HL, BOS, CHoCH), pattern detection (Engulfing, Pin Bar, Hammer, Morning Star), momentum filtering, level detection (S/R, OB, FVG), and 8-criteria scoring.
   - **Indicators** (`app/indicators/`): Stateless mathematical functions — RSI, ATR, Volume Ratio, Risk/Reward.
   - **Risk Management System** (`app/risk/`): Pre-trade safety validations — position sizing (1% max), drawdown monitoring (8%/12% circuit breakers), exposure guard (4 max positions, 12% capital), trailing stop management, kill switch.
   - **Order Management System** (`app/oms/`): Execution, order lifecycle tracking, idempotency (UUID clientOrderId), exit management (Stop, CHoCH, trailing).
   - **Exchange Adapters** (`app/exchange/`): Abstract adapter pattern with concrete CCXT, Faraz, and Paper Trading implementations; rate limiting (12s interval); position sync after reconnection.
   - **Backtesting Engine** (`app/backtest/`): Historical simulation without look-ahead bias; fee/slippage modeling; partial exit; equity curve and performance reporting.
   - **UI & Presentation** (`frontend/src/`): Visual components, TradingView chart rendering, and user interactions — fully separated from trading logic.

---

## 2. Multi-Language & Internationalization (i18n) Rules
1. **Zero Hardcoded Text**: Never write hardcoded Persian or English strings directly in:
   - UI components (React/TypeScript)
   - Backend API responses or error messages (Python/FastAPI)
   - Bot notifications (Telegram/Discord/Bale)
   - Log messages shown to users
2. **Namespace Segregation** (both backend YAML and frontend JSON):
   - `Common`: Shared buttons, general status labels, actions (`save`, `cancel`, `confirm`, `search`, `filter`, `loading`, `error`, `success`, `retry`).
   - `Dashboard`: Terminal overview, balance cards, active PnL, Win Rate, Sharpe ratio, equity curve metrics, performance summary.
   - `Strategies`: Strategy configuration, indicator parameters, trigger conditions, structure labels (HH, HL, BOS, CHoCH), pattern names, scoring criteria.
   - `Orders`: Order history, active positions, order type labels (`limit`, `market`, `stop_loss`, `take_profit`, `trailing_stop`), execution logs, fill status.
   - `Risk`: Risk parameters, maximum drawdown thresholds, stop-loss limits, kill-switch warnings, exposure alerts, circuit breaker messages.
   - `Scanner`: Opportunity list, symbol rankings, liquidity scores, signal quality labels.
   - `Backtest`: Backtest configuration, result metrics, equity curve labels, trade list headers.
   - `Bot`: Telegram/Bale notification templates, trade signal alerts, daily summary reports.
3. **Shared Components Rule**:
   - Any shared UI component in `components/shared/` **MUST ALWAYS** use the `Common` namespace.
   - **NEVER** use specialized namespaces (Dashboard, Orders, etc.) in shared generic components.
4. **Financial, Currency & Number Localization**:
   - Numbers and prices must be formatted using dedicated formatting utilities (`formatPrice`, `formatPercent`, `formatCryptoAmount`, `toPersianDigits`).
   - Timestamps must display in user's local timezone (Shamsi / Gregorian toggle) with standard **UTC** storage in the backend.
   - All decimal financial values must use `Decimal` type in Python and proper precision handling in TypeScript.

---

## 3. Trading Safety, Risk Controls & Execution Guardrails
1. **Emergency Kill-Switch**:
   - The system must provide an atomic, top-priority Kill-Switch mechanism to cancel all open orders, close all positions (optional safe flag), and suspend all strategy engines immediately.
   - Kill-Switch must be accessible from both UI (prominent red button) and API endpoint (`POST /system/kill-switch`).
2. **Pre-Trade Risk Checks (Mandatory RMS Pipeline)**:
   - Every order **MUST** pass through the Risk Engine before dispatching to the exchange:
     1. Maximum allowable slippage check.
     2. Account balance and margin verification.
     3. Maximum position size check (1% of capital per trade).
     4. Maximum simultaneous positions check (≤ 4).
     5. Maximum capital exposure check (≤ 12%).
     6. Daily drawdown cap check (8% → half size, 12% → stop entry).
     7. Stale data check (reject signals if candle latency > threshold).
     8. Minimum Risk/Reward ratio check (≥ 1.5).
3. **Order Idempotency & Duplicate Prevention**:
   - Every outgoing order must generate and attach a unique `clientOrderId` (UUID4) to avoid double-ordering during network timeouts or reconnections.
4. **Position Sync After Reconnection**:
   - After any connection interruption, the system must first sync actual exchange orders and positions before resuming strategy execution.
5. **Environment Isolation**:
   - Strict separation between `BACKTEST`, `PAPER_TRADING` (default), and `LIVE_TRADING` execution modes.
   - Live trading must require explicit user confirmation flag.
   - Paper Trading is the **default** mode.
6. **Zero Secret Leaks**:
   - API keys and private secrets must NEVER be logged, transmitted to client-side UI, or exposed in error stack traces.
   - Keys are stored server-side only, encrypted at rest.
7. **Rate Limiting & API Safety**:
   - Minimum 12 seconds between exchange API requests.
   - Maximum 3 retries with 30-second pause on rate limit errors.
   - Exponential backoff on transient failures.

---

## 4. Strategy Engine Rules & Signal Scoring
1. **Signal Source**: Entry signals come ONLY from Price Action on closed candles. Grid is NEVER an entry signal on its own.
2. **Multi-Timeframe Analysis**:
   - **4H**: Market structure direction (HH/HL = bullish, LH/LL = bearish, BOS, CHoCH).
   - **1H**: Entry patterns (Bullish Engulfing, Pin Bar, Hammer, Morning Star).
   - **15M**: Final momentum filter only.
3. **8-Criteria Scoring System**: Entry requires minimum **6 out of 8** confirmations:
   1. Proper structure (4H)
   2. Valid location (S/R, Order Block, FVG)
   3. Entry pattern confirmation (1H)
   4. Momentum confirmation (15M)
   5. RSI(14) confirmation
   6. Volume > MA(10) confirmation
   7. Risk/Reward ≥ 1.5
   8. Valid Stop Loss placement
4. **Grid Management**: 25 levels between 30-day S/R range, disabled if range < 4%.
5. **Market Scanning**: Scan liquid markets every 15 minutes after candle close, rank opportunities.
6. **All thresholds must be configurable** via YAML/env — never hardcoded in strategy logic.
7. **Decoupled Wave Pattern Engine & Skills Discipline (AlefTrade Integration)**:
   - High-precision Elliott Wave detection (Adaptive ZigZag, Running Flat, Developing Wave PRZ) is officially delegated to the external package `AlefTrade` (`app/strategy/alef_adapter.py`).
   - Markers drawn on the TradingView Lightweight Chart must snap to exact candle timestamps (`p.timestamp`) to eliminate any rendering drift.
   - For each wave pattern, mathematical ratios, noise filters, calibration guides, and edge-case diagnostics MUST be preserved as a dedicated Skill inside `AlefTrade/.agents/skills/<pattern-name>/SKILL.md`.

---

## 5. High Performance, Low-Latency & Streaming Standards
1. **WebSocket Resilience**:
   - WebSocket feeds must implement automatic heartbeat (ping/pong), exponential backoff reconnection, and connection state telemetry.
2. **Chart & UI Rendering Optimization**:
   - Real-time tick updates must not trigger heavy re-renders across the entire React component tree.
   - Use TradingView Lightweight Charts (Canvas-based) and batch/throttle state updates (100ms UI batching) while maintaining unthrottled ticks in the trading engine.
   - Use Zustand stores with selector-based subscriptions to minimize re-renders.
3. **Memory & Time-Series Data Management**:
   - In-memory candle buffers (sliding windows) must have strict capacity limits (ring buffer of last 1,000 candles per symbol per timeframe) to avoid memory leaks.
4. **Asynchronous Non-Blocking Execution**:
   - Heavy computations (backtesting, scanning all symbols, ML inference) must run in background workers or dedicated threads, never blocking the main async event loop.
5. **Market Check Interval**: Every 15 minutes, only after candle close. No intra-candle signal generation.

---

## 6. Mandatory Verification & Validation Protocol
Before concluding any task or reporting completion to the user, the AI agent **MUST** run and verify:
1. **Type Safety Verification**:
   - Python Backend: `mypy app/ --strict` or `ruff check .` (Must have zero type/lint errors).
   - TypeScript Frontend: `npx tsc --noEmit` (Must exit with code 0).
2. **Automated Test Suite**:
   - Backend: `python -m pytest tests/ -v`:
     - Mathematical indicator calculations (RSI, ATR, Volume) must match benchmark values.
     - Risk engine rules must prevent out-of-bound orders (>1% risk, >4 positions, >12% exposure).
     - Signal scorer must correctly require 6/8 minimum score.
     - Trailing stop transitions must be verified (RR=1.5→BE, RR=2.5→50% close).
     - Kill switch must atomically cancel all orders.
     - All test files must pass 100%.
   - Frontend: `npx vitest run` (All component/hook tests must pass).
3. **Production Build Validation**:
   - Frontend: `npm run build` (Must compile cleanly without build errors).
   - Backend: Application must start without import/config errors.
