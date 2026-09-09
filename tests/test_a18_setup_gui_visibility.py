from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class A18SetupGuiVisibilityTests(unittest.TestCase):
    def test_setup_finds_scrollable_body_recursively(self):
        text = (ROOT / "gui" / "setup_dialog_a18.py").read_text(encoding="utf-8")
        self.assertIn("for child in self._walk_widgets(self):", text)
        self.assertIn("isinstance(child, ctk.CTkScrollableFrame)", text)

    def test_setup_still_contains_all_log_controls(self):
        text = (ROOT / "gui" / "setup_dialog_a18.py").read_text(encoding="utf-8")
        for label in (
            "Tekstlig kjørelogg",
            "JSON-logg",
            "CSV-logg",
            "PREMIS-proveniens",
        ):
            self.assertIn(label, text)

    def test_opening_setup_hides_workflow_tooltips_first(self):
        text = (ROOT / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        self.assertIn("def _hide_workflow_tooltips", text)
        open_settings = text.split("def _open_settings", 1)[1].split("def ", 1)[0]
        self.assertIn("self._hide_workflow_tooltips()", open_settings)
        self.assertIn("SetupDialog(", open_settings)


if __name__ == "__main__":
    unittest.main()
