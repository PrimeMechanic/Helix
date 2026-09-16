# Plaid connection setup for HELIX

This connector is **holdings-only**. It has no transfers, payments, trading,
account/routing numbers, or transaction-history endpoints.

## Start in Sandbox

1. Create a Plaid developer account and use its Sandbox API keys.
2. Install `requirements-plaid.txt` in your Python virtual environment.
3. Set `PLAID_CLIENT_ID` and `PLAID_SECRET` as user environment variables. Never put them in source code, `portfolio.json`, or Git.
4. Leave `PLAID_ENV` unset; it defaults to `sandbox`.
5. Run `python -m integrations.plaid_server`, then visit `http://127.0.0.1:8765`.

After a successful connection, the service creates `%LOCALAPPDATA%\\HELIX\\plaid_item.bin`. Windows DPAPI encrypts it for the current Windows user.

## Before using a real brokerage

Test Sandbox first. Production requires both `PLAID_ENV=production` and
`HELIX_ALLOW_PRODUCTION=YES`, preventing an accidental live connection. Approve
only read access to investment holdings. If a consent screen requests trading,
money transfers, or account changes, cancel it.

`POST /api/disconnect` revokes the Plaid Item and deletes the local encrypted token.
