# T038 Verification Plan — Spec Kit and REF-002 Requirements/Design/Code/Test Traceability and Public-Safe Evidence

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T038 (capability 007, slice `T-INTG`/traceability) |
| Stage / role | plan → verification design |
| Revision | 1 (Phase 8 traceability slice) |
| Baseline revision | `d5b9c6399da67a0a028fae21c2f0dcc8da3619bc` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

"Verified" means the named command, case, or inspection exists, is deterministic, and passes at the recorded
candidate revision. It is not a deployed-service, compatibility, performance, or production-readiness claim.

## 2. Verification environment

- Admitted offline X-COM build envelope (T011): admitted `protoc` 3.12.4, admitted GTest prefix, admitted
  standard library and in-process libraries, and the admitted Python runtime; no network, DNS, TLS, legacy
  binary, or production workload.
- C++20, warning-as-error (T012), Ninja build, GoogleTest discovery; Python 3.11 or newer for the traceability
  verifier.
- The trusted Phase 8 `validation` measure invokes the task-owned verifier
  (`run_xcom_phase8_tests.py`, `mode == "validation" and task == "T038"`:
  `python3 engineering/check_xcom_traceability.py --verify reports/xcom-queue/t038-traceability.json`).
- Whole-system integration remains the trusted target-repository measure (`run_xcom_phase8_tests.py
  integration`); T038 does not re-run or re-claim it.

## 3. Requirements-to-check matrix

| Requirement | Primary checks | Verification measure / route |
| --- | --- | --- |
| T038-STK-001 | CHK-01, CHK-02 | verifier / register inspection |
| T038-STK-002 | CHK-03, CHK-04 | report inspection |
| T038-STK-003 | CHK-05, CHK-06 | public-safety / forbidden-resource inspection |
| T038-STK-004 | CHK-02, CHK-07 | verifier (REF-002) |
| T038-STK-005 | CHK-08, CHK-09 | diff / register / gate |
| T038-SR-001 | CHK-01, CHK-09 | verifier / trace inspection |
| T038-SR-002 | CHK-02 | verifier (REF-002) |
| T038-SR-003 | CHK-07 | verifier (no promotion) |
| T038-SR-004 | CHK-03, CHK-04 | report inspection / verifier |
| T038-SR-005 | CHK-05 | public-safety inspection |
| T038-SR-006 | CHK-08 | diff inspection |
| T038-SR-007 | CHK-09, CHK-10 | trace / register / gate |
| T038-SR-008 | CHK-06 | forbidden-resource inspection |
| T038-SR-009 | CHK-11 | verifier fail-closed / self-test |
| T038-SR-010 | CHK-12, CHK-13 | route / discovery / gate |

## 4. Named checks

| Check | Description | Requirement |
| --- | --- | --- |
| CHK-01 | every `refines`/`allocated_to`/`decomposes_to`/`implemented_by`/`verified_by`/`analyzed_by`/`validates` edge resolves to a declared artifact of the expected group with no missing or stale edge | T038-SR-001 |
| CHK-02 | all twenty REF-002 IDs `XVE-SYS-0139`–`0158` carry an explicit disposition and owning capability consistent with `specs/007-xcom-core/reference-traceability.md` and the accepted register | T038-SR-002 |
| CHK-03 | `reports/xcom-queue/t038-traceability.json` records `requirements`, `design`, `code`, `tests`, and `evidence` results plus the environment identity, hashes, and the exact-candidate identity | T038-SR-004 |
| CHK-04 | B-1 writes the report and `engineering/check_xcom_traceability.py --verify <report>` agrees; a stale, foreign, incomplete, or failed result is reported as failed or blocked, never as pass | T038-SR-004 |
| CHK-05 | the committed report, work products, and bounded excerpts contain no credential, private address, payload, proprietary excerpt, or host-specific absolute path (the five mechanically decidable classes) | T038-SR-005 |
| CHK-06 | no T038 command uses a TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, TLS, external peer, legacy binary, or production workload, and no dependency is added | T038-SR-008 |
| CHK-07 | no allocated, deferred, architectural-target, or superseded REF-002 ID is recorded implemented; the capability disposition stays `unchanged` with an empty `promoted` list | T038-SR-003 |
| CHK-08 | the baseline-versus-candidate diff over the accepted artifacts is additive-only; no accepted requirement, compiled token, signature, type, default, test, target, label, command, expected value, contract, schema, register, XDL profile, or ADR changes | T038-SR-006 |
| CHK-09 | the T007 ownership register and the T008/T009/T010 models are reconciled without rewrite; the current-task pointer is set; T038 is recorded implemented and T039–T041 allocated | T038-SR-007 |
| CHK-10 | every edited-artifact `implemented_by` pin (the fifteen `engineering/project.json` pins and any further edited pins) is refreshed so no stale hash remains (`T038-OPEN-02`) | T038-SR-007 |
| CHK-11 | the task-owned verifier fails closed (nonzero) on a missing edge, a stale hash pin, a promoted or incomplete disposition, or an excluded-content match; the self-test proves each rejection | T038-SR-009 |
| CHK-12 | the trusted Phase 8 T038 validation measure invokes B-1 and returns exit `0` with a complete, public-safe, exactly-bound result | T038-SR-010 |
| CHK-13 | `xcom_phase8_gate.py verify T038 <baseline>` passes with the report present, the T038 checkbox marked complete only at implementation, and no accepted target/test/label/command/expected value changed | T038-SR-010 |

## 5. Executable route, negative cases, and the exact evidence report

