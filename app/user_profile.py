from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

FILE_TYPE = "noark5-workflow-manager-user-profile"
FORMAT_VERSION = 1
_USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class UserProfile:
    user_id: str
    name: str
    username: str
    email: str

    @property
    def is_complete(self) -> bool:
        return bool(self.name.strip() and self.username.strip() and self.email.strip())

    def log_identity(self) -> dict[str, str]:
        """Stable identity fields suitable for future log/job provenance."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "name": self.name,
            "email": self.email,
        }


def user_data_dir() -> Path:
    """Per-user runtime data; deliberately outside the Git repository."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "IKAMR" / "Noark5WorkflowManager"
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "noark5-workflow-manager"
    return Path.home() / ".local" / "share" / "noark5-workflow-manager"


def profile_path() -> Path:
    return user_data_dir() / "user-profile.json"


def validate_profile_fields(name: str, username: str, email: str) -> None:
    name = name.strip()
    username = username.strip()
    email = email.strip()
    if not name:
        raise ValueError("Navn må fylles ut.")
    if not username:
        raise ValueError("Brukernavn må fylles ut.")
    if not _USERNAME_RE.fullmatch(username):
        raise ValueError("Brukernavn kan bare inneholde bokstaver, tall, punktum, bindestrek og understrek.")
    if not email or "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValueError("E-postadressen ser ikke gyldig ut.")


def load_user_profile(path: Path | None = None) -> UserProfile | None:
    path = Path(path) if path is not None else profile_path()
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("file_type") != FILE_TYPE or payload.get("format_version") != FORMAT_VERSION:
        return None
    profile = payload.get("profile")
    if not isinstance(profile, dict):
        return None
    try:
        result = UserProfile(
            user_id=str(profile["user_id"]),
            name=str(profile["name"]),
            username=str(profile["username"]),
            email=str(profile["email"]),
        )
        uuid.UUID(result.user_id)
        validate_profile_fields(result.name, result.username, result.email)
    except (KeyError, TypeError, ValueError):
        return None
    return result


def save_user_profile(
    name: str,
    username: str,
    email: str,
    *,
    path: Path | None = None,
    existing: UserProfile | None = None,
) -> UserProfile:
    validate_profile_fields(name, username, email)
    path = Path(path) if path is not None else profile_path()
    current = existing if existing is not None else load_user_profile(path)
    user_id = current.user_id if current is not None else str(uuid.uuid4())
    result = UserProfile(user_id, name.strip(), username.strip(), email.strip())
    payload = {
        "file_type": FILE_TYPE,
        "format_version": FORMAT_VERSION,
        "profile": asdict(result),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
