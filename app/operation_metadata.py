from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "operations.json"

MATURITY_LEVELS = {
    "alpha": 0,
    "beta": 1,
    "stable": 2,
}

MATURITY_LABELS = {
    "alpha": "Alpha",
    "beta": "Beta",
    "stable": "Stabil",
}

MATURITY_SHORT_LABELS = {
    "alpha": "A",
    "beta": "B",
    "stable": "S",
}

VISIBILITY_LABELS = {
    0: "Alle (inkl. Alpha)",
    1: "Beta og stabile",
    2: "Kun stabile",
}

VISIBILITY_VALUES = {label: value for value, label in VISIBILITY_LABELS.items()}


@lru_cache(maxsize=1)
def load_operation_metadata() -> dict:
    try:
        data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return {"operations": {}}
    if not isinstance(data, dict):
        return {"operations": {}}
    operations = data.get("operations", {})
    if not isinstance(operations, dict):
        operations = {}
    return {**data, "operations": operations}


def maturity_name(operation_id: str) -> str:
    operations = load_operation_metadata().get("operations", {})
    raw = operations.get(operation_id, {})
    if not isinstance(raw, dict):
        raw = {}
    maturity = str(raw.get("maturity", "alpha")).strip().lower()
    return maturity if maturity in MATURITY_LEVELS else "alpha"


def maturity_level(operation_id: str) -> int:
    return MATURITY_LEVELS[maturity_name(operation_id)]


def maturity_label(operation_id: str) -> str:
    return MATURITY_LABELS[maturity_name(operation_id)]


def maturity_short_label(operation_id: str) -> str:
    return MATURITY_SHORT_LABELS[maturity_name(operation_id)]


def is_visible(operation_id: str, minimum_level: int) -> bool:
    try:
        threshold = int(minimum_level)
    except (TypeError, ValueError):
        threshold = 2
    threshold = max(0, min(2, threshold))
    return maturity_level(operation_id) >= threshold


def visibility_label(value: int | str) -> str:
    try:
        level = int(value)
    except (TypeError, ValueError):
        level = 2
    return VISIBILITY_LABELS.get(level, VISIBILITY_LABELS[2])


def visibility_value(label: str) -> int:
    return VISIBILITY_VALUES.get(str(label), 2)
