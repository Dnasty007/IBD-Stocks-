from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from stock_watcher.config import ELECTRIC_CYAN

GRID_COLOR = "rgba(53, 242, 255, 0.10)"
STEEL_GRAY = "#718191"
BAR_MUTED = "#31414F"
PAPER_BG = "rgba(0,0,0,0)"
PLOT_BG = "rgba(0,0,0,0)"


def build_intraday_context_chart(
    stock_history: pd.DataFrame,
    benchmark_history: pd.DataFrame,
    stock_symbol: str,
    benchmark_symbol: str,
):
    stock_frame = _prepare_intraday_frame(stock_history, stock_symbol)
    benchmark_frame = _prepare_intraday_frame(benchmark_history, benchmark_symbol)
    if stock_frame.empty and benchmark_frame.empty:
        return None

    figure = go.Figure()

    if not stock_frame.empty:
        figure.add_trace(
            go.Scatter(
                x=stock_frame["timestamp"],
                y=stock_frame["pct_from_open"],
                mode="lines",
                line={"color": "rgba(53, 242, 255, 0.18)", "width": 10},
                hoverinfo="skip",
                showlegend=False,
                name=f"{stock_symbol} glow",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=stock_frame["timestamp"],
                y=stock_frame["pct_from_open"],
                mode="lines",
                line={"color": ELECTRIC_CYAN, "width": 3},
                fill="tozeroy",
                fillcolor="rgba(53, 242, 255, 0.08)",
                name=stock_symbol,
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Time: %{x|%I:%M %p}<br>"
                    "% from open: %{y:+.2f}%<br>"
                    "Price: %{customdata:.4f}<extra></extra>"
                ),
                customdata=stock_frame["price"],
            )
        )

    if not benchmark_frame.empty:
        figure.add_trace(
            go.Scatter(
                x=benchmark_frame["timestamp"],
                y=benchmark_frame["pct_from_open"],
                mode="lines",
                line={"color": STEEL_GRAY, "width": 2, "dash": "dot"},
                name=benchmark_symbol,
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Time: %{x|%I:%M %p}<br>"
                    "% from open: %{y:+.2f}%<br>"
                    "Price: %{customdata:.2f}<extra></extra>"
                ),
                customdata=benchmark_frame["price"],
            )
        )

    figure.add_hline(y=0, line_width=1, line_dash="dash", line_color=GRID_COLOR)
    figure.update_layout(
        height=360,
        margin={"l": 18, "r": 18, "t": 18, "b": 18},
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        hovermode="x unified",
        hoverlabel={"bgcolor": "#111821", "font": {"family": "JetBrains Mono", "color": "#E7EEF7"}},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
            "font": {"family": "JetBrains Mono", "color": "#91A4B7", "size": 11},
        },
        xaxis={
            "showgrid": True,
            "gridcolor": GRID_COLOR,
            "gridwidth": 1,
            "zeroline": False,
            "linecolor": "rgba(0,0,0,0)",
            "tickfont": {"family": "JetBrains Mono", "color": "#91A4B7"},
            "title": "",
        },
        yaxis={
            "showgrid": True,
            "gridcolor": GRID_COLOR,
            "gridwidth": 1,
            "zeroline": False,
            "tickfont": {"family": "JetBrains Mono", "color": "#91A4B7"},
            "title": "% from session open",
            "titlefont": {"family": "JetBrains Mono", "color": "#91A4B7"},
            "ticksuffix": "%",
        },
    )
    return figure


def build_volume_history_chart(daily_history: pd.DataFrame):
    if daily_history.empty or "Volume" not in daily_history.columns:
        return None

    frame = daily_history.reset_index().copy()
    date_column = frame.columns[0]
    frame["timestamp"] = pd.to_datetime(frame[date_column], errors="coerce")
    frame = frame[["timestamp", "Volume"]].dropna().tail(20)
    if frame.empty:
        return None

    average_volume = frame["Volume"].mean()
    frame["bar_color"] = frame["Volume"].apply(
        lambda value: ELECTRIC_CYAN if value >= average_volume else BAR_MUTED
    )

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=frame["timestamp"],
            y=frame["Volume"],
            marker={"color": frame["bar_color"], "line": {"width": 0}},
            hovertemplate="Session: %{x|%Y-%m-%d}<br>Volume: %{y:,.0f}<extra></extra>",
        )
    )
    figure.update_layout(
        height=210,
        margin={"l": 18, "r": 18, "t": 12, "b": 18},
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        showlegend=False,
        xaxis={
            "showgrid": True,
            "gridcolor": GRID_COLOR,
            "gridwidth": 1,
            "tickfont": {"family": "JetBrains Mono", "color": "#91A4B7"},
            "title": "",
        },
        yaxis={
            "showgrid": True,
            "gridcolor": GRID_COLOR,
            "gridwidth": 1,
            "tickfont": {"family": "JetBrains Mono", "color": "#91A4B7"},
            "title": "Volume",
            "titlefont": {"family": "JetBrains Mono", "color": "#91A4B7"},
        },
    )
    return figure


def build_source_exposure_chart(summary_frame: pd.DataFrame):
    if summary_frame.empty or "Exchange/Source" not in summary_frame.columns:
        return None

    working = summary_frame[["Exchange/Source", "Current Value"]].copy()
    working["Current Value"] = pd.to_numeric(working["Current Value"], errors="coerce").fillna(0)
    grouped = (
        working.groupby("Exchange/Source", as_index=False)["Current Value"]
        .sum()
        .sort_values("Current Value", ascending=True)
    )
    if grouped.empty:
        return None

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=grouped["Current Value"],
            y=grouped["Exchange/Source"],
            orientation="h",
            marker={"color": ELECTRIC_CYAN, "line": {"width": 0}},
            hovertemplate="Source: %{y}<br>Current Value: %{x:,.2f}<extra></extra>",
        )
    )
    figure.update_layout(
        height=max(180, len(grouped) * 50),
        margin={"l": 18, "r": 18, "t": 12, "b": 18},
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        showlegend=False,
        xaxis={
            "showgrid": True,
            "gridcolor": GRID_COLOR,
            "gridwidth": 1,
            "tickfont": {"family": "JetBrains Mono", "color": "#91A4B7"},
            "title": "Current value",
            "titlefont": {"family": "JetBrains Mono", "color": "#91A4B7"},
        },
        yaxis={
            "showgrid": False,
            "tickfont": {"family": "JetBrains Mono", "color": "#91A4B7"},
            "title": "",
        },
    )
    return figure


def _prepare_intraday_frame(history: pd.DataFrame, series_name: str) -> pd.DataFrame:
    if history.empty or "Close" not in history.columns:
        return pd.DataFrame(columns=["timestamp", "series", "price", "pct_from_open"])

    frame = history.reset_index().copy()
    index_column = frame.columns[0]
    frame["timestamp"] = (
        pd.to_datetime(frame[index_column], utc=True, errors="coerce")
        .dt.tz_localize(None)
    )
    frame["price"] = pd.to_numeric(frame["Close"], errors="coerce")
    frame = frame[["timestamp", "price"]].dropna()
    if frame.empty:
        return pd.DataFrame(columns=["timestamp", "series", "price", "pct_from_open"])

    baseline = frame["price"].iloc[0]
    frame["pct_from_open"] = ((frame["price"] - baseline) / baseline) * 100 if baseline else 0.0
    frame["series"] = series_name
    return frame
