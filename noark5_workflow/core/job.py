from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable


class JobStatus(str, Enum):
    READY = "Klar"
    RUNNING = "Kjører"
    WAITING = "Venter ved kontrollpunkt"
    OK = "Ferdig"
    FAILED = "Feil"
    SKIPPED = "Hoppet over"


@dataclass
class Job:
    """One workflow execution against one source/extraction."""

    job_id: str
    source_root: Path
    output_root: Path | None = None
    name: str = ""
    workflow_ids: list[str] = field(default_factory=list)
    operation_params: dict[str, dict] = field(default_factory=dict)
    status: JobStatus = JobStatus.READY
    progress: float = 0.0
    worker: str = "Lokal (denne PC-en)"
    message: str = ""
    log_entries: list[str] = field(default_factory=list)

    # v0.1.2-a2: planned stops and persistent execution cursor.
    # checkpoint_after contains operation IDs after which execution shall pause.
    # next_operation_index points to the next operation to execute (0-based).
    checkpoint_after: list[str] = field(default_factory=list)
    next_operation_index: int = 0

    def __post_init__(self) -> None:
        self.source_root = Path(self.source_root)
        if self.output_root is not None:
            self.output_root = Path(self.output_root)
        if not self.name:
            self.name = self.source_root.name or self.job_id
        self._normalise_checkpoint_state()

    def _normalise_checkpoint_state(self) -> None:
        valid = set(self.workflow_ids)
        self.checkpoint_after = [
            operation_id
            for operation_id in dict.fromkeys(self.checkpoint_after)
            if operation_id in valid
        ]
        try:
            index = int(self.next_operation_index)
        except (TypeError, ValueError):
            index = 0
        self.next_operation_index = max(0, min(index, len(self.workflow_ids)))

    def set_workflow(self, operation_ids: Iterable[str]) -> None:
        old_workflow = list(self.workflow_ids)
        self.workflow_ids = list(operation_ids)

        # Preserve checkpoints for operations that still exist.
        valid = set(self.workflow_ids)
        self.checkpoint_after = [
            operation_id
            for operation_id in self.checkpoint_after
            if operation_id in valid
        ]

        # Structural workflow edits invalidate an execution cursor.
        if self.workflow_ids != old_workflow:
            self.next_operation_index = 0
            if self.status == JobStatus.WAITING:
                self.status = JobStatus.READY
                self.progress = 0.0
                self.message = "Workflow endret - klar for ny kjøring"
        else:
            self._normalise_checkpoint_state()

    def set_operation_params(self, operation_id: str, params: dict) -> None:
        self.operation_params[operation_id] = deepcopy(dict(params))

    def get_operation_params(self, operation_id: str) -> dict:
        return deepcopy(self.operation_params.get(operation_id, {}))

    def set_checkpoint(self, operation_id: str, enabled: bool) -> None:
        if operation_id not in self.workflow_ids:
            raise ValueError(f"Operasjonen finnes ikke i workflow: {operation_id}")
        current = list(self.checkpoint_after)
        if enabled and operation_id not in current:
            current.append(operation_id)
        elif not enabled and operation_id in current:
            current.remove(operation_id)
        self.checkpoint_after = [
            oid for oid in self.workflow_ids if oid in set(current)
        ]

    def has_checkpoint(self, operation_id: str) -> bool:
        return operation_id in self.checkpoint_after

    def reset_execution(self, message: str = "") -> None:
        self.next_operation_index = 0
        self.progress = 0.0
        self.status = JobStatus.READY
        self.message = message

    def mark_operation_completed(self, operation_index: int) -> None:
        """Store cursor after a successfully completed 0-based operation index."""
        self.next_operation_index = max(
            0,
            min(operation_index + 1, len(self.workflow_ids)),
        )
        if self.workflow_ids:
            self.progress = self.next_operation_index / len(self.workflow_ids)

    def is_complete(self) -> bool:
        return bool(self.workflow_ids) and self.next_operation_index >= len(self.workflow_ids)


class JobBatch:
    """Ordered collection of jobs; execution/scheduling is handled by the app."""

    def __init__(self) -> None:
        self._jobs: list[Job] = []
        self._next_number = 1

    def new_job(
        self,
        source_root: Path,
        *,
        output_root: Path | None = None,
        name: str = "",
        workflow_ids: Iterable[str] = (),
    ) -> Job:
        job = Job(
            job_id=f"JOB-{self._next_number:03d}",
            source_root=Path(source_root),
            output_root=Path(output_root) if output_root else None,
            name=name,
            workflow_ids=list(workflow_ids),
        )
        self._next_number += 1
        self._jobs.append(job)
        return job

    def _update_next_number(self, job_id: str) -> None:
        if not job_id.startswith("JOB-"):
            return
        try:
            number = int(job_id[4:])
        except ValueError:
            return
        self._next_number = max(self._next_number, number + 1)

    def add(self, job: Job) -> None:
        if any(existing.job_id == job.job_id for existing in self._jobs):
            raise ValueError(f"Jobb-ID finnes allerede: {job.job_id}")
        self._jobs.append(job)
        self._update_next_number(job.job_id)

    def replace_all(self, jobs: Iterable[Job]) -> None:
        self._jobs = []
        self._next_number = 1
        for job in jobs:
            self.add(job)

    def clear(self) -> None:
        self._jobs = []
        self._next_number = 1

    def remove(self, job_id: str) -> bool:
        for index, job in enumerate(self._jobs):
            if job.job_id == job_id:
                del self._jobs[index]
                return True
        return False

    def get(self, job_id: str) -> Job | None:
        return next((job for job in self._jobs if job.job_id == job_id), None)

    def jobs(self) -> list[Job]:
        return list(self._jobs)

    def __len__(self) -> int:
        return len(self._jobs)

    def counts(self) -> dict[JobStatus, int]:
        return {status: sum(job.status == status for job in self._jobs) for status in JobStatus}
