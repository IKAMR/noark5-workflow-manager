import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from noark5_workflow.core.context import OperationContext
from noark5_workflow.executors.local import LocalExecutor
from noark5_workflow.operations.dias_package import DiasPackageOperation
from noark5_workflow.sources.noark5_extraction import Noark5Extraction


class DiasExtraFilesTests(unittest.TestCase):
    def _params(self, out: Path, extra_files):
        return {
            "submission_agreement": "TEST-EXTRA",
            "label": "Testpakke",
            "system": "Testsystem",
            "system_version": "1.0",
            "archivist_type": "NOARK-5",
            "period_start": "2020-01-01",
            "period_end": "2020-12-31",
            "owner_org": "Eier",
            "archivist_org": "Arkiv",
            "submitter_org": "Avleverer",
            "submitter_person": "Person",
            "producer_org": "Produsent",
            "producer_person": "Person",
            "producer_software": "Noark 5 Workflow Manager",
            "creator": "Skaper",
            "preserver": "Bevarer",
            "output_dir": str(out),
            "extra_files": json.dumps(extra_files),
        }

    def test_packages_manual_files_in_selected_dias_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "uttrekk"
            source.mkdir()
            (source / "arkivstruktur.xml").write_text("<arkiv />", encoding="utf-8")
            out = base / "out"
            out.mkdir()

            report = base / "rapport.pdf"
            report.write_bytes(b"PDF test")
            note = base / "tillegg.txt"
            note.write_text("tillegg", encoding="utf-8")

            extras = [
                {"src": str(report), "dest": "administrative_metadata/repository_operations/rapport.pdf"},
                {"src": str(note), "dest": "content/tillegg.txt"},
            ]
            op = DiasPackageOperation()
            op.configure(self._params(out, extras))
            extraction = Noark5Extraction.detect(source)
            result = LocalExecutor().execute(op, OperationContext(extraction_root=source, source=extraction))
            self.assertTrue(result.ok, result.message)
            self.assertEqual(result.data["extra_file_count"], 2)

            aic = Path(result.data["aic_path"])
            tar_files = list(aic.glob("*/content/*.tar"))
            self.assertEqual(len(tar_files), 1)
            with tarfile.open(tar_files[0], "r") as tf:
                names = tf.getnames()
                mets_name = next(name for name in names if name.endswith("/mets.xml"))
                mets_text = tf.extractfile(mets_name).read().decode("utf-8")

            self.assertTrue(any(name.endswith("/administrative_metadata/repository_operations/rapport.pdf") for name in names))
            self.assertTrue(any(name.endswith("/content/tillegg.txt") for name in names))
            self.assertIn("administrative_metadata/repository_operations/rapport.pdf", mets_text)
            self.assertIn("content/tillegg.txt", mets_text)


class DiasExtraFolderTests(unittest.TestCase):
    def _params(self, out: Path, extra_files):
        return {
            "submission_agreement": "TEST-FOLDER",
            "label": "Testpakke mapper",
            "system": "Testsystem",
            "system_version": "1.0",
            "archivist_type": "NOARK-5",
            "period_start": "2020-01-01",
            "period_end": "2020-12-31",
            "owner_org": "Eier",
            "archivist_org": "Arkiv",
            "submitter_org": "Avleverer",
            "submitter_person": "Person",
            "producer_org": "Produsent",
            "producer_person": "Person",
            "producer_software": "Noark 5 Workflow Manager",
            "creator": "Skaper",
            "preserver": "Bevarer",
            "output_dir": str(out),
            "extra_files": json.dumps(extra_files),
        }

    def test_packages_added_folder_and_created_empty_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "uttrekk"
            source.mkdir()
            (source / "arkivstruktur.xml").write_text("<arkiv />", encoding="utf-8")
            out = base / "out"
            out.mkdir()

            folder = base / "rapporter"
            (folder / "under").mkdir(parents=True)
            (folder / "rapport.txt").write_text("rapport", encoding="utf-8")
            (folder / "under" / "detalj.txt").write_text("detalj", encoding="utf-8")

            extras = [
                {
                    "kind": "folder",
                    "src": str(folder),
                    "dest": "administrative_metadata/repository_operations/rapporter",
                },
                {
                    "kind": "empty_folder",
                    "src": "",
                    "dest": "descriptive_metadata/egen_metadata",
                },
            ]
            op = DiasPackageOperation()
            op.configure(self._params(out, extras))
            extraction = Noark5Extraction.detect(source)
            # Added folders must be streamed directly into TAR, not copied to
            # the temporary staging tree first. The old a8 implementation used
            # shutil.copytree here and could fail on Windows with WinError 206.
            with patch("noark5_workflow.operations.dias_package.shutil.copytree", side_effect=AssertionError("copytree must not be used")):
                result = LocalExecutor().execute(op, OperationContext(extraction_root=source, source=extraction))
            self.assertTrue(result.ok, result.message)

            aic = Path(result.data["aic_path"])
            tar_files = list(aic.glob("*/content/*.tar"))
            self.assertEqual(len(tar_files), 1)
            with tarfile.open(tar_files[0], "r") as tf:
                names = tf.getnames()

            self.assertTrue(any(name.endswith("/administrative_metadata/repository_operations/rapporter/rapport.txt") for name in names))
            self.assertTrue(any(name.endswith("/administrative_metadata/repository_operations/rapporter/under/detalj.txt") for name in names))
            self.assertTrue(any(name.endswith("/descriptive_metadata/egen_metadata") for name in names))


if __name__ == "__main__":
    unittest.main()
