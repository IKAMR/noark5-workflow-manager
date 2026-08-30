from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.workspace import ensure_workspace, run_log_dir


def _now() -> datetime:
    return datetime.now().astimezone()


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _status_text(job) -> str:
    status = getattr(job, "status", "")
    value = getattr(status, "value", None)
    if value is not None:
        return str(value)
    name = getattr(status, "name", None)
    if name is not None:
        return str(name)
    return str(status)


@dataclass
class JobRunRecord:
    job_id: str
    name: str
    source: str
    output: str
    started: datetime
    finished: datetime | None = None
    status: str = ""
    message: str = ""


class RunOverviewLog:
    """One human-readable overview log per single or batch run."""

    def __init__(
        self,
        settings: dict,
        *,
        run_type: str,
        app_version: str,
        job_list_path: Path | None = None,
        planned_jobs: int | None = None,
    ) -> None:
        ensure_workspace(settings)
        self.run_type = run_type.lower()
        self.app_version = app_version
        self.job_list_path = Path(job_list_path) if job_list_path else None
        self.planned_jobs = planned_jobs
        self.started = _now()
        self.finished: datetime | None = None
        self.run_status = "STARTET"
        self.error_message = ""
        self.phase = "Oppretter kjøring"
        self.run_id = (
            f"RUN-{self.started.strftime('%Y%m%d-%H%M%S')}-"
            f"{uuid4().hex[:8]}"
        )
        suffix = "BATCH" if self.run_type == "batch" else "SINGLE"
        filename = (
            f"{self.started.strftime('%Y-%m-%d_%H%M%S')}_"
            f"{suffix}_{self.run_id[-8:]}.log"
        )
        self.path = run_log_dir(settings) / filename
        self.records: list[JobRunRecord] = []
        self._current: dict[str, JobRunRecord] = {}
        self._write()

    def set_phase(self, phase: str) -> None:
        self.phase = str(phase)
        self._write()

    def start_job(self, job) -> None:
        job_id = str(getattr(job, "job_id", ""))
        if job_id in self._current:
            return
        record = JobRunRecord(
            job_id=job_id,
            name=str(getattr(job, "name", "")),
            source=str(getattr(job, "source_root", "") or ""),
            output=str(getattr(job, "output_root", "") or ""),
            started=_now(),
        )
        self.records.append(record)
        self._current[record.job_id] = record
        self._write()

    def finish_job(self, job) -> None:
        job_id = str(getattr(job, "job_id", ""))
        record = self._current.get(job_id)
        if record is None:
            self.start_job(job)
            record = self._current[job_id]
        record.finished = _now()
        record.status = _status_text(job)
        record.message = str(getattr(job, "message", "") or "")
        record.output = str(getattr(job, "output_root", "") or "")
        self._write()

    def fail(self, exc: BaseException | str) -> Path:
        self.run_status = "FEIL"
        self.error_message = str(exc)
        self.finished = _now()
        self._write()
        return self.path

    def finish(self, status: str = "FERDIG") -> Path:
        if self.run_status != "FEIL":
            self.run_status = status
        self.finished = self.finished or _now()
        self._write()
        return self.path

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = [
            "Noark 5 Workflow Manager - overordnet kjørelogg",
            "",
            f"Run ID: {self.run_id}",
            f"Kjøretype: {self.run_type}",
            f"Status: {self.run_status}",
            f"Fase: {self.phase}",
            f"App-versjon: {self.app_version}",
            f"Start: {_iso(self.started)}",
            f"Slutt: {_iso(self.finished) if self.finished else ''}",
            f"Jobbliste: {self.job_list_path or ''}",
            f"Planlagte jobber: {self.planned_jobs if self.planned_jobs is not None else ''}",
        ]
        if self.error_message:
            lines.append(f"Feil: {self.error_message}")
        lines.append("")

        for index, record in enumerate(self.records, start=1):
            lines.extend(
                [
                    f"JOBB {index}",
                    f"Jobb-ID: {record.job_id}",
                    f"Navn: {record.name}",
                    f"Source: {record.source}",
                    f"Output: {record.output}",
                    f"Start: {_iso(record.started)}",
                    f"Slutt: {_iso(record.finished) if record.finished else ''}",
                    f"Status: {record.status}",
                    f"Resultat: {record.message}",
                    "",
                ]
            )

        if self.finished is not None:
            completed = sum(1 for r in self.records if r.finished is not None)
            ok = sum(1 for r in self.records if r.status.lower() in {"ok", "completed", "success", "ferdig"})
            failed = sum(1 for r in self.records if "fail" in r.status.lower() or "feil" in r.status.lower())
            waiting = sum(1 for r in self.records if "wait" in r.status.lower() or "venter" in r.status.lower())
            skipped = sum(1 for r in self.records if "skip" in r.status.lower() or "hopp" in r.status.lower())
            lines.extend(
                [
                    "SAMMENDRAG",
                    f"Planlagte jobber: {self.planned_jobs if self.planned_jobs is not None else len(self.records)}",
                    f"Startede jobber: {len(self.records)}",
                    f"Ferdigbehandlede jobber: {completed}",
                    f"OK: {ok}",
                    f"Feil: {failed}",
                    f"Venter: {waiting}",
                    f"Hoppet over: {skipped}",
                    "",
                ]
            )

        self.path.write_text("\n".join(lines), encoding="utf-8")
