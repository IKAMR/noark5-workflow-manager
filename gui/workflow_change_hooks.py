from __future__ import annotations


def install_workflow_change_hooks(panel, callback) -> None:
    """Add a generic change callback to an existing WorkflowPanel instance.

    The hook wraps user-facing add/remove/clear methods only. Direct model
    population used while opening/restoring a job is therefore not treated as
    a user edit and does not trigger autosave.
    """
    if getattr(panel, "_n5wf_change_hooks_installed", False):
        panel._n5wf_on_change = callback
        return

    panel._n5wf_change_hooks_installed = True
    panel._n5wf_on_change = callback

    original_add = panel.add
    original_remove = panel.remove
    original_clear = panel.clear

    def changed(kind: str, operation_id=None):
        current = getattr(panel, "_n5wf_on_change", None)
        if callable(current):
            current(kind, operation_id)

    def add(operation_id):
        added = original_add(operation_id)
        if added:
            changed("add", operation_id)
        return added

    def remove(operation_id):
        before = tuple(panel.workflow.operation_ids())
        result = original_remove(operation_id)
        if tuple(panel.workflow.operation_ids()) != before:
            changed("remove", operation_id)
        return result

    def clear():
        before = tuple(panel.workflow.operation_ids())
        result = original_clear()
        if before and not panel.workflow.operation_ids():
            changed("clear", None)
        return result

    panel.add = add
    panel.remove = remove
    panel.clear = clear
