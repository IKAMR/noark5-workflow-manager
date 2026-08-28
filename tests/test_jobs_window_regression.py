import unittest
from pathlib import Path


class JobsWindowRegressionTests(unittest.TestCase):
    def test_jobs_window_does_not_pass_width_none_to_ctklabel(self):
        source = (Path(__file__).resolve().parents[1] / "gui" / "jobs_window.py").read_text(encoding="utf-8")
        self.assertNotIn("width=None", source)
        self.assertNotIn("width=width if width else None", source)


if __name__ == "__main__":
    unittest.main()
