# T035 Verification Plan — Exact-Candidate Verification Matrix and Repository-Owned Results

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T035 (capability 007, slice `T-INTG`/evidence) |
| Stage / role | plan → verification design |
| Revision | 1 (Phase 8 exact-candidate verification slice) |
| Baseline revision | `dab68568bd8d189b14c7a4a9e3a9c325085a7529` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

"Verified" means the named command, case, or inspection exists, is deterministic, and passes at the recorded
candidate revision. It is not a deployed-service, remote-tool, compatibility, performance, or production-readiness
claim.

## 2. Verification environment

- Admitted offline X-COM build envelope (T011): admitted `protoc` 3.12.4, admitted GTest prefix, admitted
  standard library and in-process libraries; no network, DNS, TLS, legacy binary, or production workload.
- C++20, warning-as-error (T012), Ninja build, GoogleTest discovery; a separate ASan/UBSan configuration for the
  sanitizer measure.
- Python 3.11 or newer for the XDL plan tests, the conformance recheck, and the evidence report generation.
- Whole-system integration is only the trusted target-repository measure (`run_xcom_phase8_tests.py integration`)
  over the assembled pinned platform revision; candidate-local runs are labelled candidate-local.

## 3. Requirements-to-check matrix

| Requirement | Primary checks | Verification measure |
| --- | --- | --- |
| T035-STK-001 | CHK-01…CHK-06 | unit / integration / validation / sanitizer / static_analysis / conformance |
| T035-STK-002 | CHK-01, CHK-07…CHK-11 | unit / integration / validation / report |
| T035-STK-003 | CHK-12, CHK-13 | inspection / validation |
| T035-STK-004 | CHK-14, CHK-15 | trace validation |
| T035-STK-005 | CHK-16, CHK-17, CHK-18 | diff / register / gate |
| T035-SR-001 | CHK-01, CHK-02 | unit |
| T035-SR-002 | CHK-03 | unit / discovery inspection |
| T035-SR-003 | CHK-04 | unit |
| T035-SR-004 | CHK-05 | unit |
| T035-SR-005 | CHK-06 | sanitizer |
| T035-SR-006 | CHK-07 | static_analysis |
| T035-SR-007 | CHK-08 | validation |
| T035-SR-008 | CHK-09 | integration |
| T035-SR-009 | CHK-10 | conformance |
| T035-SR-010 | CHK-11, CHK-19 | report inspection |
| T035-SR-011 | CHK-11, CHK-19 | report inspection |
| T035-SR-012 | CHK-12 | report inspection |
| T035-SR-013 | CHK-13 | public-safety inspection |
| T035-SR-014 | CHK-16, CHK-17 | diff / discovery inspection |
| T035-SR-015 | CHK-14, CHK-18, CHK-20 | trace / register / gate |
| T035-SR-016 | CHK-05, CHK-13 | forbidden-API inspection |

## 4. Named checks

