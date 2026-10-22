# AlgoTrade — ربات معامله‌گر الگوریتمی حرفه‌ای

<div dir="rtl">

یک سامانه معامله‌گر الگوریتمی حرفه‌ای، امن و قابل بکتست با رابط کاربری فارسی/انگلیسی.

</div>

## Features

- **Multi-Timeframe Price Action**: 4H structure → 1H entry → 15M momentum filter
- **8-Criteria Signal Scoring**: Minimum 6/8 confirmations required
- **Advanced Risk Management**: 1% per trade, 4 max positions, 8%/12% drawdown circuit breakers
- **Grid Management**: 25 levels between 30-day S/R, disabled if range < 4%
- **Trailing Stop System**: RR=1.5→Breakeven, RR=2.5→50% partial close
- **Paper Trading Default**: Live trading requires explicit confirmation
- **Kill Switch**: Emergency stop for all positions and orders
- **Backtesting Engine**: No look-ahead bias, with fee/slippage simulation
- **Bilingual RTL Dashboard**: Persian/English with dark theme
- **Multi-Market**: Crypto (CCXT), Forex/TSE (Faraz API)

## Tech Stack

| Layer | Technology |
|:------|:-----------|
| Backend | Python 3.12+ / FastAPI / Pydantic |
| Frontend | React / Vite / TypeScript / Zustand |
| Charts | TradingView Lightweight Charts |
| Exchange | CCXT (Crypto) / Faraz API (Forex/TSE) |
| Database | SQLite (dev) / PostgreSQL + TimescaleDB (prod) |
| Cache | Redis |
| i18n | YAML (backend) / JSON (frontend) |

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Redis (optional for dev)

### Setup

```bash
# Clone
git clone <repo-url> && cd AlgoTrade

# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cd ..

# Frontend
cd frontend
npm install
cd ..

# Environment
copy .env.example .env
# Edit .env with your settings
```

### Run (One-Click Launcher)

Simply run the batch file or PowerShell script at the root of the project:

```cmd
# Double-click or run from terminal:
start.bat

# Or using PowerShell:
.\start.ps1
```

This automatically:
1. Verifies/Starts the **PostgreSQL 18** and **Redis** Docker containers (`Alef-DB` and `Alef-Redis`).
2. Launches the **FastAPI Backend** with hot-reload monitoring both `backend/app/` and external `G:\Projects\AlefTrade/`.
3. Launches the **Vite React Frontend** at `http://localhost:5173/`.

### Run (Manual)

```bash
# Backend with AlefTrade hot-reload
cd backend
uv run uvicorn main:app --reload --reload-dir app --reload-dir G:\Projects\AlefTrade --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev
```

### Stop Services

```cmd
# Stop Backend and Frontend:
stop.bat
```

### Paper Trading (Default)

The system starts in **Paper Trading** mode by default. No real orders are placed.
To enable live trading, set `TRADING_MODE=LIVE_TRADING` in `.env` and confirm in the UI.

> ⚠️ **No profit guarantees.** All strategy thresholds are configurable.

## Project Structure

```
AlgoTrade/
├── backend/          # Python FastAPI backend
│   ├── app/
│   │   ├── config/       # Settings & YAML defaults
│   │   ├── models/       # Pydantic + SQLAlchemy models
│   │   ├── exchange/     # Exchange adapters (CCXT, Faraz, Paper)
│   │   ├── market_data/  # Candle fetching, buffering, multi-TF
│   │   ├── strategy/     # Price Action engine & signal scoring
│   │   ├── indicators/   # RSI, ATR, Volume, R:R
│   │   ├── risk/         # Position sizing, drawdown, kill switch
│   │   ├── oms/          # Order execution & tracking
│   │   ├── backtest/     # Backtesting engine
│   │   ├── api/          # REST + WebSocket endpoints
│   │   ├── db/           # Database layer
│   │   └── scheduler/    # Cron jobs (15-min scan, daily report)
│   ├── i18n/             # Translations (fa/en YAML)
│   └── tests/            # Automated tests
├── frontend/         # React + Vite + TypeScript
│   └── src/
│       ├── components/   # UI components
│       ├── pages/        # Page layouts
│       ├── stores/       # Zustand state
│       ├── i18n/         # Frontend translations
│       └── hooks/        # Custom hooks
└── docs/             # Documentation (fa/en)
```

## License

Private — All rights reserved.
