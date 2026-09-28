# T023 Requirements — Synthetic Sink, Failure/Disconnect Isolation, and Visible Counters

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T023 (capability 007, slice `T-OBS`) |
| Task title | Implement the synthetic sink and prove failure/disconnect isolation and visible counters |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `d455c70816eb784066740427a70df9235cd1287d` |
| Authorization | capability 007 accepted design and bounded implementation authorization (ACC005/ACC010/ACC011/ACC014/ACC015); ADR-0016; ADR-0018; ADR-0019; ADR-0020 |
| Owning slice | `T-OBS` (T007 ownership register) |
| Predecessor | T022 (bounded best-effort drop/coalesce, explicit lossless validation, applied validity effect; reviewed terminal package) |
| Producer dependencies | T011 admitted offline build envelope (read-only inputs); T012 subtree CMake/CTest contract; T013 immutable core value/item/diagnostic types; T015 provider composition with the optional non-owning `ObservationHub` seam; T019 bounded activation-plan decode; T021 declared tap policy, filter, immutable record, and exact tap handle; T022 bounded retention, applied validity effect, and realized validity status |
| Successor tasks | T024 (observation test matrix incl. safe detach), then T025–T034, T035–T041 |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}`; `docs/engineering/xcom/t008/requirements-register.{json,md}`; `docs/engineering/xcom/t008/traceability-matrix.{json,md}`; `docs/engineering/xcom/t009/architecture-model.{json,md}`; `docs/engineering/xcom/t010/unit-design.{json,md}` |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production
or test change and does not implement, accept, or integrate the candidate. The T023 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T023 — Implement the synthetic sink and prove failure/disconnect isolation and visible counters.

### 1.1 Authority statement

This document specifies only the bounded T023 slice. It elaborates the accepted software requirement
`XCOM-SW-OBS-004` "Observer isolation and safe detach" (refines `XCOM-SYS-FR-014`/`XCOM-SYS-SC-005`,
spec `FR-014`/`SC-005`), which `docs/engineering/xcom/t008/requirements-register.{json,md}` attributes to
T023, together with the synthetic-sink responsibility that
`docs/engineering/xcom/t010/unit-design.{json,md}` assigns to design unit `XCOM-DU-013` "Bounded observer
queue, counters, and synthetic sink" (owning tasks T022/T023, requirement links `XCOM-SW-OBS-003`,
`XCOM-SW-OBS-004`) and to architecture component `XCOM-CMP-011` "Synthetic sink and tools" (owning tasks
T023, T032, T033; `docs/engineering/xcom/t009/architecture-model.{json,md}`). It consumes the accepted
observation contract (`specs/007-xcom-core/contracts/observation.md`, design contract `XCOM-XLC-003`),
the accepted data model (`specs/007-xcom-core/data-model.md`: `ObservationTap` counters and the tap state
`declared → attached → active → degraded → detached`), and the accepted architecture component
`XCOM-CMP-008` "Observation boundary".

Both predecessor work products record the handoff this task now closes:
`T021-GAP-03` and `T022-GAP-02` — "Synthetic sink failure/disconnect isolation and its visible counters"
— are allocated to T023, and `T022-LIM`/`T021-LIM-02` note that "T023/T035 own observable counters and
evidence". T023 realizes that allocation.

It does **not** redesign the accepted architecture, change a functional requirement, success criterion,
ADR, schema, or contract, implement T024 (broad observation matrix) or any later task, add an admitted
dependency, weaken an accepted requirement or test, or accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, the
T007 ownership register, the T008 register/matrix, the T009 architecture model, the T010 unit design, the
constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is reported
rather than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T023)

1. **Realize the synthetic sink's visible consumer counters** under `src/xverse/xcom/` in namespace
   `xverse::xcom`, within the existing units
   `src/xverse/xcom/include/xverse/xcom/observation.hpp` and `src/xverse/xcom/src/observation.cpp`
   (design unit `XCOM-DU-013`, component `XCOM-CMP-011`). The `SyntheticObservationSink` gains one
   immutable, value-owned counter projection — `pulled`, `empty`, `disconnected`, `failed` — that makes
   the consumer's observed records and observed failures visible without a durable log, a callback, or a
   view into hub storage.
2. **Local disconnect isolation.** A disconnected sink's `pull()` returns the accepted stable
   `sink_disconnected` outcome, consumes no retained record, and never detaches, acknowledges, blocks,
   reorders, or mutates its tap or the normal route. `disconnect()` remains a local, non-owning action on
   the sink only.
3. **Failure isolation (observer removal / recreation).** A sink whose copied exact handle has become
   stale, foreign, or closed (for example because the observed tap was detached or its slot recreated)
   reports the accepted stable `invalid_tap_handle` outcome on `pull()`, counts it in `failed`, and leaves
   every tap, counter, generation, and the normal route unchanged.
4. **Blocking (non-pulling) isolation.** A connected sink that does not pull must not block, delay, or
   reorder submissions; the observed tap's queue stays within its declared bound with deterministic
   drop/coalesce counters visible through the exact-handle `ObservationSnapshot`, and the sink's own
   counters are unchanged until it pulls.
5. **Focused T023 cases** for the sink counter projection and the disconnect/failure/blocking isolation
   behavior, added inside the existing T-OBS-owned observation fixtures
   (`tests/xcom/observation/core/unit_tests.cpp` and one new case in
   `tests/xcom/observation/integration/integration_tests.cpp`). The broad metadata-only,
   controlled-payload, redaction/truncation, ordering, saturation, degraded-validity, and safe-detach
   matrix remains T024.
6. The T023 repository-owned work products and the T023 package record.

### 2.2 Explicit exclusions (must remain absent from the T023 candidate)

No change to `tests/xcom/observation/integration/disabled_tap_benchmark.cpp`; no new CTest target, test
name, label, or removed/renamed case; no `CMakeLists.txt` or `cmake/*.cmake` change; no `src/xverse_xdl/`,
`xdl/`, `proto/`, or `src/xverse/xcom/contracts/` change; no `activation_plan.{hpp,cpp}`,
`provider.{hpp,cpp}`, `loopback_provider.{hpp,cpp}`, `endpoint_route_lifecycle.{hpp,cpp}`, `contract.hpp`,
`item.hpp`, `value.hpp`, `result.hpp`, `diagnostic.hpp`, `validation_session.{hpp,cpp}`, or
`stimulation_journal.{hpp,cpp}` change; **no change to the accepted retention, validity, payload, record,
filter, declaration, or handle behavior added by T021/T022**; no new `ObservationOutcome`,
`ObservationOverflowPolicy`, `ObservationValidityEffect`, or `ObservationValidityState` value; no payload
identity allow-list, redaction profile, or decoder/schema interpretation beyond the accepted
`PayloadSchemaState::undecoded`; no temporization, rate limit, retry, quota, persistence, replay,
Argus/dashboard/storage/export, OpenTelemetry, gateway, stimulation, or legacy behavior; no new admitted
dependency; no network, TCP listener, DNS, TLS, filesystem, process, dynamic-load, ambient/secret, or
legacy-repository access; no rewrite or weakening of an accepted ADR, requirement, contract, test, REF-002
disposition, or another task's ownership path; no promotion of any REF-002 or capability requirement; no
acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T023 |
| --- | --- | --- |
| Broad metadata-only zero-payload, controlled-payload, redaction/truncation, ordering, saturation, degraded-validity, safe-detach matrix; disabled-tap benchmark | T024/T036 | allocated; T023 adds only focused sink-counter/isolation cases |
| Payload identity allow-list (`payloadAccess: allow-listed` + `allowList`), redaction profile, decoder/schema status beyond `undecoded` | unclaimed behaviour | recorded; stays unimplemented/partial (§7) |
| `bounds.maxRateHz` rate limiting | not T023 | not implemented; remains a declared-but-unrealized Profile bound |
| Separate-process synthetic client and tool gateway observation path | T032/T033 | allocated; the in-process sink is the only consumer realized here |
| Executed sanitizer/static-analysis/Doxygen evidence; integration, validation, delivery bundle | T035–T040 | allocated |
| Independent review and user acceptance | T039/T041 | allocated |

## 3. Stakeholder requirements (`T023-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T023-STK-001**: Before the observation boundary is accepted, the program **shall** have one
  repository-owned, bounded, domain-neutral C++20 synthetic observation sink — with a visible consumer
  counter projection — physically under `src/xverse/xcom/`, that compiles with the T011-admitted toolchain
  under the T012 warning-as-error contract.
- **T023-STK-002**: The synthetic sink **shall** fail closed and stay bounded: a local disconnect, a
  stale/foreign/closed handle, or a non-pulling consumer never blocks, delays, reorders, emits, detaches,
  or mutates the normal route, and no consumer counter, tap counter, or outcome is inferred, defaulted, or
  strengthened.
- **T023-STK-003**: Every changed sink type **shall** keep its ownership, lifetime, thread-safety, and
  failure contract explicit, **shall** keep immutable value semantics that are safe to copy and to read
  concurrently, and **shall** treat the copied exact handle as the only (read-only) authority to observe
  its tap.
- **T023-STK-004**: The synthetic sink **shall** be offline and domain-neutral: normal use performs no
  network discovery, ambient configuration or secret lookup, filesystem access, process execution, or
  legacy-repository access, contains no domain-specific primitive, adds no admitted dependency, and claims
  no export, dashboard, storage, or presentation behavior.
- **T023-STK-005**: T023 **shall** preserve accepted intent: the delivered change is confined to the
  T023-owned observation paths, the T023 work products, and (implementation stage only) the capability task
  ledger, and it **shall** neither weaken an accepted requirement or test nor implement another task.

## 4. Software/engineering requirements (`T023-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Implemented" means the repository-owned source and its deterministic checks exist and pass; it is
not a runtime or production claim.

### 4.1 Visible consumer counters

- **T023-SR-001 [ubiquitous]**: The `SyntheticObservationSink` **shall** expose an immutable, value-owned
  consumer counter projection with exactly the fields `pulled`, `empty`, `disconnected`, and `failed`,
  monotonic over the sink's lifetime, updated only by the sink's own calls, and derived only from the
  actual pull outcomes; it **shall** expose no view into hub storage and **shall not** replace the tap's
  own loss counters.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-013, FR-014, SC-004, SC-005; `XCOM-DU-013`; `XCOM-CMP-011`;
    contracts/observation.md "every dropped or coalesced item is reflected in counters".
  - Verification intent: the visible-counter case; CHK-06, NEG-01, NEG-02.
- **T023-SR-002 [ubiquitous]**: A successful `pull()` **shall** increment `pulled` by exactly one and
  return a value-owned record; a `pull()` that finds no retained record **shall** increment `empty` by
  exactly one and return `no_record`; no other field **shall** change on either outcome.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-013, SC-004; `XCOM-DU-013`.
  - Verification intent: the counter-accounting identity `pulled + empty + disconnected + failed == pull
    attempts`; CHK-06, NEG-01.

### 4.2 Disconnect and failure isolation

- **T023-SR-003 [event-driven]**: When the sink is locally disconnected, `pull()` **shall** return the
  accepted stable `sink_disconnected` outcome, increment `disconnected` by exactly one, consume no
  retained record, and leave every tap, tap counter, generation, and the normal route unchanged; the
  disconnect **shall** be local to that sink only.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-014, SC-005; `XCOM-DU-013`; contracts/observation.md
    "Best-effort observer failure, delay, or disconnection cannot block or reorder the normal route".
  - Verification intent: the disconnect-isolation case; CHK-07, NEG-03, NEG-05.
- **T023-SR-004 [event-driven]**: When the sink's copied exact handle has become stale, foreign, or closed
  (observer removal or slot recreation), `pull()` **shall** return the accepted stable `invalid_tap_handle`
  outcome, increment `failed` by exactly one, and leave the observed tap, every unrelated tap, and the
  normal route unchanged.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-014, SC-005; `XCOM-DU-013`; data-model tap state
    `detached`.
  - Verification intent: the failure-isolation case at the unit and route boundary; CHK-08, NEG-04, NEG-05.
- **T023-SR-005 [event-driven]**: When `connect()` is called on a valid exact current handle it **shall**
  re-enable pulling and report `accepted`; on an invalid, foreign, stale, or closed handle it **shall**
  report `invalid_tap_handle`, leave the sink disabled, and mutate no tap.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-014, SC-005; `XCOM-DU-013`.
  - Verification intent: the reconnect/refuse case; CHK-07, NEG-03, NEG-04.

### 4.3 Blocking isolation and route neutrality

- **T023-SR-006 [event-driven]**: While a connected sink does not pull, normal submissions **shall** not
  block, delay, reorder, or change their outcome; the observed tap's queue **shall** remain within its
  declared capacity, with deterministic drop/coalesce counters visible through the exact-handle
  `ObservationSnapshot`, and the sink's counters **shall** be unchanged until the sink pulls.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-013, FR-014, SC-004, SC-005; `XCOM-DU-013`.
  - Verification intent: the blocking/non-pulling isolation case; CHK-09, NEG-06, NEG-07.
- **T023-SR-007 [ubiquitous]**: The synthetic sink **shall not** detach, acknowledge, reserve, commit,
  cancel, or otherwise mutate any tap or route; it **shall** read only through `poll` and the const
  authentication used by `connect`, and observe the exact handle authority it was constructed with.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-009, FR-014; `XCOM-DU-013`.
  - Verification intent: the read-only-authority case and source inspection; CHK-10, NEG-05, NEG-08.

### 4.4 Concurrency, bounds, and resource behavior

- **T023-SR-008 [ubiquitous]**: Every sink call **shall** execute through the hub's single serialization
  point for its tap; counters **shall** be updated on the calling thread only; a returned record **shall**
  be a value copy; no consumer callback **shall** exist or be invoked under an X-COM lock; and the new
  counter accessor **shall** be `noexcept` and introduce no shared mutable state.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-014; `XCOM-DU-013`; `XCOM-UDI-09`.
  - Verification intent: the preserved concurrent pull/publication case plus the no-callback source scan;
    CHK-11, CHK-12, NEG-09.
- **T023-SR-009 [ubiquitous]**: Every sink resource **shall** remain finite and preallocated: a non-owning
  hub pointer, one copied exact handle, one local connected flag, and four fixed 64-bit counters; no
  dynamic allocation, unbounded buffer, timer, retry, rate, quota, or wall-clock dependency **shall** exist
  on any T023 path.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-007, FR-013, FR-014; `XCOM-DU-013`.
  - Verification intent: the constants/member inspection and the fixed-bound case; CHK-13, CHK-18.

### 4.5 Safety, documentation, and governance

- **T023-SR-010 [ubiquitous]**: The T023 candidate **shall** perform no network, socket, resolver, TLS,
  ambient, secret, filesystem, process, dynamic-load, or legacy access, **shall** add no admitted
  dependency beyond the C++ standard library, and **shall** contain no domain-specific or export/dashboard/
  storage/query primitive.
  - Refines: `XCOM-SW-CORE-007` (domain-neutral local runtime half); anchors FR-023, FR-026, FR-028;
    ADR-0019.
  - Verification intent: the forbidden-API scan plus the successful offline build; CHK-17, NEG-10.
- **T023-SR-011 [ubiquitous]**: Committed source, tests, and work products **shall** contain no credential,
  private address, unrestricted or real payload, proprietary source excerpt, environment-specific absolute
  host path, or sensitive deployment value.
  - Refines: Constitution X; anchors FR-027; `XCOM-SW-INTG` public-safe evidence rule.
  - Verification intent: the public-safety scan; CHK-18, NEG-11.
- **T023-SR-012 [ubiquitous]**: Every new or changed public C/C++ declaration **shall** carry useful Doxygen
  documentation including its ownership, lifetime, thread-safety, and failure contract, in the `xcom_obs`
  group, without weakening the admitted repository documentation configuration.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-029; `XCOM-DU-013` Doxygen obligation; Constitution X.
  - Verification intent: declaration inspection and the existing documentation validator; CHK-19.
- **T023-SR-013 [ubiquitous]**: The T023 candidate **shall** be additive: no existing test case, target,
  label, command, threshold, expected result, requirement, ADR, contract, schema, register, or another
  task's ownership path is removed, renamed, reordered, or weakened; the accepted T021/T022 declaration,
  retention, validity, payload, record, and handle behavior and the accepted `ObservationOutcome`,
  `ObservationOverflowPolicy`, `ObservationValidityEffect`, and `ObservationValidityState` vocabularies
  **shall** be preserved unchanged; and no later task (T024+) is implemented.
  - Refines: ADR-0018, ADR-0020; T007 global prohibitions; anchors FR-030; Constitution VII, IX.
  - Verification intent: the changed-path and test-name comparison plus the preserved-behavior regression;
    CHK-02, CHK-14, CHK-20, NEG-12, NEG-13.
- **T023-SR-014 [ubiquitous]**: The T023 candidate **shall** satisfy the deterministic Fabro gate for
  implementation tasks: the six named work products exist, at least one `src/xverse/xcom/**` path changes,
  `cmake` configure, build, discovery, and the full `ctest` suite pass, and `git diff --check` is clean;
  the T023 checkbox is marked complete **only** in the implementation stage.
  - Refines: ADR-0020; anchors FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T023 <baseline>`; `git diff --check`; CHK-21.
- **T023-SR-015 [ubiquitous]**: T023 **shall** reconcile with the T007 ownership register, the T008
  requirement register/matrix, the T009 architecture model, and the T010 unit design without rewriting or
  weakening them; **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list; and
  **shall** record honestly (a) that the T008 register attributes `XCOM-SW-OBS-004` to T023 while T010
  links `XCOM-DU-013` to `XCOM-SW-OBS-003`/`-004` and `XCOM-CMP-011` to `XCOM-SW-OBS-005`, (b) the
  T021-GAP-03/T022-GAP-02 handoff this task closes, (c) the historical SESN-era `XCOM-OBS-001…009`
  evidence identifiers, and (d) that the SESN-era validator `scripts/validate_xcom_observation.py` is not
  used by the repository-owned workflow.
  - Refines: ADR-0020; anchors FR-030, FR-035; Constitution VII, IX.
  - Verification intent: the register validators plus the recorded-attribution inspection; CHK-20, CHK-22.

### 4.6 Outcome-vocabulary stability

- **T023-SR-016 [ubiquitous]**: T023 **shall not** add, rename, reorder, or narrow any `ObservationOutcome`
  value; disconnect is reported with the accepted `sink_disconnected`, an empty pull with `no_record`, and
  a stale/foreign/closed handle with `invalid_tap_handle`.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-014; `XCOM-DU-013`; T021/T022 outcome vocabulary.
  - Verification intent: the outcome-vocabulary inspection plus the isolation cases; CHK-05, CHK-14.

## 5. Requirement-to-accepted-anchor traceability

| T023 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T023-STK-001 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-014 | FR-014 | IX, X |
| T023-STK-002 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-014 | FR-014, SC-005 | IX |
| T023-STK-003 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-009/014 | FR-009, FR-014 | IX |
| T023-STK-004 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-023/026/028 | FR-023, FR-026, FR-028 | II, VII, IX |
| T023-STK-005 | Constitution VII/IX; ADR-0018/0020 | – | FR-030 | VII, IX, X |
| T023-SR-001 | `XCOM-SW-OBS-004`, `XCOM-SW-OBS-005` | XCOM-SYS-FR-013/014 | FR-013, FR-014, SC-004, SC-005 | IX |
| T023-SR-002 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-013/014 | FR-013, FR-014, SC-004 | IX |
| T023-SR-003 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-014 | FR-014, SC-005 | IX |
| T023-SR-004 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-014 | FR-014, SC-005 | IX |
| T023-SR-005 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-014 | FR-014, SC-005 | IX |
| T023-SR-006 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-013/014 | FR-013, FR-014, SC-004, SC-005 | IX |
| T023-SR-007 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-009/014 | FR-009, FR-014 | IX |
| T023-SR-008 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-014 | FR-014 | IX |
| T023-SR-009 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-007/014 | FR-007, FR-014 | IX |
| T023-SR-010 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-023/026/028 | FR-023, FR-026, FR-028 | II, VII |
| T023-SR-011 | public-safe evidence rule | XCOM-SYS-FR-027 | FR-027 | X |
| T023-SR-012 | `XCOM-SW-OBS-004` Doxygen | XCOM-SYS-FR-029 | FR-029 | X |
| T023-SR-013 | Constitution; ADR-0018/0020 | XCOM-SYS-FR-030 | FR-030 | VII, IX |
| T023-SR-014 | ADR-0020 | – | FR-030 | X |
| T023-SR-015 | Constitution; ADR-0020 | XCOM-SYS-FR-035 | FR-030, FR-035 | VII, IX |
| T023-SR-016 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-014 | FR-014 | III, IX |

`XCOM-SW-OBS-001`–`-005` are the accepted capability-007 software requirements
(`docs/engineering/xcom/t008/requirements-register.{json,md}`). They are accepted text; T023 refines and
consumes them and does not rewrite them. The register attributes `XCOM-SW-OBS-004` (FR-014/SC-005) to T023;
T023 implements the synthetic-sink counter and isolation half of that attribution and records the payload-
view allocation (`XCOM-SW-OBS-002`, unclaimed) honestly. No register row is changed and no maturity is
promoted.

## 6. REF-002 disposition

T023 owns no REF-002 SADS ID and promotes none. It provides part of the bounded observation contribution
recorded against the allocated ID `XVE-SYS-0149` (observation records, metrics, counters, and tool
streams: the visible synthetic-sink consumer counters make observed loss/failure observable) and, through
the unchanged pull path, `XVE-SYS-0142` (provider-neutral records). It touches `XVE-SYS-0140` (interaction
families retained) and `XVE-SYS-0151` (Argus analytics, storage, and presentation are **not** implemented:
the sink is an in-process counter projection only) only to preserve their existing dispositions. The
capability `ref002.disposition` stays `unchanged` with an empty `promoted` list (T023-SR-015). No allocated,
deferred, architectural-target, or superseded SADS requirement is reported as implemented, and no
`XVE-SYS-*` ID is promoted.

## 7. Affected paths

### 7.1 Paths the T023 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/observation.hpp` | edit | adds the immutable `SyntheticSinkCounters` projection, the sink's read-only `counters()` accessor, the four fixed counter members, and the Doxygen/traceability updates; no existing declaration or enumerator removed, renamed, or narrowed |
| `src/xverse/xcom/src/observation.cpp` | edit | `SyntheticObservationSink::pull`/`connect` maintain the visible counters on the actual pull outcomes; every accepted poll, handle, retention, validity, coalescing, payload, and counter rule is otherwise byte-identical |
| `tests/xcom/observation/core/unit_tests.cpp` | edit | adds the focused T023 sink-counter and disconnect/failure/blocking isolation cases and registers them in `main()`; every existing assertion is preserved |
| `tests/xcom/observation/integration/integration_tests.cpp` | edit | adds one focused route-level sink failure/disconnect isolation case with visible counters; every existing case and assertion is preserved |
| `docs/engineering/xcom/t023/requirements.md` | add | this document |
| `docs/engineering/xcom/t023/architecture.md` | add | boundary, components, data flow, interfaces (plan stage) |
| `docs/engineering/xcom/t023/detailed-design.md` | add | counter/isolation rules, failure semantics, bounds (plan stage) |
| `docs/engineering/xcom/t023/unit-specifications.md` | add | units, ownership/lifetime/thread-safety/bounds, planned tests (plan stage) |
| `docs/engineering/xcom/t023/verification-plan.md` | add | named checks, negative cases, commands, evidence (plan stage) |
| `docs/engineering/xcom/t023/implementation.md` | add (implementation stage) | realized change and candidate-bound local evidence |
| `docs/engineering/xcom/t023/internal-review.json` | add (review stage) | separate read-only DeepSeek internal review |
| `specs/007-xcom-core/tasks.md` | edit T023 checkbox (implementation stage only) | capability task ledger; `- [ ] T023` → `- [X] T023` |
| `reports/xcom-queue/t023-package.json` | add (package stage) | exact-candidate package record |

No build file change: the existing `xverse::xcom_observation` library target already compiles
`src/observation.cpp`, the existing `xcom_observation_unit` executable already compiles
`tests/xcom/observation/core/unit_tests.cpp`, and the existing `xcom_observation_integration` executable
already compiles `tests/xcom/observation/integration/integration_tests.cpp`, so the new cases are
discovered without adding or renaming a target, test, or label.

### 7.2 T023-owned observation paths consumed and re-verified unchanged

| Path | Owner | Role for T023 |
| --- | --- | --- |
| `tests/xcom/observation/integration/test_support.hpp` | T-OBS (T023/T024) | re-run unchanged; the shared `make_tap_spec` helper declares the default `none` effect and a valid observation point, so no edit is required |
| `tests/xcom/observation/integration/disabled_tap_benchmark.cpp` | T-OBS (T036 owns execution) | re-run unchanged, not edited |
| `scripts/validate_xcom_observation.py` | T-OBS (legacy SESN evidence) | not executed, not edited, and not used as T023 evidence |

### 7.3 Consumed, read-only foundation (not changed by T023)

| Path | Owner | Role for T023 |
| --- | --- | --- |
| `src/xverse/xcom/CMakeLists.txt`, `cmake/*.cmake`, `CMakeLists.txt` | shared (serialized) | T012 subtree build contract that compiles `observation.cpp` and the observation fixtures; T023 changes none |
| `src/xverse/xcom/include/xverse/xcom/{value,contract,item,diagnostic,result,core_types}.hpp` | T013 (T-CORE) | validated `Identity`, `SemanticVersion`, `CommunicationItem`, diagnostics; consumed read-only |
| `src/xverse/xcom/include/xverse/xcom/{provider,loopback_provider,endpoint_route_lifecycle}.hpp` | T014/T015 (T-CORE) | provider composition, loopback provider, and lifecycle; consumed read-only by the integration case |
| `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp`, `.../observation.hpp`/`.cpp` T021/T022 regions | T-XDL/T021/T022 | decoded plan and the accepted retention/validity/declaration behavior; re-verified unchanged |
| `docs/engineering/xcom/t021/*`, `t022/*` | T021/T022 | predecessor work products; T023 records the §7.4 handoff and rewrites nothing |
| `docs/xcom/observation-boundary.md`, `docs/xcom/observation-boundary-traceability.json` | legacy SESN evidence bundle | historical evidence for an exact superseded revision only; neither current acceptance evidence nor rewritten |

### 7.4 Recorded attribution observation (not resolved by T023)

`docs/engineering/xcom/t008/requirements-register.json` attributes `XCOM-SW-OBS-004` "Observer isolation
and safe detach" to T023. `docs/engineering/xcom/t010/unit-design.json` links `XCOM-DU-013` (owning tasks
T022/T023) to `XCOM-SW-OBS-003`/`-004` and `XCOM-CMP-011` (owning tasks T023/T032/T033) to
`XCOM-SW-OBS-005`/`XCOM-SYS-FR-023`. The accepted `tasks.md` assigns the synthetic sink, failure/disconnect
isolation, and visible counters to T023. T023 therefore implements the sink-counter/isolation half of
`XCOM-SW-OBS-004` and the synthetic-sink responsibility, preserves the accepted T021/T022 declaration,
retention, and validity behavior unchanged, and rewrites nothing (T023-SR-015). The payload-view
`payloadAccess: allow-listed` identity allow-list and any decoder/schema status beyond `undecoded` remain
unimplemented and partial; they stay recorded as allocated/unclaimed rather than silently dropped.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- `T023-LIM-01` — The synthetic sink remains a bounded prototype: it makes no runtime, telemetry,
  transport, timing, compatibility, parity, or production-readiness claim, and it is not yet user-accepted
  (T041).
- `T023-LIM-02` — The consumer counters are an in-process, per-sink projection: they are not a durable log
  and are discarded with the sink; durable experiment evidence and presentation belong to T035/Argus and
  are not implemented here.
- `T023-LIM-03` — The sink counters describe the consumer's own pull outcomes only; the tap's deterministic
  loss counters remain on `ObservationHub::snapshot` and are not duplicated by the sink.
- `T023-LIM-04` — Observer failure is modeled as the accepted stale/foreign/closed exact-handle outcome
  (`invalid_tap_handle`); no new failure-injection API or `ObservationOutcome` value is introduced.
- `T023-LIM-05` — The separate-process synthetic client and the external tool-gateway observation stream
  remain T032/T033; T023 realizes only the in-process sink.
- `T023-LIM-06` — `scripts/validate_xcom_observation.py` is legacy SESN-era tooling in the T-OBS path set
  (it binds `SESN_CANDIDATE_REVISION`); the repository-owned workflow does not use it, and T023 neither
  depends on nor edits it.
- `T023-LIM-07` — The sink retains a non-owning hub reference, so the referenced hub must outlive the sink;
  this is the accepted precondition and is not enforced at runtime.

### 8.2 Gaps with owning tasks

| Gap | Description | Owner | Disposition |
| --- | --- | --- | --- |
| `T023-GAP-01` | Broad metadata-only, controlled-payload, redaction/truncation, ordering, saturation, degraded-validity, safe-detach matrix | T024 | allocated; T023 adds only focused sink-counter/isolation cases |
| `T023-GAP-02` | Disabled-tap performance benchmark and its threshold | T036 | allocated |
| `T023-GAP-03` | Separate-process synthetic client and tool-gateway observation contract | T032/T033 | allocated |
| `T023-GAP-04` | Payload identity allow-list, redaction profile, and any decoder/schema beyond `undecoded` | unclaimed in this slice; T023 attribution recorded | allocated/partial; T023 implements no payload-view change |
| `T023-GAP-05` | Executed sanitizer/static-analysis/Doxygen evidence and the delivery/acceptance bundle | T035/T037/T038/T040/T041 | allocated |
| `T023-GAP-06` | The T008/T010/T008-matrix attribution nuance of §7.4 | T008/T010 (registers); T023 (source) | allocated; T023 records and promotes nothing |

### 8.3 Open items

- `T023-OPEN-01` — Whether a later slice (T030–T032) exposes the synthetic-sink consumer counters through
  the local tool-gateway observation contract or only through the in-process API is that slice's decision;
  T023 exposes them in-process as an immutable value projection.
- `T023-OPEN-02` — Whether `SyntheticObservationSink` should also surface the observed tap's
  `ObservationSnapshot` through a convenience accessor (in addition to the consumer counters) is left to
  T024/T032; T023 keeps the sink a pure pull consumer and does not duplicate the hub counter API.

## 9. Definition of done (requirements view)

T023 is complete for this slice when: (a) the five plan-stage work products exist under
`docs/engineering/xcom/t023/` and are mutually consistent; (b) every requirement in §3–§4 has ≥ 1 named
check in `verification-plan.md`; (c) the implementation stage realizes the visible consumer counters and
the disconnect/failure/blocking isolation behavior, adds the focused cases, marks the T023 checkbox, and
records `implementation.md`; (d) the deterministic gate and the named checks pass at the candidate revision
with no existing case weakened; (e) the package record is written; and (f) a separate DeepSeek internal
review records a passing verdict with no findings. This does **not** constitute user acceptance, which
remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary check(s) |
| --- | --- |
| T023-STK-001 | CHK-02, CHK-03, CHK-21 |
| T023-STK-002 | CHK-06, CHK-07, CHK-08, CHK-09, NEG-01…NEG-07 |
| T023-STK-003 | CHK-10, CHK-11, CHK-12 |
| T023-STK-004 | CHK-17, CHK-18 |
| T023-STK-005 | CHK-02, CHK-14, CHK-20, NEG-12, NEG-13 |
| T023-SR-001 | CHK-06, NEG-01, NEG-02 |
| T023-SR-002 | CHK-06, NEG-01 |
| T023-SR-003 | CHK-07, NEG-03, NEG-05 |
| T023-SR-004 | CHK-08, NEG-04, NEG-05 |
| T023-SR-005 | CHK-07, NEG-03, NEG-04 |
| T023-SR-006 | CHK-09, NEG-06, NEG-07 |
| T023-SR-007 | CHK-10, NEG-05, NEG-08 |
| T023-SR-008 | CHK-11, CHK-12, NEG-09 |
| T023-SR-009 | CHK-13, CHK-18 |
| T023-SR-010 | CHK-17, NEG-10 |
| T023-SR-011 | CHK-18, NEG-11 |
| T023-SR-012 | CHK-19 |
| T023-SR-013 | CHK-02, CHK-14, CHK-20, NEG-12, NEG-13 |
| T023-SR-014 | CHK-21 |
| T023-SR-015 | CHK-20, CHK-22 |
| T023-SR-016 | CHK-05, CHK-14 |
