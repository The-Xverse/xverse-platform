# T024 Requirements — Observation Acceptance Matrix (Metadata-Only, Payload Views, Ordering, Saturation, Degraded Validity, Safe Detach)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T024 (capability 007, slice `T-OBS`) |
| Task title | Test metadata-only zero-payload behavior, controlled payload views, redaction/truncation state, ordering, saturation, degraded validity, and safe detach |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6` |
| Authorization | capability 007 accepted design and bounded implementation authorization (ACC005/ACC010/ACC011/ACC014/ACC015); ADR-0016; ADR-0018; ADR-0019; ADR-0020 |
| Owning slice | `T-OBS` (T007 ownership register) |
| Predecessor | T023 (synthetic sink, failure/disconnect isolation, visible counters; reviewed terminal package) |
| Producer dependencies | T011 admitted offline build envelope (read-only inputs); T012 subtree CMake/CTest contract; T013 immutable core value/item/diagnostic types; T015 provider composition with the optional non-owning `ObservationHub` seam; T019 bounded activation-plan decode; T021 declared observation layer, immutable record, payload policy, and tap handle; T022 bounded drop/coalesce/lossless retention and applied validity effect; T023 synthetic sink consumer counters and isolation |
| Successor tasks | T025–T034 (stimulation/gateway), T035–T041 (evidence, review, acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}`; `docs/engineering/xcom/t008/requirements-register.{json,md}`; `docs/engineering/xcom/t008/traceability-matrix.{json,md}`; `docs/engineering/xcom/t009/architecture-model.{json,md}`; `docs/engineering/xcom/t010/unit-design.{json,md}` |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any test change and
does not implement, accept, or integrate the candidate. The T024 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T024 — Test metadata-only zero-payload behavior, controlled payload views, redaction/truncation state,
> ordering, saturation, degraded validity, and safe detach.

### 1.1 Authority statement

This document specifies only the bounded T024 slice. It elaborates the accepted software requirement
`XCOM-SW-OBS-005` "Normalized records for Argus consumers" (refines `XCOM-SYS-FR-023`, spec `FR-023`),
which `docs/engineering/xcom/t008/requirements-register.{json,md}` attributes to T024, and it consolidates
the verification obligations that T021 (`T021-GAP-04`), T022 (`T022-GAP-03`), and T023 (`T023-GAP-01`)
explicitly allocated to the "broad observation matrix": metadata-only zero-payload, controlled payload
views, redaction/truncation state, ordering, saturation, degraded validity, and safe detach.

It verifies — read-only — the accepted behaviours of `XCOM-SW-OBS-001…-004` at the exact T024 baseline,
and it completes the `T-OBS` slice evidence names recorded by the T007 ownership register
(`controlled-payload-view`, `degraded-validity`, `metadata-only-zero-payload`, `ordering`, `safe-detach`,
`saturation`; `disabled-tap-performance` remains T036). It consumes the accepted observation contract
(`specs/007-xcom-core/contracts/observation.md`, design contract `XCOM-XLC-003`), the accepted data model
(`specs/007-xcom-core/data-model.md`: `ObservationTap` counters and the tap state
`declared → attached → active → degraded → detached`), and the accepted architecture components
`XCOM-CMP-008` "Observation boundary" and `XCOM-CMP-011` "Synthetic sink and tools", and design units
`XCOM-DU-012` (declared observation layer) and `XCOM-DU-013` (bounded observer queue, counters, and
synthetic sink).

It does **not** redesign the accepted architecture, change a functional requirement, success criterion,
ADR, schema, or contract, add production source, fix a value, implement the payload identity allow-list,
decoder, rate limit, stimulation, gateway, benchmark, or any later task, add an admitted dependency,
weaken an accepted requirement or test, or accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, the
T007 ownership register, the T008 register/matrix, the T009 architecture model, the T010 unit design, the
constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is reported
rather than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T024)

1. **Consolidated observation acceptance matrix (tests only).** Add a cohesive, auditable set of matrix
   cases to the existing T-OBS observation fixtures under `tests/xcom/observation/`:
   - `tests/xcom/observation/core/unit_tests.cpp` — seven new matrix cases over the accepted
     `xverse::xcom` observation surface (`ObservationHub`, `ObservationTapSpec`, `ObservationRecord`,
     `ObservationSnapshot`, `SyntheticObservationSink`);
   - `tests/xcom/observation/integration/integration_tests.cpp` — two new route-level matrix cases over
     the accepted provider/loopback composition linked to one `ObservationHub`.
   The cases are additive: every existing case and assertion is preserved unchanged.
2. **Metadata-only zero-payload matrix (SC-003, FR-012).** Exercise `metadata_only` across the four
   accepted interaction families and several source sizes, proving zero exposed payload bytes, the
   `omitted` view state, `undecoded` schema state, the complete `source_payload_size`, and that **every**
   emitted observation record carries origin, logical contract/interface/endpoint, clock domain, route,
   sequence/correlation/causation, provider identity, and provider outcome.
3. **Controlled payload-view matrix (SC-003, FR-012).** Exercise `bounded_prefix` at the boundary
   (`source < bound`, `source == bound`, `source > bound`, minimum and maximum declared bound) plus
   explicit `redacted`, proving exact leading-prefix bytes, `complete`/`truncated`/`redacted`/`omitted`
   states, and that no decode/schema success (`PayloadSchemaState::undecoded`) is ever invented.
4. **Ordering matrix (SC-004, SC-005).** Exercise per-tap FIFO retention under `drop_newest` and
   `coalesce_latest` (including the coalesced replacement moving to the newest position while unrelated
   records keep their order), independent ordering across two taps on one hub, strictly increasing
   pulled sequence for a single logical stream, and the route-level `per_route_fifo` order remaining
   unchanged while a best-effort observer is blocked, removed, or failed.
