import ast
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

# Keep regression checks independent of network access and optional UI packages.
try:
    import yfinance
except ImportError:
    sys.modules['yfinance'] = types.ModuleType('yfinance')

import portfolio_manager as pm
from analytics import ai_analysis as analysis
from market.fundamentals import _series
from ui import data


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'portfolio.json'
        self.storage = patch.object(pm, 'PORTFOLIO_FILE', self.path)
        self.storage.start()
        pm.save_portfolio({'A': {'shares': 1, 'cost_basis': 80}})

    def tearDown(self):
        self.storage.stop()
        self.temp.cleanup()

    def call(self, function, inputs):
        with patch('builtins.input', side_effect=inputs), contextlib.redirect_stdout(io.StringIO()):
            function()

    def test_invalid_purchase_does_not_change_storage(self):
        before = self.path.read_bytes()
        for value in ['-2', '0', 'nan', 'inf', 'abc']:
            self.call(pm.buy_more_shares, ['A', value])
            self.assertEqual(before, self.path.read_bytes())

    def test_valid_buy_retains_cost_precision(self):
        self.call(pm.buy_more_shares, ['A', '2', '100'])
        position = pm.load_portfolio()['A']
        self.assertEqual(position['shares'], 3)
        self.assertAlmostEqual(position['cost_basis'] * 3, 280)

    def test_sell_entire_position(self):
        self.call(pm.sell_shares, ['A', '1'])
        self.assertEqual(pm.load_portfolio(), {})

    def test_oversell_and_nonfinite_sell_do_not_change_storage(self):
        before = self.path.read_bytes()
        for value in ['2', 'nan', '-1']:
            self.call(pm.sell_shares, ['A', value])
            self.assertEqual(before, self.path.read_bytes())

    def test_add_validation_and_ticker_normalization(self):
        self.call(pm.add_position, [' b ', '2', '0'])
        self.assertEqual(pm.load_portfolio()['B'], {'shares': 2, 'cost_basis': 0})
        before = self.path.read_bytes()
        self.call(pm.add_position, ['invalid ticker'])
        self.assertEqual(before, self.path.read_bytes())

    def test_atomic_save_failure_preserves_original(self):
        before = self.path.read_bytes()
        with patch.object(pm.os, 'replace', side_effect=OSError('disk error')):
            with self.assertRaises(OSError):
                pm.save_portfolio({})
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_bad_file_is_not_silently_replaced(self):
        self.path.write_text('{broken')
        with self.assertRaises(json.JSONDecodeError):
            pm.load_portfolio()
        self.assertEqual(self.path.read_text(), '{broken')

    def test_launch_directory_does_not_change_data_source(self):
        old = os.getcwd()
        try:
            os.chdir(self.temp.name)
            self.assertIn('A', pm.load_portfolio())
        finally:
            os.chdir(old)


class AnalysisTests(unittest.TestCase):
    def test_missing_quote_rejects_entire_valuation(self):
        holdings = {'A': {'shares': 1, 'cost_basis': 80}, 'B': {'shares': 1, 'cost_basis': 200}}
        with patch.object(analysis, 'load_portfolio', return_value=holdings), patch.object(analysis, 'get_current_price', side_effect=[100, None]):
            with self.assertRaisesRegex(ValueError, 'B'):
                analysis.get_portfolio_analysis()

    def test_zero_shares_are_safe(self):
        with patch.object(analysis, 'load_portfolio', return_value={'A': {'shares': 0, 'cost_basis': 80}}):
            self.assertIsNone(analysis.get_portfolio_analysis())

    def test_valid_portfolio_totals(self):
        with patch.object(analysis, 'load_portfolio', return_value={'A': {'shares': 2, 'cost_basis': 80}}), patch.object(analysis, 'get_current_price', return_value=100):
            result = analysis.get_portfolio_analysis()
        self.assertEqual(result['portfolio_value'], 200)
        self.assertEqual(result['portfolio_return'], 25)

    def test_partial_daily_change_is_unavailable(self):
        result = {'positions': [{'ticker': 'A', 'shares': 1}, {'ticker': 'B', 'shares': 1}]}
        with patch.object(data, 'get_portfolio_analysis', return_value=result), patch.object(data, 'get_daily_change', side_effect=[{'dollar': 1}, None]):
            self.assertIsNone(data.load_dashboard_data()['today_change'])

    def test_portfolio_page_imports_used_theme_name(self):
        source = Path(__file__).resolve().parents[1] / 'ui' / 'portfolio_page.py'
        tree = ast.parse(source.read_text())
        imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == 'ui.theme' for a in n.names}
        self.assertIn('SURFACE_ALT', imported)

    def test_worsening_losses_have_negative_growth(self):
        class Statement:
            empty = False
            index = ['Net Income']
            @property
            def loc(self): return self
            def __getitem__(self, key): return {'new': -200, 'old': -100}[key[1]]
        series = _series(Statement(), ('Net Income',), ['new', 'old'])
        self.assertEqual(series[0]['yoy'], -100)


class RefreshTests(unittest.TestCase):
    def shell(self, loader):
        import queue
        import threading
        source = Path(__file__).resolve().parents[1] / 'ui' / 'app.py'
        tree = ast.parse(source.read_text())
        original = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        method = next(node for node in original.body if isinstance(node, ast.FunctionDef) and node.name == 'refresh_data')
        shell = ast.ClassDef(name='Shell', bases=[], keywords=[], body=[method], decorator_list=[])
        module = ast.fix_missing_locations(ast.Module(body=[shell], type_ignores=[]))
        namespace = {'queue': queue, 'threading': threading, 'load_dashboard_data': loader}
        exec(compile(module, str(source), 'exec'), namespace)
        app = namespace['Shell']()
        app.refreshing = False
        app.refresh_error = None
        app.analysis = {'portfolio_value': 123, 'portfolio_cost': 100}
        app.page_name = 'Dashboard'
        app.show_page = lambda page: None
        app.pending = []
        app.after = lambda delay, callback: app.pending.append(callback)
        return app

    def run_refresh(self, app):
        class ImmediateThread:
            def __init__(self, target, **kwargs): self.target = target
            def start(self): self.target()
        with patch('threading.Thread', ImmediateThread):
            app.refresh_data()
        app.pending.pop(0)()

    def test_failed_refresh_retains_values_without_snapshot(self):
        def fail(): raise ValueError('Missing B quote')
        app = self.shell(fail)
        previous = app.analysis
        with patch('analytics.performance_history.record_snapshot') as record:
            self.run_refresh(app)
        self.assertIs(app.analysis, previous)
        self.assertIn('B', app.refresh_error)
        self.assertFalse(app.refreshing)
        record.assert_not_called()

    def test_successful_refresh_records_complete_values(self):
        values = {'portfolio_value': 200, 'portfolio_cost': 160}
        app = self.shell(lambda: values)
        with patch('analytics.performance_history.record_snapshot') as record:
            self.run_refresh(app)
        self.assertIs(app.analysis, values)
        record.assert_called_once_with(200, 160)
        self.assertIsNone(app.refresh_error)


if __name__ == '__main__':
    unittest.main()
