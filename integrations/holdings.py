"""Pure normalization for long, USD, quoted brokerage holdings."""
import math
import re


def finite(value):
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def normalize_snapshot(payload, environment='sandbox'):
    securities = {s['security_id']: s for s in payload.get('securities', [])}
    aggregate, skipped = {}, []
    for holding in payload.get('holdings', []):
        security = securities.get(holding.get('security_id'), {})
        ticker = (security.get('ticker_symbol') or '').upper()
        quantity = finite(holding.get('quantity'))
        cost = finite(holding.get('cost_basis'))
        currency = holding.get('iso_currency_code') or security.get('iso_currency_code')
        if (not re.fullmatch(r'[A-Z0-9.^=-]{1,15}', ticker) or quantity is None or quantity <= 0
                or cost is None or cost < 0 or currency != 'USD'
                or security.get('type') not in ('equity', 'etf', 'mutual fund')):
            skipped.append({'name': security.get('name', ticker or 'Unidentified security'),
                            'reason': 'Requires long USD equity/fund, valid ticker, quantity and reported cost basis.'})
            continue
        row = aggregate.setdefault(ticker, {'shares': 0, 'total_cost': 0})
        row['shares'] += quantity
        row['total_cost'] += cost
    positions = {t: {'shares': row['shares'], 'cost_basis': row['total_cost']/row['shares']}
                 for t, row in aggregate.items()}
    return {'positions': positions, 'skipped': skipped, 'environment': environment,
            'account_count': len(payload.get('accounts', []))}


def fetch_snapshot():
    # The desktop uses the same Windows user's encrypted token; no token is exposed to the UI.
    import os
    from integrations.plaid_server import load_item, create_client, response_dict
    from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
    item = load_item()
    if not item:
        raise ValueError('Connect a brokerage in the browser first.')
    response = response_dict(create_client().investments_holdings_get(
        InvestmentsHoldingsGetRequest(access_token=item['access_token'])))
    snapshot = normalize_snapshot(response, os.environ.get('PLAID_ENV', 'sandbox').lower())
    from analytics.research_hub import now
    snapshot['retrieved_at'] = now()
    return snapshot


def import_snapshot(snapshot):
    """Explicit UI action only. Excludes partial snapshots and creates an exclusive backup."""
    import json
    from datetime import datetime, timezone
    from pathlib import Path
    import portfolio_manager as pm
    if snapshot['skipped']:
        raise ValueError('Import blocked: unsupported or incomplete holdings. Resolve them before replacing the portfolio.')
    if not snapshot['positions']:
        raise ValueError('No supported positions to import.')
    pm.validate_portfolio(snapshot['positions'])
    path = Path(pm.PORTFOLIO_FILE)
    backup = path.with_name('portfolio.backup.'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
    if path.exists():
        with backup.open('xb') as file:
            file.write(path.read_bytes())
    # Bind provenance to the exact imported positions, so manual edits invalidate it.
    import hashlib
    marker = {'environment': snapshot['environment'], 'imported_at': datetime.now(timezone.utc).isoformat(),
              'fingerprint': hashlib.sha256(json.dumps(snapshot['positions'], sort_keys=True).encode()).hexdigest()}
    path.with_name('portfolio_source.json').write_text(json.dumps(marker), encoding='utf-8')
    pm.save_portfolio(snapshot['positions'])
    return str(backup) if backup.exists() else 'No previous portfolio existed.'


def portfolio_source():
    import hashlib
    import json
    from pathlib import Path
    import portfolio_manager as pm
    try:
        marker = json.loads(Path(pm.PORTFOLIO_FILE).with_name('portfolio_source.json').read_text())
        fingerprint = hashlib.sha256(json.dumps(pm.load_portfolio(), sort_keys=True).encode()).hexdigest()
        if marker.get('fingerprint') == fingerprint:
            return 'Plaid '+marker['environment'].upper()+' import · '+marker['imported_at']
    except (OSError, ValueError, KeyError):
        pass
    return 'Manually maintained portfolio'
