import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ThemeTooltipCompatibilityA17Tests(unittest.TestCase):
    def test_workflow_tooltip_theme_symbol_exists(self):
        theme = (ROOT / "gui" / "theme.py").read_text(encoding="utf-8")
        panel = (ROOT / "gui" / "workflow_panel.py").read_text(encoding="utf-8")
        self.assertIn("TEXT_MAIN = TEXT", theme)
        if "theme.TEXT_MAIN" in panel:
            self.assertIn("TEXT_MAIN = TEXT", theme)

    def test_main_text_colour_remains_single_authoritative_value(self):
        theme = (ROOT / "gui" / "theme.py").read_text(encoding="utf-8")
        self.assertIn('TEXT = "#d4daf0"', theme)
        self.assertIn("TEXT_MAIN = TEXT", theme)


if __name__ == "__main__":
    unittest.main()
