from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.settings_portable import export_settings, import_settings, reset_settings
from . import theme


class SettingsDialog(ctk.CTkToplevel):
    """Globale innstillinger med portabel JSON eksport/import og full reset."""

    def __init__(self, master, settings: dict, on_save):
        super().__init__(master)
        self.title("Globale innstillinger")
        self.geometry("860x660")
        self.minsize(720, 540)
        self.transient(master)
        self.grab_set()
        self.settings = dict(settings)
        self.on_save = on_save

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            self,
            text="Globale innstillinger",
            font=theme.font(theme.TITLE_SIZE, "bold"),
            text_color=theme.BLUE,
        ).grid(row=0, column=0, padx=24, pady=(20, 10), sticky="w")

        body = ctk.CTkScrollableFrame(self, fg_color=theme.PANEL_BG)
        body.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        body.grid_columnconfigure(1, weight=1)

        self.temp_var = ctk.StringVar()
        self.backend_var = ctk.StringVar()
        self.endpoint_var = ctk.StringVar()
        self.storage_var = ctk.StringVar()
        self.visibility_var = ctk.StringVar()
        self._load_vars(self.settings)

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

        tools = ctk.CTkFrame(self, fg_color="transparent")
        tools.grid(row=2, column=0, padx=20, pady=(2, 6), sticky="ew")
        ctk.CTkButton(tools, text="Eksporter setup…", command=self._export, width=130, fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER).pack(side="left", padx=(0, 6))
        ctk.CTkButton(tools, text="Importer setup…", command=self._import, width=130, fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER).pack(side="left", padx=6)
        ctk.CTkButton(tools, text="Nullstill setup", command=self._reset, width=120, fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER).pack(side="left", padx=6)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=3, column=0, padx=20, pady=(4, 18), sticky="e")
        ctk.CTkButton(buttons, text="Avbryt", command=self.destroy, width=110, font=theme.font(theme.NORMAL_SIZE), fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER).grid(row=0, column=0, padx=5)
        ctk.CTkButton(buttons, text="Lagre", command=self._save, width=130, font=theme.font(theme.NORMAL_SIZE)).grid(row=0, column=1, padx=5)
        self._backend_changed(self.backend_var.get())

    def _load_vars(self, settings: dict) -> None:
        self.temp_var.set(str(settings.get("temp_dir", "")))
        self.backend_var.set(str(settings.get("execution_backend", "local")))
        self.endpoint_var.set(str(settings.get("remote_endpoint", "")))
        self.storage_var.set(str(settings.get("shared_storage_root", "")))
        self.visibility_var.set(str(settings.get("operation_visibility", 2)))

    def _backend_changed(self, value: str) -> None:
        state = "normal" if value == "server" else "disabled"
        if hasattr(self, "endpoint_entry"):
            self.endpoint_entry.configure(state=state)
            self.storage_entry.configure(state=state)

    def _collect(self) -> dict:
        updated = dict(self.settings)
        backend = self.backend_var.get()
        if backend == "server":
            backend = "local"
        updated.update({
            "temp_dir": self.temp_var.get().strip(),
            "execution_backend": backend,
            "remote_endpoint": self.endpoint_var.get().strip(),
            "shared_storage_root": self.storage_var.get().strip(),
            "operation_visibility": int(self.visibility_var.get()),
        })
        return updated

    def _save(self) -> None:
        self.settings = self._collect()
        self.on_save(self.settings)
        self.destroy()

    def _export(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Eksporter applikasjonsoppsett",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not filename:
            return
        # Save visible edits before creating the portable export.
        self.on_save(self._collect())
        path = export_settings(Path(filename))
        messagebox.showinfo("Noark 5 Workflow Manager", f"Setup eksportert til:\n{path}")

    def _import(self) -> None:
        filename = filedialog.askopenfilename(
            title="Importer applikasjonsoppsett",
            filetypes=[("JSON", "*.json"), ("Alle filer", "*.*")],
        )
        if not filename:
            return
        try:
            imported = import_settings(Path(filename))
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror("Noark 5 Workflow Manager", f"Kunne ikke importere setup:\n{exc}")
            return
        self.settings = imported
        self._load_vars(imported)
        self._backend_changed(self.backend_var.get())
        self.on_save(imported)
        messagebox.showinfo("Noark 5 Workflow Manager", "Setup importert.")

    def _reset(self) -> None:
        if not messagebox.askyesno(
            "Noark 5 Workflow Manager",
            "Nullstille alle applikasjonsinnstillinger til standardverdier?\n\n"
            "Dette inkluderer sist brukte mapper og jobbliste-referanser.",
        ):
            return
        defaults = reset_settings()
        self.settings = defaults
        self._load_vars(defaults)
        self._backend_changed(self.backend_var.get())
        self.on_save(defaults)
        messagebox.showinfo("Noark 5 Workflow Manager", "Setup er nullstilt til standardverdier.")
