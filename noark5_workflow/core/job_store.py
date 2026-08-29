from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from .job import Job, JobBatch, JobStatus

FILE_TYPE = "noark5-workflow-manager-job-list"
FORMAT_VERSION = 1
FILE_EXTENSION = ".n5jobs"


class JobListFormatError(ValueError):
    pass


@dataclass(frozen=True)
class LoadedJobList:
    batch: JobBatch
    active_job_id: str | None
    created_at: str
    modified_at: str
    app_version: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Kan ikke lagre verdi av type {type(value).__name__} i jobblisten")


def _job_to_dict(job: Job) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "name": job.name,
        "source_root": str(job.source_root),
        "output_root": str(job.output_root) if job.output_root is not None else None,
        "workflow_ids": list(job.workflow_ids),
        "operation_params": _json_value(job.operation_params),
        "status": job.status.value,
        "progress": float(job.progress),
        "worker": job.worker,
        "message": job.message,
        "log_entries": list(job.log_entries),
    }


def _job_from_dict(data: dict[str, Any]) -> Job:
    job_id = str(data.get("job_id", "")).strip()
    source_root = str(data.get("source_root", "")).strip()
    if not job_id:
        raise JobListFormatError("Jobb mangler job_id")
    if not source_root:
        raise JobListFormatError(f"{job_id} mangler source_root")

    raw_status = data.get("status", JobStatus.READY.value)
    try:
        status = JobStatus(raw_status)
    except ValueError:
        status = JobStatus.READY

    # A persisted RUNNING state cannot still be running after a fresh app start.
    # Make it runnable again instead of presenting stale execution state.
    message = str(data.get("message", ""))
    if status == JobStatus.RUNNING:
        status = JobStatus.READY
        message = "Forrige kjøring var aktiv da jobblisten ble lagret"

    try:
        progress = max(0.0, min(1.0, float(data.get("progress", 0.0))))
    except (TypeError, ValueError):
        progress = 0.0

    params = data.get("operation_params", {})
    if not isinstance(params, dict):
        raise JobListFormatError(f"{job_id} har ugyldige operation_params")

    workflow_ids = data.get("workflow_ids", [])
    if not isinstance(workflow_ids, list):
        raise JobListFormatError(f"{job_id} har ugyldig workflow_ids")

    logs = data.get("log_entries", [])
    if not isinstance(logs, list):
        logs = []

    output_root = data.get("output_root")
    return Job(
        job_id=job_id,
        source_root=Path(source_root),
        output_root=Path(str(output_root)) if output_root else None,
        name=str(data.get("name", "")),
        workflow_ids=[str(value) for value in workflow_ids],
        operation_params=_json_value(params),
        status=status,
        progress=progress,
        worker=str(data.get("worker", "Lokal (denne PC-en)")),
        message=message,
        log_entries=[str(value) for value in logs][-2000:],
    )


def _existing_created_at(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(data, dict) and data.get("file_type") == FILE_TYPE:
        value = str(data.get("created_at", "")).strip()
        return value or None
    return None


def save_job_list(
    path: Path,
    batch: JobBatch,
    *,
    active_job_id: str | None = None,
    app_version: str = "",
) -> Path:
    path = Path(path)
    if path.suffix.lower() != FILE_EXTENSION:
        path = path.with_suffix(FILE_EXTENSION)
    path.parent.mkdir(parents=True, exist_ok=True)

    now = _now_iso()
    payload = {
        "file_type": FILE_TYPE,
        "format_version": FORMAT_VERSION,
        "app_version": app_version,
        "created_at": _existing_created_at(path) or now,
        "modified_at": now,
        "active_job_id": active_job_id,
        "jobs": [_job_to_dict(job) for job in batch.jobs()],
    }

    temp_path = path.with_name(path.name + ".tmp")
    try:
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
    return path


def load_job_list(path: Path) -> LoadedJobList:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise JobListFormatError(f"Kunne ikke lese jobblisten: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise JobListFormatError(f"Ugyldig JSON i jobblisten: {exc}") from exc

    if not isinstance(data, dict):
        raise JobListFormatError("Jobblisten må inneholde et JSON-objekt")
    if data.get("file_type") != FILE_TYPE:
        raise JobListFormatError("Filen er ikke en Noark 5 Workflow Manager-jobbliste")

    version = data.get("format_version")
    if version != FORMAT_VERSION:
        raise JobListFormatError(
            f"Jobblisteformat {version!r} støttes ikke (støttet versjon: {FORMAT_VERSION})"
        )

    raw_jobs = data.get("jobs", [])
    if not isinstance(raw_jobs, list):
        raise JobListFormatError("Feltet jobs må være en liste")

    batch = JobBatch()
    for raw_job in raw_jobs:
        if not isinstance(raw_job, dict):
            raise JobListFormatError("Ugyldig jobb i jobs-listen")
        batch.add(_job_from_dict(raw_job))

    active_job_id = data.get("active_job_id")
    if active_job_id is not None:
        active_job_id = str(active_job_id)
        if batch.get(active_job_id) is None:
            active_job_id = None

    return LoadedJobList(
        batch=batch,
        active_job_id=active_job_id,
        created_at=str(data.get("created_at", "")),
        modified_at=str(data.get("modified_at", "")),
        app_version=str(data.get("app_version", "")),
    )
