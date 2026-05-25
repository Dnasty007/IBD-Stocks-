from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from stock_watcher.alerts import build_alerts
from stock_watcher.charts import (
    build_intraday_context_chart,
    build_source_exposure_chart,
    build_volume_history_chart,
)
from stock_watcher.config import (
    DEFAULT_CRASH_TRIGGER_PCT,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_SOURCES,
    DEFAULT_VOLUME_SPIKE_RATIO,
    NEWS_LIMIT,
    build_stock_registry,
)
from stock_watcher.context import get_company_context
from stock_watcher.data.rss import RSSNewsService
from stock_watcher.data.yahoo_finance import YahooFinanceService
from stock_watcher.formatting import (
    format_currency_delta,
    format_large_number,
    format_percent,
    format_price,
    format_quantity,
    format_ratio,
    format_signed_decimal,
)
from stock_watcher.insights import build_urgent_insights, headline_sentiment_totals
from stock_watcher.models import AlertSettings, StockProfile
from stock_watcher.portfolio import EDITOR_COLUMNS, PortfolioStore
from stock_watcher.styles import (
    inject_styles,
    render_alert_rail,
    render_empty_state,
    render_header,
    render_news_feed,
    render_section_header,
    render_sidebar_brand,
    render_urgent_cards,
    render_waiting_indicator,
)


