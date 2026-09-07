from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk

from noark5_workflow.core.job import Job
from settings import load_config, save_config
from . import theme

_FIELDS = (
    ("source_root", "Source – hovedmappe", "dir"),
    ("source_tar", "Source – TAR", "file"),
    ("source_unzipped", "Source – utpakket", "dir"),
    ("source_extraction", "Source – uttrekksmappe", "dir"),
    ("work_root", "Arbeid – hovedmappe", "dir"),
    ("work_content", "Arbeid – content", "dir"),
    ("work_operations", "Arbeid – operasjoner", "dir"),
    ("archive_root", "Arkiv – hovedmappe", "dir"),
)


class StorageRolesDialog(ctk.CTkToplevel):
    """Edit generic storage roles; each role remembers its own recent locations."""

    def __init__(self, master, job: Job, on_save, *, blank_fallback_source_root: bool = False) -> None:
        super().__init__(master)
        self.job = job
        self.on_save = on_save
        self.vars = {}
        self.settings = load_config()
        self.title(f"Mapper – {job.job_id}")
        self.geometry("1380x620")
        self.minsize(1120, 520)
        self.configure(fg_color=theme.APP_BG)
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(
            self, text="MAPPE-ROLLER",
            font=theme.font(theme.TITLE_SIZE, "bold"),
            text_color=theme.BLUE,
        ).grid(row=0, column=0, columnspan=3, padx=18, pady=(16, 4), sticky="w")
        ctk.CTkLabel(
            self,
            text=(
                "Roller per jobb. Ingen fysisk DIAS- eller depotstruktur tvinges av feltene. "
                "Hver rolle husker sine egne sist brukte steder."
            ),
            font=theme.font(theme.SMALL_SIZE),
            text_color=theme.TEXT_MUTED,
        ).grid(row=1, column=0, columnspan=3, padx=18, pady=(0, 12), sticky="w")

        for row, (attr, label, kind) in enumerate(_FIELDS, start=2):
            ctk.CTkLabel(
                self, text=label, width=210,
                font=theme.font(theme.SMALL_SIZE), anchor="w",
            ).grid(row=row, column=0, padx=(18, 8), pady=5, sticky="w")

            value = getattr(job, attr)
            if (
                blank_fallback_source_root
                and attr == "source_root"
                and job.source_extraction is not None
                and value == job.source_extraction
            ):
                value = None
            var = ctk.StringVar(value=str(value) if value else "")
            self.vars[attr] = var
            ctk.CTkEntry(
                self, textvariable=var, font=theme.font(theme.SMALL_SIZE)
            ).grid(row=row, column=1, padx=4, pady=5, sticky="ew")
            ctk.CTkButton(
                self, text="Velg...", width=76,
                fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER,
                command=lambda a=attr, k=kind: self._choose(a, k),
            ).grid(row=row, column=2, padx=(8, 18), pady=5)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=20, column=0, columnspan=3, padx=18, pady=18, sticky="e")
        ctk.CTkButton(
            buttons, text="Avbryt", width=90,
            fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER,
            command=self.destroy,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            buttons, text="Lagre", width=90,
            fg_color=theme.BLUE_DIM, hover_color=theme.BLUE,
            command=self._save,
        ).pack(side="left", padx=4)

    def _role_history(self, attr: str) -> list[Path]:
        raw = self.settings.get("recent_storage_role_paths", {})
        values = raw.get(attr, []) if isinstance(raw, dict) else []
        result = []
        for value in values if isinstance(values, list) else []:
            path = Path(str(value))
            if path.exists() and path not in result:
                result.append(path)
        return result[:10]

    def _remember_role(self, attr: str, value: Path) -> None:
        raw = self.settings.get("recent_storage_role_paths", {})
        history = dict(raw) if isinstance(raw, dict) else {}
        current = [str(item) for item in history.get(attr, []) if str(item)]
        text = str(value)
        current = [item for item in current if item != text]
        current.insert(0, text)
        history[attr] = current[:10]
        self.settings["recent_storage_role_paths"] = history
        save_config({"recent_storage_role_paths": history})

    def _initial_for_role(self, attr: str, kind: str) -> str | None:
        current = self.vars[attr].get().strip()
        if current:
            path = Path(current)
            if kind == "file":
                return str(path.parent if not path.is_dir() else path)
            return str(path if path.is_dir() else path.parent)
        history = self._role_history(attr)
        if history:
            path = history[0]
            return str(path.parent if kind == "file" and path.is_file() else path)
        return None

    def _choose(self, attr: str, kind: str) -> None:
        initial = self._initial_for_role(attr, kind)
        if kind == "file":
            kwargs = {
                "parent": self,
                "title": f"Velg {dict((a, l) for a, l, _ in _FIELDS)[attr]}",
                "filetypes": [("TAR", "*.tar"), ("Alle filer", "*.*")],
            }
            if initial:
                kwargs["initialdir"] = initial
            value = filedialog.askopenfilename(**kwargs)
        else:
            kwargs = {
                "parent": self,
                "title": f"Velg {dict((a, l) for a, l, _ in _FIELDS)[attr]}",
            }
            if initial:
                kwargs["initialdir"] = initial
            value = filedialog.askdirectory(**kwargs)

        if value:
            path = Path(value)
            self.vars[attr].set(str(path))
            self._remember_role(attr, path)

    def _save(self) -> None:
        values = {
            name: (Path(text) if (text := var.get().strip()) else None)
            for name, var in self.vars.items()
        }
        # Do not invent Source – hovedmappe from Source – uttrekksmappe.
        # source_root remains the explicit existing value when left blank.
        if values["source_root"] is None:
            values["source_root"] = self.job.source_root
        self.on_save(values)
        self.destroy()
