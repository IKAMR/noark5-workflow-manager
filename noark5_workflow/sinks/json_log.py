from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.workspace import run_log_dir
from noark5_workflow.core.events import WorkflowEvent
from noark5_workflow.sinks.event_store import event_record


class JsonEventLogSink:
    """JSON formatter over the canonical generic event model.

    This is an output format, not the authoritative event store. It intentionally
    reuses the same neutral event_record structure and writes a separate JSONL
    projection controlled by its log-format definition.
    """

    sink_id = "json"
    required = False

    def __init__(self, settings: dict, *, definition=None, run_id: str = "", **kwargs) -> None:
        self.settings = dict(settings)
        self.definition = definition
        effective_run_id = run_id or str(settings.get("_current_run_id", "") or "").strip() or "runtime"
        self.path = run_log_dir(settings) / f"{effective_run_id}.jsonl"

    def handle(self, event: WorkflowEvent, **runtime: Any) -> None:
        if self.definition is not None and not self.definition.accepts(event.kind):
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = event_record(event)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, indent=None))
            handle.write("\n")

    def close(self, **runtime: Any) -> None:
        return None
