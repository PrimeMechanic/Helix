import io
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from analytics import research_hub as hub
from integrations import ai_research, holdings
import portfolio_manager as pm


class Calculations(unittest.TestCase):
    def setUp(self):
        self.positions = [{'ticker': 'A', 'value': 600, 'shares': 6}, {'ticker': 'B', 'value': 400, 'shares': 4}]

    def test_concentration(self):
        result = hub.concentration(self.positions)
        self.assertEqual(result['largest_weight_pct'], 60)
        self.assertAlmostEqual(result['effective_positions'], 1/.52)

    def test_stress(self):
        self.assertEqual(hub.stress_test(self.positions, -20)['scenario_value'], 800)
        self.assertEqual(hub.stress_test(self.positions, -100)['scenario_value'], 0)
        for value in [float('nan'), -101, 101, 'x']:
            with self.assertRaises(ValueError): hub.stress_test(self.positions, value)

    def test_rebalance_accounts_for_cash(self):
        result = hub.rebalance(self.positions, {'A': 50, 'B': 50}, 200)
        self.assertEqual([r['dollar_change'] for r in result], [0, 200])

    def test_bad_targets(self):
        for targets in [{'A': 20, 'B': 20}, {'A': -10, 'B': 110}, {'A': 100}, {'A': float('nan'), 'B': 50}]:
            with self.assertRaises(ValueError): hub.rebalance(self.positions, targets)

    def test_dcf_constant_perpetuity(self):
        result = hub.dcf(100, 0, 10, 0, 10, 0)
        self.assertAlmostEqual(result['value_per_share'], 100)
        self.assertAlmostEqual(hub.dcf(100, 0, 10, 0, 10, 200)['value_per_share'], 80)

    def test_invalid_dcf(self):
        for args in [(100, 5, 3, 3, 10), (0, 5, 10, 3, 10), (100, 5, 10, 3, 0), (100, float('nan'), 10, 3, 10)]:
            with self.assertRaises(ValueError): hub.dcf(*args)

    def test_sentiment_formula_and_limits(self):
        result = hub.sentiment_from_series([100]*200, [25], [1.1]*11)
        self.assertEqual(result['score'], 67)
        self.assertEqual(result['label'], 'Greed')
        self.assertEqual(result['components']['Sector breadth'], 100)

    def test_missing_sentiment_is_not_neutral(self):
        for args in [([100]*199, [25], [1.1]*11), ([100]*200, [], [1.1]*11), ([100]*200, [25], [1.1]*10), ([100]*200, [float('nan')], [1.1]*11)]:
            with self.assertRaises(ValueError): hub.sentiment_from_series(*args)

    def test_historical_risk_uses_common_dates_and_known_beta(self):
        import pandas as pd
        prices = pd.DataFrame({'A': [100*(1.01 if i % 2 else 1.005)**i for i in range(80)]})
        prices['SPY'] = prices['A']
        result = hub.risk_from_prices(prices, {'A': 1})
        self.assertAlmostEqual(result['beta_vs_spy'], 1)
        self.assertAlmostEqual(result['correlation_vs_spy'], 1)
        self.assertEqual(result['daily_observations'], 79)
        with self.assertRaises(ValueError):
            hub.risk_from_prices(prices.iloc[:30], {'A': 1})

    def test_ticker_validation(self):
        self.assertEqual(hub.symbol(' brk-b '), 'BRK-B')
        with self.assertRaises(ValueError): hub.symbol('../secrets')

    def test_company_missing_is_explicit(self):
        with patch.object(hub.yf, 'Ticker') as ticker:
            ticker.return_value.get_info.return_value = {}
            with self.assertRaises(ValueError): hub.company_research('BAD')

    def test_comparison_keeps_failed_symbols(self):
        with patch.object(hub, 'company_research', side_effect=[{'ticker': 'A'}, ValueError('missing')]):
            result = hub.compare_companies('A, B, A')
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]['error'], 'missing')

    def test_notes_persist_and_are_isolated(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'LOCALAPPDATA': folder}):
            hub.notebook('A', 'My thesis')
            self.assertEqual(hub.notebook('A'), 'My thesis')
            self.assertIn('Thesis:', hub.notebook('B'))

    def test_portfolio_health_coverage(self):
        company = {'ticker': 'A', 'sector': 'Technology', 'currency': 'USD', 'metrics': {'dividendRate': 2}, 'statements': {'health': {'score': 80}}}
        with patch.object(hub, 'company_research', side_effect=[company, ValueError('missing')]):
            result = hub.portfolio_research(self.positions)
        self.assertEqual(result['business_health_value_coverage_pct'], 60)
        self.assertEqual(result['covered_business_health'], 80)
        self.assertEqual(result['estimated_annual_usd_dividend'], 12)
        self.assertEqual(result['dividend_value_coverage_pct'], 60)


