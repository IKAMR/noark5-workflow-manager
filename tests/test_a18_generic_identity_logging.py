from __future__ import annotations

import unittest
from pathlib import Path

from noark5_workflow.core.events import EventDispatcher, WorkflowEvent
from noark5_workflow.core.identity import UserIdentity


ROOT = Path(__file__).resolve().parents[1]


class RecordingSink:
    sink_id = "recording"

    def __init__(self):
        self.events = []

    def handle(self, event, **runtime):
        self.events.append((event, runtime))

    def close(self, **runtime):
        return None


class FailingSink:
    sink_id = "failing"

    def handle(self, event, **runtime):
        raise RuntimeError("simulated sink failure")

    def close(self, **runtime):
        raise RuntimeError("simulated close failure")


class A18GenericIdentityLoggingTests(unittest.TestCase):
    def test_user_identity_is_transport_neutral(self):
        identity = UserIdentity(
            user_id="11111111-1111-4111-8111-111111111111",
            username="taa",
            name="Test User",
            email="test@example.org",
        )
        self.assertEqual("taa", identity.identifier())
        self.assertEqual(identity.user_id, identity.identifier("user_id"))
        self.assertEqual(identity, UserIdentity.from_mapping(identity.as_dict()))

    def test_dispatcher_can_fan_out_and_isolate_sink_failure(self):
        recorder = RecordingSink()
        dispatcher = EventDispatcher([FailingSink(), recorder])
        event = WorkflowEvent.now("operation.completed", operation_id="x")
        dispatcher.emit(event, marker="ok")
        self.assertEqual(1, len(recorder.events))
        self.assertIs(event, recorder.events[0][0])
        self.assertEqual("ok", recorder.events[0][1]["marker"])

    def test_executor_no_longer_imports_premis_implementation(self):
        text = (ROOT / "noark5_workflow" / "executors" / "local.py").read_text(encoding="utf-8")
        self.assertNotIn("PremisProvenanceLogger", text)
        self.assertNotIn("premis_eligible", text)
        self.assertIn("WorkflowEvent", text)
        self.assertIn("event_dispatcher_for", text)

    def test_premis_is_an_event_sink(self):
        text = (ROOT / "noark5_workflow" / "sinks" / "premis.py").read_text(encoding="utf-8")
        self.assertIn("class PremisEventSink", text)
        self.assertIn('event.kind != "operation.completed"', text)

    def test_a18_uses_identity_provider_boundary(self):
        text = (ROOT / "gui" / "persistent_app_a18.py").read_text(encoding="utf-8")
        self.assertIn("LocalUserProfileIdentityProvider", text)
        self.assertIn("identity_provider.current_identity()", text)
        self.assertNotIn("load_user_profile()", text)


if __name__ == "__main__":
    unittest.main()
