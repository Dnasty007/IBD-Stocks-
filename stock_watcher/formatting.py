from __future__ import annotations

from datetime import datetime

WAITING_INDICATOR = "[WAITING]"


def format_price(value: float | None, currency: str = "USD", precision: int | None = None) -> str:
    if value is None:
        return WAITING_INDICATOR
    if precision is None:
        precision = 4 if abs(value) < 10 else 2
    if currency == "USD":
        return f"${value:,.{precision}f}"
    return f"{currency} {value:,.{precision}f}"


def format_percent(value: float | None, scale: float = 1.0) -> str:
    if value is None:
        return WAITING_INDICATOR
    return f"{value / scale:+.2f}%"


def format_currency_delta(value: float | None, currency: str = "USD", precision: int = 2) -> str:
    if value is None:
        return WAITING_INDICATOR
    if currency == "USD":
        sign = "+" if value >= 0 else "-"
        return f"{sign}${abs(value):,.{precision}f}"
    return f"{currency} {value:+,.{precision}f}"


def format_large_number(value: float | None) -> str:
    if value is None:
        return WAITING_INDICATOR

    absolute = abs(value)
    if absolute >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.2f}T"
    if absolute >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if absolute >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:,.0f}"


def format_quantity(value: float | None) -> str:
    if value is None:
        return WAITING_INDICATOR
    return f"{value:,.4f}".rstrip("0").rstrip(".")


def format_ratio(value: float | None, suffix: str = "x") -> str:
    if value is None:
        return WAITING_INDICATOR
    return f"{value:,.2f}{suffix}"


def format_timestamp(value: datetime | None) -> str:
    if value is None:
        return WAITING_INDICATOR
    return value.astimezone().strftime("%Y-%m-%d %I:%M %p")


def format_signed_decimal(value: float | None, precision: int = 2) -> str:
    if value is None:
        return WAITING_INDICATOR
    return f"{value:+.{precision}f}"
