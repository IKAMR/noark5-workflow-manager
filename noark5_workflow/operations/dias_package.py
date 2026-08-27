from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import shutil
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid1
from xml.sax.saxutils import escape, quoteattr

from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.operation import BaseOperation, ExecutionTarget, OperationDefinition
from noark5_workflow.core.result import OperationResult
from noark5_workflow.sources.noark5_extraction import Noark5Extraction

DEFAULT_PARAMS = {
    "submission_agreement": "",
    "label": "",
    "system": "",
    "system_version": "",
    "archivist_type": "NOARK-5",
    "period_start": "",
    "period_end": "",
    "owner_org": "",
    "archivist_org": "",
    "submitter_org": "",
    "submitter_person": "",
    "producer_org": "",
    "producer_person": "",
    "producer_software": "Noark 5 Workflow Manager",
    "creator": "",
    "preserver": "",
    "output_dir": "",
    "extra_files": "[]",
}

_REQUIRED_META = [
    "label", "system", "system_version", "submission_agreement", "archivist_type",
    "period_start", "period_end", "owner_org", "archivist_org", "submitter_org",
    "submitter_person", "producer_org", "producer_person", "producer_software",
    "creator", "preserver",
]

_ALLOWED_EXTRA_ROOTS = ("content/", "administrative_metadata/", "descriptive_metadata/")
_RESERVED_EXTRA_DESTS = {
    "mets.xml",
    "log.xml",
    "administrative_metadata/premis.xml",
}


def _ts() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _fmt_bytes(value: int) -> str:
    for unit, factor in (("TB", 1024**4), ("GB", 1024**3), ("MB", 1024**2), ("kB", 1024)):
        if value >= factor:
            return f"{value / factor:.1f} {unit}"
    return f"{value} B"


def _sha256_file(path: Path, ctx: OperationContext | None = None) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            if ctx and ctx.cancelled():
                raise RuntimeError("Operasjonen ble avbrutt.")
            block = handle.read(4_000_000)
            if not block:
                break
            sha.update(block)
    return sha.hexdigest()


def _iter_files(root: Path):
    for base, dirs, files in os.walk(root):
        dirs.sort(key=str.lower)
        files.sort(key=str.lower)
        base_path = Path(base)
        for name in files:
            yield base_path / name


def _iter_dirs(root: Path):
    for base, dirs, _files in os.walk(root):
        dirs.sort(key=str.lower)
        base_path = Path(base)
        for name in dirs:
            yield base_path / name


def _normalise_extra_files(raw) -> list[dict[str, str]]:
    try:
        items = json.loads(raw) if isinstance(raw, str) else list(raw or [])
    except Exception:
        items = []
    result: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind", "file"))
        src = str(item.get("src", "")).strip()
        dest = str(item.get("dest", "")).replace("\\", "/").lstrip("/").rstrip("/").strip()
        if kind not in ("file", "folder", "empty_folder"):
            raise ValueError(f"Ukjent type tilleggsinnhold: {kind}")
        if kind in ("file", "folder") and not src:
            continue
        if not dest:
            continue
        parts = Path(dest).parts
        if ".." in parts or dest in _RESERVED_EXTRA_DESTS:
            raise ValueError(f"Ugyldig målsti for tilleggsinnhold: {dest}")
        if not any(dest == prefix.rstrip("/") or dest.startswith(prefix) for prefix in _ALLOWED_EXTRA_ROOTS):
            raise ValueError(
                "Tilleggsinnhold må plasseres under content/, administrative_metadata/ "
                "eller descriptive_metadata/."
            )
        result.append({"kind": kind, "src": src, "dest": dest})
    return result

