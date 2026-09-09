from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.run_overview_log import RunOverviewLog
from noark5_workflow.core.events import EventDispatcher, WorkflowEvent
from noark5_workflow.core.identity import UserIdentity
from noark5_workflow.logging_pipeline import build_event_dispatcher, find_sink
from noark5_workflow.sinks.event_store import (
    EVENT_STORE_SCHEMA_VERSION,
    GenericEventStoreSink,
    read_event_store,
)


class OptionalFailingSink:
    sink_id = "optional"
    required = False
    def handle(self, event, **runtime):
        raise RuntimeError("optional failure")
    def close(self, **runtime):
        return None


class RequiredFailingSink:
    sink_id = "required"
    required = True
    def handle(self, event, **runtime):
        raise RuntimeError("required failure")
    def close(self, **runtime):
        return None


class A18GenericEventStoreTests(unittest.TestCase):
    def test_event_store_is_append_only_and_schema_versioned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            sink = GenericEventStoreSink(path)
            sink.handle(WorkflowEvent.now("run.started", run_id="RUN-1"))
            sink.handle(WorkflowEvent.now("run.finished", run_id="RUN-1"))
            records = read_event_store(path)
            self.assertEqual(2, len(records))
            self.assertTrue(all(r["schema_version"] == EVENT_STORE_SCHEMA_VERSION for r in records))
            self.assertNotEqual(records[0]["event_id"], records[1]["event_id"])

    def test_event_store_preserves_structured_user_and_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            user = UserIdentity("id-1", "taa", "Test User", "test@example.org")
            GenericEventStoreSink(path).handle(
                WorkflowEvent.now(
                    "operation.completed",
                    run_id="RUN-1",
                    job_id="JOB-001",
                    operation_id="op",
                    user=user,
                    data={"metrics": {"count": 3}, "path": Path("x/y")},
                )
            )
            record = read_event_store(path)[0]
            self.assertEqual("taa", record["user"]["username"])
            self.assertEqual(3, record["data"]["metrics"]["count"])
            self.assertEqual(str(Path("x/y")), record["data"]["path"])

    def test_required_store_failure_is_not_silenced(self):
        dispatcher = EventDispatcher([OptionalFailingSink(), RequiredFailingSink()])
        with self.assertRaises(RuntimeError):
            dispatcher.emit(WorkflowEvent.now("run.started"))

    def test_run_facade_creates_canonical_store_and_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "temp_dir": tmp,
                "run_log_dir": "",
                "enabled_log_sinks": ["text_run_log"],
                "enable_premis_provenance": False,
                "copy_run_log_to_work_operations": False,
            }
            log = RunOverviewLog(settings, run_type="single", app_version="0.1.2-a18")
            self.assertEqual(log.run_id, settings["_current_run_id"])
            self.assertEqual(str(log.event_store_path), settings["_current_event_store_path"])
            records = read_event_store(log.event_store_path)
            self.assertEqual("run.started", records[0]["kind"])
            self.assertEqual(log.run_id, records[0]["run_id"])

    def test_output_sink_selection_does_not_disable_event_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "temp_dir": tmp,
                "enabled_log_sinks": [],
                "enable_premis_provenance": False,
                "_current_run_id": "RUN-1",
                "_current_event_store_path": str(Path(tmp) / "events.jsonl"),
            }
            dispatcher = build_event_dispatcher(settings, scope="operation")
            self.assertIsNotNone(find_sink(dispatcher, "event_store"))
            dispatcher.emit(WorkflowEvent.now("operation.completed", run_id="RUN-1"))
            self.assertEqual(1, len(read_event_store(Path(tmp) / "events.jsonl")))


if __name__ == "__main__":
    unittest.main()
