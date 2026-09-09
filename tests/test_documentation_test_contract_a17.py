import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DocumentationTestContractA17Tests(unittest.TestCase):
    def test_development_forbids_brittle_documentation_wording_tests(self):
        text = (ROOT / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8")
        self.assertIn("Tester av dokumentasjon skal ikke feile på tilfeldige ordvalg", text)
        self.assertIn("stabile overskrifter, kontraktsbegreper og nødvendige regler", text)
        self.assertIn("eksakt formulering brukes bare når ordlyden i seg selv er kontrakten", text)


if __name__ == "__main__":
    unittest.main()
