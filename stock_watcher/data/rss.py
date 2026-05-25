from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import quote_plus
from xml.etree import ElementTree

import requests

from stock_watcher.config import ANALYST_UPGRADE_KEYWORDS, PRICE_SWING_URGENT_PCT, URGENT_NEWS_KEYWORDS
from stock_watcher.models import Headline


class RSSNewsService:
    base_url = "https://news.google.com/rss/search"
    move_pattern = re.compile(r"([+-]?\d+(?:\.\d+)?)%")

    def build_feed_url(self, query: str) -> str:
        encoded_query = quote_plus(query)
        return (
            f"{self.base_url}?q={encoded_query}"
            "&hl=en-US&gl=US&ceid=US:en"
        )

    def fetch_headlines(self, queries: Sequence[str], limit: int = 10) -> list[Headline]:
        headlines: list[Headline] = []
        seen: set[tuple[str, str]] = set()

        for query in queries:
            feed_url = self.build_feed_url(query)
            for headline in self._fetch_feed(feed_url):
                key = (headline.title, headline.link)
                if key in seen:
                    continue
                seen.add(key)
                headlines.append(headline)

        headlines.sort(
            key=lambda item: item.published_at or datetime(1970, 1, 1, tzinfo=UTC),
            reverse=True,
        )
        return headlines[:limit]

    def _fetch_feed(self, url: str) -> list[Headline]:
        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "StockWatcher/1.0"},
        )
        response.raise_for_status()
        root = ElementTree.fromstring(response.text)

        items: list[Headline] = []
        for item in root.findall(".//item"):
            title = unescape((item.findtext("title") or "").strip())
            link = (item.findtext("link") or "").strip()
            source = (item.findtext("source") or "").strip() or self._extract_source(title)
            published_at = self._parse_pub_date(item.findtext("pubDate"))
            matched_keywords = self._extract_urgent_keywords(title)
            move_pct = self._extract_move_pct(title)
            is_upgrade = self._is_upgrade_headline(title)
            is_urgent = bool(matched_keywords) or (
                move_pct is not None and abs(move_pct) >= PRICE_SWING_URGENT_PCT
            )
            items.append(
                Headline(
                    title=title,
                    link=link,
                    source=source,
                    published_at=published_at,
                    is_upgrade=is_upgrade,
                    matched_keywords=matched_keywords,
                    move_pct=move_pct,
                    is_urgent=is_urgent,
                    sentiment=self._classify_sentiment(is_upgrade, matched_keywords),
                )
            )

        return items

    def _parse_pub_date(self, raw_value: str | None) -> datetime | None:
        if not raw_value:
            return None
        parsed = parsedate_to_datetime(raw_value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed

    def _extract_source(self, title: str) -> str | None:
        parts = title.rsplit(" - ", maxsplit=1)
        if len(parts) == 2:
            return parts[1].strip()
        return None

    def _is_upgrade_headline(self, title: str) -> bool:
        normalized = title.lower()
        if "downgrade" in normalized or "downgraded" in normalized:
            return False
        return any(keyword in normalized for keyword in ANALYST_UPGRADE_KEYWORDS)

    def _extract_urgent_keywords(self, title: str) -> tuple[str, ...]:
        normalized = title.lower()
        matches = [keyword for keyword in URGENT_NEWS_KEYWORDS if keyword in normalized]
        return tuple(matches)

    def _extract_move_pct(self, title: str) -> float | None:
        matches = self.move_pattern.findall(title)
        if not matches:
            return None
        values = []
        for match in matches:
            try:
                values.append(float(match))
            except ValueError:
                continue
        if not values:
            return None
        return max(values, key=abs)

    def _classify_sentiment(
        self,
        is_upgrade: bool,
        matched_keywords: tuple[str, ...],
    ) -> str:
        if matched_keywords:
            if any(keyword in {"bankruptcy", "dilution", "offering", "delisting", "lawsuit"} for keyword in matched_keywords):
                return "negative"
            return "urgent"
        if is_upgrade:
            return "positive"
        return "neutral"
