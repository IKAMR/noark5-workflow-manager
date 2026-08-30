from __future__ import annotations

import threading
import time
from tkinter import messagebox

from noark5_workflow.core.job import JobStatus
from version import APP_NAME

from . import theme
from .persistent_app import _TERMINAL_STATUSES
from .persistent_app_a2154 import WorkflowApp as A2154WorkflowApp


class WorkflowApp(A2154WorkflowApp):
    """a2.15.5: explicit batch phases and startup failsafe."""

    _BATCH_STARTUP_TIMEOUT_SECONDS = 5.0

    def _set_batch_phase(self, overview, phase: str) -> None:
        overview.set_phase(phase)
        self.after(0, lambda p=phase: self.status_bar.set_status(p))
        self.after(0, lambda p=phase: self.log_panel.append(f"BATCH FASE: {p}"))

    def _start_all_jobs(self) -> None:
        if self.batch_running:
            messagebox.showwarning(APP_NAME, "Batch-kjøring er allerede aktiv.")
            return
        if len(self.jobs) == 0:
            messagebox.showwarning(APP_NAME, "Det finnes ingen jobber å kjøre.")
            return

        jobs = self.jobs.jobs()
        for job in jobs:
            self._normalise_job_before_run(job)

        if not self._validate_unique_outputs(jobs):
            return

        terminal = [job for job in jobs if job.status in _TERMINAL_STATUSES]
        if terminal and not self._confirm_rerun(terminal):
            return

        self._capture_job_operation_params(self.current_job)
        self.batch_running = True
        self.batch_cancel_requested = False
        self.workflow_panel.run_button.configure(state="disabled")
        if self.jobs_window is not None and self.jobs_window.winfo_exists():
            self.jobs_window.set_batch_running(True)

        overview = self._new_run_log("batch", planned_jobs=len(jobs))
        overview.set_phase("Batch opprettet - worker ikke startet ennå")
        self.log_panel.append("BATCH START: kjører alle jobber sekvensielt")
        self.log_panel.append(f"OVERORDNET KJØRELOGG: {overview.path}")

        worker_started = threading.Event()
        first_job_registered = threading.Event()
        worker_finished = threading.Event()

        def worker() -> None:
            worker_started.set()
            try:
                self._set_batch_phase(overview, "Worker startet")

                for position, job in enumerate(jobs, start=1):
                    self._set_batch_phase(
                        overview,
                        f"Forbereder {job.job_id} ({position} av {len(jobs)})",
                    )

                    if self.batch_cancel_requested:
                        if job.status == JobStatus.READY:
                            job.status = JobStatus.SKIPPED
                            job.message = "Ikke startet - batch avbrutt"
                        overview.start_job(job)
                        first_job_registered.set()
                        overview.finish_job(job)
                        continue

                    if job.status in _TERMINAL_STATUSES:
                        job.reset_execution("Klar for ny batchkjøring")

                    self._set_batch_phase(
                        overview,
                        f"Registrerer {job.job_id} i kjørelogg",
                    )
                    overview.start_job(job)
                    first_job_registered.set()

                    self._set_batch_phase(
                        overview,
                        f"Kjører {job.job_id} ({position} av {len(jobs)})",
                    )
                    self._execute_job(job, batch_mode=True)
                    overview.finish_job(job)

                self._set_batch_phase(overview, "Avslutter batch")
                counts = self.jobs.counts()
                waiting = counts.get(JobStatus.WAITING, 0)
                summary = (
                    f"BATCH FERDIG: totalt={len(jobs)}, ferdig={counts[JobStatus.OK]}, "
                    f"venter={waiting}, feil={counts[JobStatus.FAILED]}, "
                    f"hoppet over={counts[JobStatus.SKIPPED]}"
                )
                status = "FEIL" if counts[JobStatus.FAILED] else ("VENTER" if waiting else "FERDIG")
                overview.finish(status)
                self.after(0, lambda s=summary: self.log_panel.append(s))
                self.after(0, lambda s=summary: self.status_bar.set_status(s))

            except Exception as exc:
                overview.set_phase("Batch stoppet med exception")
                overview.fail(exc)
                self.after(0, lambda e=str(exc): self.log_panel.append(f"BATCH FEIL: {e}"))
                self.after(0, lambda e=str(exc): self.status_bar.set_status(f"Batch stoppet med feil: {e}"))

            finally:
                worker_finished.set()
                if overview.finished is None:
                    overview.finish("AVBRUTT")
                self.after(0, lambda p=overview.path: self.log_panel.append(f"KJØRELOGG LAGRET: {p}"))
                self.batch_running = False
                self.after(0, lambda: self.workflow_panel.run_button.configure(state="normal"))
                self.after(0, self._update_run_button)
                if self.jobs_window is not None and self.jobs_window.winfo_exists():
                    self.after(0, lambda: self.jobs_window.set_batch_running(False))
                    self.after(0, self.jobs_window.refresh)

        thread = threading.Thread(target=worker, daemon=True, name="n5wfman-batch")
        thread.start()

        # Separate watchdog so Tk main loop never blocks.
        def startup_watchdog() -> None:
            deadline = time.monotonic() + self._BATCH_STARTUP_TIMEOUT_SECONDS

            while time.monotonic() < deadline:
                if worker_finished.is_set() or first_job_registered.is_set():
                    return
                time.sleep(0.1)

            # If worker did not even signal startup, report that explicitly.
            if not worker_started.is_set():
                message = "Batch-worker startet ikke innen timeout."
            else:
                message = (
                    "Batch-worker startet, men ingen jobb ble registrert innen "
                    f"{self._BATCH_STARTUP_TIMEOUT_SECONDS:.0f} sekunder."
                )

            # This is diagnostics + GUI escape hatch. We do not kill a live Python
            # thread, but we release the UI from permanent limbo and preserve the log.
            overview.set_phase("Startup-failsafe utløst")
            overview.fail(message)
            self.batch_cancel_requested = True
            self.batch_running = False

            self.after(0, lambda m=message: self.log_panel.append(f"BATCH STARTUP-FEIL: {m}"))
            self.after(0, lambda m=message: self.status_bar.set_status(m))
            self.after(0, lambda: self.workflow_panel.run_button.configure(state="normal"))
            self.after(0, self._update_run_button)
            if self.jobs_window is not None and self.jobs_window.winfo_exists():
                self.after(0, lambda: self.jobs_window.set_batch_running(False))
                self.after(0, self.jobs_window.refresh)

        threading.Thread(
            target=startup_watchdog,
            daemon=True,
            name="n5wfman-batch-watchdog",
        ).start()


def run_gui() -> None:
    theme.apply_theme()
    app = WorkflowApp()
    app.mainloop()
