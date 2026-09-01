import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from noark5_workflow.cli import EXIT_NOT_FOUND, EXIT_OK, EXIT_PREFLIGHT, main
from noark5_workflow.core.job import JobBatch, JobStatus
from noark5_workflow.core.job_runner import JobRunOutcome
from noark5_workflow.core.job_store import load_job_list, save_job_list


class CliA10Tests(unittest.TestCase):
    def make_list(self, root: Path, *, first_status=JobStatus.READY, duplicate_with_selected=False) -> Path:
        batch = JobBatch()
        first = batch.new_job(
            root / "source1",
            output_root=root / "out1",
            name="First extraction",
            workflow_ids=["metadata_inventory"],
        )
        first.status = first_status
        second_output = root / "out1" if duplicate_with_selected else root / "out2"
        batch.new_job(
            root / "source2",
            output_root=second_output,
            name="Second extraction",
            workflow_ids=["metadata_inventory"],
        )
        path = root / "run-one.n5jobs"
        save_job_list(path, batch, active_job_id=first.job_id, app_version="test")
        return path

    def test_run_unknown_job_returns_not_found(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            error = io.StringIO()
            with redirect_stderr(error):
                code = main(["jobs", "run", str(path), "--job", "JOB-999"])
            self.assertEqual(code, EXIT_NOT_FOUND)
            self.assertIn("JOB-999", error.getvalue())

    def test_selected_terminal_job_requires_rerun(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp), first_status=JobStatus.OK)
            with redirect_stdout(io.StringIO()):
                code = main(["jobs", "run", str(path), "--job", "JOB-001"])
            self.assertEqual(code, EXIT_PREFLIGHT)

    def test_selected_job_checks_output_conflicts_against_other_jobs(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp), duplicate_with_selected=True)
            with redirect_stdout(io.StringIO()):
                code = main(["jobs", "run", str(path), "--job", "JOB-001"])
            self.assertEqual(code, EXIT_PREFLIGHT)

    @patch("noark5_workflow.cli.RunOverviewLog")
    @patch("noark5_workflow.cli.JobRunner")
    def test_run_selected_job_only(self, runner_cls, overview_cls):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            runner = runner_cls.return_value

            def fake_run(job, **kwargs):
                self.assertEqual(job.job_id, "JOB-001")
                job.status = JobStatus.OK
                job.progress = 1.0
                job.message = "Workflow fullført"
                state_cb = kwargs.get("state_cb")
                if state_cb:
                    state_cb(job)
                return JobRunOutcome(True, True)

            runner.run.side_effect = fake_run
            overview_cls.return_value.path = Path(temp) / "run.log"

            with redirect_stdout(io.StringIO()):
                code = main(["jobs", "run", str(path), "--job", "JOB-001"])

            self.assertEqual(code, EXIT_OK)
            runner.run.assert_called_once()
            loaded = load_job_list(path)
            self.assertEqual(loaded.batch.get("JOB-001").status, JobStatus.OK)
            self.assertEqual(loaded.batch.get("JOB-002").status, JobStatus.READY)
            self.assertEqual(loaded.active_job_id, "JOB-001")

    @patch("noark5_workflow.cli.RunOverviewLog")
    @patch("noark5_workflow.cli.JobRunner")
    def test_run_selected_job_accepts_job_before_file(self, runner_cls, overview_cls):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            runner = runner_cls.return_value
            runner.run.return_value = JobRunOutcome(True, True)
            overview_cls.return_value.path = Path(temp) / "run.log"
            with redirect_stdout(io.StringIO()):
                code = main(["jobs", "run", "--job", "JOB-001", str(path)])
            self.assertEqual(code, EXIT_OK)

    def test_status_marks_changed_after_previous_run_as_rerun_required(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            loaded = load_job_list(path)
            job = loaded.batch.get("JOB-001")
            job.reset_execution("Konfigurasjon endret - klar for ny kjøring")
            save_job_list(path, loaded.batch, active_job_id=job.job_id, app_version="test")
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["jobs", "status", str(path), "--job", "JOB-001"])
            self.assertEqual(code, EXIT_OK)
            text = output.getvalue()
            self.assertIn("Status: Klar", text)
            self.assertIn("Rerun approval required: yes", text)
            self.assertIn("configuration changed after previous run", text)

    def test_changed_after_run_has_specific_block_message(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            loaded = load_job_list(path)
            job = loaded.batch.get("JOB-001")
            job.reset_execution("Konfigurasjon endret - klar for ny kjøring")
            save_job_list(path, loaded.batch, active_job_id=job.job_id, app_version="test")
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["jobs", "run", str(path), "--job", "JOB-001"])
            self.assertEqual(code, EXIT_PREFLIGHT)
            self.assertIn("configuration changed after a previous run", output.getvalue())

    def test_status_summary_shows_changed_after_run_label(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            loaded = load_job_list(path)
            job = loaded.batch.get("JOB-001")
            job.reset_execution("Konfigurasjon endret - klar for ny kjøring")
            save_job_list(path, loaded.batch, active_job_id=job.job_id, app_version="test")
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["jobs", "status", str(path)])
            self.assertEqual(code, EXIT_OK)
            self.assertIn("Klar – endret etter kjøring", output.getvalue())

    def test_status_detail_shows_changed_after_run_label(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            loaded = load_job_list(path)
            job = loaded.batch.get("JOB-001")
            job.reset_execution("Konfigurasjon endret - klar for ny kjøring")
            save_job_list(path, loaded.batch, active_job_id=job.job_id, app_version="test")
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["jobs", "status", str(path), "--job", "JOB-001"])
            self.assertEqual(code, EXIT_OK)
            self.assertIn("Status: Klar – endret etter kjøring", output.getvalue())


if __name__ == "__main__":
    unittest.main()
