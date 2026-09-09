from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from noark5_workflow.sources.noark5_extraction import Noark5Extraction


class A19Noark5DetectionPerformanceTests(unittest.TestCase):
    def test_detects_metadata_in_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "arkivstruktur.xml").write_text("<x/>", encoding="utf-8")
            extraction = Noark5Extraction.detect(root)
            self.assertTrue(extraction.is_noark5_candidate)

    def test_detects_metadata_one_level_below(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = root / "metadata"
            metadata.mkdir()
            (metadata / "arkivstruktur.xml").write_text("<x/>", encoding="utf-8")
            extraction = Noark5Extraction.detect(root)
            self.assertTrue(extraction.is_noark5_candidate)

    def test_document_directory_is_detected_without_traversing_its_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "dokument"
            docs.mkdir()
            (root / "arkivstruktur.xml").write_text("<x/>", encoding="utf-8")

            original_iterdir = Path.iterdir

            def guarded_iterdir(path):
                if path == docs:
                    raise AssertionError("dokumentmappen skal ikke skannes")
                return original_iterdir(path)

            with patch.object(Path, "iterdir", guarded_iterdir):
                extraction = Noark5Extraction.detect(root)

            self.assertEqual(docs.resolve(), extraction.documents_dir.resolve())

    def test_root_is_not_rescanned_for_each_metadata_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "arkivstruktur.xml").write_text("<x/>", encoding="utf-8")
            calls = []
            original_iterdir = Path.iterdir

            def counting_iterdir(path):
                calls.append(path)
                return original_iterdir(path)

            with patch.object(Path, "iterdir", counting_iterdir):
                Noark5Extraction.detect(root)

            self.assertEqual(1, sum(path == root.resolve() for path in calls))


if __name__ == "__main__":
    unittest.main()
