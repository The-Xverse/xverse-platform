# T037 Verification Plan — Complete Doxygen Comments and Warning-Free Generated Reference Documentation

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T037 (capability 007, slice `T-INTG`/documentation) |
| Stage / role | plan → verification design |
| Revision | 1 (Phase 8 Doxygen-completion slice) |
| Baseline revision | `8757a79d4e6b2630124d774fcba2a55d6342a879` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

"Verified" means the named command, case, or inspection exists, is deterministic, and passes at the recorded
candidate revision. It is not a deployed-service, compatibility, performance, or production-readiness claim.

## 2. Verification environment

- Admitted offline X-COM build envelope (T011): admitted `protoc` 3.12.4, admitted GTest prefix, admitted
  standard library and in-process libraries, and the admitted Doxygen executable (Doxygen 1.9.1); no network,
  DNS, TLS, legacy binary, or production workload.
- C++20, warning-as-error (T012), Ninja build, GoogleTest discovery; Python 3.11 or newer for the
  documentation checker.
- The trusted Phase 8 `validation` measure reads `Doxyfile`, appends `OUTPUT_DIRECTORY`, `WARN_AS_ERROR = YES`,
  and `QUIET = YES`, and runs `doxygen` with a nonzero-exit-on-warning contract
  (`run_xcom_phase8_tests.py`, `mode == "validation" and task == "T037"`).
- Whole-system integration remains the trusted target-repository measure (`run_xcom_phase8_tests.py
  integration`); T037 does not re-run or re-claim it.

## 3. Requirements-to-check matrix

| Requirement | Primary checks | Verification measure / route |
| --- | --- | --- |
| T037-STK-001 | CHK-01, CHK-02, CHK-03 | checker / source inspection |
| T037-STK-002 | CHK-04, CHK-05 | report inspection |
| T037-STK-003 | CHK-06, CHK-07 | public-safety / forbidden-resource inspection |
| T037-STK-004 | CHK-08, CHK-09 | checker / trace |
| T037-STK-005 | CHK-10, CHK-11 | diff / register / gate |
| T037-SR-001 | CHK-01, CHK-08 | checker / source inspection |
| T037-SR-002 | CHK-02 | checker (strict C++) |
| T037-SR-003 | CHK-03 | repository route |
| T037-SR-004 | CHK-04 | generation inspection |
| T037-SR-005 | CHK-05, CHK-09 | report inspection / checker |
| T037-SR-006 | CHK-10 | diff / discovery inspection |
| T037-SR-007 | CHK-06 | public-safety inspection |
| T037-SR-008 | CHK-07 | forbidden-resource inspection |
| T037-SR-009 | CHK-09, CHK-11 | trace / register / gate |
| T037-SR-010 | CHK-08, CHK-09 | checker fail-closed |

## 4. Named checks

