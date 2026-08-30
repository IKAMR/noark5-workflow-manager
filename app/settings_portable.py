from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from settings import CONFIG_PATH, DEFAULT_CONFIG

FILE_TYPE = "noark5-workflow-manager-settings"
FORMAT_VERSION = 1


def _known_settings(data: dict[str, Any]) -> dict[str, Any]:
    return {key: data[key] for key in DEFAULT_CONFIG if key in data}


def write_full_config(data: dict[str, Any]) -> dict[str, Any]:
    merged = dict(DEFAULT_CONFIG)
    merged.update(_known_settings(data))
    CONFIG_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return merged


def _load_current() -> dict[str, Any]:
    data = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.is_file():
        try:
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            loaded = {}
        if isinstance(loaded, dict):
            data.update(_known_settings(loaded))
    return data


def export_settings(path: Path) -> Path:
    path = Path(path)
    if path.suffix.lower() != ".json":
        path = path.with_suffix(".json")
    payload = {
        "file_type": FILE_TYPE,
        "format_version": FORMAT_VERSION,
        "settings": _known_settings(_load_current()),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def import_settings(path: Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("file_type") != FILE_TYPE:
        raise ValueError("Filen er ikke en Noark 5 Workflow Manager-innstillingseksport")
    if data.get("format_version") != FORMAT_VERSION:
        raise ValueError(f"Ustøttet innstillingsformat: {data.get('format_version')}")
    settings = data.get("settings")
    if not isinstance(settings, dict):
        raise ValueError("Eksportfilen mangler settings")
    return write_full_config(settings)


def reset_settings() -> dict[str, Any]:
    return write_full_config(dict(DEFAULT_CONFIG))
