from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class A19JobSourceRehydrationTests(unittest.TestCase):
    def test_guard_exists(self):
        text = (ROOT / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        self.assertIn("self._job_context_switch = False", text)
        self.assertIn("if self._job_context_switch:", text)

    def test_old_source_is_cleared_before_inherited_open(self):
        text = (ROOT / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        method = text.split("def _open_job", 1)[1].split("def ", 1)[0]
        self.assertLess(
            method.index('self.source_panel.path_var.set("")'),
            method.index("super()._open_job(job)"),
        )

    def test_redetect_happens_after_guard_release(self):
        text = (ROOT / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        method = text.split("def _open_job", 1)[1].split("def ", 1)[0]
        self.assertLess(
            method.index("self._job_context_switch = False"),
            method.rindex("self.source_panel.detect()"),
        )

if __name__ == "__main__":
    unittest.main()
