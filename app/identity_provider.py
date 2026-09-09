from __future__ import annotations

from typing import Protocol

from noark5_workflow.core.identity import UserIdentity
from app.user_profile import UserProfile, load_user_profile


class IdentityProvider(Protocol):
    """Source of the authenticated/registered runtime identity."""

    def current_identity(self) -> UserIdentity | None:
        ...


class LocalUserProfileIdentityProvider:
    """Desktop provider backed by the current per-user local profile.

    A future server provider can implement the same contract using its own
    authentication/user registry without changing Job, JobRunner or log sinks.
    """

    def __init__(self) -> None:
        self._profile: UserProfile | None = load_user_profile()

    @property
    def profile(self) -> UserProfile | None:
        return self._profile

    def set_profile(self, profile: UserProfile | None) -> None:
        self._profile = profile

    def current_identity(self) -> UserIdentity | None:
        profile = self._profile
        if profile is None:
            return None
        return UserIdentity(
            user_id=profile.user_id,
            username=profile.username,
            name=profile.name,
            email=profile.email,
        )
