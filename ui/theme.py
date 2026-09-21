"""Shared visual language for the HELIX desktop experience."""

BACKGROUND = "#121316"
SURFACE = "#1A1C21"
SURFACE_ALT = "#23252B"
TABLE_HEADER = "#2A2D34"
TEXT = "#F3F4F6"
MUTED = "#9298A3"
ACCENT = "#B7D9FF"
POSITIVE = "#55D692"
NEGATIVE = "#FF7272"


def primary_button(button):
    button.configure(
        fg_color="#F1F3F5",
        text_color="#111214",
        hover_color="#D8DBE0",
        corner_radius=8,
    )