def _estimate_source_size(root: Path, extra_files: list[dict[str, str]] | None = None) -> tuple[int, int]:
    total_bytes = 0
    total_files = 0
    for path in _iter_files(root):
        try:
            total_bytes += path.stat().st_size
            total_files += 1
        except OSError:
            continue
    for ef in extra_files or []:
        try:
            p = Path(ef.get("src", ""))
            kind = ef.get("kind", "file")
            if kind == "file" and p.is_file():
                total_bytes += p.stat().st_size
                total_files += 1
            elif kind == "folder" and p.is_dir():
                for child in _iter_files(p):
                    total_bytes += child.stat().st_size
                    total_files += 1
        except OSError:
            continue
    return int(total_bytes * 1.03) + 2 * 1024 * 1024, total_files


def _make_info(path: Path, key: str, ctx: OperationContext) -> dict:
    stat = path.stat()
    return {
        "sha256": _sha256_file(path, ctx),
        "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "size": stat.st_size,
        "mtime": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
    }


def _gather_source_info(root: Path, sip_id: str, ctx: OperationContext, total_files: int) -> dict[str, dict]:
    info: dict[str, dict] = {}
    total = max(total_files, 1)
    for index, path in enumerate(_iter_files(root), start=1):
        rel = path.relative_to(root).as_posix()
        key = f"{sip_id}/content/{rel}"
        info[key] = _make_info(path, key, ctx)
        if index == 1 or index == total_files or index % 100 == 0:
            ctx.progress(index / total, f"Sjekksummer: {index}/{total_files} filer")
    return info


def _write_sip_log(path: Path, sip_id: str, created: str, meta: dict) -> None:
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<premis:premis xmlns:premis="http://arkivverket.no/standarder/PREMIS"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:schemaLocation="http://arkivverket.no/standarder/PREMIS http://schema.arkivverket.no/PREMIS/v2.0/DIAS_PREMIS.xsd"
 version="2.0">
  <premis:object xsi:type="premis:file">
    <premis:objectIdentifier><premis:objectIdentifierType>NO/RA</premis:objectIdentifierType><premis:objectIdentifierValue>{escape(sip_id)}</premis:objectIdentifierValue></premis:objectIdentifier>
    <premis:preservationLevel><premis:preservationLevelValue>full</premis:preservationLevelValue></premis:preservationLevel>
    <premis:significantProperties><premis:significantPropertiesType>createdate</premis:significantPropertiesType><premis:significantPropertiesValue>{escape(created)}</premis:significantPropertiesValue></premis:significantProperties>
    <premis:significantProperties><premis:significantPropertiesType>archivist_organization</premis:significantPropertiesType><premis:significantPropertiesValue>{escape(meta['archivist_org'])}</premis:significantPropertiesValue></premis:significantProperties>
    <premis:significantProperties><premis:significantPropertiesType>label</premis:significantPropertiesType><premis:significantPropertiesValue>{escape(meta['label'])}</premis:significantPropertiesValue></premis:significantProperties>
    <premis:significantProperties><premis:significantPropertiesType>iptype</premis:significantPropertiesType><premis:significantPropertiesValue>SIP</premis:significantPropertiesValue></premis:significantProperties>
    <premis:objectCharacteristics><premis:compositionLevel>0</premis:compositionLevel><premis:format><premis:formatDesignation><premis:formatName>tar</premis:formatName></premis:formatDesignation></premis:format></premis:objectCharacteristics>
  </premis:object>
  <premis:event>
    <premis:eventIdentifier><premis:eventIdentifierType>NO/RA</premis:eventIdentifierType><premis:eventIdentifierValue>{uuid1()}</premis:eventIdentifierValue></premis:eventIdentifier>
    <premis:eventType>10000</premis:eventType><premis:eventDateTime>{escape(created)}</premis:eventDateTime>
    <premis:eventDetail>Log circular created</premis:eventDetail>
    <premis:eventOutcomeInformation><premis:eventOutcome>0</premis:eventOutcome></premis:eventOutcomeInformation>
    <premis:linkingObjectIdentifier><premis:linkingObjectIdentifierType>NO/RA</premis:linkingObjectIdentifierType><premis:linkingObjectIdentifierValue>{escape(sip_id)}</premis:linkingObjectIdentifierValue></premis:linkingObjectIdentifier>
  </premis:event>
