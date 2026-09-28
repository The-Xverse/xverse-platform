# T019 Unit Specifications — Ownership, Lifetime, Thread-Safety, Failure, Bounds

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T019 |
| Stage / role | plan → unit specifications |
| Revision | 1 |
| Baseline revision | `199de0baa1f50e1d429527b6d6525a6e5d8cf7cf` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Consumed unit design | `docs/engineering/xcom/t010/design-units.md` (`XCOM-DU-011`) |
| Maturity of all T019 units | `allocated` (plan stage; the decoder is implemented in the implementation stage) |

The identifiers `T019-U-01`..`T019-U-08` are fixed by this document. `T019-U-01`..`T019-U-06` realise the
accepted `XCOM-DU-011` (bounded activation-plan decode with independent version/digest checks);
`T019-U-07`/`T019-U-08` are the work-product and test units. T019 does not renumber or edit the T010 design
units. Every unit belongs to the `T-XDL` slice and is bound to baseline
`199de0baa1f50e1d429527b6d6525a6e5d8cf7cf`. All units live in namespace `xverse::xcom::plan`.

## 2. Vocabulary used below

- **Ownership model** (closed): `task-owns-artifact`, `caller-owns-value`, `platform-owns-shared`.
- **Lifetime model** (closed): `static-immutable`, `process-scoped`, `document-scoped`, `plan-scoped`.
- **Thread-safety model** (closed): `read-only-static`, `offline-single-threaded`, `immutable-value`.
- **Outcome** (closed): `accepted`, `rejected`, `failed`.
- **Overflow policy set** (closed): `reject`, `fail-closed`, `n/a`.

## 3. Unit overview and declared bounds

### 3.1 Unit overview

| Unit | Name | Kind | Language | Realises | Artifact paths |
| --- | --- | --- | --- | --- | --- |
| `T019-U-01` | Bounded strict parse | function | cpp | `XCOM-DU-011` | `src/xverse/xcom/src/activation_plan.cpp` |
| `T019-U-02` | Closed shape, vocabulary, identifiers, order | function | cpp | `XCOM-DU-011` | `src/xverse/xcom/src/activation_plan.cpp` |
| `T019-U-03` | Canonicalization, SHA-256, independent digest | function | cpp | `XCOM-DU-011` | `src/xverse/xcom/{include/xverse/xcom/activation_plan.hpp,src/activation_plan.cpp}` |
| `T019-U-04` | Capability, cross-reference, status verification | function | cpp | `XCOM-DU-011` | `src/xverse/xcom/src/activation_plan.cpp` |
| `T019-U-05` | Bounded immutable decoded model | data-plane value | cpp | `XCOM-DU-011` | `src/xverse/xcom/{include/xverse/xcom/activation_plan.hpp,src/activation_plan.cpp}` |
| `T019-U-06` | Deterministic outcome classification | function | cpp | `XCOM-DU-011` | `src/xverse/xcom/{include/xverse/xcom/activation_plan.hpp,src/activation_plan.cpp}` |
| `T019-U-07` | Work products and evidence record | documentation | markdown | `XCOM-DU-011` | `docs/engineering/xcom/t019/` |
| `T019-U-08` | Decoder tests and CTest integration | test-fixture | cpp | `XCOM-DU-011` | `tests/xcom/activation_plan/`, `src/xverse/xcom/CMakeLists.txt` |

### 3.2 Closed decode-code vocabulary

`XCOM-DECODE-INPUT`, `XCOM-DECODE-SHAPE`, `XCOM-DECODE-VERSION`, `XCOM-DECODE-DIGEST`,
`XCOM-DECODE-CAPABILITY`, `XCOM-DECODE-REFERENCE`, `XCOM-DECODE-UNRESOLVED`, `XCOM-DECODE-BOUND`,
`XCOM-DECODE-UNKNOWN`. `BOUND`/`UNKNOWN` are `failed`; the rest are `rejected`.

### 3.3 Outcome vocabulary

`accepted` (immutable value returned), `rejected` (data defect, no value), `failed` (bound or unknown step,
no value). No rejected/failed call returns a partial value.

