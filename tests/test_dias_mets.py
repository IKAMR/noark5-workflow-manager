import tempfile
import unittest
from pathlib import Path

from noark5_workflow.operations.dias_mets import read_meta_from_mets


class DiasMetsImportTests(unittest.TestCase):
    def test_reads_dias_metadata_from_mets(self):
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" LABEL="Testpakke">
  <mets:metsHdr>
    <mets:agent TYPE="ORGANIZATION" ROLE="ARCHIVIST"><mets:name>Arkivorg</mets:name></mets:agent>
    <mets:agent TYPE="OTHER" OTHERTYPE="SOFTWARE" ROLE="ARCHIVIST"><mets:name>Kildesystem</mets:name></mets:agent>
    <mets:agent TYPE="OTHER" OTHERTYPE="SOFTWARE" ROLE="ARCHIVIST"><mets:name>2.3</mets:name></mets:agent>
    <mets:agent TYPE="OTHER" OTHERTYPE="SOFTWARE" ROLE="ARCHIVIST"><mets:name>NOARK-5</mets:name></mets:agent>
    <mets:agent TYPE="ORGANIZATION" ROLE="CREATOR"><mets:name>Skaper</mets:name></mets:agent>
    <mets:agent TYPE="ORGANIZATION" ROLE="OTHER" OTHERROLE="PRODUCER"><mets:name>Produsentorg</mets:name></mets:agent>
    <mets:agent TYPE="INDIVIDUAL" ROLE="OTHER" OTHERROLE="PRODUCER"><mets:name>Produsentperson</mets:name></mets:agent>
    <mets:agent TYPE="OTHER" OTHERTYPE="SOFTWARE" ROLE="OTHER" OTHERROLE="PRODUCER"><mets:name>Noark 5 Workflow Manager</mets:name></mets:agent>
    <mets:agent TYPE="ORGANIZATION" ROLE="OTHER" OTHERROLE="SUBMITTER"><mets:name>Avlevererorg</mets:name></mets:agent>
    <mets:agent TYPE="INDIVIDUAL" ROLE="OTHER" OTHERROLE="SUBMITTER"><mets:name>Avlevererperson</mets:name></mets:agent>
    <mets:agent TYPE="ORGANIZATION" ROLE="IPOWNER"><mets:name>Eierorg</mets:name></mets:agent>
    <mets:agent TYPE="ORGANIZATION" ROLE="PRESERVATION"><mets:name>Bevarer</mets:name></mets:agent>
    <mets:altRecordID TYPE="SUBMISSIONAGREEMENT">AVT-1</mets:altRecordID>
    <mets:altRecordID TYPE="STARTDATE">2020-01-01</mets:altRecordID>
    <mets:altRecordID TYPE="ENDDATE">2020-12-31</mets:altRecordID>
  </mets:metsHdr>
</mets:mets>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "info.xml"
            path.write_text(xml, encoding="utf-8")
            meta = read_meta_from_mets(path)

        self.assertEqual(meta["label"], "Testpakke")
        self.assertEqual(meta["submission_agreement"], "AVT-1")
        self.assertEqual(meta["system"], "Kildesystem")
        self.assertEqual(meta["system_version"], "2.3")
        self.assertEqual(meta["archivist_type"], "NOARK-5")
        self.assertEqual(meta["archivist_org"], "Arkivorg")
        self.assertEqual(meta["producer_org"], "Produsentorg")
        self.assertEqual(meta["producer_person"], "Produsentperson")
        self.assertEqual(meta["submitter_org"], "Avlevererorg")
        self.assertEqual(meta["submitter_person"], "Avlevererperson")
        self.assertEqual(meta["owner_org"], "Eierorg")
        self.assertEqual(meta["creator"], "Skaper")
        self.assertEqual(meta["preserver"], "Bevarer")
        self.assertEqual(meta["period_start"], "2020-01-01")
        self.assertEqual(meta["period_end"], "2020-12-31")

    def test_rejects_non_mets_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.xml"
            path.write_text("<root/>", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_meta_from_mets(path)


if __name__ == "__main__":
    unittest.main()
