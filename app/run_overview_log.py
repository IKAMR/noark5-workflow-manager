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
    source_root: str
    source_extraction: str
    work_root: str
    work_operations: str
    archive_root: str
    output: str
    started: datetime
    finished: datetime | None = None
    status: str = ""
    message: str = ""


class RunOverviewLog:
    """One human-readable overview log per single or batch run.

    The canonical log is always written to the application's configured run-log
    directory. By default the same live log is mirrored into each job's
    Arbeid – operasjoner area under ``wf/logs``. This gives both a global
    operational history and a job-local copy without confusing PREMIS with the
    ordinary execution log.
    """

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
        self.settings = dict(settings)
        self.mirror_to_work_operations = bool(
            self.settings.get("copy_run_log_to_work_operations", True)
        )
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
        source_root = str(getattr(job, "source_root", "") or "")
        source_extraction = str(getattr(job, "source_extraction", "") or "")
        active_source = str(getattr(job, "active_extraction_root", "") or source_root)
        work_root = str(getattr(job, "work_root", "") or "")
        work_operations = str(getattr(job, "work_operations", "") or "")
        archive_root = str(getattr(job, "archive_root", "") or "")
        output = archive_root or str(getattr(job, "output_root", "") or "")
        record = JobRunRecord(
            job_id=job_id,
            name=str(getattr(job, "name", "")),
            source=active_source,
            source_root=source_root,
            source_extraction=source_extraction,
            work_root=work_root,
            work_operations=work_operations,
            archive_root=archive_root,
            output=output,
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
        record.work_root = str(getattr(job, "work_root", "") or "")
        record.work_operations = str(getattr(job, "work_operations", "") or "")
        record.archive_root = str(getattr(job, "archive_root", "") or "")
        record.output = record.archive_root or str(getattr(job, "output_root", "") or "")
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

    def _render(self) -> str:
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
                    f"Source - hovedmappe: {record.source_root}",
                    f"Source - uttrekksmappe: {record.source_extraction or record.source}",
                    f"Arbeid - hovedmappe: {record.work_root}",
                    f"Arbeid - operasjoner: {record.work_operations}",
                    f"Arkiv - hovedmappe: {record.archive_root}",
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
        return "\n".join(lines)

    def _mirror(self, text: str) -> None:
        if not self.mirror_to_work_operations:
            return
        targets = {
            Path(record.work_operations)
            for record in self.records
            if record.work_operations
        }
        for work_operations in targets:
            try:
                mirror_dir = work_operations / "wf" / "logs"
                mirror_dir.mkdir(parents=True, exist_ok=True)
                (mirror_dir / self.path.name).write_text(text, encoding="utf-8")
            except OSError:
                # The central log remains authoritative. A mirror failure must
                # never stop the workflow itself.
                continue

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = self._render()
        self.path.write_text(text, encoding="utf-8")
        self._mirror(text)