5. **Saturation matrix (SC-004, FR-013).** Exercise `drop_newest` at the minimum (1) and maximum (16)
   declared capacity, `coalesce_latest` logical-key selection, and `lossless_validation`
   pre-provider-mutation rejection and recovery, proving the queue never exceeds its declared bound,
   the accepted loss counters are exact and observable, and the accounting identity holds per policy.
6. **Degraded-validity matrix (SC-004, FR-013).** Exercise the applied declared `ObservationValidityEffect`
   across all three effects and all three loss modes, the lossless "at least degraded" rule, the realized
   `ObservationValidityState` and the `experiment_validity_degraded` compatibility projection, monotonicity
   within an interval, acknowledgement closing a `degraded` interval while `invalid` persists, and
   discarding of the realized status with safe detach or slot recreation.
7. **Safe-detach matrix (SC-005, FR-014).** Exercise the complete detach/dispatch matrix: detach discards
   only its own retained records; a stale-generation, foreign-hub, or closed handle is rejected with the
   stable outcome and mutates nothing; detach of a claimed tap returns `tap_busy`; a repeated close of an
   already closed exact handle returns `tap_closed`; and the normal route keeps its item count, order, and
   outcomes after observer removal.
8. **Normalized-record matrix (`XCOM-SW-OBS-005`, FR-023).** Exercise the complete normalized record for
   each accepted interaction family, origin, and provider outcome (`not_attempted`, `accepted`,
   `rejected`), proving the record is self-describing, value-owned, and provider-neutral, and that X-COM
   owns no dashboard rendering, storage, query, or presentation primitive (ADR-0019).
9. **Additivity and boundary preservation.** Re-verify that no production source, existing test case,
   accepted requirement, ADR, contract, schema, register, build file, or another task's path is changed,
   and that the T024 candidate implements no later task.
10. The T024 repository-owned work products and the T024 package record.

### 2.2 Explicit exclusions (must remain absent from the T024 candidate)

No production source change under `src/xverse/xcom/` (the matrix consumes `observation.hpp`/`observation.cpp`
and the accepted core/provider headers read-only); no change to any `*.hpp`/`*.cpp` unit, `CMakeLists.txt`,
`cmake/*.cmake`, or any build file; no change to `tests/xcom/observation/integration/test_support.hpp`,
`tests/xcom/observation/integration/disabled_tap_benchmark.cpp`, or any other task's test source; no
removal, rename, reordering, or weakening of any existing observation case, assertion, or expected value;
no new CTest target, test name, label, or command; no new `ObservationOutcome`,
`ObservationOverflowPolicy`, `ObservationValidityEffect`, `ObservationValidityState`, or
`PayloadViewState` value; no payload identity allow-list (`payloadAccess: allow-listed` + `allowList`), no
redaction profile, and no decoder/schema interpretation beyond the accepted
`PayloadSchemaState::undecoded`; no `bounds.maxRateHz` rate limiting; no disabled-tap benchmark execution
(T036); no stimulation, journaling, time authority, gateway, Protocol Buffers/gRPC, IPC/TCP, persistence,
XDL compilation, adapter, Argus/dashboard/storage/export/OpenTelemetry, or legacy behaviour; no new
admitted dependency; no network, socket, DNS, TLS, filesystem, process, dynamic-load, ambient/secret, or
legacy-repository access; no rewrite or weakening of an accepted ADR, requirement, contract, test, REF-002
disposition, or another task's ownership path; no promotion of any REF-002 or capability requirement; no
acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T024 |
| --- | --- | --- |
| Disabled-tap performance benchmark and its threshold (`SC-008`) | T036 | allocated; T024 re-runs the benchmark under the gate but claims no `disabled-tap-performance` evidence |
| Payload identity allow-list (`payloadAccess: allow-listed` + `allowList`), redaction profile, decoder/schema status beyond `undecoded` | unclaimed behaviour | recorded; stays unimplemented/partial (§7) |
| `bounds.maxRateHz` rate limiting | not T024 | not implemented; remains a declared-but-unrealized Profile bound |
| Separate-process synthetic client and tool-gateway observation path | T032/T033 | allocated; T024 exercises the in-process hub and sink only |
| Executed sanitizer/static-analysis/Doxygen evidence; integration, validation, delivery bundle | T035–T040 | allocated |
| Independent review and user acceptance | T039/T041 | allocated |

## 3. Stakeholder requirements (`T024-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T024-STK-001**: Before the observation boundary is accepted, the program **shall** have a
  repository-owned, bounded, domain-neutral consolidated observation acceptance matrix, physically under
  `tests/xcom/observation/`, that exercises metadata-only zero-payload behaviour, controlled payload views,
  redaction/truncation state, ordering, saturation, degraded validity, safe detach, and normalized-record
  completeness offline under the T011-admitted toolchain and the T012 warning-as-error contract.
- **T024-STK-002**: The matrix **shall** prove the accepted success criteria `SC-003`, `SC-004`, and
  `SC-005` over the accepted observation boundary: metadata-only exposes zero payload bytes while every
  emitted record is normalized and self-describing; every queue stays within its declared bound with exact
  loss counters and validity status; and removing, blocking, or failing a best-effort observer does not
  change the owned deterministic route's item count, order, or delivery outcomes.
- **T024-STK-003**: The matrix **shall** prove `XCOM-SW-OBS-005` / `FR-023`: X-COM publishes normalized
  observation records suitable for Argus and third-party consumers while owning no dashboard rendering,
  long-term storage, or query presentation; no export/presentation primitive is added by T024.
- **T024-STK-004**: The matrix **shall** be offline, domain-neutral, bounded, and deterministic: it uses
  only the C++ standard library plus the already admitted test dependencies; every thread, item, duration,
  and payload used by the matrix is finite and declared; it performs no network, ambient, secret,
  filesystem, process, dynamic-load, or legacy access; and it adds no domain-specific primitive.
