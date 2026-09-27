# T011 Verification Plan — Named Checks, Commands, and Expected Results (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T011 |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `5050666bf38fc98920dc455a85a88c08c46a2133` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | repository-owned Python 3.11-compatible offline admission checker plus the deterministic Fabro gate; no C++/GTest/CTest case is added by T011 |

This plan is written **before** implementation. The implementation must realise every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
Because T011 is a documentation/governance work-product task, the deterministic gate for T011 runs no
C++/Python test suite; the executable checks are the existing offline admission checker's self-test, the
register validators, and documentation inspection.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T011 5050666bf38fc98920dc455a85a88c08c46a2133
```

For T011 this gate requires:

- `docs/engineering/xcom/t011/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present;
- the T011 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the plan
  stage leaves it unchecked, per the stage instruction);
- a changed-path set containing **no** `src/`, `tests/`, or `xdl/` path (T011 is a work-product task);
- `git diff --check <baseline> --` clean.

## 3. Supporting commands (same tools, offline)

```sh
python3 scripts/xcom_dependency_preflight.py --self-test
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git rev-parse 5050666bf38fc98920dc455a85a88c08c46a2133
git diff --name-only 5050666bf38fc98920dc455a85a88c08c46a2133 --
git diff --check 5050666bf38fc98920dc455a85a88c08c46a2133 --
```

`git rev-parse` for the baseline must print the baseline SHA, proving the binding resolves. The
`--self-test` run must report all controlled positive and negative fixtures passing. The register validators
must still pass with the shared `task-ownership` reconciliation unchanged in substance.

