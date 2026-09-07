from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class A15Fix4RegressionContractsTests(unittest.TestCase):
    def test_workflow_preserves_checkpoint_contract_with_reorder_controls(self):
        text = (ROOT / "gui" / "workflow_panel.py").read_text(encoding="utf-8")
        self.assertIn('text="■" if active_checkpoint else ""', text)
        self.assertIn('f"{row + 1}. ({maturity_short_label(op_id)}) {operation.definition.name}"', text)
        self.assertIn('text="↑"', text)
        self.assertIn('text="↓"', text)

    def test_source_assignment_uses_active_job_without_implicit_new_job(self):
        text = (ROOT / "gui" / "persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn("job.source_extraction = path", text)
        start = text.index("def _ensure_job_for_current_source")
        end = text.index("def _open_job", start)
        self.assertNotIn("self.jobs.new_job(", text[start:end])


if __name__ == "__main__":
    unittest.main()
