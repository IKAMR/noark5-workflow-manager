from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from noark5_workflow.core.registry import OperationRegistry
from noark5_workflow.core.workflow import Workflow
from . import theme


class WorkflowPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        registry: OperationRegistry,
        workflow: Workflow,
        on_run: Callable[[], None],
    ):
        super().__init__(master, fg_color=theme.APP_BG, corner_radius=0)
        self.registry = registry
        self.workflow = workflow
        self.on_run = on_run

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="WORKFLOW", font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_MUTED).grid(
            row=0, column=0, padx=8, pady=(4, 8), sticky="w"
        )
        self.items = ctk.CTkScrollableFrame(self, fg_color=theme.PANEL_BG_DARK, corner_radius=8)
        self.items.grid(row=1, column=0, padx=4, pady=0, sticky="nsew")
        self.items.grid_columnconfigure(0, weight=1)

        run_row = ctk.CTkFrame(self, fg_color="transparent")
        run_row.grid(row=2, column=0, padx=4, pady=(10, 6), sticky="ew")
        run_row.grid_columnconfigure(0, weight=1)
        self.run_button = ctk.CTkButton(
            run_row, text="Kjør workflow", command=self.on_run, height=34, font=theme.font(theme.NORMAL_SIZE)
        )
        self.run_button.grid(row=0, column=0, sticky="ew")
        # SIARD-paritet: prosjekt-reset er synlig, men prosjektmodellen er ikke implementert ennå.
        self.reset_project_button = ctk.CTkButton(
            run_row, text="↻", width=38, height=34, state="disabled", font=theme.font(theme.NORMAL_SIZE)
        )
        self.reset_project_button.grid(row=0, column=1, padx=(6, 0))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=3, column=0, padx=4, pady=(0, 4), sticky="ew")
        buttons.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(buttons, text="Tøm", command=self.clear, height=28, font=theme.font(theme.SMALL_SIZE)).grid(
            row=0, column=0, padx=(0, 3), sticky="ew"
        )
        self.save_profile_button = ctk.CTkButton(
            buttons, text="Lagre profil...", state="disabled", height=28, font=theme.font(theme.SMALL_SIZE)
        )
        self.save_profile_button.grid(row=0, column=1, padx=(3, 0), sticky="ew")

        project_buttons = ctk.CTkFrame(self, fg_color="transparent")
        project_buttons.grid(row=4, column=0, padx=4, pady=(0, 4), sticky="ew")
        project_buttons.grid_columnconfigure((0, 1), weight=1)
        self.open_project_button = ctk.CTkButton(
            project_buttons, text="📂 Åpne prosjekt", state="disabled", height=28, font=theme.font(theme.SMALL_SIZE)
        )
        self.open_project_button.grid(row=0, column=0, padx=(0, 3), sticky="ew")
        self.save_project_button = ctk.CTkButton(
            project_buttons, text="💾 Lagre prosjekt", state="disabled", height=28, font=theme.font(theme.SMALL_SIZE)
        )
        self.save_project_button.grid(row=0, column=1, padx=(3, 0), sticky="ew")

        self.refresh()

    def add(self, operation_id: str) -> bool:
        added = self.workflow.add(operation_id)
        self.refresh()
        return added

    def remove(self, operation_id: str) -> None:
        self.workflow.remove(operation_id)
        self.refresh()

    def clear(self) -> None:
        self.workflow.clear()
        self.refresh()

    def refresh(self) -> None:
        for child in self.items.winfo_children():
            child.destroy()
        ids = self.workflow.operation_ids()
        if not ids:
            ctk.CTkLabel(
                self.items,
                text="Legg til operasjoner\nfra paletten til høyre",
                font=theme.font(theme.SMALL_SIZE),
                text_color=theme.TEXT_MUTED,
                justify="center",
            ).grid(row=0, column=0, padx=8, pady=36)
            return
        for row, op_id in enumerate(ids):
            operation = self.registry.get(op_id)
            item = ctk.CTkFrame(self.items, fg_color=theme.CARD_BG, corner_radius=6)
            item.grid(row=row, column=0, padx=5, pady=4, sticky="ew")
            item.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(item, text=f"{row + 1}. {operation.definition.name}", font=theme.font(theme.SMALL_SIZE), anchor="w").grid(
                row=0, column=0, padx=8, pady=7, sticky="ew"
            )
            ctk.CTkButton(
                item,
                text="×",
                width=28,
                height=26,
                font=("Consolas", 14, "bold"),
                command=lambda oid=op_id: self.remove(oid),
            ).grid(row=0, column=1, padx=5, pady=5)
