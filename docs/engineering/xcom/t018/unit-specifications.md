# T018 Unit Specifications — Ownership, Lifetime, Thread-Safety, Failure, Bounds

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T018 |
| Stage / role | plan → unit specifications |
| Revision | 1 |
| Baseline revision | `56506d2c9cb71791cba06a1cc418fcadee72e0fa` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Consumed unit design | `docs/engineering/xcom/t010/design-units.md` (`XCOM-DU-009`) |
| Maturity of all T018 units | `allocated` (plan stage; the compiler is implemented in the implementation stage) |

The identifiers `T018-U-01`..`T018-U-10` are fixed by this document. `T018-U-01`..`T018-U-08` realise the
accepted `XCOM-DU-009` (build-time compiler); `T018-U-09`/`T018-U-10` are the work-product and test units.
T018 does not renumber or edit the T010 design units. Every unit belongs to the `T-XDL` slice and is bound to
baseline `56506d2c9cb71791cba06a1cc418fcadee72e0fa`.

## 2. Vocabulary used below

- **Ownership model** (closed): `task-owns-artifact`, `caller-owns-value`, `platform-owns-shared`.
- **Lifetime model** (closed): `static-immutable`, `process-scoped`, `document-scoped`.
- **Thread-safety model** (closed): `read-only-static`, `offline-single-threaded`.
- **Outcome** (closed): `accepted`, `rejected`, `failed`, `inspectable`, `activatable`.
- **Overflow policy set** (closed): `drop-oldest`, `drop-newest`, `coalesce`, `lossless-backpressure`,
  `reject`, `fail-closed`, `n/a`.

## 3. Unit overview

| Unit | Name | Kind | Language | Realises | Artifact paths |
| --- | --- | --- | --- | --- | --- |
| `T018-U-01` | Graph input loader and bounds | function | python | `XCOM-DU-009` | `src/xverse_xdl/xcom_plan.py` |
| `T018-U-02` | Profile payload index and grammar | function | python | `XCOM-DU-009` | `src/xverse_xdl/xcom_plan.py` |
| `T018-U-03` | Contract/endpoint/route/provider derivation | function | python | `XCOM-DU-009` | `src/xverse_xdl/xcom_plan.py` |
| `T018-U-04` | Policy/observation/stimulation/clock/order derivation | function | python | `XCOM-DU-009` | `src/xverse_xdl/xcom_plan.py` |
| `T018-U-05` | Canonicalization, digest, provenance | function | python | `XCOM-DU-009` | `src/xverse_xdl/xcom_plan.py` |
| `T018-U-06` | Input resolution and diagnostics | function | python | `XCOM-DU-009` | `src/xverse_xdl/xcom_plan.py` |
| `T018-U-07` | Plan composition and status | function | python | `XCOM-DU-009` | `src/xverse_xdl/xcom_plan.py` |
| `T018-U-08` | Bound enforcement and failure semantics | function | python | `XCOM-DU-009` | `src/xverse_xdl/xcom_plan.py` |
| `T018-U-09` | Work products and evidence record | documentation | markdown | `XCOM-DU-009` | `docs/engineering/xcom/t018/` |
| `T018-U-10` | Compiler tests | test-fixture | python | `XCOM-DU-009` | `tests/test_xcom_plan.py` |

### 3.1 Declared bounds (consolidated)

| Bound | Kind | Value | Enforced by |
| --- | --- | --- | --- |
| graph input bytes (`compile_plan_text`) | `bytes` | `CompileLimits.max_bytes` = 5 242 880 (5 MiB) | `T018-U-01` |
| graph nesting depth | `depth` | `CompileLimits.max_depth` = 100 | `T018-U-01` |
| graph nodes | `capacity` | `CompileLimits.max_nodes` = 100 000 | `T018-U-01` |
| graph resources | `capacity` | `CompileLimits.max_resources` = 1 000 | `T018-U-01` |
| compiled endpoints | `capacity` | `CompileLimits.max_endpoints` = 4 096 | `T018-U-08` |
| compiled routes | `capacity` | `CompileLimits.max_routes` = 4 096 | `T018-U-08` |
| compiled providers | `capacity` | `CompileLimits.max_providers` = 256 | `T018-U-08` |
| compiled observation points | `capacity` | `CompileLimits.max_observation_points` = 1 024 | `T018-U-08` |
| compiled clock domains | `capacity` | `CompileLimits.max_clock_domains` = 256 | `T018-U-08` |
| compiled diagnostics | `capacity` | `CompileLimits.max_diagnostics` = 4 096 | `T018-U-08` |
| overflow policy | — | `fail-closed` | all units |

