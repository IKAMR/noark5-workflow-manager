from noark5_workflow.core.registry import OperationRegistry
from noark5_workflow.operations import (
    AnalyseArkivstrukturOperation,
    DetectExtractionOperation,
    MetadataInventoryOperation,
)


def build_registry() -> OperationRegistry:
    registry = OperationRegistry()
    registry.register(DetectExtractionOperation())
    registry.register(MetadataInventoryOperation())
    registry.register(AnalyseArkivstrukturOperation())
    return registry
