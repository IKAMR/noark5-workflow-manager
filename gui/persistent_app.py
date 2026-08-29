from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

from gui.app import WorkflowApp as BaseWorkflowApp
from noark5_workflow.core.job_store import JobListFormatError, load_job_list, save_job_list
from settings import save_config
from version import APP_NAME, VERSION

from . import theme
from .jobs_window import JobsWindow


class WorkflowApp(BaseWorkflowApp):
    """Workflow application with persistent job-list support."""

    def __init__(self) -> None:
        self.job_list_path: Path | None = None
        super().__init__()
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


def run_gui() -> None:
    theme.apply_theme()
    app = WorkflowApp()
    app.mainloop()
