from dataclasses import dataclass, field
from pathlib import Path


KNOWN_METADATA_FILES = {
    "arkivstruktur": "arkivstruktur.xml",
    "arkivuttrekk": "arkivuttrekk.xml",
    "loepende_journal": "loependeJournal.xml",
    "offentlig_journal": "offentligJournal.xml",
    "endringslogg": "endringslogg.xml",
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

        # The shell searches the selected extraction root and one level below.
        # Deeper/package-aware discovery can be added as a dedicated operation.
        candidates = [root] + [p for p in root.iterdir() if p.is_dir()]

        def find_named(name: str) -> Path | None:
            lname = name.lower()
            for base in candidates:
                for p in base.iterdir():
                    if p.is_file() and p.name.lower() == lname:
                        return p
            return None

        metadata = {key: find_named(filename) for key, filename in KNOWN_METADATA_FILES.items()}

        xsd_files: list[Path] = []
        business: list[Path] = []
        documents_dir: Path | None = None

        for base in candidates:
            for p in base.iterdir():
                if p.is_file() and p.suffix.lower() == ".xsd":
                    xsd_files.append(p)
                if p.is_file() and "virksomhetsspes" in p.name.lower() and p.suffix.lower() == ".xml":
                    business.append(p)
                if p.is_dir() and p.name.lower() == "dokumenter":
                    documents_dir = p

        return cls(
            root=root,
            metadata_files=metadata,
            xsd_files=sorted(set(xsd_files)),
            documents_dir=documents_dir,
            business_metadata_files=sorted(set(business)),
        )

    @property
    def is_noark5_candidate(self) -> bool:
        return self.metadata_files.get("arkivstruktur") is not None

    def inventory(self) -> dict:
        return {
            "root": str(self.root),
            "is_noark5_candidate": self.is_noark5_candidate,
            "metadata_files": {
                key: str(value) if value else None for key, value in self.metadata_files.items()
            },
            "xsd_count": len(self.xsd_files),
            "documents_dir": str(self.documents_dir) if self.documents_dir else None,
            "business_metadata_files": [str(p) for p in self.business_metadata_files],
        }
