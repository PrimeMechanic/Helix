"""Asynchronous desktop workspace for portfolio and company research."""
import json
import queue
import threading
import webbrowser
from tkinter import messagebox

import customtkinter as ctk

from analytics import research_hub as research
from integrations.ai_research import generate_report
from integrations.holdings import fetch_snapshot, import_snapshot
from ui.theme import BACKGROUND, SURFACE, TEXT, MUTED, ACCENT


def display(value):
    return json.dumps(value, indent=2, ensure_ascii=False, default=str, allow_nan=False)


def readable(value, depth=0):
    """Human-readable research output; raw payloads are reserved for evidence review."""
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            title = key.replace('_', ' ').replace(' pct', ' (%)').capitalize()
            if isinstance(item, (dict, list)):
                lines.append('  '*depth+title+'\n'+readable(item, depth+1))
            else:
                text = 'Unavailable' if item is None else f'{item:,.2f}' if isinstance(item, float) else str(item)
                lines.append('  '*depth+title+': '+text)
        return '\n'.join(lines)
    if isinstance(value, list):
        return '\n\n'.join(readable(item, depth) for item in value)
    return str(value)


def metric(value, percent=False):
    return 'Unavailable' if value is None else f'{value*100:,.1f}%' if percent else f'{value:,.2f}'


def company_text(company):
    if company.get('error'):
        return f"{company['ticker']} · {company['error']}"
    m = company['metrics']
    lines = [f"{company['ticker']}  |  {company['name']}",
             f"{company['sector']} · {company['currency']} · {company.get('quote_type', '')}",
             f"Source: {company['source']} · Retrieved {company['retrieved_at']}", '',
             'VALUATION', f"Price: {metric(m['currentPrice'] or m['regularMarketPrice'])}   Market cap: {metric(m['marketCap'])}",
             f"Trailing P/E: {metric(m['trailingPE'])}   Forward P/E: {metric(m['forwardPE'])}   P/S: {metric(m['priceToSalesTrailing12Months'])}",
             '', 'GROWTH & INCOME',
             f"Revenue growth: {metric(m['revenueGrowth'], True)}   Earnings growth: {metric(m['earningsGrowth'], True)}",
             f"Profit margin: {metric(m['profitMargins'], True)}   Operating margin: {metric(m['operatingMargins'], True)}",
             f"Free cash flow: {metric(m['freeCashflow'])}   Annual dividend/share: {metric(m['dividendRate'])}",
             f"Payout ratio: {metric(m['payoutRatio'], True)}   Cash: {metric(m['totalCash'])}   Debt: {metric(m['totalDebt'])}",
             '', 'BUSINESS HEALTH — ANNUAL STATEMENTS']
    health = company.get('statements', {}).get('health')
    if health:
        lines.extend([f"{health['score']} / 100 · {health['band']} · {health['coverage']}", health['summary']])
        for pillar in health['pillars']:
            lines.append(f"\n{pillar['name']} · {metric(pillar['score'])} / 100")
            lines.extend(f"  {item['label']}: {item['display']}" for item in pillar['metrics'])
        lines.extend('• '+flag for flag in health['flags'])
    else:
        lines.append(company.get('statement_warning', 'Unavailable'))
    lines.extend(['', 'Growth fields are vendor-reported; statement dates and year-over-year comparisons are in the evidence. Ratios are not comparable across all sectors.'])
    return '\n'.join(lines)


