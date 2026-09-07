from __future__ import annotations

from noark5_workflow.core.job import Job
from .jobs_window import JobsWindow


class A15JobsWindow(JobsWindow):
    """a15 job creation: create the job first; storage roles are configured next."""

    def _new_job(self) -> None:
        if self._batch_running:
            return
        # No Source chooser here. A new job is a generic blank work context.
        job: Job = self.on_create_job(None)
        self.refresh()
        self._open(job)
