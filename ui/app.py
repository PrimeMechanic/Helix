import os
import sys

import customtkinter as ctk

# Support both `python ui/app.py` and `python -m ui.app`.
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.ai_page import AIPage
from ui.dashboard import DashboardPage
from ui.data import load_dashboard_data
from ui.financials_page import FinancialsPage
from ui.markets_page import MarketsPage
from ui.news_page import NewsPage
from ui.portfolio_page import PortfolioPage
from ui.settings_page import SettingsPage


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class HelixApp(ctk.CTk):
    """Desktop shell for HELIX's existing portfolio analysis."""

    def __init__(self):
        super().__init__()
        self.title("HELIX — Investing Intelligence")
        self.geometry("1280x780")
        self.minsize(1050, 650)
        self.analysis = None
        self.page_name = "Dashboard"

        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="#17202e")
        self.content.pack(side="right", fill="both", expand=True)
        self.current_page = None

        ctk.CTkLabel(self.sidebar, text="HELIX", font=("Arial", 27, "bold"), text_color="#73b7ff").pack(anchor="w", padx=26, pady=(34, 4))
        ctk.CTkLabel(self.sidebar, text="INVESTING INTELLIGENCE", font=("Arial", 10), text_color="#8594a8").pack(anchor="w", padx=27, pady=(0, 28))
        self.buttons = {}
        for name in ("Dashboard", "Portfolio", "AI Analysis", "Markets", "Financials", "News", "Settings"):
            button = ctk.CTkButton(
                self.sidebar, text=name, anchor="w", height=40,
                fg_color="transparent", hover_color="#2a3c53",
                command=lambda page=name: self.show_page(page),
            )
            button.pack(fill="x", padx=15, pady=3)
            self.buttons[name] = button
        ctk.CTkLabel(self.sidebar, text="Market data supplied by Yahoo Finance", font=("Arial", 10), text_color="#708096", wraplength=165, justify="left").pack(side="bottom", anchor="w", padx=22, pady=24)
        self.refresh_data()

    def refresh_data(self):
        self.analysis = load_dashboard_data()
        self.show_page(self.page_name)

    def show_page(self, page_name):
        self.page_name = page_name
        if self.current_page:
            self.current_page.destroy()
        for name, button in self.buttons.items():
            button.configure(fg_color="#2879ba" if name == page_name else "transparent")
        pages = {
            "Dashboard": lambda: DashboardPage(self.content, self.analysis, self.refresh_data),
            "Portfolio": lambda: PortfolioPage(self.content, self.analysis),
            "AI Analysis": lambda: AIPage(self.content, self.analysis),
            "Markets": lambda: MarketsPage(self.content),
            "Financials": lambda: FinancialsPage(self.content),
            "News": lambda: NewsPage(self.content),
            "Settings": lambda: SettingsPage(self.content, self.refresh_data),
        }
        self.current_page = pages[page_name]()
        self.current_page.pack(fill="both", expand=True)


if __name__ == "__main__":
    HelixApp().mainloop()
