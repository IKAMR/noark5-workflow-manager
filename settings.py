from __future__ import annotations

import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"

DEFAULT_CONFIG = {
    "execution_backend": "local",
    "remote_endpoint": "",
    "shared_storage_root": "",
    "temp_dir": "",
    "log_level": "INFO",
    "operation_visibility": 2,
    "appearance_mode": "dark",
    "font_offset": 0,
    "last_noark_source_dir": "",
    "last_dias_output_dir": "",
    "last_mets_import_dir": "",
    "last_dias_add_file_dir": "",
    "last_dias_add_folder_dir": "",
}


def load_config() -> dict:
    data = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update(loaded)
        except (OSError, json.JSONDecodeError):
            pass
    return data


def save_config(changes: dict) -> dict:
    data = load_config()
    data.update(changes)
    CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return data
