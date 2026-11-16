"""Presentation helpers shared by the HELIX desktop pages."""

from analytics.ai_analysis import get_portfolio_analysis
from market.market_data import get_daily_change


def load_dashboard_data():
    """Return analysis plus a portfolio-level daily movement when quotes exist."""
    analysis = get_portfolio_analysis()
    if not analysis:
        return None

    today_change = 0.0
    quote_count = 0
    for position in analysis["positions"]:
        change = get_daily_change(position["ticker"])
        if change is None:
            continue
        today_change += change["dollar"] * position["shares"]
        quote_count += 1
    analysis["today_change"] = today_change if quote_count == len(analysis["positions"]) else None
    from integrations.holdings import portfolio_source
    analysis["holdings_source"] = portfolio_source()
    return analysis
