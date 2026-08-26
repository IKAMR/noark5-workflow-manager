from pathlib import Path

from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.operation import BaseOperation, ExecutionTarget, OperationDefinition
from noark5_workflow.core.result import OperationResult
from noark5_workflow.sources.noark5_extraction import Noark5Extraction


class MetadataInventoryOperation(BaseOperation):
    definition = OperationDefinition(
        operation_id="metadata_inventory",
        name="Metadataoversikt",
        description="Rapporter metadatafiler som er funnet og filstørrelse i byte uten å lese dokumentfiler.",
        execution_target=ExecutionTarget.EITHER,
    )

    def can_run(self, ctx: OperationContext) -> tuple[bool, str]:
        extraction = ctx.source or Noark5Extraction.detect(ctx.extraction_root)
        return extraction.is_noark5_candidate, "arkivstruktur.xml is required."

    def run(self, ctx: OperationContext) -> OperationResult:
        extraction = ctx.source or Noark5Extraction.detect(ctx.extraction_root)
        rows = []
        files = [p for p in extraction.metadata_files.values() if p]
        files += extraction.business_metadata_files
        total = max(1, len(files))
        for idx, path in enumerate(files, start=1):
            path = Path(path)
            rows.append({"name": path.name, "path": str(path), "bytes": path.stat().st_size})
            ctx.progress(idx / total, f"Inventory: {path.name}")
        return OperationResult(
            True,
            f"Metadataoversikt complete: {len(rows)} XML file(s).",
            data={"files": rows, "xsd_count": len(extraction.xsd_files)},
        )
