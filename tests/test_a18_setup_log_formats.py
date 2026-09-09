from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class A18SetupLogFormatsTests(unittest.TestCase):
    def test_setup_exposes_all_current_output_formats(self):
        text = (ROOT / "gui" / "setup_dialog_a18.py").read_text(encoding="utf-8")
        self.assertIn('text="Tekstlig kjørelogg"', text)
        self.assertIn('text="JSON-logg"', text)
        self.assertIn('text="CSV-logg"', text)
        self.assertIn('text="PREMIS-proveniens"', text)

    def test_setup_collects_json_and_csv_sink_ids(self):
        text = (ROOT / "gui" / "setup_dialog_a18.py").read_text(encoding="utf-8")
        self.assertIn('JSON_SINK = "json"', text)
        self.assertIn('CSV_SINK = "csv"', text)
        self.assertIn('sinks.append(JSON_SINK)', text)
        self.assertIn('sinks.append(CSV_SINK)', text)

    def test_setup_loads_json_and_csv_selection(self):
        text = (ROOT / "gui" / "setup_dialog_a18.py").read_text(encoding="utf-8")
        self.assertIn('self.json_enabled_var.set(JSON_SINK in configured_sinks)', text)
        self.assertIn('self.csv_enabled_var.set(CSV_SINK in configured_sinks)', text)


if __name__ == "__main__":
    unittest.main()
