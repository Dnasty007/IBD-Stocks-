from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st

from stock_watcher.models import AlertEvent, Headline, UrgentInsight


APP_CSS = """
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap");

:root {
  --bg: #0E1117;
  --panel: rgba(17, 24, 33, 0.72);
  --panel-strong: rgba(19, 28, 39, 0.92);
  --border: rgba(104, 149, 184, 0.18);
  --text: #E7EEF7;
  --muted: #90A4B8;
  --cyan: #35F2FF;
  --red: #FF4D6D;
  --cyan-soft: rgba(53, 242, 255, 0.14);
  --red-soft: rgba(255, 77, 109, 0.12);
}

html, body, [class*="css"] {
  font-family: "Inter", "Segoe UI", sans-serif;
}

[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at top left, rgba(53, 242, 255, 0.08), transparent 30%),
    radial-gradient(circle at top right, rgba(255, 77, 109, 0.08), transparent 24%),
    linear-gradient(180deg, #0A0F14 0%, var(--bg) 28%, #090C11 100%);
  color: var(--text);
}

[data-testid="stHeader"] {
  background: rgba(0, 0, 0, 0);
}

[data-testid="stToolbar"] {
  visibility: hidden;
  height: 0;
  position: fixed;
}

footer,
[data-testid="stAppDeployButton"],
[data-testid="stStatusWidget"] {
  display: none !important;
}

.block-container {
  padding-top: 0.9rem;
  padding-bottom: 1rem;
  padding-left: 1.15rem;
  padding-right: 1.15rem;
  max-width: 100%;
}

[data-testid="stSidebar"] {
  background:
    linear-gradient(180deg, rgba(9, 12, 17, 0.97), rgba(14, 17, 23, 0.94)),
    #0B1016;
  border-right: 1px solid rgba(53, 242, 255, 0.1);
}

[data-testid="stSidebar"] .block-container {
  padding-top: 1rem;
  padding-left: 0.9rem;
  padding-right: 0.9rem;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 20px;
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.22);
  backdrop-filter: blur(16px);
}

div[data-testid="stMetric"] {
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  border: 1px solid rgba(104, 149, 184, 0.14);
  border-radius: 4px;
  padding: 0.6rem 0.65rem;
}

div[data-testid="stMetricLabel"],
div[data-testid="stMetricValue"],
[data-testid="stMetricDelta"],
div[data-testid="stDataFrame"] *,
[data-baseweb="input"] input,
[data-baseweb="input"] textarea,
[data-baseweb="select"] *,
.stNumberInput input,
.stDataEditor * {
  font-family: "JetBrains Mono", "Source Code Pro", monospace !important;
}

div[data-testid="stMetricValue"] {
  letter-spacing: -0.03em;
}

div[data-testid="stDataFrame"] {
  border-radius: 16px;
  overflow: hidden;
}

div[data-testid="stMarkdownContainer"] p {
  color: var(--text);
}

[data-testid="stSidebar"] [role="radiogroup"] label {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(104, 149, 184, 0.14);
  border-radius: 14px;
  margin-bottom: 0.45rem;
  padding: 0.1rem 0.2rem;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
  border-color: rgba(53, 242, 255, 0.34);
}

[data-testid="stSidebar"] .stButton > button,
.stButton > button {
  border-radius: 14px;
  border: 1px solid rgba(53, 242, 255, 0.2);
  background: linear-gradient(180deg, rgba(53, 242, 255, 0.14), rgba(53, 242, 255, 0.04));
  color: var(--text);
}

[data-testid="stSidebar"] .stButton > button:hover,
.stButton > button:hover {
  border-color: rgba(53, 242, 255, 0.46);
  box-shadow: 0 0 0 1px rgba(53, 242, 255, 0.12) inset, 0 0 20px rgba(53, 242, 255, 0.12);
}

.command-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  padding: 0.1rem 0 0.2rem;
}

.command-kicker {
  color: var(--cyan);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  margin-bottom: 0.45rem;
}

.command-title {
  color: var(--text);
  font-size: 2rem;
  line-height: 1.02;
  font-weight: 700;
  margin: 0;
}

.command-subtitle {
  color: var(--muted);
  font-size: 0.98rem;
  margin-top: 0.55rem;
  max-width: 54rem;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  border-radius: 999px;
  border: 1px solid rgba(53, 242, 255, 0.18);
  background: rgba(53, 242, 255, 0.09);
  color: var(--text);
  padding: 0.5rem 0.8rem;
  font-family: "JetBrains Mono", monospace;
  font-size: 0.82rem;
  white-space: nowrap;
}

.heartbeat-dot {
  width: 0.72rem;
  height: 0.72rem;
  border-radius: 999px;
  background: var(--cyan);
  box-shadow: 0 0 0 0 rgba(53, 242, 255, 0.7);
  animation: heartbeatPulse 1.65s infinite;
}

.section-header {
  margin-bottom: 0.8rem;
}

.section-title {
  color: var(--text);
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0.15rem 0;
}

.section-copy {
  color: var(--muted);
  font-size: 0.92rem;
}

.alert-rail,
.urgent-grid {
  display: grid;
  gap: 0.75rem;
}

.alert-chip,
.urgent-card,
.news-item {
  border-radius: 16px;
  border: 1px solid rgba(104, 149, 184, 0.16);
  background: rgba(255, 255, 255, 0.02);
  padding: 0.9rem 1rem;
}

.alert-chip.critical,
.urgent-card.critical,
.news-item.critical {
  border-color: rgba(255, 77, 109, 0.36);
  background: rgba(255, 77, 109, 0.08);
  box-shadow: 0 0 30px rgba(255, 77, 109, 0.12);
}

.alert-chip.warning,
.urgent-card.warning,
.news-item.warning {
  border-color: rgba(255, 118, 136, 0.32);
}

.alert-chip.positive,
.urgent-card.positive,
.news-item.positive {
  border-color: rgba(53, 242, 255, 0.32);
  background: rgba(53, 242, 255, 0.08);
}

.pulse-border {
  animation: pulseBorder 1.7s infinite;
}

.urgent-panel {
  border: 2px solid rgba(255, 77, 109, 0.70);
  box-shadow: 0 0 32px rgba(255, 77, 109, 0.18);
  border-radius: 16px;
  padding: 0.9rem;
}

.insight-title,
.news-title {
  color: var(--text);
  font-weight: 600;
  line-height: 1.35;
}

.news-title a,
.insight-title a {
  color: inherit;
  text-decoration: none;
}

.news-title a:hover,
.insight-title a:hover {
  color: var(--cyan);
}

.card-meta,
.news-meta {
  color: var(--muted);
  font-family: "JetBrains Mono", monospace;
  font-size: 0.78rem;
  margin-top: 0.5rem;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.6rem;
}

.tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.22rem 0.58rem;
  font-family: "JetBrains Mono", monospace;
  font-size: 0.72rem;
  background: rgba(255,255,255,0.05);
  color: var(--text);
}

.tag.urgent {
  background: rgba(255, 77, 109, 0.14);
  color: #FFD6DE;
}

.tag.positive {
  background: rgba(53, 242, 255, 0.16);
  color: #C9FCFF;
}

.tag.neutral {
  background: rgba(144, 164, 184, 0.16);
  color: #D9E5F0;
}

.waiting-indicator {
  color: var(--muted);
  font-family: "JetBrains Mono", monospace;
  font-size: 0.88rem;
  letter-spacing: 0.12em;
  animation: waitingPulse 1.8s ease-in-out infinite;
}

.sidebar-brand {
  margin-bottom: 1rem;
  padding: 0.2rem 0 0.75rem;
  border-bottom: 1px solid rgba(104, 149, 184, 0.12);
}

.sidebar-brand .headline {
  color: var(--text);
  font-size: 1.15rem;
  font-weight: 700;
  margin-top: 0.3rem;
}

.sidebar-brand .caption {
  color: var(--muted);
  font-size: 0.84rem;
  margin-top: 0.3rem;
}

.empty-state {
  border-radius: 16px;
  border: 1px dashed rgba(104, 149, 184, 0.24);
  background: rgba(255, 255, 255, 0.015);
  padding: 1rem;
  color: var(--muted);
}

@keyframes heartbeatPulse {
  0% { box-shadow: 0 0 0 0 rgba(53, 242, 255, 0.7); }
  70% { box-shadow: 0 0 0 12px rgba(53, 242, 255, 0.0); }
  100% { box-shadow: 0 0 0 0 rgba(53, 242, 255, 0.0); }
}

@keyframes pulseBorder {
  0% { box-shadow: 0 0 0 0 rgba(255, 77, 109, 0.38); }
  70% { box-shadow: 0 0 0 8px rgba(255, 77, 109, 0.0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 77, 109, 0.0); }
}

@keyframes waitingPulse {
  0% { opacity: 0.45; }
  50% { opacity: 0.9; }
  100% { opacity: 0.45; }
}
</style>
"""


