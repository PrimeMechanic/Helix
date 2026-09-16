import customtkinter as ctk


class NewsPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        ctk.CTkLabel(
            self,
            text="Market News",
            font=("Arial", 30, "bold")
        ).pack(anchor="nw", padx=30, pady=30)

        ctk.CTkLabel(
            self,
            text="News feeds are not connected yet. This page is ready for a selected news provider.",
            font=("Arial", 16), text_color="#a8b3c2", wraplength=700, justify="left"
        ).pack(anchor="nw", padx=30)
