from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Any


ProgressCallback = Callable[[float, str], None]
LogCallback = Callable[[str], None]


@dataclass
class OperationContext:
    extraction_root: Path
    source: Any = None
    settings: dict[str, Any] = field(default_factory=dict)
    progress_cb: ProgressCallback | None = None
    log_cb: LogCallback | None = None
    cancelled_cb: Callable[[], bool] | None = None

    def progress(self, fraction: float, message: str = "") -> None:
        if self.progress_cb:
            self.progress_cb(max(0.0, min(1.0, fraction)), message)

    def log(self, message: str) -> None:
        if self.log_cb:
            self.log_cb(message)

    def cancelled(self) -> bool:
        return bool(self.cancelled_cb and self.cancelled_cb())
