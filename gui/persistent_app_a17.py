from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from version import APP_NAME
from settings import save_config
from noark5_workflow.core.job import JobStatus
from .persistent_app_a13 import WorkflowApp as A13WorkflowApp
from . import theme
from .window_placement import install_child_window_placement
from .workflow_change_hooks import install_workflow_change_hooks
from .ui_contract_a17 import HEADER_ACTIONS
from .setup_dialog_a17 import SetupDialog
from .result_history_dialog import RawResultsDialog


from .jobs_window_a17 import A17JobsWindow

class WorkflowApp(A13WorkflowApp):


    def _new_job_list(self) -> bool:
        if self.batch_running:
            return False
        if len(self.jobs) and not messagebox.askyesno(
            APP_NAME,
            "Opprette en ny tom jobbliste?\n\n"
            "Gjeldende jobbliste blir ikke lagret automatisk, og visningsloggen tømmes.\n\n"
            "Persistente kjørelogger, råresultater og PREMIS-filer på disk slettes ikke.",
        ):
            return False

        self.current_job = None
        # JobBatch.clear() is the identity-boundary reset: next new job = JOB-001.
        self.jobs.clear()
        self.workflow.clear()
        self.workflow_panel.refresh()
        self.source_panel.path_var.set("")
        self.source_panel.detect()
        self.log_panel.clear()
        self.job_list_path = None
        self._refresh_job_list_status()
        self._refresh_active_job_label()
        self._update_run_button()

        self.settings["last_job_list_file"] = ""
        save_config({"last_job_list_file": ""})
        self.status_bar.set_status("Ny tom jobbliste – neste jobb blir JOB-001")
        return True


    def _open_jobs(self) -> None:
        self._capture_job_operation_params(self.current_job)
        if self.jobs_window is not None and self.jobs_window.winfo_exists():
            self.jobs_window.focus()
            self.jobs_window.lift()
            self.jobs_window.refresh()
            return
        self.jobs_window = A17JobsWindow(
            self, self.jobs, self._open_job, self._create_job, self._start_all_jobs,
            self._stop_batch, self._new_job_list, self._open_job_list_dialog,
            self._save_job_list, self._save_job_list_as, lambda: self.job_list_path,
            lambda: self.current_job.job_id if self.current_job else None,
        )
    """a17 runtime layer: read-only visibility of append-only raw results."""

    def __init__(self) -> None:
        self._raw_results_dialog = None
        self._joblist_save_as_active = False
        self._joblist_explicit_write = False
        self._workflow_autosave_pending = False
        super().__init__()
        self._refresh_job_list_status()
        install_child_window_placement(self)
        install_workflow_change_hooks(self.workflow_panel, self._workflow_changed)
        self._normalize_header_layout()
        self.after_idle(self._normalize_header_layout)
        # Keep the established a13 header unchanged. The Resultater action belongs
        # with the run log and is exposed through LogPanel's optional auxiliary slot.
        self.log_panel.set_aux_action("Resultater", self._show_raw_results)
        self.protocol("WM_DELETE_WINDOW", self._close_with_persistence)


    def _refresh_job_list_status(self) -> None:
        self.status_bar.set_job_list(self.job_list_path)

    def _load_job_list_file(self, path: Path, *, show_error: bool) -> bool:
        loaded = super()._load_job_list_file(path, show_error=show_error)
        if loaded:
            self._refresh_job_list_status()
        return loaded

    def _save_job_list_as(self) -> bool:
        """Start one explicit Save As transaction.

        While the chooser/file-name flow is active, background/automatic
        persistence is not allowed to write the previous job-list path.
        Exactly one explicit target is written after the user confirms a
        filename.
        """
        if self.batch_running or self._joblist_save_as_active:
            return False
        self._joblist_save_as_active = True
        try:
            self._choose_job_list_location(save=True)
        except Exception:
            self._joblist_save_as_active = False
            raise
        # The custom location dialog is asynchronous; the flag is cleared by
        # _save_job_list_as_in when the user completes/cancels filename choice.
        return False

    def _save_job_list_as_in(self, directory: Path) -> bool:
        try:
            filename = filedialog.asksaveasfilename(
                title="Lagre jobbliste som",
                initialdir=str(directory),
                defaultextension=".n5jobs",
                filetypes=[("Workflow-jobbliste", "*.n5jobs"), ("Alle filer", "*.*")],
            )
            if not filename:
                return False
            target = Path(filename)
            old_path = self.job_list_path
            self._joblist_explicit_write = True
            try:
                written = self._write_job_list(target)
            finally:
                self._joblist_explicit_write = False
            if written and (old_path is None or target != old_path):
                self.log_panel.clear()
                self.status_bar.set_status("Ny jobbliste lagret – visningsloggen er nullstilt")
            return written
        finally:
            self._joblist_save_as_active = False

    def _write_job_list(self, path: Path) -> bool:
        # Guard against an implicit autosave to the previous master while a
        # Save As transaction is waiting for directory/filename confirmation.
        if self._joblist_save_as_active and not self._joblist_explicit_write:
            self.status_bar.set_status("Automatisk jobblistelagring utsatt mens Lagre som pågår")
            return False
        written = super()._write_job_list(path)
        if written:
            self._refresh_job_list_status()
        return written

    def _normalize_header_layout(self) -> None:
        """Build one compact, deterministic action strip in the header.

        Mapper | Jobber | Setup | A- | A+ | ?

        Do not keep relocating inherited buttons one by one. All inherited
        action buttons are hidden and one dedicated action frame owns the final
        a17 header controls. This avoids column collisions between runtime layers.
        """
        header = self.active_job_label.master
        header.grid_columnconfigure(3, weight=1)

        # Hide inherited action buttons from earlier runtime layers.
        action_labels = set(HEADER_ACTIONS) | {"Endre temp-mappe", "Innstillinger"}
        for child in header.winfo_children():
            if isinstance(child, ctk.CTkButton):
                try:
                    label = str(child.cget("text"))
                except Exception:
                    continue
                if label in action_labels:
                    child.grid_forget()

        existing = getattr(self, "_a17_header_actions", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.destroy()
            except Exception:
                pass

        actions = ctk.CTkFrame(header, fg_color=theme.APP_BG, corner_radius=0)
        self._a17_header_actions = actions
        actions.grid(row=0, column=4, padx=(4, 10), pady=0, sticky="e")

        specs = (
            ("Mapper", 72, theme.BUTTON_BG, theme.BUTTON_HOVER, self._edit_storage_roles),
            ("Jobber", 78, theme.BLUE_DIM, theme.BLUE, self._open_jobs),
            ("Setup", 76, theme.BUTTON_BG, theme.BUTTON_HOVER, self._open_settings),
            ("A-", 34, theme.BUTTON_BG, theme.BUTTON_HOVER, lambda: self._font_scale(-1)),
            ("A+", 34, theme.BUTTON_BG, theme.BUTTON_HOVER, lambda: self._font_scale(+1)),
        )
        implemented_actions = tuple(item[0] for item in specs) + ("?",)
        if implemented_actions != HEADER_ACTIONS:
            raise RuntimeError(
                f"Header-kontrakt avviker: {implemented_actions!r} != {HEADER_ACTIONS!r}"
            )

        for text, width, fg, hover, command in specs:
            ctk.CTkButton(
                actions, text=text, width=width, height=28,
                font=theme.font(theme.SMALL_SIZE),
                fg_color=fg, hover_color=hover, command=command,
            ).pack(side="left", padx=2, pady=8)

        ctk.CTkButton(
            actions, text="?", width=34, height=28, state="disabled",
            font=theme.font(theme.SMALL_SIZE), fg_color=theme.BUTTON_BG,
        ).pack(side="left", padx=2, pady=8)

        # One action-frame column only; old action columns must not compete for width.
        for column in range(4, 11):
            header.grid_columnconfigure(column, weight=0)

    def _open_settings(self) -> None:
        SetupDialog(self, self.settings, self._save_settings)

    def _profile_selected(self, label: str) -> None:
        """Ignore an idempotent profile selection.

        Selecting the profile that is already active for the current job is
        not a configuration change and must not trigger detection, logging or
        persistence side effects.
        """
        profile_id = self.PROFILE_LABELS.get(label)
        current_profile = self.current_job.profile_id if self.current_job is not None else self.active_profile_id
        if profile_id == current_profile:
            return
        super()._profile_selected(label)

    def _sync_active_workflow_to_job(self) -> None:
        """Make the visible workflow authoritative on the active Job immediately."""
        job = self.current_job
        if job is None:
            return
        job.set_workflow(self.workflow.operation_ids())

    def _persist_active_job_state(self, *, status_text: str | None = None) -> bool:
        """Synchronize the active GUI state and persist the current job list.

        This is the common persistence boundary used by workflow edits, job
        switches and application close. It deliberately does not depend on
        after_idle timing.
        """
        self._sync_active_workflow_to_job()
        if self.job_list_path is None:
            if status_text:
                self.status_bar.set_status(status_text)
            return False
        written = self._write_job_list(self.job_list_path)
        if written and status_text:
            self.status_bar.set_status(status_text)
        return written

    def _workflow_changed(self, change_kind: str, operation_id: str | None) -> None:
        """Persist add/remove/clear immediately for the active workflow."""
        job = self.current_job
        if job is None or self.batch_running:
            return

        self._sync_active_workflow_to_job()
        self._refresh_active_job_label()

        if job.status in {JobStatus.OK, JobStatus.FAILED, JobStatus.SKIPPED, JobStatus.WAITING}:
            job.reset_execution("Workflow endret - klar for ny kjøring")

        if self.job_list_path is None:
            self.status_bar.set_status("Workflow endret – jobblista er ikke lagret ennå")
            return

        # Immediate write is intentional. A previous after_idle implementation
        # could lose edits if the user switched jobs or closed the app before the
        # deferred callback ran. Configurable operations may write once more after
        # their parameters are committed; correctness is preferred over avoiding
        # that small extra write.
        self._persist_active_job_state(status_text="Workflow lagret automatisk")

    def _open_job(self, job) -> None:
        """Treat job switch as an explicit persistence boundary."""
        leaving = self.current_job
        if leaving is not None and leaving is not job and self.job_list_path is not None:
            self._persist_active_job_state()

        super()._open_job(job)

        # Persist the newly active job id as well, so restart returns to the same
        # job the user selected.
        if self.current_job is job and self.job_list_path is not None:
            self._persist_active_job_state()

    def _close_with_persistence(self) -> None:
        """Persist current workflow before the root window is destroyed."""
        if self.job_list_path is not None and not self.batch_running:
            self._persist_active_job_state()
        self.destroy()

    def _show_raw_results(self) -> None:
        job = self.current_job
        if job is None:
            messagebox.showinfo(APP_NAME, "Ingen aktiv jobb.")
            return
        existing = self._raw_results_dialog
        if existing is not None and existing.winfo_exists():
            existing.focus()
            existing.lift()
            existing.refresh()
            return
        dialog = RawResultsDialog(self, job)
        self._raw_results_dialog = dialog
        dialog.bind(
            "<Destroy>",
            lambda _event, d=dialog: self._raw_results_dialog_closed(d),
            add="+",
        )

    def _raw_results_dialog_closed(self, dialog) -> None:
        if self._raw_results_dialog is dialog:
            self._raw_results_dialog = None


def run_gui() -> None:
    app = WorkflowApp()
    app.mainloop()
