from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from .context import OperationContext
from .result import OperationResult


class ExecutionTarget(str, Enum):
    LOCAL = "local"
    SERVER = "server"
    EITHER = "either"


@dataclass(frozen=True)
class OperationDefinition:
    operation_id: str
    name: str
    description: str
    execution_target: ExecutionTarget = ExecutionTarget.EITHER
    category: str = "Pipeline"
    status_level: int = 2


class BaseOperation(ABC):
    definition: OperationDefinition

    # PREMIS-proveniens. Dette er med hensikt uavhengig av om operasjonen
    # endrer Noark 5-uttrekket: Noark-kilden skal normalt være read-only, mens
    # relevante validerings-/bevaringshendelser likevel kan dokumenteres.
    premis_record: bool = False
    premis_event_type: str = "Adjustment"
    premis_event_label: str = ""

    def can_run(self, ctx: OperationContext) -> tuple[bool, str]:
        return True, ""

    def premis_should_record(self, result: OperationResult, ctx: OperationContext) -> bool:
        """Standard: registrer bare vellykkede hendelser som er slått på."""
        return bool(self.premis_record and result.ok)

    def premis_detail(self, result: OperationResult, ctx: OperationContext) -> str:
        """Menneskelesbar hendelsesdetalj for PREMIS."""
        return result.message or ""

    def premis_output_dir(self, result: OperationResult, ctx: OperationContext):
        """Returner mappe for workflow-PREMIS, eller None hvis ingen er valgt.

        Kildeområdet skal aldri brukes som implisitt fallback. En operasjon kan
        overstyre dette (for eksempel DIAS-pakking), eller en eksplisitt
        workflow/PREMIS-utdatamappe kan ligge i settings.
        """
        from pathlib import Path

        configured = str(
            ctx.settings.get("workflow_output_dir")
            or ctx.settings.get("premis_output_dir")
            or ""
        ).strip()
        return Path(configured) if configured else None

    @abstractmethod
    def run(self, ctx: OperationContext) -> OperationResult:
        raise NotImplementedError