</premis:premis>
'''
    path.write_text(xml, encoding="utf-8")


def _write_sip_premis(path: Path, sip_id: str, info: dict[str, dict]) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<premis:premis xmlns:premis="http://arkivverket.no/standarder/PREMIS" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://arkivverket.no/standarder/PREMIS http://schema.arkivverket.no/PREMIS/v2.0/DIAS_PREMIS.xsd" version="2.0">',
        '  <premis:object xsi:type="premis:file">',
        '    <premis:objectIdentifier><premis:objectIdentifierType>NO/RA</premis:objectIdentifierType>'
        f'<premis:objectIdentifierValue>{escape(sip_id)}</premis:objectIdentifierValue></premis:objectIdentifier>',
        '    <premis:preservationLevel><premis:preservationLevelValue>full</premis:preservationLevelValue></premis:preservationLevel>',
        '    <premis:storage><premis:storageMedium>ESSArch Tools</premis:storageMedium></premis:storage>',
        '  </premis:object>',
    ]
    for key, item in info.items():
        extension = Path(key).suffix.lstrip(".") or "unknown"
        lines.extend([
            '  <premis:object xsi:type="premis:file">',
            '    <premis:objectIdentifier><premis:objectIdentifierType>NO/RA</premis:objectIdentifierType>'
            f'<premis:objectIdentifierValue>{escape(key)}</premis:objectIdentifierValue></premis:objectIdentifier>',
            '    <premis:objectCharacteristics>',
            '      <premis:compositionLevel>0</premis:compositionLevel>',
            '      <premis:fixity><premis:messageDigestAlgorithm>SHA-256</premis:messageDigestAlgorithm>'
            f'<premis:messageDigest>{item["sha256"]}</premis:messageDigest><premis:messageDigestOriginator>Noark 5 Workflow Manager</premis:messageDigestOriginator></premis:fixity>',
            f'      <premis:size>{item["size"]}</premis:size>',
            f'      <premis:format><premis:formatDesignation><premis:formatName>{escape(extension)}</premis:formatName></premis:formatDesignation></premis:format>',
            '    </premis:objectCharacteristics>',
            f'    <premis:storage><premis:contentLocation><premis:contentLocationType>SIP</premis:contentLocationType><premis:contentLocationValue>{escape(sip_id)}</premis:contentLocationValue></premis:contentLocation></premis:storage>',
            '    <premis:relationship><premis:relationshipType>structural</premis:relationshipType><premis:relationshipSubType>is part of</premis:relationshipSubType>'
            f'<premis:relatedObjectIdentification><premis:relatedObjectIdentifierType>NO/RA</premis:relatedObjectIdentifierType><premis:relatedObjectIdentifierValue>{escape(sip_id)}</premis:relatedObjectIdentifierValue></premis:relatedObjectIdentification></premis:relationship>',
            '  </premis:object>',
        ])
    lines.extend([
        '  <premis:agent><premis:agentIdentifier><premis:agentIdentifierType>NO/RA</premis:agentIdentifierType><premis:agentIdentifierValue>Noark5WorkflowManager</premis:agentIdentifierValue></premis:agentIdentifier><premis:agentName>Noark 5 Workflow Manager</premis:agentName><premis:agentType>software</premis:agentType></premis:agent>',
        '</premis:premis>',
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_sip_mets(path: Path, premis_path: Path, sip_id: str, created: str, info: dict[str, dict], meta: dict) -> None:
    premis_sha = _sha256_file(premis_path)
    premis_stat = premis_path.stat()
    premis_mtime = datetime.fromtimestamp(premis_stat.st_mtime).astimezone().isoformat(timespec="seconds")
    ids: list[str] = []
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/METS/ http://schema.arkivverket.no/METS/mets.xsd" PROFILE="http://xml.ra.se/METS/RA_METS_eARD.xml" LABEL={quoteattr(meta["label"])} TYPE="SIP" ID="ID{uuid1()}" OBJID="UUID:{sip_id}">',
        f'  <mets:metsHdr CREATEDATE={quoteattr(created)} RECORDSTATUS="NEW">',
        f'    <mets:agent TYPE="ORGANIZATION" ROLE="ARCHIVIST"><mets:name>{escape(meta["archivist_org"])}</mets:name></mets:agent>',
        f'    <mets:agent TYPE="OTHER" OTHERTYPE="SOFTWARE" ROLE="ARCHIVIST"><mets:name>{escape(meta["system"])}</mets:name></mets:agent>',
        f'    <mets:agent TYPE="OTHER" OTHERTYPE="SOFTWARE" ROLE="ARCHIVIST"><mets:name>{escape(meta["system_version"])}</mets:name></mets:agent>',
        f'    <mets:agent TYPE="OTHER" OTHERTYPE="SOFTWARE" ROLE="ARCHIVIST"><mets:name>{escape(meta["archivist_type"])}</mets:name></mets:agent>',
        f'    <mets:agent TYPE="ORGANIZATION" ROLE="CREATOR"><mets:name>{escape(meta["creator"])}</mets:name></mets:agent>',
        f'    <mets:agent TYPE="ORGANIZATION" ROLE="OTHER" OTHERROLE="PRODUCER"><mets:name>{escape(meta["producer_org"])}</mets:name></mets:agent>',
        f'    <mets:agent TYPE="INDIVIDUAL" ROLE="OTHER" OTHERROLE="PRODUCER"><mets:name>{escape(meta["producer_person"])}</mets:name></mets:agent>',
        f'    <mets:agent TYPE="OTHER" OTHERTYPE="SOFTWARE" ROLE="OTHER" OTHERROLE="PRODUCER"><mets:name>{escape(meta["producer_software"])}</mets:name></mets:agent>',
        f'    <mets:agent TYPE="ORGANIZATION" ROLE="OTHER" OTHERROLE="SUBMITTER"><mets:name>{escape(meta["submitter_org"])}</mets:name></mets:agent>',
        f'    <mets:agent TYPE="INDIVIDUAL" ROLE="OTHER" OTHERROLE="SUBMITTER"><mets:name>{escape(meta["submitter_person"])}</mets:name></mets:agent>',
        f'    <mets:agent TYPE="ORGANIZATION" ROLE="IPOWNER"><mets:name>{escape(meta["owner_org"])}</mets:name></mets:agent>',
        f'    <mets:agent TYPE="ORGANIZATION" ROLE="PRESERVATION"><mets:name>{escape(meta["preserver"])}</mets:name></mets:agent>',
        f'    <mets:altRecordID TYPE="SUBMISSIONAGREEMENT">{escape(meta["submission_agreement"])}</mets:altRecordID>',
        f'    <mets:altRecordID TYPE="STARTDATE">{escape(meta["period_start"])}</mets:altRecordID>',
        f'    <mets:altRecordID TYPE="ENDDATE">{escape(meta["period_end"])}</mets:altRecordID>',
        '    <mets:metsDocumentID>mets.xml</mets:metsDocumentID>',
        '  </mets:metsHdr>',
        '  <mets:amdSec ID="amdSec001"><mets:digiprovMD ID="digiprovMD001">',
        f'    <mets:mdRef MIMETYPE="text/xml" CHECKSUMTYPE="SHA-256" CHECKSUM="{premis_sha}" MDTYPE="PREMIS" xlink:href="file:administrative_metadata/premis.xml" LOCTYPE="URL" CREATED={quoteattr(premis_mtime)} xlink:type="simple" ID="ID{uuid1()}" SIZE="{premis_stat.st_size}"/>',
        '  </mets:digiprovMD></mets:amdSec>',
        '  <mets:fileSec><mets:fileGrp ID="fgrp001" USE="FILES">',
    ]
    for key, item in info.items():
        file_id = f"ID{uuid1()}"
        ids.append(file_id)
        rel = key.removeprefix(f"{sip_id}/")
        lines.append(
            f'    <mets:file MIMETYPE={quoteattr(item["mime"])} CHECKSUMTYPE="SHA-256" CREATED={quoteattr(item["mtime"])} CHECKSUM="{item["sha256"]}" USE="Datafile" ID="{file_id}" SIZE="{item["size"]}"><mets:FLocat xlink:href={quoteattr("file:" + rel)} LOCTYPE="URL" xlink:type="simple"/></mets:file>'
        )
    lines.extend(['  </mets:fileGrp></mets:fileSec>', '  <mets:structMap><mets:div LABEL="Package"><mets:div ADMID="amdSec001" LABEL="Datafiles">'])
    for file_id in ids:
        lines.append(f'    <mets:fptr FILEID="{file_id}"/>')
    lines.extend(['  </mets:div></mets:div></mets:structMap>', '</mets:mets>'])
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_info(path: Path, tar_path: Path, sip_id: str, created: str, meta: dict) -> None:
    digest = _sha256_file(tar_path)
    stat = tar_path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds")
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:schemaLocation="http://www.loc.gov/METS/ http://schema.arkivverket.no/METS/info.xsd"
 PROFILE="http://xml.ra.se/METS/RA_METS_eARD.xml" LABEL={quoteattr(meta['label'])} TYPE="SIP" ID="ID{uuid1()}" OBJID="UUID:{sip_id}">
  <mets:metsHdr CREATEDATE={quoteattr(created)} RECORDSTATUS="NEW">
    <mets:agent TYPE="ORGANIZATION" ROLE="ARCHIVIST"><mets:name>{escape(meta['archivist_org'])}</mets:name></mets:agent>
    <mets:altRecordID TYPE="SUBMISSIONAGREEMENT">{escape(meta['submission_agreement'])}</mets:altRecordID>
    <mets:metsDocumentID>info.xml</mets:metsDocumentID>
  </mets:metsHdr>
  <mets:fileSec><mets:fileGrp ID="fgrp001" USE="FILES"><mets:file MIMETYPE="application/x-tar" CHECKSUMTYPE="SHA-256" CHECKSUM="{digest}" CREATED={quoteattr(mtime)} ID="ID{uuid1()}" SIZE="{stat.st_size}"><mets:FLocat xlink:href={quoteattr(f'file:{sip_id}/content/{sip_id}.tar')} LOCTYPE="URL" xlink:type="simple"/></mets:file></mets:fileGrp></mets:fileSec>
  <mets:structMap><mets:div LABEL="Package"/></mets:structMap>
</mets:mets>
'''
    path.write_text(xml, encoding="utf-8")


