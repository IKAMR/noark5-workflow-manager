from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from pathlib import Path
from statistics import mean
from typing import Any

from lxml import etree


XSI = "http://www.w3.org/2001/XMLSchema-instance"


def _local(element: etree._Element) -> str:
    return etree.QName(element).localname


def _children(node: etree._Element, name: str) -> list[etree._Element]:
    return [child for child in node if isinstance(child.tag, str) and _local(child) == name]


def _first_text(node: etree._Element, name: str) -> str:
    items = _children(node, name)
    if not items:
        return ""
    return "".join(items[0].itertext()).strip()


def _all(root: etree._Element, name: str) -> list[etree._Element]:
    return [e for e in root.iter() if isinstance(e.tag, str) and _local(e) == name]


def _desc(node: etree._Element, name: str) -> list[etree._Element]:
    return [e for e in node.iterdescendants() if isinstance(e.tag, str) and _local(e) == name]


def _type_value(node: etree._Element) -> str:
    return (node.get(f"{{{XSI}}}type") or node.get("type") or "").strip()


def _safe_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return None


def _date_range(nodes: list[etree._Element], child_name: str) -> dict[str, str | None]:
    values = [_safe_date(_first_text(node, child_name)) for node in nodes]
    dates = sorted(value for value in values if value is not None)
    return {
        "first": dates[0].isoformat() if dates else None,
        "last": dates[-1].isoformat() if dates else None,
    }


def _value_counts(nodes: list[etree._Element], child_name: str) -> dict[str, int]:
    values = Counter(_first_text(node, child_name) for node in nodes)
    values.pop("", None)
    return dict(sorted(values.items(), key=lambda item: item[0].casefold()))


def _element_text_counts(elements: list[etree._Element]) -> dict[str, int]:
    values = Counter("".join(element.itertext()).strip() for element in elements)
    values.pop("", None)
    return dict(sorted(values.items(), key=lambda item: item[0].casefold()))


def _type_counts(nodes: list[etree._Element]) -> dict[str, int]:
    values = Counter(_type_value(node) for node in nodes)
    values.pop("", None)
    return dict(sorted(values.items(), key=lambda item: item[0].casefold()))


def _year_counts(nodes: list[etree._Element], child_name: str) -> dict[str, int]:
    values = Counter()
    for node in nodes:
        text = _first_text(node, child_name)
        if len(text) >= 4:
            values[text[:4]] += 1
    return dict(sorted(values.items()))


def _direct_parent_counts(elements: list[etree._Element]) -> dict[str, int]:
    values = Counter()
    for element in elements:
        parent = element.getparent()
        if parent is not None and isinstance(parent.tag, str):
            values[_local(parent)] += 1
    return dict(sorted(values.items(), key=lambda item: item[0].casefold()))


def _has_child(node: etree._Element, name: str) -> bool:
    return bool(_children(node, name))


def _child_equals(node: etree._Element, name: str, value: str) -> bool:
    return _first_text(node, name) == value


def _numeric_text(elements: list[etree._Element]) -> list[int]:
    result = []
    for element in elements:
        text = "".join(element.itertext()).strip()
        try:
            result.append(int(float(text)))
        except (TypeError, ValueError):
            continue
    return result


def _size_buckets(values: list[int]) -> dict[str, int]:
    labels = {
        "0": 0, "1-9": 0, "10-99": 0, "100-199": 0, "200-499": 0,
        "500-999": 0, "1000-1999": 0, "2000-9999": 0, "10k-100k": 0,
        "100k-1M": 0, "1M-10M": 0, "10M-100M": 0, ">=100M": 0,
    }
    for value in values:
        if value == 0: labels["0"] += 1
        elif value < 10: labels["1-9"] += 1
        elif value < 100: labels["10-99"] += 1
        elif value < 200: labels["100-199"] += 1
        elif value < 500: labels["200-499"] += 1
        elif value < 1000: labels["500-999"] += 1
        elif value < 2000: labels["1000-1999"] += 1
        elif value < 10000: labels["2000-9999"] += 1
        elif value < 100000: labels["10k-100k"] += 1
        elif value < 1000000: labels["100k-1M"] += 1
        elif value < 10000000: labels["1M-10M"] += 1
        elif value < 100000000: labels["10M-100M"] += 1
        else: labels[">=100M"] += 1
    return labels


