from pathlib import Path
import tempfile
import unittest

from noark5_workflow.core.job import JobBatch
from noark5_workflow.core.job_store import load_job_list, save_job_list

ROOT=Path(__file__).resolve().parents[1]

class A15Fix5BlankJobFlowTests(unittest.TestCase):
    def test_blank_job_is_valid_model_state(self):
        batch=JobBatch(); job=batch.new_job(None)
        self.assertIsNone(job.source_root)
        self.assertIsNone(job.active_extraction_root)
        self.assertEqual("JOB-001",job.name)

    def test_blank_job_roundtrip_in_v3_job_list(self):
        batch=JobBatch(); batch.new_job(None)
        with tempfile.TemporaryDirectory() as tmp:
            path=save_job_list(Path(tmp)/"blank.n5jobs",batch,active_job_id="JOB-001")
            loaded=load_job_list(path)
            self.assertIsNone(loaded.batch.jobs()[0].source_root)

    def test_open_blank_job_does_not_render_none_as_source(self):
        text=(ROOT/"gui"/"persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn("if extraction is None:",text)
        self.assertIn('self.source_panel.path_var.set("")',text)

    def test_new_job_window_does_not_open_source_folder_picker(self):
        text=(ROOT/"gui"/"jobs_window_a15.py").read_text(encoding="utf-8")
        self.assertNotIn("askdirectory",text)
        self.assertIn("self.on_create_job(None)",text)

    def test_new_job_opens_storage_roles(self):
        text=(ROOT/"gui"/"persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn("self.after(0, lambda j=job: self._show_storage_roles(j))",text)

    def test_storage_roles_do_not_require_source(self):
        text=(ROOT/"gui"/"persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn('"Opprett eller åpne en jobb før mapper konfigureres."',text)
        self.assertNotIn('"Velg en source før mapper konfigureres."',text)

    def test_source_location_dialog_is_single_instance(self):
        text=(ROOT/"gui"/"source_panel.py").read_text(encoding="utf-8")
        self.assertIn("self._location_dialog.winfo_exists()",text)
        self.assertIn("self._location_dialog=dialog",text)

    def test_storage_roles_dialog_is_single_instance(self):
        text=(ROOT/"gui"/"persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn("existing.winfo_exists()",text)
        self.assertIn("self._storage_roles_dialog = dialog",text)

if __name__=="__main__": unittest.main()
