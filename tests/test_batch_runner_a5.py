import unittest
from pathlib import Path

from noark5_workflow.core.batch_runner import BatchRunner
from noark5_workflow.core.job import Job, JobBatch, JobStatus
from noark5_workflow.core.job_runner import JobRunOutcome


class FakeJobRunner:
    def __init__(self, on_run=None):
        self.calls = []
        self.on_run = on_run

    def run(self, job, **kwargs):
        self.calls.append(job.job_id)
        if self.on_run:
            self.on_run(job)
        if job.status == JobStatus.WAITING:
            job.status = JobStatus.OK
            job.message = "Workflow fullført"
            job.progress = 1.0
        else:
            job.status = JobStatus.OK
            job.message = "Workflow fullført"
            job.progress = 1.0
        state_cb = kwargs.get("state_cb")
        if state_cb:
            state_cb(job)
        return JobRunOutcome(True, True)


class BatchRunnerA5Tests(unittest.TestCase):
    def job(self, job_id):
        return Job(job_id=job_id, source_root=Path(job_id), workflow_ids=["op"])

    def test_runs_jobs_sequentially_without_gui(self):
        batch = JobBatch()
        batch.add(self.job("JOB-001"))
        batch.add(self.job("JOB-002"))
        fake = FakeJobRunner()
        outcome = BatchRunner(fake).run(batch)
        self.assertEqual(fake.calls, ["JOB-001", "JOB-002"])
        self.assertEqual(outcome.finished, 2)
        self.assertEqual(outcome.failed, 0)

    def test_terminal_job_is_reset_before_rerun(self):
        job = self.job("JOB-001")
        job.status = JobStatus.OK
        job.next_operation_index = 1
        seen = []

        def on_run(current):
            seen.append((current.status, current.next_operation_index, current.message))

        BatchRunner(FakeJobRunner(on_run)).run([job])
        self.assertEqual(seen[0][0], JobStatus.READY)
        self.assertEqual(seen[0][1], 0)
        self.assertEqual(seen[0][2], "Klar for ny batchkjøring")

    def test_waiting_job_is_not_reset_before_continue(self):
        job = self.job("JOB-001")
        job.status = JobStatus.WAITING
        job.next_operation_index = 1
        seen = []

        def on_run(current):
            seen.append((current.status, current.next_operation_index))

        BatchRunner(FakeJobRunner(on_run)).run([job])
        self.assertEqual(seen[0], (JobStatus.WAITING, 1))

    def test_cancel_skips_jobs_not_started(self):
        first = self.job("JOB-001")
        second = self.job("JOB-002")
        state = {"cancel": False}

        def on_run(job):
            if job.job_id == "JOB-001":
                state["cancel"] = True

        fake = FakeJobRunner(on_run)
        outcome = BatchRunner(fake).run(
            [first, second],
            cancelled_cb=lambda: state["cancel"],
        )
        self.assertEqual(fake.calls, ["JOB-001"])
        self.assertEqual(second.status, JobStatus.SKIPPED)
        self.assertEqual(second.message, "Ikke startet - batch avbrutt")
        self.assertTrue(outcome.cancelled)
        self.assertEqual(outcome.skipped, 1)

    def test_callbacks_receive_batch_positions(self):
        jobs = [self.job("JOB-001"), self.job("JOB-002")]
        preparing = []
        registered = []
        finished = []
        BatchRunner(FakeJobRunner()).run(
            jobs,
            preparing_cb=lambda job, pos, total: preparing.append((job.job_id, pos, total)),
            registered_cb=lambda job, pos, total, will_run: registered.append(
                (job.job_id, pos, total, will_run)
            ),
            finished_cb=lambda job, pos, total: finished.append((job.job_id, pos, total)),
        )
        self.assertEqual(preparing, [("JOB-001", 1, 2), ("JOB-002", 2, 2)])
        self.assertEqual(registered[0], ("JOB-001", 1, 2, True))
        self.assertEqual(finished[-1], ("JOB-002", 2, 2))


if __name__ == "__main__":
    unittest.main()
