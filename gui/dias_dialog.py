from __future__ import annotations

import datetime
import json
import tkinter as tk
import tkinter.ttk as ttk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk

from noark5_workflow.operations.dias_mets import read_meta_from_mets
from noark5_workflow.operations.dias_package import DEFAULT_PARAMS
from settings import load_config, save_config
from . import theme


_FIELDS = [
    ("submission_agreement", "Submission Agreement"),
    ("label", "Pakketittel"),
    ("system", "Kildesystem"),
    ("system_version", "Systemversjon"),
    ("archivist_type", "Arkivtype"),
    ("period_start", "Periodens start (ÅÅÅÅ-MM-DD)"),
    ("period_end", "Periodens slutt (ÅÅÅÅ-MM-DD)"),
    ("owner_org", "Eierorganisasjon"),
    ("archivist_org", "Arkivorganisasjon"),
    ("submitter_org", "Avleverende organisasjon"),
    ("submitter_person", "Avleverende person"),
    ("producer_org", "Produsent (org)"),
    ("producer_person", "Produsent (person)"),
    ("producer_software", "Produsent (programvare)"),
    ("creator", "Skaper"),
    ("preserver", "Bevaringsansvarlig"),
]

_REQUIRED = {key for key, _ in _FIELDS}

_DESTINATIONS = {
    "content": "content",
    "adm": "administrative_metadata",
    "repo_ops": "administrative_metadata/repository_operations",
    "desc": "descriptive_metadata",
}


