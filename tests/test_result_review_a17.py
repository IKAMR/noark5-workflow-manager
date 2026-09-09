from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from noark5_workflow.core.result_review import (
    RawTestResultRef,
    ResultAssessment,
    ResultDisposition,
)


ROOT = Path(__file__).resolve().parents[1]


class ResultReviewA17Tests(unittest.TestCase):
    def test_raw_result_reference_is_immutable(self):
        raw = RawTestResultRef("r1", "N5-X", "1")
        with self.assertRaises(FrozenInstanceError):
            raw.test_id = "changed"

    def test_rejected_test_defect_requires_reason(self):
        raw = RawTestResultRef("r1", "N5-X", "1")
        with self.assertRaises(ValueError):
            ResultAssessment(raw, ResultDisposition.REJECTED_TEST_DEFECT)

    def test_false_failure_can_be_rejected_without_mutating_raw_result(self):
        raw = RawTestResultRef("r1", "N5-X", "1")
        assessment = ResultAssessment(
            raw,
            ResultDisposition.REJECTED_TEST_DEFECT,
            reason="Feil XPath i testdefinisjonen",
        )
        self.assertEqual(raw.definition_version, "1")
        self.assertFalse(assessment.contributes_to_authoritative_result)

    def test_superseded_result_requires_replacement_reference(self):
        raw = RawTestResultRef("r1", "N5-X", "1")
        with self.assertRaises(ValueError):
            ResultAssessment(raw, ResultDisposition.SUPERSEDED)
        assessment = ResultAssessment(
            raw,
            ResultDisposition.SUPERSEDED,
            superseded_by_result_id="r2",
        )
        self.assertFalse(assessment.contributes_to_authoritative_result)

    def test_accepted_result_can_contribute_to_authoritative_result(self):
        raw = RawTestResultRef("r2", "N5-X", "2")
        assessment = ResultAssessment(raw, ResultDisposition.ACCEPTED)
        self.assertTrue(assessment.contributes_to_authoritative_result)

    def test_confirmed_finding_can_contribute_to_authoritative_result(self):
        raw = RawTestResultRef("r3", "N5-Y", "1")
        assessment = ResultAssessment(raw, ResultDisposition.CONFIRMED_FINDING)
        self.assertTrue(assessment.contributes_to_authoritative_result)

    def test_model_has_no_premis_dependency(self):
        text = (ROOT / "noark5_workflow" / "core" / "result_review.py").read_text(encoding="utf-8")
        self.assertNotIn("premis_logger", text)
        self.assertNotIn("eventType", text)


class LoggingProvenanceDocumentationA17Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / "docs" / "LOGGING-PROVENANCE.md").read_text(encoding="utf-8")

    def test_document_separates_raw_result_and_authoritative_result(self):
        self.assertIn("rått testresultat", self.text)
        self.assertIn("autoritativt resultatsett", self.text)

    def test_document_preserves_false_failure_history_without_promoting_it(self):
        self.assertIn("testfeil identifisert", self.text)
        self.assertIn("underkjennes som feil i testapparatet", self.text)

    def test_document_says_premis_is_not_copy_of_technical_history(self):
        self.assertIn("PREMIS er en kontrollert projeksjon", self.text)
        self.assertIn("ikke brukes som database for all test- og saksbehandlingshistorikk", self.text)

    def test_document_keeps_a17_step1_conservative(self):
        self.assertIn("endrer **ikke** eksisterende PREMIS XML-format", self.text)
        self.assertIn("introduserer **ikke** automatisk faglig beslutningslogikk", self.text)


if __name__ == "__main__":
    unittest.main()
