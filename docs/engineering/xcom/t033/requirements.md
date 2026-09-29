# T033 Requirements — Reusable Provider, Observer, Stimulation-Tool, and Gateway Contract Suites

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T033 (capability 007, slice `T-CORE`/GW) |
| Task title | Build reusable provider, observer, stimulation-tool, and gateway contract suites |
| Stage / role | plan → requirements |
| Revision | 1 (reusable contract-suite slice) |
| Baseline revision | `2fd395e39e44e1f6fe9547998b47499d996b1756` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC006`, `ACC010`, `ACC011`, `ACC014`, `ACC015`); `ADR-0016` (subsystem naming); `ADR-0018` (platform-first); `ADR-0019` (X-COM observation/stimulation boundary); `ADR-0020` (repository-owned work products and exact-candidate evidence) |
| Owning slice | `T-CORE` (T007 ownership register); T033 is the reusable contract-suite task of the `T-CORE`/GW family |
| Predecessors | T032 accepted separate-process synthetic client and generated-client contract suites (`src/xverse/xcom/fixtures/synthetic_tool.cpp`, `tests/xcom/tool_gateway/synthetic_client_*`); T031 accepted bounded local-IPC-only gateway; T030 accepted versioned `XCOM-XLC-002` contract; T029 stimulation matrix; T024 observation integration; T016 consolidated core matrix; T011 admitted offline envelope; T012 subtree CMake/CTest contract |
| Successor tasks | T034 (second synthetic provider and replacement/version-rejection/failure-isolation proof), T035–T041 (evidence, review, acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-CORE` slice; T033 exclusive path `docs/engineering/xcom/t033/`, `reports/xcom-queue/t033-package.json`); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-CORE-007`, `XCOM-SW-CORE-009`, `XCOM-SW-GW-002`); `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-005`/`006`/`007`, `XCOM-CMP-010`, `XCOM-CMP-011`, `XCOM-XLC-002`, `XCOM-XB-004`/`009`/`010`); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-007` provider boundary, `XCOM-DU-020` gateway session, `XCOM-DU-021` synthetic tool client) |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production change
and does not implement, accept, or integrate the candidate. The T033 task entry in `specs/007-xcom-core/tasks.md`
is the authorized scope:

> T033 — Build reusable provider, observer, stimulation-tool, and gateway contract suites.

It realizes the accepted external-tool contract statement in `specs/007-xcom-core/contracts/provider.md`
("remain replaceable by another conforming provider") and `specs/007-xcom-core/contracts/tool-gateway.md`,
and it realizes the accepted User Story 4 independent test ("A second synthetic provider and tool adapter pass
the same contract suite") at the reusable-suite boundary.

### 1.1 Authority statement

T033 owns the **reusable provider, observer, stimulation-tool, and gateway contract suites**. It provides four
implementation-agnostic conformance-suite drivers under `tests/xcom/contract_suites/` and their thin
instantiation drivers:

- `tests/xcom/contract_suites/provider_contract_suite.hpp` (`ProviderContractSuite`, `ProviderSubject`);
- `tests/xcom/contract_suites/observer_contract_suite.hpp` (`ObserverContractSuite`, `ObserverSubject`);
- `tests/xcom/contract_suites/stimulation_tool_contract_suite.hpp` (`StimulationToolContractSuite`,
  `StimulationToolSubject`);
- `tests/xcom/contract_suites/gateway_contract_suite.hpp` (`GatewayContractSuite`, `GatewaySubject`);
- `tests/xcom/contract_suites/suite_support.hpp` (`SuiteReport`/`SuiteCheck` shared vocabulary);
- the four additive `t033-<kind>` test drivers.

The `T008` requirements register allocates no software requirement exclusively to T033; T033 therefore realizes
its per-task projection of the accepted provider/observation/stimulation/gateway software requirements that
name T033 as a contributing contract-test owner. It records `XCOM-SW-CORE-007` (owned loopback provider),
`XCOM-SW-CORE-009` (loopback conformance and negative-case suite), and `XCOM-SW-GW-002` (local-IPC-only bounded
gateway) as the accepted anchors whose *suite reuse* it contributes to. The register rows are not edited
(T026–T032 precedent).

**Recorded design decision (`T033-DD-01`).** The four suites are genuine reusable abstractions: each suite body
names only an accepted interface (provider) or an accepted fixture helper plus a narrow subject seam, and each
subject is a small adapter that the caller supplies. A different conforming implementation (for example the T034
second synthetic provider) is validated by supplying a different subject; the suite header is not edited. T033
demonstrates provider-suite reuse across two independently implemented providers (the accepted owned loopback
provider and the accepted T016 probe provider) and reuse across instances for the observer, stimulation-tool, and
gateway suites.

**Suite-only boundary.** T033 authors reusable test suites and their drivers only. It authors no production
runtime source, no second synthetic provider (T034), no change to the accepted T030 contract, T031 gateway,
T032 client, or any accepted runtime byte, and no benchmark/sanitizer/static/Doxygen/delivery bundle
(T035–T040).

It does **not** redesign the accepted architecture, change a functional requirement, success criterion, ADR,
schema, XDL profile, or contract; modify any accepted predecessor byte under `src/`, `tests/`, `xdl/`, or
`docs/engineering/xcom/t0{07..32}/`; add an admitted dependency; link a gRPC runtime; weaken an accepted
`T030-SR-*`/`T031-SR-*`/`T032-SR-*` test; or accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, data model,
the T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design, the
constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is reported rather
than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T033)

