from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk

from noark5_workflow.operations.dias_package import DEFAULT_PARAMS
from . import theme


_FIELDS = [
    ("submission_agreement", "Submission Agreement"),
    ("label", "Pakketittel"),
    ("system", "Kildesystem"),
    ("system_version", "Systemversjon"),
    ("period_start", "Periodens start (ÅÅÅÅ-MM-DD)"),
    ("period_end", "Periodens slutt (ÅÅÅÅ-MM-DD)"),
    ("owner_org", "Eierorganisasjon"),
    ("archivist_org", "Arkivorganisasjon"),
    ("submitter_org", "Avleverende organisasjon"),
    ("submitter_person", "Avleverende person"),
    ("producer_org", "Produsent (org)"),
    ("producer_person", "Produsent (person)"),
    ("creator", "Skaper"),
    ("preserver", "Bevaringsansvarlig"),
]


class DiasParamDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        initial: dict,
        extraction_root: Path | None,
        on_confirm: Callable[[dict], None],
    ) -> None:
        super().__init__(parent)
        self.title("Konfigurer: DIAS-pakking (SIP/AIC)")
        self.geometry("690x760")
        self.minsize(640, 660)
        self.configure(fg_color=theme.APP_BG)
        self.transient(parent)
        self.grab_set()
        self.on_confirm = on_confirm
        self.vars: dict[str, ctk.StringVar] = {}

        values = {**DEFAULT_PARAMS, **(initial or {})}
        if extraction_root:
            values["label"] = values.get("label") or extraction_root.name
            values["output_dir"] = values.get("output_dir") or str(extraction_root.parent)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="DIAS-PAKKING (SIP/AIC)", font=theme.font(theme.SECTION_SIZE, "bold"), text_color=theme.TEXT).grid(
            row=0, column=0, padx=18, pady=(16, 8), sticky="w"
        )

        form = ctk.CTkScrollableFrame(self, fg_color=theme.SURFACE_BG, corner_radius=8)
        form.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")
        form.grid_columnconfigure(1, weight=1)

        row = 0
        for key, label in _FIELDS:
            ctk.CTkLabel(form, text=label, font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_SUB).grid(
                row=row, column=0, padx=(12, 8), pady=5, sticky="w"
            )
            var = ctk.StringVar(value=str(values.get(key, "")))
            self.vars[key] = var
            ctk.CTkEntry(form, textvariable=var, font=theme.font(theme.SMALL_SIZE)).grid(
                row=row, column=1, padx=(0, 12), pady=5, sticky="ew"
            )
            row += 1

        ctk.CTkLabel(form, text="Arkivtype", font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_SUB).grid(
            row=row, column=0, padx=(12, 8), pady=5, sticky="w"
        )
        self.vars["archivist_type"] = ctk.StringVar(value=str(values.get("archivist_type", "NOARK-5")))
        ctk.CTkOptionMenu(
            form,
            values=["NOARK-5", "Postjournaler", "Annet"],
            variable=self.vars["archivist_type"],
            font=theme.font(theme.SMALL_SIZE),
        ).grid(row=row, column=1, padx=(0, 12), pady=5, sticky="ew")
        row += 1

        ctk.CTkLabel(form, text="Produsent (programvare)", font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_SUB).grid(
            row=row, column=0, padx=(12, 8), pady=5, sticky="w"
        )
        self.vars["producer_software"] = ctk.StringVar(value=str(values.get("producer_software", "Noark 5 Workflow Manager")))
        ctk.CTkEntry(form, textvariable=self.vars["producer_software"], font=theme.font(theme.SMALL_SIZE)).grid(
            row=row, column=1, padx=(0, 12), pady=5, sticky="ew"
        )
        row += 1

        ctk.CTkLabel(form, text="Utdatamappe", font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_SUB).grid(
            row=row, column=0, padx=(12, 8), pady=5, sticky="w"
        )
        out_row = ctk.CTkFrame(form, fg_color="transparent")
        out_row.grid(row=row, column=1, padx=(0, 12), pady=5, sticky="ew")
        out_row.grid_columnconfigure(0, weight=1)
        self.vars["output_dir"] = ctk.StringVar(value=str(values.get("output_dir", "")))
        ctk.CTkEntry(out_row, textvariable=self.vars["output_dir"], font=theme.font(theme.SMALL_SIZE)).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(out_row, text="...", width=34, command=self._browse_output, font=theme.font(theme.NORMAL_SIZE)).grid(row=0, column=1, padx=(6, 0))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=2, column=0, padx=16, pady=(6, 16), sticky="ew")
        buttons.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(buttons, text="Avbryt", fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER, command=self.destroy, font=theme.font(theme.NORMAL_SIZE)).grid(
            row=0, column=1, padx=(6, 0)
        )
        ctk.CTkButton(buttons, text="Legg til i workflow", fg_color=theme.BLUE, hover_color=theme.BLUE_DIM, command=self._confirm, font=theme.font(theme.NORMAL_SIZE)).grid(
            row=0, column=2, padx=(6, 0)
        )

    def _browse_output(self) -> None:
        folder = filedialog.askdirectory(title="Velg utdatamappe for DIAS-pakke")
        if folder:
            self.vars["output_dir"].set(folder)

    def _confirm(self) -> None:
        values = {key: var.get().strip() for key, var in self.vars.items()}
        required = [
            "submission_agreement", "label", "system", "system_version", "archivist_type",
            "period_start", "period_end", "owner_org", "archivist_org", "submitter_org",
            "submitter_person", "producer_org", "producer_person", "producer_software",
            "creator", "preserver",
        ]
        missing = [key for key in required if not values.get(key)]
        if missing:
            messagebox.showwarning("DIAS-pakking", "Fyll ut alle obligatoriske felt før operasjonen legges til.", parent=self)
            return
        self.on_confirm(values)
        self.destroy()
