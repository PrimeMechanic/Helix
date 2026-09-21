"""Persistence helpers for the user's HELIX watchlist."""

import json
import re
from pathlib import Path


WATCHLIST_FILE = Path(__file__).with_name("watchlist.json")
VALID_TICKER = re.compile(r"^[A-Z0-9.^=-]{1,15}$")


def load_watchlist():
    if not WATCHLIST_FILE.exists():
        return []
    try:
        saved = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
        return [ticker for ticker in saved if isinstance(ticker, str)]
    except (OSError, json.JSONDecodeError):
        return []


def add_to_watchlist(ticker):
    symbol = ticker.strip().upper()
    if not VALID_TICKER.fullmatch(symbol):
        raise ValueError("Enter a valid ticker, such as MSFT or BTC-USD.")
    watchlist = load_watchlist()
    if symbol not in watchlist:
        watchlist.append(symbol)
        WATCHLIST_FILE.write_text(json.dumps(watchlist, indent=2), encoding="utf-8")
    return watchlist


def remove_from_watchlist(ticker):
    watchlist = [symbol for symbol in load_watchlist() if symbol != ticker]
    WATCHLIST_FILE.write_text(json.dumps(watchlist, indent=2), encoding="utf-8")
    return watchlist
