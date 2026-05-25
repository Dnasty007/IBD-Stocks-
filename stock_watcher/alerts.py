from __future__ import annotations

from collections.abc import Sequence

from stock_watcher.config import PRICE_SWING_URGENT_PCT
from stock_watcher.formatting import format_percent, format_price
from stock_watcher.models import AlertEvent, AlertSettings, Headline, MarketSnapshot, PriceSnapshot


def build_alerts(
    quote: PriceSnapshot,
    market: MarketSnapshot,
    headlines: Sequence[Headline],
    settings: AlertSettings,
) -> list[AlertEvent]:
    alerts: list[AlertEvent] = []

    if (
        settings.high_price_target is not None
        and quote.price is not None
        and quote.price >= settings.high_price_target
    ):
        alerts.append(
            AlertEvent(
                name="high_price",
                severity="positive",
                message=(
                    f"{quote.symbol} hit the high-price alert at "
                    f"{format_price(quote.price, quote.currency)}."
                ),
            )
        )

    if (
        quote.volume_ratio is not None
        and quote.volume_ratio >= settings.volume_spike_ratio
    ):
        alerts.append(
            AlertEvent(
                name="volume_spike",
                severity="warning",
                message=(
                    f"{quote.symbol} volume is running at {quote.volume_ratio:.2f}x "
                    "its 30-day average."
                ),
            )
        )

    if (
        quote.session_change_pct is not None
        and abs(quote.session_change_pct) >= PRICE_SWING_URGENT_PCT
    ):
        alerts.append(
            AlertEvent(
                name="price_shock",
                severity="critical" if quote.session_change_pct < 0 else "positive",
                message=(
                    f"{quote.symbol} is printing a high-volatility move of "
                    f"{format_percent(quote.session_change_pct)}."
                ),
            )
        )

    if (
        market.session_change_pct is not None
        and market.session_change_pct <= settings.market_crash_pct
    ):
        alerts.append(
            AlertEvent(
                name="market_crash",
                severity="critical",
                message=(
                    f"S&P 500 crash trigger fired: {market.symbol} is "
                    f"{format_percent(market.session_change_pct)} on the session."
                ),
            )
        )

    urgent_count = sum(1 for headline in headlines if headline.is_urgent)
    if urgent_count:
        alerts.append(
            AlertEvent(
                name="urgent_news",
                severity="critical",
                message=(
                    f"{urgent_count} headline(s) hit the urgent keyword or price-swing watchlist."
                ),
            )
        )

    upgrade_count = sum(1 for headline in headlines if headline.is_upgrade)
    if upgrade_count:
        alerts.append(
            AlertEvent(
                name="upgrade_news",
                severity="info",
                message=(
                    f"{upgrade_count} recent RSS headline(s) matched the analyst "
                    "upgrade keyword watchlist."
                ),
            )
        )

    return alerts
