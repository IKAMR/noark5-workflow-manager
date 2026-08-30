import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class DiasOutputLayoutA27Tests(unittest.TestCase):
    def test_choose_button_is_left_of_path(self):
        text = (ROOT / "gui" / "dias_dialog.py").read_text(encoding="utf-8")
        self.assertIn("self.output_row = ctk.CTkFrame", text)
        self.assertIn("self.choose_output_button = ctk.CTkButton", text)
        self.assertIn("self.output_display = ctk.CTkTextbox", text)
        self.assertLess(
            text.index("self.choose_output_button = ctk.CTkButton"),
            text.index("self.output_display = ctk.CTkTextbox"),
        )

    def test_path_uses_remaining_width_and_wraps(self):
        text = (ROOT / "gui" / "dias_dialog.py").read_text(encoding="utf-8")
        self.assertIn("self.output_row.grid_columnconfigure(1, weight=1)", text)
        self.assertIn('wrap="char"', text)
        self.assertIn("row=0, column=1", text)

if __name__ == "__main__":
    unittest.main()