### 3.4 Declared bounds (consolidated)

| Bound | Kind | Default value | Enforced by |
| --- | --- | --- | --- |
| plan bytes | `bytes` | `max_bytes` = 5 242 880 (5 MiB) | `T019-U-01` |
| nesting depth | `depth` | `max_depth` = 100 | `T019-U-01` |
| node count | `capacity` | `max_nodes` = 100 000 | `T019-U-01` |
| string length | `bytes` | `max_string_length` = 4 096 | `T019-U-01` |
| decoded contracts | `capacity` | `max_contracts` = 4 096 | `T019-U-05` |
| decoded endpoints | `capacity` | `max_endpoints` = 4 096 | `T019-U-05` |
| decoded routes | `capacity` | `max_routes` = 4 096 | `T019-U-05` |
| decoded providers | `capacity` | `max_providers` = 256 | `T019-U-05` |
| decoded observation points | `capacity` | `max_observation_points` = 1 024 | `T019-U-05` |
| decoded clock domains | `capacity` | `max_clock_domains` = 256 | `T019-U-05` |
| decoded diagnostics | `capacity` | `max_diagnostics` = 4 096 | `T019-U-05` |
| activation-order entries | `capacity` | `max_activation_order` = 8 192 | `T019-U-05` |
| provenance resources | `capacity` | `max_provenance_resources` = 1 000 | `T019-U-05` |
| overflow policy | — | `fail-closed` | all units |

Every bound is finite and positive; a `DecodeLimits` member < 1 is `failed` (`XCOM-DECODE-UNKNOWN`) before any
parse. These caps are ≥ the T018 `CompileLimits` caps, so every plan the accepted compiler can emit fits, and
no production numeric value is fixed (runtime bounds come from the activation plan or unit configuration,
FR-007).

## 4. `T019-U-01` — Bounded strict parse

- **Responsibility.** Convert bounded plan bytes into a JSON document under the byte/depth/node/string bounds,
  rejecting a repeated object member, malformed JSON, a non-object root, and a non-finite/out-of-range number;
  it performs no filesystem, network, or subprocess access and exposes no partial document on error.
- **Ownership.** `caller-owns-value` — the parsed document is a local value consumed within the call; the
  caller owns only the final decoded plan.
- **Lifetime.** `process-scoped` — no state is retained between calls.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `bytes`/`depth`/`capacity` per §3.4; overflow policy `fail-closed`.
- **Failure semantics.** malformed JSON, duplicate member, non-object root, non-finite/out-of-range number →
  `rejected` (`XCOM-DECODE-INPUT`); over-byte/over-depth/over-node or over-length string →
  `failed` (`XCOM-DECODE-BOUND`) for byte/depth/node and `rejected` (`XCOM-DECODE-SHAPE`) for a string.
- **Requirement links.** T019-SR-001.
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-07; NEG-D01..NEG-D03, NEG-D19, NEG-D21; BND-01, BND-02, BND-04.

## 5. `T019-U-02` — Closed shape, vocabulary, identifiers, and order

- **Responsibility.** Enforce the exact 16 required top-level members, the closed nested objects, the closed
  enums and const values, the identifier/version/digest/diagnostic patterns, the integer ranges, the
  `minItems` minimums, and the per-collection ordering and uniqueness rules against the §2.4 tables, which a
  test asserts equal `PLAN_SCHEMA`. The closed `digest` sub-schema (`algorithm ∈ {sha256}`, value
  `^[0-9a-f]{64}$`) is enforced for every embedded digest (`provenance.graphDigest` and each
  `provenance.resources[].sourceDigest`) as `XCOM-DECODE-SHAPE`; the top-level recorded `digest`'s
  algorithm/hex form is classified at the version/digest step so `NEG-D10` is unchanged.
