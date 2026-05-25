from __future__ import annotations

import pandas as pd
import yfinance as yf

from stock_watcher.config import VOLUME_LOOKBACK_DAYS
from stock_watcher.models import (
    FundamentalsSnapshot,
    MarketSnapshot,
    PriceSnapshot,
    StockContext,
    StockProfile,
)


class YahooFinanceService:
    def build_stock_context(self, profile: StockProfile) -> StockContext:
        ticker = yf.Ticker(profile.symbol)
        benchmark_ticker = yf.Ticker(profile.benchmark_symbol)
        intraday_history = self._history(ticker, period="1d", interval="5m")
        daily_history = self._history(ticker, period="6mo", interval="1d")
        benchmark_intraday_history = self._history(benchmark_ticker, period="1d", interval="5m")
        benchmark_daily_history = self._history(benchmark_ticker, period="6mo", interval="1d")
        info = self._safe_info(ticker)

        display_name = str(info.get("longName") or info.get("shortName") or profile.display_name)
        quote = self._build_quote(profile, display_name, info, intraday_history, daily_history)
        fundamentals = self._build_fundamentals(info)
        analyst_actions = self._get_analyst_actions(ticker)

        return StockContext(
            profile=profile,
            quote=quote,
            fundamentals=fundamentals,
            intraday_history=intraday_history,
            daily_history=daily_history,
            analyst_actions=analyst_actions,
            benchmark_intraday_history=benchmark_intraday_history,
            benchmark_daily_history=benchmark_daily_history,
            market_correlation=self._calculate_correlation(
                intraday_history,
                benchmark_intraday_history,
            ),
        )

    def get_market_snapshot(self, symbol: str) -> MarketSnapshot:
        ticker = yf.Ticker(symbol)
        daily_history = self._history(ticker, period="5d", interval="1d")
        info = self._safe_info(ticker)

        latest_close = self._latest_close(daily_history)
        previous_close = (
            self._coerce_float(info.get("regularMarketPreviousClose"))
            or self._coerce_float(info.get("previousClose"))
            or self._previous_close(daily_history)
        )
        session_change_pct = self._change_pct(latest_close, previous_close)

        return MarketSnapshot(
            symbol=symbol,
            price=latest_close,
            previous_close=previous_close,
            session_change_pct=session_change_pct,
        )

    def _build_quote(
        self,
        profile: StockProfile,
        display_name: str,
        info: dict,
        intraday_history: pd.DataFrame,
        daily_history: pd.DataFrame,
    ) -> PriceSnapshot:
        latest_price = (
            self._latest_close(intraday_history)
            or self._coerce_float(info.get("currentPrice"))
            or self._coerce_float(info.get("regularMarketPrice"))
            or self._latest_close(daily_history)
        )
        previous_close = (
            self._coerce_float(info.get("regularMarketPreviousClose"))
            or self._coerce_float(info.get("previousClose"))
            or self._previous_close(daily_history)
        )
        open_price = (
            self._coerce_float(info.get("regularMarketOpen"))
            or self._coerce_float(info.get("open"))
            or self._first_open(intraday_history)
        )
        day_high = (
            self._coerce_float(info.get("regularMarketDayHigh"))
            or self._series_value(intraday_history, "High", "max")
        )
        day_low = (
            self._coerce_float(info.get("regularMarketDayLow"))
            or self._series_value(intraday_history, "Low", "min")
        )
        latest_daily_volume = self._series_value(daily_history, "Volume", "last")
        average_volume = self._average_volume(daily_history)
        volume = (
            self._coerce_float(info.get("regularMarketVolume"))
            or self._coerce_float(info.get("volume"))
            or latest_daily_volume
        )
        volume_ratio = None
        if volume is not None and average_volume not in (None, 0):
            volume_ratio = volume / average_volume

        return PriceSnapshot(
            symbol=profile.symbol,
            display_name=display_name,
            currency=str(info.get("currency") or "USD"),
            price=latest_price,
            previous_close=previous_close,
            open_price=open_price,
            day_high=day_high,
            day_low=day_low,
            fifty_two_week_high=self._coerce_float(info.get("fiftyTwoWeekHigh")),
            fifty_two_week_low=self._coerce_float(info.get("fiftyTwoWeekLow")),
            volume=volume,
            average_volume_30d=average_volume,
            volume_ratio=volume_ratio,
            session_change_pct=self._change_pct(latest_price, previous_close),
        )

    def _build_fundamentals(self, info: dict) -> FundamentalsSnapshot:
        return FundamentalsSnapshot(
            market_cap=self._coerce_float(info.get("marketCap")),
            enterprise_value=self._coerce_float(info.get("enterpriseValue")),
            revenue_growth=self._coerce_float(info.get("revenueGrowth")),
            earnings_growth=self._coerce_float(info.get("earningsGrowth")),
            total_cash=self._coerce_float(info.get("totalCash")),
            total_debt=self._coerce_float(info.get("totalDebt")),
            float_shares=self._coerce_float(info.get("floatShares")),
            analyst_target_mean=self._coerce_float(info.get("targetMeanPrice")),
            debt_to_equity=self._coerce_float(info.get("debtToEquity")),
        )

    def _get_analyst_actions(self, ticker: yf.Ticker) -> pd.DataFrame:
        try:
            actions = ticker.get_upgrades_downgrades(as_dict=False)
        except Exception:
            return pd.DataFrame(columns=["date", "firm", "toGrade", "fromGrade", "action"])

        if not isinstance(actions, pd.DataFrame) or actions.empty:
            return pd.DataFrame(columns=["date", "firm", "toGrade", "fromGrade", "action"])

        formatted = actions.reset_index().rename(columns={"index": "date"}).copy()
        if "date" in formatted.columns:
            formatted["date"] = formatted["date"].astype(str)
        keep = [column for column in ["date", "firm", "toGrade", "fromGrade", "action"] if column in formatted.columns]
        return formatted[keep].head(8)

    def _history(self, ticker: yf.Ticker, period: str, interval: str) -> pd.DataFrame:
        history = ticker.history(
            period=period,
            interval=interval,
            auto_adjust=False,
            prepost=False,
        )
        if not isinstance(history, pd.DataFrame) or history.empty:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        return history.dropna(how="all")

    def _safe_info(self, ticker: yf.Ticker) -> dict:
        try:
            info = ticker.info
        except Exception:
            return {}
        return info if isinstance(info, dict) else {}

    def _average_volume(self, daily_history: pd.DataFrame) -> float | None:
        if daily_history.empty or "Volume" not in daily_history.columns:
            return None
        volume_window = daily_history["Volume"].dropna().tail(VOLUME_LOOKBACK_DAYS)
        if volume_window.empty:
            return None
        return self._coerce_float(volume_window.mean())

    def _latest_close(self, history: pd.DataFrame) -> float | None:
        if history.empty or "Close" not in history.columns:
            return None
        closes = history["Close"].dropna()
        if closes.empty:
            return None
        return self._coerce_float(closes.iloc[-1])

    def _previous_close(self, history: pd.DataFrame) -> float | None:
        if history.empty or "Close" not in history.columns:
            return None
        closes = history["Close"].dropna()
        if len(closes) < 2:
            return self._coerce_float(closes.iloc[-1]) if not closes.empty else None
        return self._coerce_float(closes.iloc[-2])

    def _first_open(self, history: pd.DataFrame) -> float | None:
        if history.empty or "Open" not in history.columns:
            return None
        opens = history["Open"].dropna()
        if opens.empty:
            return None
        return self._coerce_float(opens.iloc[0])

    def _series_value(
        self,
        history: pd.DataFrame,
        column: str,
        reducer: str,
    ) -> float | None:
        if history.empty or column not in history.columns:
            return None
        values = history[column].dropna()
        if values.empty:
            return None
        if reducer == "max":
            return self._coerce_float(values.max())
        if reducer == "min":
            return self._coerce_float(values.min())
        return self._coerce_float(values.iloc[-1])

    def _change_pct(
        self,
        current_value: float | None,
        previous_value: float | None,
    ) -> float | None:
        if current_value is None or previous_value in (None, 0):
            return None
        return ((current_value - previous_value) / previous_value) * 100

    def _calculate_correlation(
        self,
        stock_history: pd.DataFrame,
        benchmark_history: pd.DataFrame,
    ) -> float | None:
        if stock_history.empty or benchmark_history.empty:
            return None
        if "Close" not in stock_history.columns or "Close" not in benchmark_history.columns:
            return None

        left = stock_history[["Close"]].rename(columns={"Close": "stock"})
        right = benchmark_history[["Close"]].rename(columns={"Close": "benchmark"})
        combined = left.join(right, how="inner").dropna()
        if len(combined) < 3:
            return None

        returns = combined.pct_change().dropna()
        if returns.empty:
            return None

        correlation = returns["stock"].corr(returns["benchmark"])
        return self._coerce_float(correlation)

    def _coerce_float(self, value) -> float | None:
        if value is None or pd.isna(value):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
