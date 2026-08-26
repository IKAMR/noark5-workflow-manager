import tempfile
import unittest
from pathlib import Path

from noark5_workflow.sources.noark5_extraction import Noark5Extraction


class ExtractionDetectionTests(unittest.TestCase):
    def test_detects_arkivstruktur_and_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "arkivstruktur.xml").write_text("<arkiv />", encoding="utf-8")
            (root / "arkivuttrekk.xml").write_text("<arkivuttrekk />", encoding="utf-8")
            (root / "schema.xsd").write_text("<schema />", encoding="utf-8")
            (root / "dokumenter").mkdir()
            extraction = Noark5Extraction.detect(root)
            self.assertTrue(extraction.is_noark5_candidate)
            self.assertIsNotNone(extraction.documents_dir)
            self.assertEqual(len(extraction.xsd_files), 1)


if __name__ == "__main__":
    unittest.main()
