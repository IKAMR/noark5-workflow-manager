from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VersionBoundaryA3Tests(unittest.TestCase):
    def test_internal_version_is_a12(self):
        text = (ROOT / "version.py").read_text(encoding="utf-8")
        self.assertIn('VERSION = "0.1.2-a12"', text)

    def test_alpha_state_documents_are_not_permanent(self):
        docs = ROOT / "docs"
        permanent_alpha_docs = [
            path.name
            for path in docs.glob("*a*.md")
            if path.name.lower().startswith(("a1", "a2", "a3"))
        ]
        self.assertEqual(permanent_alpha_docs, [])


if __name__ == "__main__":
    unittest.main()
