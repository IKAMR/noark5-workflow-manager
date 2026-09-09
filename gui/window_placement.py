from __future__ import annotations

import tkinter as tk


def _visible_toplevel(widget):
    """Return the nearest visible toplevel that should act as parent."""
    master = getattr(widget, "master", None)
    while master is not None:
        try:
            top = master.winfo_toplevel()
            if top is not widget and top.winfo_exists() and top.winfo_viewable():
                return top
        except tk.TclError:
            pass
        master = getattr(master, "master", None)
    return None


def place_near_parent(window, root) -> None:
    """Center a custom Tk/CTk dialog over its owning application window.

    Uses virtual desktop coordinates, so a parent on monitor 2/3 keeps its
    child dialog on that same monitor in normal multi-monitor layouts.
    """
    try:
        if getattr(window, "_n5wf_parent_positioned", False):
            return
        parent = _visible_toplevel(window) or root
        if parent is window or not parent.winfo_exists():
            return

        parent.update_idletasks()
        window.update_idletasks()

        pw = max(1, parent.winfo_width())
        ph = max(1, parent.winfo_height())
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()

        ww = max(1, window.winfo_width(), window.winfo_reqwidth())
        wh = max(1, window.winfo_height(), window.winfo_reqheight())

        x = px + max(0, (pw - ww) // 2)
        y = py + max(0, (ph - wh) // 2)

        window.geometry(f"+{x}+{y}")
        window._n5wf_parent_positioned = True
    except (tk.TclError, AttributeError):
        # Placement must never prevent a dialog from opening.
        return


def install_child_window_placement(root) -> None:
    """Position every later custom Toplevel relative to its current parent.

    One application-level binding covers Jobber, Mapper, Resultater,
    settings, project/location dialogs and later CTk/Tk dialogs without
    duplicating positioning code in each dialog class.
    """
    if getattr(root, "_n5wf_child_placement_installed", False):
        return
    root._n5wf_child_placement_installed = True

    def on_map(event):
        widget = getattr(event, "widget", None)
        if widget is None or widget is root:
            return
        try:
            if isinstance(widget, tk.Toplevel):
                root.after_idle(lambda w=widget: place_near_parent(w, root))
        except tk.TclError:
            return

    root.bind_all("<Map>", on_map, add="+")
