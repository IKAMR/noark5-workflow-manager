import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from noark5_workflow.cli import EXIT_OK, EXIT_PREFLIGHT, main
from noark5_workflow.core.job import JobBatch, JobStatus
from noark5_workflow.core.job_store import save_job_list


class CliA7Tests(unittest.TestCase):
    def make_list(self, root: Path, *, duplicate=False, completed=False) -> Path:
        batch = JobBatch()
        first = batch.new_job(root / "source1", output_root=root / "out1", workflow_ids=["metadata_inventory"])
        if completed:
            first.status = JobStatus.OK
        if duplicate:
            batch.new_job(root / "source2", output_root=root / "out1", workflow_ids=["metadata_inventory"])
        path = root / "test.n5jobs"
        save_job_list(path, batch, app_version="test")
        return path

    def test_jobs_check_valid_list(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp))
            with redirect_stdout(io.StringIO()):
                code = main(["jobs", "check", str(path)])
            self.assertEqual(code, EXIT_OK)

    def test_jobs_check_detects_duplicate_output(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp), duplicate=True)
            with redirect_stdout(io.StringIO()):
                code = main(["jobs", "check", str(path)])
            self.assertEqual(code, EXIT_PREFLIGHT)

    def test_jobs_run_requires_explicit_rerun(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_list(Path(temp), completed=True)
            with redirect_stdout(io.StringIO()):
                code = main(["jobs", "run", str(path)])
            self.assertEqual(code, EXIT_PREFLIGHT)

    def test_console_entry_point_is_n5wf(self):
        pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
        text = pyproject.read_text(encoding="utf-8")
        self.assertIn('n5wf = "noark5_workflow.cli:main"', text)


if __name__ == "__main__":
    unittest.main()
