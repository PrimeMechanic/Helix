import customtkinter as ctk

from market.market_data import get_quote
from ui.theme import BACKGROUND, MUTED, NEGATIVE, POSITIVE, SURFACE, SURFACE_ALT, TABLE_HEADER, TEXT
from watchlist_manager import add_to_watchlist, load_watchlist, remove_from_watchlist


class WatchlistPage(ctk.CTkFrame):
    """Saved symbols with their current quote and a path into company research."""

    def __init__(self, master, on_research):
        super().__init__(master, fg_color=BACKGROUND)
        self.on_research = on_research
        self.build()
        self.render()

    def build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=42, pady=(34, 8))
        title = ctk.CTkFrame(header, fg_color="transparent")
        title.pack(side="left")
        ctk.CTkLabel(title, text="Watchlist", text_color=TEXT, font=("Arial", 30, "bold")).pack(anchor="w")
        ctk.CTkLabel(title, text="Keep an eye on the companies and assets you care about.", text_color=MUTED, font=("Arial", 14)).pack(anchor="w", pady=(2, 0))
        self.symbol_input = ctk.CTkEntry(header, width=170, height=36, corner_radius=8, placeholder_text="Add ticker", fg_color=SURFACE, border_color="#30323A")
        self.symbol_input.pack(side="right", padx=(10, 0))
        self.symbol_input.bind("<Return>", lambda event: self.add_symbol())
        ctk.CTkButton(header, text="Add", width=72, height=36, corner_radius=8, fg_color="#F1F3F5", text_color="#111214", hover_color="#D8DBE0", command=self.add_symbol).pack(side="right")
        self.status = ctk.CTkLabel(self, text="Add a ticker to begin tracking it.", text_color=MUTED, font=("Arial", 14))
        self.status.pack(anchor="w", padx=42, pady=(18, 12))
        self.table = ctk.CTkScrollableFrame(self, fg_color=SURFACE, corner_radius=12)
        self.table.pack(fill="both", expand=True, padx=42, pady=(0, 34))

    def add_symbol(self):
        try:
            add_to_watchlist(self.symbol_input.get())
            self.symbol_input.delete(0, "end")
            self.status.configure(text="Watchlist updated.", text_color=MUTED)
            self.render()
        except ValueError as error:
            self.status.configure(text=str(error), text_color=NEGATIVE)

    def remove_symbol(self, ticker):
        remove_from_watchlist(ticker)
        self.status.configure(text=f"Removed {ticker} from your watchlist.", text_color=MUTED)
        self.render()

    def render(self):
        for child in self.table.winfo_children():
            child.destroy()
        symbols = load_watchlist()
        if not symbols:
            ctk.CTkLabel(self.table, text="Your watchlist is empty. Add a ticker above to get started.", text_color=MUTED, font=("Arial", 15)).pack(anchor="w", padx=20, pady=22)
            return
        header = ctk.CTkFrame(self.table, fg_color=TABLE_HEADER, corner_radius=8)
        header.pack(fill="x", padx=4, pady=(4, 5))
        for label, width in (("TICKER", 160), ("LAST PRICE", 170), ("TODAY", 140), ("", 250)):
            ctk.CTkLabel(header, text=label, width=width, anchor="w", text_color=MUTED, font=("Arial", 11, "bold")).pack(side="left", padx=8, pady=11)
        for ticker in symbols:
            quote = get_quote(ticker)
            row = ctk.CTkFrame(self.table, fg_color=SURFACE_ALT, corner_radius=8)
            row.pack(fill="x", padx=4, pady=2)
            ctk.CTkLabel(row, text=ticker, width=160, anchor="w", text_color=TEXT, font=("Arial", 14, "bold")).pack(side="left", padx=8, pady=12)
            price = "Unavailable" if not quote else f"${quote['price']:,.2f}"
            ctk.CTkLabel(row, text=price, width=170, anchor="w", text_color=TEXT, font=("Arial", 13)).pack(side="left", padx=8)
            movement = "Unavailable" if not quote else f"{quote['percent']:+.2f}%"
            movement_color = MUTED if not quote else POSITIVE if quote["percent"] >= 0 else NEGATIVE
            ctk.CTkLabel(row, text=movement, width=140, anchor="w", text_color=movement_color, font=("Arial", 13, "bold")).pack(side="left", padx=8)
            ctk.CTkButton(row, text="Research", width=82, height=30, corner_radius=8, fg_color="#30323A", hover_color="#3A3D45", command=lambda symbol=ticker: self.on_research(symbol)).pack(side="right", padx=(6, 12), pady=8)
            ctk.CTkButton(row, text="Remove", width=78, height=30, corner_radius=8, fg_color="transparent", text_color=MUTED, hover_color="#30323A", command=lambda symbol=ticker: self.remove_symbol(symbol)).pack(side="right", padx=3, pady=8)
