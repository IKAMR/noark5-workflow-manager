from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RerunDialogA14Tests(unittest.TestCase):
    def test_generic_rerun_text_is_not_dias_specific(self):
        source = (ROOT / "gui" / "persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn("Tidligere resultater slettes ikke", source)
        self.assertIn("Den nye kjøringen dokumenteres som en ny hendelse", source)
        self.assertNotIn("En ny DIAS/AIC får ny identifikator", source)

    def test_dias_note_is_conditional(self):
        source = (ROOT / "gui" / "persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn('if any("dias_package" in job.workflow_ids for job in previous):', source)
        self.assertIn("DIAS/AIC-pakking oppretter en ny pakkeidentifikator", source)


if __name__ == "__main__":
    unittest.main()
