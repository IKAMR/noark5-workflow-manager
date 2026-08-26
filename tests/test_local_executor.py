import tempfile
import unittest
from pathlib import Path

from noark5_workflow.core.context import OperationContext
from noark5_workflow.executors.local import LocalExecutor
from noark5_workflow.operations.detect_extraction import DetectExtractionOperation


class LocalExecutorTests(unittest.TestCase):
    def test_executes_operation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "arkivstruktur.xml").write_text("<arkiv />", encoding="utf-8")
            ctx = OperationContext(extraction_root=root)
            result = LocalExecutor().execute(DetectExtractionOperation(), ctx)
            self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()
