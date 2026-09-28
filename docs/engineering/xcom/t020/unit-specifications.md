# T020 Unit Specifications — Ownership, Lifetime, Thread-Safety, Failure, Bounds

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T020 |
| Stage / role | plan → unit specifications |
| Revision | 1 |
| Baseline revision | `1e289bfe6234553df94eb25065371f7d423fad88` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Consumed unit design | `docs/engineering/xcom/t010/design-units.md` (`XCOM-DU-010`, `XCOM-DU-011`) |
| Maturity of all T020 units | `allocated` (plan stage; the suites are implemented in the implementation stage) |

The identifiers `T020-U-01`..`T020-U-08` are fixed by this document. `T020-U-01`..`T020-U-05` extend the
verification coverage of the accepted `XCOM-DU-010` (canonical schema and digest contract) and `XCOM-DU-011`
(bounded activation-plan decode); `T020-U-06` is the bounded test support; `T020-U-07` is the build/test wiring;
`T020-U-08` is the work-product and evidence unit. T020 does not renumber or edit the T010 design units or the
T019 units `T019-U-01`..`T019-U-08`. Every T020 unit belongs to the `T-XDL` slice and is bound to baseline
`1e289bfe6234553df94eb25065371f7d423fad88`. The C++ suites live in the GoogleTest suites `T20OrderingEquivalence`,
`T20MalformedPlan`, `T20Drift`, `T20BoundMatrix`, and `T20Regression`; the Python module is a plain `pytest`
module.

## 2. Vocabulary used below

- **Ownership model** (closed): `task-owns-artifact`, `caller-owns-value`, `platform-owns-shared`.
- **Lifetime model** (closed): `static-immutable`, `process-scoped`, `document-scoped`, `plan-scoped`.
- **Thread-safety model** (closed): `read-only-static`, `offline-single-threaded`, `immutable-value`.
- **Outcome** (closed): `accepted`, `rejected`, `failed`.
- **Overflow policy set** (closed): `reject`, `fail-closed`, `n/a`.

## 3. Unit overview and declared bounds

### 3.1 Unit overview

| Unit | Name | Kind | Language | Requirement | Artifact paths |
| --- | --- | --- | --- | --- | --- |
| `T020-U-01` | Ordering-equivalence suite | test-fixture | cpp + py | T020-SR-001 | `tests/xcom/activation_plan/t020_ordering_equivalence_tests.cpp`, `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py` |
| `T020-U-02` | Malformed-plan suite | test-fixture | cpp | T020-SR-002 | `tests/xcom/activation_plan/t020_malformed_plan_tests.cpp` |
| `T020-U-03` | Drift suite | test-fixture | cpp | T020-SR-003 | `tests/xcom/activation_plan/t020_drift_tests.cpp` |
| `T020-U-04` | Bound-matrix suite | test-fixture | cpp | T020-SR-004 | `tests/xcom/activation_plan/t020_bound_matrix_tests.cpp` |
| `T020-U-05` | Cross-language regression suite | test-fixture | cpp + py | T020-SR-005 | `tests/xcom/activation_plan/t020_regression_tests.cpp`, `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py` |
| `T020-U-06` | Bounded test support | test-fixture | cpp | T020-SR-006 | `tests/xcom/activation_plan/t020_support.hpp` |
| `T020-U-07` | Build/test wiring and pytest integration | build-wiring | cmake | T020-SR-006 | `src/xverse/xcom/CMakeLists.txt` (shared) |
| `T020-U-08` | Work products and evidence record | documentation | markdown | T020-SR-007 | `docs/engineering/xcom/t020/` |

### 3.2 Outcome vocabulary

`accepted` (a value is returned by the decoder), `rejected` (data/shape/version/digest/capability/reference/
status defect, no value), `failed` (bound or unknown step, no value). No rejected/failed call returns a partial
value; a T020 case that observes `accepted` for a defective input fails.

### 3.3 Declared bounds (consolidated)

