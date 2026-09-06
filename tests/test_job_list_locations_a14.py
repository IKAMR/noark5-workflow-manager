from pathlib import Path
import unittest

import settings

ROOT = Path(__file__).resolve().parents[1]


class JobListLocationsA14Tests(unittest.TestCase):
    def test_recent_job_list_dirs_has_default(self):
        self.assertIn("recent_job_list_dirs", settings.DEFAULT_CONFIG)
        self.assertEqual([], settings.DEFAULT_CONFIG["recent_job_list_dirs"])

    def test_runtime_keeps_recent_job_list_dirs_bounded(self):
        source = (ROOT / "gui" / "persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn('recent = recent[:10]', source)

    def test_project_local_job_lists_use_generic_wf_root(self):
        source = (ROOT / "gui" / "persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn("return project_dir(root)", source)
        self.assertNotIn('root / "n5wf"', source)
        self.assertNotIn('root / "wf" / "jobs"', source)

    def test_location_dialog_exposes_default_and_recent_locations(self):
        source = (ROOT / "gui" / "job_list_location_dialog.py").read_text(encoding="utf-8")
        self.assertIn('"Bruk standard"', source)
        self.assertIn('"Sist brukt"', source)
        self.assertIn('"Arbeid"', source)

    def test_job_list_file_remains_single_authoritative_path(self):
        source = (ROOT / "gui" / "persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertNotIn("copy_job_list", source)
        self.assertNotIn("mirror_job_list", source)

    def test_recent_job_list_files_has_default(self):
        self.assertIn("recent_job_list_files", settings.DEFAULT_CONFIG)
        self.assertEqual([], settings.DEFAULT_CONFIG["recent_job_list_files"])

    def test_open_dialog_supports_direct_file_open(self):
        source = (ROOT / "gui" / "job_list_location_dialog.py").read_text(encoding="utf-8")
        self.assertIn('mode == "open"', source)
        self.assertIn('text="Åpne"', source)
        self.assertIn("recent_files", source)

    def test_open_history_can_remove_file_without_deleting_file(self):
        source = (ROOT / "gui" / "job_list_location_dialog.py").read_text(encoding="utf-8")
        runtime = (ROOT / "gui" / "persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn('"Slett fra historikk"', source)
        self.assertIn("_forget_recent_job_list_file", runtime)
        self.assertNotIn("unlink(", runtime)

    def test_save_as_still_chooses_directory_then_filename(self):
        source = (ROOT / "gui" / "persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn("_save_job_list_as_in", source)
        self.assertIn("asksaveasfilename", source)

    def test_location_dialog_sizes_to_long_paths(self):
        source = (ROOT / "gui" / "job_list_location_dialog.py").read_text(encoding="utf-8")
        self.assertIn("_size_for_paths", source)
        self.assertIn("longest", source)


if __name__ == "__main__":
    unittest.main()
