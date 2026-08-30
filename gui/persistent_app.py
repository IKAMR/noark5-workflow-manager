from __future__ import annotations

import json
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

from gui.app import WorkflowApp as BaseWorkflowApp
from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.job import Job, JobStatus
from noark5_workflow.core.job_store import JobListFormatError, load_job_list, save_job_list
from noark5_workflow.core.output_lock import OutputLock, OutputLockedError
from noark5_workflow.sources.noark5_extraction import Noark5Extraction
from settings import save_config
from version import APP_NAME, VERSION

from . import theme
from .dias_dialog_a24 import DiasParamDialog
from .settings_dialog_a23 import SettingsDialog
from .jobs_window import JobsWindow


_TERMINAL_STATUSES = {JobStatus.OK, JobStatus.FAILED, JobStatus.SKIPPED}


class WorkflowApp(BaseWorkflowApp):
    """Persistent jobs, editable operations and checkpoint-aware local execution."""

    def __init__(self) -> None:
        self.job_list_path: Path | None = None
        super().__init__()

        self.workflow_panel.on_edit = self._edit_operation
        self.workflow_panel.on_checkpoint_toggle = self._toggle_checkpoint
        self.workflow_panel.checkpoint_ids_provider = self._checkpoint_ids
        self.workflow_panel.refresh()
        self._restore_last_job_list()

    def _capture_job_operation_params(self, job: Job | None) -> None:
        """Keep per-job parameters authoritative.

        Registry operation instances are shared transient GUI/execution objects.
        Copying their current params back into a job can leak configuration from
        another job. Configuration dialogs already save directly on the Job.
        """
        if job is None:
            return
        job.set_workflow(self.workflow.operation_ids())

    def _open_jobs(self) -> None:
        self._capture_job_operation_params(self.current_job)
        if self.jobs_window is not None and self.jobs_window.winfo_exists():
            self.jobs_window.focus()
            self.jobs_window.refresh()
            return
        self.jobs_window = JobsWindow(
            self,
            self.jobs,
            self._open_job,
            self._create_job,
            self._start_all_jobs,
            self._stop_batch,
            self._new_job_list,
            self._open_job_list_dialog,
            self._save_job_list,
            self._save_job_list_as,
            lambda: self.job_list_path,
            lambda: self.current_job.job_id if self.current_job else None,
        )

    def _refresh_active_job_label(self) -> None:
        if not self.current_job:
            self.active_job_label.configure(
                text="AKTIV JOBB: ingen",
                text_color=theme.TEXT_SUB,
            )
            return

        jobs = self.jobs.jobs()
        try:
            position = next(
                index
                for index, job in enumerate(jobs, start=1)
                if job.job_id == self.current_job.job_id
            )
        except StopIteration:
            position = 0

        count = len(self.workflow.operation_ids())
        if count == 0:
            workflow_text = "Workflow: 0 operasjoner - legg til operasjoner"
        elif count == 1:
            workflow_text = "Workflow: 1 operasjon"
        else:
            workflow_text = f"Workflow: {count} operasjoner"

        position_text = f"{position} av {len(jobs)}" if position else f"? av {len(jobs)}"
        self.active_job_label.configure(
            text=(
                f"AKTIV JOBB: {position_text} | {self.current_job.job_id} | "
                f"{self.current_job.name} | {workflow_text}"
            ),
            text_color=theme.BLUE,
        )

    def _job_list_initial_dir(self) -> str | None:
        if self.job_list_path is not None and self.job_list_path.parent.is_dir():
            return str(self.job_list_path.parent)
        previous = str(self.settings.get("last_job_list_dir", "")).strip()
        return previous if previous and Path(previous).is_dir() else None

    def _new_job_list(self) -> bool:
        if self.batch_running:
            return False
        if len(self.jobs) and not messagebox.askyesno(
            APP_NAME,
            "Opprette en ny tom jobbliste? Gjeldende jobbliste blir ikke lagret automatisk.",
        ):
            return False

        self.current_job = None
        self.jobs.clear()
        self.workflow.clear()
        self.workflow_panel.refresh()
        self.source_panel.path_var.set("")
        self.source_panel.detect()
        self.log_panel.clear()
        self.job_list_path = None
        self._refresh_active_job_label()
        self._update_run_button()

        self.settings["last_job_list_file"] = ""
        save_config({"last_job_list_file": ""})
        self.status_bar.set_status("Ny tom jobbliste")
        return True

    def _open_job_list_dialog(self) -> bool:
        if self.batch_running:
            return False

        kwargs = {
            "title": "Åpne jobbliste",
            "filetypes": [("Noark 5 jobbliste", "*.n5jobs"), ("Alle filer", "*.*")],
        }
        initial = self._job_list_initial_dir()
        if initial:
            kwargs["initialdir"] = initial

        filename = filedialog.askopenfilename(**kwargs)
        if not filename:
            return False
        return self._load_job_list_file(Path(filename), show_error=True)

    def _load_job_list_file(self, path: Path, *, show_error: bool) -> bool:
        try:
            loaded = load_job_list(path)
        except (JobListFormatError, OSError) as exc:
            if show_error:
                messagebox.showerror(APP_NAME, f"Kunne ikke åpne jobblisten:\n{exc}")
            return False

        self.current_job = None
        self.workflow.clear()
        self.jobs.replace_all(loaded.batch.jobs())
        self.job_list_path = Path(path)

        self.settings["last_job_list_file"] = str(path)
        self.settings["last_job_list_dir"] = str(path.parent)
        save_config({
            "last_job_list_file": str(path),
            "last_job_list_dir": str(path.parent),
        })

        active = self.jobs.get(loaded.active_job_id) if loaded.active_job_id else None
        if active is None and len(self.jobs):
            active = self.jobs.jobs()[0]

        if active is not None:
            self._open_job(active)
        else:
            self.workflow_panel.refresh()
            self.source_panel.path_var.set("")
            self.source_panel.detect()
            self._refresh_active_job_label()
            self._update_run_button()

        self.status_bar.set_status(f"Jobbliste åpnet: {path.name}")
        return True

    def _save_job_list(self) -> bool:
        if self.batch_running:
            return False
        if self.job_list_path is None:
            return self._save_job_list_as()
        return self._write_job_list(self.job_list_path)

    def _save_job_list_as(self) -> bool:
        if self.batch_running:
            return False

        kwargs = {
            "title": "Lagre jobbliste som",
            "defaultextension": ".n5jobs",
            "filetypes": [("Noark 5 jobbliste", "*.n5jobs"), ("Alle filer", "*.*")],
        }
        initial = self._job_list_initial_dir()
        if initial:
            kwargs["initialdir"] = initial

        filename = filedialog.asksaveasfilename(**kwargs)
        if not filename:
            return False
        return self._write_job_list(Path(filename))

    def _write_job_list(self, path: Path) -> bool:
        self._capture_job_operation_params(self.current_job)
        try:
            saved_path = save_job_list(
                path,
                self.jobs,
                active_job_id=self.current_job.job_id if self.current_job else None,
                app_version=VERSION,
            )
        except (OSError, TypeError) as exc:
            messagebox.showerror(APP_NAME, f"Kunne ikke lagre jobblisten:\n{exc}")
            return False

        self.job_list_path = saved_path
        self.settings["last_job_list_file"] = str(saved_path)
        self.settings["last_job_list_dir"] = str(saved_path.parent)
        save_config({
            "last_job_list_file": str(saved_path),
            "last_job_list_dir": str(saved_path.parent),
        })
        self.status_bar.set_status(f"Jobbliste lagret: {saved_path.name}")
        return True

    def _restore_last_job_list(self) -> None:
        previous = str(self.settings.get("last_job_list_file", "")).strip()
        if not previous:
            return

        path = Path(previous)
        if not path.is_file():
            return

        if not self._load_job_list_file(path, show_error=False):
            self.status_bar.set_status("Sist brukte jobbliste kunne ikke åpnes")

    # ------------------------------------------------------------------
    # v0.1.2-a1: edit existing operation configuration and controlled rerun
    # ------------------------------------------------------------------

    def _add_operation(self, operation_id: str) -> None:
        """Use the a2.3 DIAS dialog also for first-time configuration."""
        if operation_id != "dias_package":
            super()._add_operation(operation_id)
            return
        if self.batch_running:
            messagebox.showwarning(APP_NAME, "Workflow kan ikke endres mens Start alle kjører.")
            return

        operation = self.registry.get(operation_id)
        extraction_root = self.extraction.root if self.extraction else None
        initial_params = self.current_job.get_operation_params(operation_id) if self.current_job else {}

        def add_configured(params: dict) -> bool:
            job = self.current_job or self._ensure_job_for_current_source()
            if job is None:
                messagebox.showwarning(APP_NAME, "Velg en source før DIAS-konfigurasjon.")
                return False
            new_output = Path(params["output_dir"]) if params.get("output_dir") else None
            conflict = self._find_output_conflict(job, new_output)
            if conflict is not None:
                messagebox.showerror(
                    APP_NAME,
                    "Utdatamappen brukes allerede av en annen jobb.\n\n"
                    f"{conflict.job_id}: {conflict.output_root}\n\n"
                    "Velg en egen utdatamappe for denne jobben.",
                )
                return False

            operation.configure(params)
            added = self.workflow_panel.add(operation_id)
            job.output_root = new_output
            job.set_workflow(self.workflow.operation_ids())
            job.set_operation_params(operation_id, params)
            self._refresh_active_job_label()
            if added:
                self.log_panel.append(f"Lagt til i workflow: {operation.definition.name}")
                self.log_panel.append(f"DIAS-utdata: {params.get('output_dir') or '(ikke valgt)'}")
            else:
                self.status_bar.set_status("DIAS-konfigurasjon oppdatert for aktiv jobb")
            if self.job_list_path is not None:
                self._write_job_list(self.job_list_path)
            return True

        DiasParamDialog(self, initial_params, extraction_root, add_configured)

    def _find_output_conflict(self, job: Job, output_root: Path | None) -> Job | None:
        if output_root is None:
            return None
        try:
            candidate = output_root.resolve()
        except OSError:
            candidate = output_root.absolute()
        for other in self.jobs.jobs():
            if other.job_id == job.job_id or other.output_root is None:
                continue
            try:
                other_path = other.output_root.resolve()
            except OSError:
                other_path = other.output_root.absolute()
            if candidate == other_path:
                return other
        return None

    def _validate_unique_outputs(self, jobs: list[Job]) -> bool:
        seen: dict[str, Job] = {}
        for job in jobs:
            if job.output_root is None:
                continue
            try:
                key = str(job.output_root.resolve()).casefold()
            except OSError:
                key = str(job.output_root.absolute()).casefold()
            other = seen.get(key)
            if other is not None and other.job_id != job.job_id:
                messagebox.showerror(
                    APP_NAME,
                    "To forskjellige jobber kan ikke bruke samme utdataområde.\n\n"
                    f"{other.job_id}: {other.output_root}\n"
                    f"{job.job_id}: {job.output_root}\n\n"
                    "Velg separate utdataområder. Samme jobb kan kjøres flere ganger "
                    "mot sitt eget område; historikk skal da bevares.",
                )
                return False
            seen[key] = job
        return True

    def _edit_operation(self, operation_id: str) -> None:
        if self.batch_running:
            messagebox.showwarning(APP_NAME, "Workflow kan ikke redigeres mens Start alle kjører.")
            return
        job = self.current_job
        if job is None:
            messagebox.showwarning(APP_NAME, "Åpne en jobb før du redigerer workflow.")
            return
        if operation_id not in job.workflow_ids:
            messagebox.showwarning(APP_NAME, "Operasjonen finnes ikke i aktiv jobb.")
            return

        if operation_id != "dias_package":
            self.status_bar.set_status("Denne operasjonen har ingen redigeringsdialog ennå")
            return

        operation = self.registry.get(operation_id)
        initial_params = job.get_operation_params(operation_id)
        extraction_root = self.extraction.root if self.extraction else job.source_root

        def save_changes(params: dict) -> bool:
            new_output = Path(params["output_dir"]) if params.get("output_dir") else None
            conflict = self._find_output_conflict(job, new_output)
            if conflict is not None:
                messagebox.showerror(
                    APP_NAME,
                    "Utdatamappen brukes allerede av en annen jobb.\n\n"
                    f"{conflict.job_id}: {conflict.output_root}\n\n"
                    "Velg en egen utdatamappe for denne jobben.",
                )
                return False
            operation.configure(params)
            job.set_operation_params(operation_id, params)
            job.set_workflow(self.workflow.operation_ids())
            job.output_root = new_output

            # Editing executed/waiting work invalidates the execution cursor:
            # a later run is a deliberate new run from the beginning.
            if job.status in _TERMINAL_STATUSES or job.status == JobStatus.WAITING:
                job.reset_execution("Konfigurasjon endret - klar for ny kjøring")

            self._job_log(job, "KONFIGURASJON ENDRET: DIAS-pakking")
            self.log_panel.append(f"DIAS-konfigurasjon oppdatert for {job.job_id}")
            self.status_bar.set_status("DIAS-konfigurasjon oppdatert")
            self._update_run_button()

            if self.jobs_window is not None and self.jobs_window.winfo_exists():
                self.jobs_window.refresh()

            if self.job_list_path is not None:
                self._write_job_list(self.job_list_path)
            return True

        DiasParamDialog(self, initial_params, extraction_root, save_changes)

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
        return messagebox.askyesno(
            APP_NAME,
            "En eller flere jobber er tidligere kjørt:\n\n"
            f"{names}\n\n"
            "Kjøre på nytt? Tidligere resultatmapper slettes ikke. "
            "En ny DIAS/AIC får ny identifikator, og ny kjøring dokumenteres som en ny hendelse.",
        )

    # ------------------------------------------------------------------
    # v0.1.2-a2: checkpoints and persistent execution cursor
    # ------------------------------------------------------------------

    def _checkpoint_ids(self) -> set[str]:
        if self.current_job is None:
            return set()
        return set(self.current_job.checkpoint_after)

    def _toggle_checkpoint(self, operation_id: str) -> None:
        if self.batch_running:
            messagebox.showwarning(APP_NAME, "Kontrollpunkter kan ikke endres mens batch kjører.")
            return
        job = self.current_job
        if job is None:
            messagebox.showwarning(APP_NAME, "Åpne en jobb før du setter kontrollpunkt.")
            return

        enabled = not job.has_checkpoint(operation_id)
        job.set_checkpoint(operation_id, enabled)
        state = "lagt til" if enabled else "fjernet"
        self._job_log(job, f"KONTROLLPUNKT {state}: etter {operation_id}")
        self.workflow_panel.refresh()

        if self.job_list_path is not None:
            self._write_job_list(self.job_list_path)

    def _update_run_button(self) -> None:
        if not hasattr(self, "workflow_panel"):
            return
        if self.current_job is not None and self.current_job.status == JobStatus.WAITING:
            self.workflow_panel.set_run_text("Fortsett workflow")
        else:
            self.workflow_panel.set_run_text("Kjør workflow")

    def _open_job(self, job: Job) -> None:
        super()._open_job(job)
        self.workflow_panel.refresh()
        self._update_run_button()

    def _execute_job(self, job: Job, *, batch_mode: bool) -> bool:
        op_ids = list(job.workflow_ids)
        if not op_ids:
            job.status = JobStatus.SKIPPED
            job.message = "Ingen operasjoner i workflow"
            self._job_log(job, "HOPPET OVER: Ingen operasjoner i workflow")
            return True

        start_index = job.next_operation_index if job.status == JobStatus.WAITING else 0
        start_index = max(0, min(start_index, len(op_ids)))

        # Explicit rerun of terminal work begins from operation 1.
        if job.status in _TERMINAL_STATUSES:
            start_index = 0
            job.next_operation_index = 0
            job.progress = 0.0

        if start_index >= len(op_ids):
            start_index = 0
            job.next_operation_index = 0
            job.progress = 0.0

        resuming = start_index > 0
        job.status = JobStatus.RUNNING
        job.message = (
            f"Workflow fortsetter fra operasjon {start_index + 1}"
            if resuming else
            "Workflow startet"
        )
        self._job_log(
            job,
            f"Workflow fortsetter fra operasjon {start_index + 1}"
            if resuming else
            "Workflow startet",
        )
        if self.jobs_window is not None and self.jobs_window.winfo_exists():
            self.after(0, self.jobs_window.refresh)

        output_lock = None
        try:
            if job.output_root:
                output_lock = OutputLock(job.output_root, job.job_id)
                output_lock.acquire()
                self._job_log(job, f"Utdata låst: {job.output_root}")

            source = Noark5Extraction.detect(job.source_root)
            ctx = OperationContext(
                extraction_root=job.source_root,
                source=source,
                settings=self.settings,
                progress_cb=lambda value, message: self._progress_callback_for_job(job, value, message),
                log_cb=lambda msg: self._job_log(job, msg),
                cancelled_cb=lambda: self.batch_cancel_requested if batch_mode else self.cancel_requested,
            )

            total = len(op_ids)
            all_ok = True

            for zero_index in range(start_index, total):
                op_id = op_ids[zero_index]

                if (self.batch_cancel_requested if batch_mode else self.cancel_requested):
                    job.status = JobStatus.SKIPPED
                    job.message = "Avbrutt"
                    self._job_log(job, "AVBRUTT før neste operasjon")
                    return False

                operation = self._configure_operation_for_job(job, op_id)

                if op_id == "dias_package":
                    params = job.get_operation_params(op_id)
                    configured_output = str(params.get("output_dir", "") or "").strip()
                    job_output = str(job.output_root) if job.output_root is not None else ""

                    # output_root mirrors the DIAS output selection. If a legacy or
                    # stale state differs, the Job value wins and is written back.
                    if job_output and configured_output != job_output:
                        params["output_dir"] = job_output
                        job.set_operation_params(op_id, params)
                        operation.configure(params)
                        self._job_log(
                            job,
                            f"DIAS-utdata synkronisert fra jobb: {job_output}",
                        )

                self._job_log(job, f"START: {operation.definition.name}")
                result = self.executor.execute(operation, ctx)
                all_ok = all_ok and result.ok
                self._job_log(job, result.message)

                for warning in result.warnings:
                    self._job_log(job, f"ADVARSEL: {warning}")
                if result.data:
                    self._job_log(job, json.dumps(result.data, ensure_ascii=False, indent=2))

                self._job_log(job, f"{'OK' if result.ok else 'FEIL'}: {operation.definition.name}")
                job.message = result.message

                if not result.ok:
                    # Retry should start with the failed operation.
                    job.next_operation_index = zero_index
                    job.progress = zero_index / total
                    break

                job.mark_operation_completed(zero_index)

                if self.jobs_window is not None and self.jobs_window.winfo_exists():
                    self.after(0, self.jobs_window.refresh)

                # Stop after a successful operation when a checkpoint is planned.
                # No stop is needed after the final operation.
                if job.has_checkpoint(op_id) and zero_index < total - 1:
                    job.status = JobStatus.WAITING
                    job.message = f"Venter ved kontrollpunkt etter {operation.definition.name}"
                    self._job_log(job, job.message)
                    if self.job_list_path is not None:
                        self._write_job_list(self.job_list_path)
                    self.after(0, self._update_run_button)
                    return True

            if all_ok:
                job.status = JobStatus.OK
                job.progress = 1.0
                job.next_operation_index = total
                job.message = "Workflow fullført"
            else:
                job.status = JobStatus.FAILED
                job.message = "Workflow stoppet med feil"

            self._job_log(job, job.message)
            if self.job_list_path is not None:
                self._write_job_list(self.job_list_path)
            self.after(0, self._update_run_button)
            return all_ok

        except OutputLockedError as exc:
            job.status = JobStatus.FAILED
            job.message = str(exc)
            self._job_log(job, f"FEIL: {exc}")
            return False
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.message = str(exc)
            self._job_log(job, f"FEIL: {exc}")
            return False
        finally:
            if output_lock is not None:
                output_lock.release()
            if self.jobs_window is not None and self.jobs_window.winfo_exists():
                self.after(0, self.jobs_window.refresh)

    def _run_workflow(self) -> None:
        if self.batch_running:
            messagebox.showwarning(APP_NAME, "Start alle kjører allerede.")
            return

        op_ids = self.workflow.operation_ids()
        if not op_ids:
            messagebox.showwarning(APP_NAME, "Legg til minst én operasjon i workflow først.")
            return
        root = self.source_panel.path_var.get().strip()
        if not root:
            messagebox.showwarning(APP_NAME, "Velg en uttrekksmappe først.")
            return

        job = self._ensure_job_for_current_source()
        if job is None:
            return
        if not self._validate_unique_outputs(self.jobs.jobs()):
            return

        job.set_workflow(op_ids)
        self._capture_job_operation_params(job)

        # WAITING means continue from the persisted cursor, not a rerun.
        if job.status != JobStatus.WAITING and job.status in _TERMINAL_STATUSES:
            if not self._confirm_rerun([job]):
                return

        self.workflow_panel.run_button.configure(state="disabled")
        self.cancel_requested = False

        def worker() -> None:
            ok = self._execute_job(job, batch_mode=False)
            if job.status == JobStatus.WAITING:
                final = job.message
            else:
                final = "Workflow fullført" if ok else "Workflow stoppet med feil"
            self.after(0, lambda: self.status_bar.set_status(final))
            self.after(0, lambda: self.workflow_panel.run_button.configure(state="normal"))
            self.after(0, self._update_run_button)

        threading.Thread(target=worker, daemon=True).start()

    def _start_all_jobs(self) -> None:
        if self.batch_running:
            return
        if len(self.jobs) == 0:
            messagebox.showwarning(APP_NAME, "Det finnes ingen jobber å kjøre.")
            return
        if not self._validate_unique_outputs(self.jobs.jobs()):
            return

        terminal = [job for job in self.jobs.jobs() if job.status in _TERMINAL_STATUSES]
        if terminal and not self._confirm_rerun(terminal):
            return

        self._capture_job_operation_params(self.current_job)
        self.batch_running = True
        self.batch_cancel_requested = False
        self.workflow_panel.run_button.configure(state="disabled")
        if self.jobs_window is not None and self.jobs_window.winfo_exists():
            self.jobs_window.set_batch_running(True)
        self.log_panel.append("BATCH START: kjører alle jobber sekvensielt")

        def worker() -> None:
            jobs = self.jobs.jobs()
            for job in jobs:
                if self.batch_cancel_requested:
                    if job.status == JobStatus.READY:
                        job.status = JobStatus.SKIPPED
                        job.message = "Ikke startet - batch avbrutt"
                    continue

                # WAITING jobs continue from their checkpoint. Terminal jobs are
                # explicit reruns and therefore restart at operation 1.
                if job.status in _TERMINAL_STATUSES:
                    job.reset_execution("Klar for ny batchkjøring")

                self._execute_job(job, batch_mode=True)

            counts = self.jobs.counts()
            waiting = counts.get(JobStatus.WAITING, 0)
            summary = (
                f"BATCH FERDIG: totalt={len(jobs)}, ferdig={counts[JobStatus.OK]}, "
                f"venter={waiting}, feil={counts[JobStatus.FAILED]}, "
                f"hoppet over={counts[JobStatus.SKIPPED]}"
            )
            self.after(0, lambda s=summary: self.log_panel.append(s))
            self.after(0, lambda s=summary: self.status_bar.set_status(s))
            self.batch_running = False
            self.after(0, lambda: self.workflow_panel.run_button.configure(state="normal"))
            self.after(0, self._update_run_button)
            if self.jobs_window is not None and self.jobs_window.winfo_exists():
                self.after(0, lambda: self.jobs_window.set_batch_running(False))
                self.after(0, self.jobs_window.refresh)

        threading.Thread(target=worker, daemon=True).start()


    def _open_settings(self) -> None:
        SettingsDialog(self, self.settings, self._save_settings)


def run_gui() -> None:
    theme.apply_theme()
    app = WorkflowApp()
    app.mainloop()
