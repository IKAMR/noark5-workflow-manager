import tarfile
import tempfile
import unittest
from pathlib import Path

from noark5_workflow.core.context import OperationContext
from noark5_workflow.executors.local import LocalExecutor
from noark5_workflow.operations.dias_package import DiasPackageOperation
from noark5_workflow.sources.noark5_extraction import Noark5Extraction


class DiasPackageTests(unittest.TestCase):
    def test_packages_complete_noark_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "uttrekk"
            source.mkdir()
            (source / "arkivstruktur.xml").write_text("<arkiv />", encoding="utf-8")
            (source / "arkivuttrekk.xml").write_text("<uttrekk />", encoding="utf-8")
            docs = source / "dokumenter"
            docs.mkdir()
            (docs / "test.txt").write_text("dokument", encoding="utf-8")
            out = base / "out"
            out.mkdir()

            op = DiasPackageOperation()
            op.configure({
                "submission_agreement": "TEST-1",
                "label": "Testpakke",
                "system": "Testsyst",
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
            })
            extraction = Noark5Extraction.detect(source)
            ctx = OperationContext(extraction_root=source, source=extraction)
            result = LocalExecutor().execute(op, ctx)
            self.assertTrue(result.ok, result.message)
            aic = Path(result.data["aic_path"])
            self.assertTrue((aic / "info.xml").is_file())
            tar_files = list(aic.glob("*/content/*.tar"))
            self.assertEqual(len(tar_files), 1)
            with tarfile.open(tar_files[0], "r") as tf:
                names = tf.getnames()
            self.assertTrue(any(name.endswith("/content/arkivstruktur.xml") for name in names))
            self.assertTrue(any(name.endswith("/content/dokumenter/test.txt") for name in names))
            self.assertTrue(any(name.endswith("/mets.xml") for name in names))
            self.assertTrue(any(name.endswith("/administrative_metadata/premis.xml") for name in names))


if __name__ == "__main__":
    unittest.main()
