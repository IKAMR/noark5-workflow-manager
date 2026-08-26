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
    "Pipeline": "#4f8ef7",
    "Integritet": "#4f8ef7",
    "Sikkerhet": "#e05252",
    "Innhold": "#f0c040",
    "Systemspesifikt": "#4f8ef7",
    "Kompatibilitet": "#4f8ef7",
    "Rapport": "#f97316",
    "Metadata": "#a78bfa",
    "SIP/AIC-Pakking": "#4f8ef7",
}

APP_BG = "#0d0f14"
SURFACE_BG = "#13161e"
PANEL_BG = "#191d28"
PANEL_BG_DARK = "#0d1017"
DROPZONE_BG = "#1a2640"
CARD_BG = "#191d28"
CARD_BORDER = "#252b3a"
TEXT = "#d4daf0"
TEXT_SUB = "#b7bcc8"
TEXT_MUTED = "#8a95b0"
BLUE = "#4f8ef7"
BLUE_DIM = "#3a70d4"
BUTTON_BG = "#1e2333"
BUTTON_HOVER = "#252b3a"
DANGER_BG = "#2a1515"
DANGER_TEXT = "#e05252"

FONT_FAMILY = "Courier New"
TITLE_FONT = (FONT_FAMILY, 13, "bold")
SECTION_FONT = (FONT_FAMILY, 10, "bold")
NORMAL_FONT = (FONT_FAMILY, 10)
SMALL_FONT = (FONT_FAMILY, 9)

HEADER_HEIGHT = 48
LEFT_WIDTH = 390
OPERATIONS_HEIGHT = 142
STATUS_HEIGHT = 24


def apply_theme() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
