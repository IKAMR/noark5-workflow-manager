import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class A25Tests(unittest.TestCase):
    def test_portable_settings_moved(self):
        self.assertFalse((ROOT / "settings_portable.py").exists())
        self.assertTrue((ROOT / "app" / "settings_portable.py").is_file())

    def test_config_files_are_in_config_folder(self):
        self.assertTrue((ROOT / "config" / "config_example.json").is_file())
        data = json.loads((ROOT / "config" / "operations.json").read_text(encoding="utf-8"))
        self.assertEqual(data["maturity_levels"]["alpha"], 0)
        self.assertEqual(data["maturity_levels"]["stable"], 2)

    def test_dias_target_uses_full_width_and_own_button_row(self):
        text = (ROOT / "gui" / "dias_dialog_a24.py").read_text(encoding="utf-8")
        self.assertIn('columnspan=2, padx=10, pady=(0, 4), sticky="ew"', text)
        self.assertIn('text="Velg mappe…"', text)
        self.assertIn('row=2, column=0, columnspan=2', text)
        self.assertIn('wrap="char"', text)

    def test_plans_are_documented(self):
        text = (ROOT / "docs" / "TODO-ROADMAP.md").read_text(encoding="utf-8")
        self.assertIn("Alle (inkl. Alpha)", text)
        self.assertIn("run-ID", text)
        self.assertIn("kort label", text)

if __name__ == "__main__":
    unittest.main()