1. **Reusable provider contract suite.** `ProviderContractSuite` validates any `CommunicationProvider` supplied
   through a `ProviderSubject`: descriptor identity/compatibility, explicit registration, duplicate rejection,
   fail-closed unsupported-version rejection, prepare/activate/submit/receive/drain/close, bounded reject-new
   saturation, and bounded reconcile reporting.
2. **Reusable observer contract suite.** `ObserverContractSuite` validates any observation boundary supplied
   through an `ObserverSubject`: metadata-only attachment, normalized metadata-only records with identity
   preservation, bounded drop-newest counters, exact-handle detach, detached-handle rejection, and normal-route
   isolation after detach.
3. **Reusable stimulation-tool contract suite.** `StimulationToolContractSuite` validates any guarded stimulation
   action path supplied through a `StimulationToolSubject`: exact-permit/policy open, all four allowed actions
   emitting exactly once, persistent synthetic provenance with journal-before-emission ordering, and zero
   emission for an out-of-window request and a non-active session.
4. **Reusable gateway contract suite.** `GatewayContractSuite` validates any gateway fixture supplied through a
   `GatewaySubject`: fail-closed protocol negotiation, the ten committed operations, exact-permit arming,
   unarmed zero emission, all four allowed actions, the exclusive generation-bound lease round trip, bounded
   metadata-only observation, bounded framing with over-bound/unknown-method rejection, and bounded counters.
5. **Reusable subject seams.** Each suite is parameterized by a small `*Subject` interface so a different
   conforming implementation is validated without editing the suite.
6. **Reuse evidence.** The provider suite is instantiated against two independently implemented providers; the
   other suites are instantiated against independent subject instances.
7. **Additive build wiring.** Four additive `t033-<kind>` test executables; the runtime-target inventory is
   unchanged and no existing target, test name, label, command, or expected value changes.
8. **Public-safe evidence and governance.** Only stable codes/phase/logical identity/size/timing/outcome are
   recorded; the T033 registers reconcile the accepted T007–T010 models and the REF-002 disposition stays
   `unchanged` with an empty `promoted` list.
9. The T033 repository-owned work products and the T033 package record.

### 2.2 Explicit exclusions (must remain absent from the T033 candidate)

No production runtime source change; no second synthetic provider (T034); no TCP listener or
`AF_INET`/`AF_INET6` socket, DNS, resolver, or TLS use; no external network peer; no legacy binary, legacy
repository, or production workload execution; no change to the accepted T030 contract, T031 gateway, T032
client, or any accepted runtime/test byte; no benchmark, executed sanitizer/static/Doxygen evidence, or
delivery bundle (T035–T040); no new admitted dependency; no compiled or linked gRPC runtime; no ambient/secret
access or dynamic load; no wall-clock-dependent verdict; no rewrite or weakening of an accepted ADR,
requirement, contract, schema, register, target, or test; no promotion of any REF-002 SADS ID beyond its
recorded disposition; no acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T033 |
| --- | --- | --- |
| Second minimal synthetic provider; replaceability/version-rejection/failure-isolation proof | T034 | allocated; T033 provides the reusable provider suite T034 runs |
| gRPC transport runtime linkage | deferred capability gap `T032-GAP-01` | recorded, not worked around |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks, delivery bundle | T035–T040 | allocated |
| Independent Codex review and user acceptance | T039/T041 | allocated; external review and acceptance deferred until backlog `xcom-t030-t034-20260928` completes |

