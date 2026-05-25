from __future__ import annotations

import unittest

from stock_watcher.config import DEFAULT_BENCHMARK_SYMBOL, build_stock_registry


class StockRegistryTests(unittest.TestCase):
    def test_hut_is_default_watched_stock(self):
        registry = build_stock_registry()

        hut = registry["HUT"]
        self.assertEqual(hut.symbol, "HUT")
        self.assertEqual(hut.display_name, "Hut 8 Corp")
        self.assertEqual(hut.benchmark_symbol, DEFAULT_BENCHMARK_SYMBOL)
        self.assertIn('"Hut 8 Corp" stock', hut.rss_queries)
        self.assertIn('"Hut 8 Corp" analyst', hut.rss_queries)

    def test_rklb_is_default_watched_stock(self):
        registry = build_stock_registry()

        rklb = registry["RKLB"]
        self.assertEqual(rklb.symbol, "RKLB")
        self.assertEqual(rklb.display_name, "Rocket Lab")
        self.assertEqual(rklb.benchmark_symbol, DEFAULT_BENCHMARK_SYMBOL)
        self.assertIn('"Rocket Lab" stock', rklb.rss_queries)
        self.assertIn('"Rocket Lab" analyst', rklb.rss_queries)


if __name__ == "__main__":
    unittest.main()
