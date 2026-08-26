from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from noark5_workflow.sources.noark5_extraction import Noark5Extraction
from . import theme


class SourcePanel(ctk.CTkFrame):
    def __init__(self, master, on_source_changed: Callable[[Noark5Extraction | None], None]):
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=8)
        self.on_source_changed = on_source_changed
        self.extraction: Noark5Extraction | None = None
        self.path_var = ctk.StringVar()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self, text="NOARK 5", font=theme.SECTION_FONT, text_color=theme.TEXT_MUTED).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )

        self.path_entry = ctk.CTkEntry(self, textvariable=self.path_var, font=theme.SMALL_FONT)
        self.path_entry.grid(row=1, column=0, padx=10, pady=(4, 4), sticky="ew")

        self.browse_button = ctk.CTkButton(
            self, text="Bla gjennom...", command=self._browse, height=30, font=theme.SMALL_FONT
        )
        self.browse_button.grid(row=2, column=0, padx=10, pady=(4, 8), sticky="ew")

        self.info = ctk.CTkTextbox(self, height=180, wrap="word", font=theme.SMALL_FONT)
        self.info.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self._set_text("Velg rotmappe for et Noark 5-uttrekk.")

    def _browse(self) -> None:
        folder = filedialog.askdirectory(title="Velg rotmappe for Noark 5-uttrekk")
        if folder:
            self.set_path(folder)

    def set_path(self, folder: str) -> None:
        self.path_var.set(folder)
        self.detect()

    def detect(self) -> None:
        root = self.path_var.get().strip()
        if not root:
            self.extraction = None
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
        lines = ["Noark 5-uttrekk" if extraction.is_noark5_candidate else "Ikke gjenkjent som Noark 5-uttrekk", ""]
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
