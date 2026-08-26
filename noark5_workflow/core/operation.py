from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from .context import OperationContext
from .result import OperationResult


class ExecutionTarget(str, Enum):
    LOCAL = "local"
    SERVER = "server"
    EITHER = "either"


@dataclass(frozen=True)
class OperationDefinition:
    operation_id: str
    name: str
    description: str
    execution_target: ExecutionTarget = ExecutionTarget.EITHER


class BaseOperation(ABC):
    definition: OperationDefinition

    def can_run(self, ctx: OperationContext) -> tuple[bool, str]:
        return True, ""

    @abstractmethod
    def run(self, ctx: OperationContext) -> OperationResult:
        raise NotImplementedError
