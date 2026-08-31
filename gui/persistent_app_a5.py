from __future__ import annotations

import threading
import time
from tkinter import messagebox

from noark5_workflow.core.batch_runner import BatchRunner
from noark5_workflow.core.job import Job, JobStatus
from noark5_workflow.core.job_runner import JobRunner
from version import APP_NAME

from . import theme
from .persistent_app import _TERMINAL_STATUSES
from .persistent_app_a2155 import WorkflowApp as A2155WorkflowApp


class WorkflowApp(A2155WorkflowApp):
    """a5: GUI-independent JobRunner and BatchRunner wired into the runtime."""

    def __init__(self) -> None:
        super().__init__()
        self.job_runner = JobRunner(self.registry, self.executor, self.settings)
        self.batch_runner = BatchRunner(self.job_runner)

    def _refresh_jobs_window_safe(self) -> None:
        if self.jobs_window is not None and self.jobs_window.winfo_exists():
            self.jobs_window.refresh()

    def _runner_state_changed(self, job: Job) -> None:
        self.after(0, self._refresh_jobs_window_safe)

    def _execute_job(self, job: Job, *, batch_mode: bool) -> bool:
        """Thin GUI adapter around the GUI-independent JobRunner."""
        outcome = self.job_runner.run(
            job,
            progress_cb=lambda value, message: self._progress_callback_for_job(
                job, value, message
            ),
            log_cb=lambda message: self._job_log(job, message),
            cancelled_cb=(
                (lambda: self.batch_cancel_requested)
                if batch_mode
                else (lambda: self.cancel_requested)
            ),
            state_cb=self._runner_state_changed,
        )

        if outcome.persist_recommended and self.job_list_path is not None:
            self._write_job_list(self.job_list_path)
        self.after(0, self._update_run_button)
        self.after(0, self._refresh_jobs_window_safe)
        return outcome.ok

    def _start_all_jobs(self) -> None:
        """GUI lifecycle around the GUI-independent sequential BatchRunner."""
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

        def preparing(job: Job, position: int, total: int) -> None:
            self._set_batch_phase(
                overview,
                f"Forbereder {job.job_id} ({position} av {total})",
            )

        def registered(job: Job, position: int, total: int, will_run: bool) -> None:
            self._set_batch_phase(overview, f"Registrerer {job.job_id} i kjørelogg")
            overview.start_job(job)
            first_job_registered.set()
            if will_run:
                self._set_batch_phase(
                    overview,
                    f"Kjører {job.job_id} ({position} av {total})",
                )

        def finished(job: Job, position: int, total: int) -> None:
            overview.finish_job(job)
            if self.job_list_path is not None:
                self._write_job_list(self.job_list_path)

        def worker() -> None:
            worker_started.set()
            try:
                self._set_batch_phase(overview, "Worker startet")
                outcome = self.batch_runner.run(
                    jobs,
                    cancelled_cb=lambda: self.batch_cancel_requested,
                    progress_cb=lambda job, value, message: self._progress_callback_for_job(
                        job, value, message
                    ),
                    log_cb=lambda job, message: self._job_log(job, message),
                    state_cb=self._runner_state_changed,
                    preparing_cb=preparing,
                    registered_cb=registered,
                    finished_cb=finished,
                )

                self._set_batch_phase(overview, "Avslutter batch")
                summary = (
                    f"BATCH FERDIG: totalt={outcome.total}, ferdig={outcome.finished}, "
                    f"venter={outcome.waiting}, feil={outcome.failed}, "
                    f"hoppet over={outcome.skipped}"
                )
                status = (
                    "FEIL"
                    if outcome.failed
                    else ("VENTER" if outcome.waiting else "FERDIG")
                )
                overview.finish(status)
                self.after(0, lambda s=summary: self.log_panel.append(s))
                self.after(0, lambda s=summary: self.status_bar.set_status(s))

            except Exception as exc:
                overview.set_phase("Batch stoppet med exception")
                overview.fail(exc)
                self.after(
                    0,
                    lambda e=str(exc): self.log_panel.append(f"BATCH FEIL: {e}"),
                )
                self.after(
                    0,
                    lambda e=str(exc): self.status_bar.set_status(
                        f"Batch stoppet med feil: {e}"
                    ),
                )

            finally:
                worker_finished.set()
                if overview.finished is None:
                    overview.finish("AVBRUTT")
                self.after(
                    0,
                    lambda p=overview.path: self.log_panel.append(
                        f"KJØRELOGG LAGRET: {p}"
                    ),
                )
                self.batch_running = False
                self.after(
                    0,
                    lambda: self.workflow_panel.run_button.configure(state="normal"),
                )
                self.after(0, self._update_run_button)
                if self.jobs_window is not None and self.jobs_window.winfo_exists():
                    self.after(
                        0,
                        lambda: self.jobs_window.set_batch_running(False),
                    )
                    self.after(0, self.jobs_window.refresh)

        thread = threading.Thread(target=worker, daemon=True, name="n5wfman-batch")
        thread.start()

        # Preserve the non-blocking startup watchdog introduced in a2.15.5.
        def startup_watchdog() -> None:
            deadline = time.monotonic() + self._BATCH_STARTUP_TIMEOUT_SECONDS

            while time.monotonic() < deadline:
                if worker_finished.is_set() or first_job_registered.is_set():
                    return
                time.sleep(0.1)

            if not worker_started.is_set():
                message = "Batch-worker startet ikke innen timeout."
            else:
                message = (
                    "Batch-worker startet, men ingen jobb ble registrert innen "
                    f"{self._BATCH_STARTUP_TIMEOUT_SECONDS:.0f} sekunder."
                )

            overview.set_phase("Startup-failsafe utløst")
            overview.fail(message)
            self.batch_cancel_requested = True
            self.batch_running = False

            self.after(
                0,
                lambda m=message: self.log_panel.append(f"BATCH STARTUP-FEIL: {m}"),
            )
            self.after(0, lambda m=message: self.status_bar.set_status(m))
            self.after(
                0,
                lambda: self.workflow_panel.run_button.configure(state="normal"),
            )
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
