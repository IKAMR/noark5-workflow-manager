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
        description="Kjører KDRS Query 2026-testkatalogen og lagrer definisjoner og isolerte testresultater som JSON.",
        execution_target=ExecutionTarget.EITHER,
        category="Innhold",
    )
    raw_result_record = True

    def raw_result_identity(self, result, ctx):
        return {"test_id":"noark5-kdrs-query-2026-05-26","definition_version":"2"}

    def can_run(self, ctx: OperationContext) -> tuple[bool,str]:
        if ctx.work_operations is None: return False,"Jobben mangler Arbeid – operasjoner."
        if not CATALOG_PATH.is_file(): return False,f"Testkatalogen mangler: {CATALOG_PATH}"
        return True,""

    def run(self, ctx: OperationContext) -> OperationResult:
        stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
        out=Path(ctx.work_operations)/"noark5_tests"/"xpath"/stamp
        ctx.progress(0.05,"Starter Noark 5 XPath-testkatalog 2026")
        index=run_catalog(CATALOG_PATH,ctx.extraction_root,out,include_disabled=True)
        ctx.progress(1.0,"Noark 5 XPath-tester 2026 fullført")
        s=index.get("summary",{})
        return OperationResult(True,f"XPath-testkatalog kjørt: {s.get('ok',0)} OK, {s.get('source_missing',0)} mangler kildefil, {s.get('disabled_by_legacy_source',0)} legacy-deaktivert, {s.get('error',0)} feil. Resultat: {out}",data={"result_index":index,"output_dir":str(out),"catalog":str(CATALOG_PATH)})
