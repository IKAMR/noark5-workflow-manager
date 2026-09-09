from __future__ import annotations

from app.user_profile import UserProfile
from app.identity_provider import LocalUserProfileIdentityProvider
from noark5_workflow.sources.noark5_extraction import Noark5Extraction
from .persistent_app_a17 import WorkflowApp as A17WorkflowApp
from .setup_dialog_a18 import SetupDialog
from .user_profile_dialog import UserProfileDialog


class WorkflowApp(A17WorkflowApp):
    """a18 runtime layer: stable local user identity and provenance-ready context."""

    def __init__(self) -> None:
        self.identity_provider = LocalUserProfileIdentityProvider()
        self.user_profile: UserProfile | None = self.identity_provider.profile
        self._user_profile_dialog = None
        self._last_source_log_key: str | None = None
        super().__init__()
        self._apply_user_identity_runtime()
        # Tooltips are transient UI only. Hide them on any click so an
        # overrideredirect/topmost tooltip cannot become an orphan window when
        # dialogs open or the workflow UI changes.
        self.bind_all("<ButtonPress>", self._hide_workflow_tooltips, add="+")
        if self.user_profile is None:
            self.after_idle(lambda: self._open_user_profile(required=True))

    @property
    def current_user_id(self) -> str | None:
        return self.user_profile.user_id if self.user_profile else None

    def current_user_identity(self) -> dict[str, str] | None:
        """Stable identity contract for job/log/PREMIS/server integrations."""
        identity = self.identity_provider.current_identity()
        return identity.as_dict() if identity is not None else None

    def _apply_user_identity_runtime(self) -> None:
        """Attach identity to runtime settings without persisting personal data in setup.

        JobRunner passes the settings mapping into OperationContext, so this private
        runtime key makes user identity available to generic execution/log layers.
        It is deliberately not part of DEFAULT_CONFIG and is stripped before setup
        is saved/exported.
        """
        identity = self.current_user_identity()
        if identity:
            self.settings["_current_user_identity"] = dict(identity)
            self.status_bar.set_user(identity.get("username"))
        else:
            self.settings.pop("_current_user_identity", None)
            self.status_bar.set_user(None)
        runner = getattr(self, "job_runner", None)
        if runner is not None:
            runner.settings = self.settings

    def _source_log_changed(self, root) -> bool:
        """Return True only when the effective source really changed."""
        key = str(root).replace("\\", "/").rstrip("/").casefold()
        if key == self._last_source_log_key:
            return False
        self._last_source_log_key = key
        return True

    def _source_changed(self, extraction: Noark5Extraction | None) -> None:
        """Preserve established source handling without duplicate GUI log entries.

        Source detection and storage-role dialogs may report the same effective
        extraction several times. Only a real source value change belongs in the
        visible run history.
        """
        self.extraction = extraction
        if extraction:
            changed = self._source_log_changed(extraction.root)
            self._ensure_job_for_current_source()
            detection = "Noark 5" if extraction.is_noark5_candidate else "ukjent"
            self.status_bar.update_storage(extraction.root, detection=detection)
            if extraction.is_noark5_candidate:
                self.status_bar.set_status("Noark 5-uttrekk funnet")
                if changed:
                    self.log_panel.append(f"Uttrekk valgt: {extraction.root}")
            else:
                self.status_bar.set_status("arkivstruktur.xml ble ikke funnet")
        else:
            # Reset only when the source field is actually cleared. A transient
            # re-detection must not make the same path appear as a new selection.
            try:
                if not self.source_panel.path_var.get().strip():
                    self._last_source_log_key = None
            except Exception:
                pass
            self.status_bar.set_status("Klar")

    def _create_job(self, source_root=None):
        """Create a new job owned by the currently registered user."""
        job = super()._create_job(source_root)
        job.set_owner_identity(self.current_user_identity())
        return job

    def _new_job_list(self) -> bool:
        """Reset the list and immediately create the first blank JOB-001.

        A new job list is a new job-identity context. The GUI should therefore
        never leave the user in an extra "no active job" step before they can
        select profile, source and workflow.
        """
        if not super()._new_job_list():
            return False

        job = self.jobs.new_job(None)
        job.set_owner_identity(self.current_user_identity())
        self.current_job = job

        self.workflow.clear()
        self.workflow_panel.refresh()
        self.source_panel.path_var.set("")
        self.source_panel.detect()
        self._refresh_active_job_label()
        self._update_run_button()
        self.status_bar.set_status("Ny jobbliste – JOB-001 opprettet")
        return True

    def _hide_workflow_tooltips(self, _event=None) -> None:
        """Close any workflow tooltip before dialogs/actions continue."""
        panel = getattr(self, "workflow_panel", None)
        for tooltip in list(getattr(panel, "_tooltips", ())):
            try:
                tooltip._hide()
            except Exception:
                pass

    def _open_settings(self) -> None:
        self._hide_workflow_tooltips()
        SetupDialog(self, self.settings, self._save_settings, self._open_user_profile)

    def _save_settings(self, settings: dict) -> None:
        clean = dict(settings)
        clean.pop("_current_user_identity", None)
        super()._save_settings(clean)
        self._apply_user_identity_runtime()

    def _open_user_profile(self, required: bool = False) -> None:
        existing = self._user_profile_dialog
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.focus(); existing.lift(); return
            except Exception:
                pass
        dialog = UserProfileDialog(self, self.user_profile, self._user_profile_saved, required=required)
        self._user_profile_dialog = dialog
        dialog.bind("<Destroy>", lambda event, d=dialog: self._user_profile_closed(event, d), add="+")

    def _user_profile_saved(self, profile: UserProfile) -> None:
        # save_user_profile preserves the existing UUID user_id; editable profile
        # fields describe the same registered identity rather than creating a new one.
        self.user_profile = profile
        self.identity_provider.set_profile(profile)
        self._apply_user_identity_runtime()
        self.status_bar.set_status(f"Brukerprofil lagret: {profile.username}")

    def _user_profile_closed(self, event, dialog) -> None:
        if event.widget is dialog and self._user_profile_dialog is dialog:
            self._user_profile_dialog = None


def run_gui() -> None:
    app = WorkflowApp()
    app.mainloop()