## 3. Stakeholder requirements (`T033-STK-###`)

- **T033-STK-001**: The program **shall** own one reusable provider contract suite that validates any conforming
  provider's identity, capabilities, registration, lifecycle, and failure semantics.
- **T033-STK-002**: The program **shall** own one reusable observer contract suite that validates any conforming
  observation boundary's metadata-only, bounded, and isolation behavior.
- **T033-STK-003**: The program **shall** own one reusable stimulation-tool contract suite that validates any
  conforming guarded stimulation composition's permit, action, provenance, and zero-emission behavior.
- **T033-STK-004**: The program **shall** own one reusable gateway contract suite that validates any conforming
  local-IPC gateway's version, permit, observation, stimulation, lease, and framing behavior with no TCP
  listener and zero items from invalid or expired sessions.
- **T033-STK-005**: T033 **shall** preserve accepted intent and report maturity honestly: the suites are reusable
  and handed to T034; the accepted registers and REF-002 disposition are unchanged with an empty `promoted`
  list; T034–T041 remain allocated.

## 4. Software/engineering requirements (`T033-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Verified" means the repository-owned suite check exists, is deterministic, and passes at the recorded
candidate revision; it is not a deployed-service, remote-tool, or compatibility claim.

### 4.1 Reusable provider suite

