import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ActiveJobListStatusA17Tests(unittest.TestCase):
    def test_status_bar_left_field_defaults_to_unsaved_job_list(self):
        text = (ROOT / "gui" / "status_bar.py").read_text(encoding="utf-8")
        self.assertIn('value="Jobbliste: [ikke lagret]"', text)
        self.assertIn("def set_job_list", text)
        self.assertIn('self.left_var.set(f"Jobbliste: {Path(path)}")', text)

    def test_temp_is_no_longer_persistent_left_context(self):
        text = (ROOT / "gui" / "status_bar.py").read_text(encoding="utf-8")
        self.assertIn("def set_temp", text)
        self.assertIn("Backward-compatible no-op", text)
        self.assertNotIn('self.left_var.set(f"Temp:', text)

    def test_restart_refreshes_restored_job_list_path(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        init = text.index("def __init__")
        super_init = text.index("super().__init__()", init)
        refresh = text.index("self._refresh_job_list_status()", super_init)
        self.assertGreater(refresh, super_init)

    def test_open_write_and_reset_refresh_job_list_status(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        self.assertIn("def _load_job_list_file", text)
        self.assertIn("if loaded:\n            self._refresh_job_list_status()", text)
        self.assertIn("if written:\n            self._refresh_job_list_status()", text)
        self.assertIn("self.job_list_path = None\n        self._refresh_job_list_status()", text)

    def test_contract_is_documented(self):
        text = (ROOT / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8")
        self.assertIn("Statuslinje og aktiv jobbliste", text)
        self.assertIn("aktive autoritative jobblistefilen", text)
        self.assertIn("Jobbliste: [ikke lagret]", text)
        self.assertIn("Temp-katalog er konfigurasjon", text)


if __name__ == "__main__":
    unittest.main()
