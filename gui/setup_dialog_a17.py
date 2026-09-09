from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from . import theme
from .settings_dialog import SettingsDialog
from .ui_contract_a17 import SETUP_TITLE


class SetupDialog(SettingsDialog):
    """a17 presentation layer for the established global settings dialog."""

    def __init__(self, master, settings: dict, on_save):
        super().__init__(master, settings, on_save)
        self.title(SETUP_TITLE)
        self._rename_heading()
        self._add_temp_browse_button()

    def _walk_widgets(self, widget):
        for child in widget.winfo_children():
            yield child
            yield from self._walk_widgets(child)

    def _rename_heading(self) -> None:
        for child in self._walk_widgets(self):
            if not isinstance(child, ctk.CTkLabel):
                continue
            try:
                if str(child.cget("text")) == "Globale innstillinger":
                    child.configure(text=SETUP_TITLE)
                    return
            except Exception:
                continue

    def _add_temp_browse_button(self) -> None:
        """Replace only the inherited Temp entry cell with entry + browse.

        Find the real CTkEntry by its StringVar rather than assuming a specific
        CTkScrollableFrame nesting. This keeps the enhancement stable when the
        base SettingsDialog layout changes.
        """
        temp_entry = None
        temp_var_name = str(self.temp_var)
        for child in self._walk_widgets(self):
            if not isinstance(child, ctk.CTkEntry):
                continue
            try:
                if str(child.cget("textvariable")) == temp_var_name:
                    temp_entry = child
                    break
            except Exception:
                continue
        if temp_entry is None:
            return

        parent = temp_entry.master
        info = temp_entry.grid_info()
        if not info:
            return
        row_no = int(info.get("row", 1))
        col_no = int(info.get("column", 1))
        padx = info.get("padx", 12)
        pady = info.get("pady", 8)
        sticky = info.get("sticky", "ew") or "ew"
        temp_entry.grid_forget()

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=row_no, column=col_no, padx=padx, pady=pady, sticky=sticky)
        row.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(
            row, textvariable=self.temp_var, font=theme.font(theme.NORMAL_SIZE)
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            row,
            text="Velg…",
            width=68,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            command=self._browse_temp_dir,
        ).grid(row=0, column=1, padx=(6, 0))

    def _browse_temp_dir(self) -> None:
        current = self.temp_var.get().strip()
        kwargs = {"title": "Velg temp-mappe"}
        if current and Path(current).is_dir():
            kwargs["initialdir"] = current
        folder = filedialog.askdirectory(**kwargs)
        if folder:
            self.temp_var.set(folder)
