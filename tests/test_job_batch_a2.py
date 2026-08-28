import tempfile
import unittest
from pathlib import Path

from noark5_workflow.core.job import JobBatch, JobStatus


class JobBatchA2Tests(unittest.TestCase):
    def test_operation_params_are_isolated_per_job(self):
        batch = JobBatch()
        one = batch.new_job(Path("one"))
        two = batch.new_job(Path("two"))
        one.set_operation_params("dias_package", {"output_dir": "A"})
        two.set_operation_params("dias_package", {"output_dir": "B"})
        self.assertEqual(one.get_operation_params("dias_package")["output_dir"], "A")
        self.assertEqual(two.get_operation_params("dias_package")["output_dir"], "B")

    def test_operation_params_are_copied(self):
        batch = JobBatch()
        job = batch.new_job(Path("one"))
        params = {"extra_files": ["x"]}
        job.set_operation_params("op", params)
        params["extra_files"].append("y")
        self.assertEqual(job.get_operation_params("op"), {"extra_files": ["x"]})

    def test_batch_counts_skipped(self):
        batch = JobBatch()
        job = batch.new_job(Path("one"))
        job.status = JobStatus.SKIPPED
        self.assertEqual(batch.counts()[JobStatus.SKIPPED], 1)


if __name__ == "__main__":
    unittest.main()
