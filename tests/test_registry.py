import unittest

from noark5_workflow.app import build_registry


class RegistryTests(unittest.TestCase):
    def test_default_operations_registered(self):
        registry = build_registry()
        ids = {op.definition.operation_id for op in registry.all()}
        self.assertNotIn("detect_extraction", ids)
        self.assertIn("metadata_inventory", ids)
        self.assertIn("analyse_arkivstruktur", ids)
        self.assertIn("dias_package", ids)


if __name__ == "__main__":
    unittest.main()
