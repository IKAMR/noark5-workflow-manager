from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk

from noark5_workflow.core.job import Job
from . import theme

_FIELDS = (
    ("source_root", "Source – hovedmappe", "dir"),
    ("source_tar", "Source – TAR", "file"),
    ("source_unzipped", "Source – utpakket", "dir"),
    ("source_extraction", "Source – uttrekksmappe", "dir"),
    ("work_root", "Arbeid – hovedmappe", "dir"),
    ("work_content", "Arbeid – content", "dir"),
    ("work_operations", "Arbeid – operasjoner", "dir"),
    ("archive_root", "Arkiv – hovedmappe", "dir"),
)

class StorageRolesDialog(ctk.CTkToplevel):
    """Edit generic storage-role paths for one job; no physical layout is imposed."""
    def __init__(self, master, job: Job, on_save) -> None:
        super().__init__(master); self.job=job; self.on_save=on_save; self.vars={}
        self.title(f"Mapper – {job.job_id}"); self.geometry("1320x600"); self.minsize(1080,520)
        self.configure(fg_color=theme.APP_BG); self.transient(master); self.grab_set()
        self.grid_columnconfigure(0,weight=0); self.grid_columnconfigure(1,weight=1); self.grid_columnconfigure(2,weight=0)
        ctk.CTkLabel(self,text="MAPPE-ROLLER",font=theme.font(theme.TITLE_SIZE,"bold"),text_color=theme.BLUE).grid(row=0,column=0,columnspan=3,padx=18,pady=(16,4),sticky="w")
        ctk.CTkLabel(self,text="Roller per jobb. Ingen fysisk DIAS- eller depotstruktur tvinges av disse feltene.",font=theme.font(theme.SMALL_SIZE),text_color=theme.TEXT_MUTED).grid(row=1,column=0,columnspan=3,padx=18,pady=(0,12),sticky="w")
        for row,(attr,label,kind) in enumerate(_FIELDS,start=2):
            ctk.CTkLabel(self,text=label,width=210,font=theme.font(theme.SMALL_SIZE),anchor="w").grid(row=row,column=0,padx=(18,8),pady=5,sticky="w")
            value=getattr(job,attr); var=ctk.StringVar(value=str(value) if value else ""); self.vars[attr]=var
            ctk.CTkEntry(self,textvariable=var,font=theme.font(theme.SMALL_SIZE)).grid(row=row,column=1,padx=4,pady=5,sticky="ew")
            ctk.CTkButton(self,text="Velg...",width=76,fg_color=theme.BUTTON_BG,hover_color=theme.BUTTON_HOVER,command=lambda a=attr,k=kind:self._choose(a,k)).grid(row=row,column=2,padx=(8,18),pady=5)
        buttons=ctk.CTkFrame(self,fg_color="transparent"); buttons.grid(row=20,column=0,columnspan=3,padx=18,pady=18,sticky="e")
        ctk.CTkButton(buttons,text="Avbryt",width=90,fg_color=theme.BUTTON_BG,hover_color=theme.BUTTON_HOVER,command=self.destroy).pack(side="left",padx=4)
        ctk.CTkButton(buttons,text="Lagre",width=90,fg_color=theme.BLUE_DIM,hover_color=theme.BLUE,command=self._save).pack(side="left",padx=4)

    def _choose(self, attr: str, kind: str) -> None:
        current=self.vars[attr].get().strip(); initial=None
        if current:
            p=Path(current); initial=str(p if p.is_dir() else p.parent)
        if kind == "file":
            value=filedialog.askopenfilename(parent=self,title="Velg TAR",initialdir=initial,filetypes=[("TAR", "*.tar"),("Alle filer","*.*")])
        else:
            value=filedialog.askdirectory(parent=self,title="Velg mappe",initialdir=initial)
        if value: self.vars[attr].set(value)

    def _save(self) -> None:
        values={name:(Path(text) if (text:=var.get().strip()) else None) for name,var in self.vars.items()}
        if values["source_root"] is None: values["source_root"]=self.job.source_root
        self.on_save(values); self.destroy()
