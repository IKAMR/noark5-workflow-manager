from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.operation import BaseOperation, ExecutionTarget, OperationDefinition
from noark5_workflow.core.premis_logger import (
    DEFAULT_EVENT_TYPE,
    PREMIS_NS,
    PremisProvenanceLogger,
    VALID_EVENT_TYPES,
)
from noark5_workflow.core.result import OperationResult
from noark5_workflow.executors.local import LocalExecutor

_NS = {"premis": PREMIS_NS}


class _FakePremisOperation(BaseOperation):
    definition = OperationDefinition(
        operation_id="fake_premis",
        name="Fake PREMIS",
        description="Test",
        execution_target=ExecutionTarget.LOCAL,
    )
    premis_record = True
    premis_event_type = "Adjustment"
    premis_event_label = "testhendelse"

    def run(self, ctx: OperationContext) -> OperationResult:
        return OperationResult(True, "test utført", data={"value": 1})


class _InvalidPremisOperation(_FakePremisOperation):
    definition = OperationDefinition(
        operation_id="fake_invalid_premis",
        name="Fake invalid PREMIS",
        description="Test",
        execution_target=ExecutionTarget.LOCAL,
    )
    premis_event_type = "fri tekst"


class PremisProvenanceTests(unittest.TestCase):
    def test_logger_writes_noark_object_event_and_agent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "noark5-uttrekk"
            root.mkdir()
            ctx = OperationContext(extraction_root=root)
            op = _FakePremisOperation()
            result = op.run(ctx)

            logger = PremisProvenanceLogger(Path(td), root, agent_version="0.1.0")
            logger.record(op, result, ctx)
            out = logger.finalize(root, ctx)

            self.assertIsNotNone(out)
            self.assertTrue(out.exists())
            self.assertEqual(out.name, "noark5-uttrekk_premis.xml")

            xml_root = ET.parse(out).getroot()
            events = xml_root.findall("premis:event", _NS)
            agents = xml_root.findall("premis:agent", _NS)
            objects = xml_root.findall("premis:object", _NS)
            self.assertEqual(len(events), 1)
            self.assertEqual(len(agents), 1)
            self.assertEqual(len(objects), 1)
            self.assertEqual(events[0].find("premis:eventType", _NS).text, "Adjustment")
            detail = events[0].find("premis:eventDetail", _NS).text
            self.assertIn("testhendelse", detail)
            self.assertIn("test utført", detail)
            self.assertEqual(
                xml_root.find(".//premis:formatName", _NS).text,
                "NOARK-5",
            )
            self.assertEqual(
                xml_root.find(".//premis:agentName", _NS).text,
                "Noark 5 Workflow Manager",
            )

    def test_invalid_event_type_falls_back(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "uttrekk"
            root.mkdir()
            ctx = OperationContext(extraction_root=root)
            op = _InvalidPremisOperation()
            result = op.run(ctx)
            logger = PremisProvenanceLogger(Path(td), root)
            logger.record(op, result, ctx)
            out = logger.finalize(root, ctx)
            event_type = ET.parse(out).getroot().find("premis:event/premis:eventType", _NS).text
            self.assertEqual(event_type, DEFAULT_EVENT_TYPE)
            self.assertIn(DEFAULT_EVENT_TYPE, VALID_EVENT_TYPES)

    def test_local_executor_records_and_writes_premis(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "uttrekk"
            root.mkdir()
            output = Path(td) / "output"
            ctx = OperationContext(
                extraction_root=root,
                settings={
                    "enable_premis_provenance": True,
                    "premis_output_dir": str(output),
                },
            )
            result = LocalExecutor().execute(_FakePremisOperation(), ctx)
            self.assertTrue(result.ok)
            premis = output / "uttrekk_premis.xml"
            self.assertTrue(premis.exists())
            self.assertIn("premis_logger", ctx.metadata)
            self.assertIn("fake_premis", ctx.results)


    def test_executor_never_falls_back_to_source_parent(self):
        with tempfile.TemporaryDirectory() as td:
            source_parent = Path(td) / "source-area"
            root = source_parent / "uttrekk"
            root.mkdir(parents=True)
            ctx = OperationContext(
                extraction_root=root,
                settings={"enable_premis_provenance": True},
            )
            LocalExecutor().execute(_FakePremisOperation(), ctx)
            self.assertFalse((source_parent / "uttrekk_premis.xml").exists())
            self.assertNotIn("premis_logger", ctx.metadata)

    def test_dias_operation_uses_selected_output_for_workflow_premis(self):
        from noark5_workflow.operations.dias_package import DiasPackageOperation

        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "source" / "uttrekk"
            root.mkdir(parents=True)
            out = Path(td) / "chosen-output"
            aic = out / "1234-aic"
            op = DiasPackageOperation()
            op.configure({"output_dir": str(out)})
            ctx = OperationContext(extraction_root=root)
            result = OperationResult(True, "ok", data={"aic_path": str(aic)})
            self.assertEqual(op.premis_output_dir(result, ctx), out)

    def test_premis_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "uttrekk"
            root.mkdir()
            ctx = OperationContext(
                extraction_root=root,
                settings={"enable_premis_provenance": False},
            )
            LocalExecutor().execute(_FakePremisOperation(), ctx)
            self.assertFalse((Path(td) / "uttrekk_premis.xml").exists())


if __name__ == "__main__":
    unittest.main()
