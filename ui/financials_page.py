import tkinter as tk

import customtkinter as ctk

from market.fundamentals import get_company_financials
from ui.theme import ACCENT, BACKGROUND, MUTED, NEGATIVE, POSITIVE, SURFACE, SURFACE_ALT, TABLE_HEADER, TEXT


class FinancialsPage(ctk.CTkFrame):
    """Searchable company financials with readable annual statement summaries."""

    def __init__(self, master, ticker=None):
        super().__init__(master, fg_color=BACKGROUND)
        self.data = None
        self.chart = None
        self.expense_chart = None
        self.build()
        if ticker:
            self.search.insert(0, ticker)
            self.after(25, self.load_company)

    def build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=42, pady=(34, 8))
        title = ctk.CTkFrame(header, fg_color="transparent")
        title.pack(side="left")
        ctk.CTkLabel(title, text="Financials", font=("Arial", 30, "bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(title, text="Company fundamentals, without the spreadsheet clutter.", font=("Arial", 14), text_color=MUTED).pack(anchor="w", pady=(2, 0))
        self.search = ctk.CTkEntry(header, width=210, height=36, corner_radius=8, placeholder_text="Search ticker, e.g. MSFT", fg_color=SURFACE, border_color="#30323A")
        self.search.pack(side="right", padx=(10, 0))
        self.search.bind("<Return>", lambda event: self.load_company())
        ctk.CTkButton(header, text="Search", width=90, height=36, corner_radius=8, fg_color="#F1F3F5", text_color="#111214", hover_color="#D8DBE0", command=self.load_company).pack(side="right")
        self.status = ctk.CTkLabel(self, text="Search a company ticker to view annual financial statements from Yahoo Finance.", text_color=MUTED, font=("Arial", 14))
        self.status.pack(anchor="w", padx=42, pady=(18, 12))
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=42, pady=(0, 34))

    def load_company(self):
        try:
            self.status.configure(text="Loading annual statements…", text_color=MUTED)
            self.update_idletasks()
            self.data = get_company_financials(self.search.get())
            self.status.configure(text=f"{self.data['ticker']} · annual financial statements", text_color=MUTED)
            self.render()
        except Exception as error:
            self.status.configure(text=str(error), text_color=NEGATIVE)

    def render(self):
        for child in self.body.winfo_children():
            child.destroy()
        self.add_company_health()
        self.add_income()
        self.add_expenses()
        self.add_balance()
        self.add_cash_flow()

    def add_company_health(self):
        """Show the score as research evidence, not an opaque recommendation."""
        health = self.data["health"]
        ctk.CTkLabel(self.body, text="Company health", font=("Arial", 21, "bold"), text_color=TEXT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            self.body,
            text=f"Sector-aware research snapshot · {health['sector']} · {health['industry']}",
            text_color=MUTED, font=("Arial", 13),
        ).pack(anchor="w", pady=(0, 10))

        panel = ctk.CTkFrame(self.body, fg_color=SURFACE, corner_radius=12)
        panel.pack(fill="x", pady=(0, 12))
        score_block = ctk.CTkFrame(panel, fg_color=TABLE_HEADER, width=190, corner_radius=10)
        score_block.pack(side="left", fill="y", padx=12, pady=12)
        score_block.pack_propagate(False)
        score = health["score"]
        score_text = "—" if score is None else str(score)
        score_color = POSITIVE if score is not None and score >= 65 else NEGATIVE if score is not None and score < 50 else TEXT
        ctk.CTkLabel(score_block, text="HELIX HEALTH", text_color=MUTED, font=("Arial", 10, "bold")).pack(pady=(20, 2))
        ctk.CTkLabel(score_block, text=score_text, text_color=score_color, font=("Arial", 42, "bold")).pack()
        ctk.CTkLabel(score_block, text=f"{health['band']} · {health['coverage']}", text_color=TEXT, font=("Arial", 11, "bold"), wraplength=165).pack(padx=8, pady=(0, 18))
        explanation = ctk.CTkFrame(panel, fg_color="transparent")
        explanation.pack(side="left", fill="both", expand=True, padx=(6, 18), pady=18)
        ctk.CTkLabel(explanation, text="Research summary", text_color=TEXT, font=("Arial", 15, "bold")).pack(anchor="w")
        ctk.CTkLabel(explanation, text=health["summary"], text_color=TEXT, justify="left", wraplength=760, font=("Arial", 14)).pack(anchor="w", pady=(6, 8))
        ctk.CTkLabel(explanation, text=health["disclaimer"], text_color=MUTED, justify="left", wraplength=760, font=("Arial", 11)).pack(anchor="w")

        ctk.CTkLabel(self.body, text="Score breakdown", font=("Arial", 18, "bold"), text_color=TEXT).pack(anchor="w", pady=(6, 8))
        grid = ctk.CTkFrame(self.body, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 12))
        for index, pillar in enumerate(health["pillars"]):
            card = ctk.CTkFrame(grid, fg_color=SURFACE_ALT, corner_radius=10)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=4, pady=4)
            grid.grid_columnconfigure(index % 2, weight=1)
            score_value = pillar["score"]
            color = POSITIVE if score_value is not None and score_value >= 65 else NEGATIVE if score_value is not None and score_value < 50 else TEXT
            heading = ctk.CTkFrame(card, fg_color="transparent")
            heading.pack(fill="x", padx=14, pady=(13, 4))
            ctk.CTkLabel(heading, text=pillar["name"], font=("Arial", 14, "bold"), text_color=TEXT).pack(side="left")
            ctk.CTkLabel(heading, text="Unavailable" if score_value is None else f"{score_value}/100", font=("Arial", 14, "bold"), text_color=color).pack(side="right")
            ctk.CTkLabel(card, text=f"{pillar['weight']}% of score · {self.pillar_label(score_value)}", text_color=MUTED, font=("Arial", 11)).pack(anchor="w", padx=14)
            for metric in pillar["metrics"][:3]:
                line = f"{metric['label']}: {metric['display']}"
                ctk.CTkLabel(card, text=line, text_color=TEXT, font=("Arial", 12)).pack(anchor="w", padx=14, pady=(5, 0))
            if pillar.get("note"):
                ctk.CTkLabel(card, text=pillar["note"], text_color=MUTED, wraplength=440, justify="left", font=("Arial", 10)).pack(anchor="w", padx=14, pady=(7, 13))
            else:
                ctk.CTkFrame(card, height=12, fg_color="transparent").pack()

        if health["flags"]:
            ctk.CTkLabel(self.body, text="What to investigate", font=("Arial", 18, "bold"), text_color=TEXT).pack(anchor="w", pady=(8, 8))
            flags = ctk.CTkFrame(self.body, fg_color=SURFACE, corner_radius=12)
            flags.pack(fill="x", pady=(0, 25))
            for flag in health["flags"]:
                ctk.CTkLabel(flags, text=f"•  {flag}", text_color="#FFD39A", justify="left", wraplength=980, font=("Arial", 13)).pack(anchor="w", padx=16, pady=6)

    @staticmethod
    def pillar_label(score):
        if score is None:
            return "data not available"
        if score >= 75:
            return "strong"
        if score >= 55:
            return "balanced"
        return "needs attention"

    def add_income(self):
        ctk.CTkLabel(self.body, text="Earnings vs. revenue", font=("Arial", 21, "bold"), text_color=TEXT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(self.body, text="Annual results. Revenue is blue; net income is green when positive and red when negative.", text_color=MUTED, font=("Arial", 13)).pack(anchor="w", pady=(0, 10))
        chart_frame = ctk.CTkFrame(self.body, fg_color=SURFACE, corner_radius=12)
        chart_frame.pack(fill="x", pady=(0, 16))
        self.chart = tk.Canvas(chart_frame, height=240, bg=SURFACE, highlightthickness=0)
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
        canvas.create_text(16, 14, text="USD billions", anchor="w", fill=MUTED, font=("Arial", 10))
        canvas.create_line(42, baseline, width - 16, baseline, fill="#3A3D45")
        for index, (rev, net, period) in enumerate(zip(revenue, income, self.data["periods"])):
            center = 52 + group_width * index + group_width / 2
            revenue_height = chart_height * rev / peak
            net_height = chart_height * abs(net) / peak
            canvas.create_rectangle(center - 24, baseline - revenue_height, center - 4, baseline, fill=ACCENT, outline="")
            if net >= 0:
                canvas.create_rectangle(center + 4, baseline - net_height, center + 24, baseline, fill=POSITIVE, outline="")
            else:
                canvas.create_rectangle(center + 4, baseline, center + 24, baseline + net_height, fill=NEGATIVE, outline="")
            canvas.create_text(center, baseline + 20, text=period, fill=TEXT, font=("Arial", 10))
        canvas.create_text(width - 16, 14, text="■ Revenue   ■ Net income", anchor="e", fill=TEXT, font=("Arial", 10))

    def add_expenses(self):
        income = self.data["income"]
        expenses = income["expenses"]
        ctk.CTkLabel(self.body, text="Where revenue goes", font=("Arial", 21, "bold"), text_color=TEXT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            self.body,
            text="Reported annual expense lines. Each bar is the latest expense as a share of the latest reported revenue.",
            text_color=MUTED, font=("Arial", 13),
        ).pack(anchor="w", pady=(0, 10))
        if not expenses:
            ctk.CTkLabel(self.body, text="Yahoo Finance did not provide expense categories for this company.", text_color=MUTED, font=("Arial", 13)).pack(anchor="w", pady=(0, 25))
            return

        chart_frame = ctk.CTkFrame(self.body, fg_color=SURFACE, corner_radius=12)
        chart_frame.pack(fill="x", pady=(0, 14))
        self.expense_chart = tk.Canvas(chart_frame, height=max(160, len(expenses) * 44 + 40), bg=SURFACE, highlightthickness=0)
        self.expense_chart.pack(fill="x", padx=8, pady=8)
        self.expense_chart.bind("<Configure>", lambda event: self.draw_expense_chart())

        latest_revenue = income["revenue"][0]["value"] if income["revenue"] else None
        snapshots = ctk.CTkFrame(self.body, fg_color="transparent")
        snapshots.pack(fill="x", pady=(0, 14))
        for index, expense in enumerate(expenses[:3]):
            value = expense["values"][0]["value"]
            share = value / latest_revenue * 100 if value is not None and latest_revenue else None
            self.metric(
                snapshots, expense["label"], value,
                None if share is None else share,
                change_label="of revenue",
            )
        self.expense_table("Expense categories", self.data["periods"], expenses, latest_revenue)
        ctk.CTkLabel(
            self.body,
            text="Categories are only shown when Yahoo Finance reports them. Companies group expenses differently, so the visible lines may not add up to total revenue or total operating expense.",
            text_color=MUTED, justify="left", wraplength=1020, font=("Arial", 11),
        ).pack(anchor="w", pady=(-13, 25))

    def draw_expense_chart(self):
        if not self.expense_chart or not self.data:
            return
        canvas = self.expense_chart
        canvas.delete("all")
        width = max(canvas.winfo_width(), 650)
        expenses = self.data["income"]["expenses"]
        revenue = self.data["income"]["revenue"][0]["value"]
        colors = ("#7FB6FF", "#B89BFF", "#FFB86A", "#F685A7", "#64D8C5", "#FFDD88")
        label_width, right_padding, top, row_height = 210, 74, 26, 42
        max_share = max((abs(item["values"][0]["value"] or 0) / revenue for item in expenses if revenue), default=1)
        max_share = max(max_share, .05)
        for index, expense in enumerate(expenses):
            value = expense["values"][0]["value"]
            if value is None or not revenue:
                continue
            share = abs(value) / revenue
            y = top + index * row_height
            end_x = width - right_padding
            bar_end = label_width + (end_x - label_width) * min(share / max_share, 1)
            canvas.create_text(12, y, text=expense["label"], anchor="w", fill=TEXT, font=("Arial", 11, "bold"))
            canvas.create_rectangle(label_width, y - 9, end_x, y + 9, fill=TABLE_HEADER, outline="")
            canvas.create_rectangle(label_width, y - 9, bar_end, y + 9, fill=colors[index % len(colors)], outline="")
            canvas.create_text(width - 12, y, text=f"{share * 100:.1f}%", anchor="e", fill=TEXT, font=("Arial", 11, "bold"))

    def expense_table(self, title, periods, expenses, latest_revenue):
        ctk.CTkLabel(self.body, text=title, font=("Arial", 18, "bold"), text_color=TEXT).pack(anchor="w", pady=(0, 8))
        table = ctk.CTkFrame(self.body, fg_color=SURFACE, corner_radius=12)
        table.pack(fill="x", pady=(0, 25))
        header = ctk.CTkFrame(table, fg_color=TABLE_HEADER, corner_radius=8)
        header.pack(fill="x", padx=2, pady=(2, 1))
        ctk.CTkLabel(header, text="Category", width=190, anchor="w", font=("Arial", 13, "bold")).pack(side="left", padx=12, pady=9)
        for period in periods:
            ctk.CTkLabel(header, text=period, width=110, anchor="e", font=("Arial", 13, "bold")).pack(side="left", padx=3)
        ctk.CTkLabel(header, text="% revenue", width=96, anchor="e", font=("Arial", 13, "bold")).pack(side="left", padx=3)
        ctk.CTkLabel(header, text="YoY", width=88, anchor="e", font=("Arial", 13, "bold")).pack(side="left", padx=3)
        for expense in expenses:
            values = expense["values"]
            row = ctk.CTkFrame(table, fg_color=SURFACE_ALT, corner_radius=8)
            row.pack(fill="x", padx=2, pady=1)
            ctk.CTkLabel(row, text=expense["label"], width=190, anchor="w", font=("Arial", 13)).pack(side="left", padx=12, pady=9)
            for item in values:
                ctk.CTkLabel(row, text=self.money(item["value"]), width=110, anchor="e", font=("Arial", 13)).pack(side="left", padx=3)
            value = values[0]["value"] if values else None
            share = value / latest_revenue if value is not None and latest_revenue else None
            ctk.CTkLabel(row, text="Unavailable" if share is None else f"{share * 100:.1f}%", width=96, anchor="e", text_color=TEXT, font=("Arial", 13, "bold")).pack(side="left", padx=3)
            yoy = values[0]["yoy"] if values else None
            yoy_color = POSITIVE if yoy is not None and yoy <= 0 else NEGATIVE if yoy is not None else MUTED
            ctk.CTkLabel(row, text="Unavailable" if yoy is None else f"{yoy:+.1f}%", width=88, anchor="e", text_color=yoy_color, font=("Arial", 13, "bold")).pack(side="left", padx=3)

    def add_balance(self):
        ctk.CTkLabel(self.body, text="Balance sheet", font=("Arial", 21, "bold"), text_color=TEXT).pack(anchor="w", pady=(0, 10))
        balance = self.data["balance"]
        self.statement_table(
            "", balance["periods"],
            (("Cash", balance["cash"]), ("Total assets", balance["total_assets"]), ("Total debt", balance["total_debt"]), ("Liabilities", balance["total_liabilities"]), ("Equity", balance["equity"])),
        )

    def add_cash_flow(self):
        ctk.CTkLabel(self.body, text="Cash flow", font=("Arial", 21, "bold"), text_color=TEXT).pack(anchor="w", pady=(0, 10))
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
        table = ctk.CTkFrame(self.body, fg_color=SURFACE, corner_radius=12)
        table.pack(fill="x", pady=(0, 25))
        header = ctk.CTkFrame(table, fg_color=TABLE_HEADER, corner_radius=8)
        header.pack(fill="x", padx=2, pady=(2, 1))
        ctk.CTkLabel(header, text="Metric", width=190, anchor="w", font=("Arial", 13, "bold")).pack(side="left", padx=12, pady=9)
        for period in periods:
            ctk.CTkLabel(header, text=period, width=120, anchor="e", font=("Arial", 13, "bold")).pack(side="left", padx=3)
        ctk.CTkLabel(header, text="YoY", width=100, anchor="e", font=("Arial", 13, "bold")).pack(side="left", padx=3)
        for label, values in rows:
            row = ctk.CTkFrame(table, fg_color=SURFACE_ALT, corner_radius=8)
            row.pack(fill="x", padx=2, pady=1)
            ctk.CTkLabel(row, text=label, width=190, anchor="w", font=("Arial", 13)).pack(side="left", padx=12, pady=9)
            for item in values:
                ctk.CTkLabel(row, text=self.money(item["value"]), width=120, anchor="e", font=("Arial", 13)).pack(side="left", padx=3)
            current_yoy = values[0]["yoy"] if values else None
            color = POSITIVE if current_yoy is not None and current_yoy >= 0 else NEGATIVE if current_yoy is not None else MUTED
            yoy_text = "Unavailable" if current_yoy is None else f"{current_yoy:+.1f}%"
            ctk.CTkLabel(row, text=yoy_text, width=100, anchor="e", text_color=color, font=("Arial", 13, "bold")).pack(side="left", padx=3)

    def metric(self, parent, label, value, yoy=None, text=False, change_label="YoY"):
        card = ctk.CTkFrame(parent, height=104, fg_color=SURFACE, corner_radius=12)
        card.pack(side="left", fill="x", expand=True, padx=5)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=label.upper(), text_color=MUTED, font=("Arial", 11, "bold")).pack(anchor="w", padx=14, pady=(18, 5))
        output = value if text else self.money(value)
        color = NEGATIVE if isinstance(value, (int, float)) and value < 0 else TEXT
        ctk.CTkLabel(card, text=output, text_color=color, font=("Arial", 17, "bold")).pack(anchor="w", padx=14)
        if yoy is not None:
            yoy_color = POSITIVE if yoy >= 0 else NEGATIVE
            ctk.CTkLabel(card, text=f"{yoy:+.1f}% {change_label}", text_color=yoy_color, font=("Arial", 11)).pack(anchor="w", padx=14, pady=(2, 0))
