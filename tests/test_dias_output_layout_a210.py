import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class DiasOutputLayoutA210Tests(unittest.TestCase):
    def test_button_and_path_are_same_row(self):
        text = (ROOT / "gui" / "dias_dialog.py").read_text(encoding="utf-8")
        self.assertIn("self.choose_output_button.grid(", text)
        self.assertIn('row=0, column=0', text)
        self.assertIn("self.output_display.grid(", text)
        self.assertIn('row=0, column=1', text)

    def test_path_column_expands(self):
        text = (ROOT / "gui" / "dias_dialog.py").read_text(encoding="utf-8")
        self.assertIn("self.output_row.grid_columnconfigure(1, weight=1)", text)
        self.assertIn('wrap="char"', text)

    def test_mets_is_below_output_row(self):
        text = (ROOT / "gui" / "dias_dialog.py").read_text(encoding="utf-8")
        self.assertIn('mets_row.grid(row=2, column=0, columnspan=2', text)

    def test_no_self_import_regression(self):
        text = (ROOT / "gui" / "dias_dialog.py").read_text(encoding="utf-8")
        self.assertNotIn("from .dias_dialog import", text)

if __name__ == "__main__":
    unittest.main()
