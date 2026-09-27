# T021 Requirements — Immutable Observation Records, Filters, Payload Policy, and Tap Handles

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T021 (capability 007, slice `T-OBS`) |
| Task title | Implement immutable observation records, filters, payload policy, and tap handles |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda` |
| Authorization | capability 007 accepted design and bounded implementation authorization (ACC005/ACC010/ACC011/ACC014/ACC015); ADR-0016; ADR-0018; ADR-0019; ADR-0020 |
| Owning slice | `T-OBS` (T007 ownership register) |
| Predecessor | T016 (consolidated core unit/negative matrix; reviewed terminal package) |
| Producer dependencies | T011 admitted offline build envelope (read-only inputs); T012 subtree CMake/CTest contract; T013 immutable core value/item/diagnostic types; T015 provider composition with the optional non-owning `ObservationHub` seam; T019 bounded activation-plan decode (`ObservationPoint`) |
| Successor tasks | T022 (bounded drop/coalesce and lossless-validation modes), T023 (synthetic sink and isolation), T024 (observation test matrix), then T025–T034, T035–T041 |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}`; `docs/engineering/xcom/t008/requirements-register.{json,md}`; `docs/engineering/xcom/t008/traceability-matrix.{json,md}`; `docs/engineering/xcom/t009/architecture-model.{json,md}`; `docs/engineering/xcom/t010/unit-design.{json,md}` |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production
or test change and does not implement, accept, or integrate the candidate. The T021 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T021 — Implement immutable observation records, filters, payload policy, and tap handles.

### 1.1 Authority statement

This document specifies only the bounded T021 slice. It elaborates the accepted software requirement
`XCOM-SW-OBS-001` "Versioned filterable observation boundary" (refines `XCOM-SYS-FR-011`, spec `FR-011`),
which `docs/engineering/xcom/t008/requirements-register.{json,md}` attributes to T021, together with the
observation-record and payload-policy responsibilities that
`docs/engineering/xcom/t010/unit-design.{json,md}` assigns to design unit `XCOM-DU-012` "Observation record
and payload-view policy" (owning task T021, requirement links `XCOM-SW-OBS-001`, `-002`, `-005`). It also
consumes the accepted observation contract (`specs/007-xcom-core/contracts/observation.md`, design contract
`XCOM-XLC-003`), the accepted data model (`specs/007-xcom-core/data-model.md`: `ObservationTap`,
`ObservationRecord`), and the accepted architecture component `XCOM-CMP-008` "Observation boundary".

It does **not** redesign the accepted architecture, change a functional requirement, success criterion,
ADR, schema, or contract, implement T022–T024 or any later task, add an admitted dependency, weaken an
accepted requirement or test, or accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, the
T007 ownership register, the T008 register/matrix, the T009 architecture model, the T010 unit design, the
constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is reported
rather than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T021)

1. **Realize the declared, versioned observation boundary for the value-and-authority layer** under
   `src/xverse/xcom/` in namespace `xverse::xcom`, within the existing units
   `src/xverse/xcom/include/xverse/xcom/observation.hpp` and `src/xverse/xcom/src/observation.cpp`
   (design unit `XCOM-DU-012`).
2. **Declared observation-point binding.** The accepted contract states that "an observation tap attaches
   to a declared logical route point using an exact filter and payload policy", and the accepted data model
   gives `ObservationTap` a "tap ID, route point, and filter". The baseline tap policy carries a contract
   version, a filter, a payload mode/bound, a record capacity, and an overflow policy, but **no declared
   tap identity and no declared route-point accessor**, so a tap cannot be correlated with the declared
   observation point it realizes. T021 adds the declared observation-point identity as a validated,
   mandatory field of the immutable tap policy and exposes the declared route point from the filter
   (single source of truth).
3. **Filter declaration accessors.** The declared logical constraint set (contract, interface, endpoint,
   route, provider, interaction kind, origin) is currently write-only input: only `matches()` can be
   called and the declaration cannot be read back. T021 adds read-only accessors for the declared
   constraints without changing any matching rule.
4. **Declared validity effect.** The accepted `io.xverse.xcom` `observation-policy` form declares
   `validityEffect ∈ {none, degrade-on-loss, invalidate-on-loss}` and the accepted data model gives
   `ObservationTap` a "validity effect". T021 declares that vocabulary on the immutable tap policy
   (vocabulary and stable external text only). **No loss, degradation, or invalidation behaviour is
   implemented here**; applying the declared effect to retention is T022.
5. **Immutable record self-description.** The accepted data model states that an `ObservationRecord`
   "carries the item identity and outcome plus observation time, **tap identity**, payload-view status,
   and **queue counters**". The baseline record carries the item projection, the observation time/clock
   domain, the provider outcome, and the payload-view state, but not the producing tap identity and not
   the queue counters. T021 adds both as immutable, value-owned record fields.
