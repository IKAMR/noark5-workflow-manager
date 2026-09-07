from __future__ import annotations


class Workflow:
    """Ordered collection of operation IDs."""

    def __init__(self) -> None:
        self._operation_ids: list[str] = []

    def add(self, operation_id: str) -> bool:
        if operation_id in self._operation_ids:
            return False
        self._operation_ids.append(operation_id)
        return True

    def remove(self, operation_id: str) -> bool:
        try:
            self._operation_ids.remove(operation_id)
            return True
        except ValueError:
            return False

    def move_up(self, operation_id: str) -> bool:
        try:
            index = self._operation_ids.index(operation_id)
        except ValueError:
            return False
        if index == 0:
            return False
        self._operation_ids[index - 1], self._operation_ids[index] = (
            self._operation_ids[index],
            self._operation_ids[index - 1],
        )
        return True

    def move_down(self, operation_id: str) -> bool:
        try:
            index = self._operation_ids.index(operation_id)
        except ValueError:
            return False
        if index >= len(self._operation_ids) - 1:
            return False
        self._operation_ids[index], self._operation_ids[index + 1] = (
            self._operation_ids[index + 1],
            self._operation_ids[index],
        )
        return True

    def clear(self) -> None:
        self._operation_ids.clear()

    def operation_ids(self) -> list[str]:
        return list(self._operation_ids)

    def __len__(self) -> int:
        return len(self._operation_ids)
