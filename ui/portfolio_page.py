import customtkinter as ctk


class PortfolioPage(ctk.CTkFrame):

    def __init__(self, master, data=None):
        super().__init__(master)

        ctk.CTkLabel(
            self,
            text="Portfolio",
            font=("Arial", 30, "bold")
        ).pack(anchor="nw", padx=30, pady=30)
        if not data:
            ctk.CTkLabel(self, text="No current portfolio data available.").pack(anchor="nw", padx=30)
            return
        table = ctk.CTkScrollableFrame(self)
        table.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        headers = ("Ticker", "Shares", "Market Value", "Gain / Loss", "Return")
        header = ctk.CTkFrame(table, fg_color="#263447")
        header.pack(fill="x", pady=(0, 5))
        for label in headers:
            ctk.CTkLabel(header, text=label, width=135, anchor="w", font=("Arial", 13, "bold")).pack(side="left", padx=8, pady=10)
        for position in sorted(data["positions"], key=lambda item: item["value"], reverse=True):
            row = ctk.CTkFrame(table)
            row.pack(fill="x", pady=3)
            gain_color = "#4ade80" if position["gain"] >= 0 else "#f87171"
            cells = (position["ticker"], f"{position['shares']:,.3f}", f"${position['value']:,.2f}", f"{position['gain']:+,.2f}", f"{position['percent']:+.2f}%")
            for index, value in enumerate(cells):
                ctk.CTkLabel(row, text=value, width=135, anchor="w", text_color=gain_color if index in (3, 4) else "#edf2f7").pack(side="left", padx=8, pady=12)