class DiasParamDialog(ctk.CTkToplevel):
    """Konfigurerer DIAS-pakken uten å endre kildefilene på disk."""

    def __init__(
        self,
        parent,
        initial: dict,
        extraction_root: Path | None,
        on_confirm: Callable[[dict], bool | None],
    ) -> None:
        super().__init__(parent)
        self.title("DIAS-pakking: Konfigurer pakke")
        self.geometry("1160x780")
        self.minsize(960, 640)
        self.resizable(True, True)
        self.configure(fg_color=theme.APP_BG)
        self.transient(parent)
        self.grab_set()

        self.on_confirm = on_confirm
        self.extraction_root = Path(extraction_root) if extraction_root else None
        self.settings = load_config()
        self.vars: dict[str, ctk.StringVar] = {}
        self.entries: dict[str, ctk.CTkEntry] = {}
        self.values = {**DEFAULT_PARAMS, **(initial or {})}
        self.extra_files: list[dict[str, str]] = self._load_extra_files(
            self.values.get("extra_files", "[]")
        )
        self._folder_ids: dict[str, str] = {}
        self._manual_items: dict[str, int] = {}
        self._tree_destinations: dict[str, str] = {}

        if self.extraction_root:
            self.values["label"] = self.values.get("label") or self.extraction_root.name
        if not self.values.get("output_dir"):
            remembered_output = str(self.settings.get("last_dias_output_dir", "")).strip()
            if remembered_output:
                self.values["output_dir"] = remembered_output
            elif self.extraction_root:
                self.values["output_dir"] = str(self.extraction_root.parent)

        self._build()
        self._populate_tree()

    @staticmethod
    def _load_extra_files(value) -> list[dict[str, str]]:
        try:
            items = json.loads(value) if isinstance(value, str) else list(value or [])
        except Exception:
            return []
        result: list[dict[str, str]] = []
        for item in items:
            if not isinstance(item, dict) or not item.get("dest"):
                continue
            kind = str(item.get("kind", "file"))
            src = str(item.get("src", ""))
            if kind in ("file", "folder") and not src:
                continue
            if kind not in ("file", "folder", "empty_folder"):
                continue
            result.append(
                {
                    "kind": kind,
                    "src": src,
                    "dest": str(item["dest"]).replace("\\", "/").rstrip("/"),
                }
            )
        return result

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=2, minsize=500)
        self.grid_columnconfigure(1, weight=1, minsize=320)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text="DIAS-PAKKING (SIP/AIC)",
            font=theme.font(theme.TITLE_SIZE, "bold"),
            text_color=theme.BLUE,
        ).grid(row=0, column=0, columnspan=2, padx=20, pady=(12, 6), sticky="w")

        left = ctk.CTkFrame(self, fg_color=theme.SURFACE_BG, corner_radius=8)
        left.grid(row=1, column=0, padx=(16, 6), pady=(0, 8), sticky="nsew")
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            left,
            text="METADATA",
            font=theme.font(theme.SECTION_SIZE, "bold"),
            text_color=theme.TEXT_MUTED,
        ).grid(row=0, column=0, padx=14, pady=(8, 2), sticky="w")
        self._build_form(left)

        right = ctk.CTkFrame(self, fg_color=theme.SURFACE_BG, corner_radius=8)
        right.grid(row=1, column=1, padx=(6, 16), pady=(0, 8), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            right,
            text="PAKKESTRUKTUR",
            font=theme.font(theme.SECTION_SIZE, "bold"),
            text_color=theme.TEXT_MUTED,
        ).grid(row=0, column=0, padx=14, pady=(8, 2), sticky="w")
        self._build_tree_panel(right)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="e")
        ctk.CTkButton(
            buttons,
            text="Avbryt",
            width=100,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            font=theme.font(theme.NORMAL_SIZE),
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            buttons,
            text="Legg til i workflow",
            width=170,
            fg_color=theme.BLUE,
            hover_color=theme.BLUE_DIM,
            font=theme.font(theme.NORMAL_SIZE, "bold"),
            command=self._confirm,
        ).pack(side="left")

    def _build_form(self, parent: ctk.CTkFrame) -> None:
        form = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        form.grid(row=1, column=0, padx=10, pady=(2, 10), sticky="nsew")
        form.grid_columnconfigure(0, weight=0)
        form.grid_columnconfigure(1, weight=1)

        # Utdatamappe: knapp til venstre og to-linjers path til høyre.
        ctk.CTkLabel(
            form,
            text="Utdatamappe",
            font=theme.font(theme.SMALL_SIZE, "bold"),
            text_color=theme.BLUE,
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(6, 3), sticky="w")

        self.output_row = ctk.CTkFrame(form, fg_color="transparent")
        self.output_row.grid(
            row=1, column=0, columnspan=2, padx=10, pady=(0, 12), sticky="ew"
        )
        self.output_row.grid_columnconfigure(1, weight=1)

        self.vars["output_dir"] = ctk.StringVar(
            value=str(self.values.get("output_dir", ""))
        )

        self.choose_output_button = ctk.CTkButton(
            self.output_row,
            text="Velg mappe…",
            width=120,
            command=self._browse_output,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            font=theme.font(theme.SMALL_SIZE),
        )
        self.choose_output_button.grid(
            row=0, column=0, padx=(0, 10), pady=0, sticky="nw"
        )

        self.output_display = ctk.CTkTextbox(
            self.output_row,
            height=58,
            wrap="char",
            font=theme.font(theme.SMALL_SIZE),
        )
        self.output_display.grid(
            row=0, column=1, padx=0, pady=0, sticky="ew"
        )
        self._refresh_output_display()

        mets_row = ctk.CTkFrame(form, fg_color="transparent")
        mets_row.grid(row=2, column=0, columnspan=2, padx=6, pady=(2, 10), sticky="w")
        ctk.CTkButton(
            mets_row,
            text="Les inn fra METS-fil …",
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            font=theme.font(theme.SMALL_SIZE),
            command=self._load_from_mets,
        ).pack(side="left")
        ctk.CTkLabel(
            mets_row,
            text="  info.xml, mets.xml eller annen METS XML",
            font=theme.font(theme.SMALL_SIZE),
            text_color=theme.TEXT_MUTED,
        ).pack(side="left")

        for row, (key, label) in enumerate(_FIELDS, start=3):
            ctk.CTkLabel(
                form,
                text=label,
                font=theme.font(theme.SMALL_SIZE),
                text_color=theme.TEXT_SUB,
            ).grid(row=row, column=0, padx=(10, 8), pady=5, sticky="w")
            var = ctk.StringVar(value=str(self.values.get(key, "")))
            self.vars[key] = var
            entry = ctk.CTkEntry(
                form, textvariable=var, font=theme.font(theme.SMALL_SIZE)
            )
            entry.grid(row=row, column=1, padx=(0, 12), pady=5, sticky="ew")
            self.entries[key] = entry
            if key in ("period_start", "period_end"):
                entry.bind(
                    "<FocusOut>",
                    lambda _event, k=key: self._validate_date(k, show_message=False),
                )

    def _build_tree_panel(self, parent: ctk.CTkFrame) -> None:
        holder = tk.Frame(parent, bg=theme.SURFACE_BG, highlightthickness=0)
        holder.grid(row=1, column=0, padx=12, pady=(4, 6), sticky="nsew")
        holder.grid_rowconfigure(0, weight=1)
        holder.grid_columnconfigure(0, weight=1)

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Dias.Treeview",
            background=theme.PANEL_BG_DARK,
            fieldbackground=theme.PANEL_BG_DARK,
            foreground=theme.TEXT,
            borderwidth=0,
            rowheight=max(22, theme.FontRegistry.effective_size(theme.SMALL_SIZE) + 12),
            font=(
                theme.FONT_FAMILY,
                theme.FontRegistry.effective_size(theme.SMALL_SIZE),
            ),
        )
        style.map("Dias.Treeview", background=[("selected", theme.BLUE_DIM)])

        self.tree = ttk.Treeview(holder, show="tree", style="Dias.Treeview")
        scroll = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        controls = ctk.CTkFrame(parent, fg_color="transparent")
        controls.grid(row=2, column=0, padx=12, pady=(2, 4), sticky="ew")
        ctk.CTkButton(
            controls,
            text="+  Legg til fil",
            width=105,
            command=self._add_file,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            font=theme.font(theme.SMALL_SIZE),
        ).pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            controls,
            text="+  Legg til mappe",
            width=120,
            command=self._add_folder,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            font=theme.font(theme.SMALL_SIZE),
        ).pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            controls,
            text="+  Opprett mappe",
            width=120,
            command=self._create_folder,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            font=theme.font(theme.SMALL_SIZE),
        ).pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            controls,
            text="Fjern",
            width=70,
            command=self._remove_file,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            font=theme.font(theme.SMALL_SIZE),
        ).pack(side="left")
        ctk.CTkButton(
            controls,
            text="Oppdater",
            width=90,
            command=self._populate_tree,
            fg_color=theme.BUTTON_BG,
            hover_color=theme.BUTTON_HOVER,
            font=theme.font(theme.SMALL_SIZE),
        ).pack(side="right")

        ctk.CTkLabel(
            parent,
            text=(
                "Velg målmappe i treet før du legger til fil/mappe eller oppretter mappe. "
                "Uten valg brukes administrative_metadata/repository_operations/. "
                "Tillegg pakkes inn, men kildene på disk endres ikke."
            ),
            wraplength=350,
            justify="left",
            font=theme.font(theme.SMALL_SIZE),
            text_color=theme.TEXT_MUTED,
        ).grid(row=3, column=0, padx=12, pady=(2, 10), sticky="w")

    def _insert_folder(
        self, parent: str, key: str, text: str, open_: bool = True
    ) -> str:
        item = self.tree.insert(
            parent, "end", text=text, open=open_, tags=("folder", key)
        )
        self._folder_ids[key] = item
        if key in _DESTINATIONS:
            self._tree_destinations[item] = _DESTINATIONS[key]
        return item

    def _populate_tree(self) -> None:
        if not hasattr(self, "tree"):
            return
        self.tree.delete(*self.tree.get_children())
        self._folder_ids.clear()
        self._manual_items.clear()
        self._tree_destinations.clear()

        root = self.tree.insert(
            "", "end", text="DIAS SIP/AIC", open=True, tags=("root",)
        )
        content = self._insert_folder(root, "content", "content/")
        adm = self._insert_folder(root, "adm", "administrative_metadata/")
        repo_ops = self._insert_folder(adm, "repo_ops", "repository_operations/")
        desc = self._insert_folder(root, "desc", "descriptive_metadata/")
        self.tree.insert(
            root, "end", text="info.xml  [genereres]", tags=("generated",)
        )
        self.tree.insert(
            root, "end", text="log.xml  [genereres]", tags=("generated",)
        )

        if not self.extraction_root or not self.extraction_root.exists():
            self.tree.insert(
                content,
                "end",
                text="[ingen Noark 5-kilde valgt]",
                tags=("source",),
            )
        else:
            source = self.tree.insert(
                content,
                "end",
                text=f"{self.extraction_root.name}/  [kilde]",
                open=True,
                tags=("source",),
            )
            try:
                children = sorted(
                    self.extraction_root.iterdir(),
                    key=lambda p: (not p.is_dir(), p.name.lower()),
                )
            except OSError as exc:
                self.tree.insert(
                    source,
                    "end",
                    text=f"[kunne ikke lese: {exc}]",
                    tags=("source",),
                )
            else:
                for child in children:
                    label = f"{child.name}/" if child.is_dir() else child.name
                    self.tree.insert(source, "end", text=label, tags=("source",))

        folder_by_dest = {
            "content": content,
            "administrative_metadata": adm,
            "administrative_metadata/repository_operations": repo_ops,
            "descriptive_metadata": desc,
        }

        def ensure_dest_folder(dest_dir: str) -> str:
            if dest_dir in folder_by_dest:
                return folder_by_dest[dest_dir]
            roots = sorted(folder_by_dest, key=len, reverse=True)
            root_key = next(
                (
                    r
                    for r in roots
                    if dest_dir == r or dest_dir.startswith(r + "/")
                ),
                "administrative_metadata/repository_operations",
            )
            parent_item = folder_by_dest[root_key]
            current = root_key
            suffix = dest_dir[len(root_key) :].strip("/")
            for part in [p for p in suffix.split("/") if p]:
                current = f"{current}/{part}"
                if current not in folder_by_dest:
                    node = self.tree.insert(
                        parent_item,
                        "end",
                        text=f"{part}/  [manuelt]",
                        open=True,
                        tags=("manual_folder",),
                    )
                    folder_by_dest[current] = node
                    self._tree_destinations[node] = current
                parent_item = folder_by_dest[current]
            return parent_item

        for index, extra in enumerate(self.extra_files):
            dest = extra["dest"].replace("\\", "/").lstrip("/").rstrip("/")
            kind = extra.get("kind", "file")
            if kind in ("folder", "empty_folder"):
                parent_dir = (
                    dest.rsplit("/", 1)[0] if "/" in dest else "content"
                )
                parent = ensure_dest_folder(parent_dir)
                name = dest.rsplit("/", 1)[-1]
                label = "[mappe]" if kind == "folder" else "[opprettet]"
                item = self.tree.insert(
                    parent,
                    "end",
                    text=f"{name}/  {label}",
                    open=True,
                    tags=("manual_folder", "manual"),
                )
                self._tree_destinations[item] = dest
                self._manual_items[item] = index
                if kind == "folder":
                    src = Path(extra.get("src", ""))
                    if src.is_dir():
                        try:
                            children = sorted(
                                src.iterdir(),
                                key=lambda p: (not p.is_dir(), p.name.lower()),
                            )
                            for child in children:
                                child_label = (
                                    f"{child.name}/"
                                    if child.is_dir()
                                    else child.name
                                )
                                self.tree.insert(
                                    item,
                                    "end",
                                    text=child_label,
                                    tags=("manual_preview",),
                                )
                        except OSError:
                            pass
            else:
                dest_dir = (
                    dest.rsplit("/", 1)[0] if "/" in dest else "content"
                )
                parent = ensure_dest_folder(dest_dir)
                item = self.tree.insert(
                    parent,
                    "end",
                    text=f"{Path(extra['src']).name}  [manuelt]",
                    tags=("manual",),
                )
                self._manual_items[item] = index

    def _selected_destination(self) -> str:
        sel = self.tree.focus()
        while sel:
            if sel in self._tree_destinations:
                return self._tree_destinations[sel]
            tags = set(self.tree.item(sel, "tags"))
            for key in _DESTINATIONS:
                if key in tags:
                    return _DESTINATIONS[key]
            sel = self.tree.parent(sel)
        return _DESTINATIONS["repo_ops"]

    def _initial_dir(
        self, key: str, fallback: str | Path | None = None
    ) -> str | None:
        value = str(self.settings.get(key, "")).strip()
        if value and Path(value).is_dir():
            return value
        if fallback:
            path = Path(fallback)
            if path.is_dir():
                return str(path)
            if path.parent.is_dir():
                return str(path.parent)
        return None

    def _remember_dir(self, key: str, folder: str | Path) -> None:
        value = str(folder)
        self.settings[key] = value
        save_config({key: value})

    def _add_file(self) -> None:
        kwargs = {"title": "Legg til fil i DIAS-pakken", "parent": self}
        initialdir = self._initial_dir("last_dias_add_file_dir")
        if initialdir:
            kwargs["initialdir"] = initialdir
        path = filedialog.askopenfilename(**kwargs)
        if not path:
            return
        self._remember_dir("last_dias_add_file_dir", Path(path).parent)
        dest_dir = self._selected_destination()
        fname = Path(path).name
        dest = f"{dest_dir}/{fname}" if dest_dir else fname
        self.extra_files.append(
            {"kind": "file", "src": path, "dest": dest}
        )
        self._populate_tree()

    def _add_folder(self) -> None:
        kwargs = {"title": "Legg til mappe i DIAS-pakken", "parent": self}
        initialdir = self._initial_dir("last_dias_add_folder_dir")
        if initialdir:
            kwargs["initialdir"] = initialdir
        path = filedialog.askdirectory(**kwargs)
        if not path:
            return
        self._remember_dir("last_dias_add_folder_dir", path)
        dest_dir = self._selected_destination()
        name = Path(path).name
        dest = f"{dest_dir}/{name}" if dest_dir else name
        self.extra_files.append(
            {"kind": "folder", "src": path, "dest": dest}
        )
        self._populate_tree()

    def _create_folder(self) -> None:
        from tkinter import simpledialog

        name = simpledialog.askstring(
            "Opprett mappe",
            "Mappenavn i DIAS-pakken:",
            parent=self,
        )
        if not name:
            return
        name = name.strip().replace("\\", "/").strip("/")
        if not name or "/" in name or name in (".", ".."):
            messagebox.showwarning(
                "DIAS-pakking",
                "Oppgi ett gyldig mappenavn uten skråstrek.",
                parent=self,
            )
            return
        dest_dir = self._selected_destination()
        dest = f"{dest_dir}/{name}" if dest_dir else name
        if any(
            item.get("dest", "").rstrip("/") == dest
            for item in self.extra_files
        ):
            messagebox.showwarning(
                "DIAS-pakking",
                f"Mappen finnes allerede i pakkeoppsettet: {dest}",
                parent=self,
            )
            return
        self.extra_files.append(
            {"kind": "empty_folder", "src": "", "dest": dest}
        )
        self._populate_tree()

    def _remove_file(self) -> None:
        sel = self.tree.focus()
        index = self._manual_items.get(sel)
        if index is None:
            messagebox.showinfo(
                "DIAS-pakking",
                "Velg en manuelt lagt til fil eller mappe for å fjerne den fra pakkeoppsettet.",
                parent=self,
            )
            return
        if 0 <= index < len(self.extra_files):
            self.extra_files.pop(index)
        self._populate_tree()

    def _load_from_mets(self) -> None:
        kwargs = {
            "title": "Velg METS-fil",
            "filetypes": [("XML-filer", "*.xml"), ("Alle filer", "*.*")],
            "parent": self,
        }
        initialdir = self._initial_dir("last_mets_import_dir")
        if initialdir:
            kwargs["initialdir"] = initialdir
        path = filedialog.askopenfilename(**kwargs)
        if not path:
            return
        self._remember_dir("last_mets_import_dir", Path(path).parent)
        try:
            meta = read_meta_from_mets(path)
        except Exception as exc:
            messagebox.showerror("Feil ved innlesing", str(exc), parent=self)
            return

        defaults = {**DEFAULT_PARAMS}
        if self.extraction_root:
            defaults["label"] = self.extraction_root.name
        for key, _label in _FIELDS:
            if key in self.vars:
                self.vars[key].set(str(defaults.get(key, "")))
        for key, value in meta.items():
            if key in self.vars:
                self.vars[key].set(value)

        messagebox.showinfo(
            "METS lest inn",
            f"Leste {len(meta)} gjenkjente metadatafelt fra:\n{Path(path).name}",
            parent=self,
        )

    def _refresh_output_display(self) -> None:
        if not hasattr(self, "output_display"):
            return
        self.output_display.configure(state="normal")
        self.output_display.delete("1.0", "end")
        self.output_display.insert("1.0", self.vars["output_dir"].get())
        self.output_display.configure(state="disabled")

    def _browse_output(self) -> None:
        kwargs = {
            "title": "Velg utdatamappe for DIAS-pakke",
            "parent": self,
        }
        initialdir = self._initial_dir(
            "last_dias_output_dir",
            self.vars.get("output_dir").get().strip()
            if self.vars.get("output_dir")
            else None,
        )
        if initialdir:
            kwargs["initialdir"] = initialdir
        folder = filedialog.askdirectory(**kwargs)
        if folder:
            self.vars["output_dir"].set(folder)
            self._refresh_output_display()
            self._remember_dir("last_dias_output_dir", folder)

    def _validate_date(self, key: str, show_message: bool) -> bool:
        value = self.vars[key].get().strip()
        entry = self.entries.get(key)
        if not value:
            if entry:
                entry.configure(border_color=theme.CARD_BORDER)
            return False
        try:
            datetime.datetime.strptime(value, "%Y-%m-%d")
            ok = True
        except ValueError:
            try:
                datetime.datetime.strptime(value, "%Y")
                suffix = "-01-01" if key == "period_start" else "-12-31"
                self.vars[key].set(value + suffix)
                ok = True
            except ValueError:
                ok = False
        if entry:
            entry.configure(
                border_color=theme.CARD_BORDER if ok else theme.DANGER_TEXT
            )
        if show_message and not ok:
            messagebox.showwarning(
                "DIAS-pakking",
                "Dato må være ÅÅÅÅ-MM-DD (eller bare ÅÅÅÅ).",
                parent=self,
            )
        return ok

    def _confirm(self) -> None:
        if not self._validate_date("period_start", show_message=True):
            return
        if not self._validate_date("period_end", show_message=True):
            return

        values = {key: var.get().strip() for key, var in self.vars.items()}
        missing = [key for key in _REQUIRED if not values.get(key)]
        if missing:
            labels = dict(_FIELDS)
            readable = ", ".join(labels.get(key, key) for key in missing)
            messagebox.showwarning(
                "DIAS-pakking",
                "Fyll ut alle obligatoriske felt før operasjonen legges til."
                f"\n\nMangler: {readable}",
                parent=self,
            )
            return

        start = datetime.datetime.strptime(
            values["period_start"], "%Y-%m-%d"
        ).date()
        end = datetime.datetime.strptime(
            values["period_end"], "%Y-%m-%d"
        ).date()
        if end < start:
            messagebox.showwarning(
                "DIAS-pakking",
                "Periodens slutt kan ikke være før periodens start.",
                parent=self,
            )
            return

        if values.get("output_dir"):
            self._remember_dir("last_dias_output_dir", values["output_dir"])
        values["extra_files"] = json.dumps(
            self.extra_files, ensure_ascii=False
        )

        accepted = self.on_confirm(values)
        if accepted is False:
            return

        self.destroy()
