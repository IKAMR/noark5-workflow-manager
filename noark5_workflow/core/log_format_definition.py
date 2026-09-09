from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FORMAT_DEFINITION_VERSION = 1


class LogFormatDefinitionError(ValueError):
    pass


@dataclass(frozen=True)
class LogFormatDefinition:
    definition_id: str
    definition_version: int
    format: str
    implementation: str
    event_kinds: tuple[str, ...]
    field_map: dict[str, str]
    options: dict[str, Any]
    path: Path

    def accepts(self, event_kind: str) -> bool:
        return "*" in self.event_kinds or event_kind in self.event_kinds


def _default_root() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "logging"


def _definition_path(definition_id: str, root: Path | None = None) -> Path:
    base = Path(root) if root is not None else _default_root()
    return base / f"{definition_id}.json"


def load_log_format_definition(
    definition_id: str,
    *,
    root: Path | None = None,
) -> LogFormatDefinition:
    path = _definition_path(definition_id, root)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise LogFormatDefinitionError(
            f"Kunne ikke lese loggdefinisjon {definition_id!r}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise LogFormatDefinitionError(
            f"Ugyldig JSON i loggdefinisjon {definition_id!r}: {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise LogFormatDefinitionError("Loggdefinisjonen må være et JSON-objekt")

    version = raw.get("definition_version")
    if version != FORMAT_DEFINITION_VERSION:
        raise LogFormatDefinitionError(
            f"Ustøttet definition_version {version!r} i {definition_id!r}"
        )

    stored_id = str(raw.get("definition_id", "") or "").strip()
    if stored_id != definition_id:
        raise LogFormatDefinitionError(
            f"definition_id {stored_id!r} samsvarer ikke med filreferansen {definition_id!r}"
        )

    format_name = str(raw.get("format", "") or "").strip()
    implementation = str(raw.get("implementation", "") or "").strip()
    if not format_name:
        raise LogFormatDefinitionError("Loggdefinisjonen mangler format")
    if not implementation:
        raise LogFormatDefinitionError("Loggdefinisjonen mangler implementation")

    event_kinds = raw.get("event_kinds", [])
    if not isinstance(event_kinds, list) or not all(isinstance(v, str) for v in event_kinds):
        raise LogFormatDefinitionError("event_kinds må være en liste med tekstverdier")

    field_map = raw.get("field_map", {})
    if not isinstance(field_map, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in field_map.items()
    ):
        raise LogFormatDefinitionError("field_map må være et tekst-til-tekst objekt")

    options = raw.get("options", {})
    if not isinstance(options, dict):
        raise LogFormatDefinitionError("options må være et objekt")

    return LogFormatDefinition(
        definition_id=stored_id,
        definition_version=int(version),
        format=format_name,
        implementation=implementation,
        event_kinds=tuple(event_kinds),
        field_map=dict(field_map),
        options=dict(options),
        path=path,
    )
