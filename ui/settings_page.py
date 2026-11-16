import webbrowser

import customtkinter as ctk

from ui.theme import BACKGROUND, MUTED, SURFACE, TEXT


class SettingsPage(ctk.CTkFrame):

    def __init__(self, master, on_refresh=None):
        super().__init__(master, fg_color=BACKGROUND)

        ctk.CTkLabel(
            self,
            text="Settings",
            font=("Arial", 30, "bold"), text_color=TEXT
        ).pack(anchor="nw", padx=42, pady=(34, 3))
        ctk.CTkLabel(self, text="Manage how HELIX refreshes and connects your data.", text_color=MUTED, font=("Arial", 14)).pack(anchor="nw", padx=42, pady=(0, 22))

        portfolio = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=12)
        portfolio.pack(fill="x", padx=42, pady=(0, 14))
        ctk.CTkLabel(portfolio, text="Portfolio data", text_color=TEXT, font=("Arial", 19, "bold")).pack(anchor="w", padx=22, pady=(18, 4))
        ctk.CTkLabel(portfolio, text="Refresh prices and recalculate the dashboard.", text_color=MUTED, font=("Arial", 14)).pack(anchor="w", padx=22)
        ctk.CTkButton(portfolio, text="Refresh portfolio", height=34, corner_radius=8, fg_color="#F1F3F5", text_color="#111214", hover_color="#D8DBE0", command=on_refresh).pack(anchor="w", padx=22, pady=(14, 18))

        brokerage = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=12)
        brokerage.pack(fill="x", padx=42, pady=14)
        ctk.CTkLabel(brokerage, text="Brokerage connection", text_color=TEXT, font=("Arial", 19, "bold")).pack(anchor="w", padx=22, pady=(18, 4))
        ctk.CTkLabel(
            brokerage,
            text="Connect through Plaid's browser-based, holdings-only flow. The local connector must be running first. Connecting does not import holdings into the desktop portfolio yet.",
            text_color=MUTED, font=("Arial", 14), wraplength=700, justify="left"
        ).pack(anchor="w", padx=22, pady=(0, 14))
        ctk.CTkButton(
            brokerage,
            text="Open secure brokerage connection",
            height=34, corner_radius=8, fg_color="#F1F3F5", text_color="#111214", hover_color="#D8DBE0",
            command=lambda: webbrowser.open("http://127.0.0.1:8765"),
        ).pack(anchor="w", padx=22, pady=(0, 18))
