from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class A18FinalGuiFlowTests(unittest.TestCase):
    def test_new_job_list_creates_first_job_automatically(self):
        text = (ROOT / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        method = text.split("def _new_job_list", 1)[1].split("def ", 1)[0]
        self.assertIn("super()._new_job_list()", method)
        self.assertIn("self.jobs.new_job(None)", method)
        self.assertIn("job.set_owner_identity", method)
        self.assertIn("self.current_job = job", method)
        self.assertIn("JOB-001 opprettet", method)

    def test_new_job_list_does_not_open_storage_dialog_for_blank_first_job(self):
        text = (ROOT / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        method = text.split("def _new_job_list", 1)[1].split("def ", 1)[0]
        self.assertNotIn("_show_storage_roles", method)
        self.assertNotIn("self._create_job(", method)

    def test_tooltips_are_hidden_on_any_click(self):
        text = (ROOT / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        self.assertIn('self.bind_all("<ButtonPress>", self._hide_workflow_tooltips, add="+")', text)
        self.assertIn("def _hide_workflow_tooltips(self, _event=None)", text)

    def test_setup_still_hides_tooltips_explicitly(self):
        text = (ROOT / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        method = text.split("def _open_settings", 1)[1].split("def ", 1)[0]
        self.assertIn("self._hide_workflow_tooltips()", method)
        self.assertIn("SetupDialog(", method)


if __name__ == "__main__":
    unittest.main()