def inject_styles() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_sidebar_brand() -> None:
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
          <div class="command-kicker">Financial Command Center</div>
          <div class="headline">Neon telemetry for live market monitoring</div>
          <div class="caption">Dark-mode tactical board with portfolio, alerts, and sentiment.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: str, status_text: str) -> None:
    st.markdown(
        f"""
        <div class="command-header">
          <div>
            <div class="command-kicker">Live Operations</div>
            <div class="command-title">{escape(title)}</div>
            <div class="command-subtitle">{escape(subtitle)}</div>
          </div>
          <div class="status-pill"><span class="heartbeat-dot"></span>{escape(status_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="section-header">
          <div class="command-kicker">{escape(kicker)}</div>
          <div class="section-title">{escape(title)}</div>
          <div class="section-copy">{escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alert_rail(alerts: Sequence[AlertEvent]) -> None:
    if not alerts:
        st.markdown(
            '<div class="empty-state">System calm. No active command-level alerts are firing right now.</div>',
            unsafe_allow_html=True,
        )
        return

    cards = []
    for alert in alerts:
        cards.append(
            f'<div class="alert-chip {escape(alert.severity)}">'
            f'<div class="insight-title">{escape(alert.message)}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="alert-rail">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def render_urgent_cards(insights: Sequence[UrgentInsight]) -> None:
    cards = []
    for insight in insights:
        title = escape(insight.title)
        if insight.link:
            title = f'<a href="{escape(insight.link, quote=True)}" target="_blank">{title}</a>'
        cards.append(
            f'<div class="urgent-card {escape(insight.severity)} pulse-border">'
            f'<div class="tag-row"><span class="tag urgent">{escape(insight.category)}</span></div>'
            f'<div class="insight-title">{title}</div>'
            f'<div class="card-meta">{escape(insight.detail)}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="urgent-panel pulse-border"><div class="urgent-grid">{"".join(cards)}</div></div>',
        unsafe_allow_html=True,
    )


def render_news_feed(headlines: Sequence[Headline]) -> None:
    if not headlines:
        st.markdown(
            '<div class="empty-state">No RSS headlines returned for this symbol.</div>',
            unsafe_allow_html=True,
        )
        return

    for headline in headlines:
        classes = ["news-item"]
        if headline.is_urgent:
            classes.extend([headline.sentiment if headline.sentiment in {"critical", "warning", "positive"} else "critical", "pulse-border"])
        elif headline.is_upgrade:
            classes.append("positive")

        tags = []
        if headline.is_upgrade:
            tags.append('<span class="tag positive">Upgrade</span>')
        if headline.is_urgent:
            for keyword in headline.matched_keywords or ("Price Swing",):
                tags.append(f'<span class="tag urgent">{escape(keyword.title())}</span>')

        st.markdown(
            f"""
            <div class="{' '.join(classes)}">
              <div class="news-title">
                <a href="{escape(headline.link, quote=True)}" target="_blank">{escape(headline.title)}</a>
              </div>
              <div class="news-meta">{escape(headline.source or 'Unknown source')}</div>
              {'<div class="tag-row">' + ''.join(tags) + '</div>' if tags else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_empty_state(message: str) -> None:
    st.markdown(
        f'<div class="empty-state">{escape(message)}</div>',
        unsafe_allow_html=True,
    )


def render_waiting_indicator(message: str = "---") -> None:
    st.markdown(
        f'<div class="waiting-indicator">{escape(message)}</div>',
        unsafe_allow_html=True,
    )
