"""Research calculations. Scores describe observations, never predict returns."""
import json
import math
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def number(value):
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def symbol(value):
    value = value.strip().upper()
    if not re.fullmatch(r'[A-Z0-9.^=-]{1,15}', value):
        raise ValueError('Enter a valid ticker.')
    return value


def company_research(ticker):
    from market.fundamentals import get_company_financials
    ticker = symbol(ticker)
    company = yf.Ticker(ticker)
    info = company.get_info() or {}
    if not info.get('shortName') and not info.get('longName'):
        raise ValueError(f'Company data unavailable for {ticker}.')
    keys = ('currentPrice', 'regularMarketPrice', 'marketCap', 'trailingPE', 'forwardPE',
            'priceToSalesTrailing12Months', 'revenueGrowth', 'earningsGrowth', 'profitMargins',
            'operatingMargins', 'freeCashflow', 'totalCash', 'totalDebt', 'dividendRate',
            'payoutRatio', 'beta', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow')
    result = {'ticker': ticker, 'name': info.get('longName', info.get('shortName')),
              'sector': info.get('sector', 'Unclassified'), 'currency': info.get('currency', 'Unknown'),
              'quote_type': info.get('quoteType'), 'metrics': {k: number(info.get(k)) for k in keys},
              'source': 'Yahoo Finance via yfinance', 'retrieved_at': now(),
              'quote_time': info.get('regularMarketTime')}
    try:
        result['statements'] = get_company_financials(ticker)
    except Exception:
        result['statement_warning'] = 'Annual statements unavailable; company health not scored.'
    return result


def compare_companies(text):
    tickers = list(dict.fromkeys(symbol(t) for t in text.replace(',', ' ').split()))
    if not 1 <= len(tickers) <= 8:
        raise ValueError('Compare between one and eight tickers.')
    rows = []
    for ticker in tickers:
        try:
            rows.append(company_research(ticker))
        except Exception as error:
            rows.append({'ticker': ticker, 'error': str(error)})
    return rows


def concentration(positions):
    total = sum(p['value'] for p in positions)
    if total <= 0:
        raise ValueError('A positive portfolio value is required.')
    weights = sorted(((p['ticker'], p['value'] / total) for p in positions), key=lambda x: -x[1])
    hhi = sum(w*w for _, w in weights)
    return {'value': total, 'largest_weight_pct': weights[0][1]*100,
            'top_three_pct': sum(w for _, w in weights[:3])*100,
            'effective_positions': 1/hhi, 'weights': {t: w*100 for t, w in weights},
            'note': 'Direct holdings only; ETFs may overlap. This is concentration, not a complete risk score.'}


def stress_test(positions, shock):
    shock = number(shock)
    if shock is None or not -100 <= shock <= 100:
        raise ValueError('Shock must be between -100% and +100%.')
    total = concentration(positions)['value']
    return {'shock_pct': shock, 'change': total*shock/100, 'scenario_value': total*(1+shock/100),
            'note': 'Uniform price shock on current positions; excludes cash, taxes and trading. Not a forecast.'}


def rebalance(positions, targets, cash=0):
    cash = number(cash)
    if cash is None or cash < 0:
        raise ValueError('New cash must be nonnegative.')
    if not targets or any(number(v) is None or v < 0 for v in targets.values()):
        raise ValueError('Targets must be finite nonnegative percentages.')
    if abs(sum(targets.values())-100) > .001:
        raise ValueError('Target weights must total 100%.')
    values = {p['ticker']: p['value'] for p in positions}
    if set(targets) != set(values):
        raise ValueError('Provide a target for each current holding.')
    total = sum(values.values()) + cash
    return [{'ticker': t, 'current_value': values[t], 'target_pct': targets[t],
             'dollar_change': total*targets[t]/100-values[t]} for t in values]


def dcf(fcf, growth, discount, terminal, shares, net_debt=0):
    values = [number(v) for v in (fcf, growth, discount, terminal, shares, net_debt)]
    if any(v is None for v in values):
        raise ValueError('All DCF inputs must be finite numbers.')
    fcf, growth, discount, terminal, shares, net_debt = values
    if fcf <= 0 or shares <= 0 or not -100 < growth <= 100 or not 0 < discount <= 100 or not -100 < terminal < discount:
        raise ValueError('Use positive FCF/shares, growth above -100%, and a discount rate above terminal growth.')
    g, r, t = growth/100, discount/100, terminal/100
    flows = [fcf*(1+g)**year for year in range(1, 6)]
    pv = sum(flow/(1+r)**year for year, flow in enumerate(flows, 1))
    terminal_pv = flows[-1]*(1+t)/(r-t)/(1+r)**5
    return {'equity_value': pv+terminal_pv-net_debt,
            'value_per_share': (pv+terminal_pv-net_debt)/shares,
            'terminal_share_pct': terminal_pv/(pv+terminal_pv)*100,
            'note': 'Five-year enterprise DCF. Use unlevered FCF, net debt and diluted shares in consistent units. Assumption-driven; unsuitable for many financial firms.'}


def sentiment_from_series(spy, vix, sectors):
    """All components required: never fabricate a neutral value for missing data."""
    if len(spy) < 200 or not vix or len(sectors) != 11:
        raise ValueError('Sentiment unavailable: requires 200 SPY closes, VIX, and all 11 sector ETFs.')
    if any(number(v) is None or v <= 0 for v in list(spy)+list(vix)+list(sectors)):
        raise ValueError('Sentiment inputs contain invalid prices or ratios.')
    momentum = (spy[-1]/(sum(spy[-200:])/200)-1)*100
    components = {'SPY vs 200-day average': max(0, min(100, 50+momentum*3)),
                  'VIX risk appetite': max(0, min(100, (40-vix[-1])/30*100)),
                  'Sector breadth': sum(r > 1 for r in sectors)/11*100}
    score = round(sum(components.values())/3)
    label = 'Extreme fear' if score < 20 else 'Fear' if score < 40 else 'Neutral' if score <= 60 else 'Greed' if score <= 80 else 'Extreme greed'
    return {'score': score, 'label': label, 'components': components, 'vix': vix[-1],
            'momentum_pct': momentum, 'source': 'Yahoo Finance daily closes', 'retrieved_at': now(),
            'method': 'HELIX proxy, not CNN Fear & Greed. Equal weights: SPY/200d (50 + 3×percent distance, clipped); VIX (40−VIX)/30×100, clipped; fraction of 11 sectors above 50d. No put/call or credit spread inputs.'}


def market_sentiment():
    from market.market_data import SECTOR_SYMBOLS
    symbols = ['SPY', '^VIX']+[ticker for _, ticker in SECTOR_SYMBOLS]
    histories = {}
    for ticker in symbols:
        history = yf.Ticker(ticker).history(period='1y', auto_adjust=True)
        if history.empty:
            raise ValueError(f'No sentiment data for {ticker}.')
        histories[ticker] = history['Close'].dropna()
    # Align dates so an old component cannot silently stand in for today's close.
    common = set(histories['SPY'].index.date)
    for history in histories.values():
        common &= set(history.index.date)
    if not common:
        raise ValueError('No common market date across sentiment components.')
    date = max(common)
    if (datetime.now(timezone.utc).date()-date).days > 5:
        raise ValueError('Sentiment data is stale by more than five days.')
    def closes(ticker):
        series = histories[ticker]
        return [float(v) for d, v in series.items() if d.date() <= date]
    sectors = []
    for _, ticker in SECTOR_SYMBOLS:
        values = closes(ticker)
        if len(values) < 50:
            raise ValueError(f'Insufficient sector history for {ticker}.')
        sectors.append(values[-1]/(sum(values[-50:])/50))
    result = sentiment_from_series(closes('SPY'), closes('^VIX'), sectors)
    result['market_date'] = str(date)
    return result


def notebook(ticker, text=None):
    ticker = symbol(ticker)
    folder = Path(os.environ.get('LOCALAPPDATA', Path.home()/'.local'/'share'))/'HELIX'
    folder.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(folder/'research.sqlite3', timeout=10) as db:
        db.execute('CREATE TABLE IF NOT EXISTS notes (ticker TEXT PRIMARY KEY, body TEXT, updated TEXT)')
        if text is not None:
            db.execute('INSERT OR REPLACE INTO notes VALUES (?, ?, ?)', (ticker, text, now()))
        row = db.execute('SELECT body FROM notes WHERE ticker=?', (ticker,)).fetchone()
    return row[0] if row else 'Thesis:\n\nGrowth drivers:\n\nRisks / disconfirming evidence:\n\nNext earnings questions:\n'


def portfolio_research(positions):
    """Weighted direct-company context, with explicit uncovered value."""
    exposure = concentration(positions)
    if len(positions) > 30:
        raise ValueError('This desktop research pass supports up to 30 holdings; use company comparisons for selected names.')
    companies, sectors = [], {}
    weighted_health = covered = income = income_covered = 0.0
    for position in positions:
        try:
            company = company_research(position['ticker'])
            weight = position['value']/exposure['value']
            sectors[company['sector']] = sectors.get(company['sector'], 0)+weight*100
            health = company.get('statements', {}).get('health', {})
            if health.get('score') is not None:
                weighted_health += weight*health['score']
                covered += weight
            dividend = company['metrics']['dividendRate']
            if dividend is not None and company['currency'] == 'USD':
                income += dividend*position['shares']
                income_covered += weight
            companies.append(company)
        except Exception as error:
            companies.append({'ticker': position['ticker'], 'error': str(error)})
    return {'concentration': exposure, 'companies': companies, 'direct_sector_weights_pct': sectors,
            'covered_business_health': weighted_health/covered if covered else None,
            'business_health_value_coverage_pct': covered*100,
            'estimated_annual_usd_dividend': income if income_covered else None,
            'dividend_value_coverage_pct': income_covered*100,
            'prepared_at': now(), 'source': 'Yahoo Finance via yfinance',
            'limitations': 'Health is a value-weighted average over scored holdings only, not overall portfolio safety. Sector exposure has no ETF look-through. Dividend estimate uses reported annual rate; uncovered income is unknown. Quotes and statements may have different dates.'}


def risk_from_prices(prices, weights, benchmark='SPY'):
    """Hypothetical constant-weight historical risk, never account performance."""
    import pandas as pd
    required = list(dict.fromkeys(list(weights)+[benchmark]))
    aligned = prices[required].dropna()
    if len(aligned) < 60:
        raise ValueError('Risk analysis needs at least 60 common daily prices for every holding and SPY.')
    if not all(number(v) is not None and v > 0 for v in aligned.to_numpy().flat):
        raise ValueError('Risk analysis received invalid adjusted prices.')
    if abs(sum(weights.values())-1) > 1e-6 or any(w < 0 for w in weights.values()):
        raise ValueError('Risk weights must be nonnegative and total one.')
    returns = aligned.pct_change().dropna()
    portfolio = sum(returns[t]*w for t, w in weights.items())
    benchmark_returns = returns[benchmark]
    index = (1+portfolio).cumprod()
    # Include starting capital so a first-day loss contributes to drawdown.
    peak = index.cummax().clip(lower=1)
    variance = benchmark_returns.var()
    beta = float(portfolio.cov(benchmark_returns)/variance) if variance > 0 else None
    corr = returns[list(weights)].corr()
    pairs = [{'first': a, 'second': b, 'correlation': number(corr.loc[a, b])}
             for i, a in enumerate(weights) for b in list(weights)[i+1:]]
    pairs.sort(key=lambda row: row['correlation'] if row['correlation'] is not None else -2, reverse=True)
    return {'annualized_volatility_pct': float(portfolio.std()*math.sqrt(252)*100),
            'max_drawdown_pct': float((index/peak-1).min()*100), 'beta_vs_spy': beta,
            'correlation_vs_spy': number(portfolio.corr(benchmark_returns)),
            'most_correlated_pairs': pairs[:10], 'daily_observations': len(returns),
            'start_date': str(aligned.index[0])[:10], 'end_date': str(aligned.index[-1])[:10],
            'source': 'Yahoo Finance adjusted daily closes', 'retrieved_at': now(),
            'method': 'Current market-value weights held constant and rebalanced daily over common available history. Not your actual returns; excludes cash, costs, tax and flows. Short histories shorten the whole window. Historical risk does not predict future losses.'}


def portfolio_risk(positions):
    import pandas as pd
    exposure = concentration(positions)
    if len(positions) > 30:
        raise ValueError('Risk analysis supports up to 30 holdings.')
    weights = {ticker: weight/100 for ticker, weight in exposure['weights'].items()}
    columns = {}
    for ticker in dict.fromkeys(list(weights)+['SPY']):
        frame = yf.Ticker(ticker).history(period='1y', auto_adjust=True)
        if frame.empty:
            raise ValueError(f'Adjusted price history unavailable for {ticker}.')
        series = frame['Close'].copy()
        series.index = series.index.tz_localize(None).normalize()
        columns[ticker] = series
    return risk_from_prices(pd.DataFrame(columns), weights)
