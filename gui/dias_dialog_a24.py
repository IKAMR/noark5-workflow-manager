from __future__ import annotations

import datetime
import json
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from .dias_dialog import _FIELDS, _REQUIRED
from .dias_dialog_a23 import DiasParamDialog as A23DiasParamDialog
from . import theme


class DiasParamDialog(A23DiasParamDialog):
    """a2.4: bedre target-visning og validering uten å lukke dialogen."""

    def __init__(
        self,
        parent,
        initial: dict,
        extraction_root,
        on_confirm: Callable[[dict], bool | None],
    ) -> None:
        super().__init__(parent, initial, extraction_root, on_confirm)

    def _build_form(self, parent: ctk.CTkFrame) -> None:
        form = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        form.grid(row=1, column=0, padx=10, pady=(2, 10), sticky="nsew")
        form.grid_columnconfigure(0, weight=0)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            form,
            text="Utdatamappe",
            font=theme.font(theme.SMALL_SIZE, "bold"),
            text_color=theme.BLUE,
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(6, 3), sticky="w")

        self.vars["output_dir"] = ctk.StringVar(value=str(self.values.get("output_dir", "")))

        self.output_display = ctk.CTkTextbox(
            form,
            height=58,
            wrap="char",
            font=theme.font(theme.SMALL_SIZE),
        )
        self.output_display.grid(
            row=1, column=0, columnspan=2, padx=10, pady=(0, 4), sticky="ew"
        )
        self._refresh_output_display()

        ctk.CTkButton(
            form,
            text="Velg mappe…",
            width=120,
            command=self._browse_output,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            font=theme.font(theme.SMALL_SIZE),
        ).grid(row=2, column=0, columnspan=2, padx=10, pady=(2, 10), sticky="w")

        mets_row = ctk.CTkFrame(form, fg_color="transparent")
        mets_row.grid(row=3, column=0, columnspan=2, padx=6, pady=(2, 8), sticky="w")
        ctk.CTkButton(
            mets_row,
            text="Les inn fra METS-fil …",
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            font=theme.font(theme.SMALL_SIZE),
            command=self._load_from_mets,
        ).pack(side="left")
        ctk.CTkLabel(
            mets_row,
            text="  info.xml, mets.xml eller annen METS XML",
            font=theme.font(theme.SMALL_SIZE),
            text_color=theme.TEXT_MUTED,
        ).pack(side="left")

        for row, (key, label) in enumerate(_FIELDS, start=4):
            ctk.CTkLabel(
                form,
                text=label,
                font=theme.font(theme.SMALL_SIZE),
                text_color=theme.TEXT_SUB,
            ).grid(row=row, column=0, padx=(10, 8), pady=5, sticky="w")
            var = ctk.StringVar(value=str(self.values.get(key, "")))
            self.vars[key] = var
            entry = ctk.CTkEntry(form, textvariable=var, font=theme.font(theme.SMALL_SIZE))
            entry.grid(row=row, column=1, padx=(0, 12), pady=5, sticky="ew")
            self.entries[key] = entry
            if key in ("period_start", "period_end"):
                entry.bind("<FocusOut>", lambda _event, k=key: self._validate_date(k, show_message=False))

    def _refresh_output_display(self) -> None:
        if not hasattr(self, "output_display"):
            return
        self.output_display.configure(state="normal")
        self.output_display.delete("1.0", "end")
        self.output_display.insert("1.0", self.vars["output_dir"].get())
        self.output_display.configure(state="disabled")

    def _browse_output(self) -> None:
        before = self.vars.get("output_dir").get() if self.vars.get("output_dir") else ""
        super()._browse_output()
        after = self.vars.get("output_dir").get() if self.vars.get("output_dir") else ""
        if after != before:
            self._refresh_output_display()

    def _confirm(self) -> None:
        if not self._validate_date("period_start", show_message=True):
            return
        if not self._validate_date("period_end", show_message=True):
            return

        values = {key: var.get().strip() for key, var in self.vars.items()}
        missing = [key for key in _REQUIRED if not values.get(key)]
        if missing:
            labels = dict(_FIELDS)
            readable = ", ".join(labels.get(key, key) for key in missing)
            messagebox.showwarning(
                "DIAS-pakking",
                f"Fyll ut alle obligatoriske felt før operasjonen legges til.\n\nMangler: {readable}",
                parent=self,
            )
            return

        start = datetime.datetime.strptime(values["period_start"], "%Y-%m-%d").date()
        end = datetime.datetime.strptime(values["period_end"], "%Y-%m-%d").date()
        if end < start:
            messagebox.showwarning(
                "DIAS-pakking",
                "Periodens slutt kan ikke være før periodens start.",
                parent=self,
            )
            return

        if values.get("output_dir"):
            self._remember_dir("last_dias_output_dir", values["output_dir"])
        values["extra_files"] = json.dumps(self.extra_files, ensure_ascii=False)

        accepted = self.on_confirm(values)
        if accepted is False:
            # Konflikt eller annen jobbvalidering: behold alle innskrevne data og
            # la brukeren rette target/metadata direkte i samme dialog.
            return

        self.destroy()
