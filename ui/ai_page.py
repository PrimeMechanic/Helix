import customtkinter as ctk

from ui.theme import ACCENT, BACKGROUND, MUTED, SURFACE, SURFACE_ALT, TEXT


class AIPage(ctk.CTkFrame):

    def __init__(self, master, data=None):
        super().__init__(master, fg_color=BACKGROUND)

        ctk.CTkLabel(
            self,
            text="AI Analysis",
            font=("Arial", 30, "bold"), text_color=TEXT
        ).pack(anchor="nw", padx=42, pady=(34, 3))
        ctk.CTkLabel(self, text="A focused read on concentration, performance, and risk.", font=("Arial", 14), text_color=MUTED).pack(anchor="nw", padx=42, pady=(0, 22))
        if not data:
            ctk.CTkLabel(self, text="Analysis is unavailable until quotes can be retrieved.", text_color=MUTED).pack(anchor="nw", padx=42)
            return
        score = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=12)
        score.pack(fill="x", padx=42, pady=(0, 18))
        ctk.CTkLabel(score, text="PORTFOLIO HEALTH", text_color=MUTED, font=("Arial", 11, "bold")).pack(anchor="w", padx=22, pady=(18, 4))
        ctk.CTkLabel(score, text=f"{data['stars']}  {data['health']} / 100", font=("Arial", 25, "bold"), text_color=ACCENT).pack(anchor="w", padx=22)
        ctk.CTkLabel(score, text=f"Risk level · {data['risk']}", font=("Arial", 13), text_color="#D6D8DE").pack(anchor="w", padx=22, pady=(3, 18))
        card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=12)
        card.pack(fill="x", padx=42)
        ctk.CTkLabel(card, text="Key insights", text_color=TEXT, font=("Arial", 20, "bold")).pack(anchor="w", padx=22, pady=(20, 10))
        for recommendation in data["recommendations"]:
            ctk.CTkLabel(card, text=f"•  {recommendation}", text_color="#D6D8DE", wraplength=760, justify="left", font=("Arial", 15)).pack(anchor="w", padx=22, pady=6)
        ctk.CTkLabel(card, text="", height=12).pack()
