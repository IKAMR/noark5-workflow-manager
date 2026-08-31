import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VersionBoundaryA3Tests(unittest.TestCase):
    def test_internal_version_is_a5(self):
        text = (ROOT / "version.py").read_text(encoding="utf-8")
        self.assertIn('VERSION = "0.1.2-a5"', text)

    def test_alpha_state_documents_are_not_permanent(self):
        for alpha in ("A2", "A3", "A4", "A5"):
            self.assertFalse((ROOT / "docs" / f"V0.1.2-{alpha}-STATE.md").exists())


if __name__ == "__main__":
    unittest.main()
