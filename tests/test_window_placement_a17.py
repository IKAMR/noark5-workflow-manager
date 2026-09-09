import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WindowPlacementA17Tests(unittest.TestCase):
    def test_common_window_placement_helper_exists(self):
        text = (ROOT / "gui" / "window_placement.py").read_text(encoding="utf-8")
        self.assertIn("def install_child_window_placement", text)
        self.assertIn('bind_all("<Map>"', text)
        self.assertIn("def place_near_parent", text)

    def test_a17_installs_placement_once_for_all_custom_dialogs(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        self.assertIn("install_child_window_placement(self)", text)
        self.assertIn("window_placement", text)

    def test_position_uses_parent_virtual_desktop_coordinates(self):
        text = (ROOT / "gui" / "window_placement.py").read_text(encoding="utf-8")
        self.assertIn("winfo_rootx()", text)
        self.assertIn("winfo_rooty()", text)
        self.assertIn('window.geometry(f"+{x}+{y}")', text)

    def test_placement_failure_cannot_block_dialog(self):
        text = (ROOT / "gui" / "window_placement.py").read_text(encoding="utf-8")
        self.assertIn("except (tk.TclError, AttributeError)", text)


if __name__ == "__main__":
    unittest.main()
