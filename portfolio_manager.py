import json
import math
import os
import re
import tempfile
from pathlib import Path

PORTFOLIO_FILE = Path(__file__).resolve().with_name("portfolio.json")


def load_portfolio():
    """Load the portfolio from the JSON file."""
    with open(PORTFOLIO_FILE, "r") as file:
        portfolio = json.load(file)
    validate_portfolio(portfolio)
    return portfolio


def save_portfolio(portfolio):
    """Save the portfolio to the JSON file."""
    validate_portfolio(portfolio)
    target = Path(PORTFOLIO_FILE)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as file:
            temporary = file.name
            json.dump(portfolio, file, indent=4, allow_nan=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, target)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def validate_portfolio(portfolio):
    if not isinstance(portfolio, dict):
        raise ValueError("Portfolio must contain ticker positions.")
    for ticker, position in portfolio.items():
        if not isinstance(ticker, str) or not re.fullmatch(r"[A-Z0-9.^=-]{1,15}", ticker):
            raise ValueError("Invalid portfolio ticker.")
        if not isinstance(position, dict):
            raise ValueError(f"Invalid position for {ticker}.")
        for key in ("shares", "cost_basis"):
            value = position.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid {key} for {ticker}.")


def read_number(prompt, allow_zero=False):
    try:
        value = float(input(prompt))
    except ValueError:
        print("Enter a valid number.")
        return None
    if not math.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
        print("Enter a positive finite number." if not allow_zero else "Enter a nonnegative finite number.")
        return None
    return value


def add_position():

    portfolio = load_portfolio()

    print("\n=== Add New Position ===")

    ticker = input("Ticker: ").strip().upper()

    if ticker in portfolio:
        print(f"\n{ticker} already exists.")
        print("Use 'Buy More Shares' instead.")
        return

    if not re.fullmatch(r"[A-Z0-9.^=-]{1,15}", ticker):
        print("Enter a valid ticker.")
        return
    shares = read_number("Shares: ")
    if shares is None:
        return
    cost_basis = read_number("Average Cost: ", allow_zero=True)
    if cost_basis is None:
        return

    portfolio[ticker] = {
        "shares": shares,
        "cost_basis": cost_basis
    }

    save_portfolio(portfolio)

    print(f"\n✅ {ticker} added successfully!")


def buy_more_shares():

    portfolio = load_portfolio()

    print("\n=== Buy More Shares ===")

    ticker = input("Ticker: ").strip().upper()

    if ticker not in portfolio:
        print(f"\n{ticker} is not in your portfolio.")
        return

    additional_shares = read_number("Additional Shares: ")
    if additional_shares is None:
        return
    purchase_price = read_number("Purchase Price: ")
    if purchase_price is None:
        return

    current_shares = portfolio[ticker]["shares"]
    current_cost = portfolio[ticker]["cost_basis"]

    old_value = current_shares * current_cost
    new_value = additional_shares * purchase_price

    total_shares = current_shares + additional_shares
    new_average_cost = (old_value + new_value) / total_shares

    portfolio[ticker]["shares"] = total_shares
    portfolio[ticker]["cost_basis"] = new_average_cost

    save_portfolio(portfolio)

    print(f"\n✅ Purchased {additional_shares} shares of {ticker}")
    print(f"New Total Shares: {total_shares}")
    print(f"New Average Cost: ${new_average_cost:.2f}")

def sell_shares():

    portfolio = load_portfolio()

    print("\n=== Sell Shares ===")

    ticker = input("Ticker: ").strip().upper()

    if ticker not in portfolio:
        print(f"\n{ticker} is not in your portfolio.")
        return

    current_shares = portfolio[ticker]["shares"]

    print(f"\nCurrent Shares: {current_shares}")

    shares_to_sell = read_number("Shares to Sell: ")
    if shares_to_sell is None:
        return

    if shares_to_sell <= 0:
        print("\nInvalid amount.")
        return

    if shares_to_sell > current_shares:
        print("\nYou don't own that many shares.")
        return

    remaining = current_shares - shares_to_sell

    if remaining == 0:
        del portfolio[ticker]
        print(f"\n✅ Sold entire position in {ticker}.")
    else:
        portfolio[ticker]["shares"] = remaining
        print(f"\n✅ Sold {shares_to_sell} shares of {ticker}.")
        print(f"Remaining Shares: {remaining}")

    save_portfolio(portfolio)
