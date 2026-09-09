from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ResultDisposition(str, Enum):
    """Review state for a raw test result.

    This is deliberately independent from PREMIS. a17 step 1 models the
    distinction between an observed result and a later assessment only.
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED_TEST_DEFECT = "rejected_test_defect"
    SUPERSEDED = "superseded"
    REQUIRES_REVIEW = "requires_review"
    CONFIRMED_FINDING = "confirmed_finding"


@dataclass(frozen=True)
class RawTestResultRef:
    """Immutable reference to one raw test result.

    The actual structured result remains owned by the test/analyse layer. This
    reference is intentionally small so a17 does not introduce a new result
    file format prematurely.
    """

    result_id: str
    test_id: str
    definition_version: str = ""

    def __post_init__(self) -> None:
        if not self.result_id.strip():
            raise ValueError("result_id kan ikke være tom")
        if not self.test_id.strip():
            raise ValueError("test_id kan ikke være tom")


@dataclass(frozen=True)
class ResultAssessment:
    """Append-only style assessment of a raw result.

    The assessment never mutates RawTestResultRef. Persistence, actor identity,
    timestamps and provenance policy are intentionally left for later a17 work.
    """

    result: RawTestResultRef
    disposition: ResultDisposition = ResultDisposition.PENDING
    reason: str = ""
    superseded_by_result_id: str = ""

    def __post_init__(self) -> None:
        if self.disposition == ResultDisposition.REJECTED_TEST_DEFECT and not self.reason.strip():
            raise ValueError("rejected_test_defect krever begrunnelse")
        if self.disposition == ResultDisposition.SUPERSEDED and not self.superseded_by_result_id.strip():
            raise ValueError("superseded krever superseded_by_result_id")

    @property
    def contributes_to_authoritative_result(self) -> bool:
        """Whether this assessment may contribute to the current result set.

        This is not a PREMIS decision. It only expresses the a17 distinction
        between active/confirmed evidence and rejected/superseded history.
        """

        return self.disposition in {
            ResultDisposition.ACCEPTED,
            ResultDisposition.CONFIRMED_FINDING,
        }


class ProvenanceEligibility(str, Enum):
    """Classification of whether an executed event may reach PREMIS.

    Eligibility is intentionally separate from ResultDisposition: an
    authoritative test result is not automatically a PREMIS event.
    """

    TECHNICAL_ONLY = "technical_only"
    JOB_HISTORY = "job_history"
    PROVENANCE_CANDIDATE = "provenance_candidate"


def premis_eligible(operation, result, ctx) -> bool:
    """Return True only for explicitly declared provenance candidates.

    This is a conservative gate. It does not decide the final PREMIS policy;
    it prevents technical/preflight activity from reaching PREMIS merely
    because an operation happened to implement the old premis_record flag.
    Legacy operations without an explicit classification retain current
    behaviour during a17 migration.
    """
    classification = getattr(operation, "provenance_eligibility", None)
    if classification is None:
        return bool(operation.premis_should_record(result, ctx))
    try:
        classification = ProvenanceEligibility(classification)
    except ValueError:
        return False
    return bool(
        classification == ProvenanceEligibility.PROVENANCE_CANDIDATE
        and operation.premis_should_record(result, ctx)
    )


# ---------------------------------------------------------------------------
# a17 step 3: append-only review ledger
# ---------------------------------------------------------------------------

import datetime as _dt
import json as _json
import uuid as _uuid
from pathlib import Path as _Path


@dataclass(frozen=True)
class ResultAssessmentEvent:
    """Durable append-only record of one assessment decision.

    The raw result remains immutable. A later correction is represented by a
    new event, never by rewriting a previous event. This is intentionally a
    project-internal JSONL contract for a17 and is not PREMIS.
    """

    event_id: str
    recorded_at: str
    assessment: ResultAssessment
    actor: str = ""

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id kan ikke være tom")
        if not self.recorded_at.strip():
            raise ValueError("recorded_at kan ikke være tom")

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "event_id": self.event_id,
            "recorded_at": self.recorded_at,
            "actor": self.actor,
            "result": {
                "result_id": self.assessment.result.result_id,
                "test_id": self.assessment.result.test_id,
                "definition_version": self.assessment.result.definition_version,
            },
            "assessment": {
                "disposition": self.assessment.disposition.value,
                "reason": self.assessment.reason,
                "superseded_by_result_id": self.assessment.superseded_by_result_id,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResultAssessmentEvent":
        if int(data.get("schema_version", 0)) != 1:
            raise ValueError("Ukjent schema_version for vurderingshendelse")
        result_data = dict(data.get("result") or {})
        assessment_data = dict(data.get("assessment") or {})
        raw = RawTestResultRef(
            str(result_data.get("result_id", "")),
            str(result_data.get("test_id", "")),
            str(result_data.get("definition_version", "")),
        )
        assessment = ResultAssessment(
            raw,
            ResultDisposition(str(assessment_data.get("disposition", "pending"))),
            reason=str(assessment_data.get("reason", "")),
            superseded_by_result_id=str(assessment_data.get("superseded_by_result_id", "")),
        )
        return cls(
            event_id=str(data.get("event_id", "")),
            recorded_at=str(data.get("recorded_at", "")),
            actor=str(data.get("actor", "")),
            assessment=assessment,
        )


class ResultReviewLedger:
    """Append-only JSONL ledger for raw-result assessments.

    This keeps the audit trail necessary for false failures and superseded
    results while allowing callers to derive a current authoritative view.
    It deliberately does not create PREMIS and does not alter raw test files.
    """

    def __init__(self, path) -> None:
        self.path = _Path(path)

    @staticmethod
    def _now() -> str:
        return _dt.datetime.now().astimezone().isoformat(timespec="seconds")

    def append(
        self,
        assessment: ResultAssessment,
        *,
        actor: str = "",
        event_id: str | None = None,
        recorded_at: str | None = None,
    ) -> ResultAssessmentEvent:
        event = ResultAssessmentEvent(
            event_id=event_id or str(_uuid.uuid4()),
            recorded_at=recorded_at or self._now(),
            actor=actor,
            assessment=assessment,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(_json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return event

    def events(self) -> list[ResultAssessmentEvent]:
        if not self.path.is_file():
            return []
        events: list[ResultAssessmentEvent] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                text = line.strip()
                if not text:
                    continue
                try:
                    data = _json.loads(text)
                    events.append(ResultAssessmentEvent.from_dict(data))
                except Exception as exc:
                    raise ValueError(
                        f"Ugyldig vurderingslogg på linje {line_number}: {exc}"
                    ) from exc
        return events

    def latest_by_result_id(self) -> dict[str, ResultAssessmentEvent]:
        latest: dict[str, ResultAssessmentEvent] = {}
        for event in self.events():
            latest[event.assessment.result.result_id] = event
        return latest

    def current_assessment(self, result_id: str) -> ResultAssessment | None:
        event = self.latest_by_result_id().get(result_id)
        return event.assessment if event else None

    def authoritative_assessments(self) -> list[ResultAssessment]:
        """Return current assessments allowed to contribute to final results.

        History is never deleted; this merely derives the present authoritative
        projection from the latest assessment for each raw result.
        """
        assessments = [event.assessment for event in self.latest_by_result_id().values()]
        return [item for item in assessments if item.contributes_to_authoritative_result]
