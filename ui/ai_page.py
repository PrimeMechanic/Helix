import customtkinter as ctk


class AIPage(ctk.CTkFrame):

    def __init__(self, master, data=None):
        super().__init__(master)

        ctk.CTkLabel(
            self,
            text="AI Analysis",
            font=("Arial", 30, "bold")
        ).pack(anchor="nw", padx=30, pady=30)
        if not data:
            ctk.CTkLabel(self, text="Analysis is unavailable until quotes can be retrieved.").pack(anchor="nw", padx=30)
            return
        ctk.CTkLabel(self, text=f"{data['stars']}  •  Health score {data['health']} / 100", font=("Arial", 21, "bold"), text_color="#60a5fa").pack(anchor="nw", padx=30)
        ctk.CTkLabel(self, text=f"Risk level: {data['risk']}", font=("Arial", 16), text_color="#c5d0df").pack(anchor="nw", padx=30, pady=(8, 24))
        card = ctk.CTkFrame(self)
        card.pack(fill="x", padx=30)
        ctk.CTkLabel(card, text="Insights", font=("Arial", 20, "bold")).pack(anchor="w", padx=22, pady=(20, 10))
        for recommendation in data["recommendations"]:
            ctk.CTkLabel(card, text=f"•  {recommendation}", wraplength=760, justify="left", font=("Arial", 15)).pack(anchor="w", padx=22, pady=6)
        ctk.CTkLabel(card, text="", height=12).pack()
