from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Iterable

import customtkinter as ctk

from . import theme


@dataclass(frozen=True)
class LocationChoice:
    """One selectable path in the common storage-location dialog."""

    label: str
    path: Path
    removable: bool = False


class StorageLocationDialog(ctk.CTkToplevel):
    """Common chooser for folder/file roles.

    The dialog presents known/current/default/recent locations first and keeps
    the native Windows chooser as an explicit secondary action.
    """

    def __init__(
        self,
        master,
        *,
        title: str,
        heading: str,
        description: str,
        choices: Iterable[LocationChoice],
        initial_path: Path | None,
        kind: str,
        on_choose: Callable[[Path], None],
        on_remove: Callable[[Path], None] | None = None,
        filetypes: list[tuple[str, str]] | None = None,
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.geometry("1320x560")
        self.minsize(960, 440)
        self.transient(master)
        self.grab_set()

        self._on_choose = on_choose
        self._on_remove = on_remove
        self._initial = initial_path
        self._kind = kind
        self._filetypes = filetypes or [("Alle filer", "*.*")]

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self,
            text=heading,
            font=theme.font(theme.TITLE_SIZE, "bold"),
            text_color=theme.BLUE,
        ).grid(row=0, column=0, padx=24, pady=(20, 6), sticky="w")
        ctk.CTkLabel(
            self,
            text=description,
            font=theme.font(theme.SMALL_SIZE),
            text_color=theme.TEXT_MUTED,
        ).grid(row=1, column=0, padx=24, pady=(0, 10), sticky="w")

        body = ctk.CTkScrollableFrame(self, fg_color=theme.PANEL_BG)
        body.grid(row=2, column=0, padx=20, pady=8, sticky="nsew")
        body.grid_columnconfigure(1, weight=1)

        unique: list[LocationChoice] = []
        seen: set[str] = set()
        for choice in choices:
            key = str(choice.path).casefold()
            if not str(choice.path).strip() or key in seen:
                continue
            seen.add(key)
            unique.append(choice)

        for row, choice in enumerate(unique):
            ctk.CTkLabel(
                body,
                text=choice.label,
                width=120,
                anchor="w",
                font=theme.font(theme.SMALL_SIZE),
            ).grid(row=row, column=0, padx=(10, 8), pady=6, sticky="w")
            ctk.CTkLabel(
                body,
                text=str(choice.path),
                anchor="w",
                font=theme.font(theme.SMALL_SIZE),
            ).grid(row=row, column=1, padx=8, pady=6, sticky="ew")
            ctk.CTkButton(
                body,
                text="Velg",
                width=72,
                command=lambda p=choice.path: self._choose(p),
                fg_color=theme.BUTTON_BG,
                hover_color=theme.BUTTON_HOVER,
            ).grid(row=row, column=2, padx=4, pady=6)
            if choice.removable and self._on_remove is not None:
                ctk.CTkButton(
                    body,
                    text="Slett fra historikk",
                    width=130,
                    command=lambda p=choice.path: self._remove(p),
                    fg_color=theme.BUTTON_BG,
                    hover_color=theme.BUTTON_HOVER,
                ).grid(row=row, column=3, padx=(4, 10), pady=6)

        if not unique:
            ctk.CTkLabel(
                body,
                text="Ingen gjeldende, foreslåtte eller tidligere steder er registrert.",
                font=theme.font(theme.NORMAL_SIZE),
                text_color=theme.TEXT_MUTED,
            ).grid(row=0, column=0, columnspan=4, padx=14, pady=24, sticky="w")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, padx=20, pady=(8, 18), sticky="ew")
        native_text = "Annen fil..." if kind == "file" else "Annen mappe..."
        ctk.CTkButton(
            footer,
            text=native_text,
            command=self._browse_native,
            width=130,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
        ).pack(side="left")
        ctk.CTkButton(
            footer,
            text="Avbryt",
            command=self.destroy,
            width=110,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
        ).pack(side="right")

    def _choose(self, path: Path) -> None:
        self.destroy()
        self._on_choose(path)

    def _remove(self, path: Path) -> None:
        if self._on_remove:
            self._on_remove(path)
        self.destroy()

    def _browse_native(self) -> None:
        kwargs = {"parent": self, "title": self.title()}
        initial = self._initial
        if initial:
            if self._kind == "file" and initial.is_file():
                initial = initial.parent
            elif not initial.is_dir():
                initial = initial.parent
            if initial.is_dir():
                kwargs["initialdir"] = str(initial)

        if self._kind == "file":
            kwargs["filetypes"] = self._filetypes
            value = filedialog.askopenfilename(**kwargs)
        else:
            value = filedialog.askdirectory(**kwargs)
        if value:
            self._choose(Path(value))


class SourceLocationDialog(StorageLocationDialog):
    """Backwards-compatible Source-specific wrapper around the common chooser."""

    def __init__(
        self,
        master,
        *,
        recent_dirs: list[Path],
        initial_dir: Path | None,
        on_choose: Callable[[Path], None],
        on_remove: Callable[[Path], None] | None = None,
    ) -> None:
        choices = [LocationChoice("Sist brukt", path, True) for path in recent_dirs]
        super().__init__(
            master,
            title="Velg Source – uttrekksmappe",
            heading="SOURCE – UTTAKK/STED",
            description="Velg et nylig brukt uttrekkssted eller en annen mappe.",
            choices=choices,
            initial_path=initial_dir,
            kind="dir",
            on_choose=on_choose,
            on_remove=on_remove,
        )
