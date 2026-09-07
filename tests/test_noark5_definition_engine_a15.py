from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from noark5_workflow.analysis.definition_engine import run_definition_analysis
from noark5_workflow.core.context import OperationContext
from noark5_workflow.operations.analyse_noark5_core import (
    AnalyseNoark5CoreOperation,
    DEFINITION_PATH,
)


ROOT = Path(__file__).resolve().parents[1]


XML = """<?xml version="1.0" encoding="UTF-8"?>
<arkiv xmlns="urn:test">
  <systemID>A-1</systemID>
  <tittel>Testarkiv</tittel>
  <arkivstatus>Avsluttet</arkivstatus>
  <arkivskaper>
    <arkivskaperID>ORG-1</arkivskaperID>
    <arkivskaperNavn>Test kommune</arkivskaperNavn>
  </arkivskaper>
  <arkivdel>
    <systemID>AD-1</systemID>
    <tittel>Arkivdel 1</tittel>
    <arkivdelstatus>Avsluttet periode</arkivdelstatus>
    <mappe><registrering><dokumentbeskrivelse><dokumentobjekt/></dokumentbeskrivelse></registrering></mappe>
  </arkivdel>
  <arkivdel>
    <systemID>AD-2</systemID>
    <tittel>Arkivdel 2</tittel>
    <mappe/>
    <mappe/>
  </arkivdel>
</arkiv>
"""


class Noark5DefinitionEngineA15Tests(unittest.TestCase):
    def test_definition_is_external_and_references_u1_u2(self):
        data = json.loads(DEFINITION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(["U1", "U2"], data["basis"]["source_material"])
        self.assertIn("C01", data["basis"]["kdrs_query_jobs"])
        self.assertIn("U02", data["basis"]["kdrs_query_jobs"])

    def test_engine_has_no_noark_xpath_literals(self):
        source = (ROOT / "noark5_workflow" / "analysis" / "definition_engine.py").read_text(encoding="utf-8")
        self.assertNotIn("local-name()='arkiv'", source)
        self.assertNotIn("local-name()='arkivdel'", source)

    def test_extracts_archive_and_archive_parts(self):
        with tempfile.TemporaryDirectory() as temp:
            xml = Path(temp) / "arkivstruktur.xml"
            xml.write_text(XML, encoding="utf-8")
            result = run_definition_analysis(xml, DEFINITION_PATH)
            self.assertEqual(1, result["summary"]["entity_counts"]["archive"])
            self.assertEqual(2, result["summary"]["entity_counts"]["archive_part"])
            self.assertEqual("Testarkiv", result["entities"]["archive"][0]["fields"]["title"])
            self.assertEqual("AD-2", result["entities"]["archive_part"][1]["fields"]["system_id"])

    def test_per_archive_part_metrics_are_independent(self):
        with tempfile.TemporaryDirectory() as temp:
            xml = Path(temp) / "arkivstruktur.xml"
            xml.write_text(XML, encoding="utf-8")
            result = run_definition_analysis(xml, DEFINITION_PATH)
            first, second = result["entities"]["archive_part"]
            self.assertEqual(1, first["metrics"]["mappe_count"])
            self.assertEqual(2, second["metrics"]["mappe_count"])
            self.assertEqual(1, first["metrics"]["dokumentobjekt_count"])
            self.assertEqual(0, second["metrics"]["dokumentobjekt_count"])

    def test_parent_archive_context_is_available_per_archive_part(self):
        with tempfile.TemporaryDirectory() as temp:
            xml = Path(temp) / "arkivstruktur.xml"
            xml.write_text(XML, encoding="utf-8")
            result = run_definition_analysis(xml, DEFINITION_PATH)
            part = result["entities"]["archive_part"][0]
            self.assertEqual("A-1", part["fields"]["parent_archive_system_id"])
            self.assertEqual("Testarkiv", part["fields"]["parent_archive_title"])

    def test_archive_creator_is_child_data_not_report_text(self):
        with tempfile.TemporaryDirectory() as temp:
            xml = Path(temp) / "arkivstruktur.xml"
            xml.write_text(XML, encoding="utf-8")
            result = run_definition_analysis(xml, DEFINITION_PATH)
            creators = result["entities"]["archive"][0]["children"]["creators"]
            self.assertEqual("ORG-1", creators[0]["fields"]["id"])
            self.assertEqual("Test kommune", creators[0]["fields"]["name"])

    def test_operation_writes_to_noark5_tests_native(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            xml = root / "arkivstruktur.xml"
            xml.write_text(XML, encoding="utf-8")
            work = root / "work"
            work.mkdir()
            ctx = OperationContext(extraction_root=root, work_operations=work)
            result = AnalyseNoark5CoreOperation().run(ctx)
            self.assertTrue(result.ok)
            report = Path(result.data["report"])
            self.assertEqual(work / "noark5_tests" / "native" / "noark5-analysis-arkiv-arkivdel.json", report)
            self.assertTrue(report.is_file())

    def test_report_views_are_separate_from_analysis_definition(self):
        analysis = json.loads(DEFINITION_PATH.read_text(encoding="utf-8"))
        views_path = ROOT / "config" / "noark5" / "report_views" / "u1_u2_views.json"
        views = json.loads(views_path.read_text(encoding="utf-8"))
        self.assertNotIn("views", analysis)
        ids = {item["id"] for item in views["views"]}
        self.assertIn("u1_whole_extraction", ids)
        self.assertIn("u2_per_archive_part", ids)


if __name__ == "__main__":
    unittest.main()
