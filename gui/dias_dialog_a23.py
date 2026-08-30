from __future__ import annotations

import customtkinter as ctk

from .dias_dialog import DiasParamDialog as BaseDiasParamDialog, _FIELDS
from . import theme


class DiasParamDialog(BaseDiasParamDialog):
    """a2.3: gjør valg av utdatamappe synlig øverst i metadataformen."""

    def _build_form(self, parent: ctk.CTkFrame) -> None:
        form = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        form.grid(row=1, column=0, padx=10, pady=(2, 10), sticky="nsew")
        form.grid_columnconfigure(0, weight=0)
        form.grid_columnconfigure(1, weight=1)

        # Target først: dette er et sentralt jobbvalg og skal være synlig uten scrolling.
        ctk.CTkLabel(
            form,
            text="Utdatamappe",
            font=theme.font(theme.SMALL_SIZE, "bold"),
            text_color=theme.BLUE,
        ).grid(row=0, column=0, padx=(10, 8), pady=(6, 10), sticky="w")
        out_row = ctk.CTkFrame(form, fg_color="transparent")
        out_row.grid(row=0, column=1, padx=(0, 12), pady=(6, 10), sticky="ew")
        out_row.grid_columnconfigure(0, weight=1)
        self.vars["output_dir"] = ctk.StringVar(value=str(self.values.get("output_dir", "")))
        ctk.CTkEntry(
            out_row,
            textvariable=self.vars["output_dir"],
            font=theme.font(theme.SMALL_SIZE),
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            out_row,
            text="Velg…",
            width=72,
            command=self._browse_output,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            font=theme.font(theme.SMALL_SIZE),
        ).grid(row=0, column=1, padx=(6, 0))

        mets_row = ctk.CTkFrame(form, fg_color="transparent")
        mets_row.grid(row=1, column=0, columnspan=2, padx=6, pady=(2, 8), sticky="w")
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

        for row, (key, label) in enumerate(_FIELDS, start=2):
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
