from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from . import theme


class LogPanel(ctk.CTkFrame):
    MAX_LINES = 2000
    LAST_LINES = 25

    def __init__(self, master):
        super().__init__(master, fg_color=theme.SURFACE_BG, corner_radius=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._entries: list[str] = []
        self._show_all = True

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="KJØRELOGG",
            font=theme.font(theme.SECTION_SIZE, "bold"),
            text_color=theme.TEXT_MUTED,
        ).grid(row=0, column=0, sticky="w")

        self.show_button = ctk.CTkButton(
            header,
            text="Vis siste",
            width=66,
            height=22,
            font=theme.font(theme.SMALL_SIZE),
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            command=self._toggle_show,
        )
        self.show_button.grid(row=0, column=1, padx=(0, 4))

        ctk.CTkButton(
            header,
            text="Tøm",
            width=50,
            height=22,
            command=self.clear,
            font=theme.font(theme.SMALL_SIZE),
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
        ).grid(row=0, column=2)

        self.textbox = ctk.CTkTextbox(
            self,
            fg_color=theme.APP_BG,
            text_color=theme.TEXT,
            wrap="word",
            font=theme.font(theme.NORMAL_SIZE),
            corner_radius=8,
            state="disabled",
        )
        self.textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def append(self, text: str, timestamp: bool = True) -> None:
        prefix = f"[{datetime.now().strftime('%H:%M:%S')}] " if timestamp else ""
        entry = prefix + text.rstrip()
        self._entries.append(entry)
        self._entries = self._entries[-self.MAX_LINES :]
        self._redraw()

    def clear(self) -> None:
        self._entries.clear()
        self._redraw()

    def _toggle_show(self) -> None:
        self._show_all = not self._show_all
        self.show_button.configure(text="Vis siste" if self._show_all else "Vis alle")
        self._redraw()

    def _redraw(self) -> None:
        entries = self._entries if self._show_all else self._entries[-self.LAST_LINES :]
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        if entries:
            self.textbox.insert("end", "\n".join(entries) + "\n")
        self.textbox.configure(state="disabled")
        self.textbox.see("end")