def _write_aic_log(path: Path, aic_id: str, sip_id: str, created: str, meta: dict) -> None:
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<premis:premis xmlns:premis="http://arkivverket.no/standarder/PREMIS" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.0">
  <premis:object xsi:type="premis:file"><premis:objectIdentifier><premis:objectIdentifierType>NO/RA</premis:objectIdentifierType><premis:objectIdentifierValue>{escape(aic_id)}</premis:objectIdentifierValue></premis:objectIdentifier><premis:significantProperties><premis:significantPropertiesType>label</premis:significantPropertiesType><premis:significantPropertiesValue>{escape(meta['label'])}</premis:significantPropertiesValue></premis:significantProperties><premis:significantProperties><premis:significantPropertiesType>iptype</premis:significantPropertiesType><premis:significantPropertiesValue>AIC</premis:significantPropertiesValue></premis:significantProperties></premis:object>
  <premis:event><premis:eventIdentifier><premis:eventIdentifierType>NO/RA</premis:eventIdentifierType><premis:eventIdentifierValue>{uuid1()}</premis:eventIdentifierValue></premis:eventIdentifier><premis:eventType>20000</premis:eventType><premis:eventDateTime>{escape(created)}</premis:eventDateTime><premis:eventDetail>Created AIC package</premis:eventDetail><premis:eventOutcomeInformation><premis:eventOutcome>0</premis:eventOutcome></premis:eventOutcomeInformation><premis:linkingObjectIdentifier><premis:linkingObjectIdentifierType>NO/RA</premis:linkingObjectIdentifierType><premis:linkingObjectIdentifierValue>{escape(sip_id)}</premis:linkingObjectIdentifierValue></premis:linkingObjectIdentifier></premis:event>
