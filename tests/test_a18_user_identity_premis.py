from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as ET

from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.premis_logger import PREMIS_NS, PremisProvenanceLogger
from noark5_workflow.core.result import OperationResult
from noark5_workflow.executors.local import LocalExecutor
from settings import DEFAULT_CONFIG


ROOT = Path(__file__).resolve().parents[1]


class _Definition:
    operation_id = "test_op"
    name = "Test operation"


class _Operation:
    definition = _Definition()
    premis_event_type = "Adjustment"
    premis_event_label = ""

    def can_run(self, ctx):
        return True, ""

    def run(self, ctx):
        return OperationResult(True, "OK")

    def premis_output_dir(self, result, ctx):
        return ctx.output_root

    def premis_detail(self, result, ctx):
        return result.message


class A18UserIdentityPremisTests(unittest.TestCase):
    def test_username_is_default_premis_agent_identifier(self):
        self.assertEqual("username", DEFAULT_CONFIG.get("premis_agent_identifier"))

    def test_executor_passes_selected_identity_strategy_to_premis(self):
        executor_text = (ROOT / "noark5_workflow" / "executors" / "local.py").read_text(encoding="utf-8")
        sink_text = (ROOT / "noark5_workflow" / "sinks" / "premis.py").read_text(encoding="utf-8")
        self.assertNotIn('ctx.settings.get("premis_agent_identifier", "username")', executor_text)
        self.assertIn('ctx.settings.get("premis_agent_identifier", "username")', sink_text)

    def test_user_id_can_be_selected_as_premis_agent_identifier(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            logger = PremisProvenanceLogger(
                root,
                root,
                user_agent_identifier_type="user_id",
                user_agent_identifier_value="abc-123",
                user_agent_name="Test User",
            )
            logger._events.append({
                "type": "Adjustment",
                "label": "",
                "op_id": "x",
                "datetime": "2026-09-09T10:00:00+02:00",
                "detail": "x",
                "success": True,
                "user_agent_identifier_type": "user_id",
                "user_agent_identifier_value": "abc-123",
                "user_agent_name": "Test User",
            })
            path = logger.finalize(root)
            tree = ET.parse(path)
            ns = {"p": PREMIS_NS}
            values = [e.text for e in tree.findall(".//p:agentIdentifierValue", ns)]
            self.assertIn("abc-123", values)

    def test_premis_event_uses_selected_username_agent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            logger = PremisProvenanceLogger(
                root,
                root,
                user_agent_identifier_type="username",
                user_agent_identifier_value="taa",
                user_agent_name="Test User",
            )
            op = _Operation()
            ctx = SimpleNamespace(log=lambda message: None)
            result = OperationResult(True, "OK")
            logger.record(op, result, ctx)
            path = logger.finalize(root)
            tree = ET.parse(path)
            ns = {"p": PREMIS_NS}
            values = [e.text for e in tree.findall(".//p:agentIdentifierValue", ns)]
            self.assertIn("taa", values)

    def test_existing_event_keeps_original_user_when_new_user_is_added(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = PremisProvenanceLogger(
                root, root,
                user_agent_identifier_type="username",
                user_agent_identifier_value="first",
                user_agent_name="First User",
            )
            first._events.append({
                "type": "Adjustment", "label": "", "op_id": "x",
                "datetime": "2026-09-09T10:00:00+02:00",
                "detail": "first", "success": True,
                "user_agent_identifier_type": "username",
                "user_agent_identifier_value": "first",
                "user_agent_name": "First User",
            })
            first.finalize(root)

            second = PremisProvenanceLogger(
                root, root,
                user_agent_identifier_type="username",
                user_agent_identifier_value="second",
                user_agent_name="Second User",
            )
            second._load_existing_events()
            second._events.append({
                "type": "Adjustment", "label": "", "op_id": "x",
                "datetime": "2026-09-09T10:01:00+02:00",
                "detail": "second", "success": True,
                "user_agent_identifier_type": "username",
                "user_agent_identifier_value": "second",
                "user_agent_name": "Second User",
            })
            path = second.finalize(root)
            tree = ET.parse(path)
            ns = {"p": PREMIS_NS}
            values = [e.text for e in tree.findall(".//p:agentIdentifierValue", ns)]
            self.assertIn("first", values)
            self.assertIn("second", values)

    def test_runtime_identity_is_transient_not_setup_data(self):
        text = (ROOT / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        self.assertIn("_current_user_identity", text)

    def test_setup_exposes_premis_toggle_and_agent_choice(self):
        text = (ROOT / "gui" / "setup_dialog_a18.py").read_text(encoding="utf-8")
        self.assertIn("PREMIS", text)
        self.assertIn("enable_premis_provenance", text)
        self.assertIn("premis_agent_identifier", text)
        self.assertIn("Brukernavn", text)
        self.assertIn("Intern user_id", text)

    def test_status_bar_exposes_username_not_internal_id(self):
        text = (ROOT / "gui" / "status_bar.py").read_text(encoding="utf-8")
        self.assertIn("Bruker:", text)
        self.assertNotIn("user_id", text)

    def test_development_documents_format_neutral_log_model(self):
        text = (ROOT / "docs" / "APP-WORKSPACE-AND-RUN-LOGS.md").read_text(encoding="utf-8")
        self.assertIn("formatnøytrale", text)
        self.assertIn("PREMIS", text)


if __name__ == "__main__":
    unittest.main()