> Recorded plan-stage observation (not candidate evidence): at baseline
> `5050666bf38fc98920dc455a85a88c08c46a2133`, `python3 scripts/xcom_dependency_preflight.py --self-test`
> reported `Ran 39 tests ... OK` (exit 0). This is a baseline sanity observation; acceptance still requires
> fresh candidate-bound evidence per §6.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T011 entry exists and states the admission scope |
| CHK-02 | Build envelope | inspect `CMakeLists.txt`, `cmake/XComWarnings.cmake` | Ninja-only, C++20 without extensions, `BUILD_TESTING=ON`, `-Wall -Wextra -Wpedantic -Werror`; the warning-rejection probe is `EXCLUDE_FROM_ALL` and must fail |
| CHK-03 | Sanitizer/analysis capability and probes | inspect `CMakeLists.txt`, `cmake/XComOfflineDependencies.cmake`; read `detailed-design.md` §4.5 | the sanitizer capability is recorded as compiler-provided with an opt-in probe obligation; static-analysis tool (clang-tidy 14.0.0) is pinned; no sanitizer is falsely claimed executed |
| CHK-04 | Manifest/lock schema | inspect `dependency-lock.md` and the checker's `PackageSpec` set | exactly twelve records; single-segment filenames; 64-hex digests; positive sizes; package/version/source/license present |
| CHK-05 | Archive identity and payload binding | inspect the checker phases in `detailed-design.md` §5.1 | archives verified against manifest **and** lock; extracted payload compared node-by-node; no archive-only admission |
| CHK-06 | Offline inputs and disabling | inspect `cmake/XComOfflineDependencies.cmake` | both explicit inputs required; registries and FetchContent disabled; imported targets only beneath the prefix |
| CHK-07 | Generated-code provenance | inspect `dependency-lock.md` §"Admitted component and generated-code provenance" | `protoc`/`protobuf-compiler` and `protobuf-compiler-grpc` identities and SHA-256 recorded; input-schema/generation-command requirement stated |
| CHK-08 | Classified decision model | inspect `detailed-design.md` §5.1–§5.2 and the checker | every failure phase maps to a stable exit class 2–15; success is only `XCOM-BLD-I000` with `admitted: true`; diagnostics sorted |
| CHK-09 | Boundedness, no network/install/writes | source inspection of the checker + over-bound probes | local reads, SHA-256, bounded subprocesses, temporary trees only; no resolver/client; no install; no input modification; single-threaded |
| CHK-10 | Documentation completeness | inspect `build-environment.md`, `dependency-lock.md` | licenses, hashes, explicit input names, prototype-only/no-runtime boundary, generated-code statement, and environment/ABI limits present |
| CHK-11 | Offline reconstruction | inspect `build-environment.md` §"Deterministic offline prefix reconstruction" | extraction-only (`dpkg-deb -x`), ordered by retained filename, no apt/maintainer scripts/network, stale-prefix rejection |
| CHK-12 | Host evidence contract | inspect `build-environment.md` §"Repository-owned host verification evidence" | five measures named; network-disabled enforced isolation; per-measure log/manifest and `command_argv`/`exit_code`/`outcome`; log/manifest hashes; `index.json` |
| CHK-13 | Public-safety scan of admission docs | manual inspection of both T-INTG docs | no credential, private address, unrestricted payload, proprietary excerpt, or sensitive deployment value |
| CHK-14 | Public-safety scan of T011 work products | manual inspection + token scan | no absolute host path, private address, credential, or unrestricted payload in the T011 work products |
| CHK-15 | Work-product boundary | `git diff --name-only <baseline> --` | no `src/`, `tests/`, or `xdl/` path; no edit to `build-environment.md`, `dependency-lock.md`, `scripts/xcom_dependency_preflight.py`, `cmake/*.cmake`, `CMakeLists.txt`, `Doxyfile`, or `scripts/check_doxygen.py` |
| CHK-16 | Work-product completeness and consistency | file presence + cross-read | the six named work products exist; every requirement in `requirements.md` §3–§4 maps to ≥ 1 check in §4/§5; the package record lists every changed path and binds the candidate revision |
| CHK-17 | Requirement-to-check coverage and checkbox | cross-read `requirements.md` §10 vs §4/§5; read tasks.md | every requirement covered; every check states an expected result; the T011 checkbox is complete in the implementation stage only |
| CHK-18 | Register reconciliation and REF-002 | run the T007/T008/T009/T010 validators; inspect the REF-002 disposition | validators pass; the shared `task-ownership` change is limited to re-validated reconciliation; `ref002.disposition == unchanged` with empty `promoted` |
| CHK-19 | Deterministic gate and diff hygiene | `xcom_feature_gate.py verify T011 <baseline>`; `git diff --check` | exit 0; the diff is whitespace-clean |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared nonzero class (or a documentation
failure) with **no** partial success and no output claiming admission. Negative cases NEG-02..NEG-23 are
exercised by the existing offline admission checker's controlled fixtures
(`scripts/xcom_dependency_preflight.py --self-test`); NEG-01 and NEG-24..NEG-33 are documentation/governance
inspections and register-validator probes.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | Select a non-Ninja generator or disable `BUILD_TESTING` | configuration error (`POLICY_INVALID`), no build |
| NEG-02 | Remove the warning-as-error option from the policy | warning-rejection probe builds; admission fails `POLICY_INVALID` (11) |
| NEG-03 | Drop `-Wall`/`-Wextra`/`-Wpedantic` from the published options | policy/evidence mismatch `POLICY_INVALID` (11) |
| NEG-04 | Manifest is not a JSON array, or has ≠ 12 records | `MANIFEST_INVALID` (3) |
| NEG-05 | A manifest record has an extra or missing field | `MANIFEST_INVALID` (3) |
| NEG-06 | Duplicate filename, or a filename with a directory component | `MANIFEST_INVALID` (3) |
| NEG-07 | A sibling retained archive is absent | `PACKAGE_MISSING` (4) |
| NEG-08 | An archive's byte size or SHA-256 differs | `HASH_MISMATCH` (5) |
| NEG-09 | An explicit input is unset, relative, or names the wrong node type | `INPUT_MISSING` (2) |
| NEG-10 | The manifest/prefix is unreadable | `IO_ERROR` (12) |
| NEG-11 | A required executable (`protoc`/`grpc_cpp_plugin`) is absent | `TOOL_MISSING` (6) |
| NEG-12 | A required admitted header is absent | `HEADER_MISSING` (8) |
| NEG-13 | A required admitted library is absent | `LIBRARY_MISSING` (9) |
| NEG-14 | Required pkg-config or Debian control metadata is absent/unreadable | `METADATA_MISSING` (10) |
| NEG-15 | A tool, header, pkg-config, or Debian version/source differs from the lock | `VERSION_MISMATCH` (7) |
| NEG-16 | A generated-code provenance record is incomplete (missing generator hash or input-schema field) | documentation `POLICY_INVALID` (11), not admitted |
| NEG-17 | Prefix payload content, file type, or symlink target differs from the extracted archives | `PAYLOAD_MISMATCH` (15) |
| NEG-18 | A retained package cannot be read | `IO_ERROR` (12) |
| NEG-19 | An extracted payload file cannot be read | `IO_ERROR` (12) |
| NEG-20 | Temporary-directory/reference extraction fails | `IO_ERROR` (12) or `PROBE_FAILED` (13) |
| NEG-21 | A bounded probe exceeds its time limit | `TIMEOUT` (14) |
| NEG-22 | `xcom-build-policy.json`/`compile_commands.json` policy evidence drifts | `POLICY_INVALID` (11) |
| NEG-23 | The intentional-warning rejection probe builds successfully | `POLICY_INVALID` (11), admission not reported |
| NEG-24 | Diagnostics are emitted unsorted or duplicated | determinism check fails (no admission) |
| NEG-25 | A failure record sets `admitted: true` | decision check fails |
| NEG-26 | A phase failure maps to an unknown/absent exit class | decision check fails |
| NEG-27 | A failure omits its diagnostic or returns exit 0 | decision check fails |
| NEG-28 | Several defects coexist and the wrong class is returned | the numerically lowest applicable class is required |
| NEG-29 | An archive is admitted by hash alone while its prefix payload is absent | `PAYLOAD_MISMATCH` (15) |
| NEG-30 | A missing/stale evidence record is presented as admission | evidence check fails; no acceptance |
| NEG-31 | The checker imports/uses a network client or resolver | CHK-09 source inspection fails |
| NEG-32 | A verification run writes to either explicit input or the repository | CHK-09 source inspection fails |
| NEG-33 | A verification run spawns an unbounded subprocess or a thread | CHK-09 source inspection fails |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline SHA;
- `command_argv`, `exit_code`, and observed output for the deterministic gate and each supporting command
  (bounded stdout/stderr);
