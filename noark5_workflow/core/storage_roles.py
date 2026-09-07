from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class StorageRoles:
    """Generic storage roles. A newly created job may have no Source yet."""
    source_root: Path | None = None
    source_tar: Path | None = None
    source_unzipped: Path | None = None
    source_extraction: Path | None = None
    work_root: Path | None = None
    work_content: Path | None = None
    work_operations: Path | None = None
    archive_root: Path | None = None

    @property
    def active_extraction_root(self) -> Path | None:
        return self.source_extraction or self.source_root
