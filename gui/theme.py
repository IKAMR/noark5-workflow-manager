import customtkinter as ctk

CATEGORIES = [
    "Pipeline",
    "Integritet",
    "Sikkerhet",
    "Innhold",
    "Systemspesifikt",
    "Kompatibilitet",
    "Rapport",
    "Metadata",
    "SIP/AIC-Pakking",
]

CATEGORY_COLORS = {
    "Pipeline": "#4d8df7",
    "Integritet": "#4d8df7",
    "Sikkerhet": "#ef5350",
    "Innhold": "#f6c23e",
    "Systemspesifikt": "#4d8df7",
    "Kompatibilitet": "#4d8df7",
    "Rapport": "#ff7a18",
    "Metadata": "#9b7df5",
    "SIP/AIC-Pakking": "#4d8df7",
}

APP_BG = "#10131a"
PANEL_BG = "#181d29"
PANEL_BG_DARK = "#0d1017"
CARD_BG = "#1a1f2b"
CARD_BORDER = "#2c3447"
TEXT = "#f3f5fa"
TEXT_MUTED = "#9ba8c3"
BLUE = "#4d8df7"

TITLE_FONT = ("Consolas", 15, "bold")
SECTION_FONT = ("Consolas", 12, "bold")
NORMAL_FONT = ("Consolas", 11)
SMALL_FONT = ("Consolas", 9)


def apply_theme() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
