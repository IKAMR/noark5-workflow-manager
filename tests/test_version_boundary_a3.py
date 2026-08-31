import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VersionBoundaryA3Tests(unittest.TestCase):
    def test_internal_version_is_a3(self):
        text = (ROOT / "version.py").read_text(encoding="utf-8")
        self.assertIn('VERSION = "0.1.2-a3"', text)

    def test_alpha_state_documents_are_not_permanent(self):
        self.assertFalse((ROOT / "docs" / "V0.1.2-A2-STATE.md").exists())
        self.assertFalse((ROOT / "docs" / "V0.1.2-A3-STATE.md").exists())


if __name__ == "__main__":
    unittest.main()
