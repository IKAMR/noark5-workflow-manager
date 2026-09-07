from pathlib import Path
import unittest
import settings

ROOT=Path(__file__).resolve().parents[1]


class A15JobIdentityStorageReorderTests(unittest.TestCase):
    def test_source_change_never_implicitly_creates_job(self):
        text=(ROOT/"gui"/"persistent_app_a13.py").read_text(encoding="utf-8")
        start=text.index("def _ensure_job_for_current_source")
        end=text.index("def _open_job",start)
        block=text[start:end]
        self.assertNotIn("self.jobs.new_job(",block)
        self.assertIn("never create a new job implicitly",block)

    def test_open_job_renders_active_extraction_not_source_root(self):
        text=(ROOT/"gui"/"persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn("extraction=job.active_extraction_root",text)
        self.assertIn("self.source_panel.set_path(str(extraction))",text)

    def test_storage_role_history_is_per_role(self):
        self.assertIn("recent_storage_role_paths",settings.DEFAULT_CONFIG)
        text=(ROOT/"gui"/"storage_roles_dialog.py").read_text(encoding="utf-8")
        self.assertIn("def _role_history(self, attr",text)
        self.assertIn("history[attr]",text)

    def test_storage_dialog_does_not_copy_extraction_to_source_root(self):
        text=(ROOT/"gui"/"storage_roles_dialog.py").read_text(encoding="utf-8")
        self.assertIn("Do not invent Source",text)
        self.assertNotIn('values["source_root"]=values["source_extraction"]',text.replace(" ",""))

    def test_workflow_model_can_move_operations(self):
        from noark5_workflow.core.workflow import Workflow
        wf=Workflow()
        wf.add("a"); wf.add("b"); wf.add("c")
        self.assertTrue(wf.move_up("c"))
        self.assertEqual(["a","c","b"],wf.operation_ids())
        self.assertTrue(wf.move_down("a"))
        self.assertEqual(["c","a","b"],wf.operation_ids())

    def test_workflow_panel_has_move_controls(self):
        text=(ROOT/"gui"/"workflow_panel.py").read_text(encoding="utf-8")
        self.assertIn('text="↑"',text)
        self.assertIn('text="↓"',text)
        self.assertIn("on_reorder",text)

    def test_reorder_persists_to_active_job(self):
        text=(ROOT/"gui"/"persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn("self.workflow_panel.on_reorder=self._workflow_reordered",text)
        self.assertIn("job.set_workflow(self.workflow.operation_ids())",text)
        self.assertIn("Workflow endret - klar for ny kjøring",text)


if __name__=="__main__":
    unittest.main()
