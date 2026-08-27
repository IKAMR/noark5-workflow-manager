from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

METS_NS = "http://www.loc.gov/METS/"


def _tag(local: str) -> str:
    return f"{{{METS_NS}}}{local}"


def _name(agent: ET.Element) -> str:
    node = agent.find(_tag("name"))
    return (node.text or "").strip() if node is not None else ""


def read_meta_from_mets(mets_path: str | Path) -> dict[str, str]:
    """Les DIAS-relevante metadata fra en eksisterende METS-fil.

    Filnavnet er uten betydning; både info.xml, mets.xml og andre METS XML-filer
    kan leses. Bare felt som faktisk kan utledes fra METS-semantikken returneres.
    """
    try:
        root = ET.parse(str(mets_path)).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Ugyldig XML: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Kunne ikke lese filen: {exc}") from exc

    if root.tag != _tag("mets"):
        raise ValueError("Filen er ikke en METS-fil (forventet mets:mets som rotelement).")

    result: dict[str, str] = {}
    label = root.get("LABEL", "").strip()
    if label:
        result["label"] = label

    hdr = root.find(_tag("metsHdr"))
    if hdr is None:
        return result

    for alt in hdr.findall(_tag("altRecordID")):
        value = (alt.text or "").strip()
        kind = (alt.get("TYPE") or "").upper()
        if not value:
            continue
        if kind == "SUBMISSIONAGREEMENT":
            result["submission_agreement"] = value
        elif kind == "STARTDATE":
            result["period_start"] = value
        elif kind == "ENDDATE":
            result["period_end"] = value

    archivist_software: list[str] = []
    for agent in hdr.findall(_tag("agent")):
        typ = (agent.get("TYPE") or "").upper()
        role = (agent.get("ROLE") or "").upper()
        otherrole = (agent.get("OTHERROLE") or "").upper()
        othertype = (agent.get("OTHERTYPE") or "").upper()
        name = _name(agent)
        if not name:
            continue

        if typ == "ORGANIZATION" and role == "ARCHIVIST":
            result["archivist_org"] = name
        elif typ == "OTHER" and othertype == "SOFTWARE" and role == "ARCHIVIST":
            archivist_software.append(name)
        elif typ == "ORGANIZATION" and role == "CREATOR":
            result["creator"] = name
        elif role == "OTHER" and otherrole == "PRODUCER":
            if typ == "ORGANIZATION":
                result["producer_org"] = name
            elif typ == "INDIVIDUAL":
                result["producer_person"] = name
            elif typ == "OTHER" and othertype == "SOFTWARE":
                result["producer_software"] = name
        elif role == "OTHER" and otherrole == "SUBMITTER":
            if typ == "ORGANIZATION":
                result["submitter_org"] = name
            elif typ == "INDIVIDUAL":
                result["submitter_person"] = name
        elif typ == "ORGANIZATION" and role == "IPOWNER":
            result["owner_org"] = name
        elif typ == "ORGANIZATION" and role == "PRESERVATION":
            result["preserver"] = name

    for key, value in zip(("system", "system_version", "archivist_type"), archivist_software):
        result[key] = value

    return result