| Step | Command (portable descriptor) | Expected |
| --- | --- | --- |
| B-1 | `python3 engineering/check_xcom_traceability.py --verify reports/xcom-queue/t038-traceability.json` | exit `0`; the chain is complete, all twenty dispositions are unchanged, nothing is promoted, and the report carries the required fields and the exact-candidate identity |
| B-2 | `python3 engineering/check_xcom_traceability.py --self-test` | exit `0`; the verifier rejects a missing edge, a stale hash pin, a promoted disposition, and an excluded-content match |
| B-3 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` | exit `0`; the accepted Spec Kit register and matrix validate unchanged |
| B-4 | `python3 scripts/validate_xcom_requirements_traceability.py --check-human` | exit `0`; the register/matrix projections are byte-stable |
| B-5 | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py unit` | `100% tests passed` |

The trusted Phase 8 `validation` measure runs B-1 as part of its route, so the task-owned verification route is
exercised by the trusted gate. The candidate-local unit measure (B-5) preserves the accepted suite and discovers
the exact selected case IDs.

**Exact evidence report.** `reports/xcom-queue/t038-traceability.json` is the task-owned evidence report; it is
required to contain `requirements`, `design`, `code`, `tests`, and `evidence` (the Phase 8 gate's T038 fields)
plus `candidate_identity`, `environment`, `ref002`, `hashes`, `limitations`, and `blockers` (§6.2 of
`architecture.md`). It is generated at the implementation stage from the executed validation; the plan stage
records only the schema and route and does not fabricate results.

**Task-owned route.** The route is the task-owned traceability verifier `engineering/check_xcom_traceability.py`
invoked by B-1/B-2 over the accepted records; it adds no accepted CTest target and no compiled symbol; the
selected case set names only already-discovered accepted cases, so the discovered inventory is unchanged.

### Negative cases (`NEG-###`)

- **NEG-01** — a changed accepted requirement, code token, test, register, or expected value under the banner
  of traceability: CHK-08 fails closed.
- **NEG-02** — an incomplete or unknown REF-002 disposition: CHK-02 fails closed.
- **NEG-03** — a promoted allocated/deferred/architectural-target/superseded REF-002 ID without proof:
  CHK-07 fails closed.
- **NEG-04** — a stale or foreign report presented as current: CHK-04/CHK-11 fail closed.
- **NEG-05** — a recorded `pass` whose observed unresolved-edge, stale-pin, or promoted count is nonzero:
  CHK-04/CHK-11 fail closed.
- **NEG-06** — a credential, private address, payload, proprietary excerpt, host path, TCP/`AF_INET` socket,
  DNS, TLS, legacy/external peer, or added dependency: CHK-05/CHK-06 fail closed.
- **NEG-07** — a missing requirement/component/unit/measure/code/validation edge: CHK-01/CHK-11 fail closed.
- **NEG-08** — a T039/T040/T041 claim or a production-readiness claim inside the T038 evidence:
  CHK-09 fails closed.
- **NEG-09** — replacing or weakening the accepted validator instead of adding the additive verifier:
  CHK-08/CHK-13 fail closed.
- **NEG-10** — the T038 checkbox marked at the plan stage, or the required report absent: CHK-13 fails closed.
- **NEG-11** — a stale hash pin after the implementation refresh: CHK-10 fails closed.

## 6. Traceability to the accepted anchors

| T038 check | Accepted anchor |
| --- | --- |
| CHK-01/CHK-02/CHK-03 | `XCOM-SW-ENB-001`; `XCOM-SYS-FR-030`, `XCOM-SYS-SC-009` |
| CHK-04/CHK-05 | `XCOM-SW-ENB-001`, `XCOM-SW-INTG-001`; `XCOM-SYS-FR-027` |
| CHK-06 | `XCOM-SW-CORE-007`; `XCOM-SYS-FR-026/028` |
| CHK-07 | `XCOM-SW-ENB-002`, `XCOM-SW-INTG-002`; `XCOM-SYS-FR-035` |
| CHK-08 | `XCOM-SW-ENB-001`, `XCOM-SW-ENB-004`; `XCOM-SYS-FR-030`; Constitution VI, X |
| CHK-09/CHK-10 | `XCOM-SW-ENB-001/002`; `XCOM-SYS-FR-030/035`; Constitution VII/IX/X; ADR-0020 |
| CHK-11/CHK-12/CHK-13 | `XCOM-SW-INTG-002`, `XCOM-SW-ENB-001`; `XCOM-SYS-FR-030`, `XCOM-SYS-SC-009`; ADR-0020 |

## 7. Measurement plan and evidence binding

- Every result is bound to the accepted baseline revision and the exact T038 candidate material digest and
  inventory; because a committed report cannot contain the hash of the commit that contains it, the candidate
  commit is the direct child of the baseline carrying that material. `requirements`, `design`, `code`,
  `tests`, `evidence`, `ref002`, `environment`, and `hashes` are retained in
  `reports/xcom-queue/t038-traceability.json`.
- The trusted policy executes `unit`, `integration`, `validation`, `static_analysis`, `conformance`, and
  `sanitizer`; T038 records the traceability result and does not replace or weaken them.
- The mechanically decidable public-safety classes and the review-judged classes are recorded honestly and are
  not presented as full content judgement.
- Any unavailable accepted input or Python runtime is recorded as `blocked` with its reason; the candidate does
  not claim a pass (`T038-OPEN-03`).

## 8. Definition of done (verification view)

T038 is verified for a candidate revision when all CHK-01…CHK-13 hold: the complete traceability chain
resolves with no missing or stale edge; all twenty REF-002 dispositions are explicit with nothing promoted; the
report carries the required sections and the exact-candidate identity; the task-owned verifier fails closed on
an incomplete, promoted, stale, or unsafe result; the accepted-artifact diff is additive-only; the registers
stay reconciled with refreshed trace pins; and `xcom_phase8_gate.py verify T038 <baseline>` passes. User
acceptance remains T041.
