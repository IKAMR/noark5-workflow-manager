from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class UserIdentity:
    """Transport-neutral user identity used by GUI, CLI and future server runtimes.

    Authentication and storage belong to an IdentityProvider. Core code only
    receives this stable identity snapshot.
    """

    user_id: str
    username: str
    name: str
    email: str

    @classmethod
    def from_mapping(cls, value: Mapping | None) -> "UserIdentity | None":
        if not value:
            return None
        user_id = str(value.get("user_id", "") or "").strip()
        username = str(value.get("username", "") or "").strip()
        name = str(value.get("name", "") or "").strip()
        email = str(value.get("email", "") or "").strip()
        if not user_id:
            return None
        return cls(user_id=user_id, username=username, name=name, email=email)

    def as_dict(self) -> dict[str, str]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "name": self.name,
            "email": self.email,
        }

    def identifier(self, strategy: str = "username") -> str:
        """Return the configured external identifier without changing identity."""
        if strategy == "user_id":
            return self.user_id
        return self.username
