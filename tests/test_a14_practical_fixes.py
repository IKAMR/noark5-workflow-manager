from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.run_overview_log import RunOverviewLog
from noark5_workflow.sources.noark5_extraction import DOCUMENT_DIR_NAMES, Noark5Extraction
from settings import DEFAULT_CONFIG

ROOT = Path(__file__).resolve().parents[1]


class A14PracticalFixesTests(unittest.TestCase):
    def test_runtime_matches_source_panel_to_active_extraction(self):
        text = (ROOT / "gui" / "persistent_app_a13.py").read_text(encoding="utf-8")
        self.assertIn("active_extraction_root == path", text)
        self.assertIn("job.active_extraction_root == path", text)

    def test_source_dialog_uses_storage_role_name(self):
        text = (ROOT / "gui" / "source_panel.py").read_text(encoding="utf-8")
        self.assertIn("Source – uttrekksmappe", text)
        self.assertNotIn("Velg rotmappe for Noark 5-uttrekk", text)

    def test_zero_xsd_is_not_rendered_as_ok(self):
        text = (ROOT / "gui" / "source_panel.py").read_text(encoding="utf-8")
        self.assertIn('[--] XSD-filer: 0', text)

    def test_document_folder_names_are_explicit(self):
        self.assertEqual(
            DOCUMENT_DIR_NAMES,
            {"dokument", "DOKUMENT", "dokumenter", "DOKUMENTER"},
        )

    def test_each_supported_document_folder_is_detected(self):
        for dirname in DOCUMENT_DIR_NAMES:
            with self.subTest(dirname=dirname), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "arkivstruktur.xml").write_text("<x/>", encoding="utf-8")
                docs = root / dirname
                docs.mkdir()
                extraction = Noark5Extraction.detect(root)
                self.assertEqual(extraction.documents_dir, docs.resolve())

    def test_run_log_mirrors_to_work_operations_by_default(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            work_operations = temp / "work" / "repository_operations"
            settings = {
                "temp_dir": str(temp / "app"),
                "run_log_dir": "",
                "setup_dir": "",
                "job_list_dir": "",
                "copy_run_log_to_work_operations": True,
            }
            job = SimpleNamespace(
                job_id="JOB-001",
                name="Test",
                source_root=temp / "source-main",
                source_extraction=temp / "source-main" / "extraction",
                active_extraction_root=temp / "source-main" / "extraction",
                work_root=temp / "work",
                work_operations=work_operations,
                archive_root=temp / "aip",
                output_root=None,
                status=SimpleNamespace(value="Ferdig"),
                message="Workflow fullført",
            )
            log = RunOverviewLog(settings, run_type="single", app_version="0.1.2-a14")
            log.start_job(job)
            log.finish_job(job)
            central = log.finish()
            mirror = work_operations / "wf" / "logs" / central.name
            self.assertTrue(central.is_file())
            self.assertTrue(mirror.is_file())
            text = mirror.read_text(encoding="utf-8")
            self.assertIn("Source - hovedmappe:", text)
            self.assertIn("Source - uttrekksmappe:", text)
            self.assertIn("Arbeid - operasjoner:", text)
            self.assertIn("Arkiv - hovedmappe:", text)

    def test_run_log_mirror_can_be_disabled(self):
        self.assertIn("copy_run_log_to_work_operations", DEFAULT_CONFIG)
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            work_operations = temp / "work-operations"
            settings = {
                "temp_dir": str(temp / "app"),
                "run_log_dir": "",
                "setup_dir": "",
                "job_list_dir": "",
                "copy_run_log_to_work_operations": False,
            }
            job = SimpleNamespace(
                job_id="JOB-001", name="Test", source_root=temp / "source",
                source_extraction=None, active_extraction_root=temp / "source",
                work_root=temp / "work", work_operations=work_operations,
                archive_root=None, output_root=None,
                status=SimpleNamespace(value="Ferdig"), message="OK",
            )
            log = RunOverviewLog(settings, run_type="single", app_version="0.1.2-a14")
            log.start_job(job)
            central = log.finish()
            self.assertFalse((work_operations / "wf" / "logs" / central.name).exists())


if __name__ == "__main__":
    unittest.main()
