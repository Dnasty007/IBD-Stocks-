from __future__ import annotations

from stock_watcher.models import StockProfile


def get_company_context(profile: StockProfile) -> str:
    """
    Returns a short, useful context blurb about why this stock might matter.
    This is a starting point — we can make it dynamic later.
    """
    contexts = {
        "HOVR": "New Horizon Aircraft — small-cap aerospace play with potential defense/gov contracts.",
        "HUT": "Hut 8 — Bitcoin mining + high-performance computing exposure.",
        "RKLB": "Rocket Lab — small-launch leader with growing constellation and space systems business.",
    }
    return contexts.get(profile.symbol, f"{profile.display_name} — high-conviction name from recent IBD lists.")