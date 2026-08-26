from .base import BaseExecutor
from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.operation import BaseOperation
from noark5_workflow.core.result import OperationResult


class LocalExecutor(BaseExecutor):
    backend_id = "local"

    def execute(self, operation: BaseOperation, ctx: OperationContext) -> OperationResult:
        allowed, reason = operation.can_run(ctx)
        if not allowed:
            return OperationResult(False, reason or "Operasjonen kan ikke kjøres i denne konteksten.")
        return operation.run(ctx)