6. **Tap-handle authority preserved.** The opaque, generation-bound `ObservationTapHandle` remains the
   only mutation/observation authority (`XCOM-INV-02`: "No endpoint, route, tap, or validation session is
   mutable without its exact issued handle"). T021 re-verifies the handle, authentication, capacity, and
   lifecycle semantics unchanged and reports the declared identity through the policy, snapshot, and
   record — **not** through the handle.
7. **Focused T021 cases** for the new declaration, rejection, record, and error cases, added inside the
   existing T-OBS-owned observation executables (`tests/xcom/observation/core/unit_tests.cpp`) with the
   minimal declaration update needed by the existing T-OBS fixtures
   (`tests/xcom/observation/integration/test_support.hpp`, `integration_tests.cpp`). The broad saturation,
   ordering, degraded-validity, safe-detach, and benchmark matrix remains T024/T036.
8. The T021 repository-owned work products and the T021 package record.

### 2.2 Explicit exclusions (must remain absent from the T021 candidate)

No change to `tests/xcom/observation/integration/disabled_tap_benchmark.cpp`; no new CTest target, test
name, label, or removed/renamed case; no `CMakeLists.txt` or `cmake/*.cmake` change; no
`src/xverse_xdl/`, `xdl/`, `proto/`, or `src/xverse/xcom/contracts/` change; no
`activation_plan.{hpp,cpp}`, `provider.{hpp,cpp}`, `loopback_provider.{hpp,cpp}`,
`endpoint_route_lifecycle.{hpp,cpp}`, `contract.hpp`, `item.hpp`, `value.hpp`, `result.hpp`,
`diagnostic.hpp`, `validation_session.{hpp,cpp}`, or `stimulation_journal.{hpp,cpp}` change; no
drop/coalesce/lossless saturation behaviour change; no synthetic sink or isolation behaviour change
(T023); no payload identity allow-list, redaction-profile, decode, Argus/dashboard/storage/export,
OpenTelemetry, gateway, stimulation, or legacy behaviour; no new admitted dependency; no network, TCP
listener, DNS, TLS, filesystem, process, dynamic-load, ambient/secret, or legacy-repository access; no
rewrite or weakening of an accepted ADR, requirement, contract, test, REF-002 disposition, or another
task's ownership path; no promotion of any REF-002 or capability requirement; no acceptance or
integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T021 |
| --- | --- | --- |
| Bounded best-effort drop/coalesce behaviour and explicit lossless-validation reservation semantics | T022 | allocated; T021 declares the policy fields and leaves every retention rule byte-identical |
| Application of the declared validity effect (`degrade-on-loss` vs `invalidate-on-loss`) to experiment validity | T022 | allocated; T021 declares the vocabulary and reports the declaration |
| Payload identity allow-list (`payloadAccess: allow-listed` + `allowList`) and any decoder/schema status beyond `undecoded` | T022 | allocated; T021 keeps the explicit-mode/bound payload policy unchanged and records `PayloadSchemaState::undecoded` |
| Synthetic sink, failure/disconnect isolation, visible counters | T023 | allocated; the existing `SyntheticObservationSink` is re-verified unchanged |
| Metadata-only zero-payload, controlled payload, redaction/truncation, ordering, saturation, degraded validity, safe-detach matrix; disabled-tap benchmark | T024/T036 | allocated; T021 adds only focused declaration/record cases |
| XDL Profile binding of a declared `observationPoints[]` entry into a tap policy | T017–T020 consumed read-only; binding of the decoded `ObservationPoint` into attachment is not part of T021 | allocated downstream |
| Executed sanitizer/static-analysis/Doxygen evidence; integration, validation, delivery bundle | T035–T040 | allocated |
| Independent review and user acceptance | T039/T041 | allocated |

## 3. Stakeholder requirements (`T021-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T021-STK-001**: Before the observation boundary is accepted, the program **shall** have one
  repository-owned, bounded, domain-neutral C++20 declared observation value-and-authority layer —
  tap policy, filter declaration, immutable record, and exact tap handle — physically under
  `src/xverse/xcom/`, that compiles with the T011-admitted toolchain under the T012 warning-as-error
  contract.
- **T021-STK-002**: The observation declaration **shall** fail closed: no unvalidated or partial tap
  policy, filter, record, or handle is exposed, every resource is finite and explicit, metadata-only is
  the default and exposes zero payload bytes, and no payload view, identity, or counter is inferred,
  substituted, or strengthened.
- **T021-STK-003**: Every observation type **shall** make its ownership, lifetime, thread-safety, and
  failure contract explicit, **shall** expose immutable value semantics that are safe to copy and to read
  concurrently, and **shall** treat the exact issued handle as the only authority to observe or mutate a
  tap.
- **T021-STK-004**: The observation declaration **shall** be offline and domain-neutral: normal use
  performs no network discovery, ambient configuration or secret lookup, filesystem access, process
  execution, or legacy-repository access, contains no domain-specific primitive, adds no admitted
  dependency, and claims no export, dashboard, storage, or presentation behaviour.
- **T021-STK-005**: T021 **shall** preserve accepted intent: the delivered change is confined to the
  T021-owned observation paths, the T021 work products, and (implementation stage only) the capability
  task ledger, and it **shall** neither weaken an accepted requirement or test nor implement another task.

## 4. Software/engineering requirements (`T021-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Implemented" means the repository-owned source and its deterministic checks exist and pass; it is
not a runtime or production claim.

### 4.1 Versioned declared boundary and tap policy

- **T021-SR-001 [ubiquitous]**: The observation boundary **shall** remain versioned by the single accepted
  observation-contract version `kObservationContractVersion` (`"1.0.0"`); `ObservationTapSpec::create`
  **shall** reject any other declared version and **shall** neither add nor accept a second observation
  vocabulary.
  - Refines: `XCOM-SW-OBS-001`; anchors FR-011, FR-002; `XCOM-XLC-003`.
  - Verification intent: the exact-version accept and wrong-version reject cases; CHK-03, NEG-01.
- **T021-SR-002 [ubiquitous]**: An observation tap declaration **shall** carry one mandatory declared
  observation-point identity (`tap_id`) taken from the declared observation point it realizes
  (`observationPoints[].tapId` in the accepted activation plan), validated as a bounded logical `Identity`
  (1–128 bytes, no ASCII control byte, no leading/trailing whitespace); an empty, out-of-bound, or
  malformed declared identity **shall** yield no policy value.
  - Refines: `XCOM-SW-OBS-001`; anchors FR-011, FR-003; `XCOM-CMP-008`; `XCOM-XLC-003`;
    data-model `ObservationTap` "tap ID".
  - Verification intent: the declared-identity positive/boundary matrix and its rejection cases;
    CHK-04, CHK-05, NEG-02, NEG-03, NEG-04.
- **T021-SR-003 [ubiquitous]**: The declared logical route point a tap attaches to **shall** have exactly
  one source of truth: the filter's declared route constraint. A tap whose filter declares no route
  constraint observes every declared route point and reports no declared route point; a tap whose filter
  declares a route constraint reports that exact identity and **shall not** be able to declare a
  contradictory attachment point.
  - Refines: `XCOM-SW-OBS-001`; anchors FR-011; `XCOM-CMP-008`;
    `contracts/observation.md` "attaches to a declared logical route point".
  - Verification intent: the declared-route-point derivation case plus the contradictory-declaration
    review probe; CHK-07, NEG-05.
- **T021-SR-004 [ubiquitous]**: `ObservationFilter` **shall** expose read-only accessors for its declared
  constraint set — contract, interface, endpoint, route, provider, interaction kind, and origin — returning
  the validated `Identity`/enumeration or `std::nullopt` for an unconstrained field, and **shall** keep
  `matches()` byte-for-byte equivalent to the accepted baseline semantics.
  - Refines: `XCOM-SW-OBS-001`; anchors FR-011; `XCOM-DU-012`.
  - Verification intent: the accessor round-trip case and the unchanged-filter-matrix case; CHK-06,
    CHK-21.
- **T021-SR-005 [ubiquitous]**: The immutable payload policy **shall** keep the accepted explicit
  vocabulary and bounds: `metadata_only` (default, zero payload bytes), `bounded_prefix` with
  `1 ≤ maximum_payload_bytes ≤ kMaximumObservedPayloadBytes`, and `redacted` (zero bytes); an unknown mode,
  a zero or over-bound prefix, a zero prefix bound on a non-prefix mode, and a record capacity outside
  `1…kMaximumObservationRecordsPerTap` **shall** each yield no policy value.
  - Refines: `XCOM-SW-OBS-001`; anchors FR-011, FR-012; `XCOM-DU-012`; `XCOM-INV-06`;
    `contracts/observation.md` modes.
  - Verification intent: the payload-mode/bound boundary matrix; CHK-09, CHK-15, NEG-06, NEG-07, NEG-08.
- **T021-SR-006 [ubiquitous]**: The declared overflow policy **shall** keep the accepted vocabulary
  (`drop_newest`, `coalesce_latest`, `lossless_validation`); an unknown value **shall** yield no policy
  value; T021 **shall** change no retention, drop, coalesce, or backpressure rule.
  - Refines: `XCOM-SW-OBS-001`, `XCOM-SW-OBS-003`; anchors FR-013; `XCOM-DU-012`/`013`.
  - Verification intent: the overflow-vocabulary case and the unchanged-retention regression cases;
    CHK-08, CHK-21, NEG-09.
- **T021-SR-007 [ubiquitous]**: The tap policy **shall** carry one declared validity effect from the
  accepted `io.xverse.xcom` `validityEffect` vocabulary — `none` (default), `degrade_on_loss`, and
  `invalidate_on_loss` — with stable external text `"none"`, `"degrade-on-loss"`, and
  `"invalidate-on-loss"`, and **shall** reject an unknown value; T021 **shall** implement no behaviour
  from this declaration.
  - Refines: `XCOM-SW-OBS-001`; anchors FR-012, FR-013, SC-004; `xdl/profiles/xcom-v0.1.schema.json`
    `observation-policy`; data-model `ObservationTap` "validity effect".
  - Verification intent: the vocabulary/text case and the unknown-value rejection case; CHK-08, NEG-10.

### 4.2 Immutable record and exact handle authority

- **T021-SR-008 [ubiquitous]**: `ObservationRecord` **shall** identify the declared observation point that
  produced it by carrying the producing tap's declared `tap_id` as an owned immutable field, in addition
  to every accepted baseline field.
  - Refines: `XCOM-SW-OBS-005`; anchors FR-023, FR-011; `XCOM-DU-012`; data-model `ObservationRecord`
    "tap identity".
  - Verification intent: the record-self-description case; CHK-10.
- **T021-SR-009 [ubiquitous]**: `ObservationRecord` **shall** carry the producer's bounded retention-time
  queue counters (queued, accepted, dropped, coalesced) as an owned immutable projection, so a pulled
  record is self-describing and every dropped or coalesced record remains visible in counters.
  - Refines: `XCOM-SW-OBS-003`, `XCOM-SW-OBS-005`; anchors FR-013, SC-004, FR-023; `XCOM-DU-012`/`013`;
    data-model `ObservationRecord` "queue counters".
  - Verification intent: the retention-counter projection case for retained, dropped, and coalesced
    submissions; CHK-11.
- **T021-SR-010 [ubiquitous]**: `ObservationRecord` and `ObservationSnapshot` **shall** be immutable
  value-owned projections: accessors **shall** remain valid for the lifetime of the returned value, no
  view into hub storage **shall** be retained after the owning call returns, and no record may be
  constructed by a consumer.
  - Refines: `XCOM-SW-OBS-001`, `XCOM-SW-OBS-005`; anchors FR-011, FR-023; `XCOM-DU-012`;
    `XCOM-UDI-09`.
  - Verification intent: the copy-safety and post-return-lifetime cases; CHK-10, CHK-21, NEG-19.
- **T021-SR-011 [ubiquitous]**: `ObservationTapHandle` **shall** remain the exact opaque authority for one
  hub instance, one fixed tap slot, and one generation; a foreign, stale, or closed handle **shall** be
  rejected with a stable outcome and no unrelated mutation, and a duplicated close **shall** report
  `tap_closed`. The declared `tap_id` is declaration metadata and **shall not** confer or replace handle
  authority.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-014, FR-009; `XCOM-INV-02`; `XCOM-DU-013`.
  - Verification intent: the existing exact-handle, foreign-authority, duplicate-close, and recreated-
    generation cases re-run unchanged; CHK-13, NEG-11, NEG-12, NEG-13.
- **T021-SR-012 [ubiquitous]**: A tap **shall** expose its declared identity, declared route point,
  declared validity effect, and counters through an exact-handle snapshot, and **shall** report no
  snapshot for an invalid, foreign, stale, or closed handle.
  - Refines: `XCOM-SW-OBS-001`; anchors FR-011; `XCOM-DU-012`; data-model tap state
    `declared → attached → active → degraded → detached`.
  - Verification intent: the snapshot-declaration case; CHK-12, NEG-11.
- **T021-SR-013 [ubiquitous]**: Multiple taps **shall** be permitted to carry the same declared
  observation-point identity (multiple observers of one declared point are an accepted edge case); the
  declared identity **shall not** be a uniqueness or ownership rule, and tap capacity remains
  `kMaximumObservationTaps` exact slots.
  - Refines: `XCOM-SW-OBS-001`, `XCOM-SW-OBS-004`; anchors FR-011, FR-014; spec edge case "multiple
  observers see different filtered views".
  - Verification intent: the repeated-declared-tap capacity case; CHK-13.

### 4.3 Concurrency, bounds, and resource behaviour

- **T021-SR-014 [ubiquitous]**: `ObservationFilter::create`, `ObservationTapSpec::create`, and every new
  accessor **shall** be `noexcept` and **shall** introduce no shared mutable state; declaration
  construction is call-local and copies every declared value into fixed storage.
  - Refines: `XCOM-SW-OBS-001`; anchors FR-011; `XCOM-DU-012`; T010 `thread_safety` vocabulary.
  - Verification intent: source inspection plus the concurrent declaration case; CHK-14, CHK-16.
- **T021-SR-015 [ubiquitous]**: Every observation resource **shall** remain finite and preallocated: eight
  fixed tap slots, at most sixteen fixed record slots per tap, payload prefixes bounded to
  `kMaximumObservedPayloadBytes` (1024) bytes, and no dynamic allocation, unbounded queue, retry, quota,
  or wall-clock dependency anywhere on the T021 path.
  - Refines: `XCOM-SW-OBS-001`, `XCOM-SW-OBS-003`; anchors FR-007, FR-013; `XCOM-DU-012`/`013`.
  - Verification intent: the constants inspection and the bounded-record-size case; CHK-14, CHK-18.
- **T021-SR-016 [ubiquitous]**: Hub mutation and pull operations **shall** remain serialized, a returned
  record/snapshot **shall** be copied after the lock is released, and no consumer callback **shall** exist
  or be invoked under an X-COM lock.
  - Refines: `XCOM-SW-OBS-004`; anchors FR-014; `XCOM-DU-013`; `XCOM-UDI-09`.
  - Verification intent: the existing concurrent publication/pull case re-run unchanged plus the
    no-callback source scan; CHK-16, NEG-19.

### 4.4 Safety, documentation, and governance

- **T021-SR-017 [ubiquitous]**: The T021 candidate **shall** perform no network, socket, resolver, TLS,
  ambient, secret, filesystem, process, dynamic-load, or legacy access, **shall** add no admitted
  dependency beyond the C++ standard library, and **shall** contain no domain-specific or export/dashboard/
  storage primitive.
  - Refines: `XCOM-SW-CORE-007` (domain-neutral local runtime half), `XCOM-SW-OBS-005` boundary half;
    anchors FR-023, FR-026, FR-028; ADR-0019.
  - Verification intent: the forbidden-API scan plus the successful offline build; CHK-17, NEG-20,
    NEG-21.
- **T021-SR-018 [ubiquitous]**: Committed source, tests, and work products **shall** contain no credential,
  private address, unrestricted or real payload, proprietary source excerpt, environment-specific absolute
  host path, or sensitive deployment value.
  - Refines: Constitution X; anchors FR-027; `XCOM-SW-INTG` public-safe evidence rule.
  - Verification intent: the public-safety scan; CHK-18, NEG-22.
- **T021-SR-019 [ubiquitous]**: Every new or changed public C/C++ declaration **shall** carry useful
  Doxygen documentation including its ownership, lifetime, thread-safety, and failure contract, in the
  `xcom_obs` group, without weakening the admitted repository documentation configuration.
  - Refines: `XCOM-SW-OBS-001`; anchors FR-029; `XCOM-DU-012` Doxygen obligation; Constitution X.
  - Verification intent: declaration inspection and the existing documentation validator; CHK-19.
- **T021-SR-020 [ubiquitous]**: The T021 candidate **shall** be additive: no existing test case, target,
  label, command, threshold, expected result, requirement, ADR, contract, schema, register, or another
  task's ownership path is removed, renamed, reordered, or weakened, and no later task is implemented.
  - Refines: ADR-0018, ADR-0020; T007 global prohibitions; anchors FR-030; Constitution VII, IX.
  - Verification intent: the changed-path and test-name comparison; CHK-02, CHK-21, NEG-23, NEG-24.
- **T021-SR-021 [ubiquitous]**: The T021 candidate **shall** satisfy the deterministic Fabro gate for
  implementation tasks: the six named work products exist, at least one `src/xverse/xcom/**` path changes,
  `cmake` configure, build, discovery, and the full `ctest` suite pass, and `git diff --check` is clean;
  the T021 checkbox is marked complete **only** in the implementation stage.
  - Refines: ADR-0020; anchors FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T021 <baseline>`; `git diff --check`; CHK-22.
- **T021-SR-022 [ubiquitous]**: T021 **shall** reconcile with the T007 ownership register, the T008
  requirement register, the T009 architecture model, and the T010 unit design without rewriting or
  weakening them; **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list; and
  **shall** record honestly (a) that `XCOM-SW-OBS-002` is attributed to T022 while `XCOM-DU-012` links it
  to the T021-owned unit, (b) the historical SESN-era `XCOM-OBS-001…009` evidence identifiers, and (c) that
  the SESN-era validator `scripts/validate_xcom_observation.py` is not used by the repository-owned
  workflow.
  - Refines: ADR-0020; anchors FR-030, FR-035; Constitution VII, IX.
  - Verification intent: the register validators plus the recorded-attribution inspection; CHK-20, CHK-23.

## 5. Requirement-to-accepted-anchor traceability

| T021 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T021-STK-001 | `XCOM-SW-OBS-001` | XCOM-SYS-FR-011 | FR-011 | IX, X |
| T021-STK-002 | `XCOM-SW-OBS-001/002` | XCOM-SYS-FR-011/012 | FR-011, FR-012 | IX |
| T021-STK-003 | `XCOM-SW-OBS-001/002` | XCOM-SYS-FR-009/011 | FR-009, FR-011 | IX |
| T021-STK-004 | `XCOM-SW-OBS-005` | XCOM-SYS-FR-023/026/028 | FR-023, FR-026, FR-028 | II, VII, IX |
| T021-STK-005 | Constitution VII/IX; ADR-0018/0020 | – | FR-030 | VII, IX, X |
| T021-SR-001 | `XCOM-SW-OBS-001` | XCOM-SYS-FR-011 | FR-011, FR-002 | III |
| T021-SR-002 | `XCOM-SW-OBS-001` | XCOM-SYS-FR-011 | FR-011 | III, V |
| T021-SR-003 | `XCOM-SW-OBS-001` | XCOM-SYS-FR-011 | FR-011 | V |
| T021-SR-004 | `XCOM-SW-OBS-001` | XCOM-SYS-FR-011 | FR-011 | IX |
| T021-SR-005 | `XCOM-SW-OBS-002` (T022) | XCOM-SYS-FR-012 | FR-012 | IX |
| T021-SR-006 | `XCOM-SW-OBS-003` (T022) | XCOM-SYS-FR-013 | FR-013 | IX |
| T021-SR-007 | `XCOM-SW-OBS-002/003` (T022) | XCOM-SYS-FR-012/013 | FR-012, FR-013, SC-004 | III, IX |
| T021-SR-008 | `XCOM-SW-OBS-005` (T024) | XCOM-SYS-FR-023 | FR-023 | IX |
| T021-SR-009 | `XCOM-SW-OBS-003/005` (T022/T024) | XCOM-SYS-FR-013/023 | FR-013, SC-004 | IX |
| T021-SR-010 | `XCOM-SW-OBS-001/005` | XCOM-SYS-FR-011/023 | FR-011, FR-023 | IX |
| T021-SR-011 | `XCOM-SW-OBS-004` (T023) | XCOM-SYS-FR-009/014 | FR-009, FR-014 | IX |
| T021-SR-012 | `XCOM-SW-OBS-001` | XCOM-SYS-FR-011 | FR-011 | IX |
| T021-SR-013 | `XCOM-SW-OBS-001/004` | XCOM-SYS-FR-011/014 | FR-011, FR-014 | IX |
| T021-SR-014 | `XCOM-SW-OBS-001` | XCOM-SYS-FR-011 | FR-011 | IX |
| T021-SR-015 | `XCOM-SW-OBS-001/003` | XCOM-SYS-FR-007/013 | FR-007, FR-013 | IX |
| T021-SR-016 | `XCOM-SW-OBS-004` (T023) | XCOM-SYS-FR-014 | FR-014 | IX |
| T021-SR-017 | `XCOM-SW-OBS-005` (T024) | XCOM-SYS-FR-023/026/028 | FR-023, FR-026, FR-028 | II, VII |
| T021-SR-018 | public-safe evidence rule | XCOM-SYS-FR-027 | FR-027 | X |
| T021-SR-019 | `XCOM-SW-OBS-001` Doxygen | XCOM-SYS-FR-029 | FR-029 | X |
| T021-SR-020 | Constitution; ADR-0018/0020 | XCOM-SYS-FR-030 | FR-030 | VII, IX |
| T021-SR-021 | ADR-0020 | – | FR-030 | X |
| T021-SR-022 | Constitution; ADR-0020 | XCOM-SYS-FR-035 | FR-030, FR-035 | VII, IX |

`XCOM-SW-OBS-001`–`-005` are the accepted capability-007 software requirements
(`docs/engineering/xcom/t008/requirements-register.{json,md}`). They are accepted text; T021 refines and
consumes them and does not rewrite them. Where a T021 requirement contributes to a software requirement
whose register row names another owning task (T022/T023/T024), the register row is **not** changed and no
maturity is promoted; the contribution is a declaration, not the owning task's behaviour.

## 6. REF-002 disposition

T021 owns no REF-002 SADS ID and promotes none. It provides part of the bounded observation contribution
recorded against the allocated IDs `XVE-SYS-0140` (records retain all four generic interaction families),
`XVE-SYS-0142` (provider-neutral filtering and records), `XVE-SYS-0146` (versioned observation contract
with undecoded schema status only), and `XVE-SYS-0149` (fixed observation records, counters, and pull
access). The capability `ref002.disposition` stays `unchanged` with an empty `promoted` list
(T021-SR-022). No allocated, deferred, architectural-target, or superseded SADS requirement is reported as
implemented, and no `XVE-SYS-*` ID is promoted.

## 7. Affected paths

### 7.1 Paths the T021 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/observation.hpp` | edit | adds `ObservationValidityEffect` + `to_string`, the declared `tap_id` and `validity_effect` policy fields and accessors, the `ObservationFilter` declared-constraint accessors, the `ObservationRecordCounters` projection, and the record/snapshot declaration accessors; no existing declaration removed, renamed, or narrowed |
| `src/xverse/xcom/src/observation.cpp` | edit | validates the declared identity and validity effect in `ObservationTapSpec::create`, implements the new accessors, and stamps the declared identity and retention counters into each retained record; every retention, drop, coalesce, backpressure, and handle rule is byte-identical |
| `tests/xcom/observation/core/unit_tests.cpp` | edit | extends the one existing T021/T-OBS unit fixture with the new declaration, record, and rejection cases; updates the fixture helper so each existing case declares a valid observation point; every existing assertion is preserved |
| `tests/xcom/observation/integration/test_support.hpp` | edit | declares a valid observation point in the shared `make_tap_spec` helper so the T022/T023 integration fixtures still compile and behave identically |
| `tests/xcom/observation/integration/integration_tests.cpp` | edit | declares the observation point at the one direct `ObservationTapSpec::create` negative site so its rejection remains attributable to the intended cause |
| `docs/engineering/xcom/t021/requirements.md` | add | this document |
| `docs/engineering/xcom/t021/architecture.md` | add | boundary, components, data flow, interfaces (plan stage) |
| `docs/engineering/xcom/t021/detailed-design.md` | add | declaration rules, vocabulary, failure semantics, bounds (plan stage) |
| `docs/engineering/xcom/t021/unit-specifications.md` | add | units, ownership/lifetime/thread-safety/bounds, planned tests (plan stage) |
| `docs/engineering/xcom/t021/verification-plan.md` | add | named checks, negative cases, commands, evidence (plan stage) |
| `docs/engineering/xcom/t021/implementation.md` | add (implementation stage) | realized change and candidate-bound local evidence |
| `docs/engineering/xcom/t021/internal-review.json` | add (review stage) | separate read-only DeepSeek internal review |
| `specs/007-xcom-core/tasks.md` | edit T021 checkbox (implementation stage only) | capability task ledger; `- [ ] T021` → `- [X] T021` |
| `reports/xcom-queue/t021-package.json` | add (package stage) | exact-candidate package record |

No build file changes: the existing `xverse::xcom_observation` library target already compiles
`src/observation.cpp`, and the existing `xcom_observation_unit` executable already compiles
`tests/xcom/observation/core/unit_tests.cpp`, so the new cases are discovered without adding or renaming a
target, test, or label.

### 7.2 T021-owned observation paths consumed and re-verified unchanged

| Path | Owner | Role for T021 |
| --- | --- | --- |
| `tests/xcom/observation/integration/disabled_tap_benchmark.cpp` | T-OBS (T036 owns execution) | disabled-tap benchmark; re-run unchanged, not edited |
| `tests/xcom/observation/integration/test_support.hpp` | T-OBS (T022/T023) | shared integration fixture; only the declared observation point is added |
| `src/xverse/xcom/include/xverse/xcom/provider.hpp`, `src/xverse/xcom/src/provider.cpp` | T015 (T-CORE) | optional non-owning `ObservationHub` seam (`reserve`/`commit`); consumed read-only and not changed by T021 |
| `scripts/validate_xcom_observation.py` | T-OBS (legacy SESN evidence) | not executed, not edited, and not used as T021 evidence |

### 7.3 Consumed, read-only foundation (not changed by T021)

| Path | Owner | Role for T021 |
| --- | --- | --- |
| `src/xverse/xcom/CMakeLists.txt`, `cmake/*.cmake`, `CMakeLists.txt` | shared (serialized) | T012 subtree build contract that compiles `observation.cpp` and the observation fixtures; T021 changes none |
| `xdl/profiles/xcom-v0.1.schema.json` | T-XDL (T017) | authoritative source of the `observation-policy` `validityEffect` vocabulary; read-only |
| `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp`, `src/xverse/xcom/src/activation_plan.cpp`, `src/xverse/xcom/contracts/v1/activation-plan.schema.json` | T-XDL (T019) | decoded `ObservationPoint{tap_id, route_id, payload_access, validity_effect}`; the declared identities T021 validates are derived from this model; read-only |
| `src/xverse/xcom/include/xverse/xcom/{value,contract,item,diagnostic,result,core_types}.hpp` | T013 (T-CORE) | validated `Identity`, `SemanticVersion`, `CommunicationItem`, diagnostics; consumed read-only |
| `docs/engineering/xcom/t008/*`, `t009/*`, `t010/*` | T008/T009/T010 | accepted registers/model/unit design; T021 records the §7.2/§8.4 observations and rewrites nothing |
| `docs/xcom/observation-boundary.md`, `docs/xcom/observation-boundary-traceability.json` | legacy SESN evidence bundle | historical evidence for an exact superseded revision only; neither current acceptance evidence nor rewritten |

### 7.4 Recorded attribution observation (not resolved by T021)

`docs/engineering/xcom/t008/requirements-register.json` attributes `XCOM-SW-OBS-001` to T021 and
`XCOM-SW-OBS-002`/`-003` to T022, while `docs/engineering/xcom/t010/unit-design.json` links `XCOM-DU-012`
(owning task T021) to `XCOM-SW-OBS-001`, `-002`, and `-005`. The accepted `tasks.md` assigns the immutable
record/filter/payload-policy/tap-handle source to T021 and the bounded drop/coalesce/lossless behaviour to
T022. T021 therefore implements the *declaration* half of the payload/validity policy and the record
projection, and implements no T022 behaviour. It records this observation, implements the source as
`tasks.md`/`XCOM-DU-012` direct, and rewrites nothing (T021-SR-022).

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- `T021-LIM-01` — The observation boundary remains a bounded prototype: it makes no runtime, telemetry,
  transport, timing, compatibility, parity, or production-readiness claim, and it is not yet user-accepted
  (T041).
- `T021-LIM-02` — Per-record queue counters are a retention-time projection, not a durable log: they
  describe the tap queue at the moment the record was retained and are not a substitute for the tap
  snapshot or for long-term storage (T023/T035 own observable counters and evidence).
- `T021-LIM-03` — The declared validity effect is a vocabulary and a report only. No loss behaviour,
  degradation policy, or invalidation rule is applied by T021; the baseline
  `ObservationSnapshot::experiment_validity_degraded` marker keeps its exact accepted semantics until T022.
- `T021-LIM-04` — Payload identity allow-listing (`payloadAccess: allow-listed` with `allowList` in the
  accepted Profile) is **not** implemented; T021 keeps the explicit mode-plus-bound payload policy, which
  never exposes more than the explicitly declared prefix.
- `T021-LIM-05` — Schema interpretation remains `PayloadSchemaState::undecoded`; no decoder is introduced
  and no schema success is claimed.
- `T021-LIM-06` — `scripts/validate_xcom_observation.py` is legacy SESN-era tooling in the T-OBS path set
  (it binds `SESN_CANDIDATE_REVISION`); the repository-owned workflow does not use it, and T021 neither
  depends on nor edits it.
- `T021-LIM-07` — Every declared record retains a fixed 1024-byte payload buffer plus the item projection,
  so tap slot storage is large; this is the bounded-storage tradeoff inherited unchanged from the baseline.
- `T021-LIM-08` — Declaring a tap identity does not bind a tap to a decoded activation plan; the
  plan-to-attachment binding of a decoded `ObservationPoint` remains downstream work.

### 8.2 Gaps with owning tasks

| Gap | Description | Owner | Disposition |
| --- | --- | --- | --- |
| `T021-GAP-01` | Applying the declared validity effect and the declared overflow policy to retention, and counting loss as experiment validity | T022 | allocated |
| `T021-GAP-02` | Payload identity allow-list, redaction profile, and any decoder/schema status beyond `undecoded` | T022 | allocated |
| `T021-GAP-03` | Synthetic sink failure/disconnect isolation and its visible counters | T023 | allocated |
| `T021-GAP-04` | Metadata-only zero-payload, controlled-payload, redaction/truncation, ordering, saturation, degraded-validity, safe-detach matrix and semantics | T024 | allocated |
| `T021-GAP-05` | The T008/T010 T021/T022 attribution nuance of §7.4 | T008/T010 (registers); T021 (source) | allocated; T021 records and promotes nothing |
| `T021-GAP-06` | Candidate acceptance under capability 007 remains with T039/T041. | T039/T041 | allocated; T021 submits for review |

### 8.3 Open items

- `T021-OPEN-01` — Whether a later slice exposes the declared validity effect through the local tool-
  gateway observation contract (T030–T032) or only through the in-process API is that slice's decision;
  T021 declares the vocabulary and its external text.
- `T021-OPEN-02` — Whether a future slice replaces `ObservationOverflowPolicy::coalesce_latest` with a
  windowed coalesce quota is T022's decision; T021 neither changes nor renames the accepted enumerator.
- `T021-OPEN-03` — If a later slice merges the four observation fixtures into a reusable observer contract
  suite (T033), the owning task updates the build contract; T021 adds no target.

## 9. Definition of done (requirements view)

T021 is complete for this slice when: (a) the five plan-stage work products exist under
`docs/engineering/xcom/t021/` and are mutually consistent; (b) every requirement in §3–§4 has ≥ 1 named
check in `verification-plan.md`; (c) the implementation stage delivers the declared tap identity,
declared route-point accessors, declared validity-effect vocabulary, and the self-describing immutable
record, marks the T021 checkbox, and records `implementation.md`; (d) the deterministic gate and the named
checks pass at the candidate revision with no existing case weakened; (e) the package record is written;
and (f) a separate DeepSeek internal review records a passing verdict with no findings. This does **not**
constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary check(s) |
| --- | --- |
| T021-STK-001 | CHK-02, CHK-03, CHK-22 |
| T021-STK-002 | CHK-04, CHK-09, CHK-15, NEG-02..NEG-10 |
| T021-STK-003 | CHK-10, CHK-12, CHK-13, CHK-16 |
| T021-STK-004 | CHK-17, CHK-18, CHK-24 |
| T021-STK-005 | CHK-02, CHK-20, CHK-21, CHK-23 |
| T021-SR-001 | CHK-03, NEG-01 |
| T021-SR-002 | CHK-04, CHK-05, NEG-02, NEG-03, NEG-04 |
| T021-SR-003 | CHK-07, NEG-05 |
| T021-SR-004 | CHK-06, CHK-21 |
| T021-SR-005 | CHK-09, CHK-15, NEG-06, NEG-07, NEG-08 |
| T021-SR-006 | CHK-08, CHK-21, NEG-09 |
| T021-SR-007 | CHK-08, NEG-10 |
| T021-SR-008 | CHK-10 |
| T021-SR-009 | CHK-11 |
| T021-SR-010 | CHK-10, CHK-21, NEG-19 |
| T021-SR-011 | CHK-13, NEG-11, NEG-12, NEG-13 |
| T021-SR-012 | CHK-12, NEG-11 |
| T021-SR-013 | CHK-13 |
| T021-SR-014 | CHK-14, CHK-16 |
| T021-SR-015 | CHK-14, CHK-18 |
| T021-SR-016 | CHK-16, NEG-19 |
| T021-SR-017 | CHK-17, NEG-20, NEG-21 |
| T021-SR-018 | CHK-18, NEG-22 |
| T021-SR-019 | CHK-19 |
| T021-SR-020 | CHK-02, CHK-21, NEG-23, NEG-24 |
| T021-SR-021 | CHK-22 |
| T021-SR-022 | CHK-20, CHK-23 |
