import customtkinter as ctk


class DashboardPage(ctk.CTkFrame):

    def __init__(self, master, data=None, on_refresh=None):
        super().__init__(master)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=34, pady=(30, 16))
        ctk.CTkLabel(header, text="Dashboard", font=("Arial", 30, "bold")).pack(side="left")
        ctk.CTkButton(header, text="Refresh", width=100, command=on_refresh).pack(side="right")
        if not data:
            ctk.CTkLabel(self, text="Portfolio data is unavailable. Refresh to try again.", font=("Arial", 16), text_color="#a8b3c2").pack(anchor="nw", padx=34, pady=20)
            return
        daily = data["today_change"]
        daily_text = "Unavailable" if daily is None else f"{'+' if daily >= 0 else '-'}${abs(daily):,.2f}"
        cards = (("Portfolio Value", f"${data['portfolio_value']:,.2f}"), ("Today's Change", daily_text), ("Health Score", f"{data['health']} / 100"), ("Risk Level", data["risk"]))
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=24)
        for label, value in cards:
            card = ctk.CTkFrame(row, height=118)
            card.pack(side="left", fill="x", expand=True, padx=8)
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=label, text_color="#9ba8b8", font=("Arial", 13)).pack(anchor="w", padx=18, pady=(22, 5))
            color = "#4ade80" if label == "Today's Change" and daily is not None and daily >= 0 else "#f87171" if label == "Today's Change" and daily is not None else "#f4f7fb"
            ctk.CTkLabel(card, text=value, text_color=color, font=("Arial", 23, "bold")).pack(anchor="w", padx=18)
        detail = ctk.CTkFrame(self)
        detail.pack(fill="both", expand=True, padx=34, pady=28)
        ctk.CTkLabel(detail, text="Portfolio snapshot", font=("Arial", 20, "bold")).pack(anchor="w", padx=22, pady=(20, 10))
        ctk.CTkLabel(detail, text=(f"Total return: {data['portfolio_return']:+.2f}%\nLargest holding: {data['largest']['ticker']}  •  ${data['largest']['value']:,.2f}\nBest performer: {data['best']['ticker']}  •  {data['best']['percent']:+.2f}%"), justify="left", font=("Arial", 16), text_color="#d3dbe7").pack(anchor="w", padx=22, pady=8)