- **T033-SR-001 [ubiquitous]**: The provider suite **shall** be parameterized by a `ProviderSubject` seam and
  **shall** validate descriptor identity, `descriptor_compatible()`, nonzero instance identity, explicit
  registration, and duplicate-registration rejection without naming a concrete provider type.
  - Refines: `T033-STK-001`; anchors `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`; `XCOM-DU-007`, `XCOM-SW-CORE-007`.
  - Verification intent: provider checks `P-01`…`P-03`; `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.
- **T033-SR-002 [unwanted]**: If a provider is asked to prepare an unsupported contract version, the suite
  **shall** observe a fail-closed `unsupported_contract_version` rejection before any provider dispatch.
  - Refines: `T033-STK-001`; anchors `XCOM-SYS-FR-022`, `XCOM-SYS-FR-006`; `XCOM-DU-007`.
  - Verification intent: provider check `P-04`.
- **T033-SR-003 [event-driven]**: When the provider suite drives the accepted lifecycle, it **shall** observe
  prepare, activate, submit, bounded reject-new saturation with preserved FIFO, receive, drain, close, and
  bounded reconcile reporting.
  - Refines: `T033-STK-001`; anchors `XCOM-SYS-FR-007`, `XCOM-SYS-FR-010`; `XCOM-DU-007`, `XCOM-SW-CORE-009`.
  - Verification intent: provider checks `P-05`…`P-13`.

### 4.2 Reusable observer suite

- **T033-SR-004 [event-driven]**: When the observer suite attaches a metadata-only tap and an item is published,
  it **shall** observe one normalized record with the exact logical identity, complete source payload size, and
  no payload byte.
  - Refines: `T033-STK-002`; anchors `XCOM-SYS-FR-011`, `XCOM-SYS-FR-012`; `XCOM-CMP-011`.
  - Verification intent: observer checks `O-01`…`O-04`, `O-07`; `T033ObserverContractSuite.AcceptedObservationHubConforms`.
- **T033-SR-005 [event-driven]**: When the observer suite overflows a bounded tap, it **shall** observe the
  declared drop-newest counter increment and a queue that drains exactly once.
  - Refines: `T033-STK-002`; anchors `XCOM-SYS-FR-013`; `XCOM-CMP-011`.
  - Verification intent: observer checks `O-05`, `O-06`, `O-08`.
- **T033-SR-006 [unwanted]**: If an observer detaches or presents a stale handle, the suite **shall** observe a
  rejected handle and **shall not** observe any change to the normal route.
  - Refines: `T033-STK-002`; anchors `XCOM-SYS-FR-014`, `XCOM-SYS-FR-023`; `XCOM-CMP-011`.
  - Verification intent: observer checks `O-09`…`O-11`.

### 4.3 Reusable stimulation-tool suite

- **T033-SR-007 [event-driven]**: When the stimulation-tool suite submits each of the four allowed actions to an
  opened action path, it **shall** observe exactly one emission per action with persistent synthetic provenance
  and journal-before-emission ordering.
  - Refines: `T033-STK-003`; anchors `XCOM-SYS-FR-015`, `XCOM-SYS-FR-017`, `XCOM-SYS-FR-018`, `XCOM-SYS-FR-021`;
    `XCOM-DU-014`…`XCOM-DU-018`.
  - Verification intent: stimulation checks `S-01`, `S-02-0`…`S-02-3`, `S-05`; `T033StimulationToolContractSuite.AcceptedStimulationPathConforms`.
- **T033-SR-008 [unwanted]**: If a request is out of window or targets a non-active session, the suite **shall**
  observe a non-emitting rejection and **shall not** observe any emission.
  - Refines: `T033-STK-003`; anchors `XCOM-SYS-FR-016`, `XCOM-SYS-FR-018`; `XCOM-SW-STIM-002`, `XCOM-SW-STIM-004`.
  - Verification intent: stimulation checks `S-03`, `S-04`.

### 4.4 Reusable gateway suite

- **T033-SR-009 [ubiquitous]**: The gateway suite **shall** validate fail-closed protocol negotiation, the ten
  committed operations, and the supported-major version report without naming a concrete transport.
  - Refines: `T033-STK-004`; anchors `XCOM-SYS-FR-022`, `XCOM-SYS-FR-032`; `XCOM-DU-020`, `XCOM-SW-GW-002`.
  - Verification intent: gateway checks `G-02`…`G-04`; `T033GatewayContractSuite.AcceptedGatewaySessionConforms`.
- **T033-SR-010 [unwanted]**: If a session is not armed, the gateway suite **shall** observe zero emitted items
  and a non-success outcome; arming the exact permit **shall** be observed.
  - Refines: `T033-STK-004`; anchors `XCOM-SYS-FR-016`, `XCOM-SYS-FR-032`; `XCOM-INV-08`.
  - Verification intent: gateway checks `G-05`, `G-08`.
- **T033-SR-011 [event-driven]**: When the gateway suite opens and reads an observation stream, it **shall**
  observe a stream bounded by the configured granted record count.
  - Refines: `T033-STK-004`; anchors `XCOM-SYS-FR-011`, `XCOM-SYS-FR-013`; `XCOM-DU-020`.
  - Verification intent: gateway check `G-09`.
- **T033-SR-012 [event-driven]**: When the gateway suite submits each of the four allowed actions and the lease
  round trip, it **shall** observe an emitted outcome per action and an exclusive active/released lease.
  - Refines: `T033-STK-004`; anchors `XCOM-SYS-FR-015`, `XCOM-SYS-FR-034`; `XCOM-DU-020`.
  - Verification intent: gateway checks `G-01`, `G-06`, `G-07`.
- **T033-SR-013 [unwanted]**: If a frame is over-bound or carries an unknown method, the gateway suite
  **shall** observe a fail-closed framing rejection; the suite **shall** also observe bounded counters with an
  explicit evidence-incomplete count.
  - Refines: `T033-STK-004`; anchors `XCOM-SYS-FR-007`, `XCOM-SYS-FR-021`; `XCOM-DU-020`.
  - Verification intent: gateway checks `G-10`, `G-11`.

### 4.5 Reuse, evidence, and governance

- **T033-SR-014 [ubiquitous]**: The four suites **shall** be reusable across conforming implementations or
  instances supplied through their subject seams; the same suite body **shall** be instantiated at least twice
  per suite **without** editing the suite header.
  - Refines: `T033-STK-005`; anchors `XCOM-SYS-FR-030`, `XCOM-SYS-FR-026`; `XCOM-DU-007`, `XCOM-DU-020`.
  - Verification intent: the four `SuiteIsReusable…` cases.
- **T033-SR-015 [ubiquitous]**: Build wiring **shall** be additive — four new `t033-<kind>` test executables in
  `src/xverse/xcom/CMakeLists.txt` — with any inventory change declared explicitly and **no** existing target,
  test name, label, command, or expected value changed; committed files and bounded logs **shall not** contain a
  payload byte, permit content, secret, private address, or host path.
  - Refines: `T033-STK-005`; anchors `XCOM-SYS-FR-027`, `XCOM-SYS-FR-030`; T012 subtree build contract; Constitution VII.
  - Verification intent: changed-path/discovery inspection; public-safety inspection (CHK-19, NEG-08).
- **T033-SR-016 [ubiquitous]**: T033 **shall** reconcile with the T007 ownership register, the T008 register, the
  T009 architecture model, and the T010 unit design without rewriting or weakening them; **shall** keep the
  REF-002 disposition `unchanged` with an empty `promoted` list; **shall** record honestly that the reusable
  suites are implemented by T033 while T034–T041 remain allocated; and **shall** satisfy the deterministic
  Phase 7 gate and the Doxygen documentation obligation for the changed test units.
  - Refines: `T033-STK-005`; anchors `XCOM-SYS-FR-029`, `XCOM-SYS-FR-035`; ADR-0020; Constitution VII, IX, X.
  - Verification intent: register validators; file-block inspection; the gate (CHK-03, CHK-21, CHK-22).

## 5. Requirement-to-accepted-anchor traceability

| T033 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T033-STK-001 | `XCOM-SW-CORE-007`, `XCOM-SW-CORE-009` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | II, VII |
| T033-STK-002 | `XCOM-SW-OBS-001`…`-004` | `XCOM-SYS-FR-011/013/014/023` | FR-011–FR-014, FR-023 | IX |
| T033-STK-003 | `XCOM-SW-STIM-001/003/004/007` | `XCOM-SYS-FR-015/017/018/021` | FR-015, FR-017, FR-018, FR-021 | IX |
| T033-STK-004 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-022/032/034` | FR-022, FR-032, FR-034 | SC-011, IX |
| T033-STK-005 | ADR-0020; Constitution VII/IX/X | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX, X |
| T033-SR-001 | `XCOM-SW-CORE-007` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | IX |
| T033-SR-002 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-022/006` | FR-022, FR-006 | IX |
| T033-SR-003 | `XCOM-SW-CORE-009` | `XCOM-SYS-FR-007/010` | FR-007, FR-010 | IX |
| T033-SR-004 | `XCOM-SW-OBS-002` | `XCOM-SYS-FR-011/012` | FR-011, FR-012 | IX |
| T033-SR-005 | `XCOM-SW-OBS-003` | `XCOM-SYS-FR-013` | FR-013 | IX |
| T033-SR-006 | `XCOM-SW-OBS-004` | `XCOM-SYS-FR-014/023` | FR-014, FR-023 | IX |
| T033-SR-007 | `XCOM-SW-STIM-003/007` | `XCOM-SYS-FR-015/017/018/021` | FR-015, FR-017, FR-018, FR-021 | IX |
| T033-SR-008 | `XCOM-SW-STIM-002/004` | `XCOM-SYS-FR-016/018` | FR-016, FR-018 | VII, IX |
| T033-SR-009 | `XCOM-SW-GW-001/002` | `XCOM-SYS-FR-022/032` | FR-022, FR-032 | IX |
| T033-SR-010 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-016/032` | FR-016, FR-032 | VII, IX |
| T033-SR-011 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-011/013` | FR-011, FR-013 | IX |
| T033-SR-012 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-015/034` | FR-015, FR-034 | IX |
| T033-SR-013 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-007/021` | FR-007, FR-021 | IX |
| T033-SR-014 | `XCOM-SW-CORE-007/009` | `XCOM-SYS-FR-026/030` | FR-026, FR-030 | IX |
| T033-SR-015 | `XCOM-SW-CORE-009` | `XCOM-SYS-FR-027/030` | FR-027, FR-030 | VII, X |
| T033-SR-016 | ADR-0020; Constitution | `XCOM-SYS-FR-029/035` | FR-029, FR-035 | VII, IX, X |

Each accepted T033 software requirement refines at least one `T033-STK-###` stakeholder requirement through an
explicit `refines` link in `engineering/trace/links.json`. `T033-VS-ACCUMULATED` validates `T033-SR-001`…`-016`
and names the eight `t033-` cases that the trusted validation measure selects and executes.

