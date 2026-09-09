from dataclasses import dataclass, field
from pathlib import Path


KNOWN_METADATA_FILES = {
    "arkivstruktur": "arkivstruktur.xml",
    "arkivuttrekk": "arkivuttrekk.xml",
    "loepende_journal": "loependeJournal.xml",
    "offentlig_journal": "offentligJournal.xml",
    "endringslogg": "endringslogg.xml",
}

DOCUMENT_DIR_NAMES = {
    "dokument",
    "DOKUMENT",
    "dokumenter",
    "DOKUMENTER",
}


@dataclass
class Noark5Extraction:
    root: Path
    metadata_files: dict[str, Path | None] = field(default_factory=dict)
    xsd_files: list[Path] = field(default_factory=list)
    documents_dir: Path | None = None
    business_metadata_files: list[Path] = field(default_factory=list)

    @classmethod
    def detect(cls, root: str | Path) -> "Noark5Extraction":
        root = Path(root).resolve()
        if not root.is_dir():
            raise ValueError(f"Uttrekksroten er ikke en mappe: {root}")

        metadata_by_name = {
            filename.casefold(): key
            for key, filename in KNOWN_METADATA_FILES.items()
        }
        metadata: dict[str, Path | None] = {
            key: None for key in KNOWN_METADATA_FILES
        }
        xsd_files: list[Path] = []
        business: list[Path] = []
        documents_dir: Path | None = None

        # Read the selected root once. Direct document folders are identified here
        # but deliberately not traversed: a Noark document directory can contain
        # very large numbers of files and is not a metadata discovery location.
        try:
            root_entries = list(root.iterdir())
        except OSError as exc:
            raise ValueError(f"Kunne ikke lese uttrekksroten {root}: {exc}") from exc

        child_dirs: list[Path] = []
        for entry in root_entries:
            try:
                if entry.is_dir():
                    if entry.name in DOCUMENT_DIR_NAMES:
                        documents_dir = entry
                    else:
                        child_dirs.append(entry)
            except OSError:
                continue

        # Search root and non-document child directories one level below, exactly
        # once per directory. This preserves the established discovery depth while
        # avoiding repeated O(n) scans for each known metadata filename.
        for base, entries in [(root, root_entries)]:
            cls._collect_entries(
                entries,
                metadata_by_name,
                metadata,
                xsd_files,
                business,
            )

        for base in child_dirs:
            try:
                entries = list(base.iterdir())
            except OSError:
                continue

            for entry in entries:
                try:
                    if entry.is_dir() and entry.name in DOCUMENT_DIR_NAMES:
                        if documents_dir is None:
                            documents_dir = entry
                except OSError:
                    continue

            cls._collect_entries(
                entries,
                metadata_by_name,
                metadata,
                xsd_files,
                business,
            )

        return cls(
            root=root,
            metadata_files=metadata,
            xsd_files=sorted(set(xsd_files)),
            documents_dir=documents_dir,
            business_metadata_files=sorted(set(business)),
        )

    @staticmethod
    def _collect_entries(
        entries: list[Path],
        metadata_by_name: dict[str, str],
        metadata: dict[str, Path | None],
        xsd_files: list[Path],
        business: list[Path],
    ) -> None:
        for entry in entries:
            try:
                if not entry.is_file():
                    continue
            except OSError:
                continue

            folded = entry.name.casefold()
            metadata_key = metadata_by_name.get(folded)
            if metadata_key is not None and metadata[metadata_key] is None:
                metadata[metadata_key] = entry

            if entry.suffix.casefold() == ".xsd":
                xsd_files.append(entry)

            if (
                entry.suffix.casefold() == ".xml"
                and "virksomhetsspes" in folded
            ):
                business.append(entry)

    @property
    def is_noark5_candidate(self) -> bool:
        return self.metadata_files.get("arkivstruktur") is not None

    def inventory(self) -> dict:
        return {
            "root": str(self.root),
            "is_noark5_candidate": self.is_noark5_candidate,
            "metadata_files": {
                key: str(value) if value else None
                for key, value in self.metadata_files.items()
            },
            "xsd_count": len(self.xsd_files),
            "documents_dir": str(self.documents_dir) if self.documents_dir else None,
            "business_metadata_files": [str(p) for p in self.business_metadata_files],
        }
