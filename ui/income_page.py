import customtkinter as ctk

from analytics.income_and_earnings import get_income_and_earnings
from ui.theme import BACKGROUND, MUTED, SURFACE, SURFACE_ALT, TABLE_HEADER, TEXT


class IncomePage(ctk.CTkFrame):
    """Dividend-income estimates and earnings dates for portfolio holdings."""

    def __init__(self, master):
        super().__init__(master, fg_color=BACKGROUND)
        self.data = None
        self.build()
        self.refresh()

    def build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=42, pady=(34, 8))
        title = ctk.CTkFrame(header, fg_color="transparent")
        title.pack(side="left")
        ctk.CTkLabel(title, text="Income & earnings", text_color=TEXT, font=("Arial", 30, "bold")).pack(anchor="w")
        ctk.CTkLabel(title, text="Dividend income estimates and the next reported earnings dates.", text_color=MUTED, font=("Arial", 14)).pack(anchor="w", pady=(2, 0))
        ctk.CTkButton(header, text="Refresh", width=96, height=36, corner_radius=8, fg_color="#F1F3F5", text_color="#111214", hover_color="#D8DBE0", command=self.refresh).pack(side="right")
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=42, pady=(24, 34))

    def refresh(self):
        self.data = get_income_and_earnings()
        for child in self.body.winfo_children():
            child.destroy()
        self.render()

    def render(self):
        income = ctk.CTkFrame(self.body, fg_color=SURFACE, corner_radius=12)
        income.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(income, text="ESTIMATED ANNUAL DIVIDEND INCOME", text_color=MUTED, font=("Arial", 11, "bold")).pack(anchor="w", padx=22, pady=(18, 5))
        ctk.CTkLabel(income, text=f"${self.data['annual_income']:,.2f}", text_color=TEXT, font=("Arial", 30, "bold")).pack(anchor="w", padx=22)
        ctk.CTkLabel(income, text="Based on dividends paid over the last 12 months. Past dividends are not guaranteed.", text_color=MUTED, font=("Arial", 13)).pack(anchor="w", padx=22, pady=(4, 18))
        ctk.CTkLabel(self.body, text="Holdings calendar", text_color=TEXT, font=("Arial", 20, "bold")).pack(anchor="w", pady=(0, 10))
        table = ctk.CTkFrame(self.body, fg_color=SURFACE, corner_radius=12)
        table.pack(fill="x")
        header = ctk.CTkFrame(table, fg_color=TABLE_HEADER, corner_radius=8)
        header.pack(fill="x", padx=4, pady=(4, 5))
        columns = (("TICKER", 130), ("ANNUAL DIVIDEND / SHARE", 220), ("EST. ANNUAL INCOME", 190), ("NEXT EARNINGS", 190), ("EPS ESTIMATE", 150))
        for label, width in columns:
            ctk.CTkLabel(header, text=label, width=width, anchor="w", text_color=MUTED, font=("Arial", 11, "bold")).pack(side="left", padx=8, pady=11)
        for holding in self.data["holdings"]:
            row = ctk.CTkFrame(table, fg_color=SURFACE_ALT, corner_radius=8)
            row.pack(fill="x", padx=4, pady=2)
            dividend = "Unavailable" if holding["annual_dividend"] is None else f"${holding['annual_dividend']:,.2f}"
            income_value = "Unavailable" if holding["estimated_income"] is None else f"${holding['estimated_income']:,.2f}"
            eps = "Unavailable" if holding["earnings_estimate"] is None else f"${holding['earnings_estimate']:,.2f}"
            values = ((holding["ticker"], 130), (dividend, 220), (income_value, 190), (holding["earnings_date"], 190), (eps, 150))
            for index, (value, width) in enumerate(values):
                ctk.CTkLabel(row, text=value, width=width, anchor="w", text_color=TEXT, font=("Arial", 13, "bold") if index == 0 else ("Arial", 13)).pack(side="left", padx=8, pady=12)
