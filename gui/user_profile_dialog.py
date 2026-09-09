from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from app.user_profile import UserProfile, save_user_profile
from version import APP_NAME
from . import theme


class UserProfileDialog(ctk.CTkToplevel):
    """Edit the three user-visible identity fields; user_id stays stable and internal."""

    def __init__(self, master, profile: UserProfile | None, on_saved, *, required: bool = False):
        super().__init__(master)
        self.profile = profile
        self.on_saved = on_saved
        self.required = required
        self.title("Brukerprofil")
        self.geometry("620x350")
        self.minsize(560, 320)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Brukerprofil", font=theme.font(theme.TITLE_SIZE, "bold"), text_color=theme.BLUE).grid(
            row=0, column=0, columnspan=2, padx=24, pady=(22, 8), sticky="w"
        )
        ctk.CTkLabel(
            self,
            text="Profilen lagres lokalt for denne brukeren og skal senere kunne knyttes til jobber, logger og serverkø.",
            font=theme.font(theme.SMALL_SIZE), text_color=theme.TEXT_MUTED, wraplength=540, justify="left",
        ).grid(row=1, column=0, columnspan=2, padx=24, pady=(0, 16), sticky="w")

        self.name_var = ctk.StringVar(value=profile.name if profile else "")
        self.username_var = ctk.StringVar(value=profile.username if profile else "")
        self.email_var = ctk.StringVar(value=profile.email if profile else "")
        for row, (label, var) in enumerate((("Navn", self.name_var), ("Brukernavn", self.username_var), ("E-post", self.email_var)), start=2):
            ctk.CTkLabel(self, text=label, font=theme.font(theme.NORMAL_SIZE)).grid(row=row, column=0, padx=(24, 12), pady=8, sticky="w")
            ctk.CTkEntry(self, textvariable=var, font=theme.font(theme.NORMAL_SIZE)).grid(row=row, column=1, padx=(0, 24), pady=8, sticky="ew")

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=5, column=0, columnspan=2, padx=24, pady=(20, 18), sticky="e")
        ctk.CTkButton(buttons, text="Avbryt", width=110, command=self._cancel, fg_color=theme.BUTTON_BG, hover_color=theme.BUTTON_HOVER).pack(side="left", padx=5)
        ctk.CTkButton(buttons, text="Lagre", width=130, command=self._save).pack(side="left", padx=5)

    def _cancel(self) -> None:
        if self.required and self.profile is None:
            if not messagebox.askyesno(APP_NAME, "Brukerprofil er ikke registrert. Avslutte programmet?"):
                return
            self.master.destroy()
            return
        self.destroy()

    def _save(self) -> None:
        try:
            profile = save_user_profile(
                self.name_var.get(), self.username_var.get(), self.email_var.get(), existing=self.profile
            )
        except (OSError, ValueError) as exc:
            messagebox.showerror(APP_NAME, str(exc), parent=self)
            return
        self.profile = profile
        self.on_saved(profile)
        self.destroy()
