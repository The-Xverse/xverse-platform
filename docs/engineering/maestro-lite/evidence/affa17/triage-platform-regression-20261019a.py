"""Read-only triage of one terminal platform regression log; no execution, no repair.

Usage: python3 -I triage-platform-regression-20261019a.py <run-directory> <output.json>

Parses pytest's terminal output (-q -ra) retained in <run-directory>/source.log,
extracts every FAILED/ERROR short-summary node, every traceback section, the final
summary line, and classifies each failed node by whether its traceback contains the
missing-build-tool signature. Classification is textual evidence, not a cause claim.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

run = Path(sys.argv[1]).resolve(strict=True)
output = Path(sys.argv[2])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
log_path = run / "source.log"
text = log_path.read_text(errors="replace")
receipt_path = run / "source-receipt.json"
receipt = json.loads(receipt_path.read_bytes()) if receipt_path.is_file() else None

BUILD_SIGNATURE = "No module named build"
WHEEL_SIGNATURE = "wheel build failed"

short = []
for line in text.splitlines():
    match = re.match(r"^(FAILED|ERROR) (\S+?)(?: - (.*))?$", line)
    if match:
        short.append(dict(outcome=match.group(1), nodeid=match.group(2), message=match.group(3)))

sections = {}
if "= FAILURES =" in text or "= ERRORS =" in text:
    body = text.split("= FAILURES =", 1)[-1] if "= FAILURES =" in text else text.split("= ERRORS =", 1)[-1]
    body = re.split(r"\n=+ short test summary info =+\n", body, maxsplit=1)[0]
    # pytest pads short names with many underscores and long names with a single one;
    # the frame separator "_ _ _ ..." is excluded because its name part is only underscores.
    parts = re.split(r"\n_+ ([^\n]*?[^_\s][^\n]*?) _+\n", "\n" + body)
    for name, content in zip(parts[1::2], parts[2::2]):
        sections[name.strip()] = content

summary = None
for line in reversed(text.splitlines()):
    if re.search(r"\d+ (passed|failed|error)", line) and line.startswith("="):
        summary = line.strip("= ")
        break

classified = []
for item in short:
    test_name = item["nodeid"].split("::")[-1]
    section = sections.get(test_name, "")
    classified.append(dict(
        item,
        traceback_found=bool(section),
        traceback_sha256=hashlib.sha256(section.encode()).hexdigest() if section else None,
        mentions_missing_build_module=BUILD_SIGNATURE in section or BUILD_SIGNATURE in (item["message"] or ""),
        mentions_wheel_build_failed=WHEEL_SIGNATURE in section or WHEEL_SIGNATURE in (item["message"] or ""),
        traceback_last_lines=section.strip().splitlines()[-12:] if section else [],
    ))

result = dict(
    run_directory=str(run), log_sha256=sha(log_path), log_bytes=log_path.stat().st_size,
    receipt_present=receipt is not None,
    receipt=receipt,
    pytest_summary_line=summary,
    short_summary_count=len(short),
    failed_count=sum(1 for i in short if i["outcome"] == "FAILED"),
    error_count=sum(1 for i in short if i["outcome"] == "ERROR"),
    traceback_sections_found=len(sections),
    failures=classified,
    all_failures_carry_missing_build_signature=bool(classified) and all(
        c["mentions_missing_build_module"] or c["mentions_wheel_build_failed"] for c in classified),
    failures_without_build_signature=[c["nodeid"] for c in classified
                                      if not (c["mentions_missing_build_module"] or c["mentions_wheel_build_failed"])],
    textual_classification_only=True, cause_confirmed=False, repair_applied=False, successor_run_started=False,
)
with output.open("x") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps({k: result[k] for k in ("pytest_summary_line", "failed_count", "error_count",
                                          "traceback_sections_found", "all_failures_carry_missing_build_signature",
                                          "failures_without_build_signature")}))
