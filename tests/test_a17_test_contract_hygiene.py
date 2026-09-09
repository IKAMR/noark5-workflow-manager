import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

SUPERSEDED_A17_TEST_TOKENS = (
    "_ensure_jobs_button_visible",
    '"Mapper": 4',
    '"Jobber": 5',
    '"Setup": 6',
    "unik grid-kolonne",
)


class A17TestContractHygieneTests(unittest.TestCase):
    def test_a17_tests_do_not_lock_superseded_header_implementation_details(self):
        offenders = []
        for path in sorted(TESTS.glob("test_*a17.py")):
            if path.name == Path(__file__).name:
                continue
            text = path.read_text(encoding="utf-8")
            for token in SUPERSEDED_A17_TEST_TOKENS:
                if token in text:
                    offenders.append(f"{path.name}: {token}")
        self.assertEqual(
            offenders,
            [],
            "Foreldede a17 testkontrakter funnet:\n" + "\n".join(offenders),
        )

    def test_stable_ui_contract_module_exists(self):
        text = (ROOT / "gui" / "ui_contract_a17.py").read_text(encoding="utf-8")
        self.assertIn("HEADER_ACTIONS", text)
        self.assertIn("HEADER_LAYOUT_KIND", text)
        self.assertIn("TEMP_DIRECTORY_IN_SETUP", text)
        self.assertIn("RESULTS_ACTION_LOCATION", text)


if __name__ == "__main__":
    unittest.main()