class Brokerage(unittest.TestCase):
    def payload(self, cost=1000, currency='USD', kind='equity'):
        return {'securities': [{'security_id': 's', 'ticker_symbol': 'A', 'type': kind, 'iso_currency_code': currency}],
                'holdings': [{'security_id': 's', 'quantity': 10, 'cost_basis': cost, 'iso_currency_code': currency}], 'accounts': []}

    def test_total_basis_converted_to_per_share(self):
        row = holdings.normalize_snapshot(self.payload())['positions']['A']
        self.assertEqual(row, {'shares': 10, 'cost_basis': 100})

    def test_multiple_accounts_aggregate_weighted_basis(self):
        payload = self.payload()
        payload['holdings'].append({'security_id': 's', 'quantity': 5, 'cost_basis': 1000, 'iso_currency_code': 'USD'})
        row = holdings.normalize_snapshot(payload)['positions']['A']
        self.assertEqual(row['shares'], 15)
        self.assertAlmostEqual(row['cost_basis'], 2000/15)

    def test_missing_basis_and_unsupported_types_not_silently_zero(self):
        for payload in [self.payload(None), self.payload(currency='EUR'), self.payload(kind='option')]:
            result = holdings.normalize_snapshot(payload)
            self.assertEqual(result['positions'], {})
            self.assertEqual(len(result['skipped']), 1)

    def test_import_backup_and_provenance(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(pm, 'PORTFOLIO_FILE', Path(folder)/'portfolio.json'):
            pm.save_portfolio({'OLD': {'shares': 1, 'cost_basis': 20}})
            before = pm.PORTFOLIO_FILE.read_bytes()
            result = holdings.normalize_snapshot(self.payload())
            backup = holdings.import_snapshot(result)
            self.assertEqual(Path(backup).read_bytes(), before)
            self.assertEqual(pm.load_portfolio()['A']['cost_basis'], 100)
            self.assertIn('SANDBOX', holdings.portfolio_source())
            pm.save_portfolio({'B': {'shares': 1, 'cost_basis': 20}})
            self.assertEqual(holdings.portfolio_source(), 'Manually maintained portfolio')

    def test_partial_import_blocked(self):
        result = holdings.normalize_snapshot(self.payload(None))
        with patch.object(pm, 'save_portfolio') as save:
            with self.assertRaises(ValueError): holdings.import_snapshot(result)
            save.assert_not_called()


class AIReports(unittest.TestCase):
    def test_no_consent_no_request(self):
        with patch.object(ai_research, 'urlopen') as request:
            with self.assertRaises(ValueError): ai_research.generate_report({}, 'Question')
            request.assert_not_called()

    def test_no_credentials_no_request(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(ai_research, 'urlopen') as request:
            with self.assertRaises(ValueError): ai_research.generate_report({}, 'Question', True)
            request.assert_not_called()

    def test_payload_and_response(self):
        response = {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'Evidence report'}]}]}
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-secret', 'HELIX_AI_MODEL': 'test-model'}), patch.object(ai_research, 'urlopen') as request:
            request.return_value.__enter__.return_value = io.BytesIO(json.dumps(response).encode())
            text = ai_research.generate_report({'source': 'Test'}, 'Question', True)
            payload = json.loads(request.call_args.args[0].data)
        self.assertEqual(text, 'Evidence report')
        self.assertFalse(payload['store'])
        self.assertNotIn('test-secret', json.dumps(payload))
        self.assertIn('Test', payload['input'])


@unittest.skipUnless(importlib.util.find_spec('flask') and importlib.util.find_spec('plaid'), 'Optional connector dependencies are not installed')
class LocalConnector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from integrations.plaid_server import app
        cls.client = app.test_client()

    def test_dns_rebinding_rejected(self):
        self.assertEqual(self.client.get('/', base_url='http://evil.example:8765').status_code, 403)

    def test_cross_origin_rejected(self):
        self.assertEqual(self.client.get('/api/holdings', base_url='http://127.0.0.1:8765', headers={'Origin': 'https://example.com'}).status_code, 403)

    def test_csrf_required(self):
        self.assertEqual(self.client.post('/api/link-token', base_url='http://127.0.0.1:8765').status_code, 403)

    def test_connector_landing_page(self):
        self.assertEqual(self.client.get('/', base_url='http://127.0.0.1:8765').status_code, 200)


if __name__ == '__main__':
    unittest.main()
