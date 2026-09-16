import yfinance as yf


MARKET_SYMBOLS = (
    ("S&P 500", "SPY"),
    ("Nasdaq 100", "QQQ"),
    ("Volatility", "VXX"),
    ("Bitcoin", "BTC-USD"),
)

SECTOR_SYMBOLS = (
    ("Communication", "XLC"),
    ("Consumer Discretionary", "XLY"),
    ("Consumer Staples", "XLP"),
    ("Energy", "XLE"),
    ("Financials", "XLF"),
    ("Health Care", "XLV"),
    ("Industrials", "XLI"),
    ("Materials", "XLB"),
    ("Real Estate", "XLRE"),
    ("Technology", "XLK"),
    ("Utilities", "XLU"),
)


def get_quote(ticker):
    """Return the latest close and movement from the prior close."""
    try:
        history = yf.Ticker(ticker).history(period="5d")
        if history.empty:
            return None
        current_price = float(history["Close"].iloc[-1])
        previous_close = float(history["Close"].iloc[-2]) if len(history) > 1 else current_price
        dollar_change = current_price - previous_close
        percent_change = (dollar_change / previous_close) * 100 if previous_close else 0
        return {
            "price": round(current_price, 2),
            "dollar": round(dollar_change, 2),
            "percent": round(percent_change, 2),
        }
    except Exception:
        return None


def get_current_price(ticker):
    """
    Returns the latest market price.
    """

    quote = get_quote(ticker)
    return quote["price"] if quote else None


def get_daily_change(ticker):
    """
    Returns today's dollar and percent change.
    """

    quote = get_quote(ticker)
    if not quote:
        return None
    return {
        "dollar": quote["dollar"],
        "percent": quote["percent"],
        "current_price": quote["price"],
    }


def get_market_summary():
    """Fetch the benchmark and sector snapshots used by the Markets page."""
    def collect(symbols):
        rows = []
        for name, ticker in symbols:
            quote = get_quote(ticker)
            if quote:
                rows.append({"name": name, "ticker": ticker, **quote})
            else:
                rows.append({"name": name, "ticker": ticker, "price": None, "dollar": None, "percent": None})
        return rows

    return {"benchmarks": collect(MARKET_SYMBOLS), "sectors": collect(SECTOR_SYMBOLS)}
if __name__ == "__main__":

    print(get_current_price("META"))

    print(get_daily_change("META"))
