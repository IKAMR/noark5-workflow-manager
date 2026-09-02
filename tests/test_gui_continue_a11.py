import unittest
from pathlib import Path
from unittest.mock import MagicMock

from gui.persistent_app_a5 import WorkflowApp
from noark5_workflow.core.job import Job, JobStatus
from noark5_workflow.core.job_runner import JobRunOutcome


class GuiContinueA11Tests(unittest.TestCase):
    def make_app(self):
        app = WorkflowApp.__new__(WorkflowApp)
        app.job_runner = MagicMock()
        app.job_list_path = None
        app.cancel_requested = False
        app.batch_cancel_requested = False
        app.jobs_window = None
        app.after = lambda delay, callback: None
        app._progress_callback_for_job = MagicMock()
        app._job_log = MagicMock()
        app._runner_state_changed = MagicMock()
        app._update_run_button = MagicMock()
        app._refresh_jobs_window_safe = MagicMock()
        app._write_job_list = MagicMock()
        return app

    def make_job(self, status: JobStatus) -> Job:
        return Job(
            job_id="JOB-001",
            source_root=Path("source"),
            workflow_ids=["one", "two"],
            checkpoint_after=["one"],
            next_operation_index=1 if status == JobStatus.WAITING else 0,
            status=status,
        )

    def test_waiting_job_uses_explicit_continue_contract(self):
        app = self.make_app()
        app.job_runner.continue_job.return_value = JobRunOutcome(True, False)
        job = self.make_job(JobStatus.WAITING)

        ok = app._execute_job(job, batch_mode=False)

        self.assertTrue(ok)
        app.job_runner.continue_job.assert_called_once()
        app.job_runner.run.assert_not_called()

    def test_ready_job_still_uses_normal_run_contract(self):
        app = self.make_app()
        app.job_runner.run.return_value = JobRunOutcome(True, False)
        job = self.make_job(JobStatus.READY)

        ok = app._execute_job(job, batch_mode=False)

        self.assertTrue(ok)
        app.job_runner.run.assert_called_once()
        app.job_runner.continue_job.assert_not_called()


if __name__ == "__main__":
    unittest.main()
