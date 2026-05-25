from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from stock_watcher.config import PORTFOLIO_STORAGE_PATH
from stock_watcher.models import PortfolioPosition, PortfolioPositionSummary

EDITOR_COLUMNS = [
    "Ticker",
    "Quantity Owned",
    "Average Cost",
    "Total Investment",
    "Current Value",
    "P/L (%)",
    "Exchange/Source",
]


class PortfolioStore:
    def __init__(self, storage_path: Path = PORTFOLIO_STORAGE_PATH) -> None:
        self.storage_path = storage_path

    def ensure_storage_exists(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text('{"positions": []}', encoding="utf-8")

    def load_positions(self) -> list[PortfolioPosition]:
        self.ensure_storage_exists()
        raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
        positions: list[PortfolioPosition] = []
        for item in raw.get("positions", []):
            symbol = str(item.get("symbol", "")).strip().upper()
            if not symbol:
                continue
            positions.append(
                PortfolioPosition(
                    symbol=symbol,
                    quantity=float(item.get("quantity", 0) or 0),
                    average_cost=float(item.get("average_cost", 0) or 0),
                    source=str(item.get("source", "Manual") or "Manual"),
                )
            )
        return positions

    def save_positions(self, positions: list[PortfolioPosition]) -> None:
        self.ensure_storage_exists()
        payload = {
            "positions": [
                {
                    "symbol": position.symbol,
                    "quantity": position.quantity,
                    "average_cost": position.average_cost,
                    "source": position.source,
                }
                for position in positions
            ]
        }
        self.storage_path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    def build_editor_frame(
        self,
        positions: list[PortfolioPosition],
        price_lookup: dict[str, float | None],
    ) -> pd.DataFrame:
        summaries = self.build_summaries(positions, price_lookup)
        rows = [
            {
                "Ticker": summary.symbol,
                "Quantity Owned": summary.quantity,
                "Average Cost": summary.average_cost,
                "Total Investment": summary.total_investment,
                "Current Value": summary.current_value,
                "P/L (%)": summary.pnl_percent,
                "Exchange/Source": summary.source,
            }
            for summary in summaries
        ]
        if not rows:
            return pd.DataFrame(columns=EDITOR_COLUMNS)
        return pd.DataFrame(rows, columns=EDITOR_COLUMNS)

    def positions_from_editor_frame(self, frame: pd.DataFrame) -> list[PortfolioPosition]:
        positions: list[PortfolioPosition] = []
        working = frame.fillna("")
        for _, row in working.iterrows():
            symbol = str(row.get("Ticker", "")).strip().upper()
            if not symbol:
                continue
            quantity = self._safe_float(row.get("Quantity Owned"))
            average_cost = self._safe_float(row.get("Average Cost"))
            if quantity <= 0:
                continue
            positions.append(
                PortfolioPosition(
                    symbol=symbol,
                    quantity=quantity,
                    average_cost=max(average_cost, 0.0),
                    source=str(row.get("Exchange/Source", "Manual") or "Manual").strip() or "Manual",
                )
            )
        return positions

    def build_summaries(
        self,
        positions: list[PortfolioPosition],
        price_lookup: dict[str, float | None],
    ) -> list[PortfolioPositionSummary]:
        summaries: list[PortfolioPositionSummary] = []
        for position in positions:
            current_price = price_lookup.get(position.symbol)
            total_investment = position.quantity * position.average_cost
            current_value = (
                position.quantity * current_price if current_price is not None else None
            )
            pnl_dollar = (
                current_value - total_investment if current_value is not None else None
            )
            pnl_percent = None
            if total_investment and pnl_dollar is not None:
                pnl_percent = (pnl_dollar / total_investment) * 100

            summaries.append(
                PortfolioPositionSummary(
                    symbol=position.symbol,
                    source=position.source,
                    quantity=position.quantity,
                    average_cost=position.average_cost,
                    total_investment=total_investment,
                    current_price=current_price,
                    current_value=current_value,
                    pnl_percent=pnl_percent,
                    pnl_dollar=pnl_dollar,
                )
            )

        summaries.sort(key=lambda item: (item.symbol, item.source))
        return summaries

    def summaries_for_symbol(
        self,
        positions: list[PortfolioPosition],
        symbol: str,
        price_lookup: dict[str, float | None],
    ) -> list[PortfolioPositionSummary]:
        matching = [position for position in positions if position.symbol == symbol]
        return self.build_summaries(matching, price_lookup)

    def aggregate_symbol(
        self,
        summaries: list[PortfolioPositionSummary],
        symbol: str,
    ) -> PortfolioPositionSummary | None:
        matching = [summary for summary in summaries if summary.symbol == symbol]
        if not matching:
            return None

        quantity = sum(summary.quantity for summary in matching)
        total_investment = sum(summary.total_investment for summary in matching)
        current_value = (
            sum(summary.current_value for summary in matching if summary.current_value is not None)
            if any(summary.current_value is not None for summary in matching)
            else None
        )
        average_cost = (total_investment / quantity) if quantity else 0.0
        current_price = (
            (current_value / quantity) if current_value is not None and quantity else None
        )
        pnl_dollar = (
            current_value - total_investment if current_value is not None else None
        )
        pnl_percent = None
        if total_investment and pnl_dollar is not None:
            pnl_percent = (pnl_dollar / total_investment) * 100

        return PortfolioPositionSummary(
            symbol=symbol,
            source=" / ".join(sorted({summary.source for summary in matching})),
            quantity=quantity,
            average_cost=average_cost,
            total_investment=total_investment,
            current_price=current_price,
            current_value=current_value,
            pnl_percent=pnl_percent,
            pnl_dollar=pnl_dollar,
        )

    def build_totals(
        self,
        summaries: list[PortfolioPositionSummary],
    ) -> dict[str, float | int | None]:
        total_investment = sum(summary.total_investment for summary in summaries)
        current_values = [summary.current_value for summary in summaries if summary.current_value is not None]
        current_value = sum(current_values) if current_values else None
        pnl_dollar = (
            current_value - total_investment if current_value is not None else None
        )
        pnl_percent = None
        if total_investment and pnl_dollar is not None:
            pnl_percent = (pnl_dollar / total_investment) * 100

        return {
            "total_investment": total_investment,
            "current_value": current_value,
            "pnl_dollar": pnl_dollar,
            "pnl_percent": pnl_percent,
            "position_count": len(summaries),
            "source_count": len({summary.source for summary in summaries}),
        }

    def tracked_symbols(self, positions: list[PortfolioPosition]) -> list[str]:
        return sorted({position.symbol for position in positions})

    def _safe_float(self, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
