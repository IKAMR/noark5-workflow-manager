import unittest
from pathlib import Path

from noark5_workflow.core.job import JobBatch, JobStatus


class UnusedDraftIdentityA17Tests(unittest.TestCase):
    def test_empty_default_job_is_unused_draft(self):
        batch = JobBatch()
        self.assertTrue(batch.new_job().is_unused_draft())

    def test_profile_selection_alone_keeps_draft_disposable(self):
        batch = JobBatch()
        job = batch.new_job()
        job.profile_id = "siard"
        self.assertTrue(job.is_unused_draft())

    def test_any_storage_role_makes_job_significant(self):
        attrs = (
            "source_root", "source_tar", "source_unzipped", "source_extraction",
            "work_root", "work_content", "work_operations", "archive_root",
        )
        for attr in attrs:
            batch = JobBatch()
            job = batch.new_job()
            setattr(job, attr, Path("C:/x"))
            self.assertFalse(job.is_unused_draft(), attr)

    def test_custom_name_makes_job_significant(self):
        batch = JobBatch()
        job = batch.new_job(name="Behold denne")
        self.assertFalse(job.is_unused_draft())

    def test_execution_history_makes_job_significant(self):
        batch = JobBatch()
        job = batch.new_job()
        job.log_entries.append("start")
        self.assertFalse(job.is_unused_draft())


if __name__ == "__main__":
    unittest.main()
