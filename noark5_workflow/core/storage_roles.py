from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StorageRoles:
    """Generic storage roles used by a workflow job.

    Physical folder names are deliberately not prescribed here. Profiles/setup
    may map these roles to DIAS or depot-specific structures.
    """

    source_root: Path
    source_tar: Path | None = None
    source_unzipped: Path | None = None
    source_extraction: Path | None = None
    work_root: Path | None = None
    work_content: Path | None = None
    work_operations: Path | None = None
    archive_root: Path | None = None

    @property
    def active_extraction_root(self) -> Path:
        return self.source_extraction or self.source_root
