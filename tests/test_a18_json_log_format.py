from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from noark5_workflow.core.events import WorkflowEvent
from noark5_workflow.logging_pipeline import (
    JSON_SINK,
    build_event_dispatcher,
    find_sink,
)
from noark5_workflow.renderers.registry import registered_implementations


class A18JsonLogFormatTests(unittest.TestCase):
    def test_json_renderer_is_registered(self):
        self.assertIn("json_full_v1", registered_implementations())

    def test_json_definition_is_loaded_through_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "temp_dir": tmp,
                "enabled_log_sinks": ["json"],
                "enable_premis_provenance": False,
                "_current_run_id": "RUN-JSON",
                "_current_event_store_path": str(Path(tmp) / "events.jsonl"),
            }
            dispatcher = build_event_dispatcher(settings, scope="run", run_id="RUN-JSON")
            sink = find_sink(dispatcher, JSON_SINK)
            self.assertIsNotNone(sink)
            self.assertEqual("json_full_v1", sink.definition.definition_id)

    def test_json_output_preserves_nested_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "temp_dir": tmp,
                "enabled_log_sinks": ["json"],
                "enable_premis_provenance": False,
                "_current_run_id": "RUN-JSON",
                "_current_event_store_path": str(Path(tmp) / "events.jsonl"),
            }
            dispatcher = build_event_dispatcher(settings, scope="operation", run_id="RUN-JSON")
            sink = find_sink(dispatcher, JSON_SINK)
            dispatcher.emit(
                WorkflowEvent.now(
                    "operation.completed",
                    run_id="RUN-JSON",
                    job_id="JOB-001",
                    operation_id="op",
                    data={"metrics": {"count": 7}, "items": [1, 2]},
                )
            )
            rows = [json.loads(line) for line in sink.path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(1, len(rows))
            self.assertEqual(7, rows[0]["data"]["metrics"]["count"])
            self.assertEqual([1, 2], rows[0]["data"]["items"])

    def test_json_is_output_projection_not_event_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "temp_dir": tmp,
                "enabled_log_sinks": ["json"],
                "enable_premis_provenance": False,
                "_current_run_id": "RUN-JSON",
                "_current_event_store_path": str(Path(tmp) / "canonical.events.jsonl"),
            }
            dispatcher = build_event_dispatcher(settings, scope="run", run_id="RUN-JSON")
            dispatcher.emit(WorkflowEvent.now("run.started", run_id="RUN-JSON"))
            self.assertTrue(Path(settings["_current_event_store_path"]).is_file())
            json_sink = find_sink(dispatcher, JSON_SINK)
            self.assertTrue(json_sink.path.is_file())
            self.assertNotEqual(Path(settings["_current_event_store_path"]), json_sink.path)


if __name__ == "__main__":
    unittest.main()
