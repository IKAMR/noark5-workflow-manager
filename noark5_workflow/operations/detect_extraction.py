from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.operation import BaseOperation, ExecutionTarget, OperationDefinition
from noark5_workflow.core.result import OperationResult
from noark5_workflow.sources.noark5_extraction import Noark5Extraction


class DetectExtractionOperation(BaseOperation):
    definition = OperationDefinition(
        operation_id="detect_extraction",
        name="Finn Noark 5-uttrekk",
        description="Finn sentrale Noark 5 XML-/XSD-filer og dokumenter-mappen.",
        execution_target=ExecutionTarget.EITHER,
    )

    def run(self, ctx: OperationContext) -> OperationResult:
        ctx.progress(0.1, "Scanning extraction root")
        extraction = Noark5Extraction.detect(ctx.extraction_root)
        ctx.source = extraction
        inventory = extraction.inventory()
        ctx.progress(1.0, "Deteksjon fullført")
        if not extraction.is_noark5_candidate:
            return OperationResult(False, "arkivstruktur.xml ble ikke funnet.", data=inventory)
        return OperationResult(True, "Noark 5-uttrekk funnet.", data=inventory)
