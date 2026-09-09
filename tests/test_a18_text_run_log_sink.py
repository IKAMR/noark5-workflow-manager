from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.run_overview_log import RunOverviewLog
from noark5_workflow.core.events import WorkflowEvent
from noark5_workflow.sinks.text_run_log import TextRunLogSink


class DummyStatus:
    value = "Ferdig"


class DummyJob:
    job_id = "JOB-001"
    name = "Testjobb"
    source_root = Path("C:/source")
    source_extraction = Path("C:/source/extraction")
    active_extraction_root = source_extraction
    work_root = Path("C:/work")
    work_operations = None
    archive_root = Path("C:/archive")
    output_root = archive_root
    status = DummyStatus()
    message = "OK"
    owner_user_id = "owner-id"
    owner_username = "owner"
    owner_name = "Owner Name"
    owner_email = "owner@example.org"


class A18TextRunLogSinkTests(unittest.TestCase):
    def test_text_run_log_is_an_event_sink(self):
        self.assertEqual("text_run_log", TextRunLogSink.sink_id)
        self.assertTrue(callable(getattr(TextRunLogSink, "handle")))

    def test_legacy_facade_preserves_current_log_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "temp_dir": tmp,
                "run_log_dir": "",
                "copy_run_log_to_work_operations": False,
                "_current_user_identity": {
                    "user_id": "runner-id",
                    "username": "runner",
                    "name": "Runner Name",
                    "email": "runner@example.org",
                },
            }
            log = RunOverviewLog(
                settings,
                run_type="single",
                app_version="0.1.2-a18",
                planned_jobs=1,
            )
            log.set_phase("Kjører")
            log.start_job(DummyJob())
            log.finish_job(DummyJob())
            path = log.finish()

            text = path.read_text(encoding="utf-8")
            self.assertIn("Run ID:", text)
            self.assertIn("Fase: Kjører", text)
            self.assertIn("Utførende bruker - brukernavn: runner", text)
            self.assertIn("Jobbeier - brukernavn: owner", text)
            self.assertIn("SAMMENDRAG", text)

    def test_sink_can_consume_neutral_event_without_job_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            sink = TextRunLogSink(
                {"temp_dir": tmp, "run_log_dir": "", "copy_run_log_to_work_operations": False},
                run_type="single",
                app_version="0.1.2-a18",
            )
            sink.handle(WorkflowEvent.now(
                "job.started",
                job_id="JOB-001",
                data={
                    "name": "Neutral",
                    "source": "source",
                    "source_root": "source",
                    "source_extraction": "source",
                    "work_root": "",
                    "work_operations": "",
                    "archive_root": "archive",
                    "output": "archive",
                    "owner": {"user_id": "id", "username": "u", "name": "U", "email": "u@example.org"},
                },
            ))
            sink.handle(WorkflowEvent.now(
                "job.finished",
                job_id="JOB-001",
                message="done",
                data={"status": "Ferdig", "output": "archive"},
            ))
            sink.handle(WorkflowEvent.now("run.finished", data={"status": "FERDIG"}))
            self.assertIn("Neutral", sink.path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
