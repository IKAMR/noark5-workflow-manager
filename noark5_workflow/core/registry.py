from .operation import BaseOperation


class OperationRegistry:
    def __init__(self) -> None:
        self._operations: dict[str, BaseOperation] = {}

    def register(self, operation: BaseOperation) -> None:
        op_id = operation.definition.operation_id
        if op_id in self._operations:
            raise ValueError(f"Operasjonen er allerede registrert: {op_id}")
        self._operations[op_id] = operation

    def get(self, operation_id: str) -> BaseOperation:
        return self._operations[operation_id]

    def all(self) -> list[BaseOperation]:
        return list(self._operations.values())
