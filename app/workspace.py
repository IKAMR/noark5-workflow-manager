from __future__ import annotations

from pathlib import Path


def _configured_path(settings: dict, key: str) -> Path | None:
    value = str(settings.get(key, "") or "").strip()
    return Path(value) if value else None


def workspace_root(settings: dict) -> Path:
    value = str(settings.get("temp_dir", "") or "").strip()
    if not value:
        # Keep the fallback local and explicit. Normal use should set temp_dir.
        return Path.cwd() / ".n5wfman-temp"
    return Path(value)


def run_log_dir(settings: dict) -> Path:
    return _configured_path(settings, "run_log_dir") or workspace_root(settings) / "logs" / "runs"


def setup_dir(settings: dict) -> Path:
    return _configured_path(settings, "setup_dir") or workspace_root(settings) / "setup"


def job_list_dir(settings: dict) -> Path:
    return _configured_path(settings, "job_list_dir") or workspace_root(settings) / "joblists"


def work_dir(settings: dict) -> Path:
    return workspace_root(settings) / "work"


def cache_dir(settings: dict) -> Path:
    return workspace_root(settings) / "cache"


def ensure_workspace(settings: dict) -> dict[str, Path]:
    paths = {
        "root": workspace_root(settings),
        "run_logs": run_log_dir(settings),
        "setup": setup_dir(settings),
        "joblists": job_list_dir(settings),
        "work": work_dir(settings),
        "cache": cache_dir(settings),
    }
    for key, path in paths.items():
        if key != "root":
            path.mkdir(parents=True, exist_ok=True)
    paths["root"].mkdir(parents=True, exist_ok=True)
    return paths


def effective_dirs(settings: dict) -> dict[str, Path]:
    return {
        "run_log_dir": run_log_dir(settings),
        "setup_dir": setup_dir(settings),
        "job_list_dir": job_list_dir(settings),
    }
