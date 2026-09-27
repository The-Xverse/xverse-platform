# T016 Unit Specifications — Test Units, Ownership, Lifetime, Thread-Safety, Bounds, and Failure Semantics

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T016 (capability 007, slice `T-CORE`) |
| Stage / role | plan → unit specifications |
| Revision | 1 |
| Baseline revision | `44d2001d48dd42dc9ed489a40d2a5f908b734501` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit-design anchors | `docs/engineering/xcom/t010/unit-design.{json,md}` (`XCOM-DU-007`, `XCOM-DU-008`) |
| Classification | Public-safe engineering work product |

This document specifies each T016 test unit before implementation. T016 introduces no product design
unit; it adds test-side units that consume `XCOM-DU-007` (provider boundary and composition) and
`XCOM-DU-008` (owned loopback provider) read-only. The vocabulary (ownership, lifetime, thread-safety,
bounds, failure semantics) follows the T010 unit-design vocabulary.

## 2. Unit summary

| Unit | Kind | Artefact | Language | Owning slice | Verified design unit(s) |
| --- | --- | --- | --- | --- | --- |
| `T016-TS-001` | test fixture | `tests/xcom/core_matrix/test_support.hpp` | cpp | T-CORE (T016) | `XCOM-DU-007`, `XCOM-DU-008` |
| `T016-TS-002` | test fixture | `tests/xcom/core_matrix/test_support.hpp` | cpp | T-CORE (T016) | `XCOM-DU-007` |
| `T016-TS-003` | test suite | `tests/xcom/core_matrix/unit_tests.cpp` | cpp | T-CORE (T016) | `XCOM-DU-007`, `XCOM-DU-008` |
| `T016-TS-004` | test suite | `tests/xcom/core_matrix/negative_tests.cpp` | cpp | T-CORE (T016) | `XCOM-DU-007`, `XCOM-DU-008` |
| `T016-TS-005` | test suite | `tests/xcom/core_matrix/recovery_tests.cpp` | cpp | T-CORE (T016) | `XCOM-DU-007`, `XCOM-DU-008` |
| `T016-TS-006` | test suite | `tests/xcom/core_matrix/concurrency_tests.cpp` | cpp | T-CORE (T016) | `XCOM-DU-007`, `XCOM-DU-008` |
| `T016-TS-007` | test suite | `tests/xcom/core_matrix/fault_boundary_tests.cpp` | cpp | T-CORE (T016) | `XCOM-DU-007` |
| `T016-TS-008` | test executable | `tests/xcom/core_matrix/consumer/main.cpp` | cpp | T-CORE (T016) | `XCOM-DU-007`, `XCOM-DU-008` |

All units are test-only. None is a runtime library, a shipped interface, or evidence of runtime,
transport, timing, compatibility, or production readiness.

## 3. `T016-TS-001` — Independent full-stack core fixture

- **Responsibility.** Build one valid accepted core stack (contract → endpoints → route → lifecycle →
  composition → loopback) for a caller-selected interaction family and declared-policy option, and own
  every retained value and handle.
- **Ownership.** `caller-owns-value` (the fixture object owns every contract, spec, controller,
  provider, composition, and handle by value). Returned `CommunicationItem` values are independent owned
  copies. The fixture exposes no borrowed internal storage.
- **Lifetime.** Bounded to the test case that constructs it. A prepared/active provider route and
  lifecycle record must not outlive the fixture; tests perform all provider operations within the same
  case. Nothing is process-scoped or static.
- **Thread-safety.** Construction and mutation are single-threaded. Immutable values, handles, and
  snapshots support concurrent const reads. Mutating provider operations serialize through the accepted
  provider/composition mutexes.
- **Bounds.** One contract; two endpoints; one route; endpoint capacity 2; route capacity 2; one
  provider; registry capacity 1; payload ≤ per-route requested bound ≤ 65,536 bytes; no dynamic growth.
