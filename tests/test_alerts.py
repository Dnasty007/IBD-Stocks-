from __future__ import annotations

import unittest
from datetime import UTC, datetime

from stock_watcher.alerts import build_alerts
from stock_watcher.models import (
    AlertSettings,
    Headline,
    MarketSnapshot,
    PriceSnapshot,
)


class BuildAlertsTests(unittest.TestCase):
    def make_quote(self, *, price=1.40, volume_ratio=2.5, session_change_pct=16.67):
        return PriceSnapshot(
            symbol="HOVR",
            display_name="New Horizon Aircraft",
            currency="USD",
            price=price,
            previous_close=1.20,
            open_price=1.22,
            day_high=1.45,
            day_low=1.18,
            fifty_two_week_high=2.25,
            fifty_two_week_low=0.82,
            volume=1_000_000,
            average_volume_30d=400_000,
            volume_ratio=volume_ratio,
            session_change_pct=session_change_pct,
        )

    def make_market(self, *, session_change_pct=-3.5):
        return MarketSnapshot(
            symbol="^GSPC",
            price=5000,
            previous_close=5200,
            session_change_pct=session_change_pct,
        )

    def make_headline(self, *, is_upgrade=True):
        return Headline(
            title="Analyst upgrades HOVR after target raise",
            link="https://example.com/hovr-upgrade",
            source="Example Wire",
            published_at=datetime(2026, 4, 27, tzinfo=UTC),
            is_upgrade=is_upgrade,
        )

    def test_all_primary_alerts_can_fire_together(self):
        alerts = build_alerts(
            self.make_quote(),
            self.make_market(),
            [self.make_headline()],
            AlertSettings(
                high_price_target=1.35,
                volume_spike_ratio=2.0,
                market_crash_pct=-3.0,
            ),
        )

        self.assertEqual({alert.name for alert in alerts}, {
            "high_price",
            "volume_spike",
            "market_crash",
            "price_shock",
            "urgent_news",
            "upgrade_news",
        })

    def test_no_alerts_fire_when_thresholds_are_not_met(self):
        alerts = build_alerts(
            self.make_quote(price=1.20, volume_ratio=1.1, session_change_pct=4.25),
            self.make_market(session_change_pct=-0.8),
            [self.make_headline(is_upgrade=False)],
            AlertSettings(
                high_price_target=1.35,
                volume_spike_ratio=2.0,
                market_crash_pct=-3.0,
            ),
        )

        self.assertEqual(alerts, [])


if __name__ == "__main__":
    unittest.main()
