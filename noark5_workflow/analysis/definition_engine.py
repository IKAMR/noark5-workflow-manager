from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lxml import etree


class AnalysisDefinitionError(ValueError):
    pass


def load_analysis_definition(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        definition = json.load(handle)
    if not isinstance(definition, dict):
        raise AnalysisDefinitionError("Analysedefinisjonen må være et JSON-objekt.")
    if not definition.get("definition_id"):
        raise AnalysisDefinitionError("Analysedefinisjonen mangler definition_id.")
    if not isinstance(definition.get("entities"), list):
        raise AnalysisDefinitionError("Analysedefinisjonen mangler entities-liste.")
    return definition


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
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _evaluate(node: etree._Element, expression: str) -> Any:
    return _scalar(node.xpath(expression))


def _coerce_metric(value: Any, metric_type: str | None) -> Any:
    if metric_type == "integer":
        if value in (None, ""):
            return 0
        return int(float(value))
    if metric_type == "float":
        if value in (None, ""):
            return 0.0
        return float(value)
    return value


def _extract_fields(node: etree._Element, fields: dict[str, str]) -> dict[str, Any]:
    return {field_id: _evaluate(node, expression) for field_id, expression in fields.items()}


def run_definition_analysis(
    xml_path: str | Path,
    definition_path: str | Path,
) -> dict[str, Any]:
    """Run an externally defined XPath analysis and return a canonical model.

    The engine knows how to execute selectors/fields/metrics, but it contains no
    Noark-specific XPath expressions. Those belong in the external definition.
    """
    xml_path = Path(xml_path)
    definition_path = Path(definition_path)
    definition = load_analysis_definition(definition_path)

    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        remove_blank_text=False,
        huge_tree=True,
    )
    tree = etree.parse(str(xml_path), parser)

    entities_result: dict[str, list[dict[str, Any]]] = {}
    entity_counts: dict[str, int] = {}

    for entity in definition["entities"]:
        entity_id = str(entity["id"])
        selector = str(entity["select"])
        nodes = tree.xpath(selector)
        items: list[dict[str, Any]] = []

        for index, node in enumerate(nodes, start=1):
            if not isinstance(node, etree._Element):
                raise AnalysisDefinitionError(
                    f"Entity selector for {entity_id!r} må returnere XML-elementer."
                )

            item: dict[str, Any] = {
                "index": index,
                "fields": _extract_fields(node, entity.get("fields", {})),
                "metrics": {},
                "children": {},
            }

            for metric in entity.get("metrics", []):
                metric_id = str(metric["id"])
                raw = _evaluate(node, str(metric["expression"]))
                item["metrics"][metric_id] = _coerce_metric(raw, metric.get("type"))

            for child in entity.get("children", []):
                child_id = str(child["id"])
                child_nodes = node.xpath(str(child["select"]))
                child_items = []
                for child_index, child_node in enumerate(child_nodes, start=1):
                    if not isinstance(child_node, etree._Element):
                        continue
                    child_items.append(
                        {
                            "index": child_index,
                            "fields": _extract_fields(
                                child_node, child.get("fields", {})
                            ),
                        }
                    )
                item["children"][child_id] = child_items

            items.append(item)

        entities_result[entity_id] = items
        entity_counts[entity_id] = len(items)

    return {
        "model_format_version": 1,
        "definition_id": definition["definition_id"],
        "definition_path": str(definition_path.resolve()),
        "source": str(xml_path.resolve()),
        "basis": definition.get("basis", {}),
        "summary": {
            "entity_counts": entity_counts,
        },
        "entities": entities_result,
    }


def write_analysis_result(result: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
