import os
import sys
import queue
import threading

import customtkinter as ctk

# Support both `python ui/app.py` and `python -m ui.app`.
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.ai_page import AIPage
from ui.dashboard import DashboardPage
from ui.data import load_dashboard_data
from ui.financials_page import FinancialsPage
from ui.income_page import IncomePage
from ui.markets_page import MarketsPage
from ui.news_page import NewsPage
from ui.portfolio_page import PortfolioPage
from ui.performance_page import PerformancePage
from ui.settings_page import SettingsPage
from ui.watchlist_page import WatchlistPage


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

APP_BACKGROUND = "#121316"
SIDEBAR_BACKGROUND = "#0B0C0E"
SURFACE = "#1A1C21"
NAV_ACTIVE = "#2A2D34"
TEXT_MUTED = "#9298A3"


class HelixApp(ctk.CTk):
    """Desktop shell for HELIX's existing portfolio analysis."""

    def __init__(self):
        super().__init__()
        self.title("HELIX — Investing Intelligence")
        self.geometry("1360x820")
        self.minsize(1050, 650)
        self.analysis = None
        self.refreshing = False
        self.refresh_error = None
        self.financials_ticker = None
        self.page_name = "Dashboard"

        self.configure(fg_color=APP_BACKGROUND)
        self.sidebar = ctk.CTkFrame(self, width=232, corner_radius=0, fg_color=SIDEBAR_BACKGROUND)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=APP_BACKGROUND)
        self.content.pack(side="right", fill="both", expand=True)
        self.current_page = None

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=24, pady=(28, 30))
        ctk.CTkLabel(brand, text="H", width=34, height=34, corner_radius=9, fg_color="#F1F3F5", text_color="#101114", font=("Arial", 18, "bold")).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(brand, text="HELIX", font=("Arial", 22, "bold"), text_color="#F4F5F7").pack(side="left")
        ctk.CTkLabel(self.sidebar, text="PORTFOLIO", font=("Arial", 10, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=26, pady=(0, 8))
        self.buttons = {}
        for name in ("Dashboard", "Portfolio", "Performance", "Watchlist", "Income & earnings"):
            button = ctk.CTkButton(
                self.sidebar, text=name, anchor="w", height=42, corner_radius=8,
                fg_color="transparent", text_color="#DFE2E7", hover_color="#202229",
                command=lambda page=name: self.show_page(page),
            )
            button.pack(fill="x", padx=16, pady=2)
            self.buttons[name] = button
        ctk.CTkLabel(self.sidebar, text="RESEARCH", font=("Arial", 10, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=26, pady=(26, 8))
        for name in ("Markets", "Financials", "News", "AI Analysis"):
            button = ctk.CTkButton(
                self.sidebar, text=name, anchor="w", height=42, corner_radius=8,
                fg_color="transparent", text_color="#DFE2E7", hover_color="#202229",
                command=lambda page=name: self.show_page(page),
            )
            button.pack(fill="x", padx=16, pady=2)
            self.buttons[name] = button
        ctk.CTkLabel(self.sidebar, text="SETTINGS", font=("Arial", 10, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=26, pady=(26, 8))
        settings_button = ctk.CTkButton(self.sidebar, text="Settings", anchor="w", height=42, corner_radius=8, fg_color="transparent", text_color="#DFE2E7", hover_color="#202229", command=lambda: self.show_page("Settings"))
        settings_button.pack(fill="x", padx=16, pady=2)
        self.buttons["Settings"] = settings_button
        ctk.CTkLabel(self.sidebar, text="Data powered by Yahoo Finance", font=("Arial", 10), text_color=TEXT_MUTED, wraplength=165, justify="left").pack(side="bottom", anchor="w", padx=24, pady=24)
        self.refresh_data()

    def refresh_data(self):
        if self.refreshing:
            return
        self.refreshing = True
        result = queue.Queue()
        def fetch():
            try:
                result.put((load_dashboard_data(), None))
            except Exception as error:
                result.put((None, str(error)))
        threading.Thread(target=fetch, daemon=True).start()
        self.show_page(self.page_name)
        def finish():
            try:
                analysis, error = result.get_nowait()
            except queue.Empty:
                self.after(100, finish)
                return
            self.refreshing = False
            self.refresh_error = error
            if error is None:
                self.analysis = analysis
                if analysis:
                    from analytics.performance_history import record_snapshot
                    try:
                        record_snapshot(analysis["portfolio_value"], analysis["portfolio_cost"])
                    except (OSError, ValueError) as failure:
                        self.refresh_error = f"Prices updated, but history could not be saved: {failure}"
            self.show_page(self.page_name)
        self.after(100, finish)

    def show_page(self, page_name):
        self.page_name = page_name
        if self.current_page:
            self.current_page.destroy()
        for name, button in self.buttons.items():
            button.configure(fg_color=NAV_ACTIVE if name == page_name else "transparent")
        pages = {
            "Dashboard": lambda: DashboardPage(self.content, self.analysis, self.refresh_data),
            "Portfolio": lambda: PortfolioPage(self.content, self.analysis),
            "Performance": lambda: PerformancePage(self.content, self.analysis),
            "Watchlist": lambda: WatchlistPage(self.content, self.open_financials),
            "Income & earnings": lambda: IncomePage(self.content),
            "AI Analysis": lambda: AIPage(self.content, self.analysis),
            "Markets": lambda: MarketsPage(self.content),
            "Financials": lambda: FinancialsPage(self.content, self.financials_ticker),
            "News": lambda: NewsPage(self.content),
            "Settings": lambda: SettingsPage(self.content, self.refresh_data),
        }
        if getattr(self, "status_label", None):
            self.status_label.destroy()
        status = "Refreshing portfolio…" if self.refreshing else self.refresh_error
        if status:
            if self.refresh_error and self.analysis:
                status += " Displaying previously loaded prices."
            self.status_label = ctk.CTkLabel(self.content, text=status, text_color="#FFD39A", wraplength=850)
            self.status_label.pack(fill="x", padx=24, pady=8)
        else:
            self.status_label = None
        self.current_page = pages[page_name]()
        self.current_page.pack(fill="both", expand=True)

    def open_financials(self, ticker):
        self.financials_ticker = ticker
        self.show_page("Financials")


if __name__ == "__main__":
    HelixApp().mainloop()
