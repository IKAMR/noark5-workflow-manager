from __future__ import annotations

import io
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from version import VERSION


def _iter_tests(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_tests(item)
        else:
            yield item


class CompactTextTestResult(unittest.TextTestResult):
    def getDescription(self, test):
        method = getattr(test, "_testMethodName", None)
        return method or str(test)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    tests = list(_iter_tests(suite))
    test_ids = []
    for test in tests:
        try:
            test_ids.append(test.id())
        except Exception:
            test_ids.append(str(test))

    # Re-discover because iterating the suite above consumes nested suites in some Python versions.
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")

    stream = io.StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        resultclass=CompactTextTestResult,
    )
    result = runner.run(suite)
    output = stream.getvalue()
    print(output, end="")

    status = "PASS" if result.wasSuccessful() else "FAIL"
    now = datetime.now().astimezone()
    out_dir = ROOT / "docs" / "test-results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"v{VERSION}.md"

    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = result.testsRun - failures - errors - skipped

    lines = [
        f"# Testresultat v{VERSION}",
        "",
        f"**Dato/tid:** {now.isoformat(timespec='seconds')}",
        f"**Resultat:** {status}",
        "",
        "## Oppsummering",
        "",
        f"- Tester kjørt: {result.testsRun}",
        f"- Bestått: {passed}",
        f"- Feilet: {failures}",
        f"- Feil under kjøring: {errors}",
        f"- Hoppet over: {skipped}",
        "",
        "## Tester",
        "",
    ]
    lines.extend(f"- `{test_id}`" for test_id in test_ids)
    lines.extend([
        "",
        "## Full testutskrift",
        "",
        "```text",
        output.rstrip(),
        "```",
        "",
    ])
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Testresultat skrevet til: {out_path.relative_to(ROOT)}")

    summary_path = out_dir / ".last-test-summary.txt"
    summary_path.write_text(
        "\n".join([
            f"TOTAL={result.testsRun}",
            f"PASSED={passed}",
            f"FAILED={failures}",
            f"ERRORS={errors}",
            f"SKIPPED={skipped}",
        ]) + "\n",
        encoding="ascii",
    )

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
