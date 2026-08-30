from __future__ import annotations

from pathlib import Path

from app.workspace import ensure_workspace, job_list_dir
from .persistent_app_a215 import WorkflowApp as A215WorkflowApp
from . import theme


class WorkflowApp(A215WorkflowApp):
    """a2.15.1: workspace creation and job-list fallback to workspace defaults."""

    def __init__(self) -> None:
        super().__init__()
        ensure_workspace(self.settings)

    def _job_list_initial_dir(self) -> str | None:
        configured = job_list_dir(self.settings)
        if configured.is_dir():
            return str(configured)

        previous = str(self.settings.get("last_job_list_dir", "")).strip()
        if previous and Path(previous).is_dir():
            return previous

        ensure_workspace(self.settings)
        return str(job_list_dir(self.settings))


def run_gui() -> None:
    theme.apply_theme()
    app = WorkflowApp()
    app.mainloop()
