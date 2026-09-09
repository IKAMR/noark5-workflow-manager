import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StorageRoleDialogSingleInstanceA17Tests(unittest.TestCase):
    def test_storage_roles_has_explicit_reentrancy_guard(self):
        text = (ROOT / "gui" / "storage_roles_dialog.py").read_text(encoding="utf-8")
        self.assertIn("self._location_dialog_open = False", text)
        self.assertIn("if self._location_dialog_open:", text)
        self.assertIn("self._location_dialog_open = True", text)

    def test_guard_is_set_before_storage_location_constructor(self):
        text = (ROOT / "gui" / "storage_roles_dialog.py").read_text(encoding="utf-8")
        start = text.index("def _choose")
        guard = text.index("self._location_dialog_open = True", start)
        ctor = text.index("StorageLocationDialog(", start)
        self.assertLess(guard, ctor)

    def test_all_role_choose_buttons_are_disabled_while_chooser_is_open(self):
        text = (ROOT / "gui" / "storage_roles_dialog.py").read_text(encoding="utf-8")
        self.assertIn("self._choose_buttons", text)
        self.assertIn('self._set_choose_buttons_state("disabled")', text)
        self.assertIn('self._set_choose_buttons_state("normal")', text)

    def test_destroy_handler_ignores_child_destroy_events(self):
        text = (ROOT / "gui" / "storage_roles_dialog.py").read_text(encoding="utf-8")
        self.assertIn('getattr(event, "widget", None) is not dialog', text)

    def test_history_remove_reopens_after_current_dialog_closes(self):
        text = (ROOT / "gui" / "storage_roles_dialog.py").read_text(encoding="utf-8")
        self.assertIn("self.after_idle", text)


if __name__ == "__main__":
    unittest.main()
