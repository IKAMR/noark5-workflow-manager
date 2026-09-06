from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FILE_TYPE = "workflow-manager-project"
FORMAT_VERSION = 1
FILE_NAME = "project.json"


class ProjectConfigError(ValueError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ProjectConfig:
    project_name: str
    profile_id: str
    job_list_file: str
    job_profile_id: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    modified_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_type": FILE_TYPE,
            "format_version": FORMAT_VERSION,
            "project_name": self.project_name,
            "profile_id": self.profile_id,
            "job_profile_id": self.job_profile_id,
            "job_list_file": self.job_list_file,
            "settings": dict(self.settings),
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }


def project_dir(work_operations: str | Path) -> Path:
    return Path(work_operations) / "wf"


def project_file(work_operations: str | Path) -> Path:
    return project_dir(work_operations) / FILE_NAME


def is_project_job_list_path(path: str | Path, work_operations: str | Path) -> bool:
    path = Path(path)
    return path.parent == project_dir(work_operations)


def load_project(path: str | Path) -> ProjectConfig:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ProjectConfigError(f"Kunne ikke lese project.json: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ProjectConfigError(f"Ugyldig JSON i project.json: {exc}") from exc

    if not isinstance(data, dict):
        raise ProjectConfigError("project.json må inneholde et JSON-objekt")
    if data.get("file_type") != FILE_TYPE:
        raise ProjectConfigError("Filen er ikke en Workflow Manager project.json")
    if data.get("format_version") != FORMAT_VERSION:
        raise ProjectConfigError(
            f"project.json format {data.get('format_version')!r} støttes ikke"
        )

    settings = data.get("settings", {})
    if not isinstance(settings, dict):
        raise ProjectConfigError("settings i project.json må være et objekt")

    return ProjectConfig(
        project_name=str(data.get("project_name", "")),
        profile_id=str(data.get("profile_id", "")),
        job_profile_id=(
            str(data["job_profile_id"]) if data.get("job_profile_id") else None
        ),
        job_list_file=str(data.get("job_list_file", "")),
        settings=dict(settings),
        created_at=str(data.get("created_at", "")),
        modified_at=str(data.get("modified_at", "")),
    )


def save_project(
    path: str | Path,
    *,
    project_name: str,
    profile_id: str,
    job_list_file: str,
    job_profile_id: str | None = None,
    settings: dict[str, Any] | None = None,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    created_at = ""
    if path.is_file():
        try:
            created_at = load_project(path).created_at
        except ProjectConfigError:
            created_at = ""

    now = _now_iso()
    config = ProjectConfig(
        project_name=project_name,
        profile_id=profile_id,
        job_profile_id=job_profile_id,
        job_list_file=job_list_file,
        settings=dict(settings or {}),
        created_at=created_at or now,
        modified_at=now,
    )

    temp = path.with_name(path.name + ".tmp")
    try:
        temp.write_text(
            json.dumps(config.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temp.replace(path)
    finally:
        if temp.exists():
            try:
                temp.unlink()
            except OSError:
                pass
    return path
