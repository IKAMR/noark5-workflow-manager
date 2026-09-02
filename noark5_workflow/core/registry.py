from __future__ import annotations

from collections.abc import Iterable, Mapping

from .operation import BaseOperation


class OperationRegistry:
    def __init__(
        self,
        categories: Iterable[str] = (),
        category_colors: Mapping[str, str] | None = None,
    ) -> None:
        self._operations: dict[str, BaseOperation] = {}
        self._categories: list[str] = []
        self._category_colors: dict[str, str] = dict(category_colors or {})
        for category in categories:
            self.register_category(category)

    def register_category(self, category: str, color: str | None = None) -> None:
        category = str(category).strip()
        if not category:
            return
        if category not in self._categories:
            self._categories.append(category)
        if color:
            self._category_colors[category] = str(color)

    def register(self, operation: BaseOperation) -> None:
        op_id = operation.definition.operation_id
        if op_id in self._operations:
            raise ValueError(f"Operasjonen er allerede registrert: {op_id}")
        self._operations[op_id] = operation
        self.register_category(operation.definition.category)

    def get(self, operation_id: str) -> BaseOperation:
        return self._operations[operation_id]

    def all(self) -> list[BaseOperation]:
        return list(self._operations.values())

    def by_category(self, category: str) -> list[BaseOperation]:
        return [op for op in self._operations.values() if op.definition.category == category]

    def categories(self) -> list[str]:
        return list(self._categories)

    def category_color(self, category: str, default: str = "") -> str:
        return self._category_colors.get(category, default)
