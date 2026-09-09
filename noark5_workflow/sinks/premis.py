from __future__ import annotations

from pathlib import Path

from noark5_workflow.core.events import WorkflowEvent
from noark5_workflow.core.premis_logger import PremisProvenanceLogger
from noark5_workflow.core.result_review import premis_eligible


class PremisEventSink:
    """PREMIS adapter for neutral WorkflowEvent instances.

    The executor no longer knows PREMIS details. Replacing this sink or adding
    another sink does not require changes to JobRunner/workflow execution.
    """

    sink_id = "premis"

    def __init__(self, settings: dict, definition=None) -> None:
        self.settings = settings
        self.definition = definition
        self._loggers: dict[str, PremisProvenanceLogger] = {}

    def _logger_for(self, operation, result, ctx) -> PremisProvenanceLogger | None:
        if not bool(self.settings.get("enable_premis_provenance", True)):
            return None
        if not premis_eligible(operation, result, ctx):
            return None
        try:
            requested_dir = operation.premis_output_dir(result, ctx)
        except Exception:
            requested_dir = None
        if not requested_dir:
            ctx.log("PREMIS: ingen eksplisitt utdatamappe - workflow-PREMIS skrives ikke")
            return None

        log_dir = Path(requested_dir).resolve()
        input_root = ctx.input_root.resolve()
        identity = ctx.settings.get("_current_user_identity")
        identity = identity if isinstance(identity, dict) else {}
        strategy = str(ctx.settings.get("premis_agent_identifier", "username") or "username")
        if strategy not in {"username", "user_id"}:
            strategy = "username"
        user_value = str(identity.get(strategy, "") or "").strip()
        user_name = str(identity.get("name", "") or "").strip()

        key = f"{log_dir}|{input_root}|{strategy}|{user_value}"
        logger = self._loggers.get(key)
        if logger is not None:
            ctx.metadata["premis_logger"] = logger
            ctx.metadata["premis_logger_key"] = key
            ctx.metadata["premis_object_root"] = input_root
            ctx.metadata["premis_output_dir"] = str(log_dir)
            return logger

        try:
            from version import VERSION
        except Exception:
            VERSION = ""

        logger = PremisProvenanceLogger(
            log_dir,
            input_root,
            agent_version=str(VERSION),
            user_agent_identifier_type=strategy,
            user_agent_identifier_value=user_value,
            user_agent_name=user_name,
        )
        self._loggers[key] = logger
        # Backward-compatible metadata bridge. PREMIS ownership stays in this
        # sink, but existing callers/tests may still inspect the active logger
        # through OperationContext.metadata.
        ctx.metadata["premis_logger"] = logger
        ctx.metadata["premis_logger_key"] = key
        ctx.metadata["premis_object_root"] = input_root
        ctx.metadata["premis_output_dir"] = str(log_dir)
        return logger

    def handle(self, event: WorkflowEvent, **runtime) -> None:
        if self.definition is not None and not self.definition.accepts(event.kind):
            return
        if self.definition is None and event.kind != "operation.completed":
            return
        operation = runtime.get("operation")
        result = runtime.get("result")
        ctx = runtime.get("ctx")
        if operation is None or result is None or ctx is None:
            return

        logger = self._logger_for(operation, result, ctx)
        if logger is None:
            return
        logger.record(operation, result, ctx)
        logger.finalize(ctx.input_root, ctx)

    def close(self, **runtime) -> None:
        return None
