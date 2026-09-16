import customtkinter as ctk

from market.market_data import get_market_summary


class MarketsPage(ctk.CTkFrame):
    """Market benchmarks and sector ETFs, with their latest daily movement."""

    def __init__(self, master):
        super().__init__(master)
        self.summary = None
        self.build()
        self.refresh()

    def build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=34, pady=(30, 16))
        ctk.CTkLabel(header, text="Markets", font=("Arial", 30, "bold")).pack(side="left")
        ctk.CTkButton(header, text="Refresh", width=100, command=self.refresh).pack(side="right")
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=34, pady=(0, 28))

    def refresh(self):
        self.summary = get_market_summary()
        for child in self.body.winfo_children():
            child.destroy()
        self.add_benchmarks()
        self.add_sectors()

    def add_benchmarks(self):
        ctk.CTkLabel(self.body, text="Market summary", font=("Arial", 20, "bold")).pack(anchor="w", pady=(0, 10))
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 24))
        for quote in self.summary["benchmarks"]:
            card = ctk.CTkFrame(row, height=128)
            card.pack(side="left", fill="x", expand=True, padx=6)
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=f"{quote['name']}  ·  {quote['ticker']}", text_color="#a8b3c2", font=("Arial", 13)).pack(anchor="w", padx=16, pady=(19, 5))
            price = "Unavailable" if quote["price"] is None else f"${quote['price']:,.2f}"
            ctk.CTkLabel(card, text=price, font=("Arial", 21, "bold")).pack(anchor="w", padx=16)
            self.movement_label(card, quote, padx=16, pady=(5, 0))

    def add_sectors(self):
        ctk.CTkLabel(self.body, text="Sector performance", font=("Arial", 20, "bold")).pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(self.body, text="Sector ETFs are used as the live performance indicator.", text_color="#9ba8b8", font=("Arial", 13)).pack(anchor="w", pady=(0, 10))
        table = ctk.CTkFrame(self.body)
        table.pack(fill="x")
        for quote in self.summary["sectors"]:
            row = ctk.CTkFrame(table, fg_color="#242424")
            row.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(row, text=quote["name"], width=230, anchor="w", font=("Arial", 14)).pack(side="left", padx=16, pady=11)
            ctk.CTkLabel(row, text=quote["ticker"], width=70, anchor="w", text_color="#a8b3c2").pack(side="left")
            ctk.CTkLabel(row, text="●", text_color=self.movement_color(quote), font=("Arial", 18)).pack(side="right", padx=(8, 16))
            self.movement_label(row, quote, side="right", padx=6, pady=0)

    @staticmethod
    def movement_color(quote):
        if quote["percent"] is None:
            return "#9ba8b8"
        return "#4ade80" if quote["percent"] >= 0 else "#f87171"

    def movement_label(self, parent, quote, **pack_options):
        if quote["percent"] is None:
            text = "Unavailable"
        else:
            text = f"{quote['percent']:+.2f}%"
        ctk.CTkLabel(parent, text=text, text_color=self.movement_color(quote), font=("Arial", 15, "bold")).pack(**pack_options)
