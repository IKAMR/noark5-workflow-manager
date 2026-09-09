from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from noark5_workflow.core.events import WorkflowEvent
from noark5_workflow.logging_pipeline import (
    CSV_SINK,
    build_event_dispatcher,
    find_sink,
)
from noark5_workflow.renderers.registry import registered_implementations


class A18CsvLogFormatTests(unittest.TestCase):
    def test_csv_renderer_is_registered(self):
        self.assertIn("csv_standard_v1", registered_implementations())

    def test_csv_definition_is_loaded_through_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "temp_dir": tmp,
                "enabled_log_sinks": ["csv"],
                "enable_premis_provenance": False,
                "_current_run_id": "RUN-CSV",
                "_current_event_store_path": str(Path(tmp) / "events.jsonl"),
            }
            dispatcher = build_event_dispatcher(settings, scope="run", run_id="RUN-CSV")
            sink = find_sink(dispatcher, CSV_SINK)
            self.assertIsNotNone(sink)
            self.assertEqual("csv_standard_v1", sink.definition.definition_id)

    def test_csv_writes_flat_selected_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "temp_dir": tmp,
                "enabled_log_sinks": ["csv"],
                "enable_premis_provenance": False,
                "_current_run_id": "RUN-CSV",
                "_current_event_store_path": str(Path(tmp) / "events.jsonl"),
            }
            dispatcher = build_event_dispatcher(settings, scope="operation", run_id="RUN-CSV")
            sink = find_sink(dispatcher, CSV_SINK)
            dispatcher.emit(
                WorkflowEvent.now(
                    "operation.completed",
                    run_id="RUN-CSV",
                    job_id="JOB-001",
                    operation_id="op",
                    operation_name="Test operation",
                    message="OK",
                )
            )
            with sink.path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter=";"))
            self.assertEqual(1, len(rows))
            self.assertEqual("RUN-CSV", rows[0]["run_id"])
            self.assertEqual("JOB-001", rows[0]["job_id"])
            self.assertEqual("op", rows[0]["operation_id"])
            self.assertEqual("Test operation", rows[0]["operation_name"])

    def test_csv_columns_come_from_definition(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "temp_dir": tmp,
                "enabled_log_sinks": ["csv"],
                "enable_premis_provenance": False,
                "_current_run_id": "RUN-CSV",
                "_current_event_store_path": str(Path(tmp) / "events.jsonl"),
            }
            dispatcher = build_event_dispatcher(settings, scope="run", run_id="RUN-CSV")
            sink = find_sink(dispatcher, CSV_SINK)
            self.assertIn("timestamp", sink.columns)
            self.assertIn("username", sink.columns)
            self.assertNotIn("data", sink.columns)


if __name__ == "__main__":
    unittest.main()
