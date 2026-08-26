from __future__ import annotations


class Workflow:
    """Ordered collection of operation IDs used by the GUI and future profiles/jobs."""

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

    def clear(self) -> None:
        self._operation_ids.clear()

    def operation_ids(self) -> list[str]:
        return list(self._operation_ids)

    def __len__(self) -> int:
        return len(self._operation_ids)
