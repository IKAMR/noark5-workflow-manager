from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

from gui.app import WorkflowApp as BaseWorkflowApp
from noark5_workflow.core.job import JobStatus
from noark5_workflow.core.job_store import JobListFormatError, load_job_list, save_job_list
from settings import save_config
from version import APP_NAME, VERSION

from . import theme
from .dias_dialog import DiasParamDialog
from .jobs_window import JobsWindow


_TERMINAL_STATUSES = {JobStatus.OK, JobStatus.FAILED, JobStatus.SKIPPED}


class WorkflowApp(BaseWorkflowApp):
    """Workflow application with persistent job-list support."""

    def __init__(self) -> None:
        self.job_list_path: Path | None = None
        super().__init__()
        # BaseWorkflowApp creates WorkflowPanel. v0.1.2-a1 adds an edit callback
        # without changing the base constructor contract.
        self.workflow_panel.on_edit = self._edit_operation
        self.workflow_panel.refresh()
        self._restore_last_job_list()

    def _open_jobs(self) -> None:
        self._capture_job_operation_params(self.current_job)
        if self.jobs_window is not None and self.jobs_window.winfo_exists():
            self.jobs_window.focus()
            self.jobs_window.refresh()
            return
        self.jobs_window = JobsWindow(
            self,
            self.jobs,
            self._open_job,
            self._create_job,
            self._start_all_jobs,
            self._stop_batch,
            self._new_job_list,
            self._open_job_list_dialog,
            self._save_job_list,
            self._save_job_list_as,
            lambda: self.job_list_path,
        )

    def _job_list_initial_dir(self) -> str | None:
        if self.job_list_path is not None and self.job_list_path.parent.is_dir():
            return str(self.job_list_path.parent)
        previous = str(self.settings.get("last_job_list_dir", "")).strip()
        return previous if previous and Path(previous).is_dir() else None

    def _new_job_list(self) -> bool:
        if self.batch_running:
            return False
        if len(self.jobs) and not messagebox.askyesno(
            APP_NAME,
            "Opprette en ny tom jobbliste? Gjeldende jobbliste blir ikke lagret automatisk.",
        ):
            return False

        self.current_job = None
        self.jobs.clear()
        self.workflow.clear()
        self.workflow_panel.refresh()
        self.source_panel.path_var.set("")
        self.source_panel.detect()
        self.log_panel.clear()
        self.job_list_path = None
        self._refresh_active_job_label()

        self.settings["last_job_list_file"] = ""
        save_config({"last_job_list_file": ""})
        self.status_bar.set_status("Ny tom jobbliste")
        return True

    def _open_job_list_dialog(self) -> bool:
        if self.batch_running:
            return False

        kwargs = {
            "title": "Åpne jobbliste",
            "filetypes": [("Noark 5 jobbliste", "*.n5jobs"), ("Alle filer", "*.*")],
        }
        initial = self._job_list_initial_dir()
        if initial:
            kwargs["initialdir"] = initial

        filename = filedialog.askopenfilename(**kwargs)
        if not filename:
            return False
        return self._load_job_list_file(Path(filename), show_error=True)

    def _load_job_list_file(self, path: Path, *, show_error: bool) -> bool:
        try:
            loaded = load_job_list(path)
        except (JobListFormatError, OSError) as exc:
            if show_error:
                messagebox.showerror(APP_NAME, f"Kunne ikke åpne jobblisten:\n{exc}")
            return False

        self.current_job = None
        self.workflow.clear()
        self.jobs.replace_all(loaded.batch.jobs())
        self.job_list_path = Path(path)

        self.settings["last_job_list_file"] = str(path)
        self.settings["last_job_list_dir"] = str(path.parent)
        save_config({
            "last_job_list_file": str(path),
            "last_job_list_dir": str(path.parent),
        })

        active = self.jobs.get(loaded.active_job_id) if loaded.active_job_id else None
        if active is None and len(self.jobs):
            active = self.jobs.jobs()[0]

        if active is not None:
            self._open_job(active)
        else:
            self.workflow_panel.refresh()
            self.source_panel.path_var.set("")
            self.source_panel.detect()
            self._refresh_active_job_label()

        self.status_bar.set_status(f"Jobbliste åpnet: {path.name}")
        return True

    def _save_job_list(self) -> bool:
        if self.batch_running:
            return False
        if self.job_list_path is None:
            return self._save_job_list_as()
        return self._write_job_list(self.job_list_path)

    def _save_job_list_as(self) -> bool:
        if self.batch_running:
            return False

        kwargs = {
            "title": "Lagre jobbliste som",
            "defaultextension": ".n5jobs",
            "filetypes": [("Noark 5 jobbliste", "*.n5jobs"), ("Alle filer", "*.*")],
        }
        initial = self._job_list_initial_dir()
        if initial:
            kwargs["initialdir"] = initial

        filename = filedialog.asksaveasfilename(**kwargs)
        if not filename:
            return False
        return self._write_job_list(Path(filename))

    def _write_job_list(self, path: Path) -> bool:
        self._capture_job_operation_params(self.current_job)
        try:
            saved_path = save_job_list(
                path,
                self.jobs,
                active_job_id=self.current_job.job_id if self.current_job else None,
                app_version=VERSION,
            )
        except (OSError, TypeError) as exc:
            messagebox.showerror(APP_NAME, f"Kunne ikke lagre jobblisten:\n{exc}")
            return False

        self.job_list_path = saved_path
        self.settings["last_job_list_file"] = str(saved_path)
        self.settings["last_job_list_dir"] = str(saved_path.parent)
        save_config({
            "last_job_list_file": str(saved_path),
            "last_job_list_dir": str(saved_path.parent),
        })
        self.status_bar.set_status(f"Jobbliste lagret: {saved_path.name}")
        return True

    def _restore_last_job_list(self) -> None:
        previous = str(self.settings.get("last_job_list_file", "")).strip()
        if not previous:
            return

        path = Path(previous)
        if not path.is_file():
            return

        if not self._load_job_list_file(path, show_error=False):
            self.status_bar.set_status("Sist brukte jobbliste kunne ikke åpnes")

    def _edit_operation(self, operation_id: str) -> None:
        """Edit existing per-job operation configuration without replacing history."""
        if self.batch_running:
            messagebox.showwarning(APP_NAME, "Workflow kan ikke redigeres mens Start alle kjører.")
            return
        job = self.current_job
        if job is None:
            messagebox.showwarning(APP_NAME, "Åpne en jobb før du redigerer workflow.")
            return
        if operation_id not in job.workflow_ids:
            messagebox.showwarning(APP_NAME, "Operasjonen finnes ikke i aktiv jobb.")
            return

        if operation_id != "dias_package":
            self.status_bar.set_status("Denne operasjonen har ingen redigeringsdialog ennå")
            return

        operation = self.registry.get(operation_id)
        initial_params = job.get_operation_params(operation_id)
        extraction_root = self.extraction.root if self.extraction else job.source_root

        def save_changes(params: dict) -> None:
            operation.configure(params)
            job.set_operation_params(operation_id, params)
            job.set_workflow(self.workflow.operation_ids())
            job.output_root = Path(params["output_dir"]) if params.get("output_dir") else None

            if job.status in _TERMINAL_STATUSES:
                job.status = JobStatus.READY
                job.progress = 0.0
                job.message = "Konfigurasjon endret - klar for ny kjøring"

            self._job_log(job, "KONFIGURASJON ENDRET: DIAS-pakking")
            self.log_panel.append(f"DIAS-konfigurasjon oppdatert for {job.job_id}")
            self.status_bar.set_status("DIAS-konfigurasjon oppdatert")
            if self.jobs_window is not None and self.jobs_window.winfo_exists():
                self.jobs_window.refresh()

            # A named job list should keep the edit immediately. An unnamed list
            # remains in memory until the user chooses Lagre/Lagre som.
            if self.job_list_path is not None:
                self._write_job_list(self.job_list_path)

        DiasParamDialog(self, initial_params, extraction_root, save_changes)

    def _confirm_rerun(self, jobs) -> bool:
        previous = [
            job for job in jobs
            if job.status in _TERMINAL_STATUSES
            or job.message == "Konfigurasjon endret - klar for ny kjøring"
        ]
        if not previous:
            return True
        names = ", ".join(job.job_id for job in previous[:6])
        if len(previous) > 6:
            names += f" + {len(previous) - 6} til"
        return messagebox.askyesno(
            APP_NAME,
            "En eller flere jobber er tidligere kjørt:\n\n"
            f"{names}\n\n"
            "Kjøre på nytt? Tidligere resultatmapper slettes ikke. "
            "En ny DIAS/AIC får ny identifikator, og ny kjøring dokumenteres som en ny hendelse.",
        )

    def _run_workflow(self) -> None:
        job = self.current_job
        if job is not None and job.status in _TERMINAL_STATUSES:
            if not self._confirm_rerun([job]):
                return
        super()._run_workflow()

    def _start_all_jobs(self) -> None:
        if not self.batch_running and not self._confirm_rerun(self.jobs.jobs()):
            return
        super()._start_all_jobs()


def run_gui() -> None:
    theme.apply_theme()
    app = WorkflowApp()
    app.mainloop()
