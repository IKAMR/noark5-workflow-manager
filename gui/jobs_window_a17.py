from __future__ import annotations

from tkinter import messagebox

from .jobs_window_a15 import A15JobsWindow


class A17JobsWindow(A15JobsWindow):
    """a17 job-list reset semantics.

    Individual deletion never resets or reuses job identity. The final job
    is therefore not deleted through Slett; use Ny jobbliste for a clean
    identity context starting again at JOB-001.
    """

    def _delete(self, job) -> None:
        if self._batch_running:
            return

        jobs = self.batch.jobs()
        if len(jobs) == 1:
            messagebox.showinfo(
                "Data Workflow Manager",
                "Dette er siste jobb i jobblista.\n\n"
                "Bruk «Ny jobbliste» for å starte helt på nytt. "
                "Da tømmes den aktive jobblista og visningsloggen, "
                "og første nye jobb får JOB-001.\n\n"
                "Persistente kjørelogger, råresultater og PREMIS-filer på disk slettes ikke.",
            )
            return

        super()._delete(job)
