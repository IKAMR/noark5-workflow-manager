from noark5_workflow.core.registry import OperationRegistry
from noark5_workflow.profile import NOARK5_PROFILE

def build_registry() -> OperationRegistry:
    return NOARK5_PROFILE.build_registry()
