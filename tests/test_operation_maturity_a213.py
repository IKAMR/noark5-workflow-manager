import unittest
from pathlib import Path

from app.operation_metadata import maturity_short_label

ROOT = Path(__file__).resolve().parents[1]


class OperationMaturityA213Tests(unittest.TestCase):
    def test_legacy_settings_import_routes_to_current_dialog(self):
        text = (ROOT / "gui" / "settings_dialog_a23.py").read_text(encoding="utf-8")
        self.assertIn("from .settings_dialog import SettingsDialog", text)

    def test_runtime_settings_dialog_has_text_choices(self):
        text = (ROOT / "gui" / "settings_dialog.py").read_text(encoding="utf-8")
        self.assertIn("values=list(VISIBILITY_LABELS.values())", text)
        self.assertNotIn('values=["0", "1", "2"]', text)
        self.assertNotIn("0 = alle | 1 = beta + ok | 2 = kun ok/stabil", text)

    def test_maturity_short_codes(self):
        self.assertEqual(maturity_short_label("dias_package"), "S")

    def test_workflow_uses_compact_maturity_prefix(self):
        text = (ROOT / "gui" / "workflow_panel.py").read_text(encoding="utf-8")
        self.assertIn("maturity_short_label", text)
        self.assertIn('f"{row + 1}. ({maturity_short_label(op_id)}) {operation.definition.name}"', text)
        self.assertNotIn(" · {maturity_label(op_id)}", text)


if __name__ == "__main__":
    unittest.main()
