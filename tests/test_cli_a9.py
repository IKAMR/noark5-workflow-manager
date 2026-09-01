import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from noark5_workflow.cli import EXIT_NOT_FOUND, EXIT_OK, main
from noark5_workflow.core.job import JobBatch, JobStatus
from noark5_workflow.core.job_store import save_job_list


class CliA9Tests(unittest.TestCase):
    def make_list(self, root: Path) -> Path:
        batch = JobBatch()
        first = batch.new_job(
            root / "source1",
            output_root=root / "out1",
            name="First extraction",
            workflow_ids=["metadata_inventory", "dias_package"],
        )
        first.status = JobStatus.WAITING
        first.progress = 0.5
        first.next_operation_index = 1
        first.checkpoint_after = ["metadata_inventory"]
        first.message = "Waiting for review"
        batch.new_job(
            root / "source2",
            output_root=root / "out2",
            name="Second extraction",
            workflow_ids=["metadata_inventory"],
        )
        path = root / "status.n5jobs"
        save_job_list(path, batch, active_job_id=first.job_id, app_version="test")
        return path

    def test_jobs_status_lists_all_jobs(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["jobs", "status", str(path)])
            self.assertEqual(code, EXIT_OK)
            text = output.getvalue()
            self.assertIn("JOB-001", text)
            self.assertIn("JOB-002", text)
            self.assertIn("Venter ved kontrollpunkt", text)
            self.assertIn("50%", text)

    def test_jobs_status_single_job_is_detailed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["jobs", "status", str(path), "--job", "JOB-001"])
            self.assertEqual(code, EXIT_OK)
            text = output.getvalue()
            self.assertIn("Job ID: JOB-001", text)
            self.assertIn("Next operation: dias_package", text)
            self.assertIn("Checkpoints: metadata_inventory", text)

    def test_jobs_status_accepts_job_option_before_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            with redirect_stdout(io.StringIO()):
                code = main(["jobs", "status", "--job", "JOB-001", str(path)])
            self.assertEqual(code, EXIT_OK)

    def test_jobs_status_unknown_job_returns_not_found(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            error = io.StringIO()
            with redirect_stderr(error):
                code = main(["jobs", "status", str(path), "--job", "JOB-999"])
            self.assertEqual(code, EXIT_NOT_FOUND)
            self.assertIn("JOB-999", error.getvalue())

    def test_jobs_status_does_not_modify_job_list(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            before = path.read_bytes()
            with redirect_stdout(io.StringIO()):
                code = main(["jobs", "status", str(path)])
            after = path.read_bytes()
            self.assertEqual(code, EXIT_OK)
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