- **Failure semantics.** A failed construction step leaves `ready()` false and exposes nothing usable;
  a test that uses a non-ready fixture fails. No partial or default value is substituted.
- **Doxygen obligation.** File block (`@file`, `@brief`, `@ownership`, `@lifetime`, `@thread_safety`,
  `@failure`); class-level `@brief` plus ownership/lifetime/thread-safety/failure tags; each accessor
  documented.
- **Requirement links.** `T016-SR-002`…`T016-SR-010`; consumed anchors `XCOM-DU-007`, `XCOM-DU-008`,
  `XCOM-SW-CORE-002/003/004/005/006/007/009/010`.
- **Planned evidence.** CHK-05…CHK-15.

## 4. `T016-TS-002` — Local probe provider

- **Responsibility.** An independently implemented `CommunicationProvider` with bounded one-route/one-
  item storage, observable prepare/activate/submit call counters, and a configurable forced-failure
  outcome, used to prove fail-closed dispatch suppression and provider isolation.
- **Ownership.** Owns its retained descriptor, binding, token, optional item, counters, and mutex. The
  registered instance must outlive its composition use; the composition retains it by non-owning
  reference.
- **Lifetime.** Bounded to the test case. Its counter state is per-instance and never static.
- **Thread-safety.** One mutex serializes every route/queue/counter operation; no callback runs while
  the composition holds its registry lock (verified by the re-entry case).
- **Bounds.** Routes ≤ 1; queue items ≤ 1; counters are `std::size_t`; `instance_id` is caller-selected
  and nonzero.
- **Failure semantics.** Invalid tokens/states return a stable outcome without mutating retained state;
  forced-failure mode returns the selected stable outcome and increments the counter; it never reports
  success.
- **Doxygen obligation.** File/class/`@brief` plus ownership/lifetime/thread-safety/failure tags.
- **Requirement links.** `T016-SR-003`, `T016-SR-005`, `T016-SR-009`, `T016-SR-010`; anchors
  `XCOM-DU-007`, `XCOM-SW-CORE-005/007`.
- **Planned evidence.** CHK-06, CHK-09, CHK-15, NEG-06…NEG-09, NEG-25.

## 5. `T016-TS-003` — Nominal unit matrix

- **Responsibility.** Execute the nominal consolidated matrix (interaction kinds, capabilities, policy,
  ownership, lifecycle, queue bounds, diagnostics) as individually named GTest cases.
- **Ownership.** Each case owns its fixture and any local values; no shared mutable fixture exists
  between cases.
- **Lifetime.** Per-case; nothing survives a case.
- **Thread-safety.** Cases are single-threaded except the const-read case, which performs concurrent
  const reads of an immutable value only.
- **Bounds.** Each case declares finite construction inputs; no unbounded loop, allocation, or wait.
- **Failure semantics.** A failed expectation fails the case; no case is skipped or disabled.
- **Doxygen obligation.** File block plus `@brief` on each helper.
- **Requirement links.** `T016-SR-002`…`T016-SR-008`, `T016-SR-011`(positive context); anchors
  `XCOM-DU-007`, `XCOM-DU-008`; `XCOM-SW-CORE-002/004/005/006/007/010`.
- **Planned evidence.** CHK-05…CHK-13.

## 6. `T016-TS-004` — Negative matrix (`SC-001`)

- **Responsibility.** Realize NEG-01…NEG-27, one named case each, spanning all four interaction
  families, asserting the exact stable outcome and the absence of any mutation on rejection.
- **Ownership.** Each case owns its fixture; injected-defect values are local; no shared state.
- **Lifetime.** Per-case.
- **Thread-safety.** Single-threaded; no concurrency assertion here (that is `T016-TS-006`).
- **Bounds.** ≤ 32 rejection attempts per case; each uses bounded identity/payload values within
  declared limits.
- **Failure semantics.** A missing, weaker, or non-exact outcome fails the case; a mutation detected
  after a rejection fails the case.
