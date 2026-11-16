"""Local, read-only Plaid Investments connector for HELIX.

This service deliberately exposes no payment, transfer, or trading endpoint.
It listens only on 127.0.0.1 and defaults to Plaid Sandbox.
"""

import base64
import ctypes
import json
import os
import secrets
from pathlib import Path

import plaid
from flask import Flask, jsonify, make_response, request
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.item_remove_request import ItemRemoveRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products


APP_NAME = "HELIX"
LOCAL_URL = "http://127.0.0.1:8765"
DATA_PATH = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "HELIX" / "plaid_item.bin"


class DataBlob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(data):
    buffer = ctypes.create_string_buffer(data)
    return DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer


def protect_for_current_windows_user(value):
    """Encrypt bytes with Windows DPAPI; only this Windows user can decrypt them."""
    if os.name != "nt":
        raise RuntimeError("Brokerage token storage requires Windows DPAPI.")
    source, keepalive = _blob(value)
    target = DataBlob()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(source), "HELIX Plaid token", None, None, None, 0, ctypes.byref(target)
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(target.pbData)


def unprotect_for_current_windows_user(value):
    if os.name != "nt":
        raise RuntimeError("Brokerage token storage requires Windows DPAPI.")
    source, keepalive = _blob(value)
    target = DataBlob()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(source), None, None, None, None, 0, ctypes.byref(target)
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(target.pbData)


def save_item(item):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(item).encode("utf-8")
    DATA_PATH.write_bytes(base64.b64encode(protect_for_current_windows_user(payload)))


def load_item():
    if not DATA_PATH.exists():
        return None
    encrypted = base64.b64decode(DATA_PATH.read_bytes())
    return json.loads(unprotect_for_current_windows_user(encrypted).decode("utf-8"))


def clear_item():
    if DATA_PATH.exists():
        DATA_PATH.unlink()


def create_client():
    client_id = os.environ.get("PLAID_CLIENT_ID")
    secret = os.environ.get("PLAID_SECRET")
    if not client_id or not secret:
        raise RuntimeError("Plaid credentials are not configured. See PLAID_SETUP.md.")

    environment = os.environ.get("PLAID_ENV", "sandbox").lower()
    if environment not in {"sandbox", "production"}:
        raise RuntimeError("PLAID_ENV must be either sandbox or production.")
    if environment == "production" and os.environ.get("HELIX_ALLOW_PRODUCTION") != "YES":
        raise RuntimeError("Production is disabled. Set HELIX_ALLOW_PRODUCTION=YES only after reviewing PLAID_SETUP.md.")

    host = plaid.Environment.Sandbox if environment == "sandbox" else plaid.Environment.Production
    configuration = plaid.Configuration(
        host=host,
        api_key={"clientId": client_id, "secret": secret, "plaidVersion": "2020-09-14"},
    )
    return plaid_api.PlaidApi(plaid.ApiClient(configuration))


def response_dict(response):
    return response.to_dict() if hasattr(response, "to_dict") else response


def normalize_holdings(payload):
    from integrations.holdings import normalize_snapshot
    snapshot = normalize_snapshot(payload)
    return [{"ticker": ticker, **position} for ticker, position in snapshot["positions"].items()]


app = Flask(__name__)
CSRF_TOKEN = secrets.token_urlsafe(32)
app.config.update(
    SECRET_KEY=secrets.token_urlsafe(32),
    SESSION_COOKIE_SECURE=False,  # This service is deliberately localhost-only.
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
)


@app.before_request
def validate_local_origin():
    if request.host != "127.0.0.1:8765":
        return jsonify({"error": "Invalid local host."}), 403
    origin = request.headers.get("Origin")
    if origin and origin != LOCAL_URL:
        return jsonify({"error": "Invalid local origin."}), 403
    if request.headers.get("Sec-Fetch-Site") == "cross-site":
        return jsonify({"error": "Cross-site access denied."}), 403


@app.after_request
def add_security_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.plaid.com; "
        "style-src 'self' 'unsafe-inline'; frame-src https://cdn.plaid.com; "
        "connect-src 'self' https://sandbox.plaid.com https://production.plaid.com"
    )
    return response


@app.get("/")
def index():
    return make_response("""<!doctype html><html><head><meta charset='utf-8'><title>HELIX secure connection</title></head>
<body><h1>Connect a brokerage to HELIX</h1><p>Holdings only. HELIX cannot place trades or transfers.</p>
<button id='connect'>Connect brokerage</button><pre id='status'></pre>
<script src='https://cdn.plaid.com/link/v2/stable/link-initialize.js'></script><script>
const status = document.getElementById('status'); const csrf = '""" + CSRF_TOKEN + """';
document.getElementById('connect').onclick = async () => {
  status.textContent = 'Opening secure brokerage connection…';
  const token = await (await fetch('/api/link-token', {method:'POST', headers:{'X-HELIX-CSRF':csrf}})).json();
  if (token.error) { status.textContent = token.error; return; }
  Plaid.create({token: token.link_token, onSuccess: async (public_token) => {
    const result = await (await fetch('/api/exchange-token', {method:'POST', headers:{'Content-Type':'application/json','X-HELIX-CSRF':csrf}, body:JSON.stringify({public_token})})).json();
    status.textContent = result.error || 'Connected. You may return to HELIX.';
  }, onExit: (error) => { if (error) status.textContent = error.display_message || 'Connection cancelled.'; }}).open();
};</script></body></html>""")


@app.post("/api/link-token")
def link_token():
    if request.headers.get("X-HELIX-CSRF") != CSRF_TOKEN:
        return jsonify({"error": "Invalid local request."}), 403
    try:
        client = create_client()
        token_request = LinkTokenCreateRequest(
            products=[Products("investments")],
            client_name=APP_NAME,
            country_codes=[CountryCode("US")],
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id="helix-local-user"),
        )
        return jsonify(response_dict(client.link_token_create(token_request)))
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@app.post("/api/exchange-token")
def exchange_token():
    if request.headers.get("X-HELIX-CSRF") != CSRF_TOKEN:
        return jsonify({"error": "Invalid local request."}), 403
    public_token = (request.get_json(silent=True) or {}).get("public_token")
    if not public_token:
        return jsonify({"error": "Missing public token."}), 400
    try:
        client = create_client()
        response = response_dict(client.item_public_token_exchange(ItemPublicTokenExchangeRequest(public_token=public_token)))
        save_item({"access_token": response["access_token"], "item_id": response["item_id"]})
        return jsonify({"connected": True})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@app.get("/api/holdings")
def holdings():
    item = load_item()
    if not item:
        return jsonify({"error": "No brokerage is connected."}), 404
    try:
        client = create_client()
        response = response_dict(client.investments_holdings_get(InvestmentsHoldingsGetRequest(access_token=item["access_token"])))
        from integrations.holdings import normalize_snapshot
        return jsonify(normalize_snapshot(response, os.environ.get("PLAID_ENV", "sandbox")))
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@app.post("/api/disconnect")
def disconnect():
    if request.headers.get("X-HELIX-CSRF") != CSRF_TOKEN:
        return jsonify({"error": "Invalid local request."}), 403
    item = load_item()
    if not item:
        return jsonify({"connected": False})
    try:
        create_client().item_remove(ItemRemoveRequest(access_token=item["access_token"]))
        clear_item()
        return jsonify({"connected": False})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=False)
