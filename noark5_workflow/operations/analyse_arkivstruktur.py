from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.operation import BaseOperation, ExecutionTarget, OperationDefinition
from noark5_workflow.core.result import OperationResult
from noark5_workflow.sources.noark5_extraction import Noark5Extraction


class AnalyseArkivstrukturOperation(BaseOperation):
    definition = OperationDefinition(
        operation_id="analyse_arkivstruktur",
        name="Analyse arkivstruktur.xml (plassholder)",
        description="Fremtidig strømmet Noark 5-metadataanalyse for U1/U2 og kvalitetskontroller.",
        execution_target=ExecutionTarget.EITHER,
        category="Metadata",
    )

    def can_run(self, ctx: OperationContext) -> tuple[bool, str]:
        extraction = ctx.source or Noark5Extraction.detect(ctx.extraction_root)
        return extraction.is_noark5_candidate, "arkivstruktur.xml er påkrevd."

    def run(self, ctx: OperationContext) -> OperationResult:
        extraction = ctx.source or Noark5Extraction.detect(ctx.extraction_root)
        arkivstruktur = extraction.metadata_files["arkivstruktur"]
        ctx.progress(1.0, "Plassholderoperasjon")
        return OperationResult(
            True,
            "Plassholder i skallet: strømmet U1/U2-analyse er ikke implementert ennå.",
            data={"arkivstruktur": str(arkivstruktur)},
            warnings=["Ingen metadata-tellere beregnes i v0.1.0-a2."],
        )