- **Ownership.** `caller-owns-value` — the unit returns a classified error or permits model construction.
- **Lifetime.** `process-scoped` — no retained state.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `capacity`/`bytes` per §3.4; overflow policy `fail-closed`.
- **Failure semantics.** a missing/unknown member, a vocabulary/pattern/range violation (including an
  embedded `provenance.graphDigest`/`provenance.resources[].sourceDigest` algorithm or value-pattern
  violation), an empty `providers[].capabilities` or `provenance.resources`, an empty/duplicate
  `activationOrder`, or an out-of-order/duplicate-keyed collection → `rejected` (`XCOM-DECODE-SHAPE`).
- **Requirement links.** T019-SR-002.
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-06, CHK-10; NEG-D04..NEG-D08, NEG-D08DigestPattern, NEG-D17, NEG-D18.

## 6. `T019-U-03` — Canonicalization, SHA-256, and independent digest

- **Responsibility.** Reproduce the T017 canonical serialization rule (member-name order, no insignificant
  whitespace, single integral-number form, no non-finite numbers, no duplicate members), form the digested
  region by removing the top-level `digest`, compute the domain-separated SHA-256 in-tree, and verify the plan
  version and the recorded digest.
- **Ownership.** `caller-owns-value` — the functions return values and retain no shared state.
- **Lifetime.** `process-scoped` — pure helpers retain no state.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `bytes`/`capacity` per §3.4; a canonicalization state that cannot occur for a shape-valid plan
  is `failed` (`XCOM-DECODE-UNKNOWN`).
- **Failure semantics.** `planVersion` ≠ `"1"` → `rejected` (`XCOM-DECODE-VERSION`); digest algorithm/hex
  malformed or recomputed ≠ recorded → `rejected` (`XCOM-DECODE-DIGEST`); an internal canonicalization defect
  → `failed` (`XCOM-DECODE-UNKNOWN`).
- **Requirement links.** T019-SR-003.
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-02, CHK-04, CHK-08; NEG-D09..NEG-D12, NEG-D22; DET-01..DET-04.

## 7. `T019-U-04` — Capability, cross-reference, and status verification

- **Responsibility.** Independently verify that a plan declaring routes selects at least one provider, that
  every provider's required capabilities are a subset of its declared capabilities, that every
  route/observation/activation-order reference resolves to a declared identity, and that a plan declaring
  `activatable` carries six resolved input-resolution states. Closure is enforced against the plan's own
  declared `capability`/`schema`/`identity` states: a complaint is raised only when the plan declares the
  governing state `resolved`, so an `inspectable` plan that honestly records an unresolved closure is
  accepted as non-activatable.
- **Ownership.** `caller-owns-value` — the unit returns a classified error or permits model construction.
- **Lifetime.** `process-scoped` — no retained state.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `capacity` per §3.4; overflow policy `fail-closed`.
- **Failure semantics.** a route with no selected provider, or capability insufficiency, while `capability`
  is `resolved` → `rejected` (`XCOM-DECODE-CAPABILITY`); an unresolved reference while the governing
  `schema`/`identity` state is `resolved` → `rejected` (`XCOM-DECODE-REFERENCE`); `activatable` with an
  unresolved member → `rejected` (`XCOM-DECODE-UNRESOLVED`); a valid `inspectable` plan is accepted.
- **Requirement links.** T019-SR-004 (`XCOM-SW-CORE-003` refinement).
- **Component refs.** `XCOM-CMP-003`, `XCOM-CMP-004`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-05; NEG-D13..NEG-D16.

## 8. `T019-U-05` — Bounded immutable decoded model

- **Responsibility.** Copy each validated member into the bounded immutable value types of
  `activation_plan.hpp`, enforce the finite entity caps, and return the value only on `accepted`; the value is
  copyable/movable, exposes no mutation surface, and is shareable read-only without synchronization.
- **Ownership.** `caller-owns-value` — the decoded `ActivationPlan` is returned to the caller, which owns it.
- **Lifetime.** `plan-scoped` — the decoded plan is valid for the activation-plan scope and immutable after
  decode.
- **Thread-safety.** `immutable-value`; shared state: none; synchronization: none.
- **Bounds.** all §3.4 entity caps; overflow policy `fail-closed`.
- **Failure semantics.** an entity-cap breach → `failed` (`XCOM-DECODE-BOUND`) with no value; an internal
  model defect → `failed` (`XCOM-DECODE-UNKNOWN`) with no value.
