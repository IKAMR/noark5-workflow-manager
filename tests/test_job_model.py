import tempfile
import unittest
from pathlib import Path

from noark5_workflow.core.job import JobBatch, JobStatus


class JobModelTests(unittest.TestCase):
    def test_batch_creates_ordered_unique_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch = JobBatch()
            one = batch.new_job(root / "one", workflow_ids=["op-a"])
            two = batch.new_job(root / "two")
            self.assertEqual(one.job_id, "JOB-001")
            self.assertEqual(two.job_id, "JOB-002")
            self.assertEqual([j.job_id for j in batch.jobs()], ["JOB-001", "JOB-002"])
            self.assertEqual(one.workflow_ids, ["op-a"])

    def test_status_counts(self):
        batch = JobBatch()
        one = batch.new_job(Path("one"))
        two = batch.new_job(Path("two"))
        one.status = JobStatus.OK
        two.status = JobStatus.FAILED
        counts = batch.counts()
        self.assertEqual(counts[JobStatus.OK], 1)
        self.assertEqual(counts[JobStatus.FAILED], 1)
        self.assertEqual(counts[JobStatus.READY], 0)

    def test_remove_job(self):
        batch = JobBatch()
        job = batch.new_job(Path("one"))
        self.assertTrue(batch.remove(job.job_id))
        self.assertFalse(batch.remove(job.job_id))
        self.assertEqual(len(batch), 0)


if __name__ == "__main__":
    unittest.main()
