import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FinalSmallFixesA17Tests(unittest.TestCase):
    def test_same_profile_selection_is_explicit_noop(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        start = text.index("def _profile_selected")
        end = text.index("def _sync_active_workflow_to_job", start)
        method = text[start:end]
        self.assertIn("current_job.profile_id", method)
        self.assertIn("if profile_id == current_profile", method)
        self.assertIn("return", method)
        self.assertIn("super()._profile_selected(label)", method)

    def test_temp_browse_finds_entry_by_temp_stringvar(self):
        text = (ROOT / "gui" / "setup_dialog_a17.py").read_text(encoding="utf-8")
        self.assertIn("temp_var_name = str(self.temp_var)", text)
        self.assertIn('child.cget("textvariable")', text)
        self.assertIn("parent = temp_entry.master", text)
        self.assertIn("temp_entry.grid_forget()", text)
        self.assertIn("command=self._browse_temp_dir", text)
        self.assertIn("filedialog.askdirectory", text)


if __name__ == "__main__":
    unittest.main()
