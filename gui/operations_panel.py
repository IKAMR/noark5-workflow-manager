from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.operation_metadata import is_visible, maturity_label
from noark5_workflow.core.registry import OperationRegistry
from settings import load_config
from . import theme


class OperationsPanel(ctk.CTkFrame):
    def __init__(self, master, registry: OperationRegistry, on_add: Callable[[str], None]):
        super().__init__(
            master,
            fg_color=theme.SURFACE_BG,
            corner_radius=10,
            height=theme.OPERATIONS_HEIGHT,
        )
        self.registry = registry
        self.on_add = on_add
        categories = self.registry.categories()
        self.active_category = categories[0] if categories else ""
        self.tab_buttons: dict[str, ctk.CTkButton] = {}

        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="TILGJENGELIGE OPERASJONER",
            font=theme.font(theme.SECTION_SIZE, "bold"),
            text_color=theme.TEXT_MUTED,
        ).grid(row=0, column=0, padx=12, pady=(8, 6), sticky="w")

        self.tabs = ctk.CTkFrame(
            self, fg_color=theme.PANEL_BG, corner_radius=8, height=34
        )
        self.tabs.grid(row=1, column=0, padx=10, pady=(0, 6), sticky="ew")
        self.tabs.grid_propagate(False)

        for col, category in enumerate(categories):
            button = ctk.CTkButton(
                self.tabs,
                text=category,
                width=80,
                height=24,
                corner_radius=5,
                font=theme.font(theme.SMALL_SIZE),
                command=lambda c=category: self.show_category(c),
                fg_color=theme.BUTTON_BG,
                hover_color=theme.BUTTON_HOVER,
                text_color=theme.TEXT,
            )
            button.grid(row=0, column=col, padx=2, pady=5)
            self.tab_buttons[category] = button

        self.cards = ctk.CTkFrame(
            self, fg_color=theme.PANEL_BG, corner_radius=8, height=62
        )
        self.cards.grid(row=2, column=0, padx=10, pady=(0, 8), sticky="ew")
        self.cards.grid_propagate(False)
        self.cards.grid_columnconfigure((0, 1, 2), weight=1, uniform="card")

        if self.active_category:
            self.show_category(self.active_category)

    def _visibility_level(self) -> int:
        settings = load_config()
        try:
            return int(settings.get("operation_visibility", 2))
        except (TypeError, ValueError):
            return 2

    def refresh_visibility(self) -> None:
        if self.active_category:
            self.show_category(self.active_category)

    def show_category(self, category: str) -> None:
        self.active_category = category
        for name, button in self.tab_buttons.items():
            button.configure(
                fg_color="#295291" if name == category else theme.BUTTON_BG,
                hover_color="#2f5aa0" if name == category else theme.BUTTON_HOVER,
            )

        for child in self.cards.winfo_children():
            child.destroy()

        minimum = self._visibility_level()
        operations = [
            op
            for op in self.registry.by_category(category)
            if is_visible(op.definition.operation_id, minimum)
        ]
        if not operations:
            ctk.CTkLabel(
                self.cards,
                text="Ingen operasjoner i denne kategorien med valgt modenhetsfilter.",
                font=theme.font(theme.NORMAL_SIZE),
                text_color=theme.TEXT_MUTED,
            ).grid(row=0, column=0, padx=14, pady=20, sticky="w")
            return

        accent = self.registry.category_color(category, theme.BLUE)
        for index, operation in enumerate(operations):
            row, col = divmod(index, 3)
            card = ctk.CTkFrame(
                self.cards,
                fg_color=theme.CARD_BG,
                border_width=1,
                border_color=accent,
                corner_radius=7,
                height=1,
            )
            card.grid(row=row, column=col, padx=6, pady=6, sticky="ew")
            card.grid_propagate(True)
            card.grid_columnconfigure(1, weight=1)

            ctk.CTkFrame(
                card, width=4, height=1, fg_color=accent, corner_radius=2
            ).grid(row=0, column=0, padx=(6, 0), pady=4, sticky="ns")

            label = (
                f"{operation.definition.name} · "
                f"{maturity_label(operation.definition.operation_id)}"
            )
            ctk.CTkLabel(
                card,
                text=label,
                font=theme.font(theme.NORMAL_SIZE),
                text_color=theme.TEXT,
                anchor="w",
            ).grid(row=0, column=1, padx=8, pady=7, sticky="ew")

            ctk.CTkButton(
                card,
                text="+",
                width=30,
                height=28,
                corner_radius=6,
                font=theme.font(14, "bold"),
                fg_color=accent,
                hover_color=accent,
                text_color="#ffffff",
                command=lambda op_id=operation.definition.operation_id: self.on_add(op_id),
            ).grid(row=0, column=2, padx=6, pady=5)
