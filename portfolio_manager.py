import json

PORTFOLIO_FILE = "portfolio.json"


def load_portfolio():
    """Load the portfolio from the JSON file."""
    with open(PORTFOLIO_FILE, "r") as file:
        return json.load(file)


def save_portfolio(portfolio):
    """Save the portfolio to the JSON file."""
    with open(PORTFOLIO_FILE, "w") as file:
        json.dump(portfolio, file, indent=4)


def add_position():

    portfolio = load_portfolio()

    print("\n=== Add New Position ===")

    ticker = input("Ticker: ").upper()

    if ticker in portfolio:
        print(f"\n{ticker} already exists.")
        print("Use 'Buy More Shares' instead.")
        return

    shares = float(input("Shares: "))
    cost_basis = float(input("Average Cost: "))

    portfolio[ticker] = {
        "shares": shares,
        "cost_basis": cost_basis
    }

    save_portfolio(portfolio)

    print(f"\n✅ {ticker} added successfully!")


def buy_more_shares():

    portfolio = load_portfolio()

    print("\n=== Buy More Shares ===")

    ticker = input("Ticker: ").upper()

    if ticker not in portfolio:
        print(f"\n{ticker} is not in your portfolio.")
        return

    additional_shares = float(input("Additional Shares: "))
    purchase_price = float(input("Purchase Price: "))

    current_shares = portfolio[ticker]["shares"]
    current_cost = portfolio[ticker]["cost_basis"]

    old_value = current_shares * current_cost
    new_value = additional_shares * purchase_price

    total_shares = current_shares + additional_shares
    new_average_cost = (old_value + new_value) / total_shares

    portfolio[ticker]["shares"] = total_shares
    portfolio[ticker]["cost_basis"] = round(new_average_cost, 2)

    save_portfolio(portfolio)

    print(f"\n✅ Purchased {additional_shares} shares of {ticker}")
    print(f"New Total Shares: {total_shares}")
    print(f"New Average Cost: ${new_average_cost:.2f}")