- **T024-STK-005**: T024 **shall** preserve accepted intent: the delivered change is confined to the
  T024-owned test paths, the T024 work products, and the capability task ledger, and it **shall** neither
  weaken an accepted requirement or test nor implement another task.

## 4. Software/engineering requirements (`T024-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Verified" means the repository-owned test exists, is deterministic, and passes at the recorded
candidate revision; it is not a runtime, transport, timing, or production claim.

### 4.1 Harness, additivity, and registration

- **T024-SR-001 [ubiquitous]**: The matrix **shall** be realized additively inside the existing T-OBS
  observation fixtures `tests/xcom/observation/core/unit_tests.cpp` and
  `tests/xcom/observation/integration/integration_tests.cpp`, registered through their existing
  `xcom_observation_unit` and `xcom_observation_integration` executables, and **shall** change no build
  file, target, test name, label, command, or existing case.
  - Refines: `XCOM-SW-OBS-005`; anchors `SC-003`, `SC-004`, `SC-005`; T012 subtree build contract;
    T007 shared-path rule.
  - Verification intent: changed-path and discovered-count comparison; CHK-02, CHK-20, NEG-01.
- **T024-SR-002 [ubiquitous]**: Every new matrix case **shall** be independently named, use only the
  accepted public observation API and the admitted test dependencies, construct each policy through
  `ObservationTapSpec::create`, and assert each expected value explicitly, so that removing or weakening an
  expectation fails the executable.
  - Refines: `XCOM-SW-OBS-005`; anchors `SC-003`; T012 warning-as-error contract.
  - Verification intent: case-inventory inspection plus the passing executable; CHK-03, CHK-04.

### 4.2 Metadata-only zero-payload matrix

- **T024-SR-003 [ubiquitous]**: Under `metadata_only`, every pulled record **shall** expose an empty
  `payload_bytes()` span with `PayloadViewState::omitted` and `PayloadSchemaState::undecoded`, report the
  complete `source_payload_size`, and preserve contract/version, interface, endpoint, schema, interaction
  kind, origin, source/observation timestamps and clock domains, sequence, correlation, causation, route,
  provider, declared tap, and provider outcome — for the four accepted interaction families and for
  zero-, one-, and four-byte sources.
  - Refines: `XCOM-SW-OBS-001`, `XCOM-SW-OBS-002`, `XCOM-SW-OBS-005`; anchors `XCOM-SYS-FR-011/FR-012`,
    `XCOM-SYS-SC-003`; FR-011, FR-012, SC-003; `XCOM-DU-012`, `XCOM-DU-013`; contracts/observation.md
    "metadata-only: no payload bytes are exposed".
  - Verification intent: metadata zero-payload family/size matrix plus the 100 %-record completeness check;
    CHK-05, NEG-02, NEG-03.
- **T024-SR-004 [ubiquitous]**: The matrix **shall** prove that 100 % of emitted observation records for a
  matched batch are retained, pulled exactly once in FIFO order, and never silently dropped while the queue
  is within its declared bound, with the accepted `accepted`/`queued` counters reporting the batch exactly.
  - Refines: `XCOM-SW-OBS-003`, `XCOM-SW-OBS-005`; anchors `XCOM-SYS-SC-003`; SC-003; `XCOM-DU-013`.
  - Verification intent: batch-completeness and accounting identity; CHK-05, CHK-15.

### 4.3 Controlled payload-view, redaction, and truncation matrix

- **T024-SR-005 [ubiquitous]**: Under `bounded_prefix`, the matrix **shall** prove the payload view for a
  source smaller than, equal to, and larger than the declared bound: `complete` with the exact source bytes
  when `source ≤ bound`, and `truncated` with exactly the leading `bound` bytes when `source > bound`; the
  declared bound **shall** be accepted from one through `kMaximumObservedPayloadBytes` and rejected at zero
  or above the maximum.
  - Refines: `XCOM-SW-OBS-002`; anchors `XCOM-SYS-FR-012`, `XCOM-SYS-SC-003`; FR-012, SC-003;
    `XCOM-DU-012`; contracts/observation.md "controlled-payload: exposes only the declared payload view and
    reports redaction/truncation/decode state".
  - Verification intent: prefix boundary table and bound acceptance/rejection; CHK-06, NEG-04, NEG-05.
- **T024-SR-006 [ubiquitous]**: Under `redacted`, every record **shall** expose an empty
  `payload_bytes()` span with `PayloadViewState::redacted` and the complete `source_payload_size`; under
  every payload mode the schema state **shall** remain `PayloadSchemaState::undecoded`, so the matrix
  **shall** fail if any decode/schema success is reported.
  - Refines: `XCOM-SW-OBS-002`; anchors `XCOM-SYS-FR-012`; FR-012; `XCOM-DU-012`.
  - Verification intent: redaction and no-decode-claim assertions; CHK-06, NEG-06, NEG-07.

### 4.4 Ordering matrix

- **T024-SR-007 [ubiquitous]**: Retained records **shall** be pulled in exact FIFO insertion order for a
  single declared tap: `drop_newest` preserves the oldest retained records and the pulled sequence is
  strictly increasing; `coalesce_latest` keeps unrelated records in order while the replacement of a
  matching logical key moves to the newest position; and two taps attached to one hub **shall** keep
  independent FIFO order and counters, so pulling from one never reorders or consumes the other's records.
  - Refines: `XCOM-SW-OBS-003`; anchors `XCOM-SYS-FR-013`, `XCOM-SYS-SC-004`; FR-013, SC-004;
    `XCOM-DU-013`.
  - Verification intent: per-tap FIFO, coalesce-position, and multi-tap independence cases; CHK-08, NEG-08,
    NEG-09.

