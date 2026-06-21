from __future__ import annotations

from pathlib import Path

from stock_watcher.models import StockProfile

APP_BACKGROUND = "#0E1117"
APP_PANEL = "#111821"
ELECTRIC_CYAN = "#35F2FF"
PULSE_RED = "#FF4D6D"
SOFT_TEXT = "#E7EEF7"
MUTED_TEXT = "#91A4B7"

DEFAULT_REFRESH_SECONDS = 45
DEFAULT_VOLUME_SPIKE_RATIO = 2.0
DEFAULT_CRASH_TRIGGER_PCT = -3.0
PRICE_SWING_URGENT_PCT = 15.0
NEWS_LIMIT = 12
VOLUME_LOOKBACK_DAYS = 30
PORTFOLIO_STORAGE_PATH = Path(__file__).resolve().parent.parent / "data" / "portfolio.json"
DEFAULT_BENCHMARK_SYMBOL = "^GSPC"
DEFAULT_SOURCES = ("Robinhood", "Coinbase", "Metamask", "Fidelity", "Schwab", "Manual")

ANALYST_UPGRADE_KEYWORDS = (
    "upgrade",
    "upgraded",
    "buy rating",
    "outperform",
    "overweight",
    "top pick",
    "initiates buy",
    "initiated buy",
    "price target raised",
    "raises price target",
    "bullish",
    "strong buy",
    "buy rating",
    "price target increased",
)

URGENT_NEWS_KEYWORDS = (
    "dilution",
    "merge",
    "bankruptcy",
    "acquisition",
    "offering",
    "reverse split",
    "delisting",
    "lawsuit",
    "sec investigation",
    "earnings miss",
    "guidance lowered",
    "contract win",
    "partnership",
)


def build_default_queries(symbol: str, display_name: str | None = None) -> tuple[str, ...]:
    query_list = [f"{symbol} stock", f"{symbol} analyst"]
    if display_name and display_name.upper() != symbol.upper():
        query_list.extend(
            [
                f'"{display_name}" stock',
                f'"{display_name}" analyst',
            ]
        )
    return tuple(dict.fromkeys(query_list))


DEFAULT_STOCKS = (
    StockProfile(
        symbol="HOVR",
        display_name="New Horizon Aircraft",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("HOVR", "New Horizon Aircraft"),
    ),
    StockProfile(
        symbol="HUT",
        display_name="Hut 8 Corp",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("HUT", "Hut 8 Corp"),
    ),
    StockProfile(
        symbol="RKLB",
        display_name="Rocket Lab",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("RKLB", "Rocket Lab"),
    ),
    StockProfile(
        symbol="RHHBY",
        display_name="Roche",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("RHHBY", "Roche"),
    ),
    StockProfile(
        symbol="CECO",
        display_name="CECO Environmental",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("CECO", "CECO Environmental"),
    ),
    StockProfile(
        symbol="TGTX",
        display_name="TG Therapeutics",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("TGTX", "TG Therapeutics"),
    ),
    StockProfile(
        symbol="TVTX",
        display_name="Travere Therapeutics",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("TVTX", "Travere Therapeutics"),
    ),
    StockProfile(
        symbol="LQDA",
        display_name="Liquidia",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("LQDA", "Liquidia"),
    ),
    StockProfile(
        symbol="CGNX",
        display_name="Cognex",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("CGNX", "Cognex"),
    ),
    StockProfile(
        symbol="GRC",
        display_name="Gorman-Rupp",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("GRC", "Gorman-Rupp"),
    ),
    StockProfile(
        symbol="LTH",
        display_name="Life Time Group",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("LTH", "Life Time Group"),
    ),
    StockProfile(
        symbol="TILE",
        display_name="Interface",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("TILE", "Interface"),
    ),
    StockProfile(
        symbol="IBKR",
        display_name="Interactive Brokers",
        benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
        rss_queries=build_default_queries("IBKR", "Interactive Brokers"),
    ),
)

STOCKS_BY_SYMBOL = {stock.symbol: stock for stock in DEFAULT_STOCKS}


def build_stock_registry(extra_symbols: list[str] | tuple[str, ...] | set[str] = ()) -> dict[str, StockProfile]:
    registry = dict(STOCKS_BY_SYMBOL)
    for raw_symbol in extra_symbols:
        symbol = str(raw_symbol).strip().upper()
        if not symbol or symbol in registry:
            continue
        registry[symbol] = StockProfile(
            symbol=symbol,
            display_name=symbol,
            benchmark_symbol=DEFAULT_BENCHMARK_SYMBOL,
            rss_queries=build_default_queries(symbol),
        )
    return registry