| Check | Description | Requirement |
| --- | --- | --- |
| CHK-01 | the candidate builds warning-as-error at the exact candidate revision and the full discovered CTest suite runs and passes (`100% tests passed`, `0 tests failed`) | T035-SR-001 |
| CHK-02 | the recorded discovered and passed counts are retained with the command argv, exit status, and log hash | T035-SR-001, T035-STK-002 |
| CHK-03 | the inherited T016/T020/T026–T034 discovered inventory is unchanged in kind and no target/label/value is reduced; the preserved suites pass | T035-SR-002 |
| CHK-04 | the accepted negative-case matrix passes with its stable outcomes | T035-SR-003 |
| CHK-05 | the accepted concurrency and recovery cases pass and repeated runs are equal; no verdict depends on ambient wall-clock time | T035-SR-004, T035-SR-016 |
| CHK-06 | the separate ASan/UBSan build runs the full suite and its outcome is recorded | T035-SR-005 |
| CHK-07 | the `cppcheck` measure over `src/xverse/xcom/src` exits `0` or its failure is recorded | T035-SR-006 |
| CHK-08 | all existing Python tests execute and their collected/passed count and outcome are recorded | T035-SR-007 |
| CHK-09 | the trusted whole-system integration measure assembles the pinned revision and passes; its assembled-revision identity is recorded | T035-SR-008 |
| CHK-10 | the inherited Phase 6 conformance recheck passes all 26 named inspections | T035-SR-009 |
| CHK-11 | `reports/xcom-queue/t035-verification.json` exists and carries `commands`, `outcomes`, `hashes`, `environment`, bounded logs, and the exact-candidate identity | T035-SR-010, T035-SR-011 |
| CHK-12 | the report records compiler/CMake/Ninja/`cppcheck`/Python and admitted toolchain/manifest/GTest-prefix identities and hashes, with no host-specific absolute path in the public report | T035-SR-012 |
| CHK-13 | the committed report, work products, and bounded logs contain no payload byte, permit content, secret, private address, host path, or proprietary excerpt | T035-SR-013, T035-SR-016 |
| CHK-14 | `validate_trace` passes; every T035 requirement carries `refines`, `allocated_to`, `implemented_by`, and `verified_by`, and every T035 unit carries `decomposes_to`, `implemented_by`, `verified_by`, and `analyzed_by` | T035-SR-015 |
| CHK-15 | every T035 software requirement is covered by at least one named case or inspection; the anchor table in `requirements.md` §5 is complete | T035-STK-004 |
| CHK-16 | the baseline-versus-candidate diff changes no accepted production source, header, contract, schema, register, XDL profile, or test; the only shared edits are the additive T035 records, the additive trace links, the content-only measure refresh, `engineering/project.json`, `reports/review-index.md`, and the T035 checkbox (implementation stage) | T035-SR-014 |
| CHK-17 | each refreshed measure descriptor keeps its `id`, `revision`, and `kind`; no accepted `verified_by`/`analyzed_by` link becomes stale; no build target is added | T035-SR-014 |
| CHK-18 | the T007 ownership register and the T008/T009/T010 models are reconciled without rewrite; REF-002 stays `unchanged` with an empty `promoted` list; T035 is recorded implemented and T036–T041 allocated | T035-SR-015 |
| CHK-19 | every recorded outcome uses the trusted discovery check; a missing, stale, mismatched, skipped, or failed measure is `failed` and an unavailable input is `blocked`, never `pass` | T035-SR-011 |
| CHK-20 | `xcom_phase8_gate.py verify T035 <baseline>` passes with the report present, the T035 checkbox marked complete only at implementation, and the T035 unit measure passing | T035-SR-015 |

## 5. Executable suites, negative cases, and the exact evidence report

| Measure | Command (portable descriptor) | Discovery check |
| --- | --- | --- |
| unit | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py unit` | `100% tests passed` |
| integration | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py integration` | `100% tests passed` |
| validation | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py validation` | `[1-9][0-9]* passed` |
| static_analysis | `cppcheck --error-exitcode=1 --quiet --std=c++20 --language=c++ --suppress=invalidLifetime src/xverse/xcom/src` | exit code `0` |
| conformance | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_conformance.py` | `26 conformance inspections passed` |
| sanitizer | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py sanitizer` | `100% tests passed` |
| python | `python3 -m pytest -q` | `[1-9][0-9]* passed` |

**Exact evidence report.** `reports/xcom-queue/t035-verification.json` is the task-owned evidence report; it is
required to contain `commands`, `outcomes`, `hashes`, and `environment`, plus bounded logs and the exact-candidate
identity (§4 of `detailed-design.md`). It is generated at the implementation stage from the executed commands; the
plan stage records only the schema and route and does not fabricate results.

**Task-owned route.** There is no new executable test target: T035's route is the admitted offline build, the
full CTest suite, the ASan/UBSan build, the `cppcheck` measure, the Phase 6 conformance recheck, the trusted
whole-system integration measure, and the Python suite, each recorded in the report. The T035 selected case set
(`detailed-design.md` §6) names only already-discovered CTest cases, so the discovered inventory is unchanged.

### Negative cases (`NEG-###`)

