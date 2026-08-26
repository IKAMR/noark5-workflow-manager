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
}

_REQUIRED_META = [
    "label",
    "system",
    "system_version",
    "submission_agreement",
    "archivist_type",
    "period_start",
    "period_end",
    "owner_org",
    "archivist_org",
    "submitter_org",
    "submitter_person",
    "producer_org",
    "producer_person",
    "producer_software",
    "creator",
    "preserver",
]


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


def _estimate_source_size(root: Path) -> tuple[int, int]:
    total_bytes = 0
    total_files = 0
    for path in _iter_files(root):
        try:
            total_bytes += path.stat().st_size
            total_files += 1
        except OSError:
            continue
    # TAR is uncompressed and metadata adds some overhead.
    return int(total_bytes * 1.03) + 2 * 1024 * 1024, total_files


def _gather_file_info(root: Path, sip_id: str, ctx: OperationContext, total_files: int) -> dict[str, dict]:
    info: dict[str, dict] = {}
    total = max(total_files, 1)
    for index, path in enumerate(_iter_files(root), start=1):
        rel = path.relative_to(root).as_posix()
        stat = path.stat()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        digest = _sha256_file(path, ctx)
        key = f"{sip_id}/content/{rel}"
        info[key] = {
            "sha256": digest,
            "mime": mime,
            "size": stat.st_size,
            "mtime": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
        }
        if index == 1 or index == total_files or index % 100 == 0:
            ctx.progress(index / total, f"Sjekksummer: {index}/{total_files} filer")
    return info


def _write_sip_log(path: Path, sip_id: str, created: str, meta: dict) -> None:
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
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
"""
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
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
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
"""
    path.write_text(xml, encoding="utf-8")


def _write_aic_log(path: Path, aic_id: str, sip_id: str, created: str, meta: dict) -> None:
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<premis:premis xmlns:premis="http://arkivverket.no/standarder/PREMIS" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.0">
  <premis:object xsi:type="premis:file"><premis:objectIdentifier><premis:objectIdentifierType>NO/RA</premis:objectIdentifierType><premis:objectIdentifierValue>{escape(aic_id)}</premis:objectIdentifierValue></premis:objectIdentifier><premis:significantProperties><premis:significantPropertiesType>label</premis:significantPropertiesType><premis:significantPropertiesValue>{escape(meta['label'])}</premis:significantPropertiesValue></premis:significantProperties><premis:significantProperties><premis:significantPropertiesType>iptype</premis:significantPropertiesType><premis:significantPropertiesValue>AIC</premis:significantPropertiesValue></premis:significantProperties></premis:object>
  <premis:event><premis:eventIdentifier><premis:eventIdentifierType>NO/RA</premis:eventIdentifierType><premis:eventIdentifierValue>{uuid1()}</premis:eventIdentifierValue></premis:eventIdentifier><premis:eventType>20000</premis:eventType><premis:eventDateTime>{escape(created)}</premis:eventDateTime><premis:eventDetail>Created AIC package</premis:eventDetail><premis:eventOutcomeInformation><premis:eventOutcome>0</premis:eventOutcome></premis:eventOutcomeInformation><premis:linkingObjectIdentifier><premis:linkingObjectIdentifierType>NO/RA</premis:linkingObjectIdentifierType><premis:linkingObjectIdentifierValue>{escape(sip_id)}</premis:linkingObjectIdentifierValue></premis:linkingObjectIdentifier></premis:event>
</premis:premis>
"""
    path.write_text(xml, encoding="utf-8")


def _build_package(source_root: Path, out_root: Path, meta: dict, ctx: OperationContext, total_files: int) -> Path:
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
        info = _gather_file_info(source_root, sip_id, ctx, total_files)

        _write_sip_log(inner / "log.xml", sip_id, created, meta)
        _write_sip_premis(inner / "administrative_metadata" / "premis.xml", sip_id, info)
        _write_sip_mets(inner / "mets.xml", inner / "administrative_metadata" / "premis.xml", sip_id, created, info, meta)

        tar_path = outer_sip / "content" / f"{sip_id}.tar"
        ctx.log("Oppretter ukomprimert SIP TAR...")
        with tarfile.open(tar_path, "w") as tar:
            for path in _iter_files(inner):
                arc = path.relative_to(inner.parent).as_posix()
                tar.add(path, arcname=arc, recursive=False)
            for index, path in enumerate(_iter_files(source_root), start=1):
                if ctx.cancelled():
                    raise RuntimeError("Operasjonen ble avbrutt.")
                rel = path.relative_to(source_root).as_posix()
                tar.add(path, arcname=f"{sip_id}/content/{rel}", recursive=False)
                if index == total_files or index % 250 == 0:
                    ctx.progress(index / max(total_files, 1), f"Pakker: {index}/{total_files} filer")

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
        return target
    finally:
        shutil.rmtree(work, ignore_errors=True)


class DiasPackageOperation(BaseOperation):
    definition = OperationDefinition(
        operation_id="dias_package",
        name="DIAS-pakking (SIP/AIC)",
        description=(
            "Pakker valgt Noark 5-uttrekk som DIAS SIP/AIC med METS, PREMIS, "
            "SHA-256 og ukomprimert TAR, etter samme hovedprinsipp som SIARD Workflow Manager."
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

        ctx.log("Estimerer pakkestørrelse...")
        estimated, total_files = _estimate_source_size(source_root)
        if total_files == 0:
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
            free = 0

        meta = {**DEFAULT_PARAMS, **self.params}
        try:
            aic_path = _build_package(source_root, out_root, meta, ctx, total_files)
        except Exception as exc:
            return OperationResult(False, f"DIAS-pakking feilet: {exc}")

        ctx.progress(1.0, "DIAS-pakking fullført")
        return OperationResult(
            True,
            f"DIAS-pakke opprettet: {aic_path.name}",
            data={
                "aic_path": str(aic_path),
                "source_root": str(source_root),
                "file_count": total_files,
                "estimated_bytes": estimated,
            },
            outputs=[str(aic_path)],
        )
