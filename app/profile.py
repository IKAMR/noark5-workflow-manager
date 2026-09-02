from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from noark5_workflow.core.operation import BaseOperation
from noark5_workflow.core.registry import OperationRegistry


OperationFactory = Callable[[], BaseOperation]


@dataclass(frozen=True)
class WorkflowProfile:
    """Application/domain contribution to the generic workflow runtime."""

    profile_id: str
    name: str
    description: str = ""
    categories: tuple[str, ...] = ()
    category_colors: dict[str, str] = field(default_factory=dict)
    operation_factories: tuple[OperationFactory, ...] = ()

    def build_registry(self) -> OperationRegistry:
        registry = OperationRegistry(
            categories=self.categories,
            category_colors=self.category_colors,
        )
        for factory in self.operation_factories:
            registry.register(factory())
        return registry
