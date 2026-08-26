from noark5_workflow.core.registry import OperationRegistry
from noark5_workflow.operations import (
    AnalyseArkivstrukturOperation,
    DiasPackageOperation,
    MetadataInventoryOperation,
)


def build_registry() -> OperationRegistry:
    registry = OperationRegistry()
    # Uttrekksdeteksjon skjer automatisk i kildepanelet og er ikke en workflow-operasjon.
    registry.register(MetadataInventoryOperation())
    registry.register(AnalyseArkivstrukturOperation())
    registry.register(DiasPackageOperation())
    return registry
