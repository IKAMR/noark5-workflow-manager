import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class A5RuntimeWiringTests(unittest.TestCase):
    def test_main_uses_a5_runtime_through_a6(self):
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        a6 = (ROOT / "gui" / "persistent_app_a6.py").read_text(encoding="utf-8")
        self.assertIn("persistent_app_a6", main)
        self.assertIn("A5WorkflowApp", a6)

    def test_a5_inherits_a2155_and_wires_runners(self):
        text = (ROOT / "gui" / "persistent_app_a5.py").read_text(encoding="utf-8")
        self.assertIn("A2155WorkflowApp", text)
        self.assertIn("JobRunner", text)
        self.assertIn("BatchRunner", text)
        self.assertIn("self.job_runner.run", text)
        self.assertIn("self.batch_runner.run", text)

    def test_a5_preserves_startup_watchdog(self):
        text = (ROOT / "gui" / "persistent_app_a5.py").read_text(encoding="utf-8")
        self.assertIn("startup_watchdog", text)
        self.assertIn("first_job_registered", text)
        self.assertIn("worker_started", text)
        self.assertIn("BATCH STARTUP-FEIL", text)


if __name__ == "__main__":
    unittest.main()
