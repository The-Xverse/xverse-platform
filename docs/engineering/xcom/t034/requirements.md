# T034 Requirements — Second Minimal Synthetic Provider and Replaceability / Version-Rejection / Failure-Isolation Proof

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T034 (capability 007, slice `T-CORE`/GW) |
| Task title | Add a second minimal synthetic provider implementation to prove replaceability and version rejection; verify adapter failures do not affect unrelated routes |
| Stage / role | plan → requirements |
| Revision | 1 (second-provider replaceability slice) |
| Baseline revision | `f63491101aed1c4f7db57fa7c506ad5c0510038f` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC002`, `ACC004`, `ACC005`, `ACC006`, `ACC007`, `ACC010`, `ACC011`, `ACC014`, `ACC015`); `ADR-0016` (subsystem naming); `ADR-0018` (platform-first); `ADR-0019` (X-COM observation/stimulation boundary); `ADR-0020` (repository-owned work products and exact-candidate evidence) |
| Owning slice | `T-CORE` (T007 ownership register); T034 is the second-provider replaceability task of the `T-CORE`/GW family |
| Predecessors | T033 accepted reusable provider/observer/stimulation-tool/gateway contract suites (`tests/xcom/contract_suites/**`); T032 accepted separate-process synthetic client (`src/xverse/xcom/fixtures/synthetic_tool.cpp`); T031 accepted bounded local-IPC-only gateway; T030 accepted versioned `XCOM-XLC-002` contract; T015/T016 accepted provider boundary, loopback provider, and core matrix; T011 admitted offline envelope; T012 subtree CMake/CTest contract |
| Successor tasks | T035–T041 (evidence, review, acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-CORE` slice; T034 exclusive paths `docs/engineering/xcom/t034/`, `reports/xcom-queue/t034-package.json`); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-CORE-003`, `-004`, `-005`, `-007`, `-009`); `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-006` provider boundary/composition, `XCOM-CMP-007` owned synthetic provider that proves replaceability, `XCOM-CMP-011` synthetic sink/tools); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-007` provider boundary and composition, `XCOM-DU-008` owned synthetic provider) |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production change
and does not implement, accept, or integrate the candidate. The T034 task entry in `specs/007-xcom-core/tasks.md`
is the authorized scope:

> T034 — Add a second minimal synthetic provider implementation to prove replaceability and version
> rejection; verify adapter failures do not affect unrelated routes.

It realizes the accepted provider contract statement in `specs/007-xcom-core/contracts/provider.md`
("remain replaceable by another conforming provider"; "reject unsupported semantics before activation") and
the accepted User Story 4 independent test in `specs/007-xcom-core/spec.md` ("A second synthetic provider and
tool adapter pass the same contract suite and are rejected when they misreport capability, violate ownership,
or emit an unsupported contract version") together with its acceptance scenario 3 ("Given an observer or
stimulation adapter failure, When X-COM isolates it, Then unrelated routes remain bounded and their state
stays observable").

### 1.1 Authority statement

T034 owns the **second minimal synthetic provider implementation and its replaceability, version-rejection,
and failure-isolation proof**. It provides:

- a second owned synthetic provider implementation under `src/xverse/xcom/fixtures/synthetic_provider.hpp`
  and `src/xverse/xcom/fixtures/synthetic_provider.cpp` (`SyntheticProvider`), independently written against
  the accepted `CommunicationProvider` boundary with its own finite route/queue storage;
- three additive `t034-<kind>` GoogleTest drivers under `tests/xcom/contract_suites/` that reuse the accepted
  T033 `ProviderContractSuite` **unchanged** through a new `ProviderSubject` adapter;
- the replaceability, version/capability rejection, and unrelated-route isolation evidence.

The `T008` requirements register allocates no software requirement exclusively to T034; T034 therefore realizes
its per-task projection of the accepted provider software requirements that name replaceability and version
rejection. It records `XCOM-SW-CORE-003` (reject incompatible before traffic), `XCOM-SW-CORE-004` (bounded
queue/ordering semantics), `XCOM-SW-CORE-005` (explicit provider registration and exact-handle ownership),
`XCOM-SW-CORE-007` (owned loopback/synthetic provider with no discovery/legacy access), and `XCOM-SW-CORE-009`
(owned-loopback conformance and negative-case suite) as the accepted anchors it contributes to. The register
rows are not edited (T026–T033 precedent).

**Recorded design decision (`T034-DD-01`).** The second provider is validated by the *same* reusable provider
suite body that the accepted owned loopback provider passes. T034 does not author a second conformance
definition: it supplies a new `ProviderSubject` adapter to the unchanged
`tests/xcom/contract_suites/provider_contract_suite.hpp`. A different conforming provider is thereby validated
by the accepted suite, which is exactly the replaceability claim the accepted contract makes.

**Provider-only, additive boundary.** T034 authors one fixture provider and additive tests only. It authors no
change to the accepted provider boundary (`provider.hpp`), the owned loopback provider
(`loopback_provider.hpp`/`.cpp`), the accepted T030 contract, T031 gateway, T032 client, or T033 suites, and no
benchmark/sanitizer/static/Doxygen/delivery bundle (T035–T040).

It does **not** redesign the accepted architecture, change a functional requirement, success criterion, ADR,
schema, XDL profile, or contract; modify any accepted predecessor byte under `src/`, `tests/`, `xdl/`, or
`docs/engineering/xcom/t0{07..33}/`; add an admitted dependency; link a gRPC runtime; weaken an accepted
`T016-`/`T030-`/`T031-`/`T032-`/`T033-` test; or accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, data model,
the T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design, the
constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is reported rather
than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T034)

1. **Second minimal synthetic provider.** A new `SyntheticProvider` implementing the accepted
   `CommunicationProvider` interface with independently written finite route/queue storage, its own nonzero
   instance identity, and a `descriptor_compatible()` predicate that admits only descriptors within its
   finite storage.
2. **Replaceability proof.** The unchanged accepted T033 `ProviderContractSuite` is run against the second
   provider through a new `ProviderSubject`; every provider check `P-01`…`P-13` passes.
3. **Bounded capability and saturation behavior.** For the second provider, a reject-new queue of capacity one
   accepts the first item, rejects the second with `queue_saturated` without losing the first, and reports a
   bounded active route state.
4. **Bounded lifecycle.** Prepare, activate, submit, receive, drain, close, and bounded reconcile complete for
   the second provider with no item lost or duplicated.
5. **Version rejection.** A second-provider instance that declares a provider-contract version other than the
   accepted `1.0.0` is rejected fail-closed at explicit registration with `unsupported_contract_version`; a
   route request naming an unsupported version is rejected before activation without issuing a provider-route
   handle.
6. **Capability rejection.** A provider that claims a capability its bounded storage cannot honor is rejected
   at registration with `invalid_descriptor`; a route that requests an unsupported capability is rejected
   before activation with the matching stable `unsupported_*` outcome.
7. **Zero emission on rejection.** Every rejection path emits no item and does not mutate unrelated operational
   state.
8. **Failure isolation.** When a provider route or adapter on one route fails or is rejected, an unrelated
   already-active route remains active, bounded, and observable, and still accepts and returns its exact items.
9. **Additive build wiring.** Three additive `t034-<kind>` test executables and the second-provider fixture
   source compiled into them; the runtime-target inventory is unchanged and no existing target, test name,
   label, command, or expected value changes.
10. **Public-safe evidence and governance.** Only stable codes/phase/logical identity/size/timing/outcome are
    recorded; the T034 registers reconcile the accepted T007–T010 models and the REF-002 disposition stays
    `unchanged` with an empty `promoted` list.
11. The T034 repository-owned work products and the T034 package record.

### 2.2 Explicit exclusions (must remain absent from the T034 candidate)

No modification of the accepted provider boundary, composition, loopback provider, T030 contract, T031 gateway,
T032 client, or any accepted `T0xx-` test; no TCP listener or `AF_INET`/`AF_INET6` socket, DNS, resolver, or
TLS use; no external network peer; no legacy binary, legacy repository, or production workload execution; no
second conformance definition (the T033 suite body is consumed unchanged); no benchmark, executed
sanitizer/static/Doxygen evidence, or delivery bundle (T035–T040); no new admitted dependency; no compiled or
linked gRPC runtime; no ambient/secret access or dynamic load; no wall-clock-dependent verdict; no rewrite or
weakening of an accepted ADR, requirement, contract, schema, register, target, or test; no promotion of any
REF-002 SADS ID beyond its recorded disposition; no acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T034 |
| --- | --- | --- |
| Independent Codex review and user acceptance | T039/T041 | allocated; external review and acceptance deferred until backlog `xcom-t030-t034-20260928` completes |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks, delivery bundle | T035–T040 | allocated |
| gRPC transport runtime linkage | deferred capability gap `T032-GAP-01` | recorded, not worked around; T034 uses in-process providers only |

## 3. Stakeholder requirements (`T034-STK-###`)

- **T034-STK-001**: Before provider replaceability is claimed, the program **shall** own one second minimal
  synthetic provider implementation that realizes the accepted `CommunicationProvider` boundary with
  independently written bounded storage and no change to the accepted provider contract, composition, or
  loopback implementation.
- **T034-STK-002**: The second synthetic provider **shall** be validated by the same reusable provider contract
  suite that the accepted owned loopback provider passes, with the suite body unchanged.
- **T034-STK-003**: A provider or route that misreports or requests an unsupported contract version or an
  unsupported capability **shall** be rejected fail-closed before activation and before any traffic or item is
  emitted.
- **T034-STK-004**: When a provider or adapter on one route fails or is rejected, it **shall not** change the
  activity, bounds, or observable state of any unrelated route.
- **T034-STK-005**: T034 **shall** preserve accepted intent and report maturity honestly: the accepted registers
  and the REF-002 disposition stay `unchanged` with an empty `promoted` list, build wiring is additive, the
  change is public-safe and documented, and T035–T041 remain allocated.

## 4. Software/engineering requirements (`T034-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Verified" means the repository-owned test case or inspection exists, is deterministic, and passes at
the recorded candidate revision; it is not a deployed-service, remote-tool, or compatibility claim.

### 4.1 Second provider implementation and replaceability

- **T034-SR-001 [ubiquitous]**: The second synthetic provider **shall** implement the accepted
  `CommunicationProvider` interface with independently written bounded route/queue storage, a valid nonzero
  instance identity distinct from the loopback provider, and a `descriptor_compatible()` predicate that admits
  only descriptors within its finite storage, without changing any accepted provider, composition, or loopback
  byte.
  - Refines: `T034-STK-001`; anchors `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`; `XCOM-SW-CORE-005`,
    `XCOM-SW-CORE-007`; `XCOM-DU-007`, `XCOM-DU-008`, `XCOM-CMP-006`, `XCOM-CMP-007`.
  - Verification intent: `T034SecondProviderSuite.ProviderIsIndependentOfLoopback`.
- **T034-SR-002 [event-driven]**: When the unchanged accepted reusable `ProviderContractSuite` (T033) is run
  against the second synthetic provider through a `ProviderSubject`, it **shall** report `ok()` with every
  provider check `P-01`…`P-13` passing.
  - Refines: `T034-STK-002`; anchors `XCOM-SYS-FR-028`, `XCOM-SYS-FR-030`; `XCOM-SW-CORE-007`,
    `XCOM-SW-CORE-009`; `XCOM-DU-007`, `XCOM-DU-008`, `XCOM-CMP-007`.
  - Verification intent: `T034SecondProviderSuite.ReusedProviderContractSuitePasses`.
- **T034-SR-003 [event-driven]**: When the second provider is driven over a reject-new queue of capacity one,
  it **shall** accept the first item, reject the second with `queue_saturated` without dropping the first, and
  report bounded active route state with `queued_items()==1` and `queue_capacity()==1`.
  - Refines: `T034-STK-001`; anchors `XCOM-SYS-FR-007`; `XCOM-SW-CORE-004`, `XCOM-SW-CORE-009`;
    `XCOM-DU-008`.
  - Verification intent: `T034SecondProviderSuite.BoundedCapabilitiesAndSaturation`.
- **T034-SR-004 [event-driven]**: When the second provider is driven through prepare, activate, submit,
  receive, drain, and close, it **shall** report `prepared`, `activated`, `accepted`, `received`, `draining`,
  and `closed` with a bounded reconcile outcome and no lost or duplicated item.
  - Refines: `T034-STK-001`; anchors `XCOM-SYS-FR-010`; `XCOM-SW-CORE-005`; `XCOM-DU-007`, `XCOM-DU-008`.
  - Verification intent: `T034SecondProviderLifecycle.CompletesFullBoundedLifecycle`.

### 4.2 Fail-closed version and capability rejection

- **T034-SR-005 [unwanted]**: If a second-provider instance declares a provider-contract version other than
  the accepted `1.0.0`, explicit registration **shall** be rejected with `unsupported_contract_version` before
  any route preparation or activation.
  - Refines: `T034-STK-003`; anchors `XCOM-SYS-FR-006`, `XCOM-SYS-FR-022`; `XCOM-SW-CORE-003`; `XCOM-DU-007`.
  - Verification intent: `T034VersionRejection.MisreportedContractVersionRejectedAtRegistration`.
- **T034-SR-006 [unwanted]**: If a route request names a provider-contract version other than the registered
  provider's declared version, preparation **shall** be rejected with `unsupported_contract_version` before
  activation and without issuing a provider-route handle.
  - Refines: `T034-STK-003`; anchors `XCOM-SYS-FR-006`; `XCOM-SW-CORE-003`; `XCOM-DU-007`.
  - Verification intent: `T034VersionRejection.UnsupportedRequestedVersionRejectedBeforeActivation`.
- **T034-SR-007 [unwanted]**: If a provider claims a capability its bounded storage cannot honor, registration
  **shall** fail with `invalid_descriptor`; if a route requests an unsupported capability, preparation **shall**
  fail with the matching stable `unsupported_*` outcome before activation.
  - Refines: `T034-STK-003`; anchors `XCOM-SYS-FR-006`; `XCOM-SW-CORE-003`; `XCOM-DU-007`.
  - Verification intent: `T034VersionRejection.MisreportedCapabilityRejectedAtRegistration`,
    `T034VersionRejection.UnsupportedRequestedCapabilityRejectedBeforeActivation`.
- **T034-SR-008 [unwanted]**: If the second provider fails a prepare or submit operation, the operation
  **shall** report the configured stable failure outcome, mutate no unrelated state, and emit no item.
  - Refines: `T034-STK-004`; anchors `XCOM-SYS-FR-010`; `XCOM-SW-CORE-005`; `XCOM-DU-007`.
  - Verification intent: `T034FailureIsolation.ProviderFailureYieldsStableOutcomeNoEmission`.

### 4.3 Failure isolation and governance

- **T034-SR-009 [unwanted]**: When a provider route or adapter on one route fails or is rejected, every
  unrelated already-active route **shall** remain active with unchanged queue bounds, still accept and return
  its exact items, and keep its provider-route state observable.
  - Refines: `T034-STK-004`; anchors `XCOM-SYS-FR-010`, `XCOM-SYS-FR-014`; `XCOM-SW-CORE-005`;
    `XCOM-DU-007`.
  - Verification intent: `T034FailureIsolation.UnrelatedRouteRemainsActiveAndBounded`,
    `T034FailureIsolation.UnrelatedRouteStateStaysObservable`,
    `T034FailureIsolation.RejectedAdapterLeavesUnrelatedRouteIntact`.
- **T034-SR-010 [ubiquitous]**: The T033 reusable provider suite header
  `tests/xcom/contract_suites/provider_contract_suite.hpp` and its `ProviderSubject` seam **shall** be consumed
  without modification; the second provider **shall** be validated through a new subject adapter only.
  - Refines: `T034-STK-002`; anchors `XCOM-SYS-FR-030`; `XCOM-SW-CORE-009`; `XCOM-DU-007`, `XCOM-CMP-007`.
  - Verification intent: contributory `T034SecondProviderSuite.ReusedProviderContractSuitePasses`; the
    unchanged-header inspection.
- **T034-SR-011 [ubiquitous]**: Build wiring **shall** be additive — new `t034-<kind>` test executables plus the
  second-provider fixture source — with any runtime-target inventory change declared explicitly and **no**
  existing target, test name, label, command, or expected value changed.
  - Refines: `T034-STK-005`; anchors `XCOM-SYS-FR-030`; `XCOM-SW-CORE-009`; T012 subtree build contract.
  - Verification intent: contributory `T034SecondProviderSuite.BoundedCapabilitiesAndSaturation`; the
    build/discovery inspection.
- **T034-SR-012 [ubiquitous]**: Committed files, bounded logs, and evidence **shall not** contain a payload
  byte, permit content, secret, private address, or host path, and every changed unit **shall** carry the X-COM
  Doxygen file block (`@file`, `@brief`, `@ownership`, `@lifetime`, `@thread_safety`, `@failure`,
  `@par Traceability`).
  - Refines: `T034-STK-005`; anchors `XCOM-SYS-FR-027`, `XCOM-SYS-FR-029`; ADR-0020.
  - Verification intent: contributory `T034FailureIsolation.UnrelatedRouteRemainsActiveAndBounded`; the
    public-safety and file-block inspection.
- **T034-SR-013 [ubiquitous]**: T034 **shall** reconcile with the T007 ownership register, the T008 register,
  the T009 architecture model, and the T010 unit design without rewriting or weakening them; **shall** keep the
  REF-002 disposition `unchanged` with an empty `promoted` list; **shall** record the second provider as
  implemented by T034 while T035–T041 remain allocated; and **shall** satisfy the deterministic Phase 7 gate
  and the required trace links.
  - Refines: `T034-STK-005`; anchors `XCOM-SYS-FR-030`, `XCOM-SYS-FR-035`; ADR-0020; Constitution VII, IX, X.
  - Verification intent: contributory `T034SecondProviderSuite.ProviderIsIndependentOfLoopback`; the register
    validators, the deterministic gate, and trace validation.
- **T034-SR-014 [unwanted]**: The second provider and its tests **shall** use only in-process owned storage and
  the accepted offline toolchain; they **shall not** create a TCP listener or `AF_INET`/`AF_INET6` socket, use
  DNS, a resolver, or TLS, contact an external peer, or execute a legacy binary or production workload.
  - Refines: `T034-STK-001`; anchors `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`; `XCOM-SW-CORE-007`;
    Constitution VII.
  - Verification intent: contributory `T034SecondProviderSuite.ReusedProviderContractSuitePasses`; the
    forbidden-API/public-safety inspection.

## 5. Requirement-to-accepted-anchor traceability

| T034 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T034-STK-001 | `XCOM-SW-CORE-005/007` | `XCOM-SYS-FR-026/028` | FR-026, FR-028, contracts/provider.md | VII, IX |
| T034-STK-002 | `XCOM-SW-CORE-007/009` | `XCOM-SYS-FR-028/030` | FR-028, FR-030, US4 independent test | IX |
| T034-STK-003 | `XCOM-SW-CORE-003` | `XCOM-SYS-FR-006/022` | FR-006, FR-022 | IX |
| T034-STK-004 | `XCOM-SW-CORE-005` | `XCOM-SYS-FR-010/014` | FR-010, FR-014 | IX |
| T034-STK-005 | ADR-0020; Constitution VII/IX/X | `XCOM-SYS-FR-027/029/030/035` | FR-027, FR-029, FR-030, FR-035 | VII, IX, X |
| T034-SR-001 | `XCOM-SW-CORE-005/007` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | IX |
| T034-SR-002 | `XCOM-SW-CORE-007/009` | `XCOM-SYS-FR-028/030` | FR-028, FR-030 | IX |
| T034-SR-003 | `XCOM-SW-CORE-004/009` | `XCOM-SYS-FR-007` | FR-007 | IX |
| T034-SR-004 | `XCOM-SW-CORE-005` | `XCOM-SYS-FR-010` | FR-010 | IX |
| T034-SR-005 | `XCOM-SW-CORE-003` | `XCOM-SYS-FR-006/022` | FR-006, FR-022 | IX |
| T034-SR-006 | `XCOM-SW-CORE-003` | `XCOM-SYS-FR-006` | FR-006 | IX |
| T034-SR-007 | `XCOM-SW-CORE-003` | `XCOM-SYS-FR-006` | FR-006 | IX |
| T034-SR-008 | `XCOM-SW-CORE-005` | `XCOM-SYS-FR-010` | FR-010 | IX |
| T034-SR-009 | `XCOM-SW-CORE-005` | `XCOM-SYS-FR-010/014` | FR-010, FR-014 | IX |
| T034-SR-010 | `XCOM-SW-CORE-009` | `XCOM-SYS-FR-030` | FR-030 | IX |
| T034-SR-011 | `XCOM-SW-CORE-009` | `XCOM-SYS-FR-030` | FR-030 | VII, X |
| T034-SR-012 | ADR-0020 | `XCOM-SYS-FR-027/029` | FR-027, FR-029 | IX, X |
| T034-SR-013 | ADR-0020; Constitution | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX, X |
| T034-SR-014 | `XCOM-SW-CORE-007` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | VII, IX |

Each accepted T034 software requirement refines at least one `T034-STK-###` stakeholder requirement through an
explicit `refines` link in `engineering/trace/links.json` at the implementation stage. `T034-VS-ACCUMULATED`
validates `T034-SR-001`…`-014` and names the thirteen `t034-` cases that the trusted validation measure selects
and executes.

## 6. REF-002 disposition

T034 owns no REF-002 SADS ID and promotes none. `XVE-SYS-0141` remains the accepted **deferred** target
("protocol/provider capabilities"); the second-provider replaceability evidence is recorded as a **partial
contribution** to the deferred target and is **not** promoted; `XVE-SYS-0142`–`0158` retain their accepted
dispositions. The capability `ref002.disposition` stays `unchanged` (T034-SR-013). No allocated, deferred,
architectural-target, or superseded SADS requirement is reported as implemented.

## 7. Affected paths

### 7.1 Paths the T034 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/fixtures/synthetic_provider.hpp` | add | the second minimal synthetic provider public interface (`SyntheticProvider`) |
| `src/xverse/xcom/fixtures/synthetic_provider.cpp` | add | the independently written bounded implementation |
| `src/xverse/xcom/CMakeLists.txt` | edit (additive) | compiles the fixture source into three `t034-<kind>` test executables; no existing target/label/value changed; runtime-target inventory unchanged |
| `tests/xcom/contract_suites/second_provider_suite_tests.cpp` | add | `t034-replaceability` driver reusing the unchanged T033 `ProviderContractSuite` |
| `tests/xcom/contract_suites/second_provider_version_tests.cpp` | add | `t034-version` version/capability rejection driver |
| `tests/xcom/contract_suites/second_provider_isolation_tests.cpp` | add | `t034-isolation` unrelated-route isolation driver |
| `engineering/project.json` | edit | current task T034 and accepted baseline `f63491101aed1c4f7db57fa7c506ad5c0510038f` |
| `engineering/requirements/T034-STK-00{1..5}.json`, `T034-SR-0{01..14}.json` | add | current-task requirement records |
| `engineering/architecture/components/T034-SR-0{01..14}-CMP.json` | add | current-task component allocations |
| `engineering/unit-specifications/T034-SR-0{01..14}-U.json` | add | current-task unit specifications |
| `engineering/validation/scenarios/T034-VS-ACCUMULATED.json` | add | current-task validation scenario |
| `engineering/trace/links.json` | edit (implementation) | additive T034 trace links and inherited digest refresh |
| `engineering/verification/measures/{unit,integration,validation}.json` | edit (implementation) | refreshed to the discovered thirteen T034 cases |
| `engineering/stage-results/*.json` | edit (implementation) | inherited artifact-digest refresh when `src/xverse/xcom/CMakeLists.txt` changes |
| `docs/engineering/xcom/t034/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md` | add | this work-product set |
| `docs/engineering/xcom/t034/internal-review.json` | add | internal-review record |
| `reports/review-index.md` | edit | T034 candidate section appended |
| `specs/007-xcom-core/tasks.md` | edit | one-line T034 checkbox, **implementation stage only** |
| `reports/xcom-queue/t034-package.json` | add | implementation-stage package record |

### 7.2 Consumed read-only (not changed by T034)

`tests/xcom/contract_suites/provider_contract_suite.hpp` and `suite_support.hpp` (T033, consumed unchanged);
the accepted `src/xverse/xcom/**` runtime sources, headers, and library targets including `provider.hpp`,
`loopback_provider.hpp`/`.cpp`; every accepted test under `tests/xcom/**` other than the new T034 drivers;
`tests/xcom/core_matrix/test_support.hpp` (T016 `CoreStackFixture`, `ProbeProvider`, `make_descriptor`,
`loopback_descriptor`); `proto/xverse/xcom/v1/tool_gateway.proto`; `docs/engineering/xcom/task-ownership.*`;
`docs/engineering/xcom/t00{7,8,9,10}/**`; `docs/engineering/xcom/t0{01..33}/**`;
`docs/engineering/xcom/build-environment.md`; `docs/engineering/xcom/dependency-lock.md`; and
`specs/007-xcom-core/**` (other than the T034 checkbox).

### 7.3 Explicitly not implemented by T034

A third provider, any change to the accepted provider boundary/composition/loopback provider, the
benchmark/sanitizer/static/Doxygen/delivery tasks (T035–T040), the gRPC transport runtime linkage
(`T032-GAP-01`), and any change to the accepted T030 contract, T031 gateway, T032 client, or T033 suites.
External Codex review and user acceptance remain T039/T041 and are deferred until the ordered backlog
`xcom-t030-t034-20260928` completes.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T034-GAP-01 — replaceability is proven against owned synthetic providers.** The second provider is an owned
  in-process fixture; the proof makes no third-party, network, transport, or legacy-provider compatibility
  claim.
- **T034-GAP-02 — isolation is bounded to independently composed routes.** The accepted composition owns one
  provider registry and one active route per fixture; isolation is demonstrated for an unrelated route on an
  independently composed provider and for a rejected provider registered into the same composition, not for an
  arbitrary multi-route topology.
- **T034-GAP-03 — gRPC transport runtime deferred.** The T011 admitted envelope still cannot link the gRPC
  runtime (`T032-GAP-01`); T034 validates the in-process provider boundary only.
- **T034-GAP-04 — no deployed-service or compatibility claim.** The second provider is a bounded prototype
  validated with owned fixtures; it makes no production-readiness or parity claim.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| Executed sanitizer/static/Doxygen/benchmark and delivery bundle | T035–T040 |
| gRPC transport runtime envelope | deferred capability gap `T032-GAP-01` |
| Independent Codex review and user acceptance | T039/T041 |

### 8.3 Open items

- **T034-OPEN-01 — inherited provenance refresh.** Editing `src/xverse/xcom/CMakeLists.txt` invalidates the
  inherited `implemented_by` target digests in `engineering/trace/links.json` and the declared
  `links.json`/`CMakeLists.txt` digests in `engineering/stage-results/*.json`; the implementation stage refreshes
  those inherited digests without changing any requirement, link identity, relation, or stage result.
- **T034-OPEN-02 — new fixture path not previously declared.** The second provider lives under the established
  synthetic-fixtures path `src/xverse/xcom/fixtures/` (T032 precedent, `XCOM-CMP-011`); no accepted T009/T010
  planned path transitions, because no accepted planned path becomes present.
- **T034-OPEN-03 — fixture source compilation.** The second-provider fixture source is compiled directly into
  each additive `t034-<kind>` test executable (no new library target, no runtime-target inventory change),
  mirroring the T032 fixture executable that also sits outside `XVERSE_XCOM_RUNTIME_TARGETS`.

## 9. Definition of done (requirements view)

T034 is done for a candidate revision when: every §4 requirement has at least one named check; the second
provider passes the unchanged T033 `ProviderContractSuite` with `P-01`…`P-13`; version and capability
misreport/mismatch are rejected fail-closed with zero emission; an unrelated route remains active, bounded, and
observable after a provider/route failure; all thirteen `t034-` cases pass in the offline admitted build; the
additive build wiring preserves every existing target/label/value and the runtime-target inventory;
`XCOM-SW-CORE-003/004/005/007/009` remain unchanged accepted text; the register validators pass with REF-002
`unchanged` and nothing promoted; the deterministic Phase 7 gate passes; and a separate DeepSeek internal review
records its findings before any repair. This does not constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T034-STK-001 | CHK-01, CHK-02, CHK-03, CHK-04 |
| T034-STK-002 | CHK-05, CHK-06 |
| T034-STK-003 | CHK-07, CHK-08, CHK-09, CHK-10 |
| T034-STK-004 | CHK-11, CHK-12, CHK-13 |
| T034-STK-005 | CHK-14, CHK-15, CHK-19, CHK-20 |
| T034-SR-001 | CHK-02 |
| T034-SR-002 | CHK-05, CHK-06 |
| T034-SR-003 | CHK-03 |
| T034-SR-004 | CHK-04 |
| T034-SR-005 | CHK-07 |
| T034-SR-006 | CHK-08 |
| T034-SR-007 | CHK-09, CHK-10 |
| T034-SR-008 | CHK-11 |
| T034-SR-009 | CHK-12, CHK-13 |
| T034-SR-010 | CHK-05, CHK-16 |
| T034-SR-011 | CHK-16, CHK-17 |
| T034-SR-012 | CHK-18, CHK-19 |
| T034-SR-013 | CHK-14, CHK-21, CHK-22 |
| T034-SR-014 | CHK-01, CHK-20 |