These are offline-input/compiled-entity caps, not production numeric values. Runtime bounds come from the
activation plan or unit configuration (FR-007). Every bound is finite and positive; a `CompileLimits` value
`< 1` is rejected at construction with `XCOM-PLAN-INPUT`.

## 4. `T018-U-01` — Graph input loader and bounds

- **Responsibility.** Convert an admitted graph input (a `GraphView`, a `{"resources":[...]}` mapping, or a
  sequence of resource mappings) into a sorted, bounded, immutable `GraphView`, rejecting malformed shape,
  non-finite numbers, non-identifier identity values, duplicate resource identities, and over-bound input.
- **Ownership.** `task-owns-artifact` — the compiler owns the derived immutable view; the caller retains the
  source document.
- **Lifetime.** `process-scoped` — the returned `GraphView` is a frozen value owned by the caller after the
  call.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `bytes`/`depth`/`capacity` per §3.1; overflow policy `fail-closed`.
- **Failure semantics.** malformed shape/non-finite/non-identifier → `rejected` (`XCOM-PLAN-INPUT`);
  duplicate identity → `rejected` (`XCOM-PLAN-DUPLICATE`); over-bound → `failed` (`XCOM-PLAN-BOUND`); no
  partial view is returned on error.
- **Requirement links.** T018-SR-001.
- **Component refs.** `XCOM-CMP-001`, `XCOM-CMP-002`.
- **Contract refs.** `XCOM-XLC-005`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-01, CHK-07; NEG-C01..NEG-C04, NEG-C21..NEG-C23, NEG-C25.

## 5. `T018-U-02` — Profile payload index and grammar

- **Responsibility.** Index every `io.xverse.xcom` Profile v0.1 payload by attachment pointer and decorated
  identity, validate it against the closed grammar table (kind discriminator, per-form member sets, placement
  and no-address/no-credential rule), and reject an unknown/mismatched/duplicated/illegally-placed payload;
  a payload whose `target` does not match its attachment is not applied and marks the identity family
  unresolved.
- **Ownership.** `task-owns-artifact` — the compiler owns the derived sorted index.
- **Lifetime.** `caller-owns-value` — the index is a frozen value scoped to one compilation.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `capacity` — the index is bounded by `max_resources` and each resource's payload list; overflow
  policy `fail-closed`.
- **Failure semantics.** unknown member/kind/version, form/kind mismatch, illegal attachment, ambiguous
  resource-level `interface-policy`, duplicate payload → `rejected` (`XCOM-PLAN-PROFILE`); target mismatch →
  identity `unresolved` (no rejection).
- **Requirement links.** T018-SR-002.
- **Component refs.** `XCOM-CMP-001`, `XCOM-CMP-002`.
- **Contract refs.** `XCOM-XLC-005`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-02, CHK-06; NEG-C09..NEG-C13, NEG-C27.

## 6. `T018-U-03` — Contract, endpoint, route, and provider derivation

- **Responsibility.** Select the compilation scope and derive the `contracts`, `endpoints`, `routes`, and
  `providers` collections from the in-scope System/Component/Deployment and their `interface-policy` and
  `network-provider` payloads, rejecting an ambiguous scope, a multi-destination flow, a conflicting/ambiguous
  endpoint role, an undeclared reference, and a duplicate/undeclared identifier.
- **Ownership.** `task-owns-artifact` — the compiler owns the derived collections until they are placed in the
  caller-owned plan.
- **Lifetime.** `caller-owns-value` — the collections are scoped to one compilation and copied into the plan
  returned to the caller.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `capacity` per §3.1 (endpoints, routes, providers); overflow policy `fail-closed`.
- **Failure semantics.** ambiguous/undeclared/conflicting identity → `rejected` (`XCOM-PLAN-IDENTITY`);
  duplicate id → `rejected` (`XCOM-PLAN-DUPLICATE`); unusable contract → `rejected` (`XCOM-PLAN-CONTRACT`);
  missing interface-policy → schema `unresolved`; unmet capability → capability `unresolved`.