### 4.5 Saturation matrix

- **T024-SR-008 [ubiquitous]**: Under `drop_newest`, when the declared capacity is reached, the new
  matching record **shall** be dropped without error, `dropped` **shall** increment by exactly one, the
  oldest retained records and their FIFO order **shall** be preserved, the queue **shall** stay at or below
  its declared capacity, and `accepted + dropped == submissions` **shall** hold — at the minimum (1) and
  maximum (16) declared capacity.
  - Refines: `XCOM-SW-OBS-003`; anchors `XCOM-SYS-FR-013`, `XCOM-SYS-SC-004`; FR-013, SC-004;
    `XCOM-DU-013`; contracts/observation.md "Queue overflow follows the configured drop or coalesce rule and
    increments deterministic counters".
  - Verification intent: min/max-capacity drop-newest bound and accounting identity; CHK-09, NEG-10, NEG-11.
- **T024-SR-009 [ubiquitous]**: Under `coalesce_latest`, when the declared capacity is reached, the newest
  retained record having the same exact logical key **shall** be replaced (moving to the newest position)
  and `coalesced` **shall** increment by exactly one; a non-matching record **shall** be dropped
  (`dropped` + 1); and the queue **shall** remain at or below its declared capacity.
  - Refines: `XCOM-SW-OBS-003`; anchors `XCOM-SYS-FR-013`, `XCOM-SYS-SC-004`; FR-013, SC-004;
    `XCOM-DU-013`.
  - Verification intent: coalesce key-selection and counters; CHK-09, NEG-12, NEG-13.
- **T024-SR-010 [ubiquitous]**: Under `lossless_validation`, a matching submission when capacity is
  unavailable **shall** be rejected with the stable `observation_backpressure` **before** any provider or
  queue mutation, `backpressure_rejections` **shall** increment by exactly one, the realized validity
  **shall** be raised, and no normal-route item **shall** be emitted; after an exact cancellation,
  acknowledgement, or drain the capacity **shall** recover and a subsequent reservation **shall** commit.
  - Refines: `XCOM-SW-OBS-003`; anchors `XCOM-SYS-FR-013`, `XCOM-SYS-SC-004`; FR-013, SC-004;
    `XCOM-DU-013`; contracts/observation.md "lossless-validation: observation backpressure may affect the
    route only because the experiment explicitly includes that behavior".
  - Verification intent: pre-mutation rejection, recovery, and zero-emission checks; CHK-10, NEG-14, NEG-15.

### 4.6 Degraded-validity matrix

- **T024-SR-011 [ubiquitous]**: The applied declared `ObservationValidityEffect` **shall** select the
  realized `ObservationValidityState` on a matching best-effort loss (`none → valid`,
  `degrade_on_loss → degraded`, `invalidate_on_loss → invalid`), and the
  `experiment_validity_degraded` compatibility projection **shall** equal
  `validity_state != valid`; a lossless-validation backpressure **shall** realize at least `degraded`
  under every declaration.
  - Refines: `XCOM-SW-OBS-003`; anchors `XCOM-SYS-FR-013`, `XCOM-SYS-SC-004`; FR-013, SC-004;
    `XCOM-DU-013`; data-model tap state `degraded`.
  - Verification intent: effect × loss-mode validity table and the at-least-degraded rule; CHK-11, NEG-16,
    NEG-17.
- **T024-SR-012 [ubiquitous]**: Within one tap interval the realized validity **shall** never decrease
  without an exact acknowledgement or detach; `acknowledge` **shall** reset `backpressure_rejections` to
  zero and return a `degraded` realized status to `valid` while an `invalid` status **shall** persist; and
  a safe detach or slot recreation **shall** discard the realized status and counters, so a recreated
  generation starts `valid` with zero counters.
  - Refines: `XCOM-SW-OBS-004`; anchors `XCOM-SYS-FR-013/FR-014`, `XCOM-SYS-SC-004/SC-005`; FR-013,
    FR-014, SC-004, SC-005; `XCOM-DU-013`.
  - Verification intent: monotonicity, acknowledgement, and discard-on-detach cases; CHK-11, CHK-12,
    NEG-18, NEG-19.

### 4.7 Safe-detach and route-neutrality matrix

- **T024-SR-013 [ubiquitous]**: `ObservationHub::detach` **shall** close one exact current handle and
  discard only that tap's retained records, leaving every other tap, its counters, its realized validity,
  and its generation unchanged; a stale-generation, foreign-hub, or unknown handle **shall** return the
  stable `invalid_tap_handle` with no mutation; a repeated close of an already closed exact handle **shall**
  return `tap_closed`; and a detach attempted while an exact claim is in flight **shall** return `tap_busy`
  without discarding the retained records.
  - Refines: `XCOM-SW-OBS-004`; anchors `XCOM-SYS-FR-009/FR-014`, `XCOM-SYS-SC-005`; FR-009, FR-014,
    SC-005; `XCOM-DU-013`; data-model tap state `detached`.
  - Verification intent: detach/ownership matrix and no-mutation checks; CHK-13, NEG-20, NEG-21.
- **T024-SR-014 [ubiquitous]**: Removing, blocking, disconnecting, or failing a best-effort observer
  **shall** not change the owned deterministic route's item count, FIFO order, or delivery outcomes: the
  matrix **shall** assert the route count, per-route `per_route_fifo` receive order, and every provider
  outcome before, during, and after observer removal, a non-pulling observer, and a stale-handle failure.
  - Refines: `XCOM-SW-OBS-004`; anchors `XCOM-SYS-FR-014`, `XCOM-SYS-SC-005`; FR-014, SC-005;
    `XCOM-DU-013`; contracts/observation.md "Best-effort observer failure, delay, or disconnection cannot
    block or reorder the normal route".
  - Verification intent: route count/order/outcome invariance across the observer-isolation matrix;
    CHK-14, NEG-22, NEG-23.

