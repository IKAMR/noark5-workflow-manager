from __future__ import annotations

from tkinter import messagebox

from noark5_workflow.core.job import Job
from noark5_workflow.core.preflight import JobPreflight
from version import APP_NAME

from . import theme
from .persistent_app_a5 import WorkflowApp as A5WorkflowApp


class WorkflowApp(A5WorkflowApp):
    """a6: GUI-independent job/batch preflight wired into the runtime."""

    def __init__(self) -> None:
        super().__init__()
        self.preflight = JobPreflight()

    def _normalise_job_before_run(self, job: Job) -> None:
        for change in self.preflight.normalize_job(job):
            self._job_log(job, f"NORMALISERT [{change.code}]: {change.message}")

    def _validate_unique_outputs(self, jobs: list[Job]) -> bool:
        conflicts = self.preflight.check_outputs(jobs)
        if not conflicts:
            return True

        conflict = conflicts[0]
        first = next((job for job in jobs if job.job_id == conflict.first_job_id), None)
        second = next((job for job in jobs if job.job_id == conflict.second_job_id), None)
        first_output = first.output_root if first is not None else conflict.output_root
        second_output = second.output_root if second is not None else conflict.output_root

        messagebox.showerror(
            APP_NAME,
            "To forskjellige jobber kan ikke bruke samme utdataområde.\n\n"
            f"{conflict.first_job_id}: {first_output}\n"
            f"{conflict.second_job_id}: {second_output}\n\n"
            "Velg separate utdataområder. Samme jobb kan kjøres flere ganger "
            "mot sitt eget område; historikk skal da bevares.",
        )
        return False

    def _confirm_rerun(self, jobs) -> bool:
        previous = self.preflight.find_reruns(jobs)
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


def run_gui() -> None:
    theme.apply_theme()
    app = WorkflowApp()
    app.mainloop()