- the `--self-test` result (test count and outcome);
- the changed-path list and the package record `reports/xcom-queue/t011-package.json` with per-file SHA-256;
- the five `VM-BLD-*` measures **when** they are run under T035–T038 (T011 defines the contract; T011 does not
  run them).

Public evidence omits host-specific, prefix, manifest, temporary, and private-store absolute paths. Missing,
stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T011 verification is complete when: the deterministic gate passes (CHK-16/CHK-17/CHK-19); every nominal check
in §4 has its expected result; every negative case in §5 fails closed as stated; the register validators still
pass with REF-002 unchanged (CHK-18); the change is confined to the work-product boundary (CHK-15); and a
separate DeepSeek internal review records a passing verdict with no findings. This does not constitute user
acceptance, which remains T041.

## 8. Requirement-to-check coverage

| Requirement | Checks |
| --- | --- |
| T011-STK-001 | CHK-01, CHK-11, CHK-16 |
| T011-STK-002 | CHK-04, CHK-05, NEG-04..NEG-10 |
| T011-STK-003 | CHK-07, NEG-16 |
| T011-STK-004 | CHK-08, NEG-11..NEG-30 |
| T011-STK-005 | CHK-13, CHK-14 |
| T011-SR-001 | CHK-02, CHK-03, NEG-01..NEG-03 |
| T011-SR-002 | CHK-04, NEG-04..NEG-06 |
| T011-SR-003 | CHK-05, NEG-07, NEG-08, NEG-17 |
| T011-SR-004 | CHK-06, CHK-11, NEG-09, NEG-10 |
| T011-SR-005 | CHK-07, NEG-16 |
| T011-SR-006 | CHK-03, CHK-07 |
| T011-SR-007 | CHK-08, NEG-11..NEG-30 |
| T011-SR-008 | CHK-09, NEG-31..NEG-33 |
| T011-SR-009 | CHK-10, CHK-13, CHK-14 |
| T011-SR-010 | CHK-12 |
| T011-SR-011 | CHK-15, CHK-16 |
| T011-SR-012 | CHK-16, CHK-17, CHK-19 |
| T011-SR-013 | CHK-18, CHK-19 |