| Check | Description | Requirement |
| --- | --- | --- |
| CHK-01 | every owned public C/C++ declaration carries `@brief` and the applicable `@param`/`@return`/`@retval` and ownership/lifetime/thread-safety/failure clauses, and every owned file carries the mandatory file block | T037-SR-001 |
| CHK-02 | the strict C++-scoped configuration (`EXTRACT_ALL = NO`, public declarations only, `WARN_IF_UNDOCUMENTED = YES`, `WARN_NO_PARAMDOC = YES`, `WARN_AS_ERROR = YES`, admitted exclusions) exits zero with zero warnings and zero coverage gaps | T037-SR-002 |
| CHK-03 | `Doxyfile` defines every command used by the admitted inputs (including `bounds`), and the repository-wide route completes warning-free under `WARN_AS_ERROR = YES` | T037-SR-003 |
| CHK-04 | the HTML and XML reference is generated warning-free, the index files exist, and the generated output is not versioned | T037-SR-004 |
| CHK-05 | `reports/xcom-queue/t037-doxygen.json` records `command`, `warnings`, `output`, the environment identity, hashes, and the exact-candidate identity | T037-SR-005 |
| CHK-06 | the committed report, work products, and bounded excerpts contain no credential, private address, payload, proprietary excerpt, or host-specific absolute path | T037-SR-007 |
| CHK-07 | no T037 command uses a TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, TLS, external peer, legacy binary, or production workload, and no dependency is added | T037-SR-008 |
| CHK-08 | the task-owned checker fails closed (nonzero) on an undocumented owned declaration, a missing mandatory tag, or any Doxygen warning; B-3 self-test proves the coverage gate rejects a synthetic undocumented symbol | T037-SR-010 |
| CHK-09 | B-4 writes the report and `scripts/check_doxygen.py --strict-cpp` plus the report inspection agree; a stale, foreign, incomplete, or failed result is reported as failed or blocked, never as pass | T037-SR-005, T037-SR-010 |
| CHK-10 | the baseline-versus-candidate diff over the owned sources is Doxygen-comment-only; no compiled token, signature, type, default, test, target, label, command, or expected value changes | T037-SR-006 |
| CHK-11 | the T007 ownership register and the T008/T009/T010 models are reconciled without rewrite; REF-002 stays `unchanged` with an empty `promoted` list; T037 is recorded implemented and T038–T041 allocated; every edited-artifact `implemented_by` pin is refreshed (`T037-OPEN-03`) | T037-SR-009 |
| CHK-12 | `xcom_phase8_gate.py verify T037 <baseline>` passes with the report present, the T037 checkbox marked complete only at implementation, and the T037 unit measure passing | T037-SR-009 |
| CHK-13 | the inherited Python docstring findings and the derived strict-C++ scope are recorded honestly as limitations rather than concealed (`T037-GAP-02`, `T037-OPEN-06`) | T037-SR-009 |

## 5. Executable route, negative cases, and the exact evidence report

| Step | Command (portable descriptor) | Expected |
| --- | --- | --- |
| B-1 | `doxygen Doxyfile` (with `WARN_AS_ERROR = YES`) | exit `0`; no warning; HTML and XML indexes generated |
| B-2 | `python3 scripts/check_doxygen.py --strict-cpp` | exit `0`; zero warnings and zero coverage gaps over the owned C++ inputs |
| B-3 | `python3 scripts/check_doxygen.py --self-test --coverage-only` | exit `0`; the coverage gate rejects the synthetic undocumented symbol |
| B-4 | `python3 scripts/check_doxygen.py --report reports/xcom-queue/t037-doxygen.json` | exit `0`; the report carries `command`, `warnings`, `output`, the environment identity, hashes, and the exact-candidate identity |
| B-5 | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py unit` | `100% tests passed` |

The trusted Phase 8 `validation` measure runs B-1 as part of its route (the appended
`WARN_AS_ERROR = YES` generation over `Doxyfile`), so the task-owned verification route is exercised by the
trusted gate. The candidate-local unit measure (B-5) preserves the accepted suite and discovers the exact
selected case IDs.

**Exact evidence report.** `reports/xcom-queue/t037-doxygen.json` is the task-owned evidence report; it is
required to contain `command`, `warnings`, and `output` (the Phase 8 gate's T037 fields) plus `environment`,
`strict_cpp`, `hashes`, and the exact-candidate identity (§4 of `detailed-design.md`). It is generated at the
implementation stage from the executed generation; the plan stage records only the schema and route and does
not fabricate results.

**Task-owned route.** The route is the task-owned documentation checker `scripts/check_doxygen.py`
invoked by B-1/B-2/B-4 over the owned C++ inputs. It adds no accepted CTest target and no compiled symbol;
the selected case set names only already-discovered accepted cases, so the discovered inventory is
unchanged.

### Negative cases (`NEG-###`)

- **NEG-01** — a changed compiled token, signature, type, default, control-flow decision, contract, or
  expected value under the banner of documentation: CHK-10 fails closed.
