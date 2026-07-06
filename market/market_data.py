import yfinance as yf


def get_current_price(ticker):
    try:
        stock = yf.Ticker(ticker)

        history = stock.history(period="5d")

        if history.empty:
            return None

        price = history["Close"].iloc[-1]
        return round(price, 2)

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    print("HELIX Market Data Test")
    print("----------------------")

    print("META:", get_current_price("META"))
    print("TSM :", get_current_price("TSM"))
    print("VOO :", get_current_price("VOO"))