The repair-pass successor adds nine `implemented_by` links (`T033-L-0199`…`T033-L-0207`) so that every
`tests/xcom/contract_suites/*` file's `@par Traceability` range is a subset of the T033 requirements whose
`implemented_by` links target that file; the mapping and its justification are recorded in `implementation.md` §13.
No requirement id, statement, acceptance criterion, disposition, or validation scenario changed.

The second repair pass corrects the `T033-SR-007` verification-intent range in §4.3 from
`S-01`…`S-03`, `S-05` to the action-emission checks `S-01`, `S-02-0`…`S-02-3`, `S-05`, so that `S-03` is owned only
by `T033-SR-008`. The corrected sets are disjoint and equal the `T033-SR-007`/`T033-SR-008` rows of
`verification-plan.md` §4/§5 (`CHK-09`, `CHK-10`) and `implementation.md` §8. No requirement id, statement,
acceptance criterion, disposition, validation scenario, or check definition changed.

## 6. REF-002 disposition

T033 owns no REF-002 SADS ID and promotes none. `XVE-SYS-0141` remains the accepted **deferred** target
("protocol/provider capabilities"); the reusable suites are recorded as a **partial contribution** to the
deferred target and are **not** promoted; `XVE-SYS-0142`–`0158` retain their accepted dispositions. The
capability `ref002.disposition` stays `unchanged` (T033-SR-016). No allocated, deferred, architectural-target,
or superseded SADS requirement is reported as implemented.

