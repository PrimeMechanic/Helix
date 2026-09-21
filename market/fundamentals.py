"""Yahoo Finance company-fundamentals adapter for the HELIX desktop UI."""

import math

import yfinance as yf


def _latest(series):
    """Return the newest statement value from one of HELIX's annual series."""
    return series[0]["value"] if series else None


def _has_reported_value(series):
    return any(item["value"] is not None for item in series)


def _ratio(numerator, denominator):
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def _bounded(value):
    return max(0, min(100, round(value)))


def _band(score):
    if score >= 80:
        return "Strong"
    if score >= 65:
        return "Healthy"
    if score >= 50:
        return "Mixed"
    return "Needs attention"


def _assessment(score):
    if score >= 75:
        return "Strong"
    if score >= 55:
        return "Balanced"
    return "Needs attention"


def _metric(label, value, display, note=None):
    return {"label": label, "value": value, "display": display, "note": note}


def _percent(value):
    return "Unavailable" if value is None else f"{value * 100:.1f}%"


def _number(value):
    return "Unavailable" if value is None else f"{value:.2f}"


def _health_profile(financials, company_info):
    """Build an explainable, sector-aware research score from annual data.

    This intentionally uses visible rules instead of an opaque prediction.  It is
    a financial-condition snapshot, not an estimate of future returns.
    """
    sector = company_info.get("sector") or "Other"
    industry = company_info.get("industry") or "Unavailable"
    income = financials["income"]
    balance = financials["balance"]
    cash_flow = financials["cash_flow"]

    revenue = _latest(income["revenue"])
    net_income = _latest(income["net_income"])
    operating_income = _latest(income["operating_income"])
    assets = _latest(balance["total_assets"])
    equity = _latest(balance["equity"])
    debt = _latest(balance["total_debt"])
    cash = _latest(balance["cash"])
    current_assets = _latest(balance["current_assets"])
    current_liabilities = _latest(balance["current_liabilities"])
    operating_cash = _latest(cash_flow["operating"])
    free_cash = _latest(cash_flow["free_cash_flow"])

    revenue_growth = income["revenue"][0].get("yoy") if income["revenue"] else None
    income_growth = income["net_income"][0].get("yoy") if income["net_income"] else None
    net_margin = _ratio(net_income, revenue)
    operating_margin = _ratio(operating_income, revenue)
    roa = _ratio(net_income, assets)
    roe = _ratio(net_income, equity)
    debt_to_equity = _ratio(debt, equity)
    current_ratio = _ratio(current_assets, current_liabilities)
    cash_to_debt = _ratio(cash, debt)
    fcf_margin = _ratio(free_cash, revenue)
    cash_conversion = _ratio(operating_cash, net_income)

    def score_growth():
        points = []
        if revenue_growth is not None:
            points.append(85 if revenue_growth >= 15 else 70 if revenue_growth >= 5 else 50 if revenue_growth >= 0 else 25)
        if income_growth is not None:
            points.append(85 if income_growth >= 15 else 70 if income_growth >= 5 else 50 if income_growth >= 0 else 25)
        return round(sum(points) / len(points)) if points else None

    def score_profitability():
        points = []
        if net_margin is not None:
            points.append(90 if net_margin >= .20 else 75 if net_margin >= .10 else 58 if net_margin >= .03 else 25)
        if operating_margin is not None:
            points.append(85 if operating_margin >= .20 else 70 if operating_margin >= .10 else 55 if operating_margin >= 0 else 25)
        if roe is not None:
            points.append(85 if roe >= .20 else 70 if roe >= .12 else 55 if roe >= .06 else 35)
        return round(sum(points) / len(points)) if points else None

    def score_health():
        points = []
        if current_ratio is not None:
            points.append(85 if current_ratio >= 1.5 else 68 if current_ratio >= 1 else 35)
        if debt_to_equity is not None:
            points.append(85 if debt_to_equity <= .5 else 68 if debt_to_equity <= 1.5 else 42 if debt_to_equity <= 3 else 22)
        if cash_to_debt is not None:
            points.append(82 if cash_to_debt >= 1 else 65 if cash_to_debt >= .4 else 42)
        return round(sum(points) / len(points)) if points else None

    def score_cash_generation():
        points = []
        if free_cash is not None:
            points.append(82 if free_cash > 0 else 25)
        if fcf_margin is not None:
            points.append(85 if fcf_margin >= .15 else 70 if fcf_margin >= .05 else 52 if fcf_margin >= 0 else 25)
        if cash_conversion is not None:
            points.append(82 if cash_conversion >= 1 else 58 if cash_conversion >= .65 else 35)
        return round(sum(points) / len(points)) if points else None

    # Financial firms are evaluated with capital and return measures. Debt and
    # current ratios are not comparable to operating companies, so they are not
    # used in their health pillar.
    financial_sector = sector == "Financial Services"
    if financial_sector:
        capital_ratio = _ratio(equity, assets)
        health_points = []
        if capital_ratio is not None:
            health_points.append(85 if capital_ratio >= .10 else 68 if capital_ratio >= .06 else 40)
        if roa is not None:
            health_points.append(85 if roa >= .015 else 68 if roa >= .008 else 42)
        health_score = round(sum(health_points) / len(health_points)) if health_points else None
        return_points = []
        if roa is not None:
            return_points.append(88 if roa >= .015 else 70 if roa >= .008 else 42)
        if roe is not None:
            return_points.append(85 if roe >= .14 else 68 if roe >= .08 else 42)
        profitability_score = round(sum(return_points) / len(return_points)) if return_points else None
        health_metrics = [
            _metric("Equity / assets", capital_ratio, _percent(capital_ratio), "Capital buffer"),
            _metric("Return on assets", roa, _percent(roa), "Efficiency measure for financial firms"),
        ]
        health_note = "Uses capital and return measures; debt and current ratios are not comparable for financial firms."
    else:
        health_score = score_health()
        profitability_score = score_profitability()
        health_metrics = [
            _metric("Current ratio", current_ratio, _number(current_ratio), "Short-term liquidity"),
            _metric("Debt / equity", debt_to_equity, _number(debt_to_equity), "Balance-sheet leverage"),
            _metric("Cash / debt", cash_to_debt, _number(cash_to_debt), "Cash coverage"),
        ]
        health_note = "Liquidity, leverage, and cash coverage are weighted for operating companies."

    # The valuation pillar is intentionally context only: it uses broad ranges
    # instead of claiming a live peer-median comparison that Yahoo does not give.
    trailing_pe = company_info.get("trailingPE")
    price_to_book = company_info.get("priceToBook")
    pe_ceiling = 45 if sector == "Technology" else 35 if sector in ("Healthcare", "Consumer Cyclical") else 25
    if trailing_pe is None or trailing_pe <= 0:
        valuation_score = None
    elif trailing_pe <= pe_ceiling * .55:
        valuation_score = 80
    elif trailing_pe <= pe_ceiling:
        valuation_score = 65
    elif trailing_pe <= pe_ceiling * 1.5:
        valuation_score = 48
    else:
        valuation_score = 32

    pillars = [
        {"name": "Profitability", "score": profitability_score, "weight": 25, "metrics": [
            _metric("Net margin", net_margin, _percent(net_margin)), _metric("Return on equity", roe, _percent(roe)),
        ]},
        {"name": "Growth", "score": score_growth(), "weight": 22 if sector == "Technology" else 18, "metrics": [
            _metric("Revenue growth", revenue_growth, "Unavailable" if revenue_growth is None else f"{revenue_growth:+.1f}%"),
            _metric("Net income growth", income_growth, "Unavailable" if income_growth is None else f"{income_growth:+.1f}%"),
        ]},
        {"name": "Financial health", "score": health_score, "weight": 25, "metrics": health_metrics, "note": health_note},
        {"name": "Cash generation", "score": score_cash_generation(), "weight": 20, "metrics": [
            _metric("Free cash flow", free_cash, "Positive" if free_cash is not None and free_cash > 0 else "Negative" if free_cash is not None else "Unavailable"),
            _metric("Free-cash-flow margin", fcf_margin, _percent(fcf_margin)), _metric("Cash conversion", cash_conversion, _number(cash_conversion)),
        ]},
        {"name": "Valuation context", "score": valuation_score, "weight": 10 if sector != "Technology" else 8, "metrics": [
            _metric("Trailing P/E", trailing_pe, _number(trailing_pe), "Broad sector-adjusted range, not a peer median"),
            _metric("Price / book", price_to_book, _number(price_to_book)),
        ], "note": "A context range, not a prediction or fair-value estimate."},
    ]
    if financial_sector:
        # Cash flow is less comparable for banks/insurers; lower its influence.
        for pillar in pillars:
            if pillar["name"] == "Cash generation":
                pillar["weight"] = 10
            elif pillar["name"] == "Financial health":
                pillar["weight"] = 32
            elif pillar["name"] == "Profitability":
                pillar["weight"] = 30
            elif pillar["name"] == "Valuation context":
                pillar["weight"] = 10

    available_weight = sum(pillar["weight"] for pillar in pillars if pillar["score"] is not None)
    weighted_score = sum(pillar["score"] * pillar["weight"] for pillar in pillars if pillar["score"] is not None)
    score = _bounded(weighted_score / available_weight) if available_weight else None
    complete = sum(pillar["score"] is not None for pillar in pillars)

    flags = []
    if revenue_growth is not None and revenue_growth < 0:
        flags.append("Annual revenue declined in the latest reported year.")
    if net_income is not None and net_income < 0:
        flags.append("The latest annual statement shows a net loss.")
    if not financial_sector and debt_to_equity is not None and debt_to_equity > 2:
        flags.append("Leverage is elevated relative to equity.")
    if not financial_sector and current_ratio is not None and current_ratio < 1:
        flags.append("Current assets are below current liabilities.")
    if free_cash is not None and free_cash < 0:
        flags.append("Free cash flow was negative in the latest reported year.")
    if sector == "Real Estate":
        flags.append("REIT-specific FFO/AFFO is not available from this Yahoo statement view; interpret cash-flow results carefully.")
    if complete < 4:
        flags.append("Several score pillars have incomplete Yahoo Finance data.")

    strongest = max((pillar for pillar in pillars if pillar["score"] is not None), key=lambda item: item["score"], default=None)
    weakest = min((pillar for pillar in pillars if pillar["score"] is not None), key=lambda item: item["score"], default=None)
    if score is None:
        summary = "HELIX could not calculate a health snapshot because Yahoo Finance did not provide enough annual data."
    else:
        summary = f"{financials['ticker']} has a {_band(score).lower()} financial-condition snapshot for the {sector} sector."
        if strongest:
            summary += f" Its strongest available pillar is {strongest['name'].lower()}."
        if weakest and weakest != strongest:
            summary += f" The main area to investigate is {weakest['name'].lower()}."

    return {
        "score": score, "band": _band(score) if score is not None else "Insufficient data",
        "sector": sector, "industry": industry, "pillars": pillars, "flags": flags,
        "summary": summary, "coverage": f"{complete} of {len(pillars)} pillars available",
        "disclaimer": "Research snapshot based on reported annual Yahoo Finance data and visible HELIX rules. It is not investment advice or a prediction of future returns.",
    }


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
    try:
        company_info = company.get_info()
    except Exception:
        company_info = {}
    periods = _periods(income)
    if not periods:
        raise ValueError(f"No annual financial statements were found for {symbol}.")

    revenue = _series(income, ("Total Revenue",), periods)
    net_income = _series(income, ("Net Income", "Net Income Common Stockholders"), periods)
    operating_income = _series(income, ("Operating Income",), periods)
    cost_of_revenue = _series(income, ("Cost Of Revenue", "Cost Of Goods And Services Sold"), periods)
    research_and_development = _series(income, ("Research And Development", "Research Development"), periods)
    selling_general_admin = _series(income, ("Selling General And Administration", "Selling General And Administrative"), periods)
    other_operating = _series(income, ("Other Operating Expenses",), periods)
    operating_expense = _series(income, ("Operating Expense", "Operating Expenses"), periods)
    interest_expense = _series(income, ("Interest Expense", "Interest Expense Non Operating"), periods)
    income_tax = _series(income, ("Tax Provision", "Income Tax Expense"), periods)
    detailed_operating_costs = _has_reported_value(research_and_development) or _has_reported_value(selling_general_admin)
    expenses = [("Cost of revenue", cost_of_revenue)]
    if detailed_operating_costs:
        expenses.extend([
            ("Research & development", research_and_development),
            ("Selling, general & admin", selling_general_admin),
            ("Other operating expense", other_operating),
        ])
    else:
        expenses.append(("Operating expenses", operating_expense))
    expenses.extend([("Interest expense", interest_expense), ("Income tax provision", income_tax)])
    latest_revenue = revenue[0]["value"]
    latest_income = net_income[0]["value"]
    margin = (latest_income / latest_revenue * 100) if latest_revenue and latest_income is not None else None

    balance_periods = _periods(balance)
    cash_periods = _periods(cash_flow)
    financials = {
        "ticker": symbol,
        "periods": [entry["period"] for entry in revenue],
        "income": {
            "revenue": revenue,
            "net_income": net_income,
            "operating_income": operating_income,
            "net_margin": margin,
            "expenses": [
                {"label": label, "values": values}
                for label, values in expenses
                if _latest(values) is not None
            ],
        },
        "balance": {
            "periods": [_year_label(period) for period in balance_periods],
            "cash": _series(balance, ("Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"), balance_periods),
            "current_assets": _series(balance, ("Current Assets", "Total Current Assets"), balance_periods),
            "current_liabilities": _series(balance, ("Current Liabilities", "Total Current Liabilities"), balance_periods),
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
    financials["health"] = _health_profile(financials, company_info)
    return financials
