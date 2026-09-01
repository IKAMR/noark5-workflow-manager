import unittest
from pathlib import Path

from noark5_workflow.core.job import JobBatch


class JobBatchOrderingA10Tests(unittest.TestCase):
    def make_batch(self):
        batch = JobBatch()
        batch.new_job(Path("one"))
        batch.new_job(Path("two"))
        batch.new_job(Path("three"))
        return batch

    def test_move_up_changes_order(self):
        batch = self.make_batch()
        self.assertTrue(batch.move_up("JOB-002"))
        self.assertEqual([j.job_id for j in batch.jobs()], ["JOB-002", "JOB-001", "JOB-003"])

    def test_move_down_changes_order(self):
        batch = self.make_batch()
        self.assertTrue(batch.move_down("JOB-002"))
        self.assertEqual([j.job_id for j in batch.jobs()], ["JOB-001", "JOB-003", "JOB-002"])

    def test_move_boundaries_do_not_change_order(self):
        batch = self.make_batch()
        self.assertFalse(batch.move_up("JOB-001"))
        self.assertFalse(batch.move_down("JOB-003"))
        self.assertEqual([j.job_id for j in batch.jobs()], ["JOB-001", "JOB-002", "JOB-003"])

    def test_remove_does_not_delete_or_renumber_other_jobs(self):
        batch = self.make_batch()
        self.assertTrue(batch.remove("JOB-002"))
        self.assertEqual([j.job_id for j in batch.jobs()], ["JOB-001", "JOB-003"])
        new_job = batch.new_job(Path("four"))
        self.assertEqual(new_job.job_id, "JOB-004")


if __name__ == "__main__":
    unittest.main()
