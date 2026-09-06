from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lxml import etree


DEFAULT_DEFINITION = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "noark5"
    / "arkivstruktur_fields.json"
)


def load_definition(path: str | Path = DEFAULT_DEFINITION) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _scalar(value: Any) -> Any:
    if isinstance(value, list):
        if not value:
            return None
        if len(value) == 1:
            return _scalar(value[0])
        return [_scalar(item) for item in value]
    if isinstance(value, etree._Element):
        return "".join(value.itertext()).strip()
    if isinstance(value, etree._ElementUnicodeResult):
        return str(value).strip()
    if isinstance(value, str):
        return value.strip()
    return value


def _extract_fields(node: etree._Element, fields: dict[str, str]) -> dict[str, Any]:
    return {field_id: _scalar(node.xpath(xpath)) for field_id, xpath in fields.items()}


def extract_defined_fields(
    xml_path: str | Path,
    definition_path: str | Path = DEFAULT_DEFINITION,
) -> dict[str, Any]:
    xml_path = Path(xml_path)
    definition = load_definition(definition_path)

    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        remove_blank_text=False,
        huge_tree=True,
    )
    tree = etree.parse(str(xml_path), parser)

    result: dict[str, Any] = {
        "definition_id": definition["definition_id"],
        "source": str(xml_path.resolve()),
    }

    for entity_id, entity in definition["entities"].items():
        nodes = tree.xpath(entity["select"])
        extracted = []

        for index, node in enumerate(nodes, start=1):
            item = _extract_fields(node, entity.get("fields", {}))
            item["index"] = index

            for child_id, child in entity.get("children", {}).items():
                child_nodes = node.xpath(child["select"])
                item[child_id] = [
                    {
                        **_extract_fields(child_node, child.get("fields", {})),
                        "index": child_index,
                    }
                    for child_index, child_node in enumerate(child_nodes, start=1)
                ]
            extracted.append(item)

        if entity.get("scope") == "single":
            result[entity_id] = extracted[0] if extracted else None
            result[f"{entity_id}_count"] = len(extracted)
        else:
            result[entity_id] = extracted
            result[f"{entity_id}_count"] = len(extracted)

    return result
