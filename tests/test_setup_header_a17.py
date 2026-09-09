import unittest
from pathlib import Path

from gui.ui_contract_a17 import HEADER_ACTIONS, SETUP_TITLE, TEMP_DIRECTORY_IN_SETUP

ROOT = Path(__file__).resolve().parents[1]


class SetupHeaderA17Tests(unittest.TestCase):
    def test_header_contract_uses_one_dedicated_action_frame(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        self.assertEqual(
            HEADER_ACTIONS,
            ("Mapper", "Jobber", "Setup", "A-", "A+", "?"),
        )
        self.assertIn("self._a17_header_actions = actions", text)
        self.assertIn("HEADER_ACTIONS", text)

    def test_setup_temp_row_has_visible_entry_and_browse_button(self):
        text = (ROOT / "gui" / "setup_dialog_a17.py").read_text(encoding="utf-8")
        self.assertEqual(SETUP_TITLE, "Setup")
        self.assertTrue(TEMP_DIRECTORY_IN_SETUP)
        self.assertIn("class SetupDialog(SettingsDialog)", text)
        self.assertIn("self.title(SETUP_TITLE)", text)
        self.assertIn("row = ctk.CTkFrame(parent", text)
        self.assertIn("temp_var_name = str(self.temp_var)", text)
        self.assertIn("textvariable=self.temp_var", text)
        self.assertIn("command=self._browse_temp_dir", text)
        self.assertIn("filedialog.askdirectory", text)

    def test_a17_uses_setup_dialog(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        self.assertIn("from .setup_dialog_a17 import SetupDialog", text)
        self.assertIn("SetupDialog(self, self.settings, self._save_settings)", text)


if __name__ == "__main__":
    unittest.main()
