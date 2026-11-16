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

See [PLAID_SETUP.md](PLAID_SETUP.md) for the optional connector. Token encryption requires Windows. The connector can connect and retrieve holdings. Research hub → Brokerage previews and explicitly imports supported holdings; no automatic synchronization runs. Never commit credentials or tokens.

Research scores use visible rules, not predictive AI.

## Checks

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
```

Regression checks mock market prices and do not contact brokers. Full desktop and live Plaid testing are separate manual checks.

## Research workspace

Open **Research hub** from the sidebar. All new external data requests run in background workers; failures stay visible and do not invent results.

| Workspace | Tools |
| --- | --- |
| Portfolio lab | Direct concentration, effective position count, company health with value coverage, dividend estimate with coverage, historical volatility/drawdown/beta/correlation, uniform stress tests, target-weight rebalance planner |
| Companies | Compare up to eight symbols, valuation/profitability/growth/dividend metrics, annual financial health and evidence |
| Sentiment | HELIX Fear/Greed-style daily proxy with component formulas, market date and missing-data checks |
| Valuation | Five-year enterprise DCF, lower/base/higher growth scenarios and terminal-value dependence |
| Notebook | Per-ticker local thesis, risks and earnings questions stored in a local SQLite database |
| Brokerage | Plaid connection, preview, explicit replacement import and backup; Sandbox provenance shown on dashboard |

Historical risk holds today's market-value weights constant with hypothetical daily rebalancing. It is **not actual account performance**. Every holding and SPY must have at least 60 aligned prices; no missing ticker is silently excluded. ETF overlap and sector look-through are not modeled. Business health averages only scored holdings; inspect coverage before interpreting the result.

The sentiment proxy is **not CNN Fear & Greed**. Three equal components are SPY's distance from its 200-day mean (`clip(50 + 3 × percent distance)`), VIX (`clip((40 − VIX) / 30 × 100)`), and the proportion of 11 sector ETFs above their 50-day means. Scores are bounded 0–100 and use a common available market date. No options positioning or credit-spread evidence is included. Missing inputs fail visibly.

### Optional AI research

Set `OPENAI_API_KEY` and `HELIX_AI_MODEL` as environment variables for an available OpenAI text model, then restart HELIX. On Windows PowerShell for the current terminal:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
$env:HELIX_AI_MODEL = "your-available-model-id"
python -m ui.app
```

Do not commit or share keys. ChatGPT subscriptions do not configure API billing. Research pages work without AI setup. Reports use the OpenAI Responses API with `store=false`; provider data handling still applies. Click **View AI evidence** to inspect exactly what is included, select the sharing checkbox, then request a report. API charges may apply. Notebook text, brokerage tokens, account IDs and credentials are excluded. Portfolio reports use last-loaded holdings; click **Holdings health** and **Historical risk** to enrich their evidence. AI reports have no web browsing and must identify unsupported claims and missing data.

### Brokerage imports

See [PLAID_SETUP.md](PLAID_SETUP.md). Production requires approved institution/product access and explicit configuration. The existing encrypted token mechanism is Windows-only. The desktop uses the same local Windows user to retrieve the encrypted token, not a remotely exposed credential endpoint.

Only long USD equities, ETFs and mutual funds with valid tickers, positive quantities and known total cost basis are accepted. Plaid's **total** cost basis is divided by quantity, and positions sharing a ticker are aggregated at a weighted per-share basis. Cash, options, shorts, other currencies and missing basis are listed as excluded and block import. An import replaces all local positions after writing an exclusive timestamped backup; it never silently merges them. Sandbox imports are explicitly labeled. Institution data may lag the market; preview is not a real-time sync.

Install optional connector dependencies to run connector security tests; those tests skip when dependencies are absent. Calculation, normalization, evidence-sharing and mocked provider tests do not make external calls. Desktop visual checks and real OpenAI/Plaid end-to-end checks require their respective environments and credentials.

API references: [Plaid Investments](https://plaid.com/docs/api/products/investments/) · [OpenAI Responses](https://developers.openai.com/api/reference/resources/responses/methods/create)
