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

        ctk.CTkLabel(
            self,
            text="WORKFLOW",
            font=theme.SECTION_FONT,
            text_color=theme.TEXT_MUTED,
        ).grid(row=0, column=0, padx=8, pady=(4, 8), sticky="w")

        self.items = ctk.CTkScrollableFrame(
            self,
            fg_color=theme.PANEL_BG_DARK,
            corner_radius=8,
        )
        self.items.grid(row=1, column=0, padx=4, pady=0, sticky="nsew")
        self.items.grid_columnconfigure(0, weight=1)

        run_row = ctk.CTkFrame(self, fg_color="transparent")
        run_row.grid(row=2, column=0, padx=4, pady=(10, 6), sticky="ew")
        run_row.grid_columnconfigure(0, weight=1)
        self.run_button = ctk.CTkButton(
            run_row,
            text="Kjør workflow",
            command=self.on_run,
            height=34,
            font=theme.NORMAL_FONT,
            fg_color=theme.BLUE,
            hover_color=theme.BLUE_DIM,
        )
        self.run_button.grid(row=0, column=0, sticky="ew")
        self.activity_button = ctk.CTkButton(
            run_row,
            text="◔",
            width=38,
            height=34,
            state="disabled",
            font=(theme.FONT_FAMILY, 14, "bold"),
            fg_color=theme.BUTTON_BG,
        )
        self.activity_button.grid(row=0, column=1, padx=(6, 0))

        buttons1 = ctk.CTkFrame(self, fg_color="transparent")
        buttons1.grid(row=3, column=0, padx=4, pady=(0, 4), sticky="ew")
        buttons1.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            buttons1,
            text="Tøm",
            command=self.clear,
            height=28,
            font=theme.SMALL_FONT,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
        ).grid(row=0, column=0, padx=(0, 3), sticky="ew")
        ctk.CTkButton(
            buttons1,
            text="Lagre profil...",
            state="disabled",
            height=28,
            font=theme.SMALL_FONT,
            fg_color=theme.BUTTON_BG,
        ).grid(row=0, column=1, padx=(3, 0), sticky="ew")

        buttons2 = ctk.CTkFrame(self, fg_color="transparent")
        buttons2.grid(row=4, column=0, padx=4, pady=(0, 4), sticky="ew")
        buttons2.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            buttons2,
            text="Åpne prosjekt",
            state="disabled",
            height=28,
            font=theme.SMALL_FONT,
            fg_color=theme.BUTTON_BG,
        ).grid(row=0, column=0, padx=(0, 3), sticky="ew")
        ctk.CTkButton(
            buttons2,
            text="Lagre prosjekt",
            state="disabled",
            height=28,
            font=theme.SMALL_FONT,
            fg_color=theme.BUTTON_BG,
        ).grid(row=0, column=1, padx=(3, 0), sticky="ew")

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
                font=theme.SMALL_FONT,
                text_color=theme.TEXT_MUTED,
                justify="center",
            ).grid(row=0, column=0, padx=8, pady=38)
            return

        for row, op_id in enumerate(ids):
            operation = self.registry.get(op_id)
            item = ctk.CTkFrame(
                self.items,
                fg_color=theme.PANEL_BG,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=6,
                height=1,
            )
            item.grid(row=row, column=0, padx=5, pady=3, sticky="ew")
            item.grid_propagate(True)
            item.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                item,
                text=f"{row + 1}. {operation.definition.name}",
                font=theme.SMALL_FONT,
                text_color=theme.TEXT,
                anchor="w",
            ).grid(row=0, column=0, padx=8, pady=6, sticky="ew")
            ctk.CTkButton(
                item,
                text="×",
                width=24,
                height=22,
                font=(theme.FONT_FAMILY, 12, "bold"),
                fg_color=theme.DANGER_BG,
                hover_color="#3d2020",
                text_color=theme.DANGER_TEXT,
                command=lambda oid=op_id: self.remove(oid),
            ).grid(row=0, column=1, padx=5, pady=4)
