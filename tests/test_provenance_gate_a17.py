import unittest
from types import SimpleNamespace

from noark5_workflow.core.result_review import ProvenanceEligibility, premis_eligible


class FakeOperation:
    premis_record = True
    provenance_eligibility = ProvenanceEligibility.PROVENANCE_CANDIDATE
    def premis_should_record(self, result, ctx):
        return bool(self.premis_record and result.ok)


class ProvenanceGateA17Tests(unittest.TestCase):
    def test_candidate_success_is_eligible(self):
        self.assertTrue(premis_eligible(FakeOperation(), SimpleNamespace(ok=True), None))

    def test_candidate_failure_is_not_eligible_by_default(self):
        self.assertFalse(premis_eligible(FakeOperation(), SimpleNamespace(ok=False), None))

    def test_technical_only_never_reaches_premis(self):
        op = FakeOperation()
        op.provenance_eligibility = ProvenanceEligibility.TECHNICAL_ONLY
        self.assertFalse(premis_eligible(op, SimpleNamespace(ok=True), None))

    def test_job_history_never_reaches_premis(self):
        op = FakeOperation()
        op.provenance_eligibility = ProvenanceEligibility.JOB_HISTORY
        self.assertFalse(premis_eligible(op, SimpleNamespace(ok=True), None))

    def test_unknown_classification_fails_closed(self):
        op = FakeOperation()
        op.provenance_eligibility = "future-value"
        self.assertFalse(premis_eligible(op, SimpleNamespace(ok=True), None))

    def test_legacy_operation_keeps_current_behaviour_during_migration(self):
        class LegacyOperation:
            premis_record = True
            def premis_should_record(self, result, ctx):
                return bool(self.premis_record and result.ok)
        self.assertTrue(premis_eligible(LegacyOperation(), SimpleNamespace(ok=True), None))
