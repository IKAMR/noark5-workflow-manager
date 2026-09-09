import unittest
from pathlib import Path

from gui.ui_contract_a17 import (
    HEADER_ACTIONS,
    HEADER_LAYOUT_KIND,
    SETUP_TITLE,
    TEMP_DIRECTORY_IN_SETUP,
)

ROOT = Path(__file__).resolve().parents[1]


class HeaderWorkflowAutosaveA17Tests(unittest.TestCase):
    def test_header_actions_use_one_deterministic_action_strip(self):
        self.assertEqual(
            HEADER_ACTIONS,
            ("Mapper", "Jobber", "Setup", "A-", "A+", "?"),
        )
        self.assertEqual(HEADER_LAYOUT_KIND, "dedicated-action-frame")

        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        self.assertIn("HEADER_ACTIONS", text)
        self.assertIn("self._a17_header_actions = actions", text)
        self.assertIn("implemented_actions != HEADER_ACTIONS", text)

    def test_workflow_user_edits_have_generic_change_hook(self):
        text = (ROOT / "gui" / "workflow_change_hooks.py").read_text(encoding="utf-8")
        self.assertIn('changed("add", operation_id)', text)
        self.assertIn('changed("remove", operation_id)', text)
        self.assertIn('changed("clear", None)', text)

    def test_autosave_is_immediate_and_not_after_idle_dependent(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        start = text.index("def _workflow_changed")
        end = text.index("def _open_job", start)
        method = text[start:end]
        self.assertIn("self._sync_active_workflow_to_job()", method)
        self.assertIn("self._persist_active_job_state", method)

        # Test executable behavior, not explanatory comments.
        code_only = "\n".join(
            line for line in method.splitlines()
            if not line.lstrip().startswith("#")
        )
        self.assertNotIn("self.after_idle(", code_only)

    def test_job_switch_and_close_are_persistence_boundaries(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        self.assertIn("def _open_job(self, job)", text)
        self.assertIn("def _close_with_persistence", text)
        self.assertIn('self.protocol("WM_DELETE_WINDOW", self._close_with_persistence)', text)

    def test_unsaved_job_list_is_not_created_implicitly(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        self.assertIn("if self.job_list_path is None:", text)

    def test_contracts_are_documented_semantically(self):
        text = (ROOT / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8")
        self.assertIn("Automatisk lagring av workflow-oppsett", text)
        self.assertIn("Stabil header-layout", text)
        for label in ("Mapper", "Jobber", "Setup"):
            self.assertIn(label, text)
        self.assertIn("dedikert header-frame", text)
        self.assertEqual(SETUP_TITLE, "Setup")
        self.assertTrue(TEMP_DIRECTORY_IN_SETUP)


if __name__ == "__main__":
    unittest.main()
