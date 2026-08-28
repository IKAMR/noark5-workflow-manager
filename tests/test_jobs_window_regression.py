import unittest
from pathlib import Path


class JobsWindowRegressionTests(unittest.TestCase):
    def test_flexible_column_does_not_pass_none_width_to_ctklabel(self):
        source = (Path(__file__).resolve().parents[1] / "gui" / "jobs_window.py").read_text(encoding="utf-8")
        self.assertNotIn("width=width if width else None", source)
        self.assertIn('if width is not None:', source)
        self.assertIn('label_kwargs["width"] = width', source)


if __name__ == "__main__":
    unittest.main()
