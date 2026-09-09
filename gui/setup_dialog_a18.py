from __future__ import annotations

import customtkinter as ctk

from . import theme
from .setup_dialog_a17 import SetupDialog as A17SetupDialog

PREMIS_AGENT_LABELS = {
    "username": "Brukernavn",
    "user_id": "Intern user_id",
}
PREMIS_AGENT_VALUES = {label: value for value, label in PREMIS_AGENT_LABELS.items()}
TEXT_RUN_LOG_SINK = "text_run_log"
PREMIS_SINK = "premis"
JSON_SINK = "json"
CSV_SINK = "csv"


class SetupDialog(A17SetupDialog):
    """a18 adds local user access and selectable PREMIS provenance settings."""

    def __init__(self, master, settings: dict, on_save, on_user_profile):
        self._on_user_profile = on_user_profile
        super().__init__(master, settings, on_save)
        configured_sinks = self.settings.get("enabled_log_sinks")
        if not isinstance(configured_sinks, (list, tuple)):
            configured_sinks = [TEXT_RUN_LOG_SINK]
            if bool(self.settings.get("enable_premis_provenance", True)):
                configured_sinks.append(PREMIS_SINK)
        self.text_log_enabled_var = ctk.BooleanVar(
            value=TEXT_RUN_LOG_SINK in configured_sinks
        )
        self.premis_enabled_var = ctk.BooleanVar(
            value=(PREMIS_SINK in configured_sinks and bool(self.settings.get("enable_premis_provenance", True)))
        )
        self.json_enabled_var = ctk.BooleanVar(value=JSON_SINK in configured_sinks)
        self.csv_enabled_var = ctk.BooleanVar(value=CSV_SINK in configured_sinks)
        strategy = str(self.settings.get("premis_agent_identifier", "username"))
        self.premis_agent_var = ctk.StringVar(
            value=PREMIS_AGENT_LABELS.get(strategy, PREMIS_AGENT_LABELS["username"])
        )
        self._add_provenance_settings()
        self._add_user_profile_button()

    def _body(self):
        # CustomTkinter may wrap the scrollable frame in internal widgets.
        # a17 already provides a recursive walker; use that instead of assuming
        # the body is a direct child of the toplevel.
        for child in self._walk_widgets(self):
            if isinstance(child, ctk.CTkScrollableFrame):
                return child
        return None

    def _add_provenance_settings(self) -> None:
        body = self._body()
        if body is None:
            return
        row = int(body.grid_size()[1])
        ctk.CTkLabel(
            body,
            text="Proveniens og loggformat",
            font=theme.font(theme.SECTION_SIZE, "bold"),
            text_color=theme.BLUE,
        ).grid(row=row, column=0, columnspan=2, padx=12, pady=(20, 8), sticky="w")

        row += 1
        ctk.CTkLabel(
            body, text="Tekstlig kjørelogg", font=theme.font(theme.NORMAL_SIZE)
        ).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        ctk.CTkSwitch(
            body,
            text="Aktivert",
            variable=self.text_log_enabled_var,
            onvalue=True,
            offvalue=False,
            font=theme.font(theme.NORMAL_SIZE),
        ).grid(row=row, column=1, padx=12, pady=8, sticky="w")

        row += 1
        ctk.CTkLabel(
            body, text="JSON-logg", font=theme.font(theme.NORMAL_SIZE)
        ).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        ctk.CTkSwitch(
            body,
            text="Aktivert",
            variable=self.json_enabled_var,
            onvalue=True,
            offvalue=False,
            font=theme.font(theme.NORMAL_SIZE),
        ).grid(row=row, column=1, padx=12, pady=8, sticky="w")

        row += 1
        ctk.CTkLabel(
            body, text="CSV-logg", font=theme.font(theme.NORMAL_SIZE)
        ).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        ctk.CTkSwitch(
            body,
            text="Aktivert",
            variable=self.csv_enabled_var,
            onvalue=True,
            offvalue=False,
            font=theme.font(theme.NORMAL_SIZE),
        ).grid(row=row, column=1, padx=12, pady=8, sticky="w")

        row += 1
        ctk.CTkLabel(
            body, text="PREMIS-proveniens", font=theme.font(theme.NORMAL_SIZE)
        ).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        ctk.CTkSwitch(
            body,
            text="Aktivert",
            variable=self.premis_enabled_var,
            onvalue=True,
            offvalue=False,
            font=theme.font(theme.NORMAL_SIZE),
        ).grid(row=row, column=1, padx=12, pady=8, sticky="w")

        row += 1
        ctk.CTkLabel(
            body, text="PREMIS agent-identifikator", font=theme.font(theme.NORMAL_SIZE)
        ).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        ctk.CTkOptionMenu(
            body,
            variable=self.premis_agent_var,
            values=list(PREMIS_AGENT_VALUES),
            font=theme.font(theme.NORMAL_SIZE),
        ).grid(row=row, column=1, padx=12, pady=8, sticky="ew")

        row += 1
        ctk.CTkLabel(
            body,
            text=(
                "Standard er Brukernavn. Intern user_id kan velges når en stabil teknisk "
                "identifikator er ønsket. Tekst, PREMIS, JSON og CSV er valgbare "
                "formatteringer over den samme generiske eventloggen."
            ),
            font=theme.font(theme.SMALL_SIZE),
            text_color=theme.TEXT_MUTED,
            wraplength=610,
            justify="left",
        ).grid(row=row, column=0, columnspan=2, padx=12, pady=(0, 16), sticky="w")

    def _collect(self) -> dict:
        updated = super()._collect()
        premis_enabled = bool(self.premis_enabled_var.get())
        sinks = []
        if bool(self.text_log_enabled_var.get()):
            sinks.append(TEXT_RUN_LOG_SINK)
        if bool(self.json_enabled_var.get()):
            sinks.append(JSON_SINK)
        if bool(self.csv_enabled_var.get()):
            sinks.append(CSV_SINK)
        if premis_enabled:
            sinks.append(PREMIS_SINK)
        updated["enabled_log_sinks"] = sinks
        updated["enable_premis_provenance"] = premis_enabled
        updated["premis_agent_identifier"] = PREMIS_AGENT_VALUES.get(
            self.premis_agent_var.get(), "username"
        )
        return updated

    def _load_vars(self, settings: dict) -> None:
        super()._load_vars(settings)
        configured_sinks = settings.get("enabled_log_sinks")
        if not isinstance(configured_sinks, (list, tuple)):
            configured_sinks = [TEXT_RUN_LOG_SINK]
            if bool(settings.get("enable_premis_provenance", True)):
                configured_sinks.append(PREMIS_SINK)
        if hasattr(self, "text_log_enabled_var"):
            self.text_log_enabled_var.set(TEXT_RUN_LOG_SINK in configured_sinks)
        if hasattr(self, "json_enabled_var"):
            self.json_enabled_var.set(JSON_SINK in configured_sinks)
        if hasattr(self, "csv_enabled_var"):
            self.csv_enabled_var.set(CSV_SINK in configured_sinks)
        if hasattr(self, "premis_enabled_var"):
            self.premis_enabled_var.set(
                PREMIS_SINK in configured_sinks and bool(settings.get("enable_premis_provenance", True))
            )
        if hasattr(self, "premis_agent_var"):
            strategy = str(settings.get("premis_agent_identifier", "username"))
            self.premis_agent_var.set(PREMIS_AGENT_LABELS.get(strategy, "Brukernavn"))

    def _add_user_profile_button(self) -> None:
        for child in self._walk_widgets(self):
            if not isinstance(child, ctk.CTkButton):
                continue
            try:
                if str(child.cget("text")) != "Eksporter setup…":
                    continue
            except Exception:
                continue
            tools = child.master
            ctk.CTkButton(
                tools, text="Brukerprofil…", command=self._on_user_profile, width=130,
                fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER,
            ).pack(side="left", padx=6)
            return
