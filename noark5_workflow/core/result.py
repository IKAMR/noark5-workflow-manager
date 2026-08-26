from dataclasses import dataclass, field
from typing import Any


@dataclass
class OperationResult:
    ok: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
