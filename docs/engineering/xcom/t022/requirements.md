# T022 Requirements — Bounded Best-Effort Drop/Coalesce and Explicit Lossless-Validation Modes

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T022 (capability 007, slice `T-OBS`) |
| Task title | Implement bounded best-effort drop/coalesce and explicit lossless-validation modes |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `7be8b9718e42e58bb1a05a486ff62e520f94567c` |
| Authorization | capability 007 accepted design and bounded implementation authorization (ACC005/ACC010/ACC011/ACC014/ACC015); ADR-0016; ADR-0018; ADR-0019; ADR-0020 |
| Owning slice | `T-OBS` (T007 ownership register) |
| Predecessor | T021 (declared observation records, filters, payload policy, tap handles; reviewed terminal package) |
| Producer dependencies | T011 admitted offline build envelope (read-only inputs); T012 subtree CMake/CTest contract; T013 immutable core value/item/diagnostic types; T015 provider composition with the optional non-owning `ObservationHub` seam; T019 bounded activation-plan decode; T021 declared tap policy, filter, immutable record, and exact tap handle |
| Successor tasks | T023 (synthetic sink and isolation), T024 (observation test matrix incl. saturation/degraded validity), then T025–T034, T035–T041 |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}`; `docs/engineering/xcom/t008/requirements-register.{json,md}`; `docs/engineering/xcom/t008/traceability-matrix.{json,md}`; `docs/engineering/xcom/t009/architecture-model.{json,md}`; `docs/engineering/xcom/t010/unit-design.{json,md}` |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production
or test change and does not implement, accept, or integrate the candidate. The T022 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T022 — Implement bounded best-effort drop/coalesce and explicit lossless-validation modes.

### 1.1 Authority statement

This document specifies only the bounded T022 slice. It elaborates the accepted software requirement
`XCOM-SW-OBS-003` "Bounded observation queues and counters" (refines `XCOM-SYS-FR-013`/`XCOM-SYS-SC-004`,
spec `FR-013`/`SC-004`), which `docs/engineering/xcom/t008/requirements-register.{json,md}` attributes to
T022, together with the bounded-queue/counter/validity responsibilities that
`docs/engineering/xcom/t010/unit-design.{json,md}` assigns to design unit `XCOM-DU-013` "Bounded observer
queue, counters, and synthetic sink" (owning tasks T022/T023, requirement links `XCOM-SW-OBS-003`,
`XCOM-SW-OBS-004`). It consumes the accepted observation contract
(`specs/007-xcom-core/contracts/observation.md`, design contract `XCOM-XLC-003`), the accepted data model
(`specs/007-xcom-core/data-model.md`: `ObservationTap` overflow policies, counters, and validity effect;
tap state `declared → attached → active → degraded → detached`), and the accepted architecture component
`XCOM-CMP-008` "Observation boundary".

It does **not** redesign the accepted architecture, change a functional requirement, success criterion,
ADR, schema, or contract, implement T023 (synthetic sink/isolation) or T024 (broad observation matrix) or
any later task, add an admitted dependency, weaken an accepted requirement or test, or accept or integrate
any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, the
T007 ownership register, the T008 register/matrix, the T009 architecture model, the T010 unit design, the
constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is reported
rather than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T022)

1. **Realize the declared retention policy for the value-and-authority layer** under `src/xverse/xcom/`
   in namespace `xverse::xcom`, within the existing units
   `src/xverse/xcom/include/xverse/xcom/observation.hpp` and `src/xverse/xcom/src/observation.cpp`
   (design unit `XCOM-DU-013`).
2. **Bounded best-effort `drop_newest`.** The declared `drop_newest` policy keeps every tap queue within
   its declared capacity, retains the oldest records in per-route FIFO order, counts each dropped matching
   submission in the `dropped` counter, returns a stable best-effort outcome, never blocks or reorders the
   normal provider route, and never invokes a consumer. The accepted baseline behavior is preserved exactly.
3. **Bounded best-effort `coalesce_latest`.** The declared `coalesce_latest` policy replaces only the
   newest queued record whose logical coalescing key matches, counts the replacement in `coalesced`, drops
   the new record with a `dropped` increment when no queued record matches, and never blocks or reorders the
   normal provider route. The accepted coalescing-key set and FIFO order of unrelated records are preserved.
4. **Explicit `lossless_validation`.** The declared `lossless_validation` policy claims exact capacity
   before provider mutation, returns the stable `observation_backpressure` outcome before any provider
   mutation when declared capacity is unavailable, counts each rejection in `backpressure_rejections`, and
   emits no normal-route item. The accepted reserve/commit/claim semantics are preserved.
5. **Applied declared validity effect (the observable effect on test validity).** FR-013 requires a
   declared drop/coalesce/lossless-validation policy "with counters and an observable effect on test
   validity", and SC-004 requires every dropped or coalesced item to be reflected "in counters **and
   validation status**". The accepted `ObservationTapSpec` declares `validityEffect ∈ {none,
   degrade-on-loss, invalidate-on-loss}` but T021 applied no behavior (`T021-LIM-03`, `T021-GAP-01`). T022
   realizes the declared effect: a matching best-effort drop or coalesce raises the tap's realized validity
   status according to the declaration (`none` → no change, `degrade_on_loss` → `degraded`,
   `invalidate_on_loss` → `invalid`); a lossless-validation backpressure realizes at least `degraded`
   (because it is the declared loss of a required observation) and escalates to `invalid` under
   `invalidate_on_loss`.
6. **Observable realized validity status.** The realized status is exposed as an immutable, value-owned
   projection on the exact-handle snapshot with stable external text, and the accepted
   `experiment_validity_degraded` marker is preserved as the compatibility projection of that status.
   Acknowledging the exact handle closes the current observation-validity interval: the backpressure
   interval counter and a `degraded` state return to `valid`, while an `invalid` state persists until the
   tap is detached or its slot is recreated.
7. **Focused T022 cases** for the retention, validity-effect, and acknowledgement behavior, added inside
   the existing T-OBS-owned observation executable (`tests/xcom/observation/core/unit_tests.cpp`). The
   broad saturation, ordering, degraded-validity, metadata-only, controlled-payload, safe-detach, and
   benchmark matrix remains T024/T036.
8. The T022 repository-owned work products and the T022 package record.

### 2.2 Explicit exclusions (must remain absent from the T022 candidate)

No change to `tests/xcom/observation/integration/disabled_tap_benchmark.cpp`; no new CTest target, test
name, label, or removed/renamed case; no `CMakeLists.txt` or `cmake/*.cmake` change; no `src/xverse_xdl/`,
`xdl/`, `proto/`, or `src/xverse/xcom/contracts/` change; no `activation_plan.{hpp,cpp}`,
`provider.{hpp,cpp}`, `loopback_provider.{hpp,cpp}`, `endpoint_route_lifecycle.{hpp,cpp}`, `contract.hpp`,
`item.hpp`, `value.hpp`, `result.hpp`, `diagnostic.hpp`, `validation_session.{hpp,cpp}`, or
`stimulation_journal.{hpp,cpp}` change; no payload identity allow-list (`payloadAccess: allow-listed` +
`allowList`), redaction-profile, or decoder/schema-interpretation change beyond the accepted
`PayloadSchemaState::undecoded`; no synthetic sink or observer-isolation behaviour change (T023); no
temporization, rate limit (`bounds.maxRateHz`), retry, quota, persistence, replay, Argus/dashboard/storage/
export, OpenTelemetry, gateway, stimulation, or legacy behaviour; no new admitted dependency; no network,
TCP listener, DNS, TLS, filesystem, process, dynamic-load, ambient/secret, or legacy-repository access; no
rewrite or weakening of an accepted ADR, requirement, contract, test, REF-002 disposition, or another
task's ownership path; no promotion of any REF-002 or capability requirement; no acceptance or integration
of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T022 |
| --- | --- | --- |
| Synthetic sink, failure/disconnect isolation, visible counters | T023 | allocated; the existing `SyntheticObservationSink` is re-verified unchanged |
| Metadata-only zero-payload, controlled-payload, redaction/truncation, ordering, saturation, degraded-validity, safe-detach matrix; disabled-tap benchmark | T024/T036 | allocated; T022 adds only focused retention/validity cases |
| Payload identity allow-list (`payloadAccess: allow-listed` + `allowList`), redaction profile, decoder/schema status beyond `undecoded` | T022 attribution, unclaimed behaviour | recorded; T022's authorized task entry covers only the bounded queue/validity modes, so the allow-list and decoder remain unimplemented/partial (§7.4, §8) |
| `bounds.maxRateHz` rate limiting | not T022 | not implemented; remains a declared-but-unrealized Profile bound |
| Executed sanitizer/static-analysis/Doxygen evidence; integration, validation, delivery bundle | T035–T040 | allocated |
| Independent review and user acceptance | T039/T041 | allocated |

## 3. Stakeholder requirements (`T022-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T022-STK-001**: Before the observation boundary is accepted, the program **shall** have one
  repository-owned, bounded, domain-neutral C++20 retention-and-validity layer — bounded best-effort drop,
  bounded best-effort coalesce, explicit lossless-validation backpressure, and the applied declared validity
  effect — physically under `src/xverse/xcom/`, that compiles with the T011-admitted toolchain under the
  T012 warning-as-error contract.
- **T022-STK-002**: The retention path **shall** fail closed and stay bounded: no tap queue ever exceeds its
  declared capacity, every dropped or coalesced matching item is counted and reflected in validation status,
  best-effort loss never blocks, delays, reorders, or mutates the normal provider route, and no validity
  effect, counter, or outcome is inferred, defaulted, or strengthened.
- **T022-STK-003**: Every changed observation type **shall** keep its ownership, lifetime, thread-safety,
  and failure contract explicit, **shall** keep immutable value semantics that are safe to copy and to read
  concurrently, and **shall** treat the exact issued handle as the only authority to observe, acknowledge,
  or mutate a tap.
- **T022-STK-004**: The retention path **shall** be offline and domain-neutral: normal use performs no
  network discovery, ambient configuration or secret lookup, filesystem access, process execution, or
  legacy-repository access, contains no domain-specific primitive, adds no admitted dependency, and claims
  no export, dashboard, storage, or presentation behaviour.
- **T022-STK-005**: T022 **shall** preserve accepted intent: the delivered change is confined to the
  T022-owned observation paths, the T022 work products, and (implementation stage only) the capability task
  ledger, and it **shall** neither weaken an accepted requirement or test nor implement another task.

## 4. Software/engineering requirements (`T022-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Implemented" means the repository-owned source and its deterministic checks exist and pass; it is
not a runtime or production claim.

### 4.1 Bounded best-effort and explicit lossless retention

- **T022-SR-001 [event-driven]**: When a matching item arrives for a full `drop_newest` tap, the tap
  **shall** retain the already-queued records in FIFO order, drop the new record, increment `dropped` by
  exactly one, keep the queue size at its declared capacity, and report the stable best-effort outcome
  (`accepted`) without blocking, delaying, reordering, or mutating the normal provider route.
  - Refines: `XCOM-SW-OBS-003`; anchors FR-013, SC-004; `XCOM-DU-013`; data-model `ObservationTap`
    overflow policy.
  - Verification intent: the bounded-drop case and the FIFO-preservation case; CHK-05, CHK-06, NEG-01,
    NEG-13.
- **T022-SR-002 [event-driven]**: When a matching item arrives for a full `coalesce_latest` tap, the tap
  **shall** replace only the newest queued record whose logical coalescing key (contract identity and
  version, interface, endpoint, schema identity and version, interaction kind, origin, route, provider)
  matches and increment `coalesced`; when no queued record matches it **shall** drop the new record and
  increment `dropped`; in both cases it **shall** keep the queue within its declared bound, preserve the
  FIFO order of unrelated records, and never block or mutate the normal provider route.
  - Refines: `XCOM-SW-OBS-003`; anchors FR-013, SC-004; `XCOM-DU-013`; contracts/observation.md
    "Queue overflow follows the configured drop or coalesce rule".
  - Verification intent: the matching-key replacement case and the no-match drop case; CHK-05, CHK-06,
    NEG-02, NEG-03, NEG-13.
- **T022-SR-003 [event-driven]**: When a matching item arrives for a `lossless_validation` tap whose
  declared capacity is already claimed or full, the hub **shall** return the stable `observation_backpressure`
  outcome before any provider mutation, increment `backpressure_rejections`, emit no normal-route item, and
  retain no record; when capacity is available the reserve/commit claim **shall** authenticate exactly and
  release exactly once.
  - Refines: `XCOM-SW-OBS-003`; anchors FR-013, SC-004; `XCOM-DU-013`; contracts/observation.md
    "lossless-validation".
  - Verification intent: the pre-dispatch backpressure case, the reserve/commit/cancel case, and the
    in-flight-claim case; CHK-07, CHK-08, NEG-04, NEG-12. NEG-05 (lossless full at retention after a valid
    claim) is a non-constructible defensive guard, not an executable case.
- **T022-SR-004 [ubiquitous]**: Every tap queue **shall** be bounded by its declared record capacity
  (`1…kMaximumObservationRecordsPerTap`) under every policy, and the FIFO order of retained records **shall**
  be preserved under drop and coalesce.
  - Refines: `XCOM-SW-OBS-003`; anchors FR-007, FR-013, SC-004; `XCOM-DU-013`.
  - Verification intent: the saturation-bound case and the ordering case; CHK-05, CHK-06, CHK-13, NEG-14.

### 4.2 Applied declared validity effect

- **T022-SR-005 [event-driven]**: When a matching best-effort drop or coalesce-loss occurs, the tap
  **shall** raise its realized validity status according to the declared `validityEffect`: `none` **shall**
  leave the status `valid`, `degrade_on_loss` **shall** raise it to at least `degraded`, and
  `invalidate_on_loss` **shall** raise it to `invalid`.
  - Refines: `XCOM-SW-OBS-003`, `XCOM-SW-OBS-002` (attribution); anchors FR-013, SC-004, FR-012;
    `XCOM-DU-013`; data-model `ObservationTap` "validity effect"; xdl Profile `validityEffect`.
  - Verification intent: the best-effort validity matrix (three effects × drop/coalesce); CHK-09, NEG-06,
    NEG-07, NEG-08.
- **T022-SR-006 [event-driven]**: When a `lossless_validation` capacity loss occurs, the tap **shall** set
  the accepted `experiment_validity_degraded` marker and realize at least `degraded`, escalating to
  `invalid` only under a declared `invalidate_on_loss`.
  - Refines: `XCOM-SW-OBS-003`; anchors FR-013, SC-004; `XCOM-DU-013`;
    docs/xcom/observation-boundary.md "experiment validity is degraded until acknowledgement".
  - Verification intent: the lossless validity matrix; CHK-08, CHK-10, NEG-04.
- **T022-SR-007 [ubiquitous]**: The realized validity status **shall** be an explicit finite value
  (`valid`, `degraded`, `invalid`) with stable external text (`"valid"`, `"degraded"`, `"invalid"`), ordered
  `valid < degraded < invalid`, exposed as an immutable value-owned projection of an exact-handle snapshot;
  it **shall** be monotonic within an interval and **shall not** be lowered except by acknowledgement or
  detach/recreation.
  - Refines: `XCOM-SW-OBS-003`; anchors FR-013, SC-004; `XCOM-DU-013`; contracts/observation.md
    "marked degraded or invalid according to its declared criterion".
  - Verification intent: the vocabulary/ordering case and the snapshot projection case; CHK-09, CHK-11,
    NEG-12.
- **T022-SR-008 [event-driven]**: When the exact current handle acknowledges a tap, the hub **shall** close
  the current observation-validity interval by resetting `backpressure_rejections` and returning a
  `degraded` status to `valid`, while an `invalid` status **shall** persist until detach or slot
  recreation; a foreign, stale, or closed handle **shall** produce the accepted stable outcome with no
  interval reset.
  - Refines: `XCOM-SW-OBS-003`, `XCOM-SW-OBS-004` (attribution); anchors FR-013, FR-014, SC-004;
    `XCOM-DU-013`; data-model tap state `degraded → detached`.
  - Verification intent: the acknowledgement-interval case and the invalid-persistence case; CHK-10,
  NEG-10, NEG-11.

### 4.3 Concurrency, bounds, and resource behaviour

- **T022-SR-009 [ubiquitous]**: Every retention, counter, and validity update **shall** occur under the
  single hub mutex; a returned record or snapshot **shall** be copied after the lock is released; no
  consumer callback **shall** exist or be invoked under an X-COM lock; and the new accessors/vocabulary
  functions **shall** be `noexcept` and introduce no shared mutable state.
  - Refines: `XCOM-SW-OBS-004` (attribution); anchors FR-014; `XCOM-DU-013`; `XCOM-UDI-09`.
  - Verification intent: the existing concurrent publication/reservation cases re-run unchanged plus the
    no-callback source scan; CHK-12, CHK-16, NEG-15.
- **T022-SR-010 [ubiquitous]**: Every observation resource **shall** remain finite and preallocated: eight
  fixed tap slots, at most sixteen fixed record slots per tap, payload prefixes bounded to
  `kMaximumObservedPayloadBytes` (1024) bytes, and no dynamic allocation, unbounded queue, retry, rate,
  quota, timer, or wall-clock dependency anywhere on the T022 path.
  - Refines: `XCOM-SW-OBS-003`; anchors FR-007, FR-013; `XCOM-DU-013`.
  - Verification intent: the constants inspection and the bounded-record-size case; CHK-13, CHK-18.

### 4.4 Safety, documentation, and governance

- **T022-SR-011 [ubiquitous]**: The T022 candidate **shall** perform no network, socket, resolver, TLS,
  ambient, secret, filesystem, process, dynamic-load, or legacy access, **shall** add no admitted
  dependency beyond the C++ standard library, and **shall** contain no domain-specific or export/dashboard/
  storage/query primitive.
  - Refines: `XCOM-SW-CORE-007` (domain-neutral local runtime half); anchors FR-023, FR-026, FR-028;
    ADR-0019.
  - Verification intent: the forbidden-API scan plus the successful offline build; CHK-17, NEG-16.
- **T022-SR-012 [ubiquitous]**: Committed source, tests, and work products **shall** contain no credential,
  private address, unrestricted or real payload, proprietary source excerpt, environment-specific absolute
  host path, or sensitive deployment value.
  - Refines: Constitution X; anchors FR-027; `XCOM-SW-INTG` public-safe evidence rule.
  - Verification intent: the public-safety scan; CHK-18, NEG-17.
- **T022-SR-013 [ubiquitous]**: Every new or changed public C/C++ declaration **shall** carry useful
  Doxygen documentation including its ownership, lifetime, thread-safety, and failure contract, in the
  `xcom_obs` group, without weakening the admitted repository documentation configuration.
  - Refines: `XCOM-SW-OBS-003`; anchors FR-029; `XCOM-DU-013` Doxygen obligation; Constitution X.
  - Verification intent: declaration inspection and the existing documentation validator; CHK-19.
- **T022-SR-014 [ubiquitous]**: The T022 candidate **shall** be additive: no existing test case, target,
  label, command, threshold, expected result, requirement, ADR, contract, schema, register, or another
  task's ownership path is removed, renamed, reordered, or weakened; the accepted
  `experiment_validity_degraded` marker semantics (set by lossless backpressure, cleared by acknowledgement
  for a `degraded` interval) **shall** be preserved; and no later task is implemented.
  - Refines: ADR-0018, ADR-0020; T007 global prohibitions; anchors FR-030; Constitution VII, IX.
  - Verification intent: the changed-path and test-name comparison plus the preserved-marker regression;
    CHK-02, CHK-20, NEG-18, NEG-19.
- **T022-SR-015 [ubiquitous]**: The T022 candidate **shall** satisfy the deterministic Fabro gate for
  implementation tasks: the six named work products exist, at least one `src/xverse/xcom/**` path changes,
  `cmake` configure, build, discovery, and the full `ctest` suite pass, and `git diff --check` is clean;
  the T022 checkbox is marked complete **only** in the implementation stage.
  - Refines: ADR-0020; anchors FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T022 <baseline>`; `git diff --check`; CHK-21.
- **T022-SR-016 [ubiquitous]**: T022 **shall** reconcile with the T007 ownership register, the T008
  requirement register/matrix, the T009 architecture model, and the T010 unit design without rewriting or
  weakening them; **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list; and
  **shall** record honestly (a) that the T008 register attributes `XCOM-SW-OBS-002` (and `XCOM-SW-OBS-003`)
  to T022 while T010 links `XCOM-DU-013` to `XCOM-SW-OBS-003`/`-004`, (b) that `XCOM-SW-OBS-002`'s payload
  allow-list and decoder portions remain unimplemented/partial, (c) the historical SESN-era
  `XCOM-OBS-001…009` evidence identifiers, and (d) that the SESN-era validator
  `scripts/validate_xcom_observation.py` is not used by the repository-owned workflow.
  - Refines: ADR-0020; anchors FR-030, FR-035; Constitution VII, IX.
  - Verification intent: the register validators plus the recorded-attribution inspection; CHK-20, CHK-22.
- **T022-SR-017 [ubiquitous]**: T022 **shall** leave the payload-view interpretation, schema status,
  observer isolation, sink behaviour, and every non-retention observation contract exactly as accepted;
  the candidate **shall** neither implement the `payloadAccess: allow-listed` identity allow-list nor claim
  a decoder/schema success.
  - Refines: `XCOM-SW-OBS-002` (attribution, partial); anchors FR-012; `XCOM-DU-012`; T021-LIM-04/LIM-05.
  - Verification intent: the payload-boundary difference inspection; CHK-14, NEG-19.

## 5. Requirement-to-accepted-anchor traceability

| T022 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T022-STK-001 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-013 | FR-013 | IX, X |
| T022-STK-002 | `XCOM-SW-OBS-003/004` | XCOM-SYS-FR-013/014 | FR-013, FR-014, SC-004 | IX |
| T022-STK-003 | `XCOM-SW-OBS-003/004` | XCOM-SYS-FR-009/014 | FR-009, FR-014 | IX |
| T022-STK-004 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-023/026/028 | FR-023, FR-026, FR-028 | II, VII, IX |
| T022-STK-005 | Constitution VII/IX; ADR-0018/0020 | – | FR-030 | VII, IX, X |
| T022-SR-001 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-013 | FR-013, SC-004 | IX |
| T022-SR-002 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-013 | FR-013, SC-004 | IX |
| T022-SR-003 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-013 | FR-013, SC-004 | IX |
| T022-SR-004 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-007/013 | FR-007, FR-013, SC-004 | IX |
| T022-SR-005 | `XCOM-SW-OBS-003`, `XCOM-SW-OBS-002` | XCOM-SYS-FR-012/013 | FR-012, FR-013, SC-004 | IX |
| T022-SR-006 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-013 | FR-013, SC-004 | IX |
| T022-SR-007 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-013 | FR-013, SC-004 | IX |
| T022-SR-008 | `XCOM-SW-OBS-003/004` | XCOM-SYS-FR-013/014 | FR-013, FR-014, SC-004 | IX |
| T022-SR-009 | `XCOM-SW-OBS-004` | XCOM-SYS-FR-014 | FR-014 | IX |
| T022-SR-010 | `XCOM-SW-OBS-003` | XCOM-SYS-FR-007/013 | FR-007, FR-013 | IX |
| T022-SR-011 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-023/026/028 | FR-023, FR-026, FR-028 | II, VII |
| T022-SR-012 | public-safe evidence rule | XCOM-SYS-FR-027 | FR-027 | X |
| T022-SR-013 | `XCOM-SW-OBS-003` Doxygen | XCOM-SYS-FR-029 | FR-029 | X |
| T022-SR-014 | Constitution; ADR-0018/0020 | XCOM-SYS-FR-030 | FR-030 | VII, IX |
| T022-SR-015 | ADR-0020 | – | FR-030 | X |
| T022-SR-016 | Constitution; ADR-0020 | XCOM-SYS-FR-035 | FR-030, FR-035 | VII, IX |
| T022-SR-017 | `XCOM-SW-OBS-002` (partial) | XCOM-SYS-FR-012 | FR-012 | III, IX |

`XCOM-SW-OBS-001`–`-005` are the accepted capability-007 software requirements
(`docs/engineering/xcom/t008/requirements-register.{json,md}`). They are accepted text; T022 refines and
consumes them and does not rewrite them. The register attributes `XCOM-SW-OBS-002` (FR-012/SC-003) and
`XCOM-SW-OBS-003` (FR-013/SC-004) to T022; T022 implements the bounded queue/validity half of that
attribution (`XCOM-SW-OBS-003`) and records the payload-view half (`XCOM-SW-OBS-002`) as unimplemented and
partial. No register row is changed and no maturity is promoted.

## 6. REF-002 disposition

T022 owns no REF-002 SADS ID and promotes none. It provides part of the bounded observation contribution
recorded against the allocated IDs `XVE-SYS-0149` (observation records, metrics, counters, and tool
streams: bounded drop/coalesce/backpressure counters and the realized validity status) and `XVE-SYS-0145`
(explicit bounded QoS: the declared finite queue capacity and its declared overflow policy). It touches
`XVE-SYS-0142` (provider-neutral records) only through the unchanged counter/record path. The capability
`ref002.disposition` stays `unchanged` with an empty `promoted` list (T022-SR-016). No allocated, deferred,
architectural-target, or superseded SADS requirement is reported as implemented, and no `XVE-SYS-*` ID is
promoted.

## 7. Affected paths

### 7.1 Paths the T022 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/observation.hpp` | edit | adds `ObservationValidityState` + `to_string`, the trailing `validity_state` field on `ObservationSnapshot`, and Doxygen/traceability updates; no existing declaration or enumerator removed, renamed, or narrowed |
| `src/xverse/xcom/src/observation.cpp` | edit | applies the declared validity effect on matching drop/coalesce/lossless losses, realizes the lossless "at least degraded" rule, projects `experiment_validity_degraded` from the realized state, resets a `degraded` interval on `acknowledge` (an `invalid` state persists), and reports `validity_state` in `snapshot`; every accepted payload, handle, claim, ordering, and counter rule is otherwise byte-identical |
| `tests/xcom/observation/core/unit_tests.cpp` | edit | extends the one existing T-OBS unit fixture with the focused T022 retention, validity-effect, ordering, bound, and acknowledgement cases; every existing assertion is preserved |
| `docs/engineering/xcom/t022/requirements.md` | add | this document |
| `docs/engineering/xcom/t022/architecture.md` | add | boundary, components, data flow, interfaces (plan stage) |
| `docs/engineering/xcom/t022/detailed-design.md` | add | retention/validity rules, vocabulary, failure semantics, bounds (plan stage) |
| `docs/engineering/xcom/t022/unit-specifications.md` | add | units, ownership/lifetime/thread-safety/bounds, planned tests (plan stage) |
| `docs/engineering/xcom/t022/verification-plan.md` | add | named checks, negative cases, commands, evidence (plan stage) |
| `docs/engineering/xcom/t022/implementation.md` | add (implementation stage) | realized change and candidate-bound local evidence |
| `docs/engineering/xcom/t022/internal-review.json` | add (review stage) | separate read-only DeepSeek internal review |
| `specs/007-xcom-core/tasks.md` | edit T022 checkbox (implementation stage only) | capability task ledger; `- [ ] T022` → `- [X] T022` |
| `reports/xcom-queue/t022-package.json` | add (package stage) | exact-candidate package record |

No build file changes: the existing `xverse::xcom_observation` library target already compiles
`src/observation.cpp`, and the existing `xcom_observation_unit` executable already compiles
`tests/xcom/observation/core/unit_tests.cpp`, so the new cases are discovered without adding or renaming a
target, test, or label. No integration-test change is required: every existing integration fixture declares
the default `validity_effect` (`none`) and its lossless cases already expect the accepted degraded marker,
so their observable behavior is unchanged.

### 7.2 T022-owned observation paths consumed and re-verified unchanged

| Path | Owner | Role for T022 |
| --- | --- | --- |
| `tests/xcom/observation/integration/{test_support.hpp,integration_tests.cpp}` | T-OBS (T023/T024) | re-run unchanged; they declare the default `none` effect and their lossless/backpressure assertions still hold |
| `tests/xcom/observation/integration/disabled_tap_benchmark.cpp` | T-OBS (T036 owns execution) | re-run unchanged, not edited |
| `scripts/validate_xcom_observation.py` | T-OBS (legacy SESN evidence) | not executed, not edited, and not used as T022 evidence |

### 7.3 Consumed, read-only foundation (not changed by T022)

| Path | Owner | Role for T022 |
| --- | --- | --- |
| `src/xverse/xcom/CMakeLists.txt`, `cmake/*.cmake`, `CMakeLists.txt` | shared (serialized) | T012 subtree build contract that compiles `observation.cpp` and the observation fixtures; T022 changes none |
| `xdl/profiles/xcom-v0.1.schema.json` | T-XDL (T017) | authoritative source of the `observation-policy` `validityEffect` vocabulary; read-only |
| `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp`, `src/xverse/xcom/src/activation_plan.cpp`, `src/xverse/xcom/contracts/v1/activation-plan.schema.json` | T-XDL (T019) | decoded `ObservationPoint{tap_id, route_id, payload_access, validity_effect}`; read-only |
| `src/xverse/xcom/include/xverse/xcom/{value,contract,item,diagnostic,result,core_types}.hpp` | T013 (T-CORE) | validated `Identity`, `SemanticVersion`, `CommunicationItem`, diagnostics; consumed read-only |
| `docs/engineering/xcom/t008/*`, `t009/*`, `t010/*` | T008/T009/T010 | accepted registers/model/unit design; T022 records the §7.4 observations and rewrites nothing |
| `docs/xcom/observation-boundary.md`, `docs/xcom/observation-boundary-traceability.json` | legacy SESN evidence bundle | historical evidence for an exact superseded revision only; neither current acceptance evidence nor rewritten |

### 7.4 Recorded attribution observation (not resolved by T022)

`docs/engineering/xcom/t008/requirements-register.json` attributes `XCOM-SW-OBS-002` and
`XCOM-SW-OBS-003` to T022, while `docs/engineering/xcom/t008/traceability-matrix.json` allocates them to
the locator `XCOM-DU-OBS-BASELINE` and `docs/engineering/xcom/t010/unit-design.json` links `XCOM-DU-013`
(owning tasks T022/T023) to `XCOM-SW-OBS-003`/`XCOM-SW-OBS-004`. The accepted `tasks.md` assigns the
bounded drop/coalesce/lossless-validation behavior to T022. T022 therefore implements the
`XCOM-SW-OBS-003` queue/validity half, preserves every `XCOM-SW-OBS-002` payload-view behavior unchanged,
and rewrites nothing (T022-SR-016). `XCOM-SW-OBS-002`'s `payloadAccess: allow-listed` identity allow-list
and any decoder/schema status beyond `undecoded` remain unimplemented and partial; they are recorded as
`T022-LIM-02`/`T022-GAP-02` rather than silently dropped.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- `T022-LIM-01` — The retention/validity boundary remains a bounded prototype: it makes no runtime,
  telemetry, transport, timing, compatibility, parity, or production-readiness claim, and it is not yet
  user-accepted (T041).
- `T022-LIM-02` — The payload identity allow-list (`payloadAccess: allow-listed` + `allowList`) and any
  decoder/schema status beyond `PayloadSchemaState::undecoded` remain unimplemented; `XCOM-SW-OBS-002`
  therefore stays partial.
- `T022-LIM-03` — The realized validity status is an in-process, per-tap projection held only until tap
  detach/recreation; durable experiment-result validity, storage, and presentation belong to Argus/Faults
  and are not implemented here.
- `T022-LIM-04` — `bounds.maxRateHz` is accepted by the Profile but is not realized by the tap policy;
  rate limiting remains out of scope. The declared record capacity is the only enforced bound.
- `T022-LIM-05` — Coalescing keyed by logical identity keeps the accepted exact-field key set and an
  insertion-order newest-match scan; no windowed coalesce quota is introduced (`T021-OPEN-02`).
- `T022-LIM-06` — `scripts/validate_xcom_observation.py` is legacy SESN-era tooling in the T-OBS path set
  (it binds `SESN_CANDIDATE_REVISION`); the repository-owned workflow does not use it, and T022 neither
  depends on nor edits it.
- `T022-LIM-07` — Every retained record still carries a fixed 1024-byte payload buffer plus the item
  projection, so tap slot storage is large; this is the bounded-storage tradeoff inherited unchanged.

### 8.2 Gaps with owning tasks

| Gap | Description | Owner | Disposition |
| --- | --- | --- | --- |
| `T022-GAP-01` | Payload identity allow-list, redaction profile, and any decoder/schema interpretation | unclaimed in this slice; T022 attribution recorded | allocated/partial; T022 implements no payload-view behavior change (T022-LIM-02) |
| `T022-GAP-02` | Synthetic sink failure/disconnect isolation and its visible counters | T023 | allocated |
| `T022-GAP-03` | The broad metadata-only, controlled-payload, ordering, saturation, degraded-validity, safe-detach matrix | T024 | allocated |
| `T022-GAP-04` | The disabled-tap performance benchmark and its threshold | T036 | allocated |
| `T022-GAP-05` | Executed sanitizer/static-analysis/Doxygen evidence and the delivery/acceptance bundle | T035/T037/T038/T040/T041 | allocated |
| `T022-GAP-06` | The T008/T010/T008-matrix T022 attribution nuance of §7.4 | T008/T010 (registers); T022 (source) | allocated; T022 records and promotes nothing |

### 8.3 Open items

- `T022-OPEN-01` — Whether acknowledgement of an `invalidate_on_loss` status should be permitted to
  restore `valid` (making invalidation interval-scoped) or whether an invalid result should be terminal
  for the tap is a design decision recorded in `detailed-design.md` §5.3; T022 makes a `degraded` interval
  resettable and an `invalid` status persistent until detach, and records this for review.
- `T022-OPEN-02` — Whether a later slice exposes `ObservationValidityState` through the local tool-gateway
  observation contract (T030–T032) or only through the in-process API is that slice's decision; T022
  exposes it in-process with stable external text.

## 9. Definition of done (requirements view)

T022 is complete for this slice when: (a) the five plan-stage work products exist under
`docs/engineering/xcom/t022/` and are mutually consistent; (b) every requirement in §3–§4 has ≥ 1 named
check in `verification-plan.md`; (c) the implementation stage realizes the bounded best-effort drop/
coalesce modes, the explicit lossless-validation mode, the applied declared validity effect, and the
observable validity status, adds the focused cases, marks the T022 checkbox, and records
`implementation.md`; (d) the deterministic gate and the named checks pass at the candidate revision with
no existing case weakened; (e) the package record is written; and (f) a separate DeepSeek internal review
records a passing verdict with no findings. This does **not** constitute user acceptance, which remains
T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary check(s) |
| --- | --- |
| T022-STK-001 | CHK-02, CHK-03, CHK-21 |
| T022-STK-002 | CHK-05, CHK-06, CHK-09, CHK-10, NEG-01…NEG-04, NEG-06…NEG-10 |
| T022-STK-003 | CHK-08, CHK-11, CHK-12 |
| T022-STK-004 | CHK-17, CHK-18 |
| T022-STK-005 | CHK-02, CHK-14, CHK-20, NEG-18, NEG-19 |
| T022-SR-001 | CHK-05, NEG-01, NEG-13 |
| T022-SR-002 | CHK-05, CHK-06, NEG-02, NEG-03 |
| T022-SR-003 | CHK-07, CHK-08, NEG-04, NEG-12 (NEG-05 is a non-constructible defensive guard) |
| T022-SR-004 | CHK-05, CHK-13, NEG-14 |
| T022-SR-005 | CHK-09, NEG-06, NEG-07, NEG-08 |
| T022-SR-006 | CHK-08, CHK-10, NEG-04 |
| T022-SR-007 | CHK-09, CHK-11, NEG-12 |
| T022-SR-008 | CHK-10, NEG-10, NEG-11 |
| T022-SR-009 | CHK-12, CHK-16, NEG-15 |
| T022-SR-010 | CHK-13, CHK-18 |
| T022-SR-011 | CHK-17, NEG-16 |
| T022-SR-012 | CHK-18, NEG-17 |
| T022-SR-013 | CHK-19 |
| T022-SR-014 | CHK-02, CHK-14, CHK-20, NEG-18, NEG-19 |
| T022-SR-015 | CHK-21 |
| T022-SR-016 | CHK-20, CHK-22 |
| T022-SR-017 | CHK-14, NEG-19 |
