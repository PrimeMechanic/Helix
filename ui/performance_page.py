import tkinter as tk

import customtkinter as ctk

from analytics.performance_history import load_history
from ui.theme import BACKGROUND, MUTED, POSITIVE, SURFACE, TEXT


class PerformancePage(ctk.CTkFrame):
    """Portfolio value history built from Helix's daily local snapshots."""

    def __init__(self, master, analysis=None):
        super().__init__(master, fg_color=BACKGROUND)
        self.analysis = analysis
        self.history = load_history()
        self.build()

    def build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=42, pady=(34, 8))
        title = ctk.CTkFrame(header, fg_color="transparent")
        title.pack(side="left")
        ctk.CTkLabel(title, text="Performance", text_color=TEXT, font=("Arial", 30, "bold")).pack(anchor="w")
        ctk.CTkLabel(title, text="Your portfolio value, recorded locally each day you refresh HELIX.", text_color=MUTED, font=("Arial", 14)).pack(anchor="w", pady=(2, 0))
        if self.analysis:
            current = ctk.CTkFrame(header, fg_color="transparent")
            current.pack(side="right")
            ctk.CTkLabel(current, text="CURRENT VALUE", text_color=MUTED, font=("Arial", 10, "bold")).pack(anchor="e")
            ctk.CTkLabel(current, text=f"${self.analysis['portfolio_value']:,.2f}", text_color=TEXT, font=("Arial", 20, "bold")).pack(anchor="e")

        chart_card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=12)
        chart_card.pack(fill="x", padx=42, pady=(24, 18))
        self.chart = tk.Canvas(chart_card, height=290, bg=SURFACE, highlightthickness=0)
        self.chart.pack(fill="x", padx=14, pady=14)
        self.chart.bind("<Configure>", lambda event: self.draw_chart())

        detail = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=12)
        detail.pack(fill="x", padx=42)
        if len(self.history) < 2:
            ctk.CTkLabel(detail, text="History starts today", text_color=TEXT, font=("Arial", 18, "bold")).pack(anchor="w", padx=22, pady=(18, 4))
            ctk.CTkLabel(detail, text="Refresh HELIX on future days to build your actual portfolio-performance trend. HELIX does not invent historical returns.", text_color=MUTED, font=("Arial", 14), wraplength=760, justify="left").pack(anchor="w", padx=22, pady=(0, 18))
        else:
            first, latest = self.history[0], self.history[-1]
            change = latest["value"] - first["value"]
            percentage = change / first["value"] * 100 if first["value"] else 0
            ctk.CTkLabel(detail, text="Recorded performance", text_color=TEXT, font=("Arial", 18, "bold")).pack(anchor="w", padx=22, pady=(18, 4))
            color = POSITIVE if change >= 0 else "#FF7272"
            ctk.CTkLabel(detail, text=f"{change:+,.2f} ({percentage:+.2f}%) since {first['date']}", text_color=color, font=("Arial", 16, "bold")).pack(anchor="w", padx=22, pady=(0, 18))

    def draw_chart(self):
        canvas = self.chart
        canvas.delete("all")
        width = max(canvas.winfo_width(), 520)
        height = 260
        left, right, top, bottom = 48, width - 22, 26, height - 44
        values = [entry["value"] for entry in self.history]
        if not values:
            canvas.create_text(width / 2, height / 2, text="Your daily portfolio-value trend will appear here.", fill=MUTED, font=("Arial", 14))
            return
        low, high = min(values), max(values)
        if low == high:
            low *= 0.98
            high *= 1.02
        padding = max((high - low) * 0.15, 1)
        low -= padding
        high += padding
        canvas.create_line(left, bottom, right, bottom, fill="#3A3D45")
        points = []
        for index, value in enumerate(values):
            x = left + (right - left) * index / max(len(values) - 1, 1)
            y = bottom - (value - low) / (high - low) * (bottom - top)
            points.extend((x, y))
        color = POSITIVE if values[-1] >= values[0] else "#FF7272"
        if len(points) == 2:
            x, y = points
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=color, outline="")
        else:
            canvas.create_line(*points, fill=color, width=3, smooth=True)
            canvas.create_oval(points[-2] - 4, points[-1] - 4, points[-2] + 4, points[-1] + 4, fill=color, outline="")
        canvas.create_text(left, 12, text=f"${high:,.0f}", anchor="w", fill=MUTED, font=("Arial", 10))
        canvas.create_text(left, bottom + 22, text=self.history[0]["date"], anchor="w", fill=MUTED, font=("Arial", 10))
        canvas.create_text(right, bottom + 22, text=self.history[-1]["date"], anchor="e", fill=MUTED, font=("Arial", 10))
