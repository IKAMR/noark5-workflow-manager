import json
import tempfile
import unittest
from pathlib import Path

from noark5_workflow.analysis.xpath_test_engine import run_test


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'config' / 'noark5' / 'tests' / 'xpath_catalog_2026_05_26.json'


class A224CoverageTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
        self.tests = {t['test_id']: t for t in self.catalog['tests']}
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        xml = '''<arkiv>
  <systemID>A1</systemID><tittel>Arkiv A</tittel><beskrivelse>Beskrivelse A</beskrivelse>
  <arkivstatus>Avsluttet</arkivstatus><dokumentmedium>Elektronisk arkiv</dokumentmedium>
  <opprettetDato>2020-01-01T00:00:00</opprettetDato><avsluttetDato>2024-12-31T00:00:00</avsluttetDato>
  <opprettetAv>AA</opprettetAv><avsluttetAv>BB</avsluttetAv>
  <arkivskaper><arkivskaperNavn>Skaper</arkivskaperNavn><arkivskaperID>S1</arkivskaperID><beskrivelse>Skaperbeskrivelse</beskrivelse></arkivskaper>
  <arkivdel>
    <systemID>D1</systemID><tittel>Del 1</tittel><beskrivelse>Første del</beskrivelse><arkivdelstatus>Avsluttet</arkivdelstatus>
    <dokumentmedium>Elektronisk arkiv</dokumentmedium><arkivperiodeStartDato>2020-01-01</arkivperiodeStartDato><arkivperiodeSluttDato>2022-12-31</arkivperiodeSluttDato>
    <opprettetDato>2020-01-01T00:00:00</opprettetDato><avsluttetDato>2023-01-10T00:00:00</avsluttetDato>
    <mappe type="moetemappe"><saksstatus>Avsluttet</saksstatus><avsluttetDato>2022-12-31T00:00:00</avsluttetDato>
      <registrering type="journalpost"><journalposttype>Inngående dokument</journalposttype><journalstatus>Arkivert</journalstatus>
        <dokumentbeskrivelse><systemID>DB1</systemID><tilknyttetRegistreringSom>Hoveddokument</tilknyttetRegistreringSom></dokumentbeskrivelse>
      </registrering>
    </mappe>
  </arkivdel>
  <arkivdel>
    <systemID>D2</systemID><tittel>Del 2</tittel><beskrivelse>Andre del</beskrivelse><arkivdelstatus>Avsluttet</arkivdelstatus>
    <dokumentmedium>Elektronisk arkiv</dokumentmedium><arkivperiodeStartDato>2023-01-01</arkivperiodeStartDato><arkivperiodeSluttDato>2024-12-31</arkivperiodeSluttDato>
    <opprettetDato>2023-01-01T00:00:00</opprettetDato><avsluttetDato>2025-01-10T00:00:00</avsluttetDato>
    <mappe><saksstatus>Utgår</saksstatus></mappe>
    <registrering type="journalpost"><journalposttype>Utgående dokument</journalposttype><journalstatus>Journalført</journalstatus>
      <dokumentbeskrivelse><systemID>DB2</systemID><tilknyttetRegistreringSom>Vedlegg</tilknyttetRegistreringSom></dokumentbeskrivelse>
    </registrering>
  </arkivdel>
</arkiv>'''
        (self.root / 'arkivstruktur.xml').write_text(xml, encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def test_c01_identity_rows(self):
        r = run_test(self.tests['kdrs.c01'], self.root)
        self.assertEqual(r['status'], 'ok')
        self.assertEqual(r['values']['archive_records'][0]['system_id'], 'A1')
        self.assertEqual(r['values']['archive_creator_records'][0]['name'], 'Skaper')

    def test_c02_archive_part_rows(self):
        r = run_test(self.tests['kdrs.c02'], self.root)
        rows = r['values']['archive_part_records']
        self.assertEqual([x['system_id'] for x in rows], ['D1', 'D2'])
        self.assertEqual(rows[0]['archive_period_start_date'], '2020-01-01')

    def test_c13_u2_parity_and_reconciliation(self):
        r = run_test(self.tests['kdrs.c13'], self.root)
        self.assertEqual(r['values']['_archive_parts'][0]['values']['closed_meeting_folder_count'], 1)
        self.assertEqual(r['values']['_reconciliation']['folder_count']['status'], 'match')
        self.assertEqual(r['values']['_reconciliation']['status_counts']['status'], 'match')

    def test_c15_journal_status_and_document_relation_per_part(self):
        r = run_test(self.tests['kdrs.c15'], self.root)
        self.assertEqual(r['values']['journal_status_counts'], {'Arkivert': 1, 'Journalført': 1})
        self.assertEqual(r['values']['_reconciliation']['journal_status_counts']['status'], 'match')
        self.assertEqual(r['values']['_reconciliation']['main_document_count']['status'], 'match')

    def test_c22_without_object_per_part(self):
        r = run_test(self.tests['kdrs.c22'], self.root)
        self.assertEqual(r['values']['without_object_count'], 2)
        self.assertEqual(r['values']['_reconciliation']['without_object_count']['status'], 'match')


if __name__ == '__main__':
    unittest.main()