### 4.8 Normalized-record matrix (`XCOM-SW-OBS-005`)

- **T024-SR-015 [ubiquitous]**: For each accepted interaction family, each declared origin, and each
  explicit provider outcome (`not_attempted`, `accepted`, `rejected`), the pulled record **shall** be
  self-describing and complete: the exact logical contract/version, interface, endpoint, schema/version,
  interaction kind, origin, source and observation timestamps with clock domains, sequence, correlation,
  causation, route, provider, declared tap, source payload size, provider outcome, payload view state, and
  the retention-time counter projection **shall** round-trip exactly, and the record **shall** remain a
  value-owned copy whose fields are independent of later hub mutation.
  - Refines: `XCOM-SW-OBS-005`; anchors `XCOM-SYS-FR-023`; FR-023; `XCOM-DU-012`, `XCOM-DU-013`;
    contracts/observation.md "Observation records include route and logical identities, origin, schema
    identity, source/observation time and clock domains, sequence/correlation/causation, sizes, outcome,
    payload-view status, and tap counters".
  - Verification intent: family × origin × outcome normalized-record cross-product; CHK-16, NEG-24.
- **T024-SR-016 [ubiquitous]**: The T024 candidate **shall** add no dashboard rendering, long-term
  storage, query, presentation, export, OpenTelemetry, or adapter primitive; the matrix **shall** exercise
  only the in-process normalized record and hub snapshot, and the matrix **shall** fail if such a
  primitive appears in the T024 surface.
  - Refines: `XCOM-SW-OBS-005`; anchors `XCOM-SYS-FR-023`; FR-023; ADR-0019.
  - Verification intent: forbidden-vocabulary scan of the changed tests; CHK-17, NEG-25.

### 4.9 Bounds, concurrency, neutrality, safety, and governance

- **T024-SR-017 [ubiquitous]**: Every resource the matrix uses **shall** be finite and declared: at most
  four test threads, at most `kMaximumObservationTaps` (8) taps per hub, at most
  `kMaximumObservationRecordsPerTap` (16) retained records per tap, bounded item and iteration counts, and
  fixture payloads of at most four synthetic bytes; no case **shall** perform an unbounded loop, unbounded
  allocation, unbounded wait, unbounded retry, or depend on wall-clock timing for its verdict.
  - Refines: `XCOM-SW-OBS-003`, `XCOM-SW-OBS-004`; anchors `XCOM-SYS-FR-007`; FR-007; `XCOM-DU-013`;
    T010 bounds vocabulary.
  - Verification intent: matrix self-bound inspection and deterministic repeated runs; CHK-18, NEG-26.
- **T024-SR-018 [ubiquitous]**: The matrix **shall** verify deterministic concurrency with a declared,
  finite budget: concurrent publication and pull (or concurrent reservations over one lossless tap)
  produce no lost or duplicated claim, no unstable outcome, and a consistent counter/queue state, and
  repeated bounded runs produce the same observable outcome with no callback under an X-COM lock.
  - Refines: `XCOM-SW-OBS-003`, `XCOM-SW-OBS-004`; anchors `XCOM-SYS-FR-014`; FR-014; `XCOM-DU-013`.
  - Verification intent: bounded deterministic concurrency and repeated-run checks; CHK-18, CHK-19,
    NEG-26.
- **T024-SR-019 [ubiquitous]**: The T024 candidate **shall** be offline and domain-neutral: it **shall**
  use only the C++ standard library plus the already admitted test dependencies, perform no network,
  socket, resolver, TLS, ambient, secret, filesystem, process, dynamic-load, or legacy access, add no
  domain-specific primitive, and add no new admitted dependency.
  - Refines: `XCOM-SW-CORE-007` (domain-neutral local runtime half); anchors FR-023, FR-026, FR-028;
    ADR-0019; Constitution II, VII.
  - Verification intent: forbidden-API source scan plus the successful offline build; CHK-21, NEG-27.
- **T024-SR-020 [ubiquitous]**: Committed test source and work products **shall** contain no credential,
  private address, unrestricted or real payload, proprietary source excerpt, environment-specific absolute
  host path, or sensitive deployment value; fixture payload bytes **shall** be bounded, synthetic, and
  non-sensitive.
  - Refines: Constitution X; anchors FR-027; `XCOM-SW-INTG` public-safe evidence rule.
  - Verification intent: public-safety scan; CHK-22, NEG-28.
- **T024-SR-021 [ubiquitous]**: The T024 candidate **shall** be additive: no existing test case,
  assertion, target, label, command, threshold, expected result, requirement, ADR, contract, schema,
  register, build file, or another task's ownership path **shall** be removed, renamed, reordered, or
  weakened; the accepted T021/T022/T023 declaration, retention, validity, payload, record, handle, and
  sink behavior **shall** be preserved unchanged; and no later task (T025+) **shall** be implemented.
  - Refines: ADR-0018, ADR-0020; T007 global prohibitions; anchors FR-030; Constitution VII, IX.
  - Verification intent: changed-path, discovered-count, and vocabulary comparison; CHK-02, CHK-20,
    NEG-01, NEG-29.
- **T024-SR-022 [ubiquitous]**: Every new test file or case helper declaration **shall** carry useful
  Doxygen documentation including its ownership, lifetime, thread-safety, and failure contract, and the
  existing file-block traceability note **shall** be updated to name T024, without changing the admitted
  repository documentation configuration.
  - Refines: `XCOM-SW-OBS-005` Doxygen; anchors FR-029; `XCOM-DU-013` Doxygen plan; Constitution X.
  - Verification intent: declaration inspection; CHK-23.
