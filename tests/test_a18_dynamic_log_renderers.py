from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from noark5_workflow.logging_pipeline import build_event_dispatcher, find_sink
from noark5_workflow.renderers.registry import (
    UnknownLogImplementationError,
    registered_implementations,
    resolve_renderer,
)


class A18DynamicLogRendererTests(unittest.TestCase):
    def test_current_implementations_are_registered(self):
        self.assertIn("premis_xml_v1", registered_implementations())
        self.assertIn("text_run_log_v1", registered_implementations())

    def test_unknown_implementation_fails_explicitly(self):
        with self.assertRaises(UnknownLogImplementationError):
            resolve_renderer("does_not_exist")

    def test_text_definition_uses_implementation_registry(self):
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
            self.assertEqual("text_run_log_v1", sink.definition.implementation)

    def test_premis_definition_uses_implementation_registry(self):
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
            self.assertEqual("premis_xml_v1", sink.definition.implementation)

    def test_pipeline_does_not_hardcode_renderer_classes(self):
        text = Path("noark5_workflow/logging_pipeline.py").read_text(encoding="utf-8")
        self.assertNotIn("PremisEventSink", text)
        self.assertNotIn("TextRunLogSink", text)
        self.assertIn("resolve_renderer", text)


if __name__ == "__main__":
    unittest.main()
