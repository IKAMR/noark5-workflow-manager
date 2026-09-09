import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourceDialogSingleInstanceA17Tests(unittest.TestCase):
    def test_source_panel_has_explicit_reentrancy_guard(self):
        text = (ROOT / "gui" / "source_panel.py").read_text(encoding="utf-8")
        self.assertIn("self._location_dialog_open=False", text)
        self.assertIn("if self._location_dialog_open:", text)
        self.assertIn("self._location_dialog_open=True", text)

    def test_guard_is_set_before_dialog_constructor(self):
        text = (ROOT / "gui" / "source_panel.py").read_text(encoding="utf-8")
        guard = text.index("self._location_dialog_open=True", text.index("def _browse"))
        ctor = text.index("SourceLocationDialog(", text.index("def _browse"))
        self.assertLess(guard, ctor)

    def test_browse_button_is_disabled_while_dialog_is_open(self):
        text = (ROOT / "gui" / "source_panel.py").read_text(encoding="utf-8")
        self.assertIn('self.browse_button.configure(state="disabled")', text)
        self.assertIn('self.browse_button.configure(state="normal")', text)

    def test_destroy_handler_ignores_child_widget_destroy(self):
        text = (ROOT / "gui" / "source_panel.py").read_text(encoding="utf-8")
        self.assertIn('getattr(event,"widget",None) is not dialog', text)

    def test_single_instance_rule_is_documented(self):
        text = (ROOT / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8")
        self.assertIn("Enkeltinstans for dialoger", text)
        self.assertIn("settes før nytt `Toplevel` konstrueres", text)
        self.assertIn("raske eller gjentatte klikk", text)


if __name__ == "__main__":
    unittest.main()
