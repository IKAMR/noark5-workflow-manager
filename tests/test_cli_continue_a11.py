import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from noark5_workflow.cli import EXIT_NOT_FOUND, EXIT_OK, EXIT_PREFLIGHT, EXIT_WAITING, main
from noark5_workflow.core.job import JobBatch, JobStatus
from noark5_workflow.core.job_runner import JobRunOutcome
from noark5_workflow.core.job_store import load_job_list, save_job_list


class CliContinueA11Tests(unittest.TestCase):
    def make_list(self, root: Path, *, waiting=True) -> Path:
        batch = JobBatch()
        first = batch.new_job(
            root / "source1",
            output_root=root / "out1",
            name="First extraction",
            workflow_ids=["one", "two", "three"],
        )
        first.set_checkpoint("one", True)
        if waiting:
            first.status = JobStatus.WAITING
            first.next_operation_index = 1
            first.progress = 1 / 3
            first.message = "Venter ved kontrollpunkt etter One"
        batch.new_job(
            root / "source2",
            output_root=root / "out2",
            name="Second extraction",
            workflow_ids=["one"],
        )
        path = root / "continue.n5jobs"
        save_job_list(path, batch, active_job_id=first.job_id, app_version="test")
        return path

    def test_continue_unknown_job_returns_not_found(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            error = io.StringIO()
            with redirect_stderr(error):
                code = main(["jobs", "continue", str(path), "--job", "JOB-999"])
            self.assertEqual(code, EXIT_NOT_FOUND)
            self.assertIn("JOB-999", error.getvalue())

    @patch("noark5_workflow.cli.RunOverviewLog")
    @patch("noark5_workflow.cli.JobRunner")
    def test_continue_calls_core_continue_job_only_for_selected_job(self, runner_cls, overview_cls):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            runner = runner_cls.return_value

            def fake_continue(job, **kwargs):
                self.assertEqual(job.job_id, "JOB-001")
                self.assertEqual(job.next_operation_index, 1)
                job.status = JobStatus.OK
                job.progress = 1.0
                job.next_operation_index = 3
                job.message = "Workflow fullført"
                state_cb = kwargs.get("state_cb")
                if state_cb:
                    state_cb(job)
                return JobRunOutcome(True, True)

            runner.continue_job.side_effect = fake_continue
            overview_cls.return_value.path = Path(temp) / "run.log"

            with redirect_stdout(io.StringIO()):
                code = main(["jobs", "continue", str(path), "--job", "JOB-001"])

            self.assertEqual(code, EXIT_OK)
            runner.continue_job.assert_called_once()
            runner.run.assert_not_called()
            loaded = load_job_list(path)
            self.assertEqual(loaded.batch.get("JOB-001").status, JobStatus.OK)
            self.assertEqual(loaded.batch.get("JOB-002").status, JobStatus.READY)
            self.assertEqual(loaded.active_job_id, "JOB-001")

    @patch("noark5_workflow.cli.RunOverviewLog")
    @patch("noark5_workflow.cli.JobRunner")
    def test_continue_waiting_again_returns_waiting_exit_code(self, runner_cls, overview_cls):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            runner = runner_cls.return_value

            def fake_continue(job, **kwargs):
                job.status = JobStatus.WAITING
                job.next_operation_index = 2
                job.progress = 2 / 3
                return JobRunOutcome(True, True)

            runner.continue_job.side_effect = fake_continue
            overview_cls.return_value.path = Path(temp) / "run.log"

            with redirect_stdout(io.StringIO()):
                code = main(["jobs", "continue", str(path), "--job", "JOB-001"])
            self.assertEqual(code, EXIT_WAITING)

    @patch("noark5_workflow.cli.RunOverviewLog")
    @patch("noark5_workflow.cli.JobRunner")
    def test_continue_rejects_non_waiting_job_through_core_contract(self, runner_cls, overview_cls):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp), waiting=False)
            runner = runner_cls.return_value
            runner.continue_job.side_effect = ValueError(
                "Jobben kan bare fortsettes når den venter ved et kontrollpunkt"
            )
            overview_cls.return_value.path = Path(temp) / "run.log"
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["jobs", "continue", str(path), "--job", "JOB-001"])
            self.assertEqual(code, EXIT_PREFLIGHT)
            self.assertIn("Continue blocked", output.getvalue())

    @patch("noark5_workflow.cli.RunOverviewLog")
    @patch("noark5_workflow.cli.JobRunner")
    def test_continue_accepts_job_before_file(self, runner_cls, overview_cls):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            runner = runner_cls.return_value

            def fake_continue(job, **kwargs):
                job.status = JobStatus.OK
                job.progress = 1.0
                job.next_operation_index = len(job.workflow_ids)
                job.message = "Workflow fullført"
                return JobRunOutcome(True, True)

            runner.continue_job.side_effect = fake_continue
            overview_cls.return_value.path = Path(temp) / "run.log"
            with redirect_stdout(io.StringIO()):
                code = main(["jobs", "continue", "--job", "JOB-001", str(path)])
            self.assertEqual(code, EXIT_OK)


if __name__ == "__main__":
    unittest.main()
