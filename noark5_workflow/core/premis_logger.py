"""
PREMIS-proveniens for Noark 5 Workflow Manager.

Arkitekturen er bevisst basert på den generiske PremisProvenanceLogger i
SIARD Workflow Manager (smult/SIARD-Workflow-Manager), tilpasset Noark 5 som
objekt og Noark 5 Workflow Manager som programvareagent.

Loggeren akkumulerer PREMIS-hendelser gjennom en workflow-kontekst og skriver
én samlet <uttrekksnavn>_premis.xml. Vanlig teknisk kjørelogg er fortsatt
separat og skal inneholde alle operasjoner/tester.
"""
from __future__ import annotations

import datetime
import logging
from pathlib import Path
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

PREMIS_NS = "http://arkivverket.no/standarder/PREMIS"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
XLINK_NS = "http://www.w3.org/1999/xlink"

# DIAS_PREMIS v2.0 eventType-enumerasjon. Samme sett som SIARD Workflow Manager.
VALID_EVENT_TYPES = frozenset({
    "Creation", "Ingestion", "Migration", "Adjustment", "Deletion", "Disposal",
})
DEFAULT_EVENT_TYPE = "Adjustment"

ET.register_namespace("premis", PREMIS_NS)
ET.register_namespace("xsi", XSI_NS)
ET.register_namespace("xlink", XLINK_NS)


def _p(tag: str) -> str:
    return f"{{{PREMIS_NS}}}{tag}"


def _base_name(extraction_root: Path) -> str:
    """Noark-uttrekk er mapper; mappenavnet er stabil base for sidefilen."""
    return Path(extraction_root).name or "noark5"


