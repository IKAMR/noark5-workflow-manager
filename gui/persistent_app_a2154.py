from __future__ import annotations

import threading
from tkinter import messagebox

from app.run_overview_log import RunOverviewLog
from noark5_workflow.core.job import JobStatus
from version import APP_NAME, VERSION

from . import theme
from .persistent_app_a2151 import WorkflowApp as A2151WorkflowApp
from .persistent_app import _TERMINAL_STATUSES


class WorkflowApp(A2151WorkflowApp):
    """a2.15.4: robust run logs and stale imported job-state normalization."""

    def _normalise_job_before_run(self, job) -> None:
        if job.status == JobStatus.RUNNING:
            job.reset_execution("Tidligere kjøring var ikke aktiv - klar for ny kjøring")
            self._job_log(job, "NORMALISERT: stale RUNNING-status satt til Klar")

        try:
            index = int(job.next_operation_index)
        except (TypeError, ValueError):
            index = 0
        if index < 0 or index > len(job.workflow_ids):
            job.next_operation_index = 0
            if job.status == JobStatus.WAITING:
                job.status = JobStatus.READY
                job.progress = 0.0
                job.message = "Ugyldig execution cursor fra import - klar for ny kjøring"
                self._job_log(job, "NORMALISERT: ugyldig execution cursor")

    def _new_run_log(self, run_type: str, planned_jobs: int | None = None) -> RunOverviewLog:
        return RunOverviewLog(
            self.settings,
            run_type=run_type,
            app_version=VERSION,
            job_list_path=self.job_list_path,
            planned_jobs=planned_jobs,
        )

    def _run_workflow(self) -> None:
        if self.batch_running:
            messagebox.showwarning(APP_NAME, "Start alle kjører allerede.")
            return

        op_ids = self.workflow.operation_ids()
        if not op_ids:
            messagebox.showwarning(APP_NAME, "Legg til minst én operasjon i workflow først.")
            return
        root = self.source_panel.path_var.get().strip()
        if not root:
            messagebox.showwarning(APP_NAME, "Velg en uttrekksmappe først.")
            return

        job = self._ensure_job_for_current_source()
        if job is None:
            return
        self._normalise_job_before_run(job)
        if not self._validate_unique_outputs(self.jobs.jobs()):
            return

        job.set_workflow(op_ids)
        self._capture_job_operation_params(job)

        if job.status != JobStatus.WAITING and job.status in _TERMINAL_STATUSES:
            if not self._confirm_rerun([job]):
                return

        self.workflow_panel.run_button.configure(state="disabled")
        self.cancel_requested = False
        overview = self._new_run_log("single", planned_jobs=1)
        self.log_panel.append(f"OVERORDNET KJØRELOGG: {overview.path}")

        def worker() -> None:
            try:
                overview.start_job(job)
                ok = self._execute_job(job, batch_mode=False)
                overview.finish_job(job)
                if job.status == JobStatus.WAITING:
                    overview.finish("VENTER")
                    final = job.message
                else:
                    overview.finish("FERDIG" if ok else "FEIL")
                    final = "Workflow fullført" if ok else "Workflow stoppet med feil"
                self.after(0, lambda: self.status_bar.set_status(final))
            except Exception as exc:
                job.status = JobStatus.FAILED
                job.message = str(exc)
                try:
                    overview.finish_job(job)
                except Exception:
                    pass
                overview.fail(exc)
                self.after(0, lambda e=str(exc): self.log_panel.append(f"FEIL I SINGLE-KJØRING: {e}"))
                self.after(0, lambda e=str(exc): self.status_bar.set_status(f"Workflow stoppet med feil: {e}"))
            finally:
                if overview.finished is None:
                    overview.finish()
                self.after(0, lambda p=overview.path: self.log_panel.append(f"KJØRELOGG LAGRET: {p}"))
                self.after(0, lambda: self.workflow_panel.run_button.configure(state="normal"))
                self.after(0, self._update_run_button)

        threading.Thread(target=worker, daemon=True).start()

    def _start_all_jobs(self) -> None:
        if self.batch_running:
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
        self.log_panel.append("BATCH START: kjører alle jobber sekvensielt")
        self.log_panel.append(f"OVERORDNET KJØRELOGG: {overview.path}")

        def worker() -> None:
            try:
                for job in jobs:
                    if self.batch_cancel_requested:
                        if job.status == JobStatus.READY:
                            job.status = JobStatus.SKIPPED
                            job.message = "Ikke startet - batch avbrutt"
                        overview.start_job(job)
                        overview.finish_job(job)
                        continue

                    if job.status in _TERMINAL_STATUSES:
                        job.reset_execution("Klar for ny batchkjøring")

                    overview.start_job(job)
                    self._execute_job(job, batch_mode=True)
                    overview.finish_job(job)

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
                overview.fail(exc)
                self.after(0, lambda e=str(exc): self.log_panel.append(f"BATCH FEIL: {e}"))
                self.after(0, lambda e=str(exc): self.status_bar.set_status(f"Batch stoppet med feil: {e}"))
            finally:
                if overview.finished is None:
                    overview.finish()
                self.after(0, lambda p=overview.path: self.log_panel.append(f"KJØRELOGG LAGRET: {p}"))
                self.batch_running = False
                self.after(0, lambda: self.workflow_panel.run_button.configure(state="normal"))
                self.after(0, self._update_run_button)
                if self.jobs_window is not None and self.jobs_window.winfo_exists():
                    self.after(0, lambda: self.jobs_window.set_batch_running(False))
                    self.after(0, self.jobs_window.refresh)


def run_gui() -> None:
    theme.apply_theme()
    app = WorkflowApp()
    app.mainloop()
