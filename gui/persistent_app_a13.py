from __future__ import annotations

import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog, messagebox

from app.workspace import job_list_dir
from settings import save_config

from noark5_workflow.core.job import Job, JobStatus
from noark5_workflow.core.project_config import (
    FILE_NAME as PROJECT_FILE_NAME,
    ProjectConfigError,
    is_project_job_list_path,
    load_project,
    project_dir,
    save_project,
)
from version import APP_NAME
from . import theme
from .persistent_app import _TERMINAL_STATUSES
from .persistent_app_a6 import WorkflowApp as A6WorkflowApp
from .storage_roles_dialog import StorageRolesDialog
from .job_list_location_dialog import JobListLocationDialog
from .jobs_window_a15 import A15JobsWindow

class WorkflowApp(A6WorkflowApp):
    """Storage roles plus a15 profile/source boundary fixes."""

    PROFILE_LABELS={"-- profil --":None,"Noark 5":"noark5","SIARD":"siard"}

    def __init__(self) -> None:
        self.active_profile_id=None
        self._storage_roles_dialog=None
        super().__init__()
        self.source_panel.on_browse_complete=self._source_browse_complete
        self.workflow_panel.on_reorder=self._workflow_reordered
        # super().__init__ may already have restored the last job list and active job.
        # Do not overwrite that job's persisted profile with the blank/default profile.
        if self.current_job is not None:
            self._apply_profile(self.current_job.profile_id, persist=False)
        else:
            self._apply_profile(None, persist=False)

    def _build_header(self) -> None:
        super()._build_header()
        header=self.active_job_label.master
        self.profile_menu=None
        for child in header.winfo_children():
            if isinstance(child, ctk.CTkOptionMenu):
                info=child.grid_info()
                if info and int(info.get("column",0))==1:
                    self.profile_menu=child
                    child.configure(values=list(self.PROFILE_LABELS),command=self._profile_selected)
                    child.set("-- profil --")
                    break
        # Make room without replacing the established header.
        for child in header.winfo_children():
            info=child.grid_info()
            if info and int(info.get("column",0)) >= 4:
                child.grid_configure(column=int(info["column"])+1)
        self.storage_button=ctk.CTkButton(header,text="Mapper",width=72,height=28,font=theme.font(theme.SMALL_SIZE),fg_color=theme.BUTTON_BG,hover_color=theme.BUTTON_HOVER,command=self._edit_storage_roles)
        self.storage_button.grid(row=0,column=4,padx=(4,2),pady=8)


    def _open_jobs(self) -> None:
        self._capture_job_operation_params(self.current_job)
        if self.jobs_window is not None and self.jobs_window.winfo_exists():
            self.jobs_window.focus(); self.jobs_window.refresh(); return
        self.jobs_window = A15JobsWindow(
            self, self.jobs, self._open_job, self._create_job, self._start_all_jobs,
            self._stop_batch, self._new_job_list, self._open_job_list_dialog,
            self._save_job_list, self._save_job_list_as, lambda: self.job_list_path,
            lambda: self.current_job.job_id if self.current_job else None,
        )

    def _create_job(self, source_root=None) -> Job:
        # Explicit Ny jobb creates a blank generic job. Source is a storage role,
        # not the identity required to create the job.
        job = self.jobs.new_job(None)
        self.current_job = job
        self.workflow.clear(); self.workflow_panel.refresh()
        self.source_panel.path_var.set(""); self.source_panel.detect()
        self._refresh_active_job_label(); self._update_run_button()
        self.after(0, lambda j=job: self._show_storage_roles(j))
        return job

    def _show_storage_roles(self, job: Job) -> None:
        existing = self._storage_roles_dialog
        if existing is not None and existing.winfo_exists():
            existing.focus(); existing.lift(); return
        dialog = StorageRolesDialog(self, job, lambda values: self._save_storage_roles(job, values))
        self._storage_roles_dialog = dialog
        dialog.bind("<Destroy>", lambda _e, d=dialog: self._storage_dialog_closed(d), add="+")

    def _storage_dialog_closed(self, dialog) -> None:
        if self._storage_roles_dialog is dialog:
            self._storage_roles_dialog = None


    def _profile_selected(self, label: str) -> None:
        profile_id=self.PROFILE_LABELS.get(label)
        if self.current_job is not None:
            self.current_job.profile_id=profile_id
        self._apply_profile(profile_id)
        if self.current_job is not None and self.job_list_path is not None:
            self._write_job_list(self.job_list_path)

    def _apply_profile(self, profile_id: str | None, *, persist: bool = True) -> None:
        self.active_profile_id=profile_id or None
        if persist:
            self.settings["last_profile_id"]=self.active_profile_id or ""
            save_config({"last_profile_id":self.active_profile_id or ""})
        self.source_panel.set_profile(self.active_profile_id)
        if self.active_profile_id=="noark5":
            for button in self.operations_panel.tab_buttons.values(): button.grid()
            categories=self.registry.categories()
            if categories: self.operations_panel.show_category(categories[0])
        else:
            for button in self.operations_panel.tab_buttons.values(): button.grid_remove()
            for child in self.operations_panel.cards.winfo_children(): child.destroy()
            text=("Velg profil for formatspesifikke operasjoner. "
                  "Generiske operasjoner legges her uavhengig av profil.")
            if self.active_profile_id=="siard":
                text="SIARD-profil valgt. SIARD-spesifikke operasjoner er ikke implementert i denne appen ennå."
            ctk.CTkLabel(self.operations_panel.cards,text=text,font=theme.font(theme.NORMAL_SIZE),
                         text_color=theme.TEXT_MUTED).grid(row=0,column=0,columnspan=3,padx=14,pady=20,sticky="w")
        if self.profile_menu is not None:
            label=next((k for k,v in self.PROFILE_LABELS.items() if v==self.active_profile_id),"-- profil --")
            self.profile_menu.set(label)

    def _source_browse_complete(self, path: Path) -> None:
        job=self._ensure_job_for_current_source()
        if job is None:
            messagebox.showwarning(
                APP_NAME,
                "Ingen aktiv jobb. Opprett eller åpne en jobb før Source kobles til jobben.",
            )
            return
        job.source_extraction = path
        self._show_storage_roles(job)

    def _ensure_job_for_current_source(self) -> Job | None:
        """Update/select a job; never create a new job implicitly.

        A JOB-xxx may only be created through the explicit Ny jobb action.
        Changing Source or workflow must preserve identity and all storage roles.
        """
        root=self.source_panel.path_var.get().strip()
        if not root:
            return self.current_job
        path=Path(root)

        if self.current_job is not None:
            self.current_job.source_extraction=path
            self._refresh_active_job_label()
            return self.current_job

        existing=next(
            (job for job in self.jobs.jobs() if job.active_extraction_root == path),
            None,
        )
        if existing is not None:
            self.current_job=existing
            self._refresh_active_job_label()
            return existing
        return None

    def _open_job(self, job: Job) -> None:
        # Profile belongs to the job and must follow JOB-xxx when switching.
        self._apply_profile(job.profile_id, persist=False)
        extraction=job.active_extraction_root
        if extraction is None:
            if self.batch_running:
                messagebox.showwarning(APP_NAME, "Vent til batch-kjøringen er ferdig eller stopp den først.")
                return
            self._capture_job_operation_params(self.current_job)
            self.current_job=job
            self.workflow.clear()
            for operation_id in job.workflow_ids:
                self.workflow.add(operation_id)
            self._apply_job_operation_params(job)
            self.workflow_panel.refresh()
            self.source_panel.path_var.set(""); self.source_panel.detect()
            self._refresh_active_job_label(); self._update_run_button()
            self.status_bar.set_status(f"Åpnet {job.job_id}: {job.name}")
            self._show_job_log(job)
            return
        super()._open_job(job)
        # The source panel represents the concrete Source – uttrekksmappe.
        self.source_panel.set_path(str(extraction))
        self._refresh_active_job_label()

    def _workflow_reordered(self, operation_id: str) -> None:
        job=self.current_job
        if job is None:
            return
        job.set_workflow(self.workflow.operation_ids())
        if job.workflow_ids:
            final_id=job.workflow_ids[-1]
            job.checkpoint_after=[oid for oid in job.checkpoint_after if oid != final_id]
        if job.status in {JobStatus.OK,JobStatus.FAILED,JobStatus.SKIPPED,JobStatus.WAITING}:
            job.reset_execution("Workflow endret - klar for ny kjøring")
        self._job_log(job,f"WORKFLOW REKKEFØLGE ENDRET: {operation_id}")
        self._refresh_active_job_label()
        if self.job_list_path is not None:
            self._write_job_list(self.job_list_path)
        if self.jobs_window is not None and self.jobs_window.winfo_exists():
            self.jobs_window.refresh()


    # ------------------------------------------------------------------
    # a14: one authoritative job-list file, with default/project/recent locations
    # ------------------------------------------------------------------

    def _remember_job_list_dir(self, directory: Path) -> None:
        directory = Path(directory)
        current = self.settings.get("recent_job_list_dirs", [])
        recent = [str(item) for item in current] if isinstance(current, list) else []
        value = str(directory)
        recent = [item for item in recent if item != value]
        recent.insert(0, value)
        recent = recent[:10]
        self.settings["last_job_list_dir"] = value
        self.settings["recent_job_list_dirs"] = recent
        save_config({"last_job_list_dir": value, "recent_job_list_dirs": recent})

    def _remember_job_list_file(self, path: Path) -> None:
        path = Path(path)
        current = self.settings.get("recent_job_list_files", [])
        recent = [str(item) for item in current] if isinstance(current, list) else []
        value = str(path)
        recent = [item for item in recent if item != value]
        recent.insert(0, value)
        recent = recent[:10]
        self.settings["last_job_list_file"] = value
        self.settings["recent_job_list_files"] = recent
        save_config({
            "last_job_list_file": value,
            "recent_job_list_files": recent,
        })

    def _forget_recent_job_list_file(self, path: Path) -> None:
        value = str(Path(path))
        current = self.settings.get("recent_job_list_files", [])
        recent = [str(item) for item in current] if isinstance(current, list) else []
        recent = [item for item in recent if item != value]
        self.settings["recent_job_list_files"] = recent
        changes = {"recent_job_list_files": recent}
        if str(self.settings.get("last_job_list_file", "")) == value:
            self.settings["last_job_list_file"] = ""
            changes["last_job_list_file"] = ""
        save_config(changes)
        self._choose_job_list_location(save=False)

    def _job_list_default_dir(self) -> Path:
        path = job_list_dir(self.settings)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _project_job_list_dir(self) -> Path | None:
        job = self.current_job
        if job is None or job.work_operations is None:
            return None
        root = Path(job.work_operations)
        if not root.is_dir():
            return None
        return project_dir(root)

    def _recent_job_list_dirs(self) -> list[Path]:
        raw = self.settings.get("recent_job_list_dirs", [])
        if not isinstance(raw, list):
            raw = []
        result: list[Path] = []
        for value in raw:
            path = Path(str(value))
            if path.is_dir() and path not in result:
                result.append(path)
        return result[:10]

    def _recent_job_list_files(self) -> list[Path]:
        raw = self.settings.get("recent_job_list_files", [])
        if not isinstance(raw, list):
            raw = []
        result: list[Path] = []
        for value in raw:
            path = Path(str(value))
            if path.is_file() and path not in result:
                result.append(path)
        return result[:10]

    def _choose_job_list_location(self, *, save: bool) -> None:
        default = self._job_list_default_dir()
        project = self._project_job_list_dir()

        def chosen_dir(directory: Path) -> None:
            if project is not None and directory == project:
                # wf is owned by Workflow Manager; its configured
                # work_operations parent must already exist.
                directory.mkdir(parents=True, exist_ok=True)
            self._remember_job_list_dir(directory)
            self._save_job_list_as_in(directory)

        def chosen_file(path: Path) -> None:
            self._load_job_list_file(Path(path), show_error=True)

        JobListLocationDialog(
            self,
            title="Lagre jobbliste" if save else "Åpne jobbliste",
            mode="save" if save else "open",
            default_dir=default,
            recent_dirs=self._recent_job_list_dirs(),
            recent_files=self._recent_job_list_files(),
            project_dir=project,
            on_choose_dir=chosen_dir if save else None,
            on_choose_file=chosen_file if not save else None,
            on_remove_recent_file=self._forget_recent_job_list_file if not save else None,
        )

    def _open_job_list_dialog(self) -> bool:
        if self.batch_running:
            return False
        self._choose_job_list_location(save=False)
        return False

    def _open_job_list_in(self, directory: Path) -> bool:
        filename = filedialog.askopenfilename(
            title="Åpne jobbliste",
            initialdir=str(directory),
            filetypes=[("Workflow-jobbliste", "*.n5jobs"), ("Alle filer", "*.*")],
        )
        if not filename:
            return False
        return self._load_job_list_file(Path(filename), show_error=True)

    def _save_job_list_as(self) -> bool:
        if self.batch_running:
            return False
        self._choose_job_list_location(save=True)
        return False

    def _save_job_list_as_in(self, directory: Path) -> bool:
        filename = filedialog.asksaveasfilename(
            title="Lagre jobbliste som",
            initialdir=str(directory),
            defaultextension=".n5jobs",
            filetypes=[("Workflow-jobbliste", "*.n5jobs"), ("Alle filer", "*.*")],
        )
        if not filename:
            return False
        old_path=self.job_list_path
        written=self._write_job_list(Path(filename))
        if written and (old_path is None or Path(filename) != old_path):
            self.log_panel.clear()
            self.status_bar.set_status("Ny jobbliste lagret – visningsloggen er nullstilt")
        return written

    def _load_job_list_file(self, path: Path, *, show_error: bool) -> bool:
        loaded = super()._load_job_list_file(path, show_error=show_error)
        if loaded:
            self._remember_job_list_dir(Path(path).parent)
            self._remember_job_list_file(Path(path))
            self._load_project_file_for_job_list(Path(path))
        return loaded

    def _write_job_list(self, path: Path) -> bool:
        written = super()._write_job_list(path)
        if written:
            saved_path = self.job_list_path or Path(path)
            self._remember_job_list_dir(Path(saved_path).parent)
            self._remember_job_list_file(Path(saved_path))
            self._sync_project_file_for_job_list(Path(saved_path))
        return written

    def _project_settings_payload(self) -> dict:
        """Project-local preferences that are safe to keep beside the project.

        Job execution state and storage roles stay authoritative in .n5jobs.
        project.json is intentionally a project metadata/preferences layer, not
        a second copy of the job itself.
        """
        return {
            "copy_run_log_to_work_operations": bool(
                self.settings.get("copy_run_log_to_work_operations", True)
            ),
        }

    def _project_name(self) -> str:
        job = self.current_job
        if job is not None and job.work_root is not None:
            return Path(job.work_root).name
        if job is not None and job.name:
            return job.name
        return "Workflow project"

    def _sync_project_file_for_job_list(self, job_list_path: Path) -> None:
        job = self.current_job
        if job is None or job.work_operations is None:
            return
        work_operations = Path(job.work_operations)
        if not is_project_job_list_path(job_list_path, work_operations):
            return
        save_project(
            project_dir(work_operations) / PROJECT_FILE_NAME,
            project_name=self._project_name(),
            profile_id=self.active_profile_id or "generic",
            job_profile_id=None,
            job_list_file=job_list_path.name,
            settings=self._project_settings_payload(),
        )

    def _load_project_file_for_job_list(self, job_list_path: Path) -> None:
        job = self.current_job
        if job is None or job.work_operations is None:
            return
        work_operations = Path(job.work_operations)
        if not is_project_job_list_path(job_list_path, work_operations):
            return
        path = project_dir(work_operations) / PROJECT_FILE_NAME
        if not path.is_file():
            return
        try:
            project = load_project(path)
        except ProjectConfigError:
            return
        if project.profile_id and project.profile_id != "generic":
            self._apply_profile(project.profile_id, persist=False)
        # Only project-safe preferences are imported. Global UI/application
        # settings remain global and are never replaced wholesale.
        if "copy_run_log_to_work_operations" in project.settings:
            self.settings["copy_run_log_to_work_operations"] = bool(
                project.settings["copy_run_log_to_work_operations"]
            )

    def _confirm_rerun(self, jobs) -> bool:
        previous = [
            job for job in jobs
            if job.status in _TERMINAL_STATUSES
            or job.message == "Konfigurasjon endret - klar for ny kjøring"
        ]
        if not previous:
            return True

        names = ", ".join(job.job_id for job in previous[:6])
        if len(previous) > 6:
            names += f" + {len(previous) - 6} til"

        message = (
            "En eller flere jobber er tidligere kjørt:\n\n"
            f"{names}\n\n"
            "Kjøre på nytt? Tidligere resultater slettes ikke. "
            "Den nye kjøringen dokumenteres som en ny hendelse."
        )
        if any("dias_package" in job.workflow_ids for job in previous):
            message += " DIAS/AIC-pakking oppretter en ny pakkeidentifikator."

        return messagebox.askyesno(APP_NAME, message)

    def _edit_storage_roles(self) -> None:
        job=self.current_job
        if job is None:
            messagebox.showwarning(APP_NAME,"Opprett eller åpne en jobb før mapper konfigureres.")
            return
        self._show_storage_roles(job)

    def _save_storage_roles(self, job: Job, values: dict) -> None:
        changed=False
        for attr,value in values.items():
            if getattr(job,attr) != value:
                setattr(job,attr,value); changed=True
        if changed and (job.status in {JobStatus.OK,JobStatus.FAILED,JobStatus.SKIPPED,JobStatus.WAITING}):
            job.reset_execution("Konfigurasjon endret - klar for ny kjøring")
        if changed:
            self._job_log(job,"KONFIGURASJON ENDRET: mappe-roller")
            if self.job_list_path is not None: self._write_job_list(self.job_list_path)
        if job.source_extraction is not None:
            self.source_panel.set_path(str(job.source_extraction))
        elif not self.source_panel.path_var.get().strip():
            self.source_panel.detect()
        self._refresh_active_job_label()
        self.status_bar.set_status("Mappe-roller oppdatert")
        if self.jobs_window is not None and self.jobs_window.winfo_exists(): self.jobs_window.refresh()

def run_gui() -> None:
    theme.apply_theme(); app=WorkflowApp(); app.mainloop()
