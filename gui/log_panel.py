from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from . import theme


class LogPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=theme.APP_BG, corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="KJØRELOGG", font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED).grid(
            row=0, column=0, padx=8, pady=(4, 8), sticky="w"
        )
        ctk.CTkButton(header, text="Tøm", width=58, height=24, command=self.clear, font=theme.SMALL_FONT).grid(
            row=0, column=1, padx=8, pady=(2, 6)
        )

        self.textbox = ctk.CTkTextbox(self, fg_color=theme.PANEL_BG_DARK, wrap="word", font=theme.NORMAL_FONT)
        self.textbox.grid(row=1, column=0, padx=4, pady=0, sticky="nsew")

    def append(self, text: str, timestamp: bool = True) -> None:
        prefix = f"[{datetime.now().strftime('%H:%M:%S')}] " if timestamp else ""
        self.textbox.insert("end", prefix + text.rstrip() + "\n")
        self.textbox.see("end")

    def clear(self) -> None:
        self.textbox.delete("1.0", "end")