- **Doxygen obligation.** File block and `@brief` documentation of the shared assertion helper.
- **Requirement links.** `T016-SR-011`, `T016-SR-003`…`T016-SR-009`; anchors `XCOM-DU-007`,
  `XCOM-DU-008`; `XCOM-SW-CORE-009`, `XCOM-SYS-SC-001`, `SC-001`.
- **Planned evidence.** CHK-16, NEG-01…NEG-27.

## 7. `T016-TS-005` — Recovery matrix

- **Responsibility.** Prove saturation recovery, rejected-operation reusability, generation recreation,
  reconciliation mismatch, and empty-queue reporting.
- **Ownership.** Each case owns its fixture and provider; closed/recreated routes use a second fixture.
- **Lifetime.** Per-case; a recreated route is a new generation, and the earlier generation's handles
  are asserted stale.
- **Thread-safety.** Single-threaded.
- **Bounds.** ≤ 8 queued items per case; finite iteration count for drain.
- **Failure semantics.** A non-FIFO, lost, or duplicated item fails; a stale handle accepted as valid
  fails; a mismatch reported as success fails.
- **Doxygen obligation.** File block plus `@brief` helper documentation.
- **Requirement links.** `T016-SR-006`, `T016-SR-009`; anchors `XCOM-DU-007`, `XCOM-DU-008`;
  `XCOM-SW-CORE-005/009`.
- **Planned evidence.** CHK-11, CHK-14, NEG-20, NEG-21, NEG-25.

## 8. `T016-TS-006` — Concurrency matrix

- **Responsibility.** Prove deterministic concurrent submit/receive over one active route with declared
  finite thread/iteration budgets.
- **Ownership.** Each case owns its fixture; the fixture outlives every spawned thread; threads are
  joined before verdict.
- **Lifetime.** Per-case; no thread outlives the case.
- **Thread-safety.** The subject under test is the accepted provider/composition mutex serialization; the
  case asserts exactly-once delivery and per-route FIFO.
- **Bounds.** ≤ 4 threads; ≤ 8 items (queue bound) or ≤ 32 iterations; finite per-case constants.
- **Failure semantics.** A lost, duplicated, or reordered item fails; a deadlock/timeout fails; a
  callback observed under a lock fails.
- **Doxygen obligation.** File block plus `@brief` helper documentation.
- **Requirement links.** `T016-SR-010`, `T016-SR-013`; anchors `XCOM-DU-007`, `XCOM-DU-008`;
  `XCOM-SW-CORE-005/007`.
- **Planned evidence.** CHK-15, CHK-18, NEG-18, NEG-22 (concurrency form).

## 9. `T016-TS-007` — Fault-boundary matrix (`XCOM-SW-CORE-008`)

- **Responsibility.** Prove the `FR-024` controlled fault-hook boundary at the T016-owned core surface:
  no domain-specific fault semantics, only bounded controlled seams, no uncontrolled mutation entry
  point.
- **Ownership.** The case owns no product resource; it inspects the accepted public headers and the
  T016-owned surface read-only.
- **Lifetime.** Per-case.
- **Thread-safety.** Single-threaded inspection.
- **Bounds.** Finite scan over a fixed list of headers; no unbounded search.
- **Failure semantics.** Presence of a domain-specific fault primitive, an unbounded/ad-hoc injection
  entry point, or a mutation path without an exact handle fails the case.
- **Doxygen obligation.** File block plus `@brief` documentation.
- **Requirement links.** `T016-SR-012`; anchors `XCOM-DU-007`, `XCOM-SW-CORE-008`, `XCOM-SYS-FR-024`,
  `FR-024`, clarification C11, ACC009.
- **Planned evidence.** CHK-17, NEG-28.

## 10. `T016-TS-008` — External consumer

- **Responsibility.** Compile, link, and run a separate translation unit over the accepted public core
  include surface, performing one minimal round trip.
- **Ownership.** Owns its local values; no shared state.
- **Lifetime.** Process of the test executable.
- **Thread-safety.** Single-threaded.
- **Bounds.** One contract, one route, one item; bounded payload.
- **Failure semantics.** Returns nonzero on any expectation failure; asserts the public surface is
  usable from outside the package.
