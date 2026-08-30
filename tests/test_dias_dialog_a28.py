import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class DiasDialogA28RegressionTests(unittest.TestCase):
    def test_dialog_is_standalone_and_has_no_self_import(self):
        text = (ROOT / "gui" / "dias_dialog.py").read_text(encoding="utf-8")
        self.assertNotIn("from .dias_dialog import", text)
        self.assertNotIn("dias_dialog_a23", text)
        self.assertNotIn("dias_dialog_a24", text)
        self.assertIn("_FIELDS = [", text)
        self.assertIn("class DiasParamDialog", text)

    def test_output_layout_is_button_left_path_right(self):
        text = (ROOT / "gui" / "dias_dialog.py").read_text(encoding="utf-8")
        b = text.index('text="Velg mappe…"')
        p = text.index("self.output_display = ctk.CTkTextbox")
        self.assertLess(b, p)
        self.assertIn("self.output_row.grid_columnconfigure(1, weight=1)", text)
        self.assertIn('wrap="char"', text)

    def test_rejected_callback_does_not_close_dialog(self):
        text = (ROOT / "gui" / "dias_dialog.py").read_text(encoding="utf-8")
        self.assertIn("accepted = self.on_confirm(values)", text)
        self.assertIn("if accepted is False:", text)

if __name__ == "__main__":
    unittest.main()
