from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable


class JobStatus(str, Enum):
    READY = "Klar"
    RUNNING = "Kjører"
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

    def __post_init__(self) -> None:
        self.source_root = Path(self.source_root)
        if self.output_root is not None:
            self.output_root = Path(self.output_root)
        if not self.name:
            self.name = self.source_root.name or self.job_id

    def set_workflow(self, operation_ids: Iterable[str]) -> None:
        self.workflow_ids = list(operation_ids)

    def set_operation_params(self, operation_id: str, params: dict) -> None:
        self.operation_params[operation_id] = deepcopy(dict(params))

    def get_operation_params(self, operation_id: str) -> dict:
        return deepcopy(self.operation_params.get(operation_id, {}))


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

    def add(self, job: Job) -> None:
        if any(existing.job_id == job.job_id for existing in self._jobs):
            raise ValueError(f"Jobb-ID finnes allerede: {job.job_id}")
        self._jobs.append(job)

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
