from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class A19JobsWindowRefreshAfterLoadTests(unittest.TestCase):
    def test_successful_async_job_list_load_refreshes_open_jobs_window(self):
        text = (ROOT / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        method = text.split("def _load_job_list_file", 1)[1].split("def ", 1)[0]
        self.assertIn('jobs_window = getattr(self, "jobs_window", None)', method)
        self.assertIn("jobs_window.winfo_exists()", method)
        self.assertIn("jobs_window.refresh()", method)

if __name__ == "__main__":
    unittest.main()