- **T024-SR-023 [ubiquitous]**: The T024 candidate **shall** satisfy the deterministic Fabro gate for a
  test task: the six named work products exist, at least one `tests/` path changes, `cmake` configure,
  build, discovery, and the full `ctest` suite pass, and `git diff --check` is clean; the T024 checkbox is
  marked complete **only** in the implementation stage.
  - Refines: ADR-0020; anchors FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T024 <baseline>`; `git diff --check`; CHK-24, NEG-29.
- **T024-SR-024 [ubiquitous]**: T024 **shall** reconcile with the T007 ownership register, the T008
  requirement register/matrix, the T009 architecture model, and the T010 unit design without rewriting or
  weakening them; **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list; and
  **shall** record honestly (a) that the T008 register attributes `XCOM-SW-OBS-005` to T024 and marks it
  `verified_by` `XCOM-T-OBS` (`XCOM-L-0100/0101/0102`), (b) the `T021-GAP-04`/`T022-GAP-03`/`T023-GAP-01`
  matrix handoff this task closes, (c) that `disabled-tap-performance` remains T036, and (d) that the
  SESN-era validator `scripts/validate_xcom_observation.py` is not used by the repository-owned workflow.
  - Refines: ADR-0020; anchors FR-030, FR-035; Constitution VII, IX.
  - Verification intent: register validators plus the recorded-attribution inspection; CHK-25, NEG-29.

## 5. Requirement-to-accepted-anchor traceability

| T024 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T024-STK-001 | `XCOM-SW-OBS-001…-005` | XCOM-SYS-FR-011…014, FR-023 | FR-011…FR-014, FR-023 | IX, X |
| T024-STK-002 | `XCOM-SW-OBS-003`, `XCOM-SW-OBS-004` | XCOM-SYS-FR-013/014 | FR-013, FR-014 | SC-003, SC-004, SC-005 |
| T024-STK-003 | `XCOM-SW-OBS-005` | XCOM-SYS-FR-023 | FR-023 | II, IX |
| T024-STK-004 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-023/026/028 | FR-023, FR-026, FR-028 | II, VII, IX |
| T024-STK-005 | Constitution VII/IX; ADR-0018/0020 | – | FR-030 | VII, IX, X |
| T024-SR-001 | `XCOM-SW-OBS-005` | XCOM-SYS-SC-003…005 | FR-013, FR-014, FR-023 | VII, X |
| T024-SR-002 | `XCOM-SW-OBS-005` | XCOM-SYS-SC-003 | FR-012 | IX |
| T024-SR-003 | `XCOM-SW-OBS-001/002/005` | XCOM-SYS-FR-011/012, SC-003 | FR-011, FR-012, SC-003 | IX |
| T024-SR-004 | `XCOM-SW-OBS-003/005` | XCOM-SYS-SC-003 | FR-013, SC-003 | IX |
| T024-SR-005 | `XCOM-SW-OBS-002` | XCOM-SYS-FR-012, SC-003 | FR-012, SC-003 | IX |
| T024-SR-006 | `XCOM-SW-OBS-002` | XCOM-SYS-FR-012 | FR-012 | IX |
| T024-SR-007 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-013, SC-004 | FR-013, SC-004 | IX |
| T024-SR-008 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-013, SC-004 | FR-013, SC-004 | IX |
| T024-SR-009 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-013, SC-004 | FR-013, SC-004 | IX |
| T024-SR-010 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-013, SC-004 | FR-013, SC-004 | IX |
| T024-SR-011 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-013, SC-004 | FR-013, SC-004 | IX |
| T024-SR-012 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-013/014, SC-004/005 | FR-013, FR-014, SC-004, SC-005 | IX |
| T024-SR-013 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-009/014, SC-005 | FR-009, FR-014, SC-005 | V, IX |
| T024-SR-014 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-014, SC-005 | FR-014, SC-005 | IX |
| T024-SR-015 | `XCOM-SW-OBS-005` | XCOM-SYS-FR-023 | FR-023 | IX |
| T024-SR-016 | `XCOM-SW-OBS-005` | XCOM-SYS-FR-023 | FR-023 | II, VII |
| T024-SR-017 | `XCOM-SW-OBS-003/004` | XCOM-SYS-FR-007 | FR-007 | IX |
| T024-SR-018 | `XCOM-SW-OBS-003/004` | XCOM-SYS-FR-014 | FR-014 | IX |
| T024-SR-019 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-023/026/028 | FR-023, FR-026, FR-028 | II, VII |
| T024-SR-020 | public-safe evidence rule | XCOM-SYS-FR-027 | FR-027 | X |
| T024-SR-021 | Constitution; ADR-0018/0020 | XCOM-SYS-FR-030 | FR-030 | VII, IX |
| T024-SR-022 | `XCOM-SW-OBS-005` Doxygen | XCOM-SYS-FR-029 | FR-029 | X |
| T024-SR-023 | ADR-0020 | – | FR-030 | X |
| T024-SR-024 | Constitution; ADR-0020 | XCOM-SYS-FR-035 | FR-030, FR-035 | VII, IX |

`XCOM-SW-OBS-001…-005` are the accepted capability-007 software requirements
(`docs/engineering/xcom/t008/requirements-register.{json,md}`). They are accepted text; T024 refines and
consumes them and does not rewrite them. The register attributes `XCOM-SW-OBS-005` (FR-023) to T024 and
records it as `verified_by` `XCOM-T-OBS` (`XCOM-L-0102`); T024 satisfies that verification obligation and
records the payload-view allocation (`XCOM-SW-OBS-002`, unclaimed allow-list half) honestly. No register
row is changed and no maturity is promoted.

## 6. REF-002 disposition

T024 owns no REF-002 SADS ID and promotes none. It provides the consolidated verification evidence against
the allocated observation IDs: `XVE-SYS-0149` (observation records, metrics, counters, and tool streams),
`XVE-SYS-0142` (provider-neutral records), and `XVE-SYS-0140` (interaction families retained), and it
preserves the `XVE-SYS-0151` disposition (Argus analytics, storage, and presentation are **not**
implemented: T024 exercises only the in-process normalized record and snapshot). The capability
`ref002.disposition` stays `unchanged` with an empty `promoted` list (T024-SR-024). No allocated, deferred,
architectural-target, or superseded SADS requirement is reported as implemented, and no `XVE-SYS-*` ID is
promoted.

## 7. Affected paths

### 7.1 Paths the T024 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `tests/xcom/observation/core/unit_tests.cpp` | edit | adds the seven T024 unit matrix cases, registers them in `main()`, and updates the file-block traceability note to name T024; every existing case and assertion is byte-preserved |
| `tests/xcom/observation/integration/integration_tests.cpp` | edit | adds the two T024 route-level matrix cases, registers them in `main()`, and updates the file-block traceability note; every existing case and assertion is byte-preserved |
| `docs/engineering/xcom/t024/requirements.md` | add | this document |
| `docs/engineering/xcom/t024/architecture.md` | add | matrix context, components, data flow, interfaces (plan stage) |
| `docs/engineering/xcom/t024/detailed-design.md` | add | case matrix, fixtures, expected values, bounds (plan stage) |
| `docs/engineering/xcom/t024/unit-specifications.md` | add | case units, ownership/lifetime/thread-safety/bounds, traceability (plan stage) |
| `docs/engineering/xcom/t024/verification-plan.md` | add | named checks, negative cases, commands, evidence (plan stage) |
| `docs/engineering/xcom/t024/implementation.md` | add (implementation stage) | realized change and candidate-bound local evidence |
| `docs/engineering/xcom/t024/internal-review.json` | add (review stage) | separate read-only DeepSeek internal review |
| `specs/007-xcom-core/tasks.md` | edit T024 checkbox (implementation stage only) | capability task ledger; `- [ ] T024` → `- [X] T024` |
| `reports/xcom-queue/t024-package.json` | add (package stage) | exact-candidate package record |

No build file change: the existing `xcom_observation_unit` executable already compiles
`tests/xcom/observation/core/unit_tests.cpp` and the existing `xcom_observation_integration` executable
already compiles `tests/xcom/observation/integration/integration_tests.cpp`, so the new cases are
discovered without adding or renaming a target, test, or label. No production source changes.

### 7.2 T024-owned observation paths consumed and re-verified unchanged

| Path | Owner | Role for T024 |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/observation.hpp`, `src/xverse/xcom/src/observation.cpp` | T-OBS (T021/T022/T023) | the accepted observation surface under test; consumed read-only, never edited |
| `tests/xcom/observation/integration/test_support.hpp` | T-OBS (T023/T024) | re-run unchanged; the new route-level cases construct any extra policy through `ObservationTapSpec::create` inline so this shared helper is not edited |
| `tests/xcom/observation/integration/disabled_tap_benchmark.cpp` | T-OBS (T036 owns execution) | re-run unchanged, not edited |
| `scripts/validate_xcom_observation.py` | T-OBS (legacy SESN evidence) | not executed, not edited, and not used as T024 evidence |

