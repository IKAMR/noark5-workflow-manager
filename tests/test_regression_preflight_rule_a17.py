import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RegressionPreflightRuleA17Tests(unittest.TestCase):
    def test_development_requires_scan_of_existing_tests(self):
        text = (ROOT / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8")
        self.assertIn("Obligatorisk regresjonskontroll før kode leveres", text)
        self.assertIn("alle eksisterende tester som refererer til dem", text)
        self.assertIn("oppdateres i **samme delta**", text)

    def test_development_forbids_per_alpha_docs(self):
        text = (ROOT / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8")
        self.assertIn("permanente `Axx-*.md`-/alpha-dokumenter", text)
        self.assertIn("kanoniske dokumenter", text)

    def test_method_observation_records_recurring_failure_pattern(self):
        text = (ROOT / "docs" / "METHOD-OBSERVATIONS.md").read_text(encoding="utf-8")
        self.assertIn("MO-010", text)
        self.assertIn("regresjons-preflight", text)
        self.assertIn("IKAMR/incremental-ai-development-method", text)


if __name__ == "__main__":
    unittest.main()
