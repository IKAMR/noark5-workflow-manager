from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.source import source_root


class ExampleSource:
    def __init__(self, root: Path):
        self.root = root


class SourceContractA12Tests(unittest.TestCase):
    def test_context_input_root_uses_source_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            fallback = Path(temp) / "fallback"
            ctx = OperationContext(
                extraction_root=fallback,
                source=ExampleSource(root),
            )
            self.assertEqual(ctx.input_root, root)

    def test_context_input_root_preserves_legacy_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            fallback = Path(temp)
            ctx = OperationContext(extraction_root=fallback)
            self.assertEqual(ctx.input_root, fallback)

    def test_source_root_has_no_noark_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            fallback = Path(temp)
            self.assertEqual(source_root(None, fallback), fallback)


if __name__ == "__main__":
    unittest.main()
