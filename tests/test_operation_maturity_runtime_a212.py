import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OperationMaturityRuntimeA212Tests(unittest.TestCase):
    def test_runtime_settings_dialog_has_text_values_only(self):
        text = (ROOT / "gui" / "settings_dialog.py").read_text(encoding="utf-8")
        self.assertIn('text="Vis operasjoner"', text)
        self.assertIn("values=list(VISIBILITY_LABELS.values())", text)
        self.assertNotIn('values=["0", "1", "2"]', text)
        self.assertNotIn("0 = alle | 1 = beta + ok | 2 = kun ok/stabil", text)
        self.assertIn('"operation_visibility": visibility_value(self.visibility_var.get())', text)

    def test_runtime_workflow_displays_maturity(self):
        text = (ROOT / "gui" / "workflow_panel.py").read_text(encoding="utf-8")
        self.assertIn("maturity_short_label(op_id)", text)
        self.assertIn('({maturity_short_label(op_id)}) {operation.definition.name}', text)

    def test_runtime_palette_displays_maturity(self):
        text = (ROOT / "gui" / "operations_panel.py").read_text(encoding="utf-8")
        self.assertIn("maturity_label(operation.definition.operation_id)", text)


if __name__ == "__main__":
    unittest.main()