- **Requirement links.** T019-SR-005.
- **Component refs.** `XCOM-CMP-003`, `XCOM-CMP-004`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-03, CHK-07, CHK-10; NEG-D20; BND-03.

## 9. `T019-U-06` — Deterministic outcome classification

- **Responsibility.** Execute the fixed-order pipeline and return exactly one outcome with a stable code and
  affected identifier or `xcom-plan`, with no partial value, and guarantee identical results across repeated
  and reordered-but-equivalent decodes.
- **Ownership.** `caller-owns-value` — the result is returned to the caller.
- **Lifetime.** `process-scoped` — no retained state.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** all §3.4; overflow policy `fail-closed`.
- **Failure semantics.** the first failing step determines the code; a bound/unknown step → `failed`; every
  other defect → `rejected`; a fully valid plan → `accepted`.
- **Requirement links.** T019-SR-006.
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0018, ADR-0020.
- **Planned evidence.** CHK-04, CHK-06, CHK-08; DET-01, DET-02; each `NEG-D*` case.

## 10. `T019-U-07` — Work products and evidence record

- **Responsibility.** Maintain the five plan work products and the implementation record for the exact
  candidate, and record the baseline, authorization, changed-path set, commands, outcomes, and limitations.
- **Ownership.** `task-owns-artifact` — `docs/engineering/xcom/t019/` is exclusive to T019.
- **Lifetime.** `document-scoped` — valid for the candidate revision.
- **Thread-safety.** `read-only-static`; shared state: none; synchronization: none.
- **Bounds.** `capacity` — work-product count fixed at 5 + implementation record; overflow policy `n/a`.
- **Failure semantics.** missing work product → `failed`; inconsistent/unsupported claim → `failed`; no
  acceptance claim.
- **Requirement links.** T019-SR-008.
- **Component refs.** (cross-cutting).
- **Contract refs.** (cross-cutting).
- **Governing ADRs.** ADR-0020.
- **Planned evidence.** CHK-09; NEG-G01..NEG-G05.

## 11. `T019-U-08` — Decoder tests and CTest integration

- **Responsibility.** Exercise the positive decode of the committed T017 fixtures, the SHA-256 known answers,
  the canonicalization invariance, the version/digest/capability/cross-reference checks, the bound behaviour,
  the immutable value contract, and every declared `NEG-D*` case, and register the decoder library and tests
  as CTest targets.
- **Ownership.** `task-owns-artifact` — the `T-XDL` slice owns the decoder test sources; the CMake target
  wiring lives on the shared `src/xverse/xcom/CMakeLists.txt`.
- **Lifetime.** `static-immutable` — the test sources are fixed for the candidate.
- **Thread-safety.** `offline-single-threaded` (`gtest_main`); shared state: none unless a case explicitly
  exercises concurrent reads of an immutable decoded value; synchronization: none.
- **Bounds.** `timeout` seconds — test-suite wall bound; `capacity` — test/fixture count (declared); overflow
  policy `fail-closed`.
- **Failure semantics.** an unexpected pass/fail → `failed`; a missing case → `failed`; no partial success.
- **Requirement links.** T019-SR-007.
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0020.
- **Planned evidence.** CHK-01..CHK-11; `ctest` gate.

## 12. Unit-to-requirement coverage

| Requirement | Units |
| --- | --- |
| T019-SR-001 | `T019-U-01` |
| T019-SR-002 | `T019-U-02` |
| T019-SR-003 | `T019-U-03` |
| T019-SR-004 | `T019-U-04` |
| T019-SR-005 | `T019-U-05` |
| T019-SR-006 | `T019-U-06` |
| T019-SR-007 | `T019-U-08` |
| T019-SR-008 | `T019-U-07` |

Every `T019-SR-###` is covered by ≥ 1 unit; every unit maps to ≥ 1 requirement. No accepted `XCOM-DU-###`
design unit is renamed or edited.
