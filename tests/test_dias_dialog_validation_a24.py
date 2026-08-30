import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DiasDialogValidationA24Tests(unittest.TestCase):
    def test_target_is_displayed_on_two_lines(self):
        text = (ROOT / "gui" / "dias_dialog_a24.py").read_text(encoding="utf-8")
        self.assertIn("self.output_display = ctk.CTkTextbox", text)
        self.assertIn("height=58", text)
        self.assertIn('wrap="char"', text)
        self.assertIn("def _refresh_output_display", text)

    def test_dialog_stays_open_when_job_validation_rejects(self):
        text = (ROOT / "gui" / "dias_dialog_a24.py").read_text(encoding="utf-8")
        self.assertIn("accepted = self.on_confirm(values)", text)
        self.assertIn("if accepted is False:", text)
        self.assertIn("self.destroy()", text)

    def test_callbacks_return_boolean_acceptance(self):
        text = (ROOT / "gui" / "persistent_app.py").read_text(encoding="utf-8")
        self.assertIn("def add_configured(params: dict) -> bool:", text)
        self.assertIn("def save_changes(params: dict) -> bool:", text)
        self.assertIn("return False", text)
        self.assertIn("return True", text)

    def test_a24_dialog_is_used(self):
        text = (ROOT / "gui" / "persistent_app.py").read_text(encoding="utf-8")
        self.assertIn("from .dias_dialog_a24 import DiasParamDialog", text)


if __name__ == "__main__":
    unittest.main()
