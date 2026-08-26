from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from noark5_workflow.core.registry import OperationRegistry
from . import theme


class OperationsPanel(ctk.CTkFrame):
    def __init__(self, master, registry: OperationRegistry, on_add: Callable[[str], None]):
        super().__init__(master, fg_color=theme.APP_BG, corner_radius=0)
        self.registry = registry
        self.on_add = on_add
        self.active_category = "Pipeline"
        self.tab_buttons: dict[str, ctk.CTkButton] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="TILGJENGELIGE OPERASJONER", font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED).grid(
            row=0, column=0, padx=8, pady=(4, 10), sticky="w"
        )

        self.tabs = ctk.CTkFrame(self, fg_color=theme.PANEL_BG, corner_radius=8)
        self.tabs.grid(row=1, column=0, padx=0, pady=(0, 8), sticky="ew")
        for col, category in enumerate(theme.CATEGORIES):
            button = ctk.CTkButton(
                self.tabs,
                text=category,
                width=84,
                height=28,
                font=theme.SMALL_FONT,
                command=lambda c=category: self.show_category(c),
                fg_color=theme.PANEL_BG,
                hover_color="#263149",
            )
            button.grid(row=0, column=col, padx=2, pady=4)
            self.tab_buttons[category] = button

        self.cards = ctk.CTkScrollableFrame(self, fg_color=theme.PANEL_BG, corner_radius=8)
        self.cards.grid(row=2, column=0, sticky="nsew")
        self.cards.grid_columnconfigure((0, 1, 2), weight=1, uniform="card")
        self.show_category(self.active_category)

    def show_category(self, category: str) -> None:
        self.active_category = category
        for name, button in self.tab_buttons.items():
            button.configure(fg_color="#2e5fa7" if name == category else theme.PANEL_BG)
        for child in self.cards.winfo_children():
            child.destroy()

        operations = self.registry.by_category(category)
        if not operations:
            ctk.CTkLabel(
                self.cards,
                text="Ingen operasjoner i denne kategorien ennå.",
                font=theme.NORMAL_FONT,
                text_color=theme.TEXT_MUTED,
            ).grid(row=0, column=0, padx=16, pady=22, sticky="w")
            return

        accent = theme.CATEGORY_COLORS.get(category, theme.BLUE)
        for index, operation in enumerate(operations):
            row, col = divmod(index, 3)
            card = ctk.CTkFrame(
                self.cards,
                fg_color=theme.CARD_BG,
                border_width=1,
                border_color=accent,
                corner_radius=8,
                height=56,
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="ew")
            card.grid_columnconfigure(1, weight=1)
            ctk.CTkFrame(card, width=6, fg_color=accent, corner_radius=3).grid(
                row=0, column=0, padx=(8, 4), pady=8, sticky="ns"
            )
            ctk.CTkLabel(card, text=operation.definition.name, font=theme.NORMAL_FONT, anchor="w").grid(
                row=0, column=1, padx=6, pady=8, sticky="ew"
            )
            ctk.CTkButton(
                card,
                text="+",
                width=38,
                height=36,
                font=("Consolas", 18, "bold"),
                fg_color=accent,
                hover_color=accent,
                command=lambda op_id=operation.definition.operation_id: self.on_add(op_id),
            ).grid(row=0, column=2, padx=8, pady=8)
