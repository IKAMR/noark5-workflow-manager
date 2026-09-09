from __future__ import annotations

from pathlib import Path

from app.workspace import run_log_dir
from noark5_workflow.core.events import EventDispatcher
from noark5_workflow.core.log_format_definition import load_log_format_definition
from noark5_workflow.sinks.event_store import GenericEventStoreSink
from noark5_workflow.renderers.registry import resolve_renderer


TEXT_RUN_LOG_SINK = "text_run_log"
PREMIS_SINK = "premis"
JSON_SINK = "json"
CSV_SINK = "csv"
DEFAULT_TEXT_DEFINITION = "text_run_default_v1"
DEFAULT_PREMIS_DEFINITION = "premis_default_v1"
DEFAULT_JSON_DEFINITION = "json_full_v1"
DEFAULT_CSV_DEFINITION = "csv_standard_v1"
KNOWN_SINKS = (TEXT_RUN_LOG_SINK, PREMIS_SINK, JSON_SINK, CSV_SINK)


def configured_sink_ids(settings: dict) -> tuple[str, ...]:
    """Return enabled output-format sinks.

    The generic event store is intentionally not listed here: it is mandatory
    runtime data, not an optional output format.
    """
    raw = settings.get("enabled_log_sinks")
    if isinstance(raw, (list, tuple)):
        selected = [str(value) for value in raw if str(value) in KNOWN_SINKS]
    else:
        selected = [TEXT_RUN_LOG_SINK]
        if bool(settings.get("enable_premis_provenance", True)):
            selected.append(PREMIS_SINK)

    if bool(settings.get("enable_premis_provenance", True)):
        if PREMIS_SINK not in selected:
            selected.append(PREMIS_SINK)
    else:
        selected = [value for value in selected if value != PREMIS_SINK]

    return tuple(dict.fromkeys(selected))


def _event_store_path(settings: dict, *, run_id: str) -> Path:
    explicit = str(settings.get("_current_event_store_path", "") or "").strip()
    if explicit:
        return Path(explicit)
    safe_run = run_id or "runtime"
    return run_log_dir(settings) / f"{safe_run}.events.jsonl"


def build_event_dispatcher(
    settings: dict,
    *,
    scope: str,
    run_type: str = "",
    app_version: str = "",
    job_list_path=None,
    planned_jobs: int | None = None,
    run_id: str = "",
) -> EventDispatcher:
    """Build the canonical event store plus selected output projections."""
    selected = set(configured_sink_ids(settings))
    effective_run_id = run_id or str(settings.get("_current_run_id", "") or "")

    sinks = [
        GenericEventStoreSink(_event_store_path(settings, run_id=effective_run_id))
    ]

    if scope == "run" and TEXT_RUN_LOG_SINK in selected:
        definition_id = str(settings.get("text_log_definition", DEFAULT_TEXT_DEFINITION) or DEFAULT_TEXT_DEFINITION)
        definition = load_log_format_definition(definition_id)
        renderer = resolve_renderer(definition.implementation)
        sinks.append(
            renderer(
                settings,
                run_type=run_type,
                app_version=app_version,
                job_list_path=job_list_path,
                planned_jobs=planned_jobs,
                definition=definition,
            )
        )

    if JSON_SINK in selected:
        definition_id = str(settings.get("json_log_definition", DEFAULT_JSON_DEFINITION) or DEFAULT_JSON_DEFINITION)
        definition = load_log_format_definition(definition_id)
        renderer = resolve_renderer(definition.implementation)
        sinks.append(renderer(settings, definition=definition, run_id=effective_run_id))

    if CSV_SINK in selected:
        definition_id = str(settings.get("csv_log_definition", DEFAULT_CSV_DEFINITION) or DEFAULT_CSV_DEFINITION)
        definition = load_log_format_definition(definition_id)
        renderer = resolve_renderer(definition.implementation)
        sinks.append(renderer(settings, definition=definition, run_id=effective_run_id))

    if scope == "operation" and PREMIS_SINK in selected:
        definition_id = str(settings.get("premis_log_definition", DEFAULT_PREMIS_DEFINITION) or DEFAULT_PREMIS_DEFINITION)
        definition = load_log_format_definition(definition_id)
        renderer = resolve_renderer(definition.implementation)
        sinks.append(renderer(settings, definition=definition))

    return EventDispatcher(sinks)


def find_sink(dispatcher: EventDispatcher, sink_id: str):
    for sink in dispatcher.sinks:
        if getattr(sink, "sink_id", "") == sink_id:
            return sink
    return None


def event_dispatcher_for(ctx) -> EventDispatcher:
    dispatcher = ctx.metadata.get("event_dispatcher")
    if isinstance(dispatcher, EventDispatcher):
        return dispatcher
    dispatcher = build_event_dispatcher(
        ctx.settings,
        scope="operation",
        run_id=str(ctx.settings.get("_current_run_id", "") or ""),
    )
    ctx.metadata["event_dispatcher"] = dispatcher
    return dispatcher
