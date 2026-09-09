from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import uuid4

from .identity import UserIdentity


@dataclass(frozen=True)
class WorkflowEvent:
    """Format-neutral runtime event and canonical event-store input."""

    kind: str
    timestamp: str
    event_id: str = ""
    success: bool = True
    message: str = ""
    operation_id: str = ""
    operation_name: str = ""
    job_id: str = ""
    run_id: str = ""
    parent_event_id: str = ""
    user: UserIdentity | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def now(cls, kind: str, **kwargs) -> "WorkflowEvent":
        return cls(
            kind=kind,
            timestamp=datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            event_id=uuid4().hex,
            **kwargs,
        )


class EventSink(Protocol):
    sink_id: str

    def handle(self, event: WorkflowEvent, **runtime: Any) -> None:
        ...

    def close(self, **runtime: Any) -> None:
        ...


class EventDispatcher:
    """Dispatch one neutral event to required and optional sinks.

    A required sink is part of the authoritative runtime contract and may fail
    the caller. Optional output-format sinks are isolated from one another.
    """

    def __init__(self, sinks=()) -> None:
        self._sinks = list(sinks)

    @property
    def sinks(self) -> tuple:
        return tuple(self._sinks)

    def add_sink(self, sink) -> None:
        self._sinks.append(sink)

    def emit(self, event: WorkflowEvent, **runtime: Any) -> None:
        for sink in tuple(self._sinks):
            try:
                sink.handle(event, **runtime)
            except Exception:
                if bool(getattr(sink, "required", False)):
                    raise
                continue

    def close(self, **runtime: Any) -> None:
        for sink in tuple(self._sinks):
            try:
                sink.close(**runtime)
            except Exception:
                if bool(getattr(sink, "required", False)):
                    raise
                continue
