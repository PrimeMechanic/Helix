import webbrowser

import customtkinter as ctk


class SettingsPage(ctk.CTkFrame):

    def __init__(self, master, on_refresh=None):
        super().__init__(master)

        ctk.CTkLabel(
            self,
            text="Settings",
            font=("Arial", 30, "bold")
        ).pack(anchor="nw", padx=30, pady=30)

        ctk.CTkLabel(self, text="Portfolio data", font=("Arial", 20, "bold")).pack(anchor="nw", padx=30)
        ctk.CTkLabel(self, text="Refresh prices and recalculate your dashboard.", text_color="#a8b3c2", font=("Arial", 15)).pack(anchor="nw", padx=30, pady=(6, 14))
        ctk.CTkButton(self, text="Refresh portfolio data", command=on_refresh).pack(anchor="nw", padx=30)

        ctk.CTkLabel(self, text="Brokerage connection", font=("Arial", 20, "bold")).pack(anchor="nw", padx=30, pady=(34, 0))
        ctk.CTkLabel(
            self,
            text="Connect through Plaid's browser-based, holdings-only flow. The local connector must be running first.",
            text_color="#a8b3c2", font=("Arial", 15), wraplength=700, justify="left"
        ).pack(anchor="nw", padx=30, pady=(6, 14))
        ctk.CTkButton(
            self,
            text="Open secure brokerage connection",
            command=lambda: webbrowser.open("http://127.0.0.1:8765"),
        ).pack(anchor="nw", padx=30)
