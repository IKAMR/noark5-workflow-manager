from pathlib import Path
import unittest
import settings
ROOT=Path(__file__).resolve().parents[1]

class A15ProfileSourceFixTests(unittest.TestCase):
    def test_generic_source_history_keys_exist(self):
        self.assertIn("last_source_extraction_dir",settings.DEFAULT_CONFIG)
        self.assertIn("recent_source_extraction_dirs",settings.DEFAULT_CONFIG)
        self.assertIn("last_profile_id",settings.DEFAULT_CONFIG)

    def test_source_panel_is_generic_without_profile(self):
        text=(ROOT/"gui"/"source_panel.py").read_text(encoding="utf-8")
        self.assertIn('text="SOURCE"',text)
        self.assertIn('self.profile_id!="noark5"',text)
        self.assertIn("SourceLocationDialog",text)

    def test_profile_menu_has_noark_and_siard(self):
        text=(ROOT/"gui"/"persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn('"Noark 5":"noark5"',text)
        self.assertIn('"SIARD":"siard"',text)
        self.assertIn("_apply_profile",text)

    def test_source_browse_opens_storage_roles(self):
        text=(ROOT/"gui"/"persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn("_source_browse_complete",text)
        self.assertIn("self._show_storage_roles(job)",text)
        self.assertIn("source_extraction = path",text)

    def test_save_as_new_master_clears_visible_log(self):
        text=(ROOT/"gui"/"persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn("self.log_panel.clear()",text)
        self.assertIn("visningsloggen er nullstilt",text)

    def test_project_profile_is_not_hardcoded_noark5(self):
        text=(ROOT/"gui"/"persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn('profile_id=self.active_profile_id or "generic"',text)

    def test_method_observation_records_regression_rule(self):
        text=(ROOT/"docs"/"METHOD-OBSERVATIONS.md").read_text(encoding="utf-8")
        self.assertIn("MO-005",text)
        self.assertIn("MO-006",text)

if __name__=="__main__": unittest.main()
