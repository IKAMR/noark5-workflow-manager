from __future__ import annotations
from pathlib import Path
from tkinter import filedialog
from typing import Callable
import customtkinter as ctk
from . import theme

class SourceLocationDialog(ctk.CTkToplevel):
    def __init__(self, master, *, recent_dirs: list[Path], initial_dir: Path | None,
                 on_choose: Callable[[Path], None],
                 on_remove: Callable[[Path], None] | None = None) -> None:
        super().__init__(master)
        self.title("Velg Source – uttrekksmappe")
        self.geometry("1220x520")
        self.minsize(900, 420)
        self.transient(master); self.grab_set()
        self._on_choose=on_choose; self._on_remove=on_remove; self._initial=initial_dir
        self.grid_columnconfigure(0,weight=1); self.grid_rowconfigure(2,weight=1)
        ctk.CTkLabel(self,text="SOURCE – UTTAKK/STED",font=theme.font(theme.TITLE_SIZE,"bold"),
                     text_color=theme.BLUE).grid(row=0,column=0,padx=24,pady=(20,6),sticky="w")
        ctk.CTkLabel(self,text="Velg et nylig brukt uttrekkssted eller en annen mappe.",
                     font=theme.font(theme.SMALL_SIZE),text_color=theme.TEXT_MUTED
                     ).grid(row=1,column=0,padx=24,pady=(0,10),sticky="w")
        body=ctk.CTkScrollableFrame(self,fg_color=theme.PANEL_BG)
        body.grid(row=2,column=0,padx=20,pady=8,sticky="nsew"); body.grid_columnconfigure(1,weight=1)
        row=0
        for path in recent_dirs:
            ctk.CTkLabel(body,text="Sist brukt",width=90,anchor="w",
                         font=theme.font(theme.SMALL_SIZE)).grid(row=row,column=0,padx=(10,8),pady=6,sticky="w")
            ctk.CTkLabel(body,text=str(path),anchor="w",font=theme.font(theme.SMALL_SIZE)
                         ).grid(row=row,column=1,padx=8,pady=6,sticky="ew")
            ctk.CTkButton(body,text="Velg",width=72,command=lambda p=path:self._choose(p),
                          fg_color=theme.BUTTON_BG,hover_color=theme.BUTTON_HOVER
                          ).grid(row=row,column=2,padx=4,pady=6)
            ctk.CTkButton(body,text="Slett fra historikk",width=120,
                          command=lambda p=path:self._remove(p),
                          fg_color=theme.BUTTON_BG,hover_color=theme.BUTTON_HOVER
                          ).grid(row=row,column=3,padx=(4,10),pady=6)
            row+=1
        if not recent_dirs:
            ctk.CTkLabel(body,text="Ingen tidligere Source – uttrekksmapper registrert.",
                         font=theme.font(theme.NORMAL_SIZE),text_color=theme.TEXT_MUTED
                         ).grid(row=0,column=0,columnspan=4,padx=14,pady=24,sticky="w")
        footer=ctk.CTkFrame(self,fg_color="transparent")
        footer.grid(row=3,column=0,padx=20,pady=(8,18),sticky="ew")
        ctk.CTkButton(footer,text="Annen mappe...",command=self._browse,width=130,
                      fg_color=theme.BUTTON_BG,hover_color=theme.BUTTON_HOVER).pack(side="left")
        ctk.CTkButton(footer,text="Avbryt",command=self.destroy,width=110,
                      fg_color=theme.BUTTON_BG,hover_color=theme.BUTTON_HOVER).pack(side="right")

    def _choose(self,path:Path)->None:
        self.destroy(); self._on_choose(path)
    def _remove(self,path:Path)->None:
        if self._on_remove: self._on_remove(path)
        self.destroy()
    def _browse(self)->None:
        kwargs={"title":"Velg Source – uttrekksmappe"}
        if self._initial and self._initial.is_dir(): kwargs["initialdir"]=str(self._initial)
        folder=filedialog.askdirectory(**kwargs)
        if folder: self._choose(Path(folder))