- **NEG-02** — an owned public declaration left undocumented, a missing mandatory tag, or strictness enabled
  over out-of-scope inputs with the resulting warnings concealed: CHK-01/CHK-02/CHK-08/CHK-13 fail closed.
- **NEG-03** — a committed generated tree, or a claim of warning-free generation when a warning exists:
  CHK-03/CHK-04/CHK-09 fail closed.
- **NEG-04** — a stale or foreign report presented as current: CHK-05/CHK-09 fail closed.
- **NEG-05** — a recorded `pass` whose observed warning count is nonzero: CHK-02/CHK-09 fail closed.
- **NEG-06** — a new accepted test target or a changed accepted expected value: CHK-10 fails closed.
- **NEG-07** — a credential, private address, payload, proprietary excerpt, host path, TCP/`AF_INET` socket,
  DNS, TLS, legacy/external peer, or added dependency: CHK-06/CHK-07 fail closed.
- **NEG-08** — a T038/T039/T041 claim or a production-readiness claim inside the T037 evidence:
  CHK-04/CHK-11 fail closed.
- **NEG-09** — the T037 checkbox marked at the plan stage, or the required report absent: CHK-12 fails closed.
- **NEG-10** — a missing requirement/component/unit/measure/code/validation trace edge, or a stale hash pin
  after the implementation refresh: CHK-11 fails closed.

## 6. Traceability to the accepted anchors

| T037 check | Accepted anchor |
| --- | --- |
| CHK-01/CHK-02/CHK-03/CHK-04 | `XCOM-SW-INTG-002`, `XCOM-SW-ENB-004`; `XCOM-SYS-FR-029`, `XCOM-SYS-SC-009` |
| CHK-05/CHK-06 | `XCOM-SW-INTG-002`, `XCOM-SW-INTG-001`; `XCOM-SYS-FR-027`, `XCOM-SYS-FR-029` |
| CHK-07 | `XCOM-SW-CORE-007`; `XCOM-SYS-FR-026/028` |
| CHK-08/CHK-09 | `XCOM-SW-INTG-002`; `XCOM-SYS-FR-029`, `XCOM-SYS-SC-009`; ADR-0020 |
| CHK-10 | `XCOM-SW-ENB-004`, `XCOM-SW-INTG-002`; `XCOM-SYS-FR-029`; Constitution VI, X |
| CHK-11/CHK-12/CHK-13 | `XCOM-SW-ENB-001/002`; `XCOM-SYS-FR-030/035`; Constitution VII/IX/X; ADR-0020 |

## 7. Measurement plan and evidence binding

- Every result is bound to the accepted baseline revision and the exact T037 candidate material digest and
  inventory; because a committed report cannot contain the hash of the commit that contains it, the candidate
  commit is the direct child of the baseline carrying that material. `command`, `warnings`, `output`,
  `environment`, `strict_cpp`, and `hashes` are retained in `reports/xcom-queue/t037-doxygen.json`.
- The trusted policy executes `unit`, `integration`, `validation`, `static_analysis`, `conformance`, and
  `sanitizer`; T037 records the documentation result and does not replace or weaken them.
- The strict C++ scope, the exclusion list, and the inherited Python findings are recorded honestly and are
  not presented as full-repository declaration-level strictness.
- Any unavailable admitted input or Doxygen executable is recorded as `blocked` with its reason; the
  candidate does not claim a pass (T037-OPEN-04).

## 8. Definition of done (verification view)

T037 is verified for a candidate revision when all CHK-01…CHK-13 hold: every owned public C/C++ declaration
and file is documented; the strict C++-scoped configuration is warning-free with zero coverage gaps; the
repository-wide `Doxyfile` route is warning-free under `WARN_AS_ERROR = YES`; the report carries the required
fields and the exact-candidate identity; the checker fails closed on an incomplete or warned result; the
owned-source diff is comment-only; no accepted test/behavior changes; the registers stay reconciled with
REF-002 `unchanged` and refreshed trace pins; and `xcom_phase8_gate.py verify T037 <baseline>` passes. User
acceptance remains T041.