### 7.3 Consumed, read-only foundation (not changed by T024)

| Path | Owner | Role for T024 |
| --- | --- | --- |
| `src/xverse/xcom/CMakeLists.txt`, `cmake/*.cmake`, `CMakeLists.txt` | shared (serialized) | T012 subtree build contract that compiles the observation fixtures; T024 changes none |
| `src/xverse/xcom/include/xverse/xcom/{value,contract,item,diagnostic,result,core_types}.hpp` | T013 (T-CORE) | validated `Identity`, `SemanticVersion`, `CommunicationItem`, diagnostics; consumed read-only |
| `src/xverse/xcom/include/xverse/xcom/{provider,loopback_provider,endpoint_route_lifecycle}.hpp` | T014/T015 (T-CORE) | provider composition, loopback provider, and lifecycle; consumed read-only by the integration cases |
| `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp` | T-XDL | decoded plan; not exercised by T024 |
| `docs/engineering/xcom/t021/*`, `t022/*`, `t023/*` | T021/T022/T023 | predecessor work products; T024 records the §7.4 handoff and rewrites nothing |
| `docs/xcom/observation-boundary.md`, `docs/xcom/observation-boundary-traceability.json` | legacy SESN evidence bundle | historical evidence for an exact superseded revision only; neither current acceptance evidence nor rewritten |

### 7.4 Recorded attribution observation (not resolved by T024)

`docs/engineering/xcom/t008/requirements-register.json` attributes `XCOM-SW-OBS-005` "Normalized records
for Argus consumers" (`FR-023`) to T024 and records it as `verified_by` `XCOM-T-OBS`
(`docs/engineering/xcom/t008/traceability-matrix.json`, `XCOM-L-0100/0101/0102`, all `planned`). The
accepted `tasks.md` T024 entry names the observation test matrix. T024 therefore implements the
**verification** obligation the register assigns: it realizes the normalized-record and
metadata/payload/ordering/saturation/validity/detach acceptance matrix over the accepted observation
boundary, and it records the payload-view allocation (`XCOM-SW-OBS-002`, unclaimed) honestly. The
`disabled-tap-performance` evidence name remains T036. The registers are **not** rewritten and no maturity
is promoted.

The historical SESN-era identifiers `XCOM-OBS-001…009` are retained as evidence only, and
`scripts/validate_xcom_observation.py` (legacy SESN tooling that binds `SESN_CANDIDATE_REVISION`) is
neither executed nor edited by this repository-owned workflow.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- `T024-LIM-01` — The matrix is prototype verification evidence only: passing it proves no runtime,
  telemetry, transport, timing, compatibility, parity, or production readiness, and it is not yet
  user-accepted (T041).
