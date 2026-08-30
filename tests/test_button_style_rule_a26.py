import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestButtonStyleRule(unittest.TestCase):
    def test_dias_support_buttons_secondary(self):
        text=(ROOT/"gui/dias_dialog_a24.py").read_text(encoding="utf-8")
        pos=text.index('text="Velg mappe…"')
        self.assertIn("fg_color=theme.BUTTON_BG", text[pos:pos+400])
        pos=text.index('text="Les inn fra METS-fil …"')
        self.assertIn("fg_color=theme.BUTTON_BG", text[pos:pos+400])
    def test_rule_documented(self):
        text=(ROOT/"docs/INTERFACE.md").read_text(encoding="utf-8")
        self.assertIn("Primær (blå)",text); self.assertIn("Sekundær (mørk)",text); self.assertIn("Stopp/fare",text)
if __name__=="__main__": unittest.main()
