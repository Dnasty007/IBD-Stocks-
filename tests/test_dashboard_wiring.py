from __future__ import annotations

import unittest
from pathlib import Path


class DashboardWiringTests(unittest.TestCase):
    def test_stock_deep_dive_renders_company_context(self):
        app_source = Path("app.py").read_text(encoding="utf-8")

        self.assertIn("from stock_watcher.context import get_company_context", app_source)
        self.assertIn("get_company_context(profile)", app_source)
        self.assertIn("get_company_context(context.profile)", app_source)


if __name__ == "__main__":
    unittest.main()
