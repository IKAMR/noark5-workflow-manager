import unittest
from pathlib import Path
from types import SimpleNamespace

from noark5_workflow.core.job import Job, JobStatus
from noark5_workflow.core.job_runner import JobContinueError, JobRunner


class _Operation:
    def __init__(self, operation_id: str):
        self.operation_id = operation_id
        self.definition = SimpleNamespace(name=operation_id)


class _Registry:
    def get(self, operation_id: str):
        return _Operation(operation_id)


class _Executor:
    def __init__(self):
        self.executed = []

    def execute(self, operation, ctx):
        self.executed.append(operation.operation_id)
        return SimpleNamespace(ok=True, message="OK", warnings=[], data={})


class JobContinueA11Tests(unittest.TestCase):
    def _runner(self, executor=None):
        executor = executor or _Executor()
        return JobRunner(
            _Registry(),
            executor,
            {},
            source_factory=lambda source_root: SimpleNamespace(root=source_root),
        ), executor

    def test_continue_runs_from_next_operation_only(self):
        job = Job(
            job_id="JOB-001",
            source_root=Path("source"),
            workflow_ids=["one", "two", "three"],
            checkpoint_after=["one"],
            next_operation_index=1,
            status=JobStatus.WAITING,
            progress=1 / 3,
        )
        runner, executor = self._runner()

        outcome = runner.continue_job(job)

        self.assertTrue(outcome.ok)
        self.assertEqual(executor.executed, ["two", "three"])
        self.assertEqual(job.status, JobStatus.OK)
        self.assertEqual(job.next_operation_index, 3)
        self.assertEqual(job.progress, 1.0)

    def test_continue_rejects_job_that_is_not_waiting(self):
        job = Job(
            job_id="JOB-001",
            source_root=Path("source"),
            workflow_ids=["one", "two"],
            checkpoint_after=["one"],
            next_operation_index=1,
            status=JobStatus.READY,
        )
        runner, executor = self._runner()

        with self.assertRaises(JobContinueError):
            runner.continue_job(job)

        self.assertEqual(executor.executed, [])
        self.assertEqual(job.status, JobStatus.READY)

    def test_continue_rejects_invalid_waiting_cursor(self):
        job = Job(
            job_id="JOB-001",
            source_root=Path("source"),
            workflow_ids=["one", "two"],
            checkpoint_after=["one"],
            next_operation_index=0,
            status=JobStatus.WAITING,
        )
        runner, executor = self._runner()

        with self.assertRaises(JobContinueError):
            runner.continue_job(job)

        self.assertEqual(executor.executed, [])

    def test_continue_rejects_waiting_state_not_backed_by_checkpoint(self):
        job = Job(
            job_id="JOB-001",
            source_root=Path("source"),
            workflow_ids=["one", "two"],
            next_operation_index=1,
            status=JobStatus.WAITING,
        )
        runner, executor = self._runner()

        with self.assertRaises(JobContinueError):
            runner.continue_job(job)

        self.assertEqual(executor.executed, [])


if __name__ == "__main__":
    unittest.main()
