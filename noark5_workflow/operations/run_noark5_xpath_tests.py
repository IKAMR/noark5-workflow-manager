from __future__ import annotations

from datetime import datetime
from pathlib import Path

from noark5_workflow.analysis.xpath_test_engine import run_catalog
from noark5_workflow.core.context import OperationContext
from noark5_workflow.core.operation import BaseOperation, ExecutionTarget, OperationDefinition
from noark5_workflow.core.result import OperationResult

CATALOG_PATH = Path(__file__).resolve().parents[2] / "config" / "noark5" / "tests" / "xpath_catalog_2026_05_26.json"


class RunNoark5XpathTestsOperation(BaseOperation):
    definition = OperationDefinition(
        operation_id="run_noark5_xpath_tests_2026",
        name="Noark 5 XPath-tester 2026",
        description="Kjører IKAMR/KDRS Query 2026-testkatalogen med lxml, isolerte testresultater, per-test status og tidsmåling.",
        execution_target=ExecutionTarget.EITHER,
        category="Innhold",
    )
    raw_result_record = True

    def raw_result_identity(self, result, ctx):
        return {"test_id": "noark5-kdrs-query-2026-05-26", "definition_version": "3"}

    def can_run(self, ctx: OperationContext) -> tuple[bool, str]:
        if ctx.work_operations is None:
            return False, "Jobben mangler Arbeid – operasjoner."
        if not CATALOG_PATH.is_file():
            return False, f"Testkatalogen mangler: {CATALOG_PATH}"
        return True, ""

    def run(self, ctx: OperationContext) -> OperationResult:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = Path(ctx.work_operations) / "noark5_tests" / "xpath" / stamp
        ctx.progress(0.02, "Starter Noark 5 XPath-tester 2026")

        def on_test_progress(phase, current, total, test, status, duration):
            job_id = test["legacy"]["job_id"]
            point = test["legacy"].get("test_point") or test.get("normalized_test_point") or "–"
            label = f"Test {current}/{total} – {job_id} / {point} – {test['name']}"
            if phase == "started":
                fraction = 0.02 + (0.94 * (current - 1) / max(total, 1))
                ctx.progress(fraction, label)
                ctx.log(f"TEST START {current}/{total} | {test['test_id']} | {job_id} | {point} | {test['source_xml']} | {test['name']}")
            else:
                fraction = 0.02 + (0.94 * current / max(total, 1))
                suffix = f" | {duration:.3f}s" if duration is not None else ""
                ctx.progress(fraction, f"{label} – {status}{suffix}")
                ctx.log(f"TEST SLUTT {current}/{total} | {test['test_id']} | {job_id} | {point} | {status}{suffix}")

        index = run_catalog(
            CATALOG_PATH,
            ctx.extraction_root,
            out,
            include_disabled=True,
            progress_callback=on_test_progress,
        )
        ctx.progress(1.0, "Noark 5 XPath-tester 2026 fullført")
        s = index.get("summary", {})
        return OperationResult(
            True,
            f"Noark 5-testkatalog kjørt: {s.get('ok', 0)} OK, {s.get('source_missing', 0)} mangler kildefil, "
            f"{s.get('disabled_by_legacy_source', 0)} legacy-deaktivert, {s.get('error', 0)} feil. Resultat: {out}",
            data={"result_index": index, "output_dir": str(out), "catalog": str(CATALOG_PATH)},
        )
