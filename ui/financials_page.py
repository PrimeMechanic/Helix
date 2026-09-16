import tkinter as tk

import customtkinter as ctk

from market.fundamentals import get_company_financials


class FinancialsPage(ctk.CTkFrame):
    """Searchable company financials with readable annual statement summaries."""

    def __init__(self, master):
        super().__init__(master)
        self.data = None
        self.chart = None
        self.build()

    def build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=34, pady=(30, 16))
        ctk.CTkLabel(header, text="Financials", font=("Arial", 30, "bold")).pack(side="left")
        self.search = ctk.CTkEntry(header, width=210, placeholder_text="Search ticker, e.g. MSFT")
        self.search.pack(side="right", padx=(10, 0))
        self.search.bind("<Return>", lambda event: self.load_company())
        ctk.CTkButton(header, text="Search", width=90, command=self.load_company).pack(side="right")
        self.status = ctk.CTkLabel(self, text="Search a company ticker to view annual financial statements from Yahoo Finance.", text_color="#a8b3c2", font=("Arial", 15))
        self.status.pack(anchor="w", padx=34, pady=(0, 16))
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=34, pady=(0, 28))

    def load_company(self):
        try:
            self.status.configure(text="Loading annual statements…", text_color="#a8b3c2")
            self.update_idletasks()
            self.data = get_company_financials(self.search.get())
            self.status.configure(text=f"{self.data['ticker']} · annual financial statements", text_color="#a8b3c2")
            self.render()
        except Exception as error:
            self.status.configure(text=str(error), text_color="#f87171")

    def render(self):
        for child in self.body.winfo_children():
            child.destroy()
        self.add_income()
        self.add_balance()
        self.add_cash_flow()

    def add_income(self):
        ctk.CTkLabel(self.body, text="Earnings vs. revenue", font=("Arial", 21, "bold")).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(self.body, text="Annual results. Revenue is blue; net income is green when positive and red when negative.", text_color="#9ba8b8", font=("Arial", 13)).pack(anchor="w", pady=(0, 10))
        chart_frame = ctk.CTkFrame(self.body)
        chart_frame.pack(fill="x", pady=(0, 16))
        self.chart = tk.Canvas(chart_frame, height=240, bg="#242424", highlightthickness=0)
        self.chart.pack(fill="x", padx=8, pady=8)
        self.chart.bind("<Configure>", lambda event: self.draw_chart())
        cards = ctk.CTkFrame(self.body, fg_color="transparent")
        cards.pack(fill="x", pady=(0, 25))
        latest = self.data["income"]
        self.metric(cards, "Revenue", latest["revenue"][0]["value"], latest["revenue"][0]["yoy"])
        self.metric(cards, "Net income", latest["net_income"][0]["value"], latest["net_income"][0]["yoy"])
        margin = latest["net_margin"]
        self.metric(cards, "Net margin", None if margin is None else f"{margin:.1f}%", text=True)
        self.statement_table(
            "Income statement", self.data["periods"],
            (("Revenue", latest["revenue"]), ("Operating income", latest["operating_income"]), ("Net income", latest["net_income"])),
        )

    def draw_chart(self):
        if not self.chart or not self.data:
            return
        canvas = self.chart
        canvas.delete("all")
        width, height = max(canvas.winfo_width(), 500), 224
        values = self.data["income"]
        revenue = [item["value"] or 0 for item in values["revenue"]]
        income = [item["value"] or 0 for item in values["net_income"]]
        peak = max(max(revenue, default=0), max(abs(value) for value in income) if income else 0, 1)
        baseline, chart_height = 175, 135
        count = len(revenue)
        group_width = (width - 64) / max(count, 1)
        canvas.create_text(16, 14, text="USD billions", anchor="w", fill="#9ba8b8", font=("Arial", 10))
        canvas.create_line(42, baseline, width - 16, baseline, fill="#586273")
        for index, (rev, net, period) in enumerate(zip(revenue, income, self.data["periods"])):
            center = 52 + group_width * index + group_width / 2
            revenue_height = chart_height * rev / peak
            net_height = chart_height * abs(net) / peak
            canvas.create_rectangle(center - 24, baseline - revenue_height, center - 4, baseline, fill="#2d89d0", outline="")
            if net >= 0:
                canvas.create_rectangle(center + 4, baseline - net_height, center + 24, baseline, fill="#4ade80", outline="")
            else:
                canvas.create_rectangle(center + 4, baseline, center + 24, baseline + net_height, fill="#f87171", outline="")
            canvas.create_text(center, baseline + 20, text=period, fill="#dbe4ef", font=("Arial", 10))
        canvas.create_text(width - 16, 14, text="■ Revenue   ■ Net income", anchor="e", fill="#dbe4ef", font=("Arial", 10))

    def add_balance(self):
        ctk.CTkLabel(self.body, text="Balance sheet", font=("Arial", 21, "bold")).pack(anchor="w", pady=(0, 10))
        balance = self.data["balance"]
        self.statement_table(
            "", balance["periods"],
            (("Cash", balance["cash"]), ("Total assets", balance["total_assets"]), ("Total debt", balance["total_debt"]), ("Liabilities", balance["total_liabilities"]), ("Equity", balance["equity"])),
        )

    def add_cash_flow(self):
        ctk.CTkLabel(self.body, text="Cash flow", font=("Arial", 21, "bold")).pack(anchor="w", pady=(0, 10))
        cash_flow = self.data["cash_flow"]
        self.statement_table(
            "", cash_flow["periods"],
            (("Operating cash flow", cash_flow["operating"]), ("Capital spending", cash_flow["capital_expenditure"]), ("Free cash flow", cash_flow["free_cash_flow"]), ("Investing cash flow", cash_flow["investing"]), ("Financing cash flow", cash_flow["financing"])),
        )

    @staticmethod
    def money(value):
        if value is None:
            return "Unavailable"
        prefix = "-" if value < 0 else ""
        return f"{prefix}${abs(value) / 1_000_000_000:,.2f}B"

    def statement_table(self, title, periods, rows):
        if title:
            ctk.CTkLabel(self.body, text=title, font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 8))
        table = ctk.CTkFrame(self.body)
        table.pack(fill="x", pady=(0, 25))
        header = ctk.CTkFrame(table, fg_color="#293c56")
        header.pack(fill="x", padx=2, pady=(2, 1))
        ctk.CTkLabel(header, text="Metric", width=190, anchor="w", font=("Arial", 13, "bold")).pack(side="left", padx=12, pady=9)
        for period in periods:
            ctk.CTkLabel(header, text=period, width=120, anchor="e", font=("Arial", 13, "bold")).pack(side="left", padx=3)
        ctk.CTkLabel(header, text="YoY", width=100, anchor="e", font=("Arial", 13, "bold")).pack(side="left", padx=3)
        for label, values in rows:
            row = ctk.CTkFrame(table, fg_color="#242424")
            row.pack(fill="x", padx=2, pady=1)
            ctk.CTkLabel(row, text=label, width=190, anchor="w", font=("Arial", 13)).pack(side="left", padx=12, pady=9)
            for item in values:
                ctk.CTkLabel(row, text=self.money(item["value"]), width=120, anchor="e", font=("Arial", 13)).pack(side="left", padx=3)
            current_yoy = values[0]["yoy"] if values else None
            color = "#4ade80" if current_yoy is not None and current_yoy >= 0 else "#f87171" if current_yoy is not None else "#9ba8b8"
            yoy_text = "Unavailable" if current_yoy is None else f"{current_yoy:+.1f}%"
            ctk.CTkLabel(row, text=yoy_text, width=100, anchor="e", text_color=color, font=("Arial", 13, "bold")).pack(side="left", padx=3)

    def metric(self, parent, label, value, yoy=None, text=False):
        card = ctk.CTkFrame(parent, height=104)
        card.pack(side="left", fill="x", expand=True, padx=5)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=label, text_color="#9ba8b8", font=("Arial", 12)).pack(anchor="w", padx=14, pady=(18, 5))
        output = value if text else self.money(value)
        color = "#f87171" if isinstance(value, (int, float)) and value < 0 else "#edf2f7"
        ctk.CTkLabel(card, text=output, text_color=color, font=("Arial", 17, "bold")).pack(anchor="w", padx=14)
        if yoy is not None:
            yoy_color = "#4ade80" if yoy >= 0 else "#f87171"
            ctk.CTkLabel(card, text=f"{yoy:+.1f}% YoY", text_color=yoy_color, font=("Arial", 11)).pack(anchor="w", padx=14, pady=(2, 0))
