from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from noark5_workflow.core.job import Job, JobBatch, JobStatus
from noark5_workflow.core.job_runner import JobRunner


_TERMINAL_STATUSES = {JobStatus.OK, JobStatus.FAILED, JobStatus.SKIPPED}


@dataclass(frozen=True)
class BatchRunOutcome:
    total: int
    finished: int
    waiting: int
    failed: int
    skipped: int
    cancelled: bool = False

    @property
    def ok(self) -> bool:
        return self.failed == 0


class BatchRunner:
    """GUI-independent sequential execution of a collection of Jobs.

    BatchRunner owns batch execution semantics only. UI threading, dialogs,
    run-overview logging and job-list persistence remain responsibilities of
    the calling client.
    """

    def __init__(self, job_runner: JobRunner) -> None:
        self.job_runner = job_runner

    def run(
        self,
        jobs: JobBatch | Iterable[Job],
        *,
        cancelled_cb: Callable[[], bool] | None = None,
        progress_cb: Callable[[Job, float, str], None] | None = None,
        log_cb: Callable[[Job, str], None] | None = None,
        state_cb: Callable[[Job], None] | None = None,
        preparing_cb: Callable[[Job, int, int], None] | None = None,
        registered_cb: Callable[[Job, int, int, bool], None] | None = None,
        finished_cb: Callable[[Job, int, int], None] | None = None,
    ) -> BatchRunOutcome:
        ordered = jobs.jobs() if isinstance(jobs, JobBatch) else list(jobs)
        total = len(ordered)
        cancelled_seen = False

        def cancelled() -> bool:
            return bool(cancelled_cb and cancelled_cb())

        for position, job in enumerate(ordered, start=1):
            if preparing_cb:
                preparing_cb(job, position, total)

            if cancelled():
                cancelled_seen = True
                if job.status == JobStatus.READY:
                    job.status = JobStatus.SKIPPED
                    job.message = "Ikke startet - batch avbrutt"
                    if state_cb:
                        state_cb(job)
                if registered_cb:
                    registered_cb(job, position, total, False)
                if finished_cb:
                    finished_cb(job, position, total)
                continue

            # Terminal jobs in an explicitly approved batch rerun start from the
            # beginning. WAITING jobs keep their cursor and continue normally.
            if job.status in _TERMINAL_STATUSES:
                job.reset_execution("Klar for ny batchkjøring")
                if state_cb:
                    state_cb(job)

            if registered_cb:
                registered_cb(job, position, total, True)

            self.job_runner.run(
                job,
                progress_cb=(
                    (lambda value, message, j=job: progress_cb(j, value, message))
                    if progress_cb else None
                ),
                log_cb=((lambda message, j=job: log_cb(j, message)) if log_cb else None),
                cancelled_cb=cancelled_cb,
                state_cb=state_cb,
            )

            if finished_cb:
                finished_cb(job, position, total)

            if cancelled():
                cancelled_seen = True

        counts = {
            status: sum(job.status == status for job in ordered)
            for status in JobStatus
        }
        return BatchRunOutcome(
            total=total,
            finished=counts[JobStatus.OK],
            waiting=counts[JobStatus.WAITING],
            failed=counts[JobStatus.FAILED],
            skipped=counts[JobStatus.SKIPPED],
            cancelled=cancelled_seen,
        )
