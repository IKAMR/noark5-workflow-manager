from pathlib import Path
import json
import tempfile
import unittest

from noark5_workflow.core.result_review import (
    RawTestResultRef,
    ResultAssessment,
    ResultAssessmentEvent,
    ResultDisposition,
    ResultReviewLedger,
)


class ResultReviewLedgerA17Tests(unittest.TestCase):
    def test_append_and_read_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = ResultReviewLedger(Path(td) / "review.jsonl")
            raw = RawTestResultRef("r1", "N5-X", "1")
            ledger.append(ResultAssessment(raw, ResultDisposition.ACCEPTED), actor="tester")
            events = ledger.events()
            self.assertEqual(1, len(events))
            self.assertEqual("tester", events[0].actor)
            self.assertEqual(ResultDisposition.ACCEPTED, events[0].assessment.disposition)

    def test_append_is_physically_append_only(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "review.jsonl"
            ledger = ResultReviewLedger(path)
            raw = RawTestResultRef("r1", "N5-X", "1")
            ledger.append(ResultAssessment(raw, ResultDisposition.REQUIRES_REVIEW), event_id="e1", recorded_at="2026-01-01T00:00:00+00:00")
            first = path.read_text(encoding="utf-8")
            ledger.append(ResultAssessment(raw, ResultDisposition.ACCEPTED), event_id="e2", recorded_at="2026-01-01T00:01:00+00:00")
            second = path.read_text(encoding="utf-8")
            self.assertTrue(second.startswith(first))
            self.assertEqual(2, len([x for x in second.splitlines() if x.strip()]))

    def test_latest_assessment_wins_without_deleting_history(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = ResultReviewLedger(Path(td) / "review.jsonl")
            raw = RawTestResultRef("r1", "N5-X", "1")
            ledger.append(ResultAssessment(raw, ResultDisposition.REQUIRES_REVIEW))
            ledger.append(ResultAssessment(raw, ResultDisposition.REJECTED_TEST_DEFECT, reason="Feil XPath"))
            self.assertEqual(2, len(ledger.events()))
            self.assertEqual(ResultDisposition.REJECTED_TEST_DEFECT, ledger.current_assessment("r1").disposition)

    def test_false_failure_does_not_enter_authoritative_projection(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = ResultReviewLedger(Path(td) / "review.jsonl")
            raw = RawTestResultRef("r1", "N5-X", "1")
            ledger.append(ResultAssessment(raw, ResultDisposition.REJECTED_TEST_DEFECT, reason="Feil test"))
            self.assertEqual([], ledger.authoritative_assessments())

    def test_accepted_retest_can_be_authoritative_while_old_failure_remains(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = ResultReviewLedger(Path(td) / "review.jsonl")
            old = RawTestResultRef("r1", "N5-X", "1")
            new = RawTestResultRef("r2", "N5-X", "2")
            ledger.append(ResultAssessment(old, ResultDisposition.REJECTED_TEST_DEFECT, reason="Feil XPath"))
            ledger.append(ResultAssessment(new, ResultDisposition.ACCEPTED))
            authoritative = ledger.authoritative_assessments()
            self.assertEqual(["r2"], [x.result.result_id for x in authoritative])
            self.assertEqual(2, len(ledger.events()))

    def test_superseded_result_is_not_authoritative(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = ResultReviewLedger(Path(td) / "review.jsonl")
            old = RawTestResultRef("r1", "N5-X", "1")
            ledger.append(ResultAssessment(old, ResultDisposition.SUPERSEDED, superseded_by_result_id="r2"))
            self.assertEqual([], ledger.authoritative_assessments())

    def test_unknown_schema_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "review.jsonl"
            path.write_text(json.dumps({"schema_version": 99}) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                ResultReviewLedger(path).events()

    def test_ledger_model_has_no_premis_dependency(self):
        import inspect
        import noark5_workflow.core.result_review as module
        text = inspect.getsource(module)
        self.assertNotIn("premis_logger", text)
        self.assertNotIn("PremisProvenanceLogger", text)


if __name__ == "__main__":
    unittest.main()
