from __future__ import annotations

import json
import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from noark5_workflow.app import build_registry
from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.workflow import Workflow
from noark5_workflow.executors.local import LocalExecutor
from noark5_workflow.sources.noark5_extraction import Noark5Extraction
from version import APP_NAME, VERSION

from . import theme
from .log_panel import LogPanel
from .operations_panel import OperationsPanel
from .settings_dialog import SettingsDialog
from .source_panel import SourcePanel
from .status_bar import StatusBar
from .workflow_panel import WorkflowPanel


class WorkflowApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("1580x900")
        self.minsize(1200, 720)
        self.configure(fg_color=theme.APP_BG)

        self.registry = build_registry()
        self.workflow = Workflow()
        self.executor = LocalExecutor()
        self.extraction: Noark5Extraction | None = None
        self.cancel_requested = False
        self.settings = {
            "execution_backend": "local",
            "remote_endpoint": "",
            "shared_storage_root": "",
            "temp_dir": "",
            "log_level": "INFO",
            "operation_visibility": 2,
        }

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()

        left = ctk.CTkFrame(self, fg_color=theme.APP_BG, width=320, corner_radius=0)
        left.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="nsew")
        left.grid_propagate(False)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        self.source_panel = SourcePanel(left, self._source_changed)
        self.source_panel.grid(row=0, column=0, padx=0, pady=(0, 8), sticky="nsew")

        self.workflow_panel = WorkflowPanel(left, self.registry, self.workflow, self._run_workflow)
        self.workflow_panel.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")

        right = ctk.CTkFrame(self, fg_color=theme.APP_BG, corner_radius=0)
        right.grid(row=1, column=1, padx=(5, 10), pady=5, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self.operations_panel = OperationsPanel(right, self.registry, self._add_operation)
        self.operations_panel.grid(row=0, column=0, padx=0, pady=(0, 8), sticky="ew")

        self.log_panel = LogPanel(right)
        self.log_panel.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")

        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=theme.PANEL_BG_DARK, height=54, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(header, text=APP_NAME.upper(), font=theme.TITLE_FONT, text_color=theme.BLUE).grid(
            row=0, column=0, padx=(16, 20), pady=14, sticky="w"
        )
        ctk.CTkOptionMenu(header, values=["-- profil --"], width=130, font=theme.SMALL_FONT).grid(
            row=0, column=1, padx=6, pady=10
        )
        ctk.CTkLabel(header, text=f"v{VERSION}", font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED).grid(
            row=0, column=2, padx=8, pady=10, sticky="w"
        )
        ctk.CTkButton(header, text="Innstillinger", width=110, height=28, font=theme.SMALL_FONT, command=self._open_settings).grid(
            row=0, column=3, padx=8, pady=10
        )
        ctk.CTkButton(header, text="A-", width=36, height=28, state="disabled").grid(row=0, column=4, padx=2, pady=10)
        ctk.CTkButton(header, text="A+", width=36, height=28, state="disabled").grid(row=0, column=5, padx=2, pady=10)
        ctk.CTkButton(header, text="?", width=36, height=28, state="disabled").grid(row=0, column=6, padx=(2, 12), pady=10)

    def _source_changed(self, extraction: Noark5Extraction | None) -> None:
        self.extraction = extraction
        if extraction:
            self.status_bar.update_storage(extraction.root)
            if extraction.is_noark5_candidate:
                self.status_bar.set_status("Noark 5-uttrekk funnet")
                self.log_panel.append(f"Uttrekk valgt: {extraction.root}")
            else:
                self.status_bar.set_status("arkivstruktur.xml ble ikke funnet")
        else:
            self.status_bar.set_status("Klar")

    def _add_operation(self, operation_id: str) -> None:
        if self.workflow_panel.add(operation_id):
            operation = self.registry.get(operation_id)
            self.log_panel.append(f"Lagt til i workflow: {operation.definition.name}")
        else:
            self.status_bar.set_status("Operasjonen finnes allerede i workflow")

    def _progress_callback(self, value: float, message: str) -> None:
        self.after(0, lambda: self.status_bar.set_status(message or f"Kjører {value:.0%}"))

    def _run_workflow(self) -> None:
        op_ids = self.workflow.operation_ids()
        if not op_ids:
            messagebox.showwarning(APP_NAME, "Legg til minst én operasjon i workflow først.")
            return
        root = self.source_panel.path_var.get().strip()
        if not root:
            messagebox.showwarning(APP_NAME, "Velg en uttrekksmappe først.")
            return

        self.workflow_panel.run_button.configure(state="disabled")
        self.cancel_requested = False

        def worker() -> None:
            try:
                source = self.extraction or Noark5Extraction.detect(root)
                ctx = OperationContext(
                    extraction_root=Path(root),
                    source=source,
                    settings=self.settings,
                    progress_cb=self._progress_callback,
                    log_cb=lambda msg: self.after(0, lambda m=msg: self.log_panel.append(m)),
                    cancelled_cb=lambda: self.cancel_requested,
                )
                total = len(op_ids)
                all_ok = True
                for index, op_id in enumerate(op_ids, start=1):
                    operation = self.registry.get(op_id)
                    self.after(0, lambda n=operation.definition.name: self.log_panel.append(f"START: {n}"))
                    result = self.executor.execute(operation, ctx)
                    all_ok = all_ok and result.ok
                    self.after(0, lambda r=result: self._log_result(r))
                    self.after(0, lambda n=operation.definition.name, ok=result.ok: self.log_panel.append(f"{'OK' if ok else 'FEIL'}: {n}"))
                    self.after(0, lambda i=index, t=total: self.status_bar.set_status(f"Workflow {i}/{t}"))
                    if not result.ok:
                        break
                if isinstance(ctx.source, Noark5Extraction):
                    self.extraction = ctx.source
                final = "Workflow fullført" if all_ok else "Workflow stoppet med feil"
                self.after(0, lambda: self.status_bar.set_status(final))
            except Exception as exc:
                self.after(0, lambda: self.log_panel.append(f"FEIL: {exc}"))
                self.after(0, lambda: self.status_bar.set_status("Feil"))
            finally:
                self.after(0, lambda: self.workflow_panel.run_button.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _log_result(self, result) -> None:
        self.log_panel.append(result.message)
        for warning in result.warnings:
            self.log_panel.append(f"ADVARSEL: {warning}")
        if result.data:
            self.log_panel.append(json.dumps(result.data, ensure_ascii=False, indent=2), timestamp=False)

    def _open_settings(self) -> None:
        SettingsDialog(self, self.settings, self._save_settings)

    def _save_settings(self, settings: dict) -> None:
        self.settings = dict(settings)
        self.status_bar.set_status("Innstillinger oppdatert")


def run_gui() -> None:
    theme.apply_theme()
    app = WorkflowApp()
    app.mainloop()
