from __future__ import annotations

import unittest
from pathlib import Path


class DashboardWiringTests(unittest.TestCase):
    def test_stock_deep_dive_renders_company_context(self):
        app_source = Path("app.py").read_text(encoding="utf-8")

        self.assertIn("from stock_watcher.context import get_company_context", app_source)
        self.assertIn("get_company_context(profile)", app_source)
        self.assertIn("get_company_context(context.profile)", app_source)

    def test_global_alert_badges_use_loaded_market_snapshot(self):
        app_source = Path("app.py").read_text(encoding="utf-8")

        self.assertIn("market_snapshots = {}", app_source)
        self.assertIn("market = market_snapshots.get(symbol)", app_source)
        self.assertNotIn("except Exception:\n                                pass", app_source)

    def test_news_color_coding_stays_inside_recent_news_loop(self):
        app_source = Path("app.py").read_text(encoding="utf-8")

        self.assertIn(
            'for headline, published_at in filtered[:3]:\n'
            '                                    title = headline.title[:75] + "..." if len(headline.title) > 75 else headline.title\n'
            '                                    source = headline.source or "Unknown"\n'
            '                                    days_ago = (datetime.now(timezone.utc) - published_at).days\n'
            '                                    time_str = f"{days_ago}d ago" if days_ago > 0 else "Today"\n'
            '                                    if headline.is_urgent or headline.sentiment == "negative":',
            app_source,
        )
        self.assertNotIn("\n                        if headline.is_urgent", app_source)


if __name__ == "__main__":
    unittest.main()