</premis:premis>
'''
    path.write_text(xml, encoding="utf-8")


def _prepare_extra_content(source_root: Path, sip_id: str, meta: dict, ctx: OperationContext) -> tuple[list[dict[str, str]], dict[str, dict]]:
    """Validate extra package content and gather metadata without staging copies.

    Files and folders selected by the user remain at their original locations on
    disk and are later streamed directly into the uncompressed TAR. This avoids
    duplicating large directory trees in the temporary work area and prevents
    unnecessary Windows path-length growth.
    """
    extras = _normalise_extra_files(meta.get("extra_files", "[]"))
    extra_info: dict[str, dict] = {}
    prepared: list[dict[str, str]] = []
    seen_dests: set[str] = set()

    def check_content_collision(dest_rel: str) -> None:
        if dest_rel == "content" or dest_rel.startswith("content/"):
            rel = dest_rel.removeprefix("content/") if dest_rel != "content" else ""
            source_collision = source_root / rel if rel else source_root
            if rel and source_collision.exists():
                raise FileExistsError(f"Tilleggsinnhold kolliderer med kildeinnhold: {dest_rel}")

    for ef in extras:
        kind = ef.get("kind", "file")
        src = Path(ef.get("src", "")) if ef.get("src") else None
        dest_rel = ef["dest"]
        check_content_collision(dest_rel)
        if dest_rel in seen_dests:
            raise FileExistsError(f"To elementer har samme målsti i DIAS-pakken: {dest_rel}")
        seen_dests.add(dest_rel)

        if kind == "empty_folder":
            prepared.append({"kind": kind, "src": "", "dest": dest_rel})
            ctx.log(f"Mappe opprettet i pakke: {dest_rel}/")
            continue

        if kind == "folder":
            if src is None or not src.is_dir():
                raise FileNotFoundError(f"Ekstra mappe finnes ikke: {src}")
            file_count = 0
            for child in _iter_files(src):
                rel_inside = child.relative_to(src).as_posix()
                key = f"{sip_id}/{dest_rel}/{rel_inside}"
                extra_info[key] = _make_info(child, key, ctx)
                file_count += 1
            prepared.append({"kind": kind, "src": str(src), "dest": dest_rel})
            ctx.log(f"Ekstra mappe klar for pakking: {dest_rel}/ ({file_count} filer)")
            continue

        if src is None or not src.is_file():
            raise FileNotFoundError(f"Ekstra fil finnes ikke: {src}")
        key = f"{sip_id}/{dest_rel}"
        extra_info[key] = _make_info(src, key, ctx)
        prepared.append({"kind": kind, "src": str(src), "dest": dest_rel})
        ctx.log(f"Ekstra fil klar for pakking: {dest_rel}")

    return prepared, extra_info


def _add_extra_content_to_tar(tar: tarfile.TarFile, sip_id: str, extras: list[dict[str, str]], ctx: OperationContext) -> None:
    """Stream additional files/folders directly into the SIP TAR."""
    for ef in extras:
        if ctx.cancelled():
            raise RuntimeError("Operasjonen ble avbrutt.")
        kind = ef.get("kind", "file")
        dest_rel = ef["dest"].rstrip("/")
        arc_root = f"{sip_id}/{dest_rel}"

        if kind == "empty_folder":
            info = tarfile.TarInfo(name=arc_root + "/")
            info.type = tarfile.DIRTYPE
            info.mode = 0o755
            info.mtime = int(datetime.now().timestamp())
            tar.addfile(info)
            continue

        src = Path(ef["src"])
        if kind == "file":
            tar.add(src, arcname=arc_root, recursive=False)
            continue

        tar.add(src, arcname=arc_root, recursive=False)
        for directory in _iter_dirs(src):
            rel = directory.relative_to(src).as_posix()
            tar.add(directory, arcname=f"{arc_root}/{rel}", recursive=False)
        for child in _iter_files(src):
            if ctx.cancelled():
                raise RuntimeError("Operasjonen ble avbrutt.")
            rel = child.relative_to(src).as_posix()
            tar.add(child, arcname=f"{arc_root}/{rel}", recursive=False)


def _build_package(source_root: Path, out_root: Path, meta: dict, ctx: OperationContext, source_file_count: int) -> tuple[Path, int]:
    sip_id = str(uuid1())
    aic_id = str(uuid1())
    temp_dir_setting = str(ctx.settings.get("temp_dir", "") or "").strip()
    temp_base = Path(temp_dir_setting) if temp_dir_setting and Path(temp_dir_setting).is_dir() else None
    work = Path(tempfile.mkdtemp(dir=temp_base))
    package_root = work / "d"
    outer_sip = package_root / sip_id
    inner = outer_sip / "content" / sip_id
    (outer_sip / "administrative_metadata" / "repository_operations").mkdir(parents=True, exist_ok=True)
    (outer_sip / "descriptive_metadata").mkdir(parents=True, exist_ok=True)
    (inner / "administrative_metadata").mkdir(parents=True, exist_ok=True)
    (inner / "descriptive_metadata").mkdir(parents=True, exist_ok=True)
    (inner / "content").mkdir(parents=True, exist_ok=True)

    try:
        created = _ts()
        ctx.log("Beregner SHA-256 for filer i Noark 5-uttrekket...")
        source_info = _gather_source_info(source_root, sip_id, ctx, source_file_count)
        prepared_extras, extra_info = _prepare_extra_content(source_root, sip_id, meta, ctx)
        info = {**source_info, **extra_info}

        _write_sip_log(inner / "log.xml", sip_id, created, meta)
        _write_sip_premis(inner / "administrative_metadata" / "premis.xml", sip_id, info)
        _write_sip_mets(inner / "mets.xml", inner / "administrative_metadata" / "premis.xml", sip_id, created, info, meta)

        tar_path = outer_sip / "content" / f"{sip_id}.tar"
        ctx.log("Oppretter ukomprimert SIP TAR...")
        with tarfile.open(tar_path, "w") as tar:
            for path in _iter_dirs(inner):
                arc = path.relative_to(inner.parent).as_posix()
                tar.add(path, arcname=arc, recursive=False)
            for path in _iter_files(inner):
                arc = path.relative_to(inner.parent).as_posix()
                tar.add(path, arcname=arc, recursive=False)
            for path in _iter_dirs(source_root):
                rel = path.relative_to(source_root).as_posix()
                tar.add(path, arcname=f"{sip_id}/content/{rel}", recursive=False)
            for index, path in enumerate(_iter_files(source_root), start=1):
                if ctx.cancelled():
                    raise RuntimeError("Operasjonen ble avbrutt.")
                rel = path.relative_to(source_root).as_posix()
                tar.add(path, arcname=f"{sip_id}/content/{rel}", recursive=False)
                if index == source_file_count or index % 250 == 0:
                    ctx.progress(index / max(source_file_count, 1), f"Pakker: {index}/{source_file_count} filer")
            _add_extra_content_to_tar(tar, sip_id, prepared_extras, ctx)

        shutil.rmtree(inner)
        _write_info(package_root / "info.xml", tar_path, sip_id, created, meta)
        _write_aic_log(outer_sip / "log.xml", aic_id, sip_id, _ts(), meta)
        target = out_root / aic_id
        if target.exists():
            raise FileExistsError(f"Målmappen finnes allerede: {target}")
        try:
            package_root.rename(target)
        except OSError:
            shutil.move(str(package_root), str(target))
        return target, len(prepared_extras)
    finally:
        shutil.rmtree(work, ignore_errors=True)


class DiasPackageOperation(BaseOperation):
    definition = OperationDefinition(
        operation_id="dias_package",
        name="DIAS-pakking (SIP/AIC)",
        description=(
            "Pakker valgt Noark 5-uttrekk som DIAS SIP/AIC med METS, PREMIS, "
            "SHA-256 og ukomprimert TAR. Pakken kan suppleres med filer og mapper."
        ),
        execution_target=ExecutionTarget.EITHER,
        category="SIP/AIC-Pakking",
        status_level=2,
    )

    def __init__(self) -> None:
        self.params = dict(DEFAULT_PARAMS)

    def configure(self, params: dict) -> None:
        self.params = {**DEFAULT_PARAMS, **params}

    def can_run(self, ctx: OperationContext) -> tuple[bool, str]:
        extraction = ctx.source or Noark5Extraction.detect(ctx.extraction_root)
        if not extraction.is_noark5_candidate:
            return False, "Valgt mappe inneholder ikke arkivstruktur.xml."
        missing = [key for key in _REQUIRED_META if not str(self.params.get(key, "")).strip()]
        if missing:
            return False, "Manglende DIAS-parametere: " + ", ".join(missing)
        try:
            _normalise_extra_files(self.params.get("extra_files", "[]"))
        except ValueError as exc:
            return False, str(exc)
        return True, ""

    def run(self, ctx: OperationContext) -> OperationResult:
        extraction = ctx.source or Noark5Extraction.detect(ctx.extraction_root)
        arkivstruktur = extraction.metadata_files.get("arkivstruktur")
        source_root = Path(arkivstruktur).parent if arkivstruktur else extraction.root
        out_root = Path(str(self.params.get("output_dir", "")).strip() or source_root.parent).resolve()
        out_root.mkdir(parents=True, exist_ok=True)
        try:
            source_resolved = source_root.resolve()
            out_resolved = out_root.resolve()
            if out_resolved == source_resolved or source_resolved in out_resolved.parents:
                return OperationResult(False, "Utdatamappen kan ikke ligge inne i Noark 5-uttrekket.")
        except OSError:
            pass

        try:
            extras = _normalise_extra_files(self.params.get("extra_files", "[]"))
        except ValueError as exc:
            return OperationResult(False, str(exc))

        ctx.log("Estimerer pakkestørrelse...")
        estimated, total_with_extras = _estimate_source_size(source_root, extras)
        source_file_count = sum(1 for _ in _iter_files(source_root))
        if source_file_count == 0:
            return OperationResult(False, "Noark 5-uttrekket inneholder ingen filer.")
        try:
            free = shutil.disk_usage(out_root).free
            ctx.log(f"Estimert pakkestørrelse: {_fmt_bytes(estimated)}. Ledig: {_fmt_bytes(free)}.")
            if free < estimated:
                return OperationResult(
                    False,
                    f"Ikke nok ledig plass i {out_root}: trenger ca. {_fmt_bytes(estimated)}, har {_fmt_bytes(free)}.",
                )
        except OSError:
            pass

        meta = {**DEFAULT_PARAMS, **self.params}
        try:
            aic_path, extra_count = _build_package(source_root, out_root, meta, ctx, source_file_count)
        except Exception as exc:
            return OperationResult(False, f"DIAS-pakking feilet: {exc}")
        ctx.progress(1.0, "DIAS-pakking fullført")
        return OperationResult(
            True,
            f"DIAS-pakke opprettet: {aic_path.name}",
            data={
                "aic_path": str(aic_path),
                "source_root": str(source_root),
                "file_count": total_with_extras,
                "source_file_count": source_file_count,
                "extra_file_count": extra_count,
                "estimated_bytes": estimated,
            },
            outputs=[str(aic_path)],
        )