- `T024-LIM-02` — The matrix exercises the in-process observation hub, the owned loopback provider, and the
  public headers only; it executes no legacy binary, external peer, or out-of-process path (that is
  T030–T034).
- `T024-LIM-03` — The `payloadAccess: allow-listed` identity allow-list, a redaction profile, and any
  decoder/schema status beyond `PayloadSchemaState::undecoded` remain unimplemented and partial; T024 tests
  only the accepted `metadata_only`, `bounded_prefix`, and `redacted` behaviour.
- `T024-LIM-04` — `bounds.maxRateHz` rate limiting remains a declared-but-unrealized Profile bound; T024
  does not test a rate limit.
- `T024-LIM-05` — Deterministic concurrency is asserted by a bounded, repeated competing-reservation
  sub-check (≤ 4 threads, atomic flags, three runs), not a formal race proof; executed sanitizer evidence is
  T035's obligation.
- `T024-LIM-06` — The disabled-tap performance benchmark and its `SC-008` threshold remain T036; T024
  re-runs the benchmark under the gate but claims no `disabled-tap-performance` evidence.
- `T024-LIM-07` — Strict declaration-level Doxygen remains `DOX-GAP-01`, owned by T011/T037; T024 adds
  tagged documentation to its new cases but does not repair that unrelated coverage debt.
- `T024-LIM-08` — `scripts/validate_xcom_observation.py` is legacy SESN-era tooling in the T-OBS path set
  (it binds `SESN_CANDIDATE_REVISION`); the repository-owned workflow does not use it, and T024 neither
  depends on nor edits it.

### 8.2 Gaps with owning tasks

| Gap | Description | Owner | Disposition |
| --- | --- | --- | --- |
| `T024-GAP-01` | Payload identity allow-list, redaction profile, and any decoder/schema beyond `undecoded` | unclaimed in this slice; attribution recorded | allocated/partial; T024 implements no payload-view change |
| `T024-GAP-02` | Disabled-tap performance benchmark and its threshold | T036 | allocated |
| `T024-GAP-03` | Separate-process synthetic client and tool-gateway observation contract | T032/T033 | allocated |
| `T024-GAP-04` | Executed sanitizer/static-analysis/Doxygen evidence and the delivery/acceptance bundle | T035/T037/T038/T040/T041 | allocated |
| `T024-GAP-05` | Rate limiting (`bounds.maxRateHz`) | unclaimed in this slice | recorded; not implemented |

### 8.3 Open items

- `T024-OPEN-01` — Whether a later slice exposes the observation counters or records through the local
  tool-gateway contract is T030–T033's decision; T024 exercises the in-process API only.
- `T024-OPEN-02` — T024 continues the T-OBS hand-rolled `expect()`-style fixtures rather than introducing
  a separate GTest matrix area; this keeps the change additive with no build-file edit. A later task that
  unifies the observation suites must preserve every T024 case name or replace it with an equivalent
  stronger case.

## 9. Definition of done (requirements view)

T024 is complete for this slice when: (a) the five plan-stage work products exist under
`docs/engineering/xcom/t024/` and are mutually consistent; (b) every requirement in §3–§4 has ≥ 1 named
check in `verification-plan.md`; (c) the implementation stage realizes the observation acceptance matrix,
adds the nine matrix cases, marks the T024 checkbox, and records `implementation.md`; (d) the deterministic
gate and the named checks pass at the candidate revision with no existing case weakened; (e) the package
record is written; and (f) a separate DeepSeek internal review records a passing verdict with no findings.
This does **not** constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary check(s) |
| --- | --- |
| T024-STK-001 | CHK-02, CHK-04, CHK-25 |
| T024-STK-002 | CHK-05, CHK-08, CHK-09, CHK-11, CHK-13, CHK-14 |
| T024-STK-003 | CHK-16, CHK-17 |
| T024-STK-004 | CHK-18, CHK-21, CHK-22 |
| T024-STK-005 | CHK-02, CHK-20, CHK-24, NEG-01, NEG-29 |
| T024-SR-001 | CHK-02, CHK-04, CHK-20, NEG-01 |
| T024-SR-002 | CHK-03, CHK-04 |
| T024-SR-003 | CHK-05, NEG-02, NEG-03 |
| T024-SR-004 | CHK-05, CHK-15 |
| T024-SR-005 | CHK-06, NEG-04, NEG-05 |
| T024-SR-006 | CHK-06, NEG-06, NEG-07 |
| T024-SR-007 | CHK-08, NEG-08, NEG-09 |
| T024-SR-008 | CHK-09, NEG-10, NEG-11 |
| T024-SR-009 | CHK-09, NEG-12, NEG-13 |
| T024-SR-010 | CHK-10, NEG-14, NEG-15 |
| T024-SR-011 | CHK-11, NEG-16, NEG-17 |
| T024-SR-012 | CHK-11, CHK-12, NEG-18, NEG-19 |
| T024-SR-013 | CHK-13, NEG-20, NEG-21 |
| T024-SR-014 | CHK-14, NEG-22, NEG-23 |
| T024-SR-015 | CHK-16, NEG-24 |
| T024-SR-016 | CHK-17, NEG-25 |
| T024-SR-017 | CHK-18, NEG-26 |
| T024-SR-018 | CHK-18, CHK-19, NEG-26 |
| T024-SR-019 | CHK-21, NEG-27 |
| T024-SR-020 | CHK-22, NEG-28 |
| T024-SR-021 | CHK-02, CHK-20, NEG-01, NEG-29 |
| T024-SR-022 | CHK-23 |
| T024-SR-023 | CHK-24, NEG-29 |
| T024-SR-024 | CHK-25, NEG-29 |
