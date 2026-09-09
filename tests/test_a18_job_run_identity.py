from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.run_overview_log import RunOverviewLog
from noark5_workflow.core.job import Job, JobBatch
from noark5_workflow.core.job_store import load_job_list, save_job_list


IDENTITY = {
    "user_id": "11111111-1111-4111-8111-111111111111",
    "username": "owner",
    "name": "Owner Name",
    "email": "owner@example.org",
}


class A18JobRunIdentityTests(unittest.TestCase):
    def test_job_owner_is_set_once(self):
        job = Job("JOB-001")
        job.set_owner_identity(IDENTITY)
        first = dict(job.owner_identity or {})
        job.set_owner_identity({
            "user_id": "22222222-2222-4222-8222-222222222222",
            "username": "other",
            "name": "Other",
            "email": "other@example.org",
        })
        self.assertEqual(first, job.owner_identity)

    def test_owner_only_does_not_make_blank_draft_significant(self):
        job = Job("JOB-001")
        job.set_owner_identity(IDENTITY)
        self.assertTrue(job.is_unused_draft())

    def test_job_owner_roundtrip_and_legacy_job_without_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.n5jobs"
            batch = JobBatch()
            job = batch.new_job()
            job.set_owner_identity(IDENTITY)
            save_job_list(path, batch, active_job_id=job.job_id, app_version="0.1.2-a18")
            loaded = load_job_list(path).batch.get("JOB-001")
            self.assertEqual(IDENTITY, loaded.owner_identity)

            payload = json.loads(path.read_text(encoding="utf-8"))
            for key in ("owner_user_id", "owner_username", "owner_name", "owner_email"):
                payload["jobs"][0].pop(key, None)
            path.write_text(json.dumps(payload), encoding="utf-8")
            legacy = load_job_list(path).batch.get("JOB-001")
            self.assertIsNone(legacy.owner_identity)

    def test_run_log_records_executor_and_job_owner_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "temp_dir": tmp,
                "run_log_dir": "",
                "copy_run_log_to_work_operations": False,
                "_current_user_identity": {
                    "user_id": "33333333-3333-4333-8333-333333333333",
                    "username": "runner",
                    "name": "Runner Name",
                    "email": "runner@example.org",
                },
            }
            log = RunOverviewLog(settings, run_type="single", app_version="0.1.2-a18")
            job = Job("JOB-001")
            job.set_owner_identity(IDENTITY)
            log.start_job(job)
            text = log.path.read_text(encoding="utf-8")
            self.assertIn("Utførende bruker - brukernavn: runner", text)
            self.assertIn("Jobbeier - brukernavn: owner", text)
            self.assertNotEqual(log.run_user_id, job.owner_user_id)

    def test_a18_runtime_assigns_owner_on_new_job_only(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        self.assertIn("job = super()._create_job(source_root)", text)
        self.assertIn("job.set_owner_identity(self.current_user_identity())", text)


if __name__ == "__main__":
    unittest.main()
