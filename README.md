# Trend Breakout Portfolio Framework

A professional multi-symbol trend-following breakout trading framework using **Backtrader**, designed for futures, commodities, FX, and index micros. Supports portfolio-level backtesting, walkforward testing, and trade analytics.

---
## Core Logic
1. Trend-following breakout strategy:
    - Entry on N-day high breakout (long) or N-day low breakout (short).
    - Risk-defined position sizing with contract multipliers.
    - Trailing stops to lock in profits.
    - Hard stops at opposite breakout levels.

2. Portfolio-level engine:
    - Manages trades across multiple assets.
    - Shared cash, shared risk.

3. Walkforward testing:
    - Rolling train/test windows (e.g., train 2 years, test 6 months).

## 🚀 Features

- ✅ **Portfolio-level strategy** — shared cash, risk, and trades across multiple assets.
- 🔥 **Breakout trading logic** — based on N-day high/low breakouts with trailing stops.
- 💰 **Risk-based position sizing** — per contract, with customizable multipliers.
- ⚙️ **Commission, slippage, and margin modeling** — realistic futures execution.
- 🏗️ **Walkforward testing** — rolling train/test periods for robustness.
- 📊 **Full trade logs and performance reporting** — equity curves, win rates, PnL stats.
- ✅ Supports **micro futures (MES, MNQ, MGC, etc.)**, standard futures, and FX.

---

## 📁 Project Structure

```plaintext
trend_breakout_framework/
├── config/                   # Configurations for parameters and symbols
│   ├── contracts.json         # Symbol mapping (e.g., MES → MES=F Yahoo Finance)
│   └── config.json            # Strategy parameters and backtest settings
│
├── data/                     # Data storage (by timeframe)
│   └── 1d/                    # Example: MES=F.csv
│   └── 5m/                    # (Optional) For intraday backtesting
│
├── reports/                  # Outputs
│   ├── trade logs             # Per-symbol trade logs
│   ├── walkforward results    # CSV for walkforward and optimizer
│   ├── grid search results    # Scored parameter runs
│   └── report.ipynb           # Jupyter notebook — equity curve, drawdowns, summaries
│
├── strategies/               # Trading strategies
│   └── breakout_strategy.py   # ✅ PortfolioBreakoutStrategy
│
├── utils/                    # Supporting tools
│   ├── data_loader.py         # ✅ Loads data, auto-download if missing
│   ├── walkforward.py         # ✅ Walkforward with fixed parameters
│   ├── walkforward_optimizer.py # ✅ Walkforward with parameter optimization
│   ├── grid_optimizer.py      # ✅ Grid search optimizer (Sharpe, Win Rate, etc.)
│   ├── performance.py         # ✅ Performance summary + equity curves
│   ├── plot_results.py        # (Optional) Entry/exit plotting
│   └── broker_models.py       # ✅ Commission, slippage, margin models
│
├── main.py                   # ✅ Main script — runs backtest, walkforward, optimizer
│
├── requirements.txt           # ✅ Dependencies
├── .gitignore                 # ✅ Exclude .venv, data, reports, pycache
└── README.md                  # ✅ Full documentation

```

## 🚀 Quick Start

**Clone the repo**
```bash
git clone https://github.com/yourusername/trend_breakout_framework.git
cd trend_breakout_framework
pip install -r requirements.txt
python main.py
```

**Create a virtual environment**
```bash
python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.venv\Scripts\activate        # On Windows
# or
source .venv/bin/activate     # On macOS/Linux
```

1️⃣ **Install dependencies:**

```bash
pip install -r requirements.txt
```

2️⃣ **Configure your trading setup:**

Edit config/config.json.
```bash
{
  "strategy": {
    "breakout_window": 20,
    "trailing_stop_pct": 0.03,
    "risk_per_trade": 0.01
  },
  "symbols": [
    { "symbol": "MES", "contract_multiplier": 5 },
    { "symbol": "MNQ", "contract_multiplier": 2 },
    { "symbol": "MGC", "contract_multiplier": 10 },
    { "symbol": "MCL", "contract_multiplier": 100 },
    { "symbol": "M6E", "contract_multiplier": 12500 }
  ],
  "timeframe": "1d",
  "start_date": "2020-01-01",
  "end_date": "2025-06-30",
  "initial_cash": 100000
}
```

**If wish to add more contracts. Edit config/contracts.json**
<br><br>***Example***
```plaintext
{
    "CL": "CL=F",      // Crude Oil
    "NG": "NG=F",      // Natural Gas
    "GC": "GC=F",      // Gold
    "SI": "SI=F",      // Silver
    "HG": "HG=F",      // Copper

    "ZC": "ZC=F",      // Corn
    "ZS": "ZS=F",      // Soybeans
    "ZW": "ZW=F",      // Wheat

    "ES": "ES=F",      // S&P 500 E-mini
    "NQ": "NQ=F",      // Nasdaq E-mini
    "YM": "YM=F",      // Dow Jones E-mini
    "RTY": "RTY=F",    // Russell 2000 E-mini

    "6E": "6E=F",      // Euro Futures
    "6B": "6B=F",      // British Pound Futures
    "6J": "6J=F",      // Japanese Yen Futures
    "6C": "6C=F",      // Canadian Dollar Futures
    "6A": "6A=F",      // Australian Dollar Futures

    "LE": "LE=F",      // Live Cattle
    "HE": "HE=F",      // Lean Hogs
    "KC": "KC=F"       // Coffee

    "MES": "MES=F",   // Micro S&P 500
    "MNQ": "MNQ=F",   // Micro Nasdaq 100
    "M2K": "M2K=F",   // Micro Russell 2000
    "MYM": "MYM=F",   // Micro Dow Jones

    "MGC": "MGC=F",   // Micro Gold
    "SIL": "SIL=F",   // Micro Silver
    "MCL": "MCL=F",   // Micro Crude Oil

    "M6E": "M6E=F",   // Micro EUR/USD
    "M6B": "M6B=F",   // Micro GBP/USD
}
```