| Bound | Kind | Value exercised | Enforced by | Unit |
| --- | --- | --- | --- | --- |
| plan bytes | `bytes` | `max_bytes` = 5 242 880 (5 MiB) default | decoder | `T020-U-04` |
| nesting depth | `depth` | `max_depth` = 100 | decoder | `T020-U-02`, `T020-U-04` |
| node count | `capacity` | `max_nodes` = 100 000 | decoder | `T020-U-04` |
| string length | `bytes` | `max_string_length` = 4 096 | decoder | `T020-U-04` |
| decoded contracts | `capacity` | `max_contracts` = 4 096 | decoder | `T020-U-04` |
| decoded endpoints | `capacity` | `max_endpoints` = 4 096 | decoder | `T020-U-04` |
| decoded routes | `capacity` | `max_routes` = 4 096 | decoder | `T020-U-04` |
| decoded providers | `capacity` | `max_providers` = 256 | decoder | `T020-U-04` |
| decoded observation points | `capacity` | `max_observation_points` = 1 024 | decoder | `T020-U-04` |
| decoded clock domains | `capacity` | `max_clock_domains` = 256 | decoder | `T020-U-04` |
| decoded diagnostics | `capacity` | `max_diagnostics` = 4 096 | decoder | `T020-U-04` |
| activation-order entries | `capacity` | `max_activation_order` = 8 192 | decoder | `T020-U-04` |
| provenance resources | `capacity` | `max_provenance_resources` = 1 000 | decoder | `T020-U-04` |
| test-suite wall time | `timeout` | gate timeout (2400 s) | gate | `T020-U-07` |
| test/fixture count | `capacity` | fixed declared set (see `verification-plan.md` §8) | `T020-U-08` | `T020-U-08` |
| overflow policy | — | `fail-closed` | all units | all |

Every exercised bound is finite and positive; a `DecodeLimits` member `< 1` is `failed` (`XCOM-DECODE-UNKNOWN`)
before any parse. These caps are the decoder's declared caps; T020 fixes **no** production numeric bound value
(runtime bounds come from the activation plan or unit configuration, FR-007). No concurrency bound applies:
T020 spawns no thread and holds no mutable shared state (§7).

## 4. `T020-U-01` — Ordering-equivalence suite

- **Responsibility.** Prove that equivalent plan representations produce one canonical body and digest and one
  decode outcome, that the declared per-collection ordering/unique-key rules and the duplicate-free
  `activationOrder` rule hold, and that diagnostics are ordered deterministically; provide the cross-language
  leg that the Python compiler and the T017 validator agree on the canonical bytes of a synthetic plan.
- **Ownership.** `task-owns-artifact` — the `T-XDL` slice owns the test source; the decoder is
  `caller-owns-value`.
- **Lifetime.** `static-immutable` — the test source is fixed for the candidate.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** decoder `bytes`/`capacity` per §3.3; overflow policy `fail-closed`.
- **Failure semantics.** An unexpected outcome, a canonical-bytes or digest inequality, or an out-of-order
  collection that is not rejected fails the case; a golden/equivalence mismatch is never weakened.
- **Requirement links.** T020-SR-001 (refines T020-STK-001); `XCOM-SW-XDL-002`, `XCOM-SW-XDL-003`.
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-20-01, CHK-20-02; `T20-ORD-01`..`T20-ORD-08`; `T20-DET-01`..`T20-DET-04`.

## 5. `T020-U-02` — Malformed-plan suite

- **Responsibility.** Systematically inject structural/closed-shape defects (truncation, unbalanced delimiters,
  trailing content, duplicate members at every level, non-object roots, wrong JSON types, `null` where an
  object/array is required, missing required members, unknown nested members, invalid UTF-8, over-nesting) and
  assert the declared fail-closed outcome, code, target, and the absence of a decoded plan.
- **Ownership.** `task-owns-artifact`; the decoder is `caller-owns-value`.
- **Lifetime.** `static-immutable`.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** decoder `bytes`/`depth` per §3.3; overflow policy `fail-closed`.
- **Failure semantics.** Any malformed case that returns a decoded value or reports `accepted` fails; every
  malformed case must return `rejected` or `failed` with its declared code.
