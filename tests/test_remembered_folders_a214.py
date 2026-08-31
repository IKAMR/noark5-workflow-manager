import unittest
from pathlib import Path

from settings import DEFAULT_CONFIG

ROOT = Path(__file__).resolve().parents[1]


class RememberedFoldersA214Tests(unittest.TestCase):
    def test_standard_remembered_keys_exist(self):
        expected = {
            "last_noark_source_dir",
            "last_dias_output_dir",
            "last_mets_import_dir",
            "last_dias_add_file_dir",
            "last_dias_add_folder_dir",
            "last_setup_dir",
            "last_job_list_file",
            "last_job_list_dir",
        }
        self.assertTrue(expected.issubset(DEFAULT_CONFIG))

    def test_setup_dialog_remembers_export_and_import_folder(self):
        text = (ROOT / "gui" / "settings_dialog.py").read_text(encoding="utf-8")
        self.assertIn('self.settings.get("last_setup_dir"', text)
        self.assertIn('kwargs["initialdir"] = initialdir', text)
        self.assertIn('save_config({"last_setup_dir": folder})', text)
        self.assertIn("self._remember_setup_dir(path)", text)
        self.assertIn("self._remember_setup_dir(Path(filename))", text)

    def test_job_list_folder_is_a_standard_key(self):
        self.assertIn("last_job_list_dir", DEFAULT_CONFIG)
        self.assertIn("last_job_list_file", DEFAULT_CONFIG)

    def test_documentation_lists_remembered_folders(self):
        # Mappeadferd er en utviklings-/GUI-konvensjon, ikke en interface-kontrakt.
        text = (ROOT / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8")
        self.assertIn("## Innstillinger og mappeadferd", text)
        self.assertIn("last_setup_dir", text)
        self.assertIn("last_job_list_dir", text)


if __name__ == "__main__":
    unittest.main()
