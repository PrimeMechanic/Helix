# HELIX

Local Python desktop portfolio tracker with quotes, company financials, news, and rule-based research scores. Use Python 3.10 or newer.

## Start on Windows

From the Helix folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m ui.app
```

On macOS/Linux activate with `source .venv/bin/activate`. Linux may require your distribution's Python Tk package. Run `python main.py` for the terminal menu.

## Data and limitations

The desktop reads `portfolio.json` beside `portfolio_manager.py`, regardless of launch directory. Each ticker has `shares` and per-share `cost_basis`. Use the terminal menu to add, buy, and sell positions. Invalid numbers are rejected and saves use atomic replacement. Back up your portfolio before manual edits.

Dashboard return is the unrealized gain on currently held shares, not lifetime return. Cash, realized gains, and dividends are excluded. Performance shows value snapshots including purchases and sales; it does not calculate cash-flow-adjusted returns.

Dashboard refresh runs in the background. Missing or invalid quotes reject the whole valuation, retain previously displayed data with a warning, and do not overwrite history. Yahoo prices are latest available daily history values, not guaranteed real-time quotes. Markets, News, Financials, and Income still load on the UI thread.

See [PLAID_SETUP.md](PLAID_SETUP.md) for the optional connector. Token encryption requires Windows. The connector can connect and retrieve holdings, but the desktop does not yet import or synchronize them. Continue maintaining `portfolio.json` manually. Never commit credentials or tokens.

Research scores use visible rules, not predictive AI.

## Checks

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
```

Regression checks mock market prices and do not contact brokers. Full desktop and live Plaid testing are separate manual checks.
