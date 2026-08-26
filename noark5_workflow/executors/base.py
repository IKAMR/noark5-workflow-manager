from abc import ABC, abstractmethod

from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.operation import BaseOperation
from noark5_workflow.core.result import OperationResult


class BaseExecutor(ABC):
    """Execution backend boundary.

    The GUI/workflow layer submits operations through this interface. A future
    server executor can implement the same contract without changing operation
    panels or Noark-specific analysis code.
    """

    backend_id = "base"

    @abstractmethod
    def execute(self, operation: BaseOperation, ctx: OperationContext) -> OperationResult:
        raise NotImplementedError
