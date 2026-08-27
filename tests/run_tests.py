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


def _iter_test_ids(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_test_ids(item)
        else:
            try:
                yield item.id()
            except Exception:
                yield str(item)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    test_ids = list(_iter_test_ids(suite))

    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
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
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
