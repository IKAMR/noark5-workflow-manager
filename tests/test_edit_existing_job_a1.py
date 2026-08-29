import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EditExistingJobA1RegressionTests(unittest.TestCase):
    def test_workflow_panel_exposes_edit_for_configurable_operations(self):
        text = (ROOT / "gui" / "workflow_panel.py").read_text(encoding="utf-8")
        self.assertIn('text="Rediger"', text)
        self.assertIn("self.on_edit", text)
        self.assertIn("callable(configure)", text)

    def test_persistent_app_edits_existing_dias_configuration(self):
        text = (ROOT / "gui" / "persistent_app.py").read_text(encoding="utf-8")
        self.assertIn("def _edit_operation", text)
        self.assertIn("job.get_operation_params(operation_id)", text)
        self.assertIn("job.set_operation_params(operation_id, params)", text)
        self.assertIn("DiasParamDialog(self, initial_params", text)

    def test_edit_of_completed_job_marks_it_ready_for_rerun(self):
        text = (ROOT / "gui" / "persistent_app.py").read_text(encoding="utf-8")
        self.assertIn("job.status = JobStatus.READY", text)
        self.assertIn("Konfigurasjon endret - klar for ny kjøring", text)

    def test_rerun_requires_explicit_confirmation(self):
        text = (ROOT / "gui" / "persistent_app.py").read_text(encoding="utf-8")
        self.assertIn("def _confirm_rerun", text)
        self.assertIn("Tidligere resultatmapper slettes ikke", text)
        self.assertIn("super()._run_workflow()", text)
        self.assertIn("super()._start_all_jobs()", text)


if __name__ == "__main__":
    unittest.main()
