import json
import unittest
from pathlib import Path

from app.operation_metadata import (
    is_visible,
    maturity_label,
    maturity_level,
    visibility_label,
    visibility_value,
)

ROOT = Path(__file__).resolve().parents[1]


class OperationMaturityA212Tests(unittest.TestCase):
    def test_config_is_generic_and_dias_is_stable(self):
        path = ROOT / "config" / "operations.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["operations"]["dias_package"]["maturity"], "stable")
        self.assertFalse((ROOT / "noark5_workflow" / "operations.json").exists())

    def test_maturity_mapping(self):
        self.assertEqual(maturity_level("dias_package"), 2)
        self.assertEqual(maturity_label("dias_package"), "Stabil")
        self.assertTrue(is_visible("dias_package", 2))

    def test_unknown_operation_defaults_to_alpha(self):
        self.assertEqual(maturity_level("unknown_operation"), 0)
        self.assertEqual(maturity_label("unknown_operation"), "Alpha")
        self.assertTrue(is_visible("unknown_operation", 0))
        self.assertFalse(is_visible("unknown_operation", 1))

    def test_visibility_labels_roundtrip(self):
        for value in (0, 1, 2):
            self.assertEqual(visibility_value(visibility_label(value)), value)

    def test_settings_dialog_uses_friendly_labels(self):
        text = (ROOT / "gui" / "settings_dialog.py").read_text(encoding="utf-8")
        self.assertIn('text="Vis operasjoner"', text)
        self.assertIn("list(VISIBILITY_LABELS.values())", text)
        self.assertNotIn('values=["0", "1", "2"]', text)

    def test_palette_and_workflow_show_maturity(self):
        palette = (ROOT / "gui" / "operations_panel.py").read_text(encoding="utf-8")
        workflow = (ROOT / "gui" / "workflow_panel.py").read_text(encoding="utf-8")
        self.assertIn("maturity_label(operation.definition.operation_id)", palette)
        self.assertIn("is_visible(op.definition.operation_id, minimum)", palette)
        self.assertIn("maturity_short_label(op_id)", workflow)


if __name__ == "__main__":
    unittest.main()
