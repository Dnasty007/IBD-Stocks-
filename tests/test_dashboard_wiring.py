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


if __name__ == "__main__":
    unittest.main()
