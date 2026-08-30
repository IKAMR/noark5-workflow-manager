import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class DiasOutputLayoutA211Tests(unittest.TestCase):
    def test_button_and_path_share_same_parent_and_row(self):
        text = (ROOT / "gui" / "dias_dialog.py").read_text(encoding="utf-8")
        self.assertIn("self.output_row = ctk.CTkFrame", text)
        self.assertIn("self.choose_output_button = ctk.CTkButton(\n            self.output_row,", text)
        self.assertIn("self.output_display = ctk.CTkTextbox(\n            self.output_row,", text)
        self.assertIn("self.choose_output_button.grid(\n            row=0, column=0", text)
        self.assertIn("self.output_display.grid(\n            row=0, column=1", text)

    def test_mets_row_is_separate_below(self):
        text = (ROOT / "gui" / "dias_dialog.py").read_text(encoding="utf-8")
        self.assertIn('mets_row.grid(row=2, column=0, columnspan=2', text)

    def test_no_self_import(self):
        text = (ROOT / "gui" / "dias_dialog.py").read_text(encoding="utf-8")
        self.assertNotIn("from .dias_dialog import", text)

if __name__ == "__main__":
    unittest.main()
