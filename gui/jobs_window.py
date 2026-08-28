from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from noark5_workflow.core.job import Job, JobBatch, JobStatus
from settings import load_config, save_config
from . import theme


class JobsWindow(ctk.CTkToplevel):
    """Top-level job/batch overview."""

    def __init__(
        self,
        master,
        batch: JobBatch,
        on_open_job: Callable[[Job], None],
        on_create_job: Callable[[Path], Job],
        on_start_all: Callable[[], None],
        on_stop: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self.batch = batch
        self.on_open_job = on_open_job
        self.on_create_job = on_create_job
        self.on_start_all = on_start_all
        self.on_stop = on_stop
        self.settings = load_config()
        self._batch_running = False
        self.title("Jobber - Noark 5 Workflow Manager")
        self.geometry("1300x760")
        self.minsize(1000, 620)
        self.configure(fg_color=theme.APP_BG)
        self.transient(master)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color=theme.APP_BG, corner_radius=0)
        header.grid(row=0, column=0, padx=18, pady=(14, 6), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header, text="JOBBER", font=theme.font(theme.TITLE_SIZE, "bold"), text_color=theme.BLUE
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Batch-oversikt. Start alle kjører jobbene sekvensielt på lokal worker.",
            font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_MUTED,
        ).grid(row=1, column=0, pady=(4, 0), sticky="w")

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=1, column=0, padx=18, pady=8, sticky="ew")
        self.new_button = ctk.CTkButton(buttons, text="+ Ny jobb", command=self._new_job, width=110)
        self.new_button.pack(side="left", padx=(0, 6))
        self.start_all_button = ctk.CTkButton(
            buttons, text="Start alle", command=self.on_start_all, width=100,
            fg_color=theme.BLUE_DIM, hover_color=theme.BLUE,
        )
        self.start_all_button.pack(side="left", padx=6)
        self.stop_button = ctk.CTkButton(
            buttons, text="Stopp", command=self.on_stop, width=80, state="disabled",
            fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER,
        )
        self.stop_button.pack(side="left", padx=6)
        self.scheduler_label = ctk.CTkLabel(
            buttons,
            text="Scheduler: lokal / sekvensiell   |   Worker: Lokal (denne PC-en)",
            font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_MUTED,
        )
        self.scheduler_label.pack(side="right")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=theme.PANEL_BG_DARK, corner_radius=8)
        self.list_frame.grid(row=2, column=0, padx=18, pady=(0, 8), sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

        self.summary = ctk.CTkLabel(self, text="", font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_SUB)
        self.summary.grid(row=3, column=0, padx=18, pady=(2, 14), sticky="w")
        self.refresh()

    def set_batch_running(self, running: bool) -> None:
        self._batch_running = bool(running)
        self.new_button.configure(state="disabled" if running else "normal")
        self.start_all_button.configure(state="disabled" if running or len(self.batch) == 0 else "normal")
        self.stop_button.configure(state="normal" if running else "disabled")
        self.scheduler_label.configure(
            text=("Scheduler: KJØRER sekvensielt   |   Worker: Lokal (denne PC-en)"
                  if running else "Scheduler: lokal / sekvensiell   |   Worker: Lokal (denne PC-en)"),
            text_color=theme.BLUE if running else theme.TEXT_MUTED,
        )

    def _new_job(self) -> None:
        kwargs = {"title": "Velg rotmappe for ny Noark 5-jobb"}
        previous = str(self.settings.get("last_noark_source_dir", "")).strip()
        if previous and Path(previous).is_dir():
            kwargs["initialdir"] = previous
        folder = filedialog.askdirectory(**kwargs)
        if not folder:
            return
        save_config({"last_noark_source_dir": folder})
        job = self.on_create_job(Path(folder))
        self.refresh()
        self._open(job)

    def _open(self, job: Job) -> None:
        if self._batch_running:
            return
        self.on_open_job(job)
        self.destroy()

    def refresh(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        jobs = self.batch.jobs()
        if not jobs:
            ctk.CTkLabel(
                self.list_frame,
                text="Ingen jobber ennå.\nVelg «+ Ny jobb» for å opprette første jobb.",
                font=theme.font(theme.NORMAL_SIZE), text_color=theme.TEXT_MUTED, justify="center",
            ).grid(row=0, column=0, padx=20, pady=80)
        else:
            for row, job in enumerate(jobs):
                self._row(row, job)

        counts = self.batch.counts()
        self.summary.configure(
            text=(
                f"Totalt: {len(jobs)}   |   Ferdig: {counts[JobStatus.OK]}   |   "
                f"Kjører: {counts[JobStatus.RUNNING]}   |   Klar: {counts[JobStatus.READY]}   |   "
                f"Feil: {counts[JobStatus.FAILED]}   |   Hoppet over: {counts[JobStatus.SKIPPED]}"
            )
        )
        self.set_batch_running(self._batch_running)

    def _row(self, row: int, job: Job) -> None:
        card = ctk.CTkFrame(self.list_frame, fg_color=theme.CARD_BG, corner_radius=6)
        card.grid(row=row, column=0, padx=5, pady=4, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        status_color = theme.BLUE if job.status == JobStatus.RUNNING else theme.TEXT_SUB
        if job.status == JobStatus.FAILED:
            status_color = theme.DANGER_TEXT

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=2, padx=8, pady=(7, 0), sticky="ew")
        top.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(top, text=job.job_id, width=80, anchor="w", font=theme.font(theme.SMALL_SIZE, "bold")).grid(row=0, column=0, padx=(0, 8), sticky="w")
        ctk.CTkLabel(top, text=job.name, anchor="w", font=theme.font(theme.SMALL_SIZE, "bold")).grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(top, text=job.status.value, width=90, anchor="w", font=theme.font(theme.SMALL_SIZE), text_color=status_color).grid(row=0, column=2, padx=8, sticky="w")
        ctk.CTkLabel(top, text=f"{job.progress:.0%}", width=55, font=theme.font(theme.SMALL_SIZE)).grid(row=0, column=3, padx=8)
        ctk.CTkLabel(top, text=job.worker, width=145, anchor="w", font=theme.font(theme.SMALL_SIZE)).grid(row=0, column=4, padx=8, sticky="w")
        ctk.CTkButton(top, text="Åpne", width=70, height=27, state="disabled" if self._batch_running else "normal", command=lambda j=job: self._open(j)).grid(row=0, column=5, padx=(8, 0))

        details = ctk.CTkFrame(card, fg_color="transparent")
        details.grid(row=1, column=0, columnspan=2, padx=8, pady=(2, 7), sticky="ew")
        details.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(details, text=f"Kilde: {job.source_root}", anchor="w", font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_MUTED).grid(row=0, column=0, padx=(0, 18), sticky="w")
        ctk.CTkLabel(details, text=f"Utdata: {job.output_root or '(ikke valgt)'}", anchor="w", font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_MUTED).grid(row=0, column=1, sticky="ew")
        if job.message:
            ctk.CTkLabel(details, text=job.message, anchor="w", font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_SUB).grid(row=1, column=0, columnspan=2, pady=(2, 0), sticky="ew")
