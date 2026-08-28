from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path


class OutputLockedError(RuntimeError):
    pass


class OutputLock:
    """Small cross-process lock stored in the selected output directory.

    The lock prevents two app instances/jobs from writing to the same output
    directory at the same time. A lock left behind after a crash is deliberately
    not removed automatically; that requires an explicit human check.
    """

    FILENAME = ".noark5-workflow-manager.lock"

    def __init__(self, output_root: Path, job_id: str) -> None:
        self.output_root = Path(output_root)
        self.job_id = job_id
        self.path = self.output_root / self.FILENAME
        self._acquired = False

    def acquire(self) -> None:
        self.output_root.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({
            "job_id": self.job_id,
            "pid": os.getpid(),
            "created": datetime.now().astimezone().isoformat(timespec="seconds"),
        }, ensure_ascii=False, indent=2)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(self.path), flags)
        except FileExistsError as exc:
            detail = ""
            try:
                detail = self.path.read_text(encoding="utf-8").strip()
            except OSError:
                pass
            suffix = f" Innhold: {detail}" if detail else ""
            raise OutputLockedError(
                f"Utdataområdet er låst av en annen jobb/appinstans: {self.output_root}.{suffix}"
            ) from exc
        try:
            os.write(fd, payload.encode("utf-8"))
        finally:
            os.close(fd)
        self._acquired = True

    def release(self) -> None:
        if not self._acquired:
            return
        try:
            self.path.unlink(missing_ok=True)
        finally:
            self._acquired = False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False
