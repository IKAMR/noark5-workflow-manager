import tempfile
import unittest
from pathlib import Path

from app.workspace import ensure_workspace, job_list_dir, run_log_dir, setup_dir

ROOT = Path(__file__).resolve().parents[1]


class WorkspaceDefaultsA2151Tests(unittest.TestCase):
    def test_workspace_is_created_from_temp(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "n5wfman"
            settings = {"temp_dir": str(root), "run_log_dir": "", "setup_dir": "", "job_list_dir": ""}
            ensure_workspace(settings)
            self.assertTrue((root / "logs" / "runs").is_dir())
            self.assertTrue((root / "setup").is_dir())
            self.assertTrue((root / "joblists").is_dir())
            self.assertTrue((root / "work").is_dir())
            self.assertTrue((root / "cache").is_dir())

    def test_empty_custom_value_means_default(self):
        settings = {"temp_dir": "C:/uttrekk-n5wfman", "run_log_dir": "", "setup_dir": "", "job_list_dir": ""}
        self.assertEqual(run_log_dir(settings), Path("C:/uttrekk-n5wfman") / "logs" / "runs")
        self.assertEqual(setup_dir(settings), Path("C:/uttrekk-n5wfman") / "setup")
        self.assertEqual(job_list_dir(settings), Path("C:/uttrekk-n5wfman") / "joblists")

    def test_settings_dialog_has_browse_and_default_buttons(self):
        text = (ROOT / "gui" / "settings_dialog.py").read_text(encoding="utf-8")
        self.assertIn('text="Velg…"', text)
        self.assertIn('text="Bruk standard"', text)
        self.assertIn("def _browse_standard_dir", text)
        self.assertIn("def _use_default_dir", text)

    def test_latest_runtime_uses_joblist_workspace_fallback(self):
        latest = (ROOT / "gui" / "persistent_app_a2155.py").read_text(encoding="utf-8")
        parent = (ROOT / "gui" / "persistent_app_a2151.py").read_text(encoding="utf-8")
        self.assertIn("A2154WorkflowApp", latest)
        self.assertIn("job_list_dir(self.settings)", parent)
        self.assertIn("ensure_workspace(self.settings)", parent)

    def test_main_uses_workspace_runtime_chain(self):
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        a5 = (ROOT / "gui" / "persistent_app_a5.py").read_text(encoding="utf-8")
        self.assertIn("persistent_app_a5", main)
        self.assertIn("A2155WorkflowApp", a5)


if __name__ == "__main__":
    unittest.main()