class ResearchHub(ctk.CTkFrame):
    def __init__(self, master, analysis=None, on_refresh=None):
        super().__init__(master, fg_color=BACKGROUND)
        self.analysis = analysis
        self.on_refresh = on_refresh
        self.evidence = None
        self.snapshot = None
        self.busy = False
        self.results = queue.Queue()
        self.job = None
        ctk.CTkLabel(self, text='Research workspace', font=('Arial', 30, 'bold'), text_color=TEXT).pack(anchor='w', padx=28, pady=(24, 3))
        ctk.CTkLabel(self, text='Understand the business. Inspect your exposure. Build a stronger thesis.', text_color=MUTED).pack(anchor='w', padx=28)
        self.status = ctk.CTkLabel(self, text='Ready · Data loads on demand', text_color=ACCENT)
        self.status.pack(anchor='w', padx=28, pady=6)
        self.tabs = ctk.CTkTabview(self, fg_color=SURFACE)
        self.tabs.pack(fill='both', expand=True, padx=22, pady=(0, 18))
        for name in ('Portfolio lab', 'Companies', 'Sentiment', 'Valuation', 'Notebook', 'Brokerage'):
            self.tabs.add(name)
        self.build_portfolio()
        self.build_companies()
        self.build_sentiment()
        self.build_valuation()
        self.build_notebook()
        self.build_brokerage()
        self.poll_id = self.after(100, self.poll)

    def destroy(self):
        if getattr(self, 'poll_id', None):
            self.after_cancel(self.poll_id)
            self.poll_id = None
        super().destroy()

    def label(self, parent, text):
        ctk.CTkLabel(parent, text=text, text_color=MUTED, wraplength=850, justify='left').pack(anchor='w', padx=12, pady=(6, 3))

    def row(self, parent):
        row = ctk.CTkFrame(parent, fg_color='transparent')
        row.pack(fill='x', padx=12, pady=5)
        return row

    def entry(self, parent, placeholder, value=None, width=160):
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, width=width)
        entry.pack(side='left', padx=(0, 8), pady=3)
        if value is not None:
            entry.insert(0, str(value))
        return entry

    def button(self, parent, title, callback):
        ctk.CTkButton(parent, text=title, command=callback, width=140).pack(side='left', padx=(0, 8), pady=3)

    def output(self, parent, height=280):
        box = ctk.CTkTextbox(parent, height=height, font=('Arial', 14), wrap='word')
        box.pack(fill='both', expand=True, padx=12, pady=8)
        box.configure(state='disabled')
        return box

    def write(self, box, text):
        box.configure(state='normal')
        box.delete('1.0', 'end')
        box.insert('1.0', text)
        box.configure(state='disabled')

    def run(self, work, finish):
        if self.busy:
            self.status.configure(text='A request is running. Wait for it to finish.')
            return
        self.busy = True
        self.status.configure(text='Loading… You can continue using other tabs.')
        def worker():
            try:
                self.results.put((finish, work(), None))
            except Exception as error:
                self.results.put((finish, None, str(error)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            finish, value, error = self.results.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            if error:
                self.status.configure(text='Request failed · '+error[:250])
            else:
                try:
                    finish(value)
                    self.status.configure(text='Updated · '+research.now())
                except Exception as error:
                    self.status.configure(text='Unable to display result · '+str(error)[:200])
        self.poll_id = self.after(100, self.poll)

    def positions(self):
        if not self.analysis:
            raise ValueError('Refresh portfolio prices from Settings first, then reopen the workspace.')
        return self.analysis['positions']

    def local(self, action):
        try:
            action()
        except Exception as error:
            self.status.configure(text=str(error)[:250])

    def build_portfolio(self):
        tab = self.tabs.tab('Portfolio lab')
        self.label(tab, 'Direct holdings concentration, uniform stress scenarios and a target-weight planner. All values use the last loaded portfolio prices; refresh Settings before reopening this workspace.')
        row = self.row(tab)
        self.shock = self.entry(row, 'Shock %', '-20', 100)
        self.button(row, 'Holdings health', self.load_portfolio_research)
        self.button(row, 'Stress test', lambda: self.local(self.stress))
        self.cash = self.entry(row, 'New cash', '0', 100)
        self.button(row, 'Plan rebalance', lambda: self.local(self.plan))
        self.label(tab, 'Targets: TICKER=percentage, separated by commas. Every holding must be included; totals must equal 100%. Dollar changes are hypothetical buys (+) / sells (−).')
        self.targets = ctk.CTkEntry(tab, placeholder_text='VOO=60, QQQM=40')
        self.targets.pack(fill='x', padx=12, pady=5)
        self.button(self.row(tab), 'Historical risk', self.load_risk)
        self.portfolio_output = self.output(tab)
        self.ai_controls(tab, 'portfolio')
        if self.analysis:
            self.local(self.show_concentration)
        else:
            self.write(self.portfolio_output, 'No complete portfolio valuation is loaded yet. Open Settings → Refresh portfolio.')

    def show_concentration(self):
        result = research.concentration(self.positions())
        self.portfolio_evidence = {'portfolio': self.analysis, 'concentration': result,
                                   'source': 'Local portfolio and latest available Yahoo quotes',
                                   'prepared_at': research.now(), 'quote_asof': 'Not supplied by legacy dashboard; refresh before research.'}
        self.write(self.portfolio_output, 'EXPOSURE SNAPSHOT\n\n'+readable(result))

    def load_portfolio_research(self):
        def start():
            positions = self.positions()
            def done(result):
                self.portfolio_evidence['holdings_research'] = result
                self.portfolio_consent.deselect()
                header = {k: v for k, v in result.items() if k != 'companies'}
                self.write(self.portfolio_output, 'PORTFOLIO BUSINESS HEALTH\n\n'+readable(header)+'\n\n'+
                           ('\n\n'+'─'*60+'\n\n').join(company_text(row) for row in result['companies']))
            self.run(lambda: research.portfolio_research(positions), done)
        self.local(start)

    def load_risk(self):
        def start():
            positions = self.positions()
            def done(result):
                self.portfolio_evidence['historical_risk'] = result
                self.portfolio_consent.deselect()
                self.write(self.portfolio_output, 'HISTORICAL RISK · Hypothetical current-weight portfolio\n\n'+readable(result))
            self.run(lambda: research.portfolio_risk(positions), done)
        self.local(start)

    def stress(self):
        result = research.stress_test(self.positions(), self.shock.get())
        self.write(self.portfolio_output, 'STRESS SCENARIO\n\n'+readable(result))

    def plan(self):
        targets = {}
        for pair in self.targets.get().split(','):
            ticker, weight = pair.split('=')
            ticker = research.symbol(ticker)
            if ticker in targets:
                raise ValueError('Duplicate target ticker.')
            targets[ticker] = float(weight)
        result = research.rebalance(self.positions(), targets, float(self.cash.get()))
        self.write(self.portfolio_output, 'REBALANCE PLAN · No orders are placed\n\n'+readable(result))

    def ai_controls(self, parent, scope):
        row = self.row(parent)
        consent = ctk.CTkCheckBox(row, text='Send this research data to OpenAI (API charges may apply)', width=360)
        consent.pack(side='left', padx=(0, 8))
        setattr(self, scope+'_consent', consent)
        self.button(row, 'View AI evidence', lambda: self.view_evidence(scope))
        self.button(row, 'AI research report', lambda: self.ai_report(scope))

    def get_evidence(self, scope):
        evidence = getattr(self, scope+'_evidence', None)
        if not evidence:
            raise ValueError('Load research data first.')
        return evidence

    def view_evidence(self, scope):
        def show():
            evidence = self.get_evidence(scope)
            window = ctk.CTkToplevel(self)
            window.title('Data included in AI request')
            window.geometry('850x620')
            self.write(self.output(window), display(evidence))
        self.local(show)

    def ai_report(self, scope):
        def start():
            evidence = self.get_evidence(scope)
            consent = bool(getattr(self, scope+'_consent').get())
            if not consent:
                raise ValueError('Select the data-sharing checkbox to request an AI report.')
            output = self.portfolio_output if scope == 'portfolio' else self.company_output
            question = self.question.get() if scope == 'company' else 'Assess my current holdings, concentration, portfolio health and evidence gaps. Discuss income/growth only where supplied data supports it.'
            self.run(lambda: generate_report(evidence, question, consent=True), lambda text: self.write(output, text))
        self.local(start)

    def build_companies(self):
        tab = self.tabs.tab('Companies')
        self.label(tab, 'Company health, valuation, profitability, income and growth. Compare up to eight tickers; statement-based health is available when annual filings are returned.')
        row = self.row(tab)
        self.tickers = self.entry(row, 'AAPL, MSFT, GOOGL', width=300)
        self.button(row, 'Research / compare', self.load_companies)
        self.question = ctk.CTkEntry(tab, placeholder_text='Research question')
        self.question.pack(fill='x', padx=12, pady=5)
        self.question.insert(0, 'Compare business health, valuation, growth durability, income and risks. What should I investigate before investing?')
        self.comparison = ctk.CTkScrollableFrame(tab, height=100, fg_color=BACKGROUND)
        self.comparison.pack(fill='x', padx=12, pady=4)
        self.company_output = self.output(tab)
        self.write(self.company_output, 'Enter tickers above. No model or API key is required for the research dashboard.\n\nOptional AI reports use OPENAI_API_KEY and HELIX_AI_MODEL from your environment. They use the evidence shown here and do not browse the web.')
        self.ai_controls(tab, 'company')

    def load_companies(self):
        text = self.tickers.get()
        def done(rows):
            self.company_evidence = {'companies': rows}
            self.company_consent.deselect()
            for child in self.comparison.winfo_children():
                child.destroy()
            headers = ('Ticker / currency', 'Trailing P/E', 'Revenue growth', 'Profit margin', 'Annual DPS')
            for col, heading in enumerate(headers):
                ctk.CTkLabel(self.comparison, text=heading, text_color=MUTED).grid(row=0, column=col, padx=12, pady=3, sticky='w')
            for index, item in enumerate(rows, 1):
                if item.get('error'):
                    values = (item['ticker'], 'Unavailable', 'Unavailable', 'Unavailable', 'Unavailable')
                else:
                    m = item['metrics']
                    values = (item['ticker']+' / '+item['currency'], metric(m['trailingPE']), metric(m['revenueGrowth'], True), metric(m['profitMargins'], True), metric(m['dividendRate']))
                for col, value in enumerate(values):
                    ctk.CTkLabel(self.comparison, text=value, text_color=TEXT).grid(row=index, column=col, padx=12, pady=3, sticky='w')
            self.write(self.company_output, ('\n\n'+'─'*60+'\n\n').join(company_text(row) for row in rows))
        self.run(lambda: research.compare_companies(text), done)

    def build_sentiment(self):
        tab = self.tabs.tab('Sentiment')
        self.label(tab, 'HELIX Fear / Greed proxy · Daily market observations, not a trading signal or the CNN index. Missing inputs produce an unavailable result.')
        self.button(self.row(tab), 'Refresh sentiment', lambda: self.run(research.market_sentiment, self.show_sentiment))
        scale = self.row(tab)
        for name, color in (('Extreme fear', '#FF7272'), ('Fear', '#E5AA72'), ('Neutral', '#B7BDCA'), ('Greed', '#79C9AF'), ('Extreme greed', '#55D692')):
            ctk.CTkLabel(scale, text=name, text_color=color).pack(side='left', expand=True)
        self.sentiment_meter = ctk.CTkProgressBar(tab, height=16, progress_color=ACCENT)
        self.sentiment_meter.pack(fill='x', padx=18, pady=8)
        self.sentiment_meter.set(0)
        self.sentiment_output = self.output(tab)
        self.write(self.sentiment_output, 'Load the latest available SPY, VIX and sector closes.\n\nThree equal-weight components:\n• SPY distance from its 200-day average\n• VIX level as a risk-appetite proxy\n• Share of 11 sector ETFs above their 50-day averages\n\nEvery result shows its market date and formula. This proxy excludes options positioning and credit spreads.')

    def show_sentiment(self, result):
        self.sentiment_meter.set(result['score']/100)
        self.write(self.sentiment_output, f"{result['score']} / 100  ·  {result['label'].upper()}\nMarket close: {result['market_date']}\n\n"+readable(result))

    def build_valuation(self):
        tab = self.tabs.tab('Valuation')
        self.label(tab, 'Five-year DCF sandbox · Enter unlevered free cash flow, net debt and diluted shares in the SAME units. Example: FCF and debt in millions, shares in millions. Rates are percentages. These are your assumptions, not price targets.')
        row = self.row(tab)
        self.fcf = self.entry(row, 'FCF', '1000', 130)
        self.shares = self.entry(row, 'Shares', '100', 130)
        self.debt = self.entry(row, 'Net debt', '0', 130)
        self.label(tab, 'First row: FCF / diluted shares / net debt. Second row: annual growth % / discount % / terminal growth %.')
        row = self.row(tab)
        self.growth = self.entry(row, 'Growth %', '8', 130)
        self.discount = self.entry(row, 'Discount %', '10', 130)
        self.terminal = self.entry(row, 'Terminal %', '3', 130)
        self.button(row, 'Calculate scenarios', lambda: self.local(self.calculate_dcf))
        self.valuation_output = self.output(tab)

    def calculate_dcf(self):
        fcf, growth, discount, terminal, shares, debt = [float(x.get()) for x in (self.fcf, self.growth, self.discount, self.terminal, self.shares, self.debt)]
        results = {label: research.dcf(fcf, g, discount, terminal, shares, debt)
                   for label, g in (('Lower growth (−3pp)', growth-3), ('Your base case', growth), ('Higher growth (+3pp)', growth+3))}
        self.write(self.valuation_output, readable(results))

    def build_notebook(self):
        tab = self.tabs.tab('Notebook')
        self.label(tab, 'Keep a local investment thesis, risks, evidence and earnings questions for each ticker. Notes remain on this computer and are not included in AI requests.')
        row = self.row(tab)
        self.note_ticker = self.entry(row, 'Ticker', width=160)
        self.button(row, 'Load thesis', lambda: self.local(self.load_note))
        self.button(row, 'Save thesis', lambda: self.local(self.save_note))
        self.loaded_note_ticker = None
        self.notes = ctk.CTkTextbox(tab, font=('Arial', 15), wrap='word')
        self.notes.pack(fill='both', expand=True, padx=12, pady=8)

    def load_note(self):
        ticker = research.symbol(self.note_ticker.get())
        text = research.notebook(ticker)
        self.notes.delete('1.0', 'end')
        self.notes.insert('1.0', text)
        self.loaded_note_ticker = ticker
        self.status.configure(text='Loaded thesis · '+ticker)

    def save_note(self):
        ticker = research.symbol(self.note_ticker.get())
        if self.loaded_note_ticker != ticker:
            raise ValueError('Load this ticker first so notes are saved to the correct company.')
        research.notebook(ticker, self.notes.get('1.0', 'end-1c'))
        self.status.configure(text='Saved thesis · '+ticker)

    def build_brokerage(self):
        tab = self.tabs.tab('Brokerage')
        self.label(tab, 'Connect with Plaid, preview holdings, then explicitly import. Windows encrypted token storage is required. Sandbox data is simulated. Real institutions require approved Plaid production access. Imports replace the local portfolio after creating a backup.')
        row = self.row(tab)
        self.button(row, 'Connect in browser', lambda: webbrowser.open('http://127.0.0.1:8765'))
        self.button(row, 'Preview holdings', lambda: self.run(fetch_snapshot, self.show_snapshot))
        self.button(row, 'Import preview', lambda: self.local(self.import_preview))
        self.broker_output = self.output(tab)
        self.write(self.broker_output, 'Start the optional local connector first:\n\npython -m pip install -r requirements-plaid.txt\npython -m integrations.plaid_server\n\nSee PLAID_SETUP.md for credentials.\n\nOnly long USD equities, ETFs and mutual funds with a reported cost basis can be imported. Cash, shorts, options, non-USD and incomplete holdings are listed as exclusions and block import, avoiding a silently incomplete portfolio.\n\nPlaid totals are converted to per-share basis. Identical tickers across accounts are aggregated. No orders, payments or transfers are supported.')

    def show_snapshot(self, snapshot):
        self.snapshot = snapshot
        self.write(self.broker_output, 'BROKERAGE PREVIEW · '+snapshot['environment'].upper()+'\n\n'+readable(snapshot))

    def import_preview(self):
        if self.busy:
            raise ValueError('Wait for the current request to finish.')
        if not self.snapshot:
            raise ValueError('Preview holdings first.')
        if not messagebox.askyesno('Replace portfolio?', 'Import this '+self.snapshot['environment'].upper()+' preview? This replaces your local positions and creates a backup.', parent=self):
            return
        backup = import_snapshot(self.snapshot)
        self.write(self.broker_output, 'Imported holdings. Backup: '+backup+'\n\nOpen Settings → Refresh portfolio to update all portfolio pages.')
        self.snapshot = None
