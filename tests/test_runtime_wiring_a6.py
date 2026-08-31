import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class A6RuntimeWiringTests(unittest.TestCase):
    def test_main_uses_a6_runtime(self):
        text = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn("persistent_app_a6", text)

    def test_a6_inherits_a5_and_wires_preflight(self):
        text = (ROOT / "gui" / "persistent_app_a6.py").read_text(encoding="utf-8")
        self.assertIn("A5WorkflowApp", text)
        self.assertIn("JobPreflight", text)
        self.assertIn("self.preflight.normalize_job", text)
        self.assertIn("self.preflight.check_outputs", text)
        self.assertIn("self.preflight.find_reruns", text)

    def test_gui_keeps_user_confirmation(self):
        text = (ROOT / "gui" / "persistent_app_a6.py").read_text(encoding="utf-8")
        self.assertIn("messagebox.askyesno", text)
        core = (ROOT / "noark5_workflow" / "core" / "preflight.py").read_text(encoding="utf-8")
        self.assertNotIn("messagebox", core)


if __name__ == "__main__":
    unittest.main()