- **NEG-01** — a changed accepted production source, test, target, label, command, or expected value: CHK-03 and
  CHK-16 fail closed.
- **NEG-02** — a recorded `pass` whose trusted discovery check is not satisfied: CHK-19 fails closed.
- **NEG-03** — stale, mismatched, skipped, or foreign-revision evidence presented as current: CHK-02, CHK-11, and
  CHK-19 fail closed.
- **NEG-04** — a payload, permit, secret, private address, host path, proprietary excerpt, TCP/`AF_INET` socket,
  DNS, TLS, or legacy/external peer use: CHK-13 and CHK-05 fail closed.
- **NEG-05** — the T035 checkbox marked at the plan stage, or the required report absent: CHK-20 fails closed.
- **NEG-06** — a measure `revision` bump, a new test target, or a changed descriptor `kind`: CHK-16 and CHK-17
  fail closed.
- **NEG-07** — a candidate-local run reported as whole-system integration: CHK-09 fails closed.
- **NEG-08** — a T036 benchmark, T037 Doxygen, T038 traceability/SADS, T039 review, or T041 acceptance claim
  inside the T035 evidence: CHK-11 and CHK-18 fail closed.
- **NEG-09** — an unavailable admitted input reported as pass: CHK-19 records `blocked`, never `pass`.
- **NEG-10** — a missing requirement/component/unit/measure/code/validation trace edge: CHK-14 fails closed.

## 6. Traceability to the accepted anchors

| T035 check | Accepted anchor |
| --- | --- |
| CHK-01/CHK-02/CHK-03 | plan step 9; `XCOM-SW-ENB-004`; `XCOM-SYS-FR-030`; SC-009 |
| CHK-04/CHK-05 | `XCOM-SW-CORE-003/005`; FR-006/007/010 |
| CHK-06/CHK-07/CHK-08 | `XCOM-SW-ENB-004`; FR-029/030 |
| CHK-09/CHK-10 | `XCOM-SW-ENB-001`, `XCOM-SW-CORE-009`; FR-030 |
| CHK-11/CHK-12/CHK-13 | `XCOM-SW-INTG-001`; FR-027; `build-environment.md` evidence contract |
| CHK-14/CHK-15 | `XCOM-SW-ENB-001`; FR-030; SC-009; ADR-0020 |
| CHK-16/CHK-17 | ADR-0020; Constitution X; T012 build contract |
| CHK-18/CHK-19/CHK-20 | Constitution VII/IX/X; `XCOM-SW-ENB-002`; ADR-0020 |

## 7. Measurement plan and evidence binding

- Every measure is bound to the exact T035 candidate revision; `commands`, `outcomes`, `hashes`, `environment`,
  bounded logs, and exit status are retained in `reports/xcom-queue/t035-verification.json` and in the workflow's
  trusted evidence bundle.
- The trusted policy executes `unit`, `integration`, `validation`, `static_analysis`, `conformance`, and
  `sanitizer`; T035 records their results and does not replace or weaken them.
- No stale, skipped, mismatched, or failed evidence supports acceptance; whole-system integration and static
  analysis run separately from the candidate-local checks.
- Any unavailable admitted input or tool is recorded as `blocked` with its reason; the candidate does not claim
  a pass (T035-OPEN-04).

## 8. Definition of done (verification view)

T035 is verified for a candidate revision when all CHK-01…CHK-20 hold: the full C++ suite, sanitizer build,
`cppcheck`, conformance recheck, whole-system integration measure, and Python suite pass or are honestly
recorded; `reports/xcom-queue/t035-verification.json` carries the required fields and the exact-candidate
identity; `validate_trace` passes; no accepted production byte changes; the registers stay reconciled with
REF-002 `unchanged`; and `xcom_phase8_gate.py verify T035 <baseline>` passes. User acceptance remains T041.
