from pathlib import Path
import unittest

from version import VERSION

ROOT = Path(__file__).resolve().parents[1]


class A18RuntimeBoundaryTests(unittest.TestCase):
    def test_main_uses_current_a18_runtime(self):
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn("persistent_app_a18", main)

    def test_a18_extends_a17_instead_of_replacing_it(self):
        a18 = (ROOT / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        self.assertIn("from .persistent_app_a17 import WorkflowApp as A17WorkflowApp", a18)
        self.assertIn("class WorkflowApp(A17WorkflowApp)", a18)

    def test_version_boundary_matches_a18(self):
        self.assertEqual(VERSION, "0.1.2-a18")


if __name__ == "__main__":
    unittest.main()
