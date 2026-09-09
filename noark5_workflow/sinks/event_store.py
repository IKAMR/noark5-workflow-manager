from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping

from noark5_workflow.core.events import WorkflowEvent


EVENT_STORE_SCHEMA_VERSION = 1


def _json_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return _json_value(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_value(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def event_record(event: WorkflowEvent) -> dict[str, Any]:
    user = event.user.as_dict() if event.user is not None else None
    return {
        "schema_version": EVENT_STORE_SCHEMA_VERSION,
        "event_id": event.event_id,
        "timestamp": event.timestamp,
        "kind": event.kind,
        "run_id": event.run_id,
        "job_id": event.job_id,
        "operation_id": event.operation_id,
        "operation_name": event.operation_name,
        "parent_event_id": event.parent_event_id,
        "success": bool(event.success),
        "message": event.message,
        "user": user,
        "data": _json_value(event.data),
    }


class GenericEventStoreSink:
    """Mandatory append-only source of truth for one runtime event stream.

    JSONL is an internal persistence encoding, not the public JSON log format.
    PREMIS/CSV/JSON/text outputs are projections over these records.
    """

    sink_id = "event_store"
    required = True

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def handle(self, event: WorkflowEvent, **runtime: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = event_record(event)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")

    def close(self, **runtime: Any) -> None:
        return None


def read_event_store(path: Path | str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    path = Path(path)
    if not path.is_file():
        return result
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            value = json.loads(text)
            if not isinstance(value, dict):
                raise ValueError(f"Ugyldig event record på linje {line_number}")
            if value.get("schema_version") != EVENT_STORE_SCHEMA_VERSION:
                raise ValueError(
                    f"Ukjent event-store schema_version på linje {line_number}: "
                    f"{value.get('schema_version')!r}"
                )
            result.append(value)
    return result
