from __future__ import annotations

import unittest
from pathlib import Path

from noark5_workflow.logging_pipeline import (
    PREMIS_SINK,
    TEXT_RUN_LOG_SINK,
    build_event_dispatcher,
    configured_sink_ids,
    find_sink,
)


ROOT = Path(__file__).resolve().parents[1]


class A18LogSinkConfigurationTests(unittest.TestCase):
    def test_legacy_settings_keep_text_and_premis_defaults(self):
        self.assertEqual(
            (TEXT_RUN_LOG_SINK, PREMIS_SINK),
            configured_sink_ids({"enable_premis_provenance": True}),
        )

    def test_premis_legacy_toggle_remains_authoritative(self):
        self.assertEqual(
            (TEXT_RUN_LOG_SINK,),
            configured_sink_ids({
                "enabled_log_sinks": [TEXT_RUN_LOG_SINK, PREMIS_SINK],
                "enable_premis_provenance": False,
            }),
        )

    def test_run_and_operation_use_same_dispatcher_builder(self):
        pipeline = (ROOT / "noark5_workflow" / "logging_pipeline.py").read_text(encoding="utf-8")
        run_log = (ROOT / "app" / "run_overview_log.py").read_text(encoding="utf-8")
        executor = (ROOT / "noark5_workflow" / "executors" / "local.py").read_text(encoding="utf-8")
        self.assertIn("build_event_dispatcher(", run_log)
        self.assertIn("event_dispatcher_for", executor)
        self.assertIn('scope="run"', run_log)
        self.assertIn('scope="operation"', pipeline)

    def test_setup_exposes_both_current_sink_choices(self):
        text = (ROOT / "gui" / "setup_dialog_a18.py").read_text(encoding="utf-8")
        self.assertIn("Tekstlig kjørelogg", text)
        self.assertIn("PREMIS-proveniens", text)
        self.assertIn("enabled_log_sinks", text)

    def test_operation_dispatcher_does_not_create_text_run_sink(self):
        dispatcher = build_event_dispatcher(
            {"enabled_log_sinks": [TEXT_RUN_LOG_SINK], "enable_premis_provenance": False},
            scope="operation",
        )
        self.assertIsNone(find_sink(dispatcher, "text-run-log"))


if __name__ == "__main__":
    unittest.main()
