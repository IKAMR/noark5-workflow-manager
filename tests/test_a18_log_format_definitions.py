from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from noark5_workflow.core.log_format_definition import (
    LogFormatDefinitionError,
    load_log_format_definition,
)
from noark5_workflow.logging_pipeline import (
    build_event_dispatcher,
    find_sink,
)


ROOT = Path(__file__).resolve().parents[1]


class A18LogFormatDefinitionTests(unittest.TestCase):
    def test_default_text_definition_is_external_json(self):
        definition = load_log_format_definition("text_run_default_v1")
        self.assertEqual("text", definition.format)
        self.assertEqual("text_run_log_v1", definition.implementation)
        self.assertTrue(definition.accepts("run.started"))
        self.assertFalse(definition.accepts("operation.completed"))

    def test_default_premis_definition_is_external_json(self):
        definition = load_log_format_definition("premis_default_v1")
        self.assertEqual("premis", definition.format)
        self.assertEqual("premis_xml_v1", definition.implementation)
        self.assertTrue(definition.accepts("operation.completed"))
        self.assertEqual("username", definition.options["default_agent_identifier"])

    def test_pipeline_passes_loaded_definition_to_text_sink(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "temp_dir": tmp,
                "enabled_log_sinks": ["text_run_log"],
                "enable_premis_provenance": False,
                "_current_run_id": "RUN-1",
                "_current_event_store_path": str(Path(tmp) / "events.jsonl"),
            }
            dispatcher = build_event_dispatcher(
                settings,
                scope="run",
                run_type="single",
                app_version="test",
                run_id="RUN-1",
            )
            sink = find_sink(dispatcher, "text_run_log")
            self.assertIsNotNone(sink)
            self.assertEqual("text_run_default_v1", sink.definition.definition_id)

    def test_pipeline_passes_loaded_definition_to_premis_sink(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "temp_dir": tmp,
                "enabled_log_sinks": ["premis"],
                "enable_premis_provenance": True,
                "_current_run_id": "RUN-1",
                "_current_event_store_path": str(Path(tmp) / "events.jsonl"),
            }
            dispatcher = build_event_dispatcher(settings, scope="operation", run_id="RUN-1")
            sink = find_sink(dispatcher, "premis")
            self.assertIsNotNone(sink)
            self.assertEqual("premis_default_v1", sink.definition.definition_id)

    def test_definition_id_must_match_file_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "x.json"
            path.write_text(json.dumps({
                "definition_id": "wrong",
                "definition_version": 1,
                "format": "csv",
                "implementation": "csv_v1",
                "event_kinds": ["*"],
                "field_map": {},
                "options": {},
            }), encoding="utf-8")
            with self.assertRaises(LogFormatDefinitionError):
                load_log_format_definition("x", root=root)

    def test_format_mapping_is_not_hardcoded_in_executor(self):
        executor = (ROOT / "noark5_workflow" / "executors" / "local.py").read_text(encoding="utf-8")
        self.assertNotIn("eventIdentifierValue", executor)
        self.assertNotIn("eventDateTime", executor)
        self.assertNotIn("agentIdentifierValue", executor)


if __name__ == "__main__":
    unittest.main()