- **Requirement links.** T020-SR-002 (refines T020-STK-002); `XCOM-SW-CORE-003`.
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-20-03; `T20-MAL-01`..`T20-MAL-14`.

## 6. `T020-U-03` — Drift suite

- **Responsibility.** Assert the decoder's declared member, enum, pattern, ordering-key, minimum, and
  numeric-range tables equal the committed plan schema; assert the closed `$defs/digest` sub-schema equals the
  decoder's embedded-digest rule; and pin the plan-version const, the domain separator, the committed fixtures'
  canonical body/digest, and the accepted five Profile forms against golden values.
- **Ownership.** `task-owns-artifact`; anchors `PLAN_SCHEMA`/`PROFILE_SCHEMA` read-only.
- **Lifetime.** `static-immutable`.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** decoder `capacity` per §3.3; overflow policy `fail-closed`.
- **Failure semantics.** Any table/golden inequality, or any violated embedded digest that is not rejected
  `XCOM-DECODE-SHAPE`, fails; drift is never resolved in favour of the implementation.
- **Requirement links.** T020-SR-003 (refines T020-STK-003); `XCOM-SW-XDL-001`, `XCOM-SW-XDL-003`.
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-20-04; `T20-DRF-01`..`T20-DRF-09`.

## 7. `T020-U-04` — Bound-matrix suite

- **Responsibility.** Exercise each declared `DecodeLimits` member at, below, and above its value; assert the
  declared `failed`/`rejected` classification with no decoded value on a breach; and assert every limit `< 1`
  is `failed` (`XCOM-DECODE-UNKNOWN`).
- **Ownership.** `task-owns-artifact`; the decoder is `caller-owns-value`.
- **Lifetime.** `static-immutable`.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** decoder `bytes`/`depth`/`capacity` per §3.3; test inputs are small and bounded; overflow policy
  `fail-closed`.
- **Failure semantics.** An over-bound input that is not `failed` (`XCOM-DECODE-BOUND`) — or an over-length
  string that is not `rejected` (`XCOM-DECODE-SHAPE`) — fails; any breach that returns a value fails.
- **Requirement links.** T020-SR-004 (refines T020-STK-004); `XCOM-SW-XDL-003`.
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-20-05; `T20-BND-01`..`T20-BND-11`.

## 8. `T020-U-05` — Cross-language regression suite

- **Responsibility.** Pin the committed fixtures' decode, recorded and recomputed digests, canonical digested
  bytes, the 16 required members, the `DecodeLimits` defaults, the closed decode-code vocabulary, and the
  SHA-256 known answers; and prove the Python compiler/validator and the C++ decoder agree on the committed
  fixtures' canonical body and digest.
- **Ownership.** `task-owns-artifact`; consumes the decoder `caller-owns-value` and the compiler/validator
  read-only.
- **Lifetime.** `static-immutable`; a decoded plan is `plan-scoped` within a case.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** decoder `capacity` per §3.3; overflow policy `fail-closed`.
- **Failure semantics.** Any golden mismatch (fixture bytes, canonical body hash, recorded/recomputed digest,
  defaults, member set, code vocabulary) fails; a golden is never updated to match a drifted artifact.
- **Requirement links.** T020-SR-005 (refines T020-STK-001, T020-STK-005); `XCOM-SW-XDL-001`, `XCOM-SW-XDL-002`,
  `XCOM-SW-XDL-003`.
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-20-06, CHK-20-07; `T20-REG-01`..`T20-REG-10`.

## 9. `T020-U-06` — Bounded test support

- **Responsibility.** Provide header-only, inline helpers for bounded fixture/schema reading, JSON parsing,
  digest sealing, canonical-body comparison, deterministic reordering/whitespace permutation, small
  two-item-collection construction, and outcome/code assertions, with no global mutable state and no I/O
  writes.
- **Ownership.** `task-owns-artifact`; returns `caller-owns-value` values.
- **Lifetime.** `process-scoped` — helpers retain no state between calls.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** reads are bounded by the fixture/schema sizes; no unbounded allocation; overflow policy
  `fail-closed`.
