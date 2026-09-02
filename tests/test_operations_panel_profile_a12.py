from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OperationsPanelProfileA12Tests(unittest.TestCase):
    def setUp(self):
        self.text = (
            ROOT / "gui" / "operations_panel.py"
        ).read_text(encoding="utf-8")

    def test_constructor_defines_categories_before_enumerating_them(self):
        definition = "categories = self.registry.categories()"
        enumeration = "for col, category in enumerate(categories):"
        self.assertIn(definition, self.text)
        self.assertIn(enumeration, self.text)
        self.assertLess(self.text.index(definition), self.text.index(enumeration))

    def test_active_category_comes_from_registry(self):
        self.assertIn(
            'self.active_category = categories[0] if categories else ""',
            self.text,
        )

    def test_panel_uses_registry_for_category_colors(self):
        self.assertIn(
            "self.registry.category_color(category, theme.BLUE)",
            self.text,
        )


if __name__ == "__main__":
    unittest.main()
