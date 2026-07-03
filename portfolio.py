import yfinance as yf

# =============================
# YOUR PORTFOLIO
# Replace the sample values
# with your real shares and
# average purchase prices.
# =============================


portfolio = {
    "META": {
        "shares": 10.577,
        "cost_basis": 622.00
    },
    "GOOGL": {
        "shares": 11.613,
        "cost_basis": 249.98
    },
    "TSM": {
        "shares": 8.432,
        "cost_basis": 288.74
    },
    "VOO": {
        "shares": 5.836,
        "cost_basis": 597.39
    },
    "DRAM": {
        "shares": 9,
        "cost_basis": 64.66
    }
}

print("\n")
print("=" * 70)
print("               TREZY AI PORTFOLIO DASHBOARD")
print("=" * 70)

total_value = 0
total_cost = 0

holdings = []

for ticker, info in portfolio.items():

    shares = info["shares"]
    cost_basis = info["cost_basis"]

    stock = yf.Ticker(ticker)

    try:
        current_price = stock.history(period="1d")["Close"].iloc[-1]

        current_value = current_price * shares
        original_cost = cost_basis * shares

        profit = current_value - original_cost
        percent = (profit / original_cost) * 100

        total_value += current_value
        total_cost += original_cost

        holdings.append({
            "ticker": ticker,
            "shares": shares,
            "price": current_price,
            "value": current_value,
            "profit": profit
        })

        print(f"{ticker}")
        print(f"  Shares:        {shares}")
        print(f"  Avg Cost:      ${cost_basis:.2f}")
        print(f"  Current Price: ${current_price:.2f}")
        print(f"  Position:      ${current_value:,.2f}")
        print(f"  Gain/Loss:     ${profit:,.2f} ({percent:.2f}%)")
        print()

    except Exception as e:
        print(f"Error retrieving {ticker}: {e}")

print("=" * 70)

portfolio_profit = total_value - total_cost
portfolio_percent = (portfolio_profit / total_cost) * 100

print(f"Portfolio Cost:     ${total_cost:,.2f}")
print(f"Portfolio Value:    ${total_value:,.2f}")
print(f"Total Gain/Loss:    ${portfolio_profit:,.2f}")
print(f"Overall Return:     {portfolio_percent:.2f}%")

largest = max(holdings, key=lambda x: x["value"])
smallest = min(holdings, key=lambda x: x["value"])

print()
print(f"Largest Position : {largest['ticker']} (${largest['value']:,.2f})")
print(f"Smallest Position: {smallest['ticker']} (${smallest['value']:,.2f})")

print("=" * 70)