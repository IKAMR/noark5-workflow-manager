import unittest
from pathlib import Path

from noark5_workflow.core.job import JobBatch, JobStatus

ROOT = Path(__file__).resolve().parents[1]


class JobListResetA17Tests(unittest.TestCase):
    def test_unused_last_draft_releases_its_number(self):
        batch = JobBatch()
        j1 = batch.new_job()
        j2 = batch.new_job()
        self.assertEqual(j1.job_id, "JOB-001")
        self.assertEqual(j2.job_id, "JOB-002")
        self.assertTrue(batch.remove(j2.job_id))
        self.assertEqual(batch.new_job().job_id, "JOB-002")

    def test_profile_only_draft_can_release_its_number(self):
        batch = JobBatch()
        batch.new_job()
        draft = batch.new_job()
        draft.profile_id = "noark5"
        self.assertTrue(draft.is_unused_draft())
        batch.remove(draft.job_id)
        self.assertEqual(batch.new_job().job_id, "JOB-002")

    def test_configured_job_number_is_not_reused(self):
        batch = JobBatch()
        batch.new_job()
        configured = batch.new_job()
        configured.source_extraction = Path("C:/example/extraction")
        self.assertFalse(configured.is_unused_draft())
        batch.remove(configured.job_id)
        self.assertEqual(batch.new_job().job_id, "JOB-003")

    def test_workflow_job_number_is_not_reused(self):
        batch = JobBatch()
        batch.new_job()
        configured = batch.new_job(workflow_ids=["validate_xml_schema"])
        batch.remove(configured.job_id)
        self.assertEqual(batch.new_job().job_id, "JOB-003")

    def test_executed_job_number_is_not_reused(self):
        batch = JobBatch()
        batch.new_job()
        executed = batch.new_job()
        executed.status = JobStatus.OK
        executed.message = "Workflow fullført"
        batch.remove(executed.job_id)
        self.assertEqual(batch.new_job().job_id, "JOB-003")

    def test_middle_hole_is_never_reused(self):
        batch = JobBatch()
        batch.new_job()  # 001
        middle = batch.new_job()  # 002, unused
        batch.new_job()  # 003
        batch.remove(middle.job_id)
        self.assertEqual(batch.new_job().job_id, "JOB-004")

    def test_clear_creates_new_identity_context_at_job_001(self):
        batch = JobBatch()
        batch.new_job()
        batch.new_job()
        batch.clear()
        self.assertEqual(batch.new_job().job_id, "JOB-001")

    def test_last_job_cannot_be_deleted_individually_in_gui(self):
        text = (ROOT / "gui" / "jobs_window_a17.py").read_text(encoding="utf-8")
        self.assertIn("if len(jobs) == 1", text)
        self.assertIn("Bruk «Ny jobbliste»", text)

    def test_new_job_list_clears_visible_log(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        self.assertIn("self.log_panel.clear()", text)
        self.assertIn("self.jobs.clear()", text)
        self.assertIn("neste jobb blir JOB-001", text)

    def test_reset_contract_is_documented_in_development(self):
        text = (ROOT / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8")
        self.assertIn("Jobbidentitet og full reset av jobbliste", text)
        self.assertIn("ubrukt kladdejobb", text)
        self.assertIn("siste/høyeste opprettede jobbnummeret", text)
        self.assertIn("Hull i midten av en eksisterende jobbliste fylles aldri automatisk", text)

    def test_reset_does_not_claim_disk_history_is_deleted(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        self.assertIn("Persistente kjørelogger, råresultater og PREMIS-filer på disk slettes ikke.", text)


if __name__ == "__main__":
    unittest.main()