## 7. Affected paths

### 7.1 Paths the T033 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `tests/xcom/contract_suites/suite_support.hpp` | add | shared bounded report vocabulary |
| `tests/xcom/contract_suites/provider_contract_suite.hpp` | add | reusable provider suite + subject seam |
| `tests/xcom/contract_suites/observer_contract_suite.hpp` | add | reusable observer suite + subject seam |
| `tests/xcom/contract_suites/stimulation_tool_contract_suite.hpp` | add | reusable stimulation-tool suite + subject seam |
| `tests/xcom/contract_suites/gateway_contract_suite.hpp` | add | reusable gateway suite + subject seam |
| `tests/xcom/contract_suites/{provider,observer,stimulation_tool,gateway}_suite_tests.cpp` | add | `t033-<kind>` drivers |
| `src/xverse/xcom/CMakeLists.txt` | edit (additive) | four `t033-<kind>` test executables; no existing target/label/value changes |
| `engineering/project.json` | edit | current task T033 and accepted baseline `2fd395e39e44e1f6fe9547998b47499d996b1756` |
| `engineering/requirements/T033-STK-00{1..5}.json`, `T033-SR-0{01..16}.json` | add | current-task requirement records |
| `engineering/architecture/components/T033-SR-0{01..16}-CMP.json` | add | current-task component allocations |
| `engineering/unit-specifications/T033-SR-0{01..16}-U.json` | add | current-task unit specifications |
| `engineering/validation/scenarios/T033-VS-ACCUMULATED.json` | add | current-task validation scenario |
| `engineering/trace/links.json` | edit (implementation) | additive T033 trace links and inherited digest refresh |
| `engineering/verification/measures/{unit,integration,validation}.json` | edit (implementation) | refreshed to the discovered T033 cases |
| `engineering/stage-results/*.json` | edit (implementation) | inherited artifact-digest refresh when `src/xverse/xcom/CMakeLists.txt` changes |
| `docs/engineering/xcom/t033/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md` | add | this work-product set |
| `docs/engineering/xcom/t033/internal-review.json` | add | internal-review record |
| `reports/review-index.md` | edit | T033 candidate section appended |
| `specs/007-xcom-core/tasks.md` | edit | one-line T033 checkbox, **implementation stage only** |
| `reports/xcom-queue/t033-package.json` | add | implementation-stage package record |

### 7.2 Consumed read-only (not changed by T033)

`proto/xverse/xcom/v1/tool_gateway.proto`; the accepted `src/xverse/xcom/**` runtime sources, headers, and
library targets; every accepted test under `tests/xcom/**` other than the new T033 suites; the accepted T016
`tests/xcom/core_matrix/test_support.hpp`, T024 `tests/xcom/observation/integration/test_support.hpp`, T029
`tests/xcom/stimulation_matrix/test_support.hpp`, and T031 `tests/xcom/tool_gateway/gateway_support.hpp`
fixtures; `docs/engineering/xcom/task-ownership.*`; `docs/engineering/xcom/t00{7,8,9,10}/**`;
`docs/engineering/xcom/t0{01..32}/**`; `docs/engineering/xcom/build-environment.md`;
`docs/engineering/xcom/dependency-lock.md`; and `specs/007-xcom-core/**` (other than the T033 checkbox).

### 7.3 Explicitly not implemented by T033

