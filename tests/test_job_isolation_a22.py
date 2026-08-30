import unittest
from pathlib import Path

from noark5_workflow.core.job import Job, JobBatch


ROOT = Path(__file__).resolve().parents[1]


class A22JobIsolationRegressionTests(unittest.TestCase):
    def test_persistent_app_does_not_copy_shared_registry_params_back_to_job(self):
        text = (ROOT / "gui" / "persistent_app.py").read_text(encoding="utf-8")
        self.assertIn("def _capture_job_operation_params", text)
        self.assertIn("Registry operation instances are shared", text)
        self.assertNotIn(
            'params = getattr(operation, "params", None)',
            text[text.index("def _capture_job_operation_params"):text.index("def _open_jobs")],
        )

    def test_dias_execution_synchronises_output_from_job(self):
        text = (ROOT / "gui" / "persistent_app.py").read_text(encoding="utf-8")
        self.assertIn('if op_id == "dias_package":', text)
        self.assertIn('params["output_dir"] = job_output', text)
        self.assertIn("job.set_operation_params(op_id, params)", text)
        self.assertIn("operation.configure(params)", text)

    def test_jobs_window_marks_active_job(self):
        text = (ROOT / "gui" / "jobs_window.py").read_text(encoding="utf-8")
        self.assertIn("get_active_job_id", text)
        self.assertIn("• AKTIV", text)
        self.assertIn("active=(job.job_id == active_job_id)", text)

    def test_main_header_shows_position_and_unique_id(self):
        text = (ROOT / "gui" / "persistent_app.py").read_text(encoding="utf-8")
        self.assertIn('f"AKTIV JOBB: {position_text} | {self.current_job.job_id} | "', text)

    def test_same_source_jobs_keep_distinct_output_roots(self):
        batch = JobBatch()
        a = batch.new_job(Path("same-source"))
        b = batch.new_job(Path("same-source"))
        a.output_root = Path("out-a")
        b.output_root = Path("out-b")
        a.set_operation_params("dias_package", {"output_dir": "out-a"})
        b.set_operation_params("dias_package", {"output_dir": "out-b"})
        self.assertEqual(a.get_operation_params("dias_package")["output_dir"], "out-a")
        self.assertEqual(b.get_operation_params("dias_package")["output_dir"], "out-b")
        self.assertNotEqual(a.output_root, b.output_root)


if __name__ == "__main__":
    unittest.main()
