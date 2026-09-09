from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from app.workspace import run_log_dir
from noark5_workflow.core.events import WorkflowEvent
from noark5_workflow.sinks.event_store import event_record


def _resolve_path(record: dict[str, Any], dotted: str):
    value: Any = record
    for part in dotted.split("."):
        if not isinstance(value, dict):
            return ""
        value = value.get(part, "")
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return str(value)
    return value


class CsvEventLogSink:
    """Flat CSV projection over canonical generic events."""

    sink_id = "csv"
    required = False

    def __init__(self, settings: dict, *, definition=None, run_id: str = "", **kwargs) -> None:
        self.settings = dict(settings)
        self.definition = definition
        effective_run_id = run_id or str(settings.get("_current_run_id", "") or "").strip() or "runtime"
        self.path = run_log_dir(settings) / f"{effective_run_id}.csv"

        field_map = dict(getattr(definition, "field_map", {}) or {})
        self.source_fields = list(field_map.keys())
        self.columns = [field_map[key] for key in self.source_fields]

        options = dict(getattr(definition, "options", {}) or {})
        self.delimiter = str(options.get("delimiter", ";") or ";")
        self.encoding = str(options.get("encoding", "utf-8-sig") or "utf-8-sig")
        self.include_header = bool(options.get("include_header", True))

    def handle(self, event: WorkflowEvent, **runtime: Any) -> None:
        if self.definition is not None and not self.definition.accepts(event.kind):
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        existed = self.path.is_file() and self.path.stat().st_size > 0
        record = event_record(event)
        row = {
            column: _resolve_path(record, source)
            for source, column in zip(self.source_fields, self.columns)
        }

        with self.path.open("a", encoding=self.encoding, newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.columns, delimiter=self.delimiter)
            if self.include_header and not existed:
                writer.writeheader()
            writer.writerow(row)

    def close(self, **runtime: Any) -> None:
        return None
