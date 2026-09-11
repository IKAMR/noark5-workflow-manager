import json
import tempfile
import unittest
from pathlib import Path

from noark5_workflow.analysis.xpath_test_engine import run_test

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config" / "noark5" / "tests" / "xpath_catalog_2026_05_26.json"


class A222ArchivePartReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.tests = {t["legacy"]["job_id"]: t for t in catalog["tests"]}

    def _run(self, job_id, xml):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "arkivstruktur.xml").write_text(xml, encoding="utf-8")
            return run_test(self.tests[job_id], root)

    def test_core_counts_and_generic_distribution_reconcile(self):
        xml = """<arkiv><arkivdel><mappe><registrering><dokumentbeskrivelse><dokumentmedium>Elektronisk arkiv</dokumentmedium></dokumentbeskrivelse></registrering></mappe></arkivdel><arkivdel><mappe><registrering><dokumentbeskrivelse><dokumentmedium>Fysisk medium</dokumentmedium></dokumentbeskrivelse></registrering></mappe></arkivdel></arkiv>"""
        result = self._run("C02", xml)
        self.assertEqual(result["status"], "ok")
        values = result["values"]
        self.assertEqual(len(values["_archive_parts"]), 2)
        self.assertEqual(values["_reconciliation_summary"]["status"], "match")
        self.assertEqual(values["_reconciliation"]["folder_count"]["archive_parts_sum"], 2)
        self.assertEqual(values["_reconciliation"]["document_medium_counts"]["archive_parts_sum"], {"Elektronisk arkiv": 1, "Fysisk medium": 1})

    def test_reconciliation_reports_difference_without_failing_test(self):
        # A screening directly under arkiv is deliberately outside archive parts.
        # The technical XPath execution remains OK while reconciliation documents the mismatch.
        xml = """<arkiv><skjerming/><arkivdel><mappe><skjerming/></mappe></arkivdel></arkiv>"""
        result = self._run("F08", xml)
        self.assertEqual(result["status"], "ok")
        rec = result["values"]["_reconciliation"]["screening_count"]
        self.assertEqual(rec["total"], 2)
        self.assertEqual(rec["archive_parts_sum"], 1)
        self.assertEqual(rec["difference"], 1)
        self.assertEqual(rec["status"], "mismatch")
        self.assertEqual(result["values"]["_reconciliation_summary"]["status"], "review")

    def test_selected_tests_have_archive_part_metrics(self):
        expected = {"C02", "C23", "C24", "F01", "F05", "F06", "F08", "F10", "F11", "F13"}
        for job_id in expected:
            execution = self.tests[job_id]["execution"]
            self.assertTrue(execution.get("archive_part_metrics"), job_id)
            self.assertTrue(execution.get("reconciliation"), job_id)

    def test_counter_reconciliation_uses_all_observed_values(self):
        xml = """<arkiv><arkivdel><dokumentbeskrivelse><dokumentobjekt><variantformat>A</variantformat></dokumentobjekt></dokumentbeskrivelse></arkivdel><arkivdel><dokumentbeskrivelse><dokumentobjekt><variantformat>B</variantformat></dokumentobjekt><dokumentobjekt><variantformat>A</variantformat></dokumentobjekt></dokumentbeskrivelse></arkivdel></arkiv>"""
        result = self._run("C24", xml)
        rec = result["values"]["_reconciliation"]["variant_format_counts"]
        self.assertEqual(rec["total"], {"A": 2, "B": 1})
        self.assertEqual(rec["archive_parts_sum"], {"A": 2, "B": 1})
        self.assertEqual(rec["difference"], {})
        self.assertEqual(rec["status"], "match")


if __name__ == "__main__":
    unittest.main()
