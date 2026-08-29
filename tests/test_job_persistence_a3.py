import json
import tempfile
import unittest
from pathlib import Path

from noark5_workflow.core.job import JobBatch, JobStatus
from noark5_workflow.core.job_store import FILE_TYPE, FORMAT_VERSION, load_job_list, save_job_list


class JobPersistenceA3Tests(unittest.TestCase):
    def test_job_list_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batch = JobBatch()
            first = batch.new_job(root / "source-a", output_root=root / "out-a", name="A")
            first.set_workflow(["dias_package", "example"])
            first.set_operation_params("dias_package", {
                "output_dir": str(root / "out-a"),
                "metadata": {"title": "Æ Ø Å"},
                "extra_files": [str(root / "one.txt")],
            })
            first.status = JobStatus.OK
            first.progress = 1.0
            first.message = "Workflow fullført"
            first.log_entries = ["[12:00:00] test"]

            second = batch.new_job(root / "source-b")
            path = save_job_list(
                root / "many-jobs",
                batch,
                active_job_id=second.job_id,
                app_version="0.1.1-a3",
            )

            self.assertEqual(path.suffix, ".n5jobs")
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(raw["file_type"], FILE_TYPE)
            self.assertEqual(raw["format_version"], FORMAT_VERSION)
            self.assertEqual(len(raw["jobs"]), 2)

            loaded = load_job_list(path)
            self.assertEqual(loaded.active_job_id, "JOB-002")
            self.assertEqual(
                [job.job_id for job in loaded.batch.jobs()],
                ["JOB-001", "JOB-002"],
            )

            restored = loaded.batch.get("JOB-001")
            self.assertIsNotNone(restored)
            self.assertEqual(restored.source_root, root / "source-a")
            self.assertEqual(restored.output_root, root / "out-a")
            self.assertEqual(restored.workflow_ids, ["dias_package", "example"])
            self.assertEqual(
                restored.get_operation_params("dias_package")["metadata"]["title"],
                "Æ Ø Å",
            )
            self.assertEqual(restored.status, JobStatus.OK)
            self.assertEqual(restored.progress, 1.0)

            third = loaded.batch.new_job(root / "source-c")
            self.assertEqual(third.job_id, "JOB-003")

    def test_running_job_becomes_ready_after_reload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batch = JobBatch()
            job = batch.new_job(root / "source")
            job.status = JobStatus.RUNNING
            job.progress = 0.5

            path = save_job_list(root / "running.n5jobs", batch)
            restored = load_job_list(path).batch.get("JOB-001")

            self.assertIsNotNone(restored)
            self.assertEqual(restored.status, JobStatus.READY)
            self.assertIn("aktiv", restored.message)


if __name__ == "__main__":
    unittest.main()
