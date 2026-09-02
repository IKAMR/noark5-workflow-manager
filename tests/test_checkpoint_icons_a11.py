import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CheckpointIconsA11Tests(unittest.TestCase):
    def setUp(self):
        self.panel = (ROOT / "gui" / "workflow_panel.py").read_text(encoding="utf-8")

    def test_checkpoint_uses_media_stop_square_only_when_active(self):
        self.assertIn('text="■" if active_checkpoint else ""', self.panel)
        self.assertNotIn('text="Stopp etter"', self.panel)
        self.assertNotIn('text="Stopp ✓"', self.panel)

    def test_checkpoint_uses_checkpoint_terminology(self):
        self.assertIn('"Sett kontrollpunkt etter operasjonen"', self.panel)
        self.assertIn('"Fjern kontrollpunkt"', self.panel)

    def test_edit_action_uses_compact_pencil_icon(self):
        self.assertIn('text="✎"', self.panel)
        self.assertIn('"Rediger operasjonen"', self.panel)
        self.assertNotIn('text="Rediger"', self.panel)

    def test_remove_action_remains_independent(self):
        self.assertIn('text="×"', self.panel)
        self.assertIn('"Fjern operasjonen fra workflow"', self.panel)


if __name__ == "__main__":
    unittest.main()
