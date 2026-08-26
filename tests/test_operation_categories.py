import unittest

from noark5_workflow.app import build_registry


class OperationCategoryTests(unittest.TestCase):
    def test_categories_and_filtering(self):
        registry = build_registry()
        self.assertEqual(registry.get("metadata_inventory").definition.category, "Metadata")
        self.assertEqual(registry.get("analyse_arkivstruktur").definition.category, "Metadata")
        self.assertEqual(registry.get("dias_package").definition.category, "SIP/AIC-Pakking")
        metadata_ids = {op.definition.operation_id for op in registry.by_category("Metadata")}
        self.assertEqual(metadata_ids, {"metadata_inventory", "analyse_arkivstruktur"})
        packing_ids = {op.definition.operation_id for op in registry.by_category("SIP/AIC-Pakking")}
        self.assertEqual(packing_ids, {"dias_package"})


if __name__ == "__main__":
    unittest.main()
