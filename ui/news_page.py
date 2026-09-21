import webbrowser

import customtkinter as ctk

from market.market_data import get_company_news
from ui.theme import BACKGROUND, MUTED, NEGATIVE, SURFACE, SURFACE_ALT, TEXT


class NewsPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master, fg_color=BACKGROUND)
        self.build()
        self.load_news()

    def build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=42, pady=(34, 8))
        title = ctk.CTkFrame(header, fg_color="transparent")
        title.pack(side="left")
        ctk.CTkLabel(title, text="Market news", font=("Arial", 30, "bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(title, text="A blended view of the stories moving markets.", font=("Arial", 14), text_color=MUTED).pack(anchor="w", pady=(2, 0))
        self.search = ctk.CTkEntry(header, width=200, height=36, corner_radius=8, placeholder_text="Ticker, e.g. NVDA", fg_color=SURFACE, border_color="#30323A")
        self.search.insert(0, "MARKET")
        self.search.pack(side="right", padx=(10, 0))
        self.search.bind("<Return>", lambda event: self.load_news())
        ctk.CTkButton(header, text="Search", width=88, height=36, corner_radius=8, fg_color="#F1F3F5", text_color="#111214", hover_color="#D8DBE0", command=self.load_news).pack(side="right")
        self.status = ctk.CTkLabel(self, text="A blended feed from Yahoo Finance and Google News", text_color=MUTED, font=("Arial", 14))
        self.status.pack(anchor="w", padx=42, pady=(18, 12))
        self.feed = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.feed.pack(fill="both", expand=True, padx=42, pady=(0, 34))

    def load_news(self):
        ticker = self.search.get().strip().upper() or "MARKET"
        self.status.configure(text=f"Loading latest news for {ticker}…", text_color=MUTED)
        self.update_idletasks()
        self.render(get_company_news(ticker), ticker)

    def render(self, stories, ticker):
        for child in self.feed.winfo_children():
            child.destroy()
        if not stories:
            self.status.configure(text=f"No recent stories found for {ticker}.", text_color=NEGATIVE)
            return
        topic = "the market" if ticker == "MARKET" else ticker
        self.status.configure(text=f"Blended market coverage for {topic} · Yahoo Finance + Google News", text_color=MUTED)
        for story in stories:
            card = ctk.CTkFrame(self.feed, fg_color=SURFACE, corner_radius=12)
            card.pack(fill="x", pady=5)
            ctk.CTkLabel(card, text=story["title"], text_color=TEXT, font=("Arial", 17, "bold"), justify="left", anchor="w", wraplength=800).pack(anchor="w", padx=18, pady=(16, 4))
            ctk.CTkLabel(card, text=f"{story['publisher']}  ·  {story['published']}", text_color=MUTED, font=("Arial", 12)).pack(anchor="w", padx=18)
            if story["summary"]:
                ctk.CTkLabel(card, text=story["summary"], text_color="#D6D8DE", font=("Arial", 13), justify="left", anchor="w", wraplength=820).pack(anchor="w", padx=18, pady=(8, 4))
            if story["url"]:
                ctk.CTkButton(card, text="Read article", width=105, height=30, corner_radius=8, fg_color=SURFACE_ALT, hover_color="#30323A", command=lambda url=story["url"]: webbrowser.open(url)).pack(anchor="w", padx=18, pady=(6, 16))
