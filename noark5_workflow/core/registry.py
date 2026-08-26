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

    def by_category(self, category: str) -> list[BaseOperation]:
        return [op for op in self._operations.values() if op.definition.category == category]

    def categories(self) -> list[str]:
        seen: list[str] = []
        for operation in self._operations.values():
            category = operation.definition.category
            if category not in seen:
                seen.append(category)
        return seen
