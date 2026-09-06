from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from lxml import etree


@dataclass(frozen=True)
class XmlSchemaValidationResult:
    valid: bool
    xml_path: Path
    schema_path: Path | None
    errors: list[dict]

    def as_dict(self) -> dict:
        return {
            "valid": self.valid,
            "xml": str(self.xml_path),
            "schema": str(self.schema_path) if self.schema_path else None,
            "errors": self.errors,
        }


def _error_rows(log) -> list[dict]:
    return [
        {
            "line": entry.line,
            "column": entry.column,
            "level": entry.level_name,
            "domain": entry.domain_name,
            "type": entry.type_name,
            "message": entry.message,
        }
        for entry in log
    ]


def schema_location_candidates(xml_path: Path) -> list[str]:
    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()
    xsi = "http://www.w3.org/2001/XMLSchema-instance"

    values = []
    schema_location = root.get(f"{{{xsi}}}schemaLocation", "")
    tokens = schema_location.split()
    values.extend(tokens[1::2])

    no_namespace = root.get(f"{{{xsi}}}noNamespaceSchemaLocation", "")
    if no_namespace:
        values.append(no_namespace)

    return values


def resolve_local_schema(
    xml_path: str | Path,
    available_xsds: list[Path],
    preferred_names: list[str] | None = None,
) -> Path | None:
    xml_path = Path(xml_path)
    available = [Path(p).resolve() for p in available_xsds]
    by_name = {p.name.lower(): p for p in available}

    for name in preferred_names or []:
        found = by_name.get(name.lower())
        if found:
            return found

    for location in schema_location_candidates(xml_path):
        candidate_name = Path(urlparse(location).path).name.lower()
        if candidate_name and candidate_name in by_name:
            return by_name[candidate_name]

        local_candidate = (xml_path.parent / location).resolve()
        if local_candidate.is_file() and local_candidate.suffix.lower() == ".xsd":
            return local_candidate

    same_stem = by_name.get(f"{xml_path.stem}.xsd".lower())
    if same_stem:
        return same_stem

    return available[0] if len(available) == 1 else None


def validate_xml_against_xsd(
    xml_path: str | Path,
    schema_path: str | Path,
) -> XmlSchemaValidationResult:
    xml_path = Path(xml_path).resolve()
    schema_path = Path(schema_path).resolve()

    secure_parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        huge_tree=True,
    )

    try:
        schema_doc = etree.parse(str(schema_path), secure_parser)
        schema = etree.XMLSchema(schema_doc)
    except (etree.XMLSyntaxError, etree.XMLSchemaParseError, OSError) as exc:
        return XmlSchemaValidationResult(
            False,
            xml_path,
            schema_path,
            [{"line": getattr(exc, "lineno", None), "column": None,
              "level": "ERROR", "domain": "SCHEMA", "type": exc.__class__.__name__,
              "message": str(exc)}],
        )

    try:
        xml_doc = etree.parse(str(xml_path), secure_parser)
    except (etree.XMLSyntaxError, OSError) as exc:
        return XmlSchemaValidationResult(
            False,
            xml_path,
            schema_path,
            [{"line": getattr(exc, "lineno", None), "column": None,
              "level": "ERROR", "domain": "XML", "type": exc.__class__.__name__,
              "message": str(exc)}],
        )

    valid = schema.validate(xml_doc)
    return XmlSchemaValidationResult(
        valid,
        xml_path,
        schema_path,
        _error_rows(schema.error_log),
    )


def write_validation_report(
    result: XmlSchemaValidationResult,
    output_path: str | Path,
    *,
    validation_id: str,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "validation_id": validation_id,
        **result.as_dict(),
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
