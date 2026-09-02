from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class WorkflowSource(Protocol):
    """Minimal source contract understood by generic workflow infrastructure."""

    @property
    def root(self) -> Path:
        ...


def source_root(source: Any, fallback: Path) -> Path:
    """Return the source root without knowing the concrete source type."""
    root = getattr(source, "root", None)
    return Path(root if root is not None else fallback)