The second synthetic provider and its replacement/version-rejection/failure-isolation proof (T034), the
benchmark/sanitizer/static/Doxygen/delivery tasks (T035–T040), the gRPC transport runtime linkage
(`T032-GAP-01`), and any change to the accepted T030 contract, T031 gateway, or T032 client. External Codex
review and user acceptance remain T039/T041 and are deferred until the ordered backlog
`xcom-t030-t034-20260928` completes.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T033-GAP-01 — reuse is proven for provider implementations and for suite instances.** The provider suite is
  instantiated against two independently implemented providers; the observer/stimulation-tool/gateway suites are
  instantiated against independent instances of the accepted implementations. No third-party implementation
  claim is made; T034 owns the production second-provider proof.
- **T033-GAP-02 — gRPC transport runtime deferred.** The T011 admitted envelope still cannot link the gRPC
  runtime (`T032-GAP-01`); the gateway suite validates the accepted local-IPC framing, not a gRPC server.
- **T033-GAP-03 — generated-code documentation.** The generated Protocol Buffers documentation policy remains
  `DOX-GAP-02` (T037); T033 documents its hand-written suite headers only.
- **T033-GAP-04 — no deployed-service or compatibility claim.** The suites are bounded prototypes validated with
  owned local fixtures; they make no production-readiness or parity claim.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| Second minimal synthetic provider; replaceability/version-rejection/failure-isolation proof | T034 |
| gRPC transport runtime envelope | deferred capability gap `T032-GAP-01` |
| Executed sanitizer/static/Doxygen/benchmark and delivery bundle | T035–T040 |
| Independent Codex review and user acceptance | T039/T041 |

### 8.3 Open items

- **T033-OPEN-01 — inherited provenance refresh.** Editing `src/xverse/xcom/CMakeLists.txt` invalidates the
  inherited `implemented_by` target digests in `engineering/trace/links.json` and the declared
  `links.json`/`CMakeLists.txt` digests in `engineering/stage-results/*.json`; the implementation stage refreshes
  those inherited digests without changing any requirement, link identity, relation, or stage result.
- **T033-OPEN-02 — suite-only scope.** T033 authors only test suites and additive build registration; the
  runtime-target inventory `XVERSE_XCOM_RUNTIME_TARGETS` is unchanged.
- **T033-OPEN-03 — new test path not previously declared.** The reusable suites live under the new
  `tests/xcom/contract_suites/` path owned by the T033 components; no accepted T009/T010 artifact path
  transitions, because no accepted planned path becomes present.

## 9. Definition of done (requirements view)

T033 is done for a candidate revision when: every §4 requirement has at least one named check; the four reusable
suites are parameterized by their subject seams and are instantiated at least twice each; the provider suite
passes against two independently implemented providers; all eight `t033-` cases pass in the offline admitted
build; the additive build wiring preserves every existing target/label/value and the runtime-target inventory;
`XCOM-SW-CORE-007`/`XCOM-SW-CORE-009`/`XCOM-SW-GW-002` remain unchanged accepted text; the register validators
pass with REF-002 `unchanged` and nothing promoted; the deterministic Phase 7 gate passes; and a separate
DeepSeek internal review records its findings before any repair. This does not constitute user acceptance, which
remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T033-STK-001 | CHK-01, CHK-03, CHK-05 |
| T033-STK-002 | CHK-06, CHK-07, CHK-08 |
| T033-STK-003 | CHK-09, CHK-10 |
| T033-STK-004 | CHK-11, CHK-12, CHK-13, CHK-14 |
| T033-STK-005 | CHK-15, CHK-16, CHK-21, CHK-22 |
| T033-SR-001 | CHK-01, CHK-02 |
| T033-SR-002 | CHK-04 |
| T033-SR-003 | CHK-05 |
| T033-SR-004 | CHK-06, CHK-07 |
| T033-SR-005 | CHK-08 |
| T033-SR-006 | CHK-07, CHK-08 |
| T033-SR-007 | CHK-09 |
| T033-SR-008 | CHK-10 |
| T033-SR-009 | CHK-11, CHK-12 |
| T033-SR-010 | CHK-12 |
| T033-SR-011 | CHK-13 |
| T033-SR-012 | CHK-14 |
| T033-SR-013 | CHK-11, CHK-14 |
| T033-SR-014 | CHK-15 |
| T033-SR-015 | CHK-16, CHK-19, CHK-20 |
| T033-SR-016 | CHK-03, CHK-21, CHK-22 |
