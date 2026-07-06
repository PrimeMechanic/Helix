from portfolio_manager import load_portfolio
from market_data import get_current_price


def display_portfolio():

    portfolio = load_portfolio()

    print()
    print("=" * 70)
    print("                         HELIX")
    print("=" * 70)
    print("               Live Portfolio Dashboard")
    print("=" * 70)

    total_value = 0
    total_cost = 0

    holdings = []

    for ticker, info in portfolio.items():

        shares = info["shares"]
        cost_basis = info["cost_basis"]

        try:
            current_price = get_current_price(ticker)

            if current_price is None:
                print(f"Unable to retrieve {ticker}")
                continue

            current_value = current_price * shares
            original_cost = cost_basis * shares

            profit = current_value - original_cost

            if original_cost > 0:
                percent = (profit / original_cost) * 100
            else:
                percent = 0

            total_value += current_value
            total_cost += original_cost

            holdings.append({
                "ticker": ticker,
                "shares": shares,
                "price": current_price,
                "value": current_value,
                "profit": profit
            })

            print(f"\n{ticker}")
            print("-" * 40)
            print(f"Shares:         {shares}")
            print(f"Avg Cost:       ${cost_basis:.2f}")
            print(f"Current Price:  ${current_price:.2f}")
            print(f"Market Value:   ${current_value:,.2f}")
            print(f"Gain/Loss:      ${profit:,.2f} ({percent:.2f}%)")

        except Exception as e:
            print(f"Error retrieving {ticker}: {e}")

    print()
    print("=" * 70)

    portfolio_profit = total_value - total_cost

    if total_cost > 0:
        portfolio_percent = (portfolio_profit / total_cost) * 100
    else:
        portfolio_percent = 0

    print(f"Portfolio Cost:     ${total_cost:,.2f}")
    print(f"Portfolio Value:    ${total_value:,.2f}")
    print(f"Total Gain/Loss:    ${portfolio_profit:,.2f}")
    print(f"Overall Return:     {portfolio_percent:.2f}%")

    if holdings:
        largest = max(holdings, key=lambda x: x["value"])
        smallest = min(holdings, key=lambda x: x["value"])

        print()
        print(f"Largest Position : {largest['ticker']} (${largest['value']:,.2f})")
        print(f"Smallest Position: {smallest['ticker']} (${smallest['value']:,.2f})")

    print("=" * 70)


if __name__ == "__main__":
    display_portfolio()