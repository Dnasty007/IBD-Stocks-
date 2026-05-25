from __future__ import annotations

from collections.abc import Sequence

from stock_watcher.config import PRICE_SWING_URGENT_PCT
from stock_watcher.formatting import format_percent, format_ratio, format_timestamp
from stock_watcher.models import Headline, PriceSnapshot, UrgentInsight


def build_urgent_insights(
    quote: PriceSnapshot,
    headlines: Sequence[Headline],
) -> list[UrgentInsight]:
    insights: list[UrgentInsight] = []

    if quote.session_change_pct is not None and abs(quote.session_change_pct) >= PRICE_SWING_URGENT_PCT:
        direction = "surge" if quote.session_change_pct > 0 else "drawdown"
        insights.append(
            UrgentInsight(
                title=f"{quote.symbol} volatility event: {format_percent(quote.session_change_pct)}",
                detail=(
                    f"Session {direction} detected with volume at "
                    f"{format_ratio(quote.volume_ratio)}."
                ),
                category="Price Shock",
                severity="positive" if quote.session_change_pct > 0 else "critical",
            )
        )

    for headline in headlines:
        if not headline.is_urgent:
            continue
        keyword_label = ", ".join(word.title() for word in headline.matched_keywords) or "Price Swing"
        insights.append(
            UrgentInsight(
                title=headline.title,
                detail=(
                    f"{headline.source or 'Unknown source'} | {format_timestamp(headline.published_at)}"
                    f" | {keyword_label}"
                ),
                category="Headline Trigger",
                severity="critical" if headline.sentiment == "negative" else "warning",
                link=headline.link,
            )
        )

    return insights


def headline_sentiment_totals(headlines: Sequence[Headline]) -> dict[str, int]:
    totals = {
        "urgent": 0,
        "positive": 0,
        "neutral": 0,
    }
    for headline in headlines:
        if headline.is_urgent:
            totals["urgent"] += 1
        elif headline.is_upgrade or headline.sentiment == "positive":
            totals["positive"] += 1
        else:
            totals["neutral"] += 1
    return totals
