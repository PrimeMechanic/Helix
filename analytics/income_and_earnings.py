"""Dividend-income estimates and earnings dates for HELIX holdings."""

from datetime import datetime

import yfinance as yf

from portfolio_manager import load_portfolio


def _calendar_value(calendar, key):
    if calendar is None:
        return None
    if isinstance(calendar, dict):
        value = calendar.get(key)
    else:
        try:
            value = calendar.loc[key].iloc[0] if key in calendar.index else None
        except (AttributeError, IndexError, KeyError):
            value = None
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


def _format_date(value):
    if value is None:
        return "Unavailable"
    if isinstance(value, datetime):
        return value.strftime("%b %d, %Y")
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime().strftime("%b %d, %Y")
    return str(value)[:16]


def get_income_and_earnings(portfolio=None):
    """Return per-holding dividend estimates and reported earnings dates."""
    portfolio = load_portfolio() if portfolio is None else portfolio
    rows = []
    total_income = 0.0
    for ticker, position in portfolio.items():
        try:
            company = yf.Ticker(ticker)
            dividends = company.dividends
            cutoff = datetime.now().astimezone().replace(tzinfo=None).timestamp() - 365 * 24 * 60 * 60
            trailing_dividend = float(dividends[dividends.index.map(lambda day: day.timestamp()) >= cutoff].sum()) if not dividends.empty else 0.0
            estimated_income = trailing_dividend * position["shares"]
            total_income += estimated_income
            calendar = company.calendar
            rows.append({
                "ticker": ticker,
                "annual_dividend": trailing_dividend,
                "estimated_income": estimated_income,
                "earnings_date": _format_date(_calendar_value(calendar, "Earnings Date")),
                "earnings_estimate": _calendar_value(calendar, "Earnings Average"),
            })
        except Exception:
            rows.append({
                "ticker": ticker,
                "annual_dividend": None,
                "estimated_income": None,
                "earnings_date": "Unavailable",
                "earnings_estimate": None,
            })
    return {"annual_income": total_income, "holdings": rows}
