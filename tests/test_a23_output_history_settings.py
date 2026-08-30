import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from xml.etree import ElementTree as ET

from noark5_workflow.core.premis_logger import PREMIS_NS, PremisProvenanceLogger
from app import settings_portable

ROOT = Path(__file__).resolve().parents[1]


class FakeOperation:
    premis_event_type = "Creation"
    premis_event_label = "Test"
    definition = SimpleNamespace(operation_id="fake")

    def premis_detail(self, result, ctx):
        return result.message


class FakeContext:
    def __init__(self):
        self.lines = []
    def log(self, text):
        self.lines.append(text)


class A23OutputHistorySettingsTests(unittest.TestCase):
    def test_premis_repeated_runs_preserve_previous_events(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out = Path(temp_dir)
            source = Path(temp_dir) / "noark5"
            ctx = FakeContext()
            op = FakeOperation()
            first = SimpleNamespace(ok=True, message="første kjøring")
            second = SimpleNamespace(ok=True, message="andre kjøring")

            logger1 = PremisProvenanceLogger(out, source, "0.1.2-a2")
            logger1.record(op, first, ctx)
            logger1.finalize(source, ctx)

            logger2 = PremisProvenanceLogger(out, source, "0.1.2-a2")
            logger2.record(op, second, ctx)
            path = logger2.finalize(source, ctx)

            root = ET.parse(path).getroot()
            events = root.findall(f"{{{PREMIS_NS}}}event")
            self.assertEqual(len(events), 2)
            details = [e.findtext(f"{{{PREMIS_NS}}}eventDetail") for e in events]
            self.assertTrue(any("første kjøring" in value for value in details))
            self.assertTrue(any("andre kjøring" in value for value in details))

    def test_different_jobs_same_output_is_blocked_in_app(self):
        text = (ROOT / "gui" / "persistent_app.py").read_text(encoding="utf-8")
        self.assertIn("def _validate_unique_outputs", text)
        self.assertIn("To forskjellige jobber kan ikke bruke samme utdataområde", text)
        self.assertIn("if not self._validate_unique_outputs(self.jobs.jobs()):", text)

    def test_dias_target_is_at_top_in_a23_dialog(self):
        text = (ROOT / "gui" / "dias_dialog_a23.py").read_text(encoding="utf-8")
        output_pos = text.index('text="Utdatamappe"')
        mets_pos = text.index('text="Les inn fra METS-fil …"')
        fields_pos = text.index("for row, (key, label) in enumerate(_FIELDS")
        self.assertLess(output_pos, mets_pos)
        self.assertLess(output_pos, fields_pos)
        self.assertIn('text="Velg…"', text)

    def test_settings_export_import_and_reset_are_portable_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "config.json"
            export = Path(temp_dir) / "setup.json"
            with patch.object(settings_portable, "CONFIG_PATH", config):
                settings_portable.write_full_config({"font_offset": 3, "temp_dir": "X:/temp"})
                settings_portable.export_settings(export)
                payload = json.loads(export.read_text(encoding="utf-8"))
                self.assertEqual(payload["file_type"], settings_portable.FILE_TYPE)
                self.assertEqual(payload["format_version"], 1)
                self.assertEqual(payload["settings"]["font_offset"], 3)

                settings_portable.write_full_config({"font_offset": -2})
                imported = settings_portable.import_settings(export)
                self.assertEqual(imported["font_offset"], 3)
                self.assertEqual(imported["temp_dir"], "X:/temp")

                reset = settings_portable.reset_settings()
                self.assertEqual(reset["font_offset"], 0)
                self.assertEqual(reset["last_job_list_file"], "")

    def test_settings_dialog_exposes_export_import_reset(self):
        text = (ROOT / "gui" / "settings_dialog_a23.py").read_text(encoding="utf-8")
        self.assertIn("Eksporter setup…", text)
        self.assertIn("Importer setup…", text)
        self.assertIn("Nullstill setup", text)


if __name__ == "__main__":
    unittest.main()
