from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from noark5_workflow.core.job import Job, JobBatch, JobStatus
from settings import load_config, save_config
from . import theme


class JobsWindow(ctk.CTkToplevel):
    """Top-level job overview introduced in v0.1.1-a1.

    Scheduler and Worker remain technical concepts in a1. The window presents
    jobs, while double-click/Open returns to the familiar single-job workflow.
    """

    def __init__(
        self,
        master,
        batch: JobBatch,
        on_open_job: Callable[[Job], None],
        on_create_job: Callable[[Path], Job],
    ) -> None:
        super().__init__(master)
        self.batch = batch
        self.on_open_job = on_open_job
        self.on_create_job = on_create_job
        self.settings = load_config()
        self.title("Jobber - Noark 5 Workflow Manager")
        self.geometry("1250x720")
        self.minsize(980, 600)
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
            text="Batch-oversikt. Én jobb = én kilde + ett workflow + ett utdataområde.",
            font=theme.font(theme.SMALL_SIZE),
            text_color=theme.TEXT_MUTED,
        ).grid(row=1, column=0, pady=(4, 0), sticky="w")

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=1, column=0, padx=18, pady=8, sticky="ew")
        ctk.CTkButton(buttons, text="+ Ny jobb", command=self._new_job, width=110).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            buttons, text="Start alle", state="disabled", width=100,
            fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            buttons, text="Stopp", state="disabled", width=80,
            fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER,
        ).pack(side="left", padx=6)
        ctk.CTkLabel(
            buttons,
            text="Scheduler: lokal / sekvensiell (planlagt)   |   Worker: Lokal (denne PC-en)",
            font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_MUTED,
        ).pack(side="right")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=theme.PANEL_BG_DARK, corner_radius=8)
        self.list_frame.grid(row=2, column=0, padx=18, pady=(0, 8), sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

        self.summary = ctk.CTkLabel(self, text="", font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_SUB)
        self.summary.grid(row=3, column=0, padx=18, pady=(2, 14), sticky="w")
        self.refresh()

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
                f"Feil: {counts[JobStatus.FAILED]}"
            )
        )

    def _row(self, row: int, job: Job) -> None:
        card = ctk.CTkFrame(self.list_frame, fg_color=theme.CARD_BG, corner_radius=6)
        card.grid(row=row, column=0, padx=5, pady=4, sticky="ew")
        card.grid_columnconfigure(2, weight=1)

        status_color = theme.BLUE if job.status == JobStatus.RUNNING else theme.TEXT_SUB
        if job.status == JobStatus.FAILED:
            status_color = theme.DANGER_TEXT

        values = [
            (job.job_id, 85),
            (job.name, 180),
            (str(job.source_root), None),
            (job.status.value, 90),
            (f"{job.progress:.0%}", 60),
            (job.worker, 150),
        ]
        for col, (text, width) in enumerate(values):
            # CustomTkinter does not accept width=None because its scaling layer
            # multiplies the supplied width by the widget scaling factor.
            # Omit the width argument entirely for the flexible source-path column.
            label_kwargs = {
                "text": text,
                "anchor": "w",
                "font": theme.font(theme.SMALL_SIZE),
                "text_color": status_color if col == 3 else theme.TEXT,
            }
            if width is not None:
                label_kwargs["width"] = width

            label = ctk.CTkLabel(card, **label_kwargs)
            label.grid(row=0, column=col, padx=8, pady=10, sticky="ew" if col == 2 else "w")
            label.bind("<Double-Button-1>", lambda _event, j=job: self._open(j))

        ctk.CTkButton(card, text="Åpne", width=70, height=27, command=lambda j=job: self._open(j)).grid(
            row=0, column=6, padx=8, pady=6
        )
