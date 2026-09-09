from __future__ import annotations

from app.user_profile import UserProfile
from app.identity_provider import LocalUserProfileIdentityProvider
from noark5_workflow.sources.noark5_extraction import Noark5Extraction
from .persistent_app_a17 import WorkflowApp as A17WorkflowApp
from .setup_dialog_a18 import SetupDialog
from .user_profile_dialog import UserProfileDialog


class WorkflowApp(A17WorkflowApp):
    def __init__(self) -> None:
        self.identity_provider = LocalUserProfileIdentityProvider()
        self.user_profile: UserProfile | None = self.identity_provider.profile
        self._user_profile_dialog = None
        self._last_source_log_key: str | None = None
        self._job_context_switch = False
        super().__init__()
        self._apply_user_identity_runtime()
        self.bind_all("<ButtonPress>", self._hide_workflow_tooltips, add="+")
        if self.user_profile is None:
            self.after_idle(lambda: self._open_user_profile(required=True))

    @property
    def current_user_id(self) -> str | None:
        return self.user_profile.user_id if self.user_profile else None

    def current_user_identity(self) -> dict[str, str] | None:
        identity = self.identity_provider.current_identity()
        return identity.as_dict() if identity is not None else None

    def _apply_user_identity_runtime(self) -> None:
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
        key = str(root).replace("\\", "/").rstrip("/").casefold()
        if key == self._last_source_log_key:
            return False
        self._last_source_log_key = key
        return True

    def _source_changed(self, extraction: Noark5Extraction | None) -> None:
        self.extraction = extraction
        if self._job_context_switch:
            return
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
            try:
                if not self.source_panel.path_var.get().strip():
                    self._last_source_log_key = None
            except Exception:
                pass
            self.status_bar.set_status("Klar")

    def _load_job_list_file(self, path, *, show_error: bool) -> bool:
        self._job_context_switch = True
        try:
            self.source_panel.path_var.set("")
            self.source_panel.extraction = None
            self.extraction = None
            self._last_source_log_key = None
            loaded = super()._load_job_list_file(path, show_error=show_error)
            if not loaded:
                return False
            active_source = (
                self.current_job.active_extraction_root
                if self.current_job is not None
                else None
            )
            self.source_panel.path_var.set(
                str(active_source) if active_source is not None else ""
            )
            self.source_panel.extraction = None
            self.extraction = None
        finally:
            self._job_context_switch = False
        self.source_panel.detect()

        # The custom job-list chooser is asynchronous. JobsWindow._open_list()
        # cannot refresh based on the immediate return value, so refresh an
        # already open Jobs window explicitly after the new list is active.
        jobs_window = getattr(self, "jobs_window", None)
        if jobs_window is not None:
            try:
                if jobs_window.winfo_exists():
                    jobs_window.refresh()
            except Exception:
                pass
        return True

    def _open_job(self, job) -> None:
        already_guarded = self._job_context_switch
        if not already_guarded:
            self._job_context_switch = True
            self.source_panel.path_var.set("")
            self.source_panel.extraction = None
        try:
            super()._open_job(job)
        finally:
            if not already_guarded:
                self._job_context_switch = False
        if not already_guarded:
            active_source = job.active_extraction_root
            self.source_panel.path_var.set(
                str(active_source) if active_source is not None else ""
            )
            self.source_panel.extraction = None
            self.extraction = None
            self.source_panel.detect()

    def _create_job(self, source_root=None):
        job = super()._create_job(source_root)
        job.set_owner_identity(self.current_user_identity())
        return job

    def _new_job_list(self) -> bool:
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
                    existing.focus()
                    existing.lift()
                    return
            except Exception:
                pass
        dialog = UserProfileDialog(self, self.user_profile, self._user_profile_saved, required=required)
        self._user_profile_dialog = dialog
        dialog.bind("<Destroy>", lambda event, d=dialog: self._user_profile_closed(event, d), add="+")

    def _user_profile_saved(self, profile: UserProfile) -> None:
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
