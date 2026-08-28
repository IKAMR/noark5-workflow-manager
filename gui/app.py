from __future__ import annotations

import json
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from noark5_workflow.app import build_registry
from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.job import Job, JobBatch, JobStatus
from noark5_workflow.core.workflow import Workflow
from noark5_workflow.executors.local import LocalExecutor
from noark5_workflow.sources.noark5_extraction import Noark5Extraction
from version import APP_NAME, VERSION
from settings import load_config, save_config
from . import theme
from .dias_dialog import DiasParamDialog
from .jobs_window import JobsWindow
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
        self.geometry("1500x900")
        self.minsize(1180, 720)
        self.configure(fg_color=theme.APP_BG)

        self.registry = build_registry()
        self.workflow = Workflow()
        self.jobs = JobBatch()
        self.current_job: Job | None = None
        self.jobs_window: JobsWindow | None = None
        self.executor = LocalExecutor()
        self.extraction: Noark5Extraction | None = None
        self.cancel_requested = False
        self.settings = load_config()
        theme.FontRegistry.set_offset(int(self.settings.get("font_offset", 0)))

        self._build_ui()
        self.status_bar.set_temp(self.settings.get("temp_dir") or None)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()

        left = ctk.CTkFrame(self, fg_color=theme.APP_BG, width=theme.LEFT_WIDTH, corner_radius=0)
        left.grid(row=1, column=0, padx=(10, 5), pady=4, sticky="nsew")
        left.grid_propagate(False)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        self.source_panel = SourcePanel(left, self._source_changed)
        self.source_panel.grid(row=0, column=0, padx=0, pady=(0, 8), sticky="nsew")

        self.workflow_panel = WorkflowPanel(left, self.registry, self.workflow, self._run_workflow)
        self.workflow_panel.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")

        right = ctk.CTkFrame(self, fg_color=theme.APP_BG, corner_radius=0)
        right.grid(row=1, column=1, padx=(5, 10), pady=4, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self.operations_panel = OperationsPanel(right, self.registry, self._add_operation)
        self.operations_panel.grid(row=0, column=0, padx=0, pady=(0, 8), sticky="ew")

        self.log_panel = LogPanel(right)
        self.log_panel.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")

        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=theme.APP_BG, height=theme.HEADER_HEIGHT, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            header,
            text=APP_NAME.upper(),
            font=theme.font(theme.TITLE_SIZE, "bold"),
            text_color=theme.BLUE,
        ).grid(row=0, column=0, padx=(16, 18), pady=10, sticky="w")

        ctk.CTkOptionMenu(
            header,
            values=["-- profil --"],
            width=135,
            height=28,
            font=theme.font(theme.SMALL_SIZE),
        ).grid(row=0, column=1, padx=6, pady=8)

        ctk.CTkLabel(
            header,
            text=f"v{VERSION}",
            font=theme.font(theme.SMALL_SIZE),
            text_color=theme.TEXT_MUTED,
        ).grid(row=0, column=2, padx=8, pady=8, sticky="w")

        self.active_job_label = ctk.CTkLabel(
            header,
            text="AKTIV JOBB: ingen",
            font=theme.font(theme.SMALL_SIZE, "bold"),
            text_color=theme.TEXT_SUB,
            anchor="w",
        )
        self.active_job_label.grid(row=0, column=3, padx=12, pady=8, sticky="ew")

        ctk.CTkButton(
            header,
            text="Jobber",
            width=78,
            height=28,
            font=theme.font(theme.SMALL_SIZE),
            fg_color=theme.BLUE_DIM,
            hover_color=theme.BLUE,
            command=self._open_jobs,
        ).grid(row=0, column=4, padx=(6, 4), pady=8)

        ctk.CTkButton(
            header,
            text="Endre temp-mappe",
            width=110,
            height=28,
            font=theme.font(theme.SMALL_SIZE),
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            command=self._change_temp_dir,
        ).grid(row=0, column=5, padx=(6, 4), pady=8)

        ctk.CTkButton(
            header,
            text="Innstillinger",
            width=100,
            height=28,
            font=theme.font(theme.SMALL_SIZE),
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            command=self._open_settings,
        ).grid(row=0, column=6, padx=4, pady=8)

        ctk.CTkButton(
            header, text="A-", width=34, height=28,
            font=theme.font(theme.SMALL_SIZE),
            fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER,
            command=lambda: self._font_scale(-1),
        ).grid(row=0, column=7, padx=2, pady=8)
        ctk.CTkButton(
            header, text="A+", width=34, height=28,
            font=theme.font(theme.SMALL_SIZE),
            fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER,
            command=lambda: self._font_scale(+1),
        ).grid(row=0, column=8, padx=2, pady=8)
        ctk.CTkButton(
            header, text="?", width=34, height=28, state="disabled",
            font=theme.font(theme.SMALL_SIZE), fg_color=theme.BUTTON_BG,
        ).grid(row=0, column=9, padx=(2, 10), pady=8)

    def _open_jobs(self) -> None:
        if self.current_job:
            self.current_job.set_workflow(self.workflow.operation_ids())
        if self.jobs_window is not None and self.jobs_window.winfo_exists():
            self.jobs_window.focus()
            self.jobs_window.refresh()
            return
        self.jobs_window = JobsWindow(self, self.jobs, self._open_job, self._create_job)

    def _create_job(self, source_root: Path) -> Job:
        # A new job starts with an empty workflow. Reuse/copy of another job's
        # workflow must be an explicit user action in a later version.
        return self.jobs.new_job(source_root)

    def _refresh_active_job_label(self) -> None:
        if not self.current_job:
            self.active_job_label.configure(text="AKTIV JOBB: ingen", text_color=theme.TEXT_SUB)
            return
        count = len(self.workflow.operation_ids())
        if count == 0:
            suffix = "Workflow: 0 operasjoner - legg til operasjoner"
        elif count == 1:
            suffix = "Workflow: 1 operasjon"
        else:
            suffix = f"Workflow: {count} operasjoner"
        self.active_job_label.configure(
            text=f"AKTIV JOBB: {self.current_job.job_id} | {self.current_job.name} | {suffix}",
            text_color=theme.BLUE,
        )

    def _ensure_job_for_current_source(self) -> Job | None:
        root = self.source_panel.path_var.get().strip()
        if not root:
            return None
        path = Path(root)
        if self.current_job and self.current_job.source_root == path:
            return self.current_job
        existing = next((job for job in self.jobs.jobs() if job.source_root == path), None)
        if existing:
            self.current_job = existing
            self._refresh_active_job_label()
            return existing
        self.current_job = self.jobs.new_job(path, workflow_ids=self.workflow.operation_ids())
        self._refresh_active_job_label()
        return self.current_job

    def _open_job(self, job: Job) -> None:
        if self.current_job:
            self.current_job.set_workflow(self.workflow.operation_ids())
        self.current_job = job
        self.workflow.clear()
        for operation_id in job.workflow_ids:
            self.workflow.add(operation_id)
        self.workflow_panel.refresh()
        self.source_panel.set_path(str(job.source_root))
        self._refresh_active_job_label()
        self.status_bar.set_status(f"Åpnet {job.job_id}: {job.name}")
        self.log_panel.append(f"Jobb åpnet: {job.job_id} - {job.name}")

    def _font_scale(self, delta: int) -> None:
        """Juster skriftstørrelsen dynamisk, på samme måte som SIARD Workflow Manager."""
        theme.FontRegistry.scale(delta)
        offset = theme.FontRegistry.current_offset()
        self.settings["font_offset"] = offset
        save_config({"font_offset": offset})
        sign = f"+{offset}" if offset > 0 else str(offset)
        self.status_bar.set_status(f"Skriftstørrelse: {sign}")

    def _change_temp_dir(self) -> None:
        folder = filedialog.askdirectory(title="Velg temp-mappe")
        if folder:
            self.settings["temp_dir"] = folder
            save_config({"temp_dir": folder})
            self.status_bar.set_temp(folder)
            self.log_panel.append(f"Temp-mappe endret: {folder}")

    def _source_changed(self, extraction: Noark5Extraction | None) -> None:
        self.extraction = extraction
        if extraction:
            self._ensure_job_for_current_source()
            detection = "Noark 5" if extraction.is_noark5_candidate else "ukjent"
            self.status_bar.update_storage(extraction.root, detection=detection)
            if extraction.is_noark5_candidate:
                self.status_bar.set_status("Noark 5-uttrekk funnet")
                self.log_panel.append(f"Uttrekk valgt: {extraction.root}")
            else:
                self.status_bar.set_status("arkivstruktur.xml ble ikke funnet")
        else:
            self.status_bar.set_status("Klar")

    def _add_operation(self, operation_id: str) -> None:
        if operation_id == "dias_package":
            operation = self.registry.get(operation_id)
            extraction_root = self.extraction.root if self.extraction else None

            def add_configured(params: dict) -> None:
                operation.configure(params)
                if self.workflow_panel.add(operation_id):
                    if self.current_job:
                        self.current_job.output_root = Path(params["output_dir"]) if params.get("output_dir") else None
                        self.current_job.set_workflow(self.workflow.operation_ids())
                    self._refresh_active_job_label()
                    self.log_panel.append(f"Lagt til i workflow: {operation.definition.name}")
                    self.log_panel.append(f"DIAS-utdata: {params.get('output_dir') or '(samme mappe som uttrekk)'}")
                else:
                    self.status_bar.set_status("Operasjonen finnes allerede i workflow")

            DiasParamDialog(self, getattr(operation, "params", {}), extraction_root, add_configured)
            return

        if self.workflow_panel.add(operation_id):
            if self.current_job:
                self.current_job.set_workflow(self.workflow.operation_ids())
            self._refresh_active_job_label()
            operation = self.registry.get(operation_id)
            self.log_panel.append(f"Lagt til i workflow: {operation.definition.name}")
        else:
            self.status_bar.set_status("Operasjonen finnes allerede i workflow")

    def _progress_callback(self, value: float, message: str) -> None:
        if self.current_job:
            self.current_job.progress = max(0.0, min(1.0, float(value)))
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

        job = self._ensure_job_for_current_source()
        if job:
            job.set_workflow(op_ids)
            job.status = JobStatus.RUNNING
            job.progress = 0.0
            job.message = "Workflow startet"

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
                    self.after(
                        0,
                        lambda n=operation.definition.name, ok=result.ok: self.log_panel.append(
                            f"{'OK' if ok else 'FEIL'}: {n}"
                        ),
                    )
                    if job:
                        job.progress = index / total
                        job.message = result.message
                    self.after(0, lambda i=index, t=total: self.status_bar.set_status(f"Workflow {i}/{t}"))
                    if not result.ok:
                        break

                if isinstance(ctx.source, Noark5Extraction):
                    self.extraction = ctx.source
                if job:
                    job.status = JobStatus.OK if all_ok else JobStatus.FAILED
                    job.progress = 1.0 if all_ok else job.progress
                final = "Workflow fullført" if all_ok else "Workflow stoppet med feil"
                self.after(0, lambda: self.status_bar.set_status(final))
            except Exception as exc:
                if job:
                    job.status = JobStatus.FAILED
                    job.message = str(exc)
                self.after(0, lambda: self.log_panel.append(f"FEIL: {exc}"))
                self.after(0, lambda: self.status_bar.set_status("Feil"))
            finally:
                self.after(0, lambda: self.workflow_panel.run_button.configure(state="normal"))
                if self.jobs_window is not None and self.jobs_window.winfo_exists():
                    self.after(0, self.jobs_window.refresh)

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
        self.settings["font_offset"] = theme.FontRegistry.current_offset()
        save_config(self.settings)
        self.status_bar.set_temp(self.settings.get("temp_dir") or None)
        self.status_bar.set_status("Innstillinger oppdatert")


def run_gui() -> None:
    theme.apply_theme()
    app = WorkflowApp()
    app.mainloop()
