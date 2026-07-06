from portfolio_manager import load_portfolio
from market.market_data import get_current_price


def analyze_portfolio():

    portfolio = load_portfolio()

    print()
    print("=" * 70)
    print("                    HELIX AI ANALYSIS")
    print("=" * 70)

    total_value = 0
    total_cost = 0

    positions = []

    for ticker, info in portfolio.items():

        shares = info["shares"]
        cost_basis = info["cost_basis"]

        current_price = get_current_price(ticker)

        if current_price is None:
            continue

        market_value = shares * current_price
        original_cost = shares * cost_basis

        gain = market_value - original_cost

        if original_cost > 0:
            percent = (gain / original_cost) * 100
        else:
            percent = 0

        total_value += market_value
        total_cost += original_cost

        positions.append({
            "ticker": ticker,
            "value": market_value,
            "gain": gain,
            "percent": percent
        })

    if not positions:
        print("Unable to analyze portfolio.")
        return

    total_gain = total_value - total_cost
    total_percent = (total_gain / total_cost) * 100

    largest = max(positions, key=lambda x: x["value"])
    best = max(positions, key=lambda x: x["percent"])
    worst = min(positions, key=lambda x: x["percent"])

    print(f"\nPortfolio Value : ${total_value:,.2f}")
    print(f"Overall Return  : {total_percent:.2f}%")
    print()

    print(f"Largest Holding : {largest['ticker']}")
    print(f"Best Performer  : {best['ticker']} ({best['percent']:.2f}%)")
    print(f"Worst Performer : {worst['ticker']} ({worst['percent']:.2f}%)")

    print("\nAI Insights")
    print("-" * 40)

    if largest["value"] / total_value > 0.25:
        print("• Your largest position exceeds 25% of your portfolio.")

    if total_percent > 20:
        print("• Excellent long-term performance.")

    elif total_percent > 10:
        print("• Portfolio is performing well.")

    elif total_percent > 0:
        print("• Portfolio is profitable but has room for improvement.")

    else:
        print("• Portfolio is currently at a loss.")

    if len(portfolio) < 5:
        print("• Consider increasing diversification.")

    print()
    print("=" * 70)