- **Doxygen obligation.** File block with `@brief`.
- **Requirement links.** `T016-SR-001`, `T016-SR-002`; anchors `XCOM-XLC-004`, `XCOM-DU-007`,
  `XCOM-DU-008`.
- **Planned evidence.** CHK-03, CHK-04.

## 11. Concurrency/resource bound summary

| Unit | Max threads | Max items/iterations | Max payload | Unbounded resources |
| --- | --- | --- | --- | --- |
| `T016-TS-001/002` | 1 | 1 (fixture) | ≤ 65,536 | none |
| `T016-TS-003` | 2 (const-read case only) | ≤ 8 | ≤ 65,536 | none |
| `T016-TS-004` | 1 | ≤ 32 attempts | ≤ 65,536 | none |
| `T016-TS-005` | 1 | ≤ 8 items | ≤ 65,536 | none |
| `T016-TS-006` | ≤ 4 | ≤ 8 items / ≤ 32 iterations | ≤ 65,536 | none |
| `T016-TS-007` | 1 | fixed header list | n/a | none |
| `T016-TS-008` | 1 | 1 item | ≤ 65,536 | none |

## 12. Traceability

| T016 requirement | Unit(s) | Planned checks |
| --- | --- | --- |
| T016-SR-001 | `T016-TS-001`, `T016-TS-008` | CHK-03, CHK-04, NEG-30 |
| T016-SR-002 | `T016-TS-001`, `T016-TS-003` | CHK-05 |
| T016-SR-003 | `T016-TS-002`, `T016-TS-003`, `T016-TS-004` | CHK-06, NEG-06…NEG-09, NEG-14, NEG-16, NEG-26 |
| T016-SR-004 | `T016-TS-001`, `T016-TS-003`, `T016-TS-004` | CHK-07, CHK-08, NEG-05, NEG-10…NEG-13 |
| T016-SR-005 | `T016-TS-001`, `T016-TS-002`, `T016-TS-003`, `T016-TS-004` | CHK-09, NEG-21, NEG-22, NEG-24, NEG-27 |
| T016-SR-006 | `T016-TS-003`, `T016-TS-005` | CHK-10, CHK-11, NEG-18, NEG-20 |
| T016-SR-007 | `T016-TS-003`, `T016-TS-004` | CHK-12, CHK-18, NEG-04, NEG-15, NEG-17…NEG-19 |
| T016-SR-008 | `T016-TS-003`, `T016-TS-004` | CHK-13 |
| T016-SR-009 | `T016-TS-005` | CHK-14 |
| T016-SR-010 | `T016-TS-006` | CHK-15 |
| T016-SR-011 | `T016-TS-004` | CHK-16, NEG-01…NEG-27 |
| T016-SR-012 | `T016-TS-007` | CHK-17, NEG-28 |
| T016-SR-013 | `T016-TS-005`, `T016-TS-006` | CHK-18 |
| T016-SR-014 | all | CHK-19, NEG-30 |
| T016-SR-015 | all | CHK-20, NEG-28 |
| T016-SR-016 | all | CHK-21, NEG-29 |
| T016-SR-017 | all | CHK-22 |
| T016-SR-018 | all | CHK-23, NEG-30 |
| T016-SR-019 | all | CHK-24, NEG-30 |
| T016-SR-020 | all | CHK-25 |

## 13. Bounds and open items

- `T016-LIM-04` — strict declaration-level Doxygen remains `DOX-GAP-01` (T011/T037); T016 documents
  every new file/declaration but does not enable the strict configuration.
- `T016-OPEN-01` — the GTest discovery style diverges from the hand-rolled suites of T013–T015 by design
  (per-case `SC-001` evidence); the divergence is additive and preserves every existing case.
- `T016-OPEN-02` — a later task that unifies core tests must preserve each T016 case name or replace it
  with an equivalent stronger case.
