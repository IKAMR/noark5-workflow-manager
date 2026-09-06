from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


KEY_ELEMENTS = (
    "arkiv",
    "arkivdel",
    "klassifikasjonssystem",
    "klasse",
    "mappe",
    "registrering",
    "dokumentbeskrivelse",
    "dokumentobjekt",
)


def _local_name(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _namespace(tag: str) -> str | None:
    if tag.startswith("{") and "}" in tag:
        return tag[1:].split("}", 1)[0]
    return None


@dataclass(frozen=True)
class ArkivstrukturAnalysis:
    path: Path
    bytes: int
    root_element: str
    namespace: str | None
    total_elements: int
    element_counts: dict[str, int]
    key_counts: dict[str, int]

    def as_dict(self) -> dict:
        return {
            "path": str(self.path),
            "bytes": self.bytes,
            "root_element": self.root_element,
            "namespace": self.namespace,
            "total_elements": self.total_elements,
            "element_counts": dict(self.element_counts),
            "key_counts": dict(self.key_counts),
        }


def analyse_arkivstruktur(path: str | Path) -> ArkivstrukturAnalysis:
    """Stream arkivstruktur.xml and return reusable structural counts.

    This deliberately performs structural analysis only. No U1/U2 compliance
    conclusion is inferred from the counts in this layer.
    """
    path = Path(path)
    counts: Counter[str] = Counter()
    root_tag: str | None = None
    total = 0

    for event, elem in ET.iterparse(path, events=("start", "end")):
        if event == "start":
            if root_tag is None:
                root_tag = elem.tag
            continue

        local = _local_name(elem.tag)
        counts[local] += 1
        total += 1
        elem.clear()

    if root_tag is None:
        raise ValueError("arkivstruktur.xml inneholder ikke et rotelement.")

    key_counts = {name: counts.get(name, 0) for name in KEY_ELEMENTS}
    return ArkivstrukturAnalysis(
        path=path.resolve(),
        bytes=path.stat().st_size,
        root_element=_local_name(root_tag),
        namespace=_namespace(root_tag),
        total_elements=total,
        element_counts=dict(sorted(counts.items())),
        key_counts=key_counts,
    )