def _archive_part_brief(archive_parts: list[etree._Element]) -> list[dict[str, Any]]:
    rows = []
    for index, part in enumerate(archive_parts, 1):
        docs = _desc(part, "dokumentbeskrivelse")
        rows.append({
            "index": index,
            "title": _first_text(part, "tittel"),
            "document_medium": _first_text(part, "dokumentmedium"),
            "created_date": _first_text(part, "opprettetDato")[:10],
            "closed_date": _first_text(part, "avsluttetDato")[:10],
            "status": _first_text(part, "arkivdelstatus"),
            "mappe_count": len(_desc(part, "mappe")),
            "registrering_count": len(_desc(part, "registrering")),
            "dokumentbeskrivelse_count": len(docs),
            "document_medium_counts": _value_counts(docs, "dokumentmedium"),
        })
    return rows


def run_u1_total(xml_path: str | Path) -> dict[str, Any]:
    """Execute the 2022-09-21 U1 semantics against arkivstruktur.xml.

    The uploaded U1 file is the semantic source. This implementation uses lxml
    and namespace-neutral element names so the same analysis can run against
    Noark 5 3.1/4.0/5.0 namespace variants.
    """
    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()

    archives = _all(root, "arkiv")
    creators = _all(root, "arkivskaper")
    archive_parts = _all(root, "arkivdel")
    classification_systems = _all(root, "klassifikasjonssystem")
    classes = _all(root, "klasse")
    folders = _all(root, "mappe")
    registrations = _all(root, "registrering")
    doc_desc = _all(root, "dokumentbeskrivelse")
    doc_obj = _all(root, "dokumentobjekt")

    journalposts = [r for r in registrations if _type_value(r) == "journalpost"]

    archive_rows = []
    for archive in archives:
        archive_rows.append({
            "title": _first_text(archive, "tittel"),
            "system_id": _first_text(archive, "systemID"),
            "description": _first_text(archive, "beskrivelse"),
            "status": _first_text(archive, "arkivstatus"),
            "document_medium": _first_text(archive, "dokumentmedium"),
            "created_date": _first_text(archive, "opprettetDato")[:10],
            "closed_date": _first_text(archive, "avsluttetDato")[:10],
            "created_by": _first_text(archive, "opprettetAv"),
            "closed_by": _first_text(archive, "avsluttetAv"),
        })

    creator_rows = [{
        "name": _first_text(c, "arkivskaperNavn"),
        "id": _first_text(c, "arkivskaperID"),
        "description": _first_text(c, "beskrivelse"),
    } for c in creators]

    folder_status = _value_counts(folders, "saksstatus")
    registration_types = _type_counts(registrations)
    journalpost_types = _value_counts(registrations, "journalposttype")
    journal_status = _value_counts(registrations, "journalstatus")

    document_numbers = _numeric_text(_all(root, "dokumentnummer"))
    versions = _numeric_text(_all(root, "versjonsnummer"))
    file_sizes = _numeric_text(_all(root, "filstoerrelse"))

    def count_direct(parent_name: str, child_name: str) -> int:
        return sum(len(_children(parent, child_name)) for parent in _all(root, parent_name))

    def count_text(name: str, value: str) -> int:
        return sum(
            1 for element in _all(root, name)
            if "".join(element.itertext()).strip() == value
        )

    def elements_under(parent_name: str, child_name: str) -> int:
        return sum(len(_desc(parent, child_name)) for parent in _all(root, parent_name))

    result = {
        "model_format_version": 1,
        "definition_id": "noark5.u1.total.v1",
        "source": str(Path(xml_path)),
        "scope": "whole_extraction",
        "archive": {
            "count": len(archives),
            "items": archive_rows,
            "creator_count": len(creators),
            "creators": creator_rows,
        },
        "dates": {
            "archive_created": _date_range(archives, "opprettetDato"),
            "archive_closed": _date_range(archives, "avsluttetDato"),
            "archive_part_created": _date_range(archive_parts, "opprettetDato"),
            "archive_part_closed": _date_range(archive_parts, "avsluttetDato"),
            "folder_created": _date_range(folders, "opprettetDato"),
            "folder_closed": _date_range(folders, "avsluttetDato"),
            "case_date": _date_range(folders, "saksdato"),
            "meeting_date": _date_range(folders, "moetedato"),
            "registration_archived": _date_range(registrations, "arkivertDato"),
            "journal_date": _date_range(journalposts, "journaldato"),
            "document_created": _date_range(doc_desc, "opprettetDato"),
        },
        "structure": {
            "archive_part_count": len(archive_parts),
            "archive_parts": _archive_part_brief(archive_parts),
            "classification_system_count": len(classification_systems),
            "class_count": len(classes),
            "class_with_subclass_and_folder": sum(
                len(_children(c, "mappe")) for c in classes if _has_child(c, "klasse")
            ),
            "class_with_subclass_and_registration": sum(
                len(_children(c, "registrering")) for c in classes if _has_child(c, "klasse")
            ),
        },
        "folders": {
            "count": len(folders),
            "type_counts": _type_counts(folders),
            "without_specialization_attribute_model": sum(1 for f in folders if len(f.attrib) == 3),
            "without_subfolder_or_registration": sum(
                1 for f in folders if not (_has_child(f, "mappe") or _has_child(f, "registrering"))
            ),
            "status_counts": folder_status,
            "case_status_fixed": {
                "Avsluttet": sum(_child_equals(f, "saksstatus", "Avsluttet") for f in folders),
                "Utgår": sum(_child_equals(f, "saksstatus", "Utgår") for f in folders),
                # Preserve source-U1 spelling/semantics: sakstatus, not saksstatus.
                "Under behandling (source sakstatus=Underbehandling)": sum(
                    _child_equals(f, "sakstatus", "Underbehandling") for f in folders
                ),
            },
            "closed_date_by_type": {
                "saksmappe": sum(
                    _type_value(f) == "saksmappe" and bool(_first_text(f, "avsluttetDato"))
                    for f in folders
                ),
                "moetemappe": sum(
                    _type_value(f) == "moetemappe" and bool(_first_text(f, "avsluttetDato"))
                    for f in folders
                ),
            },
            "created_per_year": _year_counts(folders, "opprettetDato"),
        },
        "registrations": {
            "count": len(registrations),
            "type_counts": registration_types,
            "without_specialization_attribute_model": sum(1 for r in registrations if len(r.attrib) == 3),
            "empty_journalstatus_elements": sum(
                not "".join(e.itertext()).strip() for e in _all(root, "journalstatus")
            ),
            "without_document_description": sum(not _has_child(r, "dokumentbeskrivelse") for r in registrations),
            "without_document_description_with_id": sum(
                (not _has_child(r, "dokumentbeskrivelse")) and bool(_first_text(r, "registreringsID"))
                for r in registrations
            ),
            "created_per_year": _year_counts(registrations, "opprettetDato"),
            "journalposts": {
                "count": len(journalposts),
                "type_counts": journalpost_types,
                "status_counts": journal_status,
                "journal_date_per_year": _year_counts(registrations, "journaldato"),
                "fixed_types": {
                    "Inngående dokument": sum(_child_equals(r, "journalposttype", "Inngående dokument") for r in registrations),
                    "Utgående dokument": sum(_child_equals(r, "journalposttype", "Utgående dokument") for r in registrations),
                    "Organinternt dokument for oppfølging": sum(_child_equals(r, "journalposttype", "Organinternt dokument for oppfølging") for r in registrations),
                    "Organinternt dokument uten oppfølging": sum(_child_equals(r, "journalposttype", "Organinternt dokument uten oppfølging") for r in registrations),
                    "Saksframlegg": sum(_child_equals(r, "journalposttype", "Saksframlegg") for r in registrations),
                },
                "fixed_status": {
                    "Arkivert": sum(_child_equals(r, "journalstatus", "Arkivert") for r in registrations),
                    "Utgår": sum(_child_equals(r, "journalstatus", "Utgår") for r in registrations),
                    "Journalført": sum(_child_equals(r, "journalstatus", "Journalført") for r in registrations),
                    "Ekspedert": sum(_child_equals(r, "journalstatus", "Ekspedert") for r in registrations),
                },
            },
        },
        "documents": {
            "description_count": len(doc_desc),
            "main_document_count": sum(
                _child_equals(d, "tilknyttetRegistreringSom", "Hoveddokument") for d in doc_desc
            ),
            "attachment_or_other_count": sum(
                not _child_equals(d, "tilknyttetRegistreringSom", "Hoveddokument") for d in doc_desc
            ),
            "relation_type_counts": _element_text_counts(_all(root, "tilknyttetRegistreringSom")),
            "document_number": {
                "count": len(document_numbers),
                "1": sum(v == 1 for v in document_numbers),
                "2": sum(v == 2 for v in document_numbers),
                "3": sum(v == 3 for v in document_numbers),
                ">=4": sum(v >= 4 for v in document_numbers),
                ">=100": sum(v >= 100 for v in document_numbers),
            },
            "version_number": {
                "count": len(versions),
                **{str(v): sum(x == v for x in versions) for v in range(1, 10)},
                ">=10": sum(v >= 10 for v in versions),
            },
            "without_object": sum(not _has_child(d, "dokumentobjekt") for d in doc_desc),
            "status": {
                "Ferdigstilt": sum(_child_equals(d, "dokumentstatus", "Dokumentet er ferdigstilt") for d in doc_desc),
                "Under redigering": sum(_child_equals(d, "dokumentstatus", "Dokumentet er under redigering") for d in doc_desc),
                "Annen status": sum(
                    _first_text(d, "dokumentstatus") not in {
                        "Dokumentet er ferdigstilt", "Dokumentet er under redigering"
                    } for d in doc_desc
                ),
                "generic": _value_counts(doc_desc, "dokumentstatus"),
            },
            "medium_counts": _value_counts(doc_desc, "dokumentmedium"),
            "object_count": len(doc_obj),
            "variant_format_counts": _value_counts(doc_obj, "variantformat"),
            "document_type_counts": _element_text_counts(_all(root, "dokumenttype")),
        },
        "relations": {
            "correspondence_party_count": len(_all(root, "korrespondansepart")),
            "correspondence_party_parent_counts": _direct_parent_counts(_all(root, "korrespondansepart")),
            "sakspart_count": len(_all(root, "sakspart")),
            "part_count": len(_all(root, "part")),
            "part_direct": {
                "mappe": count_direct("mappe", "part"),
                "registrering": count_direct("registrering", "part"),
                "dokumentbeskrivelse": count_direct("dokumentbeskrivelse", "part"),
            },
            "merknad": {
                "count": len(_all(root, "merknad")),
                "mappe": count_direct("mappe", "merknad"),
                "registrering": count_direct("registrering", "merknad"),
                "dokumentbeskrivelse": count_direct("dokumentbeskrivelse", "merknad"),
            },
            "cross_reference_children": {
                "count": sum(len(e) for e in _all(root, "kryssreferanse")),
                "klasse": sum(len(k) for parent in _all(root, "klasse") for k in _children(parent, "kryssreferanse")),
                "mappe": sum(len(k) for parent in _all(root, "mappe") for k in _children(parent, "kryssreferanse")),
                "registrering": sum(len(k) for parent in _all(root, "registrering") for k in _children(parent, "kryssreferanse")),
            },
            "precedent": {
                "count": len(_all(root, "presedens")),
                "mappe": count_direct("mappe", "presedens"),
                "journalpost": sum(len(_children(r, "presedens")) for r in journalposts),
            },
            "write_off": {
                "method_count": len(_all(root, "avskrivningsmaate")),
                "method_counts": _element_text_counts(_all(root, "avskrivningsmaate")),
                "journalpost_with_method": sum(
                    1 for r in journalposts for a in _children(r, "avskrivning")
                    if bool(_first_text(a, "avskrivningsmaate"))
                ),
                "reference_to_other_journalpost": sum(
                    1 for r in journalposts for a in _children(r, "avskrivning")
                    if bool(_first_text(a, "referanseAvskrivesAvJournalpost"))
                ),
            },
            "document_flow": {
                "count": elements_under("registrering", "dokumentflyt"),
                "journalpost": sum(bool(_children(r, "dokumentflyt")) for r in journalposts),
                "arkivnotat": sum(
                    len(_children(r, "dokumentflyt"))
                    for r in registrations if _type_value(r) == "arkivnotat"
                ),
            },
        },
        "preservation": {
            "screening": {
                "count": len(_all(root, "skjerming")),
                "arkivdel": count_direct("arkivdel", "skjerming"),
                "klasse": count_direct("klasse", "skjerming"),
                "mappe": count_direct("mappe", "skjerming"),
                "registrering": count_direct("registrering", "skjerming"),
                "dokumentbeskrivelse": count_direct("dokumentbeskrivelse", "skjerming"),
            },
            "grading_v31_v40": {
                "count": len(_all(root, "gradering")),
                "arkivdel": count_direct("arkivdel", "gradering"),
                "klasse": count_direct("klasse", "gradering"),
                "mappe": count_direct("mappe", "gradering"),
                "registrering": count_direct("registrering", "gradering"),
                "dokumentbeskrivelse": count_direct("dokumentbeskrivelse", "gradering"),
            },
            "grading_v50": {
                "count": len(_all(root, "grad")),
                "arkivdel": count_direct("arkivdel", "grad"),
                "klasse": count_direct("klasse", "grad"),
                "mappe": count_direct("mappe", "grad"),
                "registrering": count_direct("registrering", "grad"),
                "dokumentbeskrivelse": count_direct("dokumentbeskrivelse", "grad"),
            },
            "disposal_decision": {
                "count": len(_all(root, "kassasjon")),
                "arkivdel": count_direct("arkivdel", "kassasjon"),
                "klasse": count_direct("klasse", "kassasjon"),
                "mappe": count_direct("mappe", "kassasjon"),
                "registrering": count_direct("registrering", "kassasjon"),
                "dokumentbeskrivelse": count_direct("dokumentbeskrivelse", "kassasjon"),
            },
            "performed_disposal_document_description": count_direct("dokumentbeskrivelse", "utfoertKassasjon"),
            "deletion": {
                "count": len(_all(root, "sletting")),
                "type_counts": _element_text_counts(_all(root, "slettingstype")),
            },
            "business_specific_metadata": {
                "count": len(_all(root, "virksomhetsspesifikkeMetadata")),
                "mappe": count_direct("mappe", "virksomhetsspesifikkeMetadata"),
                "registrering": count_direct("registrering", "virksomhetsspesifikkeMetadata"),
                "dokumentbeskrivelse": count_direct("dokumentbeskrivelse", "virksomhetsspesifikkeMetadata"),
                "part": count_direct("part", "virksomhetsspesifikkeMetadata"),
            },
        },
        "files": {
            "size_count": len(file_sizes),
            "size_buckets": _size_buckets(file_sizes),
            "size_average": round(mean(file_sizes)) if file_sizes else 0,
            "size_max": max(file_sizes) if file_sizes else 0,
            "size_sum": sum(file_sizes),
            "format_counts": _element_text_counts(_all(root, "format")),
            "format_details_counts": _element_text_counts(_all(root, "formatDetaljer")),
        },
        "conversion": {
            "count": len(_all(root, "konvertering")),
            "object_conversion_count": count_direct("dokumentobjekt", "konvertering"),
            "from_format_counts": _element_text_counts(_all(root, "konvertertFraFormat")),
            "to_format_counts": _element_text_counts(_all(root, "konvertertTilFormat")),
            "tool_counts": _element_text_counts(_all(root, "konverteringsverktoey")),
        },
        "reserved_cross_file_u1_items": [
            "N5.52 loependeJournal",
            "N5.53 loependeJournal per år",
            "N5.55 skjermede journalposter i loependeJournal",
            "N5.56 offentligJournal",
            "N5.57 offentligJournal per år",
            "N5.61 endringslogg og per år",
        ],
    }
    return result