- **Requirement links.** T018-SR-003.
- **Component refs.** `XCOM-CMP-001`, `XCOM-CMP-002`, `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`, `XCOM-XLC-005`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-03, CHK-04; NEG-C05..NEG-C08, NEG-C16, NEG-C17.

## 7. `T018-U-04` — Policy, observation, stimulation, clock, and order derivation

- **Responsibility.** Derive the `policies`, `observationPoints`, `stimulation`, `clockDomains`, and
  `activationOrder` members from the `flow-policy`, `observation-policy`, and `validation-policy` payloads and
  the System time domains, rejecting a `serviceEmulation` payload without a permit reference, an observer
  whose target is not a declared route, and an undeclared identifier.
- **Ownership.** `task-owns-artifact` — the compiler owns the derived members until they are placed in the
  caller-owned plan.
- **Lifetime.** `caller-owns-value` — scoped to one compilation and copied into the returned plan.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `capacity` per §3.1 (observation points, clock domains, diagnostics); overflow policy
  `fail-closed`.
- **Failure semantics.** contradiction (observer target, `serviceEmulation` without permit, bad identifier) →
  `rejected` (`XCOM-PLAN-POLICY`/`XCOM-PLAN-IDENTITY`); policy conflict/absence → policy `unresolved`;
  unmapped clock → time `unresolved`; empty activation order → `rejected` (`XCOM-PLAN-IDENTITY`).
- **Requirement links.** T018-SR-004.
- **Component refs.** `XCOM-CMP-001`, `XCOM-CMP-002`, `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`, `XCOM-XLC-005`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-04; NEG-C14, NEG-C15, NEG-C18, NEG-C20, NEG-C24.

## 8. `T018-U-05` — Canonicalization, digest, and provenance

- **Responsibility.** Reproduce the T017 canonical serialization rule (member-name order, no insignificant
  whitespace, single integral-number form, no non-finite numbers, no duplicate members), compute the
  domain-separated SHA-256 digest over the digested region, and build the `generator` and `provenance`
  members (generation time, graph digest, ordered contributing resource identities and source digests).
- **Ownership.** `caller-owns-value` — the function returns a value and retains no shared state.
- **Lifetime.** `process-scoped` — the helper functions are pure and retain no state.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `capacity` — the provenance resource list is bounded by `max_resources`; overflow policy
  `fail-closed`.
- **Failure semantics.** non-finite number, malformed generation time/version → `rejected`
  (`XCOM-PLAN-INPUT` at the graph-loader boundary; the canonicalization helper raises `XCOM-PLAN-UNKNOWN` as a
  defensive fallback); empty contributing resource set → `rejected` (`XCOM-PLAN-INPUT`); a digest self-check
  mismatch → `failed` (`XCOM-PLAN-UNKNOWN`).
- **Requirement links.** T018-SR-005, T018-SR-006.
- **Component refs.** `XCOM-CMP-002`, `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0018, ADR-0020.
- **Planned evidence.** CHK-03, DET-01, DET-02; NEG-C01, NEG-C23, NEG-C26.

## 9. `T018-U-06` — Input resolution and diagnostics

- **Responsibility.** Compute the six `inputResolution` families and the ordered, unique diagnostic list from
  the derived collections, using only declared data and the fixed classification rules.
- **Ownership.** `caller-owns-value` — pure function returning values.
- **Lifetime.** `process-scoped` — no retained state.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `capacity` — diagnostics ≤ `max_diagnostics`; overflow policy `fail-closed`.
- **Failure semantics.** a diagnostic cap breach → `failed` (`XCOM-PLAN-BOUND`); an unresolved family is never
  reported as resolved.
- **Requirement links.** T018-SR-007.
- **Component refs.** `XCOM-CMP-002`, `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0018, ADR-0020.
- **Planned evidence.** CHK-05; NEG-C16..NEG-C20, NEG-C27.

## 10. `T018-U-07` — Plan composition and status

- **Responsibility.** Compose the final plan value from the derived members, set `status` from the six
  families, compute and set `digest`, and verify the plan matches its digest before returning it to the
  caller, without embedding a schema validator at import time.
