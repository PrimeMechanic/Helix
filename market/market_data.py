import yfinance as yf


def get_current_price(ticker):
    """
    Returns the latest market price.
    """

    try:
        stock = yf.Ticker(ticker)

        history = stock.history(period="2d")

        if history.empty:
            return None

        return round(history["Close"].iloc[-1], 2)

    except Exception:
        return None


def get_daily_change(ticker):
    """
    Returns today's dollar and percent change.
    """

    try:
        stock = yf.Ticker(ticker)

        history = stock.history(period="2d")

        if len(history) < 2:
            return None

        previous_close = history["Close"].iloc[-2]
        current_price = history["Close"].iloc[-1]

        dollar_change = current_price - previous_close
        percent_change = (dollar_change / previous_close) * 100

        return {
            "dollar": round(dollar_change, 2),
            "percent": round(percent_change, 2),
            "previous_close": round(previous_close, 2),
            "current_price": round(current_price, 2)
        }

    except Exception:
        return None
if __name__ == "__main__":

    print(get_current_price("META"))

    print(get_daily_change("META"))    