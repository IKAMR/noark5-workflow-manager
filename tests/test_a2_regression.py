import unittest
from pathlib import Path


class A2RegressionTests(unittest.TestCase):
    def test_start_all_is_connected(self):
        root = Path(__file__).resolve().parents[1]
        jobs = (root / "gui" / "jobs_window.py").read_text(encoding="utf-8")
        app = (root / "gui" / "app.py").read_text(encoding="utf-8")
        self.assertIn('text="Start alle", command=self.on_start_all', jobs)
        self.assertIn("def _start_all_jobs", app)
        self.assertIn("def _execute_job", app)

    def test_dias_params_are_stored_on_job(self):
        root = Path(__file__).resolve().parents[1]
        app = (root / "gui" / "app.py").read_text(encoding="utf-8")
        self.assertIn("self.current_job.set_operation_params(operation_id, params)", app)


if __name__ == "__main__":
    unittest.main()
