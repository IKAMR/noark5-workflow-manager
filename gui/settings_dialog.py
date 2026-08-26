from __future__ import annotations

import customtkinter as ctk

from . import theme


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, settings: dict, on_save):
        super().__init__(master)
        self.title("Globale innstillinger")
        self.geometry("820x620")
        self.minsize(700, 520)
        self.transient(master)
        self.grab_set()
        self.settings = dict(settings)
        self.on_save = on_save

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Globale innstillinger", font=theme.font(theme.TITLE_SIZE, "bold"), text_color=theme.BLUE).grid(
            row=0, column=0, padx=24, pady=(20, 10), sticky="w"
        )

        body = ctk.CTkScrollableFrame(self, fg_color=theme.PANEL_BG)
        body.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        body.grid_columnconfigure(1, weight=1)

        self.temp_var = ctk.StringVar(value=self.settings.get("temp_dir", ""))
        self.backend_var = ctk.StringVar(value=self.settings.get("execution_backend", "local"))
        self.endpoint_var = ctk.StringVar(value=self.settings.get("remote_endpoint", ""))
        self.storage_var = ctk.StringVar(value=self.settings.get("shared_storage_root", ""))
        self.visibility_var = ctk.StringVar(value=str(self.settings.get("operation_visibility", 2)))

        row = 0
        ctk.CTkLabel(body, text="Generelt", font=theme.font(theme.SECTION_SIZE, "bold"), text_color=theme.BLUE).grid(row=row, column=0, columnspan=2, padx=12, pady=(12, 8), sticky="w")
        row += 1
        ctk.CTkLabel(body, text="Temp-mappe", font=theme.font(theme.NORMAL_SIZE)).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        ctk.CTkEntry(body, textvariable=self.temp_var, font=theme.font(theme.NORMAL_SIZE)).grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        row += 1
        ctk.CTkLabel(body, text="Kjøring", font=theme.font(theme.SECTION_SIZE, "bold"), text_color=theme.BLUE).grid(row=row, column=0, columnspan=2, padx=12, pady=(20, 8), sticky="w")
        row += 1
        ctk.CTkLabel(body, text="Execution backend", font=theme.font(theme.NORMAL_SIZE)).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        ctk.CTkOptionMenu(body, variable=self.backend_var, values=["local", "server"], command=self._backend_changed, font=theme.font(theme.NORMAL_SIZE)).grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        row += 1
        ctk.CTkLabel(body, text="Server-endepunkt", font=theme.font(theme.NORMAL_SIZE)).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.endpoint_entry = ctk.CTkEntry(body, textvariable=self.endpoint_var, font=theme.font(theme.NORMAL_SIZE))
        self.endpoint_entry.grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        row += 1
        ctk.CTkLabel(body, text="Delt lagringsrot", font=theme.font(theme.NORMAL_SIZE)).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.storage_entry = ctk.CTkEntry(body, textvariable=self.storage_var, font=theme.font(theme.NORMAL_SIZE))
        self.storage_entry.grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        row += 1
        ctk.CTkLabel(body, text="Operasjoner-synlighet", font=theme.font(theme.SECTION_SIZE, "bold"), text_color=theme.BLUE).grid(row=row, column=0, columnspan=2, padx=12, pady=(20, 8), sticky="w")
        row += 1
        ctk.CTkLabel(body, text="Vis operasjoner med status over", font=theme.font(theme.NORMAL_SIZE)).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        ctk.CTkOptionMenu(body, variable=self.visibility_var, values=["0", "1", "2"], font=theme.font(theme.NORMAL_SIZE)).grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        row += 1
        ctk.CTkLabel(body, text="0 = alle | 1 = beta + ok | 2 = kun ok/stabil", font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_MUTED).grid(row=row, column=0, columnspan=2, padx=12, pady=(0, 16), sticky="w")

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=2, column=0, padx=20, pady=(4, 18), sticky="e")
        ctk.CTkButton(buttons, text="Avbryt", command=self.destroy, width=110, font=theme.font(theme.NORMAL_SIZE)).grid(row=0, column=0, padx=5)
        ctk.CTkButton(buttons, text="Lagre", command=self._save, width=130, font=theme.font(theme.NORMAL_SIZE)).grid(row=0, column=1, padx=5)
        self._backend_changed(self.backend_var.get())

    def _backend_changed(self, value: str) -> None:
        state = "normal" if value == "server" else "disabled"
        self.endpoint_entry.configure(state=state)
        self.storage_entry.configure(state=state)

    def _save(self) -> None:
        # Server is exposed as a future setting, but the a2 executor remains local.
        backend = self.backend_var.get()
        if backend == "server":
            backend = "local"
        self.settings.update(
            {
                "temp_dir": self.temp_var.get().strip(),
                "execution_backend": backend,
                "remote_endpoint": self.endpoint_var.get().strip(),
                "shared_storage_root": self.storage_var.get().strip(),
                "operation_visibility": int(self.visibility_var.get()),
            }
        )
        self.on_save(self.settings)
        self.destroy()