st.set_page_config(
    page_title="Financial Command Center",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_styles()

finance_service = YahooFinanceService()
news_service = RSSNewsService()
portfolio_store = PortfolioStore()


@st.cache_data(ttl=45, show_spinner=False)
def load_stock_context(profile: StockProfile):
    return finance_service.build_stock_context(profile)


@st.cache_data(ttl=45, show_spinner=False)
def load_market_snapshot(symbol: str):
    return finance_service.get_market_snapshot(symbol)


@st.cache_data(ttl=300, show_spinner=False)
def load_headlines(profile: StockProfile):
    return news_service.fetch_headlines(profile.rss_queries, limit=NEWS_LIMIT)


def ensure_price_target(profile: StockProfile) -> float:
    state_key = f"high_target_{profile.symbol}"
    if state_key in st.session_state:
        return float(st.session_state[state_key])

    default_target = 1.0
    try:
        context = load_stock_context(profile)
        if context.quote.price is not None:
            default_target = round(context.quote.price * 1.08, 4)
    except Exception:
        default_target = 1.0

    st.session_state[state_key] = default_target
    return default_target


def build_status_text(auto_refresh: bool, refresh_seconds: int) -> str:
    live_state = "LIVE" if auto_refresh else "MANUAL"
    cadence = f"{refresh_seconds}s cadence" if auto_refresh else "refresh on command"
    timestamp = datetime.now().astimezone().strftime("%I:%M:%S %p %Z")
    return f"{live_state} | {cadence} | {timestamp}"


def render_sidebar(
    stock_registry: dict[str, StockProfile],
    selected_view: str,
) -> tuple[str, bool, int, AlertSettings | None]:
    render_sidebar_brand()

    st.sidebar.markdown("#### Navigation")
    selected = st.sidebar.radio(
        "Command Views",
        options=["Global Portfolio", *stock_registry.keys()],
        index=(["Global Portfolio", *stock_registry.keys()].index(selected_view)),
        label_visibility="collapsed",
    )

    st.session_state["selected_view"] = selected

    st.sidebar.markdown("#### Telemetry")
    auto_refresh = st.sidebar.toggle("Heartbeat live updates", value=True)
    refresh_seconds = st.sidebar.slider(
        "Refresh cadence (seconds)",
        min_value=15,
        max_value=180,
        value=DEFAULT_REFRESH_SECONDS,
        step=15,
    )

    if st.sidebar.button("Refresh command center", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    settings = None
    if selected != "Global Portfolio":
        profile = stock_registry[selected]
        ensure_price_target(profile)
        st.sidebar.markdown("#### Signal Thresholds")
        settings = AlertSettings(
            high_price_target=st.sidebar.number_input(
                "High price trigger",
                min_value=0.0,
                step=0.05,
                format="%.4f",
                key=f"high_target_{profile.symbol}",
            ),
            volume_spike_ratio=st.sidebar.slider(
                "Volume spike multiple",
                min_value=1.0,
                max_value=5.0,
                value=DEFAULT_VOLUME_SPIKE_RATIO,
                step=0.1,
            ),
            market_crash_pct=st.sidebar.slider(
                "Market crash trigger (%)",
                min_value=-10.0,
                max_value=-1.0,
                value=DEFAULT_CRASH_TRIGGER_PCT,
                step=0.5,
            ),
        )
    else:
        st.sidebar.caption(
            "Portfolio data is stored locally in `data/portfolio.json` and valuation refreshes off live market prices."
        )

    return selected, auto_refresh, refresh_seconds, settings


def collect_price_lookup(stock_registry: dict[str, StockProfile]) -> dict[str, float | None]:
    prices: dict[str, float | None] = {}
    for profile in stock_registry.values():
        try:
            prices[profile.symbol] = load_stock_context(profile).quote.price
        except Exception:
            prices[profile.symbol] = None
    return prices


def render_portfolio_editor(
    editor_frame: pd.DataFrame,
) -> None:
    render_section_header(
        "Portfolio Ledger",
        "Holdings storage + editing",
        "Edit your positions here. Base fields are writable; derived valuation fields are read-only.",
    )

    with st.container(border=True):
        show_editor = not editor_frame.empty or st.session_state.get("portfolio_editor_ready", False)
        if not show_editor:
            render_empty_state("Ready for Input")
            render_waiting_indicator("Create your first position to initialize the ledger.")
            if st.button("Initialize Portfolio Ledger", width="stretch", key="init_portfolio_ledger"):
                st.session_state["portfolio_editor_ready"] = True
                st.rerun()
            return

        if editor_frame.empty:
            editor_frame = pd.DataFrame(
                [
                    {
                        "Ticker": "",
                        "Quantity Owned": None,
                        "Average Cost": None,
                        "Total Investment": None,
                        "Current Value": None,
                        "P/L (%)": None,
                        "Exchange/Source": DEFAULT_SOURCES[0],
                    }
                ],
                columns=EDITOR_COLUMNS,
            )

        edited_frame = st.data_editor(
            editor_frame,
            width="stretch",
            hide_index=True,
            num_rows="dynamic",
            disabled=["Total Investment", "Current Value", "P/L (%)"],
            column_config={
                "Ticker": st.column_config.TextColumn(
                    "Ticker",
                    help="Tracked symbol.",
                    required=False,
                    width="small",
                ),
                "Quantity Owned": st.column_config.NumberColumn(
                    "Quantity Owned",
                    min_value=0.0,
                    step=1.0,
                    format="%.4f",
                ),
                "Average Cost": st.column_config.NumberColumn(
                    "Average Cost",
                    min_value=0.0,
                    format="$%.4f",
                ),
                "Total Investment": st.column_config.NumberColumn(
                    "Total Investment",
                    format="$%.2f",
                    disabled=True,
                ),
                "Current Value": st.column_config.NumberColumn(
                    "Current Value",
                    format="$%.2f",
                    disabled=True,
                ),
                "P/L (%)": st.column_config.NumberColumn(
                    "P/L (%)",
                    format="%.2f%%",
                    disabled=True,
                ),
                "Exchange/Source": st.column_config.SelectboxColumn(
                    "Exchange/Source",
                    options=list(DEFAULT_SOURCES),
                    required=False,
                ),
            },
            key="portfolio_editor",
        )

        save_col, reset_col = st.columns((1, 1))
        if save_col.button("Save portfolio", type="primary", width="stretch"):
            new_positions = portfolio_store.positions_from_editor_frame(edited_frame)
            portfolio_store.save_positions(new_positions)
            st.session_state["portfolio_positions"] = new_positions
            st.session_state["portfolio_editor_ready"] = bool(new_positions) or show_editor
            st.cache_data.clear()
            st.rerun()
        if reset_col.button("Reset view cache", width="stretch"):
            st.cache_data.clear()
            st.rerun()


def render_position_summary(symbol: str, price_lookup: dict[str, float | None], positions) -> None:
    summaries = portfolio_store.summaries_for_symbol(positions, symbol, price_lookup)
    aggregate = portfolio_store.aggregate_symbol(summaries, symbol)

    render_section_header(
        "Position Summary",
        f"{symbol} holdings",
        "Source-level exposure and blended cost basis tied to your local portfolio ledger.",
    )
    with st.container(border=True):
        if not summaries or aggregate is None:
            render_empty_state(
                f"No {symbol} position is stored yet. Add it from the Global Portfolio view."
            )
            return

        top = st.columns(4)
        top[0].metric("Quantity Owned", format_quantity(aggregate.quantity), border=True)
        top[1].metric(
            "Average Cost",
            format_price(aggregate.average_cost, precision=4),
            border=True,
        )
        top[2].metric(
            "Current Value",
            format_price(aggregate.current_value, precision=2),
            format_currency_delta(aggregate.pnl_dollar),
            border=True,
        )
        top[3].metric(
            "P/L (%)",
            format_percent(aggregate.pnl_percent),
            aggregate.source,
            border=True,
        )

        frame = pd.DataFrame(
            [
                {
                    "Ticker": summary.symbol,
                "Source": summary.source,
                "Quantity": summary.quantity,
                "Average Cost": summary.average_cost,
                "Total Investment": summary.total_investment,
                "Current Value": summary.current_value,
                    "P/L (%)": summary.pnl_percent,
                }
                for summary in summaries
            ]
        )
        st.dataframe(
            frame,
            width="stretch",
            hide_index=True,
            column_config={
                "Quantity": st.column_config.NumberColumn(format="%.4f"),
                "Average Cost": st.column_config.NumberColumn(format="$%.4f"),
                "Total Investment": st.column_config.NumberColumn(format="$%.2f"),
                "Current Value": st.column_config.NumberColumn(format="$%.2f"),
                "P/L (%)": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )


def render_financial_health(context) -> None:
    render_section_header(
        "Financial Health",
        "Balance sheet precision grid",
        "Core valuation and leverage telemetry organized for fast scanning.",
    )
    with st.container(border=True):
        fundamentals = context.fundamentals
        row_one = st.columns(4)
        row_two = st.columns(4)

        row_one[0].metric("Market Cap", format_large_number(fundamentals.market_cap), border=True)
        row_one[1].metric(
            "Enterprise Value",
            format_large_number(fundamentals.enterprise_value),
            border=True,
        )
        row_one[2].metric(
            "Debt / Equity",
            format_ratio(fundamentals.debt_to_equity, suffix=""),
            border=True,
        )
        row_one[3].metric(
            "Analyst Target",
            format_price(fundamentals.analyst_target_mean, context.quote.currency),
            border=True,
        )

        row_two[0].metric("Cash", format_large_number(fundamentals.total_cash), border=True)
        row_two[1].metric("Debt", format_large_number(fundamentals.total_debt), border=True)
        row_two[2].metric(
            "Revenue Growth",
            format_percent(fundamentals.revenue_growth, scale=100),
            border=True,
        )
        row_two[3].metric(
            "Earnings Growth",
            format_percent(fundamentals.earnings_growth, scale=100),
            border=True,
        )


def render_analyst_tape(actions) -> None:
    render_section_header(
        "Analyst Tape",
        "Ratings + desk actions",
        "Recent upgrades and downgrades pulled through yfinance when available.",
    )
    with st.container(border=True):
        if actions.empty:
            render_empty_state("No recent analyst actions were available for this symbol.")
            return
        formatted = actions.copy()
        formatted["date"] = formatted["date"].astype(str)
        st.dataframe(formatted, hide_index=True, width="stretch")


def render_stock_deep_dive(
    profile: StockProfile,
    positions,
    price_lookup: dict[str, float | None],
    auto_refresh: bool,
    refresh_seconds: int,
    settings: AlertSettings,
) -> None:
    run_every = f"{refresh_seconds}s" if auto_refresh else None

    @st.fragment(run_every=run_every)
    def live_stock_view() -> None:
        try:
            context = load_stock_context(profile)
            market = load_market_snapshot(profile.benchmark_symbol)
            headlines = load_headlines(profile)
        except Exception as exc:
            st.error(f"Live market data failed to load for {profile.symbol}: {exc}")
            return

        render_header(
            f"{context.quote.symbol} // {context.quote.display_name}",
            "Futuristic deep-dive view with live price telemetry, market context overlay, urgent sentiment, and balance-sheet precision.",
            build_status_text(auto_refresh, refresh_seconds),
        )

        alerts = build_alerts(context.quote, market, headlines, settings)
        render_alert_rail(alerts)
        render_position_summary(profile.symbol, price_lookup, positions)

        render_section_header(
            "Company Context",
            "Why this stock matters",
            "Static thesis note from the local watchlist context layer.",
        )
        with st.container(border=True):
            st.markdown(get_company_context(profile))

        urgent_insights = build_urgent_insights(context.quote, headlines)
        if urgent_insights:
            render_section_header(
                "Urgent Insight",
                "High-priority triggers",
                "Keywords, market shocks, and outsized moves that deserve immediate attention.",
            )
            render_urgent_cards(urgent_insights)

        metric_row = st.columns(4)
        metric_row[0].metric(
            "Last Price",
            format_price(context.quote.price, context.quote.currency),
            format_percent(context.quote.session_change_pct),
            border=True,
        )
        metric_row[1].metric(
            "Volume Spike",
            format_large_number(context.quote.volume),
            format_ratio(context.quote.volume_ratio),
            border=True,
        )
        metric_row[2].metric(
            "S&P 500",
            format_price(market.price, "USD"),
            format_percent(market.session_change_pct),
            border=True,
        )
        metric_row[3].metric(
            "Correlation",
            format_signed_decimal(context.market_correlation, precision=2),
            "vs S&P 500",
            border=True,
        )

        flow_col, news_col = st.columns((1.8, 1.15))
        with flow_col:
            render_section_header(
                "Market Context",
                "Intraday flow + S&P overlay",
                "Price action normalized from the open so HOVR can be compared directly with the benchmark tape.",
            )
            with st.container(border=True):
                chart = build_intraday_context_chart(
                    context.intraday_history,
                    context.benchmark_intraday_history,
                    context.quote.symbol,
                    profile.benchmark_symbol,
                )
                if chart is None:
                    render_empty_state("Intraday price series was unavailable.")
                else:
                    st.plotly_chart(
                        chart,
                        width="stretch",
                        theme=None,
                        config={"displayModeBar": False},
                    )

        with news_col:
            render_section_header(
                "News Impact",
                "Urgent news + sentiment",
                "Headline tape positioned beside price action for fast context and escalation.",
            )
            with st.container(border=True):
                sentiment_totals = headline_sentiment_totals(headlines)
                sentiment_row = st.columns(3)
                sentiment_row[0].metric("Urgent", sentiment_totals["urgent"], border=True)
                sentiment_row[1].metric("Positive", sentiment_totals["positive"], border=True)
                sentiment_row[2].metric("Neutral", sentiment_totals["neutral"], border=True)
                render_news_feed(headlines)

        health_col, tape_col = st.columns((1.35, 1.0))
        with health_col:
            render_financial_health(context)
        with tape_col:
            render_section_header(
                "Execution Rhythm",
                "Volume pulse + analyst tape",
                "Monitor volume compression or expansion while keeping the ratings stream in frame.",
            )
            with st.container(border=True):
                volume_chart = build_volume_history_chart(context.daily_history)
                if volume_chart is None:
                    render_empty_state("Daily volume history was unavailable.")
                else:
                    st.plotly_chart(
                        volume_chart,
                        width="stretch",
                        theme=None,
                        config={"displayModeBar": False},
                    )
            render_analyst_tape(context.analyst_actions)

    live_stock_view()


def render_global_portfolio(
    stock_registry: dict[str, StockProfile],
    positions,
    editor_frame: pd.DataFrame,
    price_lookup: dict[str, float | None],
    auto_refresh: bool,
    refresh_seconds: int,
) -> None:
    run_every = f"{refresh_seconds}s" if auto_refresh else None

    @st.fragment(run_every=run_every)
    def live_global_view() -> None:
        contexts = {}
        headlines_map = {}
        for profile in stock_registry.values():
            try:
                contexts[profile.symbol] = load_stock_context(profile)
                headlines_map[profile.symbol] = load_headlines(profile)
            except Exception:
                continue

        summaries = portfolio_store.build_summaries(positions, price_lookup)
        totals = portfolio_store.build_totals(summaries)
        urgent_count = 0
        for symbol, context in contexts.items():
            urgent_count += len(build_urgent_insights(context.quote, headlines_map.get(symbol, [])))

        render_header(
            "Global Portfolio",
            "Mission control across your tracked positions, sources, and urgent signal flow.",
            build_status_text(auto_refresh, refresh_seconds),
        )

        summary_row = st.columns(4)
        summary_row[0].metric(
            "Current Value",
            format_price(totals["current_value"], precision=2),
            format_currency_delta(totals["pnl_dollar"]),
            border=True,
        )
        summary_row[1].metric(
            "Invested Capital",
            format_price(totals["total_investment"], precision=2),
            f"{totals['position_count']} positions",
            border=True,
        )
        summary_row[2].metric(
            "Portfolio P/L",
            format_percent(totals["pnl_percent"]),
            f"{totals['source_count']} sources",
            border=True,
        )
        summary_row[3].metric("Urgent Signals", urgent_count, "cross-market", border=True)

        if contexts:
            render_section_header(
                "Tracked Assets",
                "Command tiles",
                "Each tracked symbol gets a dense card with price action, portfolio value, and signal load.",
            )
            symbols = list(contexts.keys())
            for chunk_start in range(0, len(symbols), 2):
                chunk = symbols[chunk_start : chunk_start + 2]
                columns = st.columns(len(chunk))
                for column, symbol in zip(columns, chunk):
                    context = contexts[symbol]
                    aggregate = portfolio_store.aggregate_symbol(summaries, symbol)
                    urgent_signals = len(build_urgent_insights(context.quote, headlines_map.get(symbol, [])))
                    sparkline = (
                        context.daily_history["Close"].dropna().tail(20).tolist()
                        if not context.daily_history.empty and "Close" in context.daily_history.columns
                        else None
                    )
                    with column:
                        with st.container(border=True):
                            render_section_header(
                                "Asset",
                                f"{context.quote.symbol} // {context.quote.display_name}",
                                "Price telemetry fused with your stored position context.",
                            )
                            st.metric(
                                "Last Price",
                                format_price(context.quote.price, context.quote.currency),
                                format_percent(context.quote.session_change_pct),
                                chart_data=sparkline,
                                chart_type="line",
                                border=True,
                            )
                            mini = st.columns(2)
                            mini[0].metric(
                                "Position Value",
                                format_price(aggregate.current_value if aggregate else None, precision=2),
                                border=True,
                            )
                            mini[1].metric(
                                "Urgent",
                                urgent_signals,
                                format_ratio(context.quote.volume_ratio),
                                border=True,
                            )
                            st.caption("Why this stock matters")
                            st.markdown(get_company_context(context.profile))

                            # Recent news links with recency filter + source + date
                            try:
                                news_service = RSSNewsService()
                                recent_headlines = news_service.fetch_headlines(context.profile.rss_queries, limit=5)
                                
                                # Filter to last 7 days only
                                cutoff = datetime.now(timezone.utc) - timedelta(days=7)
                                filtered = []
                                for h in recent_headlines:
                                    if h.published_at and h.published_at >= cutoff and h.link:
                                        filtered.append(h)
                                
                                if filtered:
                                    st.caption("Latest News (Last 7 days)")
                                    for h in filtered[:3]:
                                        title = h.title[:75] + "..." if len(h.title) > 75 else h.title
                                        source = h.source or "Unknown"
                                        days_ago = (datetime.now(timezone.utc) - h.published_at).days
                                        time_str = f"{days_ago}d ago" if days_ago > 0 else "Today"
                                        st.markdown(f"- [{title}]({h.link})  •  {source} • {time_str}")
                            except Exception:
                                pass

        render_section_header(
            "Source Allocation",
            "Capital by exchange/source",
            "Quick read on where current value is parked across brokers, wallets, and manual sources.",
        )
        with st.container(border=True):
            source_chart = build_source_exposure_chart(editor_frame)
            if source_chart is None:
                render_empty_state("Add one or more positions to visualize source allocation.")
            else:
                st.plotly_chart(
                    source_chart,
                    width="stretch",
                    theme=None,
                    config={"displayModeBar": False},
                )

    live_global_view()
    render_portfolio_editor(editor_frame)


positions = st.session_state.get("portfolio_positions")
if positions is None:
    positions = portfolio_store.load_positions()
    st.session_state["portfolio_positions"] = positions
st.session_state.setdefault("portfolio_editor_ready", bool(positions))
stock_registry = build_stock_registry(portfolio_store.tracked_symbols(positions))
selected_view = st.session_state.get("selected_view", "Global Portfolio")
if selected_view not in {"Global Portfolio", *stock_registry.keys()}:
    selected_view = "Global Portfolio"

selected_view, auto_refresh, refresh_seconds, alert_settings = render_sidebar(
    stock_registry,
    selected_view,
)

price_lookup = collect_price_lookup(stock_registry)
editor_frame = portfolio_store.build_editor_frame(positions, price_lookup)

if selected_view == "Global Portfolio":
    render_global_portfolio(
        stock_registry=stock_registry,
        positions=positions,
        editor_frame=editor_frame,
        price_lookup=price_lookup,
        auto_refresh=auto_refresh,
        refresh_seconds=refresh_seconds,
    )
else:
    selected_profile = stock_registry[selected_view]
    render_stock_deep_dive(
        profile=selected_profile,
        positions=positions,
        price_lookup=price_lookup,
        auto_refresh=auto_refresh,
        refresh_seconds=refresh_seconds,
        settings=alert_settings or AlertSettings(
            high_price_target=st.session_state.get(f"high_target_{selected_profile.symbol}", None),
            volume_spike_ratio=DEFAULT_VOLUME_SPIKE_RATIO,
            market_crash_pct=DEFAULT_CRASH_TRIGGER_PCT,
        ),
    )