class PremisProvenanceLogger:
    """Samler PREMIS-hendelser og skriver én samlet proveniensfil."""

    def __init__(self, log_dir, extraction_root, agent_version: str = ""):
        self.log_dir = Path(log_dir)
        self.base = _base_name(Path(extraction_root))
        self.agent_id = (
            f"Noark 5 Workflow Manager v{agent_version}"
            if agent_version else "Noark 5 Workflow Manager"
        )
        self._events: list[dict] = []
        self._path: Path | None = None

    @property
    def out_path(self) -> Path:
        return self.log_dir / f"{self.base}_premis.xml"

    @property
    def path(self) -> Path | None:
        return self._path

    def has_events(self) -> bool:
        return bool(self._events)

    def _ts(self) -> str:
        return datetime.datetime.now().astimezone().isoformat(timespec="seconds")

    def record(self, op, result, ctx) -> None:
        """Registrer én PREMIS-hendelse og speil den i vanlig kjørelogg."""
        try:
            raw_type = (getattr(op, "premis_event_type", "") or "").strip()
            if raw_type in VALID_EVENT_TYPES:
                event_type = raw_type
            else:
                if raw_type:
                    logger.warning(
                        "Ugyldig PREMIS eventType %r fra %s - bruker %r",
                        raw_type,
                        getattr(getattr(op, "definition", None), "operation_id", "?"),
                        DEFAULT_EVENT_TYPE,
                    )
                event_type = DEFAULT_EVENT_TYPE

            label = (getattr(op, "premis_event_label", "") or "").strip()
            if not label and raw_type and raw_type not in VALID_EVENT_TYPES:
                label = raw_type

            try:
                detail = op.premis_detail(result, ctx)
            except Exception:
                detail = getattr(result, "message", "") or ""

            definition = getattr(op, "definition", None)
            self._events.append({
                "type": event_type,
                "label": label,
                "op_id": getattr(definition, "operation_id", ""),
                "datetime": self._ts(),
                "detail": detail or "",
                "success": bool(getattr(result, "ok", True)),
            })

            if ctx is not None:
                status = "OK" if getattr(result, "ok", True) else "FEIL"
                shown = f"{event_type} ({label})" if label else event_type
                ctx.log(f"PREMIS: {shown} ({status}) - {detail or '-'}")
        except Exception:
            logger.exception("Kunne ikke registrere PREMIS-hendelse for %r", op)

    def finalize(self, extraction_root, ctx=None) -> "Path | None":
        """Skriv akkumulert proveniens. Returner None dersom det ikke finnes events."""
        if not self._events:
            return None
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            root = self._build_tree(Path(extraction_root), ctx)
            tree = ET.ElementTree(root)
            try:
                ET.indent(tree, space="  ")
            except Exception:
                pass
            out = self.out_path
            tree.write(out, encoding="utf-8", xml_declaration=True)
            self._path = out
            logger.info("PREMIS-proveniens skrevet: %s (%d hendelser)", out, len(self._events))
            if ctx is not None:
                ctx.log(f"PREMIS-proveniens skrevet: {out}")
            return out
        except Exception:
            logger.exception("Kunne ikke skrive PREMIS-proveniensfil")
            if ctx is not None:
                ctx.log("ADVARSEL: Kunne ikke skrive PREMIS-proveniensfil")
            return None

    def _build_tree(self, extraction_root: Path, ctx) -> ET.Element:
        obj_id = extraction_root.name
        root = ET.Element(_p("premis"), {
            f"{{{XSI_NS}}}schemaLocation": (
                f"{PREMIS_NS} http://schema.arkivverket.no/PREMIS/v2.0/DIAS_PREMIS.xsd"
            ),
            "version": "2.0",
        })

        obj = ET.SubElement(root, _p("object"))
        obj.set(f"{{{XSI_NS}}}type", "premis:file")
        oid = ET.SubElement(obj, _p("objectIdentifier"))
        ET.SubElement(oid, _p("objectIdentifierType")).text = "NO/RA"
        ET.SubElement(oid, _p("objectIdentifierValue")).text = obj_id
        chars = ET.SubElement(obj, _p("objectCharacteristics"))
        ET.SubElement(chars, _p("compositionLevel")).text = "0"
        fmt = ET.SubElement(chars, _p("format"))
        fmt_des = ET.SubElement(fmt, _p("formatDesignation"))
        ET.SubElement(fmt_des, _p("formatName")).text = "NOARK-5"

        for i, ev in enumerate(self._events, 1):
            e = ET.SubElement(root, _p("event"))
            eid = ET.SubElement(e, _p("eventIdentifier"))
            ET.SubElement(eid, _p("eventIdentifierType")).text = "Noark5-Workflow-Manager"
            ET.SubElement(eid, _p("eventIdentifierValue")).text = str(i)
            ET.SubElement(e, _p("eventType")).text = ev["type"]
            ET.SubElement(e, _p("eventDateTime")).text = ev["datetime"]

            label, detail = ev.get("label", ""), ev.get("detail", "")
            if label and detail:
                detail_text = f"{label}: {detail}"
            else:
                detail_text = label or detail
            if detail_text:
                ET.SubElement(e, _p("eventDetail")).text = detail_text

            outcome_inf = ET.SubElement(e, _p("eventOutcomeInformation"))
            ET.SubElement(outcome_inf, _p("eventOutcome")).text = "0" if ev["success"] else "1"

            lai = ET.SubElement(e, _p("linkingAgentIdentifier"))
            ET.SubElement(lai, _p("linkingAgentIdentifierType")).text = "Noark5-Workflow-Manager"
            ET.SubElement(lai, _p("linkingAgentIdentifierValue")).text = self.agent_id

            loi = ET.SubElement(e, _p("linkingObjectIdentifier"))
            ET.SubElement(loi, _p("linkingObjectIdentifierType")).text = "NO/RA"
            ET.SubElement(loi, _p("linkingObjectIdentifierValue")).text = obj_id

        agent = ET.SubElement(root, _p("agent"))
        aid = ET.SubElement(agent, _p("agentIdentifier"))
        ET.SubElement(aid, _p("agentIdentifierType")).text = "Noark5-Workflow-Manager"
        ET.SubElement(aid, _p("agentIdentifierValue")).text = self.agent_id
        ET.SubElement(agent, _p("agentName")).text = "Noark 5 Workflow Manager"
        ET.SubElement(agent, _p("agentType")).text = "software"

        return root
