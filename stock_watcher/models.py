from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class StockProfile:
    symbol: str
    display_name: str
    benchmark_symbol: str
    rss_queries: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlertSettings:
    high_price_target: float | None
    volume_spike_ratio: float
    market_crash_pct: float


@dataclass(frozen=True, slots=True)
class Headline:
    title: str
    link: str
    source: str | None
    published_at: datetime | None
    is_upgrade: bool
    matched_keywords: tuple[str, ...] = ()
    move_pct: float | None = None
    is_urgent: bool = False
    sentiment: str = "neutral"


@dataclass(frozen=True, slots=True)
class AlertEvent:
    name: str
    severity: str
    message: str


@dataclass(frozen=True, slots=True)
class PriceSnapshot:
    symbol: str
    display_name: str
    currency: str
    price: float | None
    previous_close: float | None
    open_price: float | None
    day_high: float | None
    day_low: float | None
    fifty_two_week_high: float | None
    fifty_two_week_low: float | None
    volume: float | None
    average_volume_30d: float | None
    volume_ratio: float | None
    session_change_pct: float | None


@dataclass(frozen=True, slots=True)
class FundamentalsSnapshot:
    market_cap: float | None
    enterprise_value: float | None
    revenue_growth: float | None
    earnings_growth: float | None
    total_cash: float | None
    total_debt: float | None
    float_shares: float | None
    analyst_target_mean: float | None
    debt_to_equity: float | None = None


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    symbol: str
    price: float | None
    previous_close: float | None
    session_change_pct: float | None


@dataclass(frozen=True, slots=True)
class StockContext:
    profile: StockProfile
    quote: PriceSnapshot
    fundamentals: FundamentalsSnapshot
    intraday_history: Any
    daily_history: Any
    analyst_actions: Any
    benchmark_intraday_history: Any
    benchmark_daily_history: Any
    market_correlation: float | None


@dataclass(frozen=True, slots=True)
class PortfolioPosition:
    symbol: str
    quantity: float
    average_cost: float
    source: str


@dataclass(frozen=True, slots=True)
class PortfolioPositionSummary:
    symbol: str
    source: str
    quantity: float
    average_cost: float
    total_investment: float
    current_price: float | None
    current_value: float | None
    pnl_percent: float | None
    pnl_dollar: float | None


@dataclass(frozen=True, slots=True)
class UrgentInsight:
    title: str
    detail: str
    category: str
    severity: str
    link: str | None = None