- **Failure semantics.** A read or parse failure aborts the calling case with a GoogleTest assertion; the
  helper never invents a value.
- **Requirement links.** T020-SR-006 (refines T020-STK-005).
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0018, ADR-0020.
- **Planned evidence.** CHK-20-08; source inspection of the header for purity/offline rule (`T20-G03`).

## 10. `T020-U-07` — Build/test wiring and pytest integration

- **Responsibility.** Register the five C++ suites as CMake/CTest targets with T020 labels and the compile-time
  fixture/schema/profile paths under the shared `src/xverse/xcom/CMakeLists.txt`, and have the Python module
  discovered by `python3 -m pytest -q`, without editing any existing target, test, or configuration.
- **Ownership.** `platform-owns-shared` — the build path is a declared shared path; the targets are T020-owned.
- **Lifetime.** `static-immutable` — the wiring is fixed for the candidate.
- **Thread-safety.** `read-only-static`; shared state: none; synchronization: none.
- **Bounds.** `timeout` (gate 2400 s); target count fixed at five CTest targets plus one pytest module;
  overflow policy `n/a`.
- **Failure semantics.** A missing target, a label collision with `t019`, or an edit to an existing target
  fails the gate; the T019 library and targets stay unchanged.
- **Requirement links.** T020-SR-006 (refines T020-STK-005).
- **Component refs.** (cross-cutting build).
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0018, ADR-0020.
- **Planned evidence.** CHK-20-08, CHK-20-10; `ctest`/`pytest` gates.

## 11. `T020-U-08` — Work products and evidence record

- **Responsibility.** Maintain the five plan work products and the implementation record for the exact
  candidate, and record the baseline, authorization, changed-path set, commands, outcomes, golden-value
  captures, and limitations.
- **Ownership.** `task-owns-artifact` — `docs/engineering/xcom/t020/` is exclusive to T020.
- **Lifetime.** `document-scoped` — valid for the candidate revision.
- **Thread-safety.** `read-only-static`; shared state: none; synchronization: none.
- **Bounds.** `capacity` — work-product count fixed at 5 + implementation record; overflow policy `n/a`.
- **Failure semantics.** A missing work product, an inconsistent/unsupported claim, or an updated golden fails;
  no acceptance/review claim is recorded.
- **Requirement links.** T020-SR-007 (refines T020-STK-005).
- **Component refs.** (cross-cutting).
- **Contract refs.** (cross-cutting).
- **Governing ADRs.** ADR-0020.
- **Planned evidence.** CHK-20-09; `T20-G01`..`T20-G05`.

## 12. Unit-to-requirement coverage

| Requirement | Units |
| --- | --- |
| T020-SR-001 | `T020-U-01` |
| T020-SR-002 | `T020-U-02` |
| T020-SR-003 | `T020-U-03` |
| T020-SR-004 | `T020-U-04` |
| T020-SR-005 | `T020-U-05` |
| T020-SR-006 | `T020-U-06`, `T020-U-07` |
| T020-SR-007 | `T020-U-08` |

Every `T020-SR-###` is covered by ≥ 1 unit; every unit maps to ≥ 1 requirement. No accepted `XCOM-DU-###` or
`T019-U-###` design unit is renamed, renumbered, or edited. The accepted `XCOM-DU-010`/`XCOM-DU-011`
planned-evidence tokens `CHK-06`, `CHK-09`, `NEG-21`, `NEG-22`, `NEG-23` (and `NEG-42`, `NEG-43` for
`XCOM-DU-010`) are T008/T010-scoped capability tokens realised for those units by the T017/T018/T019 check
sets as a whole; T020 extends their evidence with `CHK-20-01`..`CHK-20-10` and
`T20-ORD-*`/`T20-MAL-*`/`T20-DRF-*`/`T20-BND-*`/`T20-REG-*`/`T20-DET-*`/`T20-G*`, and does not edit the
T008/T010 work products.
