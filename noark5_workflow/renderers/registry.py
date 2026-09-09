from __future__ import annotations

from typing import Callable

from noark5_workflow.sinks.premis import PremisEventSink
from noark5_workflow.sinks.text_run_log import TextRunLogSink
from noark5_workflow.sinks.json_log import JsonEventLogSink
from noark5_workflow.sinks.csv_log import CsvEventLogSink


class UnknownLogImplementationError(ValueError):
    pass


_RENDERERS: dict[str, Callable] = {
    "premis_xml_v1": PremisEventSink,
    "text_run_log_v1": TextRunLogSink,
    "json_full_v1": JsonEventLogSink,
    "csv_standard_v1": CsvEventLogSink,
}


def registered_implementations() -> tuple[str, ...]:
    return tuple(sorted(_RENDERERS))


def resolve_renderer(implementation: str):
    try:
        return _RENDERERS[implementation]
    except KeyError as exc:
        raise UnknownLogImplementationError(
            f"Ukjent loggimplementasjon: {implementation!r}. "
            f"Registrerte implementasjoner: {', '.join(registered_implementations())}"
        ) from exc


def register_renderer(implementation: str, factory) -> None:
    implementation = str(implementation or "").strip()
    if not implementation:
        raise ValueError("implementation kan ikke være tom")
    _RENDERERS[implementation] = factory
