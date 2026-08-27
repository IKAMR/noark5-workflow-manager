from pathlib import Path

from .base import BaseExecutor
from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.operation import BaseOperation
from noark5_workflow.core.premis_logger import PremisProvenanceLogger
from noark5_workflow.core.result import OperationResult


class LocalExecutor(BaseExecutor):
    backend_id = "local"

    def _premis_logger(
        self, operation: BaseOperation, result: OperationResult, ctx: OperationContext
    ) -> PremisProvenanceLogger | None:
        """Opprett/gjenbruk sentral PREMIS-logger i eksplisitt utdataområde.

        Viktig bevaringsregel: kildeområdet er read-only og brukes aldri som
        fallback for genererte workflow-filer.
        """
        if not bool(ctx.settings.get("enable_premis_provenance", True)):
            return None

        try:
            requested_dir = operation.premis_output_dir(result, ctx)
        except Exception:
            requested_dir = None
        if not requested_dir:
            ctx.log("PREMIS: ingen eksplisitt utdatamappe - workflow-PREMIS skrives ikke")
            return None

        log_dir = Path(requested_dir).resolve()
        extraction_root = Path(getattr(ctx.source, "root", None) or ctx.extraction_root).resolve()

        logger = ctx.metadata.get("premis_logger")
        logger_dir = ctx.metadata.get("premis_output_dir")
        if logger is not None and logger_dir == str(log_dir):
            return logger

        try:
            from version import VERSION
        except Exception:
            VERSION = ""

        logger = PremisProvenanceLogger(log_dir, extraction_root, agent_version=str(VERSION))
        ctx.metadata["premis_object_root"] = extraction_root
        ctx.metadata["premis_output_dir"] = str(log_dir)
        ctx.metadata["premis_logger"] = logger
        return logger

    def execute(self, operation: BaseOperation, ctx: OperationContext) -> OperationResult:
        allowed, reason = operation.can_run(ctx)
        if not allowed:
            return OperationResult(False, reason or "Operasjonen kan ikke kjøres i denne konteksten.")

        result = operation.run(ctx)
        ctx.set_result(operation.definition.operation_id, result.data)

        if operation.premis_should_record(result, ctx):
            premis_logger = self._premis_logger(operation, result, ctx)
            if premis_logger:
                premis_logger.record(operation, result, ctx)
                premis_root = ctx.metadata.get("premis_object_root", ctx.extraction_root)
                premis_logger.finalize(premis_root, ctx)

        return result
