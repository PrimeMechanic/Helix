import customtkinter as ctk

from ui.theme import BACKGROUND, MUTED, NEGATIVE, POSITIVE, SURFACE, TABLE_HEADER, TEXT


class PortfolioPage(ctk.CTkFrame):

    def __init__(self, master, data=None):
        super().__init__(master, fg_color=BACKGROUND)

        ctk.CTkLabel(
            self,
            text="Portfolio",
            font=("Arial", 30, "bold"), text_color=TEXT
        ).pack(anchor="nw", padx=42, pady=(34, 3))
        ctk.CTkLabel(self, text="A live view of your positions and performance.", text_color=MUTED, font=("Arial", 14)).pack(anchor="nw", padx=42, pady=(0, 22))
        if not data:
            ctk.CTkLabel(self, text="No current portfolio data available.", text_color=MUTED).pack(anchor="nw", padx=42)
            return
        table = ctk.CTkScrollableFrame(self, fg_color=SURFACE, corner_radius=12)
        table.pack(fill="both", expand=True, padx=42, pady=(0, 34))
        headers = ("Ticker", "Shares", "Market Value", "Gain / Loss", "Return")
        header = ctk.CTkFrame(table, fg_color=TABLE_HEADER, corner_radius=8)
        header.pack(fill="x", padx=4, pady=(4, 5))
        for label in headers:
            ctk.CTkLabel(header, text=label.upper(), width=145, anchor="w", text_color=MUTED, font=("Arial", 11, "bold")).pack(side="left", padx=8, pady=11)
        for position in sorted(data["positions"], key=lambda item: item["value"], reverse=True):
            row = ctk.CTkFrame(table, fg_color=SURFACE_ALT, corner_radius=8)
            row.pack(fill="x", padx=4, pady=2)
            gain_color = POSITIVE if position["gain"] >= 0 else NEGATIVE
            cells = (position["ticker"], f"{position['shares']:,.3f}", f"${position['value']:,.2f}", f"{position['gain']:+,.2f}", f"{position['percent']:+.2f}%")
            for index, value in enumerate(cells):
                ctk.CTkLabel(row, text=value, width=145, anchor="w", text_color=gain_color if index in (3, 4) else TEXT, font=("Arial", 13, "bold") if index == 0 else ("Arial", 13)).pack(side="left", padx=8, pady=13)
