from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from noark5_workflow.sources.noark5_extraction import Noark5Extraction
from . import theme


class SourcePanel(ctk.CTkFrame):
    def __init__(self, master, on_source_changed: Callable[[Noark5Extraction | None], None]):
        super().__init__(master, fg_color=theme.SURFACE_BG, corner_radius=10)
        self.on_source_changed = on_source_changed
        self.extraction: Noark5Extraction | None = None
        self.path_var = ctk.StringVar()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self,
            text="NOARK 5",
            font=theme.font(theme.SECTION_SIZE, "bold"),
            text_color=theme.TEXT_MUTED,
        ).grid(row=0, column=0, padx=12, pady=(10, 6), sticky="w")

        self.dropzone = ctk.CTkButton(
            self,
            text="Dra og slipp eller klikk for å velge\nNoark 5-uttrekk",
            command=self._browse,
            height=52,
            fg_color=theme.DROPZONE_BG,
            hover_color="#223152",
            text_color=theme.TEXT_SUB,
            font=theme.font(theme.NORMAL_SIZE),
            corner_radius=4,
        )
        self.dropzone.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")

        self.selected_label = ctk.CTkLabel(
            self,
            text="(tom)",
            font=theme.font(theme.SMALL_SIZE),
            text_color=theme.TEXT_MUTED,
            anchor="center",
        )
        self.selected_label.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")

        self.info = ctk.CTkTextbox(
            self,
            wrap="word",
            font=theme.font(theme.SMALL_SIZE),
            fg_color=theme.PANEL_BG_DARK,
            text_color=theme.TEXT_SUB,
            corner_radius=6,
            state="disabled",
        )
        self.info.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self._set_text("Velg rotmappe for et Noark 5-uttrekk.")

    def _browse(self) -> None:
        folder = filedialog.askdirectory(title="Velg rotmappe for Noark 5-uttrekk")
        if folder:
            self.set_path(folder)

    def set_path(self, folder: str) -> None:
        self.path_var.set(folder)
        self.selected_label.configure(text=Path(folder).name or folder)
        self.detect()

    def detect(self) -> None:
        root = self.path_var.get().strip()
        if not root:
            self.extraction = None
            self.selected_label.configure(text="(tom)")
            self.on_source_changed(None)
            return
        try:
            self.extraction = Noark5Extraction.detect(Path(root))
            self._render_inventory(self.extraction)
        except Exception as exc:
            self.extraction = None
            self._set_text(f"FEIL: {exc}")
        self.on_source_changed(self.extraction)

    def _render_inventory(self, extraction: Noark5Extraction) -> None:
        lines = []
        labels = {
            "arkivstruktur": "arkivstruktur.xml",
            "arkivuttrekk": "arkivuttrekk.xml",
            "loepende_journal": "loependeJournal.xml",
            "offentlig_journal": "offentligJournal.xml",
            "endringslogg": "endringslogg.xml",
        }
        for key, label in labels.items():
            lines.append(f"[OK] {label}" if extraction.metadata_files.get(key) else f"[--] {label}")
        lines.append(f"[OK] XSD-filer: {len(extraction.xsd_files)}")
        lines.append("[OK] dokumenter/" if extraction.documents_dir else "[--] dokumenter/")
        if extraction.business_metadata_files:
            lines.append(f"[OK] Virksomhetsspesifikke metadata: {len(extraction.business_metadata_files)}")
        self._set_text("\n".join(lines))

    def _set_text(self, text: str) -> None:
        self.info.configure(state="normal")
        self.info.delete("1.0", "end")
        self.info.insert("1.0", text)
        self.info.configure(state="disabled")
