from __future__ import annotations

import os
import shutil
from pathlib import Path

import customtkinter as ctk

from . import theme


class StatusBar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=theme.PANEL_BG_DARK, corner_radius=0, height=26)
        self.grid_columnconfigure(1, weight=1)
        self.left_var = ctk.StringVar(value="Temp: (auto)")
        self.status_var = ctk.StringVar(value="Klar")
        self.right_var = ctk.StringVar(value=f"Backend: lokal | Tråder: {os.cpu_count() or 1}")
        ctk.CTkLabel(self, textvariable=self.left_var, font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED).grid(
            row=0, column=0, padx=10, pady=4, sticky="w"
        )
        ctk.CTkLabel(self, textvariable=self.status_var, font=theme.SMALL_FONT).grid(
            row=0, column=1, padx=10, pady=4
        )
        ctk.CTkLabel(self, textvariable=self.right_var, font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED).grid(
            row=0, column=2, padx=10, pady=4, sticky="e"
        )

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def update_storage(self, path: str | Path | None) -> None:
        if not path:
            return
        try:
            usage = shutil.disk_usage(str(path))
            free_gib = usage.free / (1024 ** 3)
            self.right_var.set(f"Ledig: {free_gib:,.1f} GB | Tråder: {os.cpu_count() or 1} | Backend: lokal")
        except OSError:
            self.right_var.set(f"Tråder: {os.cpu_count() or 1} | Backend: lokal")
