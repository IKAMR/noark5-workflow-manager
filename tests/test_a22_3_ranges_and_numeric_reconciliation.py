import json
import tempfile
import unittest
from pathlib import Path

from noark5_workflow.analysis.xpath_test_engine import run_test

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'config' / 'noark5' / 'tests' / 'xpath_catalog_2026_05_26.json'


class A223RangesAndNumericReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
        cls.tests = {t['legacy']['job_id']: t for t in catalog['tests']}

    def _run(self, job_id, xml):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'arkivstruktur.xml').write_text(xml, encoding='utf-8')
            return run_test(self.tests[job_id], root)

    def test_date_range_reconciliation_uses_min_and_max_across_parts(self):
        xml = '''<arkiv>
          <arkivdel><opprettetDato>2020-01-02T00:00:00</opprettetDato><avsluttetDato>2021-02-03T00:00:00</avsluttetDato></arkivdel>
          <arkivdel><opprettetDato>2019-04-05T00:00:00</opprettetDato><avsluttetDato>2022-06-07T00:00:00</avsluttetDato></arkivdel>
        </arkiv>'''
        result = self._run('C02', xml)
        rec = result['values']['_reconciliation']['archive_part_created_date_range']
        self.assertEqual(rec['archive_parts_range'], {'first': '2019-04-05', 'last': '2020-01-02'})
        self.assertEqual(rec['status'], 'match')
        closed = result['values']['_reconciliation']['archive_part_closed_date_range']
        self.assertEqual(closed['archive_parts_range'], {'first': '2021-02-03', 'last': '2022-06-07'})
        self.assertEqual(closed['status'], 'match')

    def test_folder_and_registration_ranges_reconcile(self):
        xml = '''<arkiv>
          <arkivdel><mappe><opprettetDato>2020-01-01T00:00:00</opprettetDato><saksdato>2020-01-02</saksdato><registrering><arkivertDato>2020-02-01T00:00:00</arkivertDato></registrering></mappe></arkivdel>
          <arkivdel><mappe><opprettetDato>2021-01-01T00:00:00</opprettetDato><saksdato>2021-01-02</saksdato><registrering><arkivertDato>2021-02-01T00:00:00</arkivertDato></registrering></mappe></arkivdel>
        </arkiv>'''
        c08 = self._run('C08', xml)
        self.assertEqual(c08['values']['_reconciliation']['folder_created_date_range']['status'], 'match')
        self.assertEqual(c08['values']['_reconciliation']['case_date_range']['status'], 'match')
        c14 = self._run('C14', xml)
        self.assertEqual(c14['values']['_reconciliation']['archived_date_range']['status'], 'match')

    def test_numeric_stats_reconstruct_weighted_average(self):
        xml = '''<arkiv>
          <arkivdel><dokumentbeskrivelse><dokumentobjekt><filstoerrelse>10</filstoerrelse></dokumentobjekt></dokumentbeskrivelse></arkivdel>
          <arkivdel><dokumentbeskrivelse><dokumentobjekt><filstoerrelse>20</filstoerrelse></dokumentobjekt><dokumentobjekt><filstoerrelse>30</filstoerrelse></dokumentobjekt></dokumentbeskrivelse></arkivdel>
        </arkiv>'''
        result = self._run('C24', xml)
        rec = result['values']['_reconciliation']['file_size_stats']
        self.assertEqual(rec['archive_parts_reconstructed']['count'], 3)
        self.assertEqual(rec['archive_parts_reconstructed']['sum'], 60)
        self.assertEqual(rec['archive_parts_reconstructed']['average'], 20)
        self.assertEqual(rec['archive_parts_reconstructed']['min'], 10)
        self.assertEqual(rec['archive_parts_reconstructed']['max'], 30)
        self.assertEqual(rec['status'], 'match')
        buckets = result['values']['_reconciliation']['file_size_buckets']
        self.assertEqual(buckets['status'], 'match')

    def test_document_date_and_conversion_distribution_reconcile(self):
        xml = '''<arkiv>
          <arkivdel><dokumentbeskrivelse><opprettetDato>2020-01-01T00:00:00</opprettetDato><dokumentobjekt><konvertering><konvertertFraFormat>doc</konvertertFraFormat><konvertertTilFormat>pdf</konvertertTilFormat><konverteringsverktoey>A</konverteringsverktoey></konvertering></dokumentobjekt></dokumentbeskrivelse></arkivdel>
          <arkivdel><dokumentbeskrivelse><opprettetDato>2021-01-01T00:00:00</opprettetDato><dokumentobjekt><konvertering><konvertertFraFormat>docx</konvertertFraFormat><konvertertTilFormat>pdf</konvertertTilFormat><konverteringsverktoey>B</konverteringsverktoey></konvertering></dokumentobjekt></dokumentbeskrivelse></arkivdel>
        </arkiv>'''
        c25 = self._run('C25', xml)
        self.assertEqual(c25['values']['_reconciliation']['created_date_range']['status'], 'match')
        f12 = self._run('F12', xml)
        self.assertEqual(f12['values']['_reconciliation_summary']['status'], 'match')
        self.assertEqual(f12['values']['_reconciliation']['converted_to_format_counts']['archive_parts_sum'], {'pdf': 2})


if __name__ == '__main__':
    unittest.main()
