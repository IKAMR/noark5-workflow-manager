from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from noark5_workflow.core.project_config import (
    FILE_NAME,
    ProjectConfigError,
    is_project_job_list_path,
    load_project,
    project_dir,
    save_project,
)

ROOT = Path(__file__).resolve().parents[1]


class ProjectConfigA14Tests(unittest.TestCase):
    def test_project_dir_is_generic_wf_root(self):
        root = Path("work") / "repository_operations"
        self.assertEqual(project_dir(root), root / "wf")
        self.assertEqual(FILE_NAME, "project.json")

    def test_project_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "wf" / "project.json"
            save_project(
                path,
                project_name="1502_030",
                profile_id="noark5",
                job_profile_id=None,
                job_list_file="1502_030.n5jobs",
                settings={"copy_run_log_to_work_operations": True},
            )
            loaded = load_project(path)
            self.assertEqual(loaded.project_name, "1502_030")
            self.assertEqual(loaded.profile_id, "noark5")
            self.assertEqual(loaded.job_list_file, "1502_030.n5jobs")
            self.assertTrue(loaded.settings["copy_run_log_to_work_operations"])
            self.assertTrue(loaded.created_at)
            self.assertTrue(loaded.modified_at)

    def test_project_json_reserves_future_job_profile_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "project.json"
            save_project(
                path,
                project_name="Test",
                profile_id="noark5",
                job_profile_id="ikamr-noark5-standard",
                job_list_file="test.n5jobs",
            )
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["job_profile_id"], "ikamr-noark5-standard")
            self.assertIn("settings", data)

    def test_project_job_list_is_directly_below_wf(self):
        work_operations = Path("work") / "repository_operations"
        self.assertTrue(
            is_project_job_list_path(
                work_operations / "wf" / "project.n5jobs",
                work_operations,
            )
        )
        self.assertFalse(
            is_project_job_list_path(
                work_operations / "wf" / "jobs" / "project.n5jobs",
                work_operations,
            )
        )

    def test_runtime_syncs_project_json_and_uses_wf_logs(self):
        runtime = (ROOT / "gui" / "persistent_app_a13.py").read_text(encoding="utf-8")
        logs = (ROOT / "app" / "run_overview_log.py").read_text(encoding="utf-8")
        self.assertIn("_sync_project_file_for_job_list", runtime)
        self.assertIn("save_project(", runtime)
        self.assertIn('work_operations / "wf" / "logs"', logs)


if __name__ == "__main__":
    unittest.main()
