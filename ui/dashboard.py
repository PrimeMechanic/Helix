import customtkinter as ctk


class DashboardPage(ctk.CTkFrame):

    def __init__(self, master, data=None, on_refresh=None):
        super().__init__(master, fg_color="#121316")
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=42, pady=(34, 8))
        heading = ctk.CTkFrame(header, fg_color="transparent")
        heading.pack(side="left")
        ctk.CTkLabel(heading, text="Your portfolio", font=("Arial", 31, "bold"), text_color="#F4F5F7").pack(anchor="w")
        ctk.CTkLabel(heading, text="Live view of your investments", font=("Arial", 14), text_color="#9298A3").pack(anchor="w", pady=(2, 0))
        ctk.CTkButton(header, text="Refresh", width=96, height=36, corner_radius=8, fg_color="#F1F3F5", text_color="#111214", hover_color="#D8DBE0", command=on_refresh).pack(side="right")
        if not data:
            ctk.CTkLabel(self, text="Portfolio data is unavailable. Refresh to try again.", font=("Arial", 16), text_color="#a8b3c2").pack(anchor="nw", padx=34, pady=20)
            return
        daily = data["today_change"]
        summary = ctk.CTkFrame(self, fg_color="#1A1C21", corner_radius=12)
        summary.pack(fill="x", padx=42, pady=(24, 20))
        left = ctk.CTkFrame(summary, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=24, pady=22)
        ctk.CTkLabel(left, text="TOTAL PORTFOLIO VALUE", text_color="#9298A3", font=("Arial", 11, "bold")).pack(anchor="w")
        ctk.CTkLabel(left, text=f"${data['portfolio_value']:,.2f}", text_color="#F6F7F9", font=("Arial", 32, "bold")).pack(anchor="w", pady=(6, 2))
        ctk.CTkLabel(left, text=f"{data['portfolio_return']:+.2f}% unrealized return", text_color="#55D692" if data['portfolio_return'] >= 0 else "#FF7272", font=("Arial", 14, "bold")).pack(anchor="w")
        divider = ctk.CTkFrame(summary, width=1, fg_color="#30323A")
        divider.pack(side="left", fill="y", pady=22)
        right = ctk.CTkFrame(summary, fg_color="transparent", width=270)
        right.pack(side="right", padx=24, pady=22)
        ctk.CTkLabel(right, text="TODAY", text_color="#9298A3", font=("Arial", 11, "bold")).pack(anchor="w")
        daily_text = "Unavailable" if daily is None else f"{'+' if daily >= 0 else '-'}${abs(daily):,.2f}"
        daily_color = "#55D692" if daily is not None and daily >= 0 else "#FF7272" if daily is not None else "#F6F7F9"
        ctk.CTkLabel(right, text=daily_text, text_color=daily_color, font=("Arial", 23, "bold")).pack(anchor="w", pady=(7, 2))
        ctk.CTkLabel(right, text=f"Health {data['health']} / 100  ·  {data['risk']} risk", text_color="#C4C8D0", font=("Arial", 13)).pack(anchor="w")
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=42, pady=(0, 34))
        allocation = ctk.CTkFrame(grid, fg_color="#1A1C21", corner_radius=12)
        allocation.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(allocation, text="Portfolio allocation", font=("Arial", 19, "bold"), text_color="#F3F4F6").pack(anchor="w", padx=22, pady=(20, 4))
        ctk.CTkLabel(allocation, text="Your largest positions by market value", font=("Arial", 13), text_color="#9298A3").pack(anchor="w", padx=22, pady=(0, 14))
        for holding in data["allocations"][:5]:
            item = ctk.CTkFrame(allocation, fg_color="transparent")
            item.pack(fill="x", padx=22, pady=5)
            ctk.CTkLabel(item, text=holding["ticker"], width=66, anchor="w", text_color="#F2F3F5", font=("Arial", 14, "bold")).pack(side="left")
            ctk.CTkProgressBar(item, height=7, corner_radius=4, progress_color="#B7D9FF", fg_color="#30323A").pack(side="left", fill="x", expand=True, padx=8)
            item.winfo_children()[-1].set(min(holding["allocation"] / 100, 1))
            ctk.CTkLabel(item, text=f"{holding['allocation']:.1f}%", width=52, anchor="e", text_color="#C9CDD4", font=("Arial", 13)).pack(side="right")
        insight = ctk.CTkFrame(grid, fg_color="#1A1C21", corner_radius=12)
        insight.pack(side="right", fill="both", expand=True, padx=(10, 0))
        ctk.CTkLabel(insight, text="Key insights", font=("Arial", 19, "bold"), text_color="#F3F4F6").pack(anchor="w", padx=22, pady=(20, 14))
        highlights = (("Largest position", f"{data['largest']['ticker']} · ${data['largest']['value']:,.0f}"), ("Best performer", f"{data['best']['ticker']} · {data['best']['percent']:+.2f}%"), ("Portfolio health", f"{data['stars']} · {data['health']} / 100"))
        for label, value in highlights:
            item = ctk.CTkFrame(insight, fg_color="#23252B", corner_radius=8)
            item.pack(fill="x", padx=22, pady=5)
            ctk.CTkLabel(item, text=label.upper(), text_color="#9298A3", font=("Arial", 10, "bold")).pack(anchor="w", padx=14, pady=(10, 2))
            ctk.CTkLabel(item, text=value, text_color="#F1F3F5", font=("Arial", 14, "bold")).pack(anchor="w", padx=14, pady=(0, 10))
