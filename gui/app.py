from __future__ import annotations

import json
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from noark5_workflow.app import build_registry
from noark5_workflow.core.context import OperationContext
from noark5_workflow.executors.local import LocalExecutor
from noark5_workflow.sources.noark5_extraction import Noark5Extraction
from version import APP_NAME, VERSION


class WorkflowApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} {VERSION}")
        self.geometry("1100x720")
        self.minsize(900, 620)

        self.registry = build_registry()
        self.executor = LocalExecutor()
        self.extraction: Noark5Extraction | None = None
        self.cancel_requested = False

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(header, text=APP_NAME, font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=12, pady=12, sticky="w"
        )
        ctk.CTkLabel(header, text=f"Shell {VERSION} | execution backend: local").grid(
            row=0, column=1, padx=12, pady=12, sticky="e"
        )

        source = ctk.CTkFrame(self)
        source.grid(row=1, column=0, padx=12, pady=6, sticky="ew")
        source.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(source, text="Uttrekksmappe").grid(row=0, column=0, padx=8, pady=8)
        self.path_var = ctk.StringVar()
        ctk.CTkEntry(source, textvariable=self.path_var).grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        ctk.CTkButton(source, text="Bla gjennom", width=90, command=self._browse).grid(row=0, column=2, padx=8, pady=8)
        ctk.CTkButton(source, text="Finn", width=90, command=self._detect).grid(row=0, column=3, padx=8, pady=8)

        body = ctk.CTkFrame(self)
        body.grid(row=2, column=0, padx=12, pady=6, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body)
        left.grid(row=0, column=0, padx=(8, 4), pady=8, sticky="nsew")
        left.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(left, text="Operasjoner", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=8, pady=(10, 4), sticky="w"
        )
        self.op_var = ctk.StringVar(value="detect_extraction")
        for row, op in enumerate(self.registry.all(), start=1):
            ctk.CTkRadioButton(
                left,
                text=op.definition.name,
                variable=self.op_var,
                value=op.definition.operation_id,
            ).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        run_row = len(self.registry.all()) + 1
        self.run_button = ctk.CTkButton(left, text="Kjør valgt operasjon", command=self._run_selected)
        self.run_button.grid(row=run_row, column=0, padx=10, pady=(16, 8), sticky="ew")

        right = ctk.CTkFrame(body)
        right.grid(row=0, column=1, padx=(4, 8), pady=8, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(right, text="Logg / resultat", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=8, pady=(10, 4), sticky="w"
        )
        self.logbox = ctk.CTkTextbox(right, wrap="word")
        self.logbox.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")

        footer = ctk.CTkFrame(self)
        footer.grid(row=3, column=0, padx=12, pady=(6, 12), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        self.progress = ctk.CTkProgressBar(footer)
        self.progress.set(0)
        self.progress.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        self.status_var = ctk.StringVar(value="Klar")
        ctk.CTkLabel(footer, textvariable=self.status_var, width=260, anchor="w").grid(
            row=0, column=1, padx=8, pady=8
        )

    def _browse(self) -> None:
        folder = filedialog.askdirectory(title="Velg rotmappe for Noark 5-uttrekk")
        if folder:
            self.path_var.set(folder)

    def _append_log(self, text: str) -> None:
        self.logbox.insert("end", text + "\n")
        self.logbox.see("end")

    def _detect(self) -> None:
        root = self.path_var.get().strip()
        if not root:
            messagebox.showwarning(APP_NAME, "Velg en uttrekksmappe først.")
            return
        try:
            self.extraction = Noark5Extraction.detect(root)
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        self._append_log(json.dumps(self.extraction.inventory(), ensure_ascii=False, indent=2))
        self.status_var.set("Noark 5-uttrekk funnet" if self.extraction.is_noark5_candidate else "arkivstruktur.xml ble ikke funnet")

    def _progress_callback(self, value: float, message: str) -> None:
        self.after(0, lambda: self.progress.set(value))
        self.after(0, lambda: self.status_var.set(message or "Kjorer"))

    def _run_selected(self) -> None:
        root = self.path_var.get().strip()
        if not root:
            messagebox.showwarning(APP_NAME, "Velg en uttrekksmappe først.")
            return
        operation = self.registry.get(self.op_var.get())
        self.run_button.configure(state="disabled")
        self.progress.set(0)
        self.cancel_requested = False

        def worker() -> None:
            try:
                source = self.extraction or Noark5Extraction.detect(root)
                ctx = OperationContext(
                    extraction_root=Path(root),
                    source=source,
                    progress_cb=self._progress_callback,
                    log_cb=lambda msg: self.after(0, lambda: self._append_log(msg)),
                    cancelled_cb=lambda: self.cancel_requested,
                )
                result = self.executor.execute(operation, ctx)
                payload = {
                    "ok": result.ok,
                    "message": result.message,
                    "warnings": result.warnings,
                    "outputs": result.outputs,
                    "data": result.data,
                }
                self.after(0, lambda: self._append_log(json.dumps(payload, ensure_ascii=False, indent=2)))
                self.after(0, lambda: self.status_var.set("Done" if result.ok else "Failed"))
            except Exception as exc:
                self.after(0, lambda: self._append_log(f"ERROR: {exc}"))
                self.after(0, lambda: self.status_var.set("Feil"))
            finally:
                self.after(0, lambda: self.run_button.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()


def run_gui() -> None:
    ctk.set_appearance_mode("system")
    app = WorkflowApp()
    app.mainloop()
