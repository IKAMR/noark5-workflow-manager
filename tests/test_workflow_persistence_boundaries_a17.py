import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WorkflowPersistenceBoundariesA17Tests(unittest.TestCase):
    def test_runtime_imports_jobstatus_used_by_workflow_change(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        self.assertIn("from noark5_workflow.core.job import JobStatus", text)

    def test_workflow_change_writes_synchronously(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        start = text.index("def _workflow_changed")
        end = text.index("def _open_job", start)
        method = text[start:end]
        self.assertIn("self._persist_active_job_state", method)
        self.assertNotIn("self.after_idle", method)

    def test_leaving_job_is_persisted_before_super_opens_next_job(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        start = text.index("def _open_job(self, job)")
        end = text.index("def _close_with_persistence", start)
        method = text[start:end]
        before = method.index("self._persist_active_job_state()")
        open_next = method.index("super()._open_job(job)")
        self.assertLess(before, open_next)

    def test_close_persists_before_destroy(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        start = text.index("def _close_with_persistence")
        end = text.index("def _show_raw_results", start)
        method = text[start:end]
        self.assertLess(method.index("self._persist_active_job_state()"), method.index("self.destroy()"))

    def test_development_documents_both_persistence_boundaries(self):
        text = (ROOT / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8")
        self.assertIn("Jobbskifte er en eksplisitt persistensgrense", text)
        self.assertIn("Applikasjonslukking er en eksplisitt persistensgrense", text)
        self.assertIn("ikke være avhengig av `after_idle`", text)


if __name__ == "__main__":
    unittest.main()
