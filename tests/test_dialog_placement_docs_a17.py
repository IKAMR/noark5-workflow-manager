import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DialogPlacementDocumentationA17Tests(unittest.TestCase):
    def test_development_locks_dialog_parent_placement_rule(self):
        text = (ROOT / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8")
        self.assertIn("Dialogplassering og fler-skjermsoppsett", text)
        self.assertIn("vinduet som eier eller utløser dem", text)
        self.assertIn("implementeres sentralt og gjenbrukes", text)

    def test_development_requires_practical_multiscreen_test_when_available(self):
        text = (ROOT / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8")
        self.assertIn("fler-skjermsoppsett", text)
        self.assertIn("praktisk testes", text)

    def test_method_observation_records_general_candidate(self):
        text = (ROOT / "docs" / "METHOD-OBSERVATIONS.md").read_text(encoding="utf-8")
        self.assertIn("MO-009", text)
        self.assertIn("aktive arbeidskontekst", text)
        self.assertIn("IKAMR/incremental-ai-development-method", text)


if __name__ == "__main__":
    unittest.main()
