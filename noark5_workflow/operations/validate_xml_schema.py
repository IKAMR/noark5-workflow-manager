from __future__ import annotations

import json
from pathlib import Path

from noark5_workflow.analysis.xml_schema_validation import (
    resolve_local_schema,
    validate_xml_against_xsd,
    write_validation_report,
)
from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.operation import BaseOperation, ExecutionTarget, OperationDefinition
from noark5_workflow.core.result import OperationResult
from noark5_workflow.sources.noark5_extraction import Noark5Extraction


DEFINITION_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "noark5"
    / "xml_schema_validation.json"
)


class ValidateXmlSchemaOperation(BaseOperation):
    definition = OperationDefinition(
        operation_id="validate_xml_schema",
        name="Valider XML mot XSD",
        description=(
            "Validerer arkivstruktur.xml mot lokal XSD med lxml og skriver "
            "et strukturert JSON-resultat til jobbens utdataområde."
        ),
        execution_target=ExecutionTarget.EITHER,
        category="Integritet",
    )

    def can_run(self, ctx: OperationContext) -> tuple[bool, str]:
        extraction = ctx.source or Noark5Extraction.detect(ctx.extraction_root)
        if not extraction.metadata_files.get("arkivstruktur"):
            return False, "arkivstruktur.xml er påkrevd."
        if not extraction.xsd_files:
            return False, "Ingen lokal XSD-fil ble funnet i uttrekket."
        if ctx.output_root is None:
            return False, "Jobben må ha et utdataområde for valideringsrapporten."
        return True, ""

    def run(self, ctx: OperationContext) -> OperationResult:
        extraction = ctx.source or Noark5Extraction.detect(ctx.extraction_root)
        definition = json.loads(DEFINITION_PATH.read_text(encoding="utf-8"))
        item = definition["validations"][0]

        xml_path = extraction.metadata_files[item["source_key"]]
        if xml_path is None:
            return OperationResult(False, f"{item['source']} ble ikke funnet.")

        schema_path = resolve_local_schema(
            xml_path,
            extraction.xsd_files,
            item.get("schema", {}).get("preferred_names", []),
        )
        if schema_path is None:
            return OperationResult(
                False,
                "Kunne ikke avgjøre hvilken lokal XSD som hører til arkivstruktur.xml.",
                data={"available_xsds": [str(p) for p in extraction.xsd_files]},
            )

        ctx.progress(0.25, f"XSD: {schema_path.name}")
        result = validate_xml_against_xsd(xml_path, schema_path)

        report_path = (
            Path(ctx.output_root)
            / "noark5-analysis"
            / item["output"]
        )
        write_validation_report(
            result,
            report_path,
            validation_id=item["id"],
        )
        ctx.progress(1.0, "XML/XSD-validering fullført")

        if result.valid:
            return OperationResult(
                True,
                f"XML/XSD-validering OK. Rapport: {report_path}",
                data={
                    **result.as_dict(),
                    "report": str(report_path),
                },
            )

        return OperationResult(
            False,
            f"XML/XSD-validering feilet med {len(result.errors)} avvik. Rapport: {report_path}",
            data={
                **result.as_dict(),
                "report": str(report_path),
            },
        )
