from .base import BaseExecutor
from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.operation import BaseOperation
from noark5_workflow.core.result import OperationResult


class RemoteExecutor(BaseExecutor):
    """Placeholder for future server/client execution.

    Intended future responsibilities:
    - authenticate to a workflow server
    - submit a job referencing shared-storage extraction IDs/paths
    - stream progress and log events back to the client
    - support cancellation, queueing and worker selection
    - return output references and structured OperationResult data

    Large preservation packages should normally remain on shared/server storage;
    this executor should not require uploading entire Noark extractions by default.
    """

    backend_id = "remote"

    def __init__(self, endpoint: str = "") -> None:
        self.endpoint = endpoint

    def execute(self, operation: BaseOperation, ctx: OperationContext) -> OperationResult:
        return OperationResult(
            False,
            "Fjernkjøring er ikke implementert i skallversjon v0.1.0-a1.",
            data={"endpoint": self.endpoint, "operation": operation.definition.operation_id},
        )
