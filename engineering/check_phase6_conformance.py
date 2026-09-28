"""Inspect the 26 Phase 6 obligations that a behavioral CTest cannot prove.

Each printed ID names a concrete source, configuration, or governance inspection.
The trusted verifier binds this script, selected IDs, and its log to the candidate.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TASK_FILES = {
    26: ("stimulation_journal", "bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f"),
    27: ("stimulation_guard", "c518c5e4fcb2055666db25cb62018769e7f56ae4"),
    28: ("stimulation_actions", "4d3985855ef7a62b68aa4c66d3b7df032b29f5e9"),
    29: ("stimulation_matrix", "70e98d7a3033ca9f0f5a919c742f0c0e3f43d785"),
}
BASELINES = {
    26: "1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d",
    27: TASK_FILES[26][1], 28: TASK_FILES[27][1], 29: TASK_FILES[28][1],
}
KINDS = {
    26: {1: "layout", 2: "dependencies", 18: "offline", 19: "content",
         20: "documentation", 21: "governance", 22: "gate"},
    27: {2: "dependencies", 4: "bounded_values", 17: "content",
         18: "documentation", 19: "governance", 20: "gate"},
    28: {1: "layout", 2: "dependencies", 21: "content",
         22: "documentation", 23: "governance", 24: "gate"},
    29: {1: "layout", 2: "dependencies", 3: "fixture", 22: "offline",
         23: "content", 24: "governance", 25: "gate"},
}
ALLOWED_PUBLIC_INCLUDES = {
    26: {"validation_session.hpp"},
    27: {"contract.hpp", "result.hpp", "validation_session.hpp"},
    28: {"contract.hpp", "item.hpp", "result.hpp", "validation_session.hpp",
         "stimulation_guard.hpp", "stimulation_journal.hpp"},
    29: {"contract.hpp", "item.hpp", "observation.hpp", "provider.hpp",
         "loopback_provider.hpp", "endpoint_route_lifecycle.hpp",
         "stimulation_actions.hpp", "stimulation_guard.hpp",
         "stimulation_journal.hpp", "validation_session.hpp"},
}
PUBLIC_METHODS = {
    26: ("open", "open_local_file", "recover", "last_recovery", "snapshot",
         "recovered_intents", "recovered_outcomes", "journal_then_emit", "resolve"),
    27: ("open", "authorize", "snapshot", "is_open", "status"),
    28: ("reserve_emission", "finish_emission", "execute", "drain", "close",
         "revoke", "expire", "mark_evidence_incomplete", "snapshot"),
}
CONTENT_PATTERN = re.compile(
    r"(?:AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
    r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b|/" r"home/[^/\s]+/)"
)


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(detail)


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def owned_paths(task: int) -> list[Path]:
    if task == 29:
        return sorted((ROOT / "tests/xcom/stimulation_matrix").glob("*.cpp")) + [
            ROOT / "tests/xcom/stimulation_matrix/test_support.hpp"]
    name = TASK_FILES[task][0]
    return [ROOT / f"src/xverse/xcom/include/xverse/xcom/{name}.hpp",
            ROOT / f"src/xverse/xcom/src/{name}.cpp"]


def content_paths(task: int) -> list[Path]:
    """Inventory scoped source, tests, work products, and current task evidence."""
    docs = ROOT / f"docs/engineering/xcom/t0{task}"
    tests = ROOT / "tests/xcom" / TASK_FILES[task][0]
    paths = set(owned_paths(task))
    for folder in (docs, tests):
        paths.update(path for path in folder.rglob("*") if path.is_file())
    paths.add(ROOT / f"reports/xcom-queue/t0{task}-package.json")
    for group in ("requirements", "architecture/components", "unit-specifications",
                  "validation/scenarios"):
        paths.update((ROOT / "engineering" / group).glob(f"T0{task}-*.json"))
    if task == 29:
        paths.update((ROOT / "engineering").glob("*phase6*.py"))
        paths.update((ROOT / "engineering/verification/measures").glob("*.json"))
        paths.add(ROOT / "engineering/trace/links.json")
        paths.add(ROOT / "reports/repair-review-index.md")
        for path in (ROOT / "engineering/stage-results").glob("*.json"):
            if json.loads(path.read_text(encoding="utf-8")).get("task_id") == "T029":
                paths.add(path)
    return sorted(paths)


def scan_content(paths: list[Path]) -> None:
    require(paths and all(path.is_file() for path in paths), "declared content inventory is absent")
    for path in paths:
        require(not CONTENT_PATTERN.search(path.read_text(encoding="utf-8")),
                f"public-content pattern in {path.relative_to(ROOT)}")


def method_documentation(header: str, symbol: str) -> str:
    declarations = list(re.finditer(
        rf"(?m)^[ \t]*(?:\[\[nodiscard\]\][ \t]*)?[^/;\n]*\b{re.escape(symbol)}[ \t]*\(",
        header,
    ))
    require(declarations, f"public declaration {symbol} is absent")
    blocks = []
    for declaration in declarations:
        leading = header[:declaration.start()]
        block = re.search(r"(?:(?:[ \t]*///[^\n]*\n)+)$", leading)
        require(block is not None and "\\brief" in block.group(),
                f"public declaration {symbol} lacks its own Doxygen block")
        blocks.append(block.group())
    return "\n".join(blocks)


def original_changes(task: int) -> dict[str, str]:
    output = git("diff", "--name-status", BASELINES[task], TASK_FILES[task][1])
    return {path: status for status, path in
            (line.split("\t", 1) for line in output.splitlines())}


def inspect(task: int, number: int, kind: str) -> str:
    name = TASK_FILES[task][0]
    paths = owned_paths(task)
    require(all(path.is_file() for path in paths), "task-owned source is absent")
    sources = [path.read_text(encoding="utf-8") for path in paths]
    changes = original_changes(task)
    if kind == "layout":
        original_paths = [path for path in paths
                          if path.relative_to(ROOT).as_posix() in changes]
        require(original_paths and
                all(changes[path.relative_to(ROOT).as_posix()] == "A"
                    for path in original_paths),
                "original task did not add its declared source")
        if task != 29:
            cmake = (ROOT / "src/xverse/xcom/CMakeLists.txt").read_text()
            require(f"xverse_xcom_{name}" in cmake and "XVERSE_XCOM_RUNTIME_TARGETS" in cmake,
                    "runtime target inventory is missing")
        else:
            require(not any(path.startswith("src/xverse/xcom/") and
                            path != "src/xverse/xcom/CMakeLists.txt" for path in changes),
                    "original T029 task changed production source")
            cmake = (ROOT / "src/xverse/xcom/CMakeLists.txt").read_text()
            matrix = cmake.split("# T029 complete stimulation verification matrix tests.", 1)[1]
            require(all(re.search(rf"^\s+{kind}\s*$", matrix, re.MULTILINE)
                        for kind in ("permit_action_matrix", "journal_recovery", "zero_emission",
                                     "provenance", "lease_drain", "concurrency")) and
                    'PROPERTIES LABELS "t029-${matrix_label}"' in matrix and
                    'string(REPLACE "_" "-" matrix_label "${matrix_kind}")' in matrix,
                    "matrix test labels are missing")
        return f"{len(paths)} task-owned additions and declared CMake registration inspected"
    if kind == "dependencies":
        found = set()
        for body in sources:
            found.update(re.findall(r'^#include\s+"xverse/xcom/([^\"]+)"', body, re.MULTILINE))
        unexpected = found - ALLOWED_PUBLIC_INCLUDES[task] - {f"{name}.hpp"}
        require(not unexpected, f"undeclared X-COM includes: {sorted(unexpected)}")
        require(not any(re.search(r"#include\s+[<\"](?:grpc|google/protobuf|boost|curl)", body)
                        for body in sources), "external dependency include found")
        return f"{len(found)} public X-COM includes and no prohibited external include inspected"
    if kind == "bounded_values":
        body = sources[0]
        for value in ("StimulationPolicy", "StimulationRequest", "SchemaKey", "ServiceOwner",
                      "ResolvedTime", "GuardDiagnostic", "GuardSnapshot"):
            require(f"sizeof({value}) <=" in body, f"missing size bound for {value}")
        require("!std::is_constructible_v<StimulationRequest, std::vector<std::uint8_t>>" in body,
                "payload construction prohibition absent")
        require("kGuardMaxSchemas" in body, "schema-table bound absent")
        return "seven declared value sizes and payload-construction prohibition inspected"
    if kind == "offline":
        executable = "\n".join(re.sub(r"/\*.*?\*/|//[^\n]*", "", body, flags=re.DOTALL)
                               for body in sources)
        require(not re.search(r"\b(?:socket|connect|getaddrinfo|curl_easy|dlopen|fork|execve|"
                              r"popen|getenv|system)\s*\(", executable),
                "prohibited ambient, network, process, or dynamic-load call found")
        return f"{len(paths)} task-owned files scanned for prohibited host operations"
    if kind == "content":
        reviewed = content_paths(task)
        scan_content(reviewed)
        return (f"{len(reviewed)} scoped source, test, work-product, and evidence files scanned; "
                "independent content review remains required")
    if kind == "documentation":
        header = sources[0]
        require(f"\\brief T0{task}" in header and "\\ingroup xcom_stim" in header,
                "header block lacks task and group")
        require(not git("diff", "--name-only", BASELINES[task], "HEAD", "--", "Doxyfile"),
                "repository Doxygen configuration changed")
        for marker in ("\\ownership", "\\lifetime", "\\thread_safety", "\\failure"):
            require(marker in header, f"missing declaration contract marker {marker}")
        for symbol in PUBLIC_METHODS[task]:
            block = method_documentation(header, symbol)
            if task == 26 and symbol in ("open", "open_local_file", "recover", "resolve"):
                require("in-flight" in block, f"{symbol} omits the active-callback contract")
        if task == 26:
            design = (ROOT / "docs/engineering/xcom/t026/detailed-design.md").read_text()
            require("in-flight emission callback" in design and
                    "without scanning, rebinding, or creating a file" in design,
                    "journal detailed design omits active-callback recovery contract")
        return (f"{len(PUBLIC_METHODS[task])} public method Doxygen blocks, task header contract, "
                "and unchanged Doxyfile inspected")
    if kind == "governance":
        for predecessor in ("t007", "t008", "t009"):
            require(not git("diff", "--name-only", BASELINES[26], "HEAD", "--",
                            f"docs/engineering/xcom/{predecessor}"),
                    f"accepted {predecessor} work products changed")
        for path in ("docs/engineering/xcom/t010/design-units.md",
                     "docs/engineering/xcom/t010/unit-design.json"):
            diff = git("diff", "--unified=0", BASELINES[26], "HEAD", "--", path)
            removed = [line[1:].replace("planned", "established")
                       for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
            added = [line[1:] for line in diff.splitlines()
                     if line.startswith("+") and not line.startswith("+++")]
            require(removed == added, f"accepted {path} has changes beyond planned-to-established status")
        body = (ROOT / f"docs/engineering/xcom/t0{task}/requirements.md").read_text()
        for marker in ("REF-002", "unchanged", "promoted", "allocated"):
            require(marker in body, f"missing governance disposition {marker}")
        return "T007-T009 unchanged, T010 only planned-to-established, and task disposition declarations inspected"
    if kind == "gate":
        folder = ROOT / f"docs/engineering/xcom/t0{task}"
        for name in ("requirements.md", "architecture.md", "detailed-design.md",
                     "unit-specifications.md", "verification-plan.md", "implementation.md"):
            require((folder / name).is_file(), f"missing task work product {name}")
        require(any(path.startswith("tests/") for path in changes), "task test change missing")
        if task != 29:
            require(any(path.startswith("src/xverse/xcom/") for path in changes),
                    "task source change missing")
        require((ROOT / f"reports/xcom-queue/t0{task}-package.json").is_file(),
                "task package manifest missing")
        require(not git("diff", "--check"), "candidate has whitespace errors")
        return "six work products, original task source/test inventory, and whitespace inspected; trusted build/test measures are separate"
    if kind == "fixture":
        body = (ROOT / "tests/xcom/stimulation_matrix/test_support.hpp").read_text()
        for marker in ("kMaxThreads = 4U", "kMaxDurableBytes = 16U * 1024U",
                       "kMaxInjectionPoints = 4U", "class MatrixFixture", "class FaultStorage",
                       "class RecordingEmitter", "class ObservationBridge"):
            require(marker in body, f"fixture bound/member absent: {marker}")
        return "declared finite fixture bounds and composed accepted seams inspected"
    raise ValueError(f"unknown inspection kind {kind}")


def main() -> None:
    # Verify every declared system anchor and every selected repair case from the source,
    # independently of the generated trace records. The source documents are authoritative.
    for task, requirements in KINDS.items():
        body = (ROOT / f"docs/engineering/xcom/t0{task}/requirements.md").read_text()
        blocks = re.split(r"(?=^- \*\*T0\d+-SR-\d{3} \[)", body, flags=re.MULTILINE)
        for block in blocks:
            match = re.match(r"^- \*\*(T0\d+-SR-\d{3}) \[", block)
            if not match:
                continue
            requirement_id = match.group(1)
            declared = set(re.findall(r"XCOM-SYS-(?:FR|SC)-\d{3}", block.split("\n## ", 1)[0]))
            record = json.loads((ROOT / f"engineering/requirements/{requirement_id}.json").read_text())
            require(set(record["parents"]) == declared,
                    f"{requirement_id}: system ancestry differs from the accepted task text")
        for number, kind in requirements.items():
            requirement_id = f"T0{task}-SR-{number:03}"
            record = json.loads((ROOT / f"engineering/requirements/{requirement_id}.json").read_text())
            require(record.get("verification_mode") == "conformance" and
                    record.get("conformance_check_id") == requirement_id,
                    f"{requirement_id}: conformance identity is absent")
            detail = inspect(task, number, kind)
            print(f"PASS {requirement_id.replace('-', '_')} {kind}: {detail}")
    unit = json.loads((ROOT / "engineering/verification/measures/unit.json").read_text())
    selected = set(unit["test_ids"])
    traced = {case["id"] for path in (ROOT / "engineering/unit-specifications").glob("T02*-*.json")
              for case in json.loads(path.read_text())["unit_cases"]}
    require(selected <= traced, f"selected unit cases lack a unit specification: {sorted(selected - traced)}")
    print("26 conformance inspections passed; all declared system anchors and selected unit cases traced")


if __name__ == "__main__":
    main()
