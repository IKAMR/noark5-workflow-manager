import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _method_source(path: Path, method_name: str) -> str:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(f"Fant ikke metode: {method_name}")


class JobListSaveAsSingleWriteA17Tests(unittest.TestCase):
    def test_save_as_has_transaction_guard(self):
        text = (ROOT / "gui" / "persistent_app_a17.py").read_text(encoding="utf-8")
        self.assertIn("_joblist_save_as_active", text)
        self.assertIn("_joblist_explicit_write", text)

    def test_save_as_waits_for_filename_before_write(self):
        method = _method_source(
            ROOT / "gui" / "persistent_app_a17.py",
            "_save_job_list_as_in",
        )
        self.assertLess(method.index("asksaveasfilename"), method.index("_write_job_list(target)"))

    def test_only_explicit_target_is_written_in_save_as_method(self):
        method = _method_source(
            ROOT / "gui" / "persistent_app_a17.py",
            "_save_job_list_as_in",
        )
        self.assertEqual(method.count("_write_job_list("), 1)
        self.assertIn("_write_job_list(target)", method)

    def test_implicit_write_is_blocked_during_save_as(self):
        method = _method_source(
            ROOT / "gui" / "persistent_app_a17.py",
            "_write_job_list",
        )
        self.assertIn("self._joblist_save_as_active and not self._joblist_explicit_write", method)
        self.assertIn("return False", method)


if __name__ == "__main__":
    unittest.main()
