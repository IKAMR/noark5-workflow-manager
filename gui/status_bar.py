from __future__ import annotations

import os
import shutil
from pathlib import Path

import customtkinter as ctk

from . import theme


class StatusBar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=theme.APP_BG, corner_radius=0, height=theme.STATUS_HEIGHT)
        self.grid_columnconfigure(1, weight=1)
        self.left_var = ctk.StringVar(value="Temp: (auto)")
        self.status_var = ctk.StringVar(value="Klar")
        self.right_var = ctk.StringVar(value=f"Tråder: {os.cpu_count() or 1} | Deteksjon: -- | Backend: lokal")

        ctk.CTkLabel(self, textvariable=self.left_var, font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED).grid(
            row=0, column=0, padx=10, pady=3, sticky="w"
        )
        ctk.CTkLabel(self, textvariable=self.status_var, font=theme.SMALL_FONT, text_color=theme.TEXT).grid(
            row=0, column=1, padx=10, pady=3
        )
        ctk.CTkLabel(self, textvariable=self.right_var, font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED).grid(
            row=0, column=2, padx=10, pady=3, sticky="e"
        )

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def set_temp(self, temp_dir: str | None) -> None:
        self.left_var.set(f"Temp: {temp_dir}" if temp_dir else "Temp: (auto)")

    def update_storage(self, path: str | Path | None, detection: str = "Noark 5") -> None:
        threads = os.cpu_count() or 1
        if not path:
            self.right_var.set(f"Tråder: {threads} | Deteksjon: {detection} | Backend: lokal")
            return
        try:
            usage = shutil.disk_usage(str(path))
            free_gib = usage.free / (1024 ** 3)
            self.right_var.set(
                f"Ledig: {free_gib:,.1f} GB | Tråder: {threads} | Deteksjon: {detection} | Backend: lokal"
            )
        except OSError:
            self.right_var.set(f"Tråder: {threads} | Deteksjon: {detection} | Backend: lokal")
