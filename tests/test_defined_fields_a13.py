from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from noark5_workflow.analysis.defined_fields import (
    DEFAULT_DEFINITION,
    extract_defined_fields,
    load_definition,
)


SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<arkivstruktur xmlns="urn:noark:test">
  <arkiv>
    <systemID>ARK-001</systemID>
    <tittel>Testarkiv</tittel>
    <beskrivelse>Eksempelarkiv</beskrivelse>
    <arkivstatus>Avsluttet</arkivstatus>
    <dokumentmedium>Elektronisk arkiv</dokumentmedium>
    <opprettetDato>2008-01-01T12:00:00</opprettetDato>
    <opprettetAv>Testbruker</opprettetAv>
    <avsluttetDato>2019-12-31T23:59:59</avsluttetDato>
    <avsluttetAv>Testavslutter</avsluttetAv>
    <arkivskaper>
      <arkivskaperID>1535</arkivskaperID>
      <arkivskaperNavn>Vestnes kommune</arkivskaperNavn>
      <beskrivelse>Arkivskaperbeskrivelse</beskrivelse>
    </arkivskaper>
    <arkivdel>
      <tittel>Saksarkiv</tittel>
      <beskrivelse>Saker</beskrivelse>
      <arkivdelstatus>Avsluttet periode</arkivdelstatus>
      <dokumentmedium>Elektronisk arkiv</dokumentmedium>
      <arkivperiodeStartDato>2008-01-01</arkivperiodeStartDato>
      <arkivperiodeSluttDato>2019-12-31</arkivperiodeSluttDato>
      <opprettetDato>2007-12-01T10:00:00</opprettetDato>
      <avsluttetDato>2022-06-30T10:00:00</avsluttetDato>
    </arkivdel>
    <arkivdel>
      <tittel>Møter</tittel>
      <beskrivelse>Meeting series</beskrivelse>
      <arkivdelstatus>Avsluttet periode</arkivdelstatus>
      <dokumentmedium>Elektronisk arkiv</dokumentmedium>
      <arkivperiodeStartDato>2008-01-01</arkivperiodeStartDato>
      <arkivperiodeSluttDato>2019-12-31</arkivperiodeSluttDato>
      <opprettetDato>2007-12-01T10:00:00</opprettetDato>
      <avsluttetDato>2022-06-30T10:00:00</avsluttetDato>
    </arkivdel>
  </arkiv>
</arkivstruktur>
"""


class DefinedFieldsA13Tests(unittest.TestCase):
    def _write_sample(self, root: Path) -> Path:
        path = root / "arkivstruktur.xml"
        path.write_text(SAMPLE, encoding="utf-8")
        return path

    def test_definition_is_external_json(self):
        definition = load_definition()
        self.assertTrue(DEFAULT_DEFINITION.is_file())
        self.assertEqual(definition["definition_id"], "noark5.archive_structure.metadata.v1")
        self.assertIn("archive", definition["entities"])
        self.assertIn("archive_parts", definition["entities"])

    def test_archive_n504_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            result = extract_defined_fields(self._write_sample(Path(temp)))
            archive = result["archive"]
            self.assertEqual(result["archive_count"], 1)
            self.assertEqual(archive["title"], "Testarkiv")
            self.assertEqual(archive["system_id"], "ARK-001")
            self.assertEqual(archive["status"], "Avsluttet")
            self.assertEqual(archive["document_medium"], "Elektronisk arkiv")
            self.assertEqual(archive["created_by"], "Testbruker")
            self.assertEqual(archive["closed_by"], "Testavslutter")

    def test_archive_creator_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            result = extract_defined_fields(self._write_sample(Path(temp)))
            creator = result["archive"]["creators"][0]
            self.assertEqual(creator["name"], "Vestnes kommune")
            self.assertEqual(creator["id"], "1535")
            self.assertEqual(creator["description"], "Arkivskaperbeskrivelse")

    def test_archive_parts_n505_06_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            result = extract_defined_fields(self._write_sample(Path(temp)))
            parts = result["archive_parts"]
            self.assertEqual(result["archive_parts_count"], 2)
            self.assertEqual(parts[0]["index"], 1)
            self.assertEqual(parts[0]["title"], "Saksarkiv")
            self.assertEqual(parts[0]["period_start"], "2008-01-01")
            self.assertEqual(parts[0]["period_end"], "2019-12-31")
            self.assertEqual(parts[1]["index"], 2)
            self.assertEqual(parts[1]["title"], "Møter")

    def test_noark_xpath_fields_are_not_hardcoded_in_engine(self):
        engine = (
            Path(__file__).resolve().parents[1]
            / "noark5_workflow"
            / "analysis"
            / "defined_fields.py"
        ).read_text(encoding="utf-8")
        definition_text = DEFAULT_DEFINITION.read_text(encoding="utf-8")
        self.assertNotIn("arkivstatus", engine)
        self.assertNotIn("arkivperiodeStartDato", engine)
        self.assertIn("arkivstatus", definition_text)
        self.assertIn("arkivperiodeStartDato", definition_text)


if __name__ == "__main__":
    unittest.main()
