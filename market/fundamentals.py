"""Yahoo Finance company-fundamentals adapter for the HELIX desktop UI."""

import math

import yfinance as yf


def _statement_value(statement, labels, column):
    """Return the first available Yahoo Finance row matching one of *labels*."""
    if statement is None or statement.empty:
        return None
    for label in labels:
        if label in statement.index:
            value = statement.loc[label, column]
            if value is not None and not _is_nan(value):
                return float(value)
    return None


def _is_nan(value):
    try:
        return math.isnan(value)
    except (TypeError, ValueError):
        return False


def _periods(statement, count=4):
    if statement is None or statement.empty:
        return []
    return list(statement.columns[:count])


def _year_label(period):
    return str(period.year) if hasattr(period, "year") else str(period)[:4]


def _series(statement, labels, periods):
    values = [
        {"period": _year_label(period), "value": _statement_value(statement, labels, period)}
        for period in periods
    ]
    for index, item in enumerate(values):
        previous = values[index + 1]["value"] if index + 1 < len(values) else None
        current = item["value"]
        item["yoy"] = ((current / previous) - 1) * 100 if current is not None and previous not in (None, 0) else None
    return values


def get_company_financials(ticker):
    """Return a compact, annual financial profile for a ticker.

    Yahoo Finance can omit rows for some companies; missing figures are returned
    as ``None`` so the page can label them clearly rather than invent values.
    """
    symbol = ticker.strip().upper()
    if not symbol:
        raise ValueError("Enter a ticker symbol, such as AAPL or MSFT.")

    company = yf.Ticker(symbol)
    income = company.income_stmt
    balance = company.balance_sheet
    cash_flow = company.cashflow
    periods = _periods(income)
    if not periods:
        raise ValueError(f"No annual financial statements were found for {symbol}.")

    revenue = _series(income, ("Total Revenue",), periods)
    net_income = _series(income, ("Net Income", "Net Income Common Stockholders"), periods)
    operating_income = _series(income, ("Operating Income",), periods)
    latest_revenue = revenue[0]["value"]
    latest_income = net_income[0]["value"]
    margin = (latest_income / latest_revenue * 100) if latest_revenue and latest_income is not None else None

    balance_periods = _periods(balance)
    cash_periods = _periods(cash_flow)
    return {
        "ticker": symbol,
        "periods": [entry["period"] for entry in revenue],
        "income": {
            "revenue": revenue,
            "net_income": net_income,
            "operating_income": operating_income,
            "net_margin": margin,
        },
        "balance": {
            "periods": [_year_label(period) for period in balance_periods],
            "cash": _series(balance, ("Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"), balance_periods),
            "total_assets": _series(balance, ("Total Assets",), balance_periods),
            "total_debt": _series(balance, ("Total Debt",), balance_periods),
            "total_liabilities": _series(balance, ("Total Liabilities Net Minority Interest", "Total Liabilities"), balance_periods),
            "equity": _series(balance, ("Stockholders Equity", "Total Equity Gross Minority Interest"), balance_periods),
        },
        "cash_flow": {
            "periods": [_year_label(period) for period in cash_periods],
            "operating": _series(cash_flow, ("Operating Cash Flow", "Total Cash From Operating Activities"), cash_periods),
            "capital_expenditure": _series(cash_flow, ("Capital Expenditure",), cash_periods),
            "free_cash_flow": _series(cash_flow, ("Free Cash Flow",), cash_periods),
            "investing": _series(cash_flow, ("Investing Cash Flow", "Total Cashflows From Investing Activities"), cash_periods),
            "financing": _series(cash_flow, ("Financing Cash Flow", "Total Cash From Financing Activities"), cash_periods),
        },
    }
