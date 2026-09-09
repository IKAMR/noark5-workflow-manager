import unittest
from pathlib import Path

from noark5_workflow.core.job import JobBatch


class DraftIdRegressionCompatibilityA17Tests(unittest.TestCase):
    def test_removing_configured_job_preserves_monotonic_identity(self):
        batch = JobBatch()
        first = batch.new_job()
        second = batch.new_job(source_root=Path("C:/configured"))
        batch.remove(second.job_id)
        third = batch.new_job()
        self.assertEqual(first.job_id, "JOB-001")
        self.assertEqual(third.job_id, "JOB-003")

    def test_removing_middle_job_never_renumbers_remaining_jobs(self):
        batch = JobBatch()
        first = batch.new_job()
        second = batch.new_job()
        third = batch.new_job()
        batch.remove(second.job_id)
        self.assertEqual([j.job_id for j in batch.jobs()], ["JOB-001", "JOB-003"])
        self.assertEqual(first.job_id, "JOB-001")
        self.assertEqual(third.job_id, "JOB-003")


if __name__ == "__main__":
    unittest.main()
