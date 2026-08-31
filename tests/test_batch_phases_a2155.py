import tempfile
import unittest

from app.run_overview_log import RunOverviewLog

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


class BatchPhasesA2155Tests(unittest.TestCase):
    def test_run_log_persists_phase(self):
        with tempfile.TemporaryDirectory() as temp:
            log = RunOverviewLog(
                {"temp_dir": temp, "run_log_dir": ""},
                run_type="batch",
                app_version="0.1.2-a2",
                planned_jobs=2,
            )
            log.set_phase("Worker startet")
            text = log.path.read_text(encoding="utf-8")
            self.assertIn("Fase: Worker startet", text)

    def test_runtime_has_explicit_pre_job_phases(self):
        text = (ROOT / "gui" / "persistent_app_a2155.py").read_text(encoding="utf-8")
        for phrase in ("Worker startet", "Forbereder", "Registrerer", "Kjører", "Avslutter batch"):
            self.assertIn(phrase, text)

    def test_runtime_has_nonblocking_startup_watchdog(self):
        text = (ROOT / "gui" / "persistent_app_a2155.py").read_text(encoding="utf-8")
        self.assertIn("startup_watchdog", text)
        self.assertIn("first_job_registered", text)
        self.assertIn("worker_started", text)
        self.assertIn("BATCH STARTUP-FEIL", text)
        self.assertIn("self.batch_running = False", text)

    def test_main_uses_a2155_through_current_runtime(self):
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        a6 = (ROOT / "gui" / "persistent_app_a6.py").read_text(encoding="utf-8")
        a5 = (ROOT / "gui" / "persistent_app_a5.py").read_text(encoding="utf-8")
        self.assertIn("persistent_app_a6", main)
        self.assertIn("A5WorkflowApp", a6)
        self.assertIn("A2155WorkflowApp", a5)


if __name__ == "__main__":
    unittest.main()