- **Ownership.** `caller-owns-value` — `compile_plan` returns a fresh plain dict tree owned by the caller.
- **Lifetime.** `process-scoped` — the compiler retains no state between calls.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `capacity` per §3.1; overflow policy `fail-closed`.
- **Failure semantics.** any derivation error propagates its stable code and no plan is returned; a digest
  self-check failure → `failed` (`XCOM-PLAN-UNKNOWN`); a fully resolved compilation → `activatable`, an
  unresolved compilation → `inspectable`.
- **Requirement links.** T018-SR-005, T018-SR-007.
- **Component refs.** `XCOM-CMP-002`, `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0018, ADR-0020.
- **Planned evidence.** CHK-03, CHK-05; NEG-C24, NEG-C26.

## 11. `T018-U-08` — Bound enforcement and failure semantics

- **Responsibility.** Apply the compiled-entity caps after derivation and guarantee that a bound breach or an
  unknown compilation step yields a `failed` class with no plan value.
- **Ownership.** `caller-owns-value` — the unit returns a classified error or permits composition.
- **Lifetime.** `process-scoped` — no retained state.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** all §3.1 caps; overflow policy `fail-closed`.
- **Failure semantics.** cap breach → `failed` (`XCOM-PLAN-BOUND`); unknown step → `failed`
  (`XCOM-PLAN-UNKNOWN`); no partial success.
- **Requirement links.** T018-SR-008.
- **Component refs.** `XCOM-CMP-002`, `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0018, ADR-0020.
- **Planned evidence.** CHK-07; NEG-C21, NEG-C22.

## 12. `T018-U-09` — Work products and evidence record

- **Responsibility.** Maintain the five plan work products and the implementation record for the exact
  candidate, and record the baseline, authorization, changed-path set, commands, outcomes, and limitations.
- **Ownership.** `task-owns-artifact` — `docs/engineering/xcom/t018/` is exclusive to T018.
- **Lifetime.** `document-scoped` — valid for the candidate revision.
- **Thread-safety.** `read-only-static`; shared state: none; synchronization: none.
- **Bounds.** `capacity` — work-product count fixed at 5 + implementation record; overflow policy `n/a`.
- **Failure semantics.** missing work product → `failed`; inconsistent/unsupported claim → `failed`; no
  acceptance claim.
- **Requirement links.** T018-SR-010.
- **Component refs.** (cross-cutting).
- **Contract refs.** (cross-cutting).
- **Governing ADRs.** ADR-0020.
- **Planned evidence.** CHK-09; NEG-G01..NEG-G05.

## 13. `T018-U-10` — Compiler tests

- **Responsibility.** Exercise the compiler's positive derivation, byte-stable determinism, digest agreement
  with the T017 reference, schema/ordering validity, the inspectable/activatable rule, the bound behaviour,
  the grammar drift guard, and every declared negative case, via `tests/test_xcom_plan.py`.
- **Ownership.** `task-owns-artifact` — the `T-XDL` slice owns `tests/test_xcom_plan.py` (exclusive path).
- **Lifetime.** `static-immutable` — the test module is fixed for the candidate.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `timeout` seconds — test-suite wall bound; `capacity` — test/fixture count (declared); overflow
  policy `fail-closed`.
- **Failure semantics.** an unexpected pass/fail → `failed`; a missing case → `failed`; no partial success.
- **Requirement links.** T018-SR-009.
- **Component refs.** `XCOM-CMP-002`, `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0020.
- **Planned evidence.** CHK-01..CHK-08; `pytest` gate.

## 14. Unit-to-requirement coverage

| Requirement | Units |
| --- | --- |
| T018-SR-001 | `T018-U-01` |
| T018-SR-002 | `T018-U-02` |
| T018-SR-003 | `T018-U-03` |
| T018-SR-004 | `T018-U-04` |
| T018-SR-005 | `T018-U-05`, `T018-U-07` |
| T018-SR-006 | `T018-U-05` |
| T018-SR-007 | `T018-U-06`, `T018-U-07` |
| T018-SR-008 | `T018-U-08` |
| T018-SR-009 | `T018-U-10` |
| T018-SR-010 | `T018-U-09` |

Every `T018-SR-###` is covered by ≥ 1 unit; every unit maps to ≥ 1 requirement. No accepted `XCOM-DU-###`
design unit is renamed or edited.
