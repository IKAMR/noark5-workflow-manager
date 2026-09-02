import json
import tempfile
import unittest
from pathlib import Path

from noark5_workflow.core.job import Job, JobBatch, JobStatus
from noark5_workflow.core.job_store import (
    FILE_TYPE,
    FORMAT_VERSION,
    load_job_list,
    save_job_list,
)


class CheckpointA2Tests(unittest.TestCase):
    def test_checkpoint_and_cursor_model(self):
        job = Job(
            job_id="JOB-001",
            source_root=Path("source"),
            workflow_ids=["one", "two", "three"],
        )
        job.set_checkpoint("one", True)
        self.assertTrue(job.has_checkpoint("one"))
        job.mark_operation_completed(0)
        self.assertEqual(job.next_operation_index, 1)
        self.assertAlmostEqual(job.progress, 1 / 3)

        job.status = JobStatus.WAITING
        job.message = "Venter"
        self.assertEqual(job.status.value, "Venter ved kontrollpunkt")

    def test_checkpoint_can_be_removed(self):
        job = Job(
            job_id="JOB-001",
            source_root=Path("source"),
            workflow_ids=["one", "two"],
            checkpoint_after=["one"],
        )
        job.set_checkpoint("one", False)
        self.assertFalse(job.has_checkpoint("one"))

    def test_workflow_edit_invalidates_waiting_cursor(self):
        job = Job(
            job_id="JOB-001",
            source_root=Path("source"),
            workflow_ids=["one", "two"],
            checkpoint_after=["one"],
            next_operation_index=1,
            status=JobStatus.WAITING,
        )
        job.set_workflow(["one", "two", "three"])
        self.assertEqual(job.next_operation_index, 0)
        self.assertEqual(job.status, JobStatus.READY)

    def test_v2_roundtrip_persists_checkpoint_and_cursor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batch = JobBatch()
            job = batch.new_job(root / "source", workflow_ids=["one", "two", "three"])
            job.set_checkpoint("one", True)
            job.mark_operation_completed(0)
            job.status = JobStatus.WAITING
            job.message = "Venter ved kontrollpunkt"

            path = save_job_list(root / "list.n5jobs", batch, active_job_id=job.job_id, app_version="0.1.2-a2")
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(raw["format_version"], FORMAT_VERSION)
            self.assertEqual(raw["jobs"][0]["checkpoint_after"], ["one"])
            self.assertEqual(raw["jobs"][0]["next_operation_index"], 1)

            loaded = load_job_list(path)
            restored = loaded.batch.get("JOB-001")
            self.assertIsNotNone(restored)
            self.assertEqual(restored.checkpoint_after, ["one"])
            self.assertEqual(restored.next_operation_index, 1)
            self.assertEqual(restored.status, JobStatus.WAITING)

    def test_v1_job_list_remains_loadable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "old.n5jobs"
            payload = {
                "file_type": FILE_TYPE,
                "format_version": 1,
                "app_version": "0.1.1",
                "created_at": "",
                "modified_at": "",
                "active_job_id": "JOB-001",
                "jobs": [{
                    "job_id": "JOB-001",
                    "name": "Old",
                    "source_root": "source",
                    "output_root": None,
                    "workflow_ids": ["one", "two"],
                    "operation_params": {},
                    "status": "Klar",
                    "progress": 0.0,
                    "worker": "Lokal (denne PC-en)",
                    "message": "",
                    "log_entries": [],
                }],
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = load_job_list(path)
            job = loaded.batch.get("JOB-001")
            self.assertIsNotNone(job)
            self.assertEqual(job.checkpoint_after, [])
            self.assertEqual(job.next_operation_index, 0)

    def test_gui_exposes_checkpoint_and_continue(self):
        root = Path(__file__).resolve().parents[1]
        panel = (root / "gui" / "workflow_panel.py").read_text(encoding="utf-8")
        app = (root / "gui" / "persistent_app.py").read_text(encoding="utf-8")
        self.assertIn('text="■" if active_checkpoint else ""', panel)
        self.assertIn('"Sett kontrollpunkt etter operasjonen"', panel)
        self.assertIn('set_run_text("Fortsett workflow")', app)
        self.assertIn("JobStatus.WAITING", app)
        self.assertIn("next_operation_index", app)


if __name__ == "__main__":
    unittest.main()
