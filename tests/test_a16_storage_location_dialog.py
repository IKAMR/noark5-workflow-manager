from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class A16StorageLocationDialogTests(unittest.TestCase):
    def test_common_location_dialog_exists(self):
        text = (ROOT / "gui" / "source_location_dialog.py").read_text(encoding="utf-8")
        self.assertIn("class StorageLocationDialog", text)
        self.assertIn("class LocationChoice", text)

    def test_source_chooser_reuses_common_dialog(self):
        text = (ROOT / "gui" / "source_location_dialog.py").read_text(encoding="utf-8")
        self.assertIn("class SourceLocationDialog(StorageLocationDialog)", text)

    def test_storage_roles_use_common_chooser_before_native_dialog(self):
        text = (ROOT / "gui" / "storage_roles_dialog.py").read_text(encoding="utf-8")
        self.assertIn("StorageLocationDialog", text)
        self.assertNotIn("filedialog.askdirectory", text)
        self.assertNotIn("filedialog.askopenfilename", text)

    def test_role_chooser_shows_current_suggestions_and_history(self):
        text = (ROOT / "gui" / "storage_roles_dialog.py").read_text(encoding="utf-8")
        self.assertIn('LocationChoice("Gjeldende"', text)
        self.assertIn('LocationChoice("Forslag"', text)
        self.assertIn('LocationChoice("Sist brukt"', text)

    def test_work_role_suggestions_are_nonbinding(self):
        text = (ROOT / "gui" / "storage_roles_dialog.py").read_text(encoding="utf-8")
        self.assertIn('work_root / "content"', text)
        self.assertIn('work_root / "repository_operations"', text)
        self.assertIn('work_root / "aip"', text)
        self.assertIn("never write these without user choice", text)

    def test_history_can_be_removed_per_role(self):
        text = (ROOT / "gui" / "storage_roles_dialog.py").read_text(encoding="utf-8")
        self.assertIn("def _forget_role", text)
        self.assertIn('history[attr] = values', text)

    def test_only_one_role_location_dialog_is_open(self):
        text = (ROOT / "gui" / "storage_roles_dialog.py").read_text(encoding="utf-8")
        self.assertIn("self._location_dialog", text)
        self.assertIn("self._location_dialog.winfo_exists()", text)


if __name__ == "__main__":
    unittest.main()
