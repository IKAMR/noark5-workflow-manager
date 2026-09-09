from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class A19AtomicJobListSourceRestoreTests(unittest.TestCase):
    def test_job_list_load_clears_old_source_before_loading(self):
        text = (ROOT/"gui"/"persistent_app_a18.py").read_text(encoding="utf-8")
        method = text.split("def _load_job_list_file",1)[1].split("def ",1)[0]
        self.assertLess(method.index('self.source_panel.path_var.set("")'),
                        method.index("super()._load_job_list_file"))

    def test_post_load_source_comes_from_active_job(self):
        text = (ROOT/"gui"/"persistent_app_a18.py").read_text(encoding="utf-8")
        method = text.split("def _load_job_list_file",1)[1].split("def ",1)[0]
        self.assertIn("self.current_job.active_extraction_root", method)

    def test_source_callback_is_blocked_during_restore(self):
        text = (ROOT/"gui"/"persistent_app_a18.py").read_text(encoding="utf-8")
        method = text.split("def _source_changed",1)[1].split("def ",1)[0]
        self.assertIn("if self._job_context_switch:", method)
        self.assertIn("return", method)

if __name__ == "__main__":
    unittest.main()
