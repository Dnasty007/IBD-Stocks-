# Stock Watcher

Streamlit dashboard for tracking `HOVR` (New Horizon Aircraft) with:

- live-ish Yahoo Finance price and volume snapshots through `yfinance`
- S&P 500 crash monitoring using `^GSPC`
- RSS headline monitoring with upgrade keyword detection
- configurable alerts for price targets, volume spikes, and market drops
- a modular package layout so more stocks can be added later

## Features

- `HOVR` quote monitoring with intraday charting
- daily volume spike detection versus the last 30 trading days
- market crash alerting based on the S&P 500 daily move
- RSS headline aggregation from Google News search feeds
- recent analyst action table via `yfinance`
- fundamentals snapshot for quick context
- auto-refresh using Streamlit fragments

## Project Layout

```text
stock-watcher/
├── app.py
├── requirements.txt
├── stock_watcher/
│   ├── alerts.py
│   ├── config.py
│   ├── formatting.py
│   ├── models.py
│   └── data/
│       ├── rss.py
│       └── yahoo_finance.py
└── tests/
    └── test_alerts.py
```

## Setup

```powershell
cd C:\Users\Pennl\OneDrive\Documents\Playground\stock-watcher
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Easiest Launch On Windows

If Streamlit permissions are finicky on your machine, use [launch_stock_watcher.cmd](C:\Users\Pennl\OneDrive\Documents\Playground\stock-watcher\launch_stock_watcher.cmd). It pins Streamlit's local profile to the project folder and starts the app on `http://localhost:8504`.

## Adding More Stocks

Add more `StockProfile` entries in [stock_watcher/config.py](C:\Users\Pennl\OneDrive\Documents\Playground\stock-watcher\stock_watcher\config.py) and they will automatically appear in the sidebar ticker selector.

## Notes

- `yfinance` uses Yahoo Finance data and is intended for personal and research use.
- Yahoo data may be delayed and should not be treated as an exchange-grade real-time feed.
- The RSS module uses public search feeds, so headline availability can vary by source and query quality.
