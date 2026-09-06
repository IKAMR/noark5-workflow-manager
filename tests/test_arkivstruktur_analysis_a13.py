from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from noark5_workflow.analysis.arkivstruktur import analyse_arkivstruktur
from noark5_workflow.core.context import OperationContext
from noark5_workflow.operations.analyse_arkivstruktur import AnalyseArkivstrukturOperation
from noark5_workflow.sources.noark5_extraction import Noark5Extraction


SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<arkivstruktur xmlns="urn:test:noark5">
  <arkiv>
    <arkivdel>
      <klassifikasjonssystem>
        <klasse>
          <mappe>
            <registrering>
              <dokumentbeskrivelse>
                <dokumentobjekt/>
                <dokumentobjekt/>
              </dokumentbeskrivelse>
            </registrering>
          </mappe>
          <mappe/>
        </klasse>
      </klassifikasjonssystem>
    </arkivdel>
  </arkiv>
</arkivstruktur>
"""


class ArkivstrukturAnalysisA13Tests(unittest.TestCase):
    def _write_sample(self, root: Path, text: str = SAMPLE) -> Path:
        path = root / "arkivstruktur.xml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_streamed_analysis_counts_key_noark_elements(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self._write_sample(Path(temp))
            result = analyse_arkivstruktur(path)

            self.assertEqual(result.root_element, "arkivstruktur")
            self.assertEqual(result.namespace, "urn:test:noark5")
            self.assertEqual(result.key_counts["arkiv"], 1)
            self.assertEqual(result.key_counts["arkivdel"], 1)
            self.assertEqual(result.key_counts["klasse"], 1)
            self.assertEqual(result.key_counts["mappe"], 2)
            self.assertEqual(result.key_counts["registrering"], 1)
            self.assertEqual(result.key_counts["dokumentbeskrivelse"], 1)
            self.assertEqual(result.key_counts["dokumentobjekt"], 2)

    def test_analysis_exposes_complete_element_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self._write_sample(Path(temp))
            result = analyse_arkivstruktur(path)

            self.assertEqual(result.element_counts["arkivstruktur"], 1)
            self.assertEqual(result.element_counts["dokumentobjekt"], 2)
            self.assertEqual(
                result.total_elements,
                sum(result.element_counts.values()),
            )
            self.assertGreater(result.bytes, 0)

    def test_operation_returns_structured_analysis_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write_sample(root)
            source = Noark5Extraction.detect(root)
            ctx = OperationContext(extraction_root=root, source=source)

            result = AnalyseArkivstrukturOperation().run(ctx)

            self.assertTrue(result.ok)
            self.assertEqual(result.data["root_element"], "arkivstruktur")
            self.assertEqual(result.data["key_counts"]["mappe"], 2)
            self.assertNotIn("plassholder", result.message.lower())

    def test_operation_reports_invalid_xml_as_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write_sample(root, "<arkivstruktur><arkiv></arkivstruktur>")
            source = Noark5Extraction.detect(root)
            ctx = OperationContext(extraction_root=root, source=source)

            result = AnalyseArkivstrukturOperation().run(ctx)

            self.assertFalse(result.ok)
            self.assertIn("feilet", result.message.lower())

    def test_analysis_does_not_claim_u1_u2_validation(self):
        source = Path(__file__).resolve().parents[1] / "noark5_workflow" / "operations" / "analyse_arkivstruktur.py"
        text = source.read_text(encoding="utf-8").lower()
        self.assertNotIn("u1 godkjent", text)
        self.assertNotIn("u2 godkjent", text)


if __name__ == "__main__":
    unittest.main()
