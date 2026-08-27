from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import settings


class RecentFolderSettingsTests(unittest.TestCase):
    def test_recent_folder_keys_have_defaults(self):
        for key in (
            "last_noark_source_dir",
            "last_dias_output_dir",
            "last_mets_import_dir",
            "last_dias_add_file_dir",
            "last_dias_add_folder_dir",
        ):
            self.assertIn(key, settings.DEFAULT_CONFIG)
            self.assertEqual(settings.DEFAULT_CONFIG[key], "")

    def test_recent_folders_roundtrip(self):
        old_path = settings.CONFIG_PATH
        try:
            with tempfile.TemporaryDirectory() as tmp:
                settings.CONFIG_PATH = Path(tmp) / "config.json"
                settings.save_config({
                    "last_noark_source_dir": r"C:\\archive\\noark5",
                    "last_dias_output_dir": r"D:\\dias",
                })
                loaded = settings.load_config()
                self.assertEqual(loaded["last_noark_source_dir"], r"C:\\archive\\noark5")
                self.assertEqual(loaded["last_dias_output_dir"], r"D:\\dias")
        finally:
            settings.CONFIG_PATH = old_path


if __name__ == "__main__":
    unittest.main()
