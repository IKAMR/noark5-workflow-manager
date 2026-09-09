from pathlib import Path
import json
import tempfile
import unittest

from noark5_workflow.core.raw_result_store import (
    RawResultStore,
    persist_operation_raw_result,
    raw_result_store_path,
)


class _Definition:
    operation_id = "demo_test"


class _Operation:
    definition = _Definition()
    raw_result_record = True

    def raw_result_identity(self, result, ctx):
        return {"test_id": "demo.rule.v1", "definition_version": "1"}


class _Result:
    def __init__(self, ok=False):
        self.ok = ok
        self.message = "FAIL" if not ok else "PASS"
        self.data = {"count": 3}
        self.warnings = []
        self.outputs = []


class _Context:
    def __init__(self, root):
        self.work_operations = Path(root)
        self.input_root = Path(root) / "source"
        self.metadata = {"job_id": "JOB-001"}
        self.logs = []

    def log(self, text):
        self.logs.append(text)


class RawResultStoreA17Tests(unittest.TestCase):
    def test_store_is_append_only_and_preserves_fail_then_pass(self):
        with tempfile.TemporaryDirectory() as td:
            store = RawResultStore(Path(td) / "raw.jsonl")
            fail = store.append(operation_id="x", test_id="rule", definition_version="1", ok=False, message="fail")
            passed = store.append(operation_id="x", test_id="rule", definition_version="2", ok=True, message="pass")
            items = store.results()
            self.assertEqual(2, len(items))
            self.assertNotEqual(fail.result_id, passed.result_id)
            self.assertFalse(items[0].ok)
            self.assertTrue(items[1].ok)

    def test_result_id_can_be_used_as_review_reference(self):
        with tempfile.TemporaryDirectory() as td:
            store = RawResultStore(Path(td) / "raw.jsonl")
            item = store.append(operation_id="x", test_id="rule", definition_version="1", ok=True, message="ok")
            self.assertEqual(item.result_id, item.ref.result_id)
            self.assertEqual("rule", item.ref.test_id)

    def test_store_roundtrip_preserves_structured_data(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "raw.jsonl"
            store = RawResultStore(path)
            item = store.append(operation_id="x", test_id="rule", definition_version="1", ok=False, message="æøå", data={"nested": {"n": 2}})
            loaded = store.get(item.result_id)
            self.assertIsNotNone(loaded)
            self.assertEqual({"nested": {"n": 2}}, loaded.data)
            self.assertEqual("æøå", loaded.message)

    def test_generic_store_path_is_under_work_operations_wf(self):
        with tempfile.TemporaryDirectory() as td:
            ctx = _Context(td)
            self.assertEqual(Path(td) / "wf" / "results" / "raw-results.jsonl", raw_result_store_path(ctx))

    def test_no_source_fallback_when_work_operations_missing(self):
        ctx = _Context(".")
        ctx.work_operations = None
        self.assertIsNone(raw_result_store_path(ctx))

    def test_executor_helper_attaches_result_reference(self):
        with tempfile.TemporaryDirectory() as td:
            ctx = _Context(td)
            result = _Result(ok=False)
            envelope = persist_operation_raw_result(_Operation(), result, ctx)
            self.assertIsNotNone(envelope)
            self.assertEqual(envelope.result_id, result.data["_result_ref"]["result_id"])
            self.assertEqual("demo.rule.v1", result.data["_result_ref"]["test_id"])

    def test_non_opt_in_operation_is_not_recorded(self):
        class Operation:
            definition = _Definition()
        with tempfile.TemporaryDirectory() as td:
            ctx = _Context(td)
            result = _Result(ok=True)
            self.assertIsNone(persist_operation_raw_result(Operation(), result, ctx))
            self.assertFalse((Path(td) / "wf" / "results" / "raw-results.jsonl").exists())

    def test_noark_operations_explicitly_opt_in(self):
        root = Path(__file__).resolve().parents[1]
        validate = (root / "noark5_workflow" / "operations" / "validate_xml_schema.py").read_text(encoding="utf-8")
        analyse = (root / "noark5_workflow" / "operations" / "analyse_noark5_core.py").read_text(encoding="utf-8")
        self.assertIn("raw_result_record = True", validate)
        self.assertIn("raw_result_record = True", analyse)
        self.assertIn("raw_result_identity", validate)
        self.assertIn("raw_result_identity", analyse)


if __name__ == "__main__":
    unittest.main()
