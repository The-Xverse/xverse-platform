# T031 Unit Specifications — Bounded Local-IPC-Only Tool Gateway

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T031 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → unit specifications |
| Revision | 1 (local-IPC gateway session slice) |
| Baseline revision | `4dded2317f895978cce0331ae88e34ac28b3a609` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit framework | GoogleTest over the T011-admitted offline envelope and the T012 subtree build contract, plus the deterministic Phase 7 gate and the T007–T010 register validators for governance |
| Classification | Public-safe engineering work product |

T031 realizes one bounded gateway production interface (`tool_gateway.hpp`/`tool_gateway.cpp`) and proves it with six
additive `t031-<kind>` suites. Each requirement `T031-SR-###` owns one unit specification `T031-SR-###-U` whose
cases are named `T31-TS-###`. "Verified" means the test exists, is deterministic, and passes at the recorded
candidate revision; it is not a deployed-service, separate-process, or compatibility claim.

## 2. Unit inventory

| Unit | Component | Source of truth | Kind | Cases |
| --- | --- | --- | --- | --- |
| `T031-SR-001-U` | `T031-SR-001-CMP` | `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` | gateway interface | T31-TS-003 |
| `T031-SR-002-U` | `T031-SR-002-CMP` | `src/xverse/xcom/src/tool_gateway.cpp` | operation surface | T31-TS-003 |
| `T031-SR-003-U` | `T031-SR-003-CMP` | `src/xverse/xcom/src/tool_gateway.cpp` | version predicate | T31-TS-001, T31-TS-002, T31-TS-020 |
| `T031-SR-004-U` | `T031-SR-004-CMP` | `tests/xcom/tool_gateway/gateway_session_tests.cpp` | permit enforcement | T31-TS-004, T31-TS-019, T31-TS-021 |
| `T031-SR-005-U` | `T031-SR-005-CMP` | `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` | explicit bounds | T31-TS-007, T31-TS-018, T31-TS-010 |
| `T031-SR-006-U` | `T031-SR-006-CMP` | `tests/xcom/tool_gateway/gateway_bounds_tests.cpp` | deadline enforcement | T31-TS-008 |
| `T031-SR-007-U` | `T031-SR-007-CMP` | `tests/xcom/tool_gateway/gateway_bounds_tests.cpp` | bounded flow control | T31-TS-009, T31-TS-010 |
| `T031-SR-008-U` | `T031-SR-008-CMP` | `tests/xcom/tool_gateway/gateway_local_ipc_tests.cpp` | local-IPC endpoint | T31-TS-015, T31-TS-016 |
| `T031-SR-009-U` | `T031-SR-009-CMP` | `tests/xcom/tool_gateway/gateway_local_ipc_tests.cpp` | host protection | T31-TS-017, T31-TS-021 |
| `T031-SR-010-U` | `T031-SR-010-CMP` | `tests/xcom/tool_gateway/gateway_bounds_tests.cpp` | observation stream | T31-TS-010, T31-TS-011 |
| `T031-SR-011-U` | `T031-SR-011-CMP` | `tests/xcom/tool_gateway/gateway_session_tests.cpp` | stimulation submission | T31-TS-008, T31-TS-018 |
| `T031-SR-012-U` | `T031-SR-012-CMP` | `tests/xcom/tool_gateway/gateway_lifecycle_tests.cpp` | emulation lease | T31-TS-012, T31-TS-021 |
| `T031-SR-013-U` | `T031-SR-013-CMP` | `tests/xcom/tool_gateway/gateway_lifecycle_tests.cpp` | cleanup | T31-TS-005, T31-TS-011, T31-TS-012, T31-TS-013, T31-TS-014 |
| `T031-SR-014-U` | `T031-SR-014-CMP` | `tests/xcom/tool_gateway/gateway_logging_tests.cpp` | log boundary | T31-TS-023, T31-TS-024 |
| `T031-SR-015-U` | `T031-SR-015-CMP` | `tests/xcom/tool_gateway/gateway_session_tests.cpp` | session query | T31-TS-006 |
| `T031-SR-016-U` | `T031-SR-016-CMP` | `tests/xcom/tool_gateway/gateway_bounds_tests.cpp` | determinism/concurrency | T31-TS-009, T31-TS-010 |
| `T031-SR-017-U` | `T031-SR-017-CMP` | `src/xverse/xcom/CMakeLists.txt` | build contract | build/discovery inspection; contributory `XcomToolGatewaySession.OperationSurfaceMatchesContract` |
| `T031-SR-018-U` | `T031-SR-018-CMP` | `tests/xcom/tool_gateway/**` | offline safety | T31-TS-022 |
| `T031-SR-019-U` | `T031-SR-019-CMP` | `docs/engineering/xcom/t031/**` | governance | register validators; contributory `XcomToolGatewaySession.OperationSurfaceMatchesContract` |
| `T031-SR-020-U` | `T031-SR-020-CMP` | `docs/engineering/xcom/t031/**` | deterministic gate | Phase 7 gate; contributory `XcomToolGatewayBounds.DeadlineEnforcedBeforeEmission` |
| `T031-SR-021-U` | `T031-SR-021-CMP` | `src/xverse/xcom/src/tool_gateway.cpp` | envelope decision | T31-TS-001, T31-TS-003 |

## 3. Unit specifications

### T031-SR-001-U — Single gateway production interface

- **Inputs:** the committed gateway header and source.
- **Outputs:** the declared interface and its component allocation.
- **Invariants:** exactly one committed gateway interface realizes the accepted `XCOM-XLC-002` message contract; no
  competing contract, RPC, or configuration language.
- **Cases:** `XcomToolGatewaySession.T31-TS-003 OperationSurfaceMatchesContract`.
- **Static checks:** the header and source compile under the warning-as-error policy.

### T031-SR-002-U — Complete operation surface

- **Inputs:** `gateway_operation_names()` and the T030 generated service descriptor.
- **Outputs:** the operation-table equality verdict.
- **Invariants:** the committed operation table equals the T030 descriptor method set in order; a mismatch fails
  closed.
- **Cases:** `T31-TS-003`.

### T031-SR-003-U — Fail-closed version negotiation

- **Inputs:** `ProtocolVersion` and the production compatibility predicate.
- **Outputs:** the predicate verdict per tested major and minor.
- **Invariants:** the supported major (and any higher minor) is accepted; any other major is rejected before any
  other operation; no rejection depends on an absent field.
- **Cases:** `T31-TS-001`, `T31-TS-002`, `T31-TS-020`.

### T031-SR-004-U — Exact permit enforcement

- **Inputs:** `ArmSessionRequest`, `SubmitStimulationRequest`, `AcquireLeaseRequest`, and the accepted T025 permit.
- **Outputs:** the permit-enforcement verdict and the emission count.
- **Invariants:** an exact permit arms/succeeds; a missing, expired, or mismatched permit is rejected with zero
  emitted items; no field or framing element bypasses the permit.
- **Cases:** `T31-TS-004`, `T31-TS-019`, `T31-TS-021`.

### T031-SR-005-U — Explicit bounds

- **Inputs:** `GatewayConfigInput` and the message/stream/queue/payload bounds.
- **Outputs:** the bound inventory and the over-bound rejection verdict.
- **Invariants:** every bound is an explicit config value; an over-bound frame, stream, record, or payload is
  rejected before allocation or emission.
- **Cases:** `T31-TS-007`, `T31-TS-018`, `T31-TS-010`.

### T031-SR-006-U — Per-request deadlines

- **Inputs:** the declared `deadline_millis` and the injected T025 time authority.
- **Outputs:** the deadline verdict and the emission count.
- **Invariants:** a request over `max_deadline_millis` is rejected; an overdue request returns a deterministic
  diagnostic and emits no item; no verdict uses an ambient wall clock.
- **Cases:** `T31-TS-008`.

### T031-SR-007-U — Bounded flow control

- **Inputs:** the bounded per-session in-flight queue and rate.
- **Outputs:** the saturation verdict and the visible counters.
- **Invariants:** the queue never exceeds its bound; saturation rejects deterministically and is counted; memory and
  blocking stay bounded.
- **Cases:** `T31-TS-009`, `T31-TS-010`.

### T031-SR-008-U — Local IPC only, no TCP listener

- **Inputs:** `LocalIpcEndpoint::create` and the gateway source.
- **Outputs:** the endpoint-family, no-TCP, and forbidden-API verdicts.
- **Invariants:** only `AF_UNIX`/`socketpair` are bound; no `AF_INET`/`AF_INET6`, DNS, resolver, or TLS facility is
  referenced; the runtime family is `AF_UNIX`.
- **Cases:** `T31-TS-015`, `T31-TS-016`, `T31-TS-022`.

### T031-SR-009-U — Host-protected endpoint

- **Inputs:** the bound socket path and its file permissions.
- **Outputs:** the host-protection verdict.
- **Invariants:** the socket lives under a restricted directory with restrictive permissions; transport access
  confers no stimulation authorization.
- **Cases:** `T31-TS-017`, `T31-TS-021`.

### T031-SR-010-U — Bounded observation stream

- **Inputs:** open/read/close messages and the accepted `ObservationHub`.
- **Outputs:** the bounded record count and the delivered/dropped counters.
- **Invariants:** a read returns at most the granted record count before the deadline; records are metadata-only by
  default; close returns bounded counters.
- **Cases:** `T31-TS-010`, `T31-TS-011`.

### T031-SR-011-U — Stimulation submission

- **Inputs:** `SubmitStimulationRequest` and the accepted guard/journal/action path.
- **Outputs:** the outcome and the emission count.
- **Invariants:** all four allowed actions route through the accepted boundary; accepted items carry persistent
  synthetic provenance; a rejected or failed request emits zero normal-route items.
- **Cases:** `T31-TS-008`, `T31-TS-018`, `T31-TS-019`.

### T031-SR-012-U — Service-emulation lease

- **Inputs:** acquire/release messages and the accepted lease registry.
- **Outputs:** the lease state and the cleanup verdict.
- **Invariants:** a lease is exclusive and generation-bound; conflict is reported without ambiguous ownership;
  expiry/disconnect releases or quarantines.
- **Cases:** `T31-TS-012`, `T31-TS-021`.

### T031-SR-013-U — Deterministic disconnect and expiry cleanup

- **Inputs:** a live session with observation handles, a lease, and a pending request.
- **Outputs:** the post-cleanup snapshot and the pending-request outcome.
- **Invariants:** observation handles close; validation resources drain/revoke/release/quarantine; a revoke is
  terminal; pending requests end explicit; unknown is never success.
- **Cases:** `T31-TS-005`, `T31-TS-011`, `T31-TS-012`, `T31-TS-013`, `T31-TS-014`.

### T031-SR-014-U — Safe log boundary

- **Inputs:** a payload-bearing stimulation and an armed session.
- **Outputs:** the captured log records.
- **Invariants:** records carry only code/phase/identity/size/timing/outcome; no payload byte or permit content is
  present.
- **Cases:** `T31-TS-023`, `T31-TS-024`.

### T031-SR-015-U — Session outcome and counter query

- **Inputs:** `QuerySessionRequest` and the session snapshot.
- **Outputs:** the bounded counter set.
- **Invariants:** counters are finite and include an explicit evidence-incomplete count; no dashboard/storage/
  query-presentation/export primitive is exposed.
- **Cases:** `T31-TS-006`.

### T031-SR-016-U — Determinism and bounded concurrency

- **Inputs:** the per-session mutex, bounded queue, and injected time authority.
- **Outputs:** the determinism and bound verdict.
- **Invariants:** one per-session mutex plus a bounded queue; every call performs a finite declared operation; no
  verdict depends on ambient wall clock, randomness, or environment.
- **Cases:** `T31-TS-009`, `T31-TS-010`.

### T031-SR-017-U — Additive build wiring

- **Inputs:** the build files and the test inventory.
- **Outputs:** the discovered test count and the runtime-target inventory.
- **Invariants:** one declared runtime-target addition (`xverse_xcom_tool_gateway`); six additive `t031-<kind>` test
  targets; no existing target, test name, label, command, or expected value changes.
- **Cases:** changed-path and discovered-count inspection (CHK-19); contributory
  `XcomToolGatewaySession.OperationSurfaceMatchesContract`.

### T031-SR-018-U — Offline and no new dependency

- **Inputs:** the gateway sources, tests, and the build link line.
- **Outputs:** the forbidden-API scan and offline-build verdict.
- **Invariants:** only the standard library, the T030 generated messages, the accepted in-process boundaries, and
  GTest are used; no network/`AF_INET`/DNS/TLS/ambient/secret/dynamic-load/subprocess/legacy access; no new admitted
  dependency.
- **Cases:** `T31-TS-022`.

### T031-SR-019-U — Governance reconciliation

- **Inputs:** the T007–T010 registers, the status-only path reconciliation, and the work products.
- **Outputs:** the validator verdict and the recorded maturity.
- **Invariants:** registers unchanged in substance; REF-002 `unchanged` with an empty `promoted` list;
  `XCOM-SW-GW-002` recorded implemented for the gateway slice; T032–T041 remain allocated.
- **Cases:** register validators (CHK-21); contributory
  `XcomToolGatewaySession.OperationSurfaceMatchesContract`.

### T031-SR-020-U — Deterministic gate

- **Inputs:** the candidate revision and the Phase 7 gate.
- **Outputs:** the gate verdict.
- **Invariants:** the gate passes with a `t031-`-labelled discovered case; the checkbox is marked complete only at
  implementation; the diff is whitespace-clean.
- **Cases:** `xcom_phase7_gate.py verify T031 <baseline>` (CHK-22); contributory
  `XcomToolGatewayBounds.DeadlineEnforcedBeforeEmission`.

### T031-SR-021-U — gRPC runtime envelope decision

- **Inputs:** the admitted envelope fact and the operation table.
- **Outputs:** the recorded envelope decision and the operation-table equality verdict.
- **Invariants:** the accepted messages/methods are realized over bounded local-IPC framing; no admitted dependency
  is added; no gRPC runtime link is claimed; the transport gap is recorded as `T031-GAP-01`.
- **Cases:** `T31-TS-001`, `T31-TS-003`.

## 4. Case index

| Case | Suite | Primary requirement |
| --- | --- | --- |
| T31-TS-001 | XcomToolGatewaySession | T031-SR-003, T031-SR-021 |
| T31-TS-002 | XcomToolGatewaySession | T031-SR-003 |
| T31-TS-003 | XcomToolGatewaySession | T031-SR-001, T031-SR-002, T031-SR-021 |
| T31-TS-004 | XcomToolGatewaySession | T031-SR-004 |
| T31-TS-005 | XcomToolGatewaySession | T031-SR-013 |
| T31-TS-006 | XcomToolGatewaySession | T031-SR-015 |
| T31-TS-007 | XcomToolGatewayBounds | T031-SR-005 |
| T31-TS-008 | XcomToolGatewayBounds | T031-SR-006, T031-SR-011 |
| T31-TS-009 | XcomToolGatewayBounds | T031-SR-007, T031-SR-016 |
| T31-TS-010 | XcomToolGatewayBounds | T031-SR-007, T031-SR-010, T031-SR-016 |
| T31-TS-011 | XcomToolGatewayLifecycle | T031-SR-010, T031-SR-013 |
| T31-TS-012 | XcomToolGatewayLifecycle | T031-SR-012, T031-SR-013 |
| T31-TS-013 | XcomToolGatewayLifecycle | T031-SR-013 |
| T31-TS-014 | XcomToolGatewayLifecycle | T031-SR-013 |
| T31-TS-015 | XcomToolGatewayLocalIpc | T031-SR-008 |
| T31-TS-016 | XcomToolGatewayLocalIpc | T031-SR-008 |
| T31-TS-017 | XcomToolGatewayLocalIpc | T031-SR-009 |
| T31-TS-018 | XcomToolGatewayNegative | T031-SR-005, T031-SR-011 |
| T31-TS-019 | XcomToolGatewayNegative | T031-SR-004, T031-SR-011 |
| T31-TS-020 | XcomToolGatewayNegative | T031-SR-003 |
| T31-TS-021 | XcomToolGatewayNegative | T031-SR-004, T031-SR-009, T031-SR-012 |
| T31-TS-022 | XcomToolGatewayNegative | T031-SR-008, T031-SR-018 |
| T31-TS-023 | XcomToolGatewayLogging | T031-SR-014 |
| T31-TS-024 | XcomToolGatewayLogging | T031-SR-014 |

## 5. Coverage

Every `T031-SR-###` requirement is covered by at least one unit case or named inspection; every case belongs to one
listed requirement and one suite. Unit cases are contributory; the exact acceptance decision remains T039/T041.

## Successor addendum (T039 R3, recorded 2026-09-30)

This addendum records successor unit cases for the linked gRPC gateway component. It does not
rename, remove, or weaken any `T31-TS-###` case above, and the historical inventory remains evidence
at its pinned revision. The generated-client cases run in
`tests/xcom/tool_gateway/grpc_generated_client_tests.cpp` against the production adapter
(`tool_gateway_grpc.hpp`/`.cpp`) and the `GatewayLiveness` watch contract
(`proto/xverse/xcom/v1/gateway_liveness.proto`).

| Requirement unit | Successor cases | Purpose |
| --- | --- | --- |
| `T031-SR-012-U` | `XcomGrpcGeneratedClient.RepeatedAcquireLeaseDeclinesSecondAllocation`, `XcomGrpcGeneratedClient.RepeatedAcquireLeaseOriginalIdentityStillReleases`, `XcomGrpcGeneratedClient.UnassociatedPeerCannotBorrowLiveWatch`, `XcomGrpcGeneratedClient.SeparateServerHonorsContractAndWireRejection` | Enforce the single-owned-lease boundary (T039-F07) and the logical watch-owner association (T039-F02) with the authoritative registry and exact-identity release. |
| `T031-SR-013-U` | `XcomGrpcGeneratedClient.ShutdownTerminatesLiveWatchAndCleansResources`, `XcomGrpcGeneratedClient.WatchCancellationReleasesLiveResources`, `XcomGrpcGeneratedClient.AbruptClientExitReleasesLiveResources`, `XcomGrpcGeneratedClient.RepeatedAcquireLeaseDeclinesSecondAllocation` | Owner cancellation, abrupt exit, and server shutdown leave no active owned lease in the authoritative registry. |
| `T031-SR-010-U` | `XcomGrpcGeneratedClient.RejectedObservationReadHasExplicitTransportStatus`, `XcomGrpcGeneratedClient.WatchCancellationReleasesLiveResources` | Explicit transport status for rejected observation reads (T039-F05). |
| `T031-SR-006-U` | `XcomGrpcGeneratedClient.DeadlineAndCancellationAreTransportEnforced`, `XcomGrpcGeneratedClient.LateTransportFailuresReconcileCommittedEmission` | Transport deadline/cancellation and post-commit reconciliation (T039-F03/F04). |
| `T031-SR-011-U` | `XcomGrpcGeneratedClient.DeadlineAndCancellationAreTransportEnforced`, `XcomGrpcGeneratedClient.LateTransportFailuresReconcileCommittedEmission` | Zero emission on a rejected transport and reconciliation of a committed emission (T039-F03). |
| `T035-SR-005-U` | the generated-client harness suite | Compiler ASan/UBSan and leak detection with `GRPC_ASAN_SUPPRESSED=1` preserving the admitted binary ABI (T039-F01). |

**Successor single-owned-lease boundary (`T039-F07`).** A session owns at most one exclusive
service-emulation lease. While one is held, a further acquisition is declined with `LEASE_CONFLICT`
before any registry allocation; the original lease identity is preserved and never aliased, and the
declined request does not mutate the held lease's registry entry. The linked identity releases the
lease exactly, and every cleanup path leaves no active owned lease in the authoritative registry.
An expanded bounded ownership set is explicitly out of scope and requires its own design.

**Declared limits carried forward.** The watch association is a logical lifecycle association, not
OS process authentication; clients must keep the watch identifier private and must not share it. A
running host action callback must return before shutdown can complete. Durable lookup reconciles a
committed immediate outcome; the absence of a scheduled intent remains explicitly uncertain and does
not authorize a retry.

## Successor addendum (T039 R4, recorded 2026-09-30)

This additive addendum records the `T039-F08` identity repair for the linked gRPC gateway component.
It does not rename, remove, or weaken any `T31-TS-###` case or the R3 addendum above, and the
historical inventory remains evidence at its pinned revision. The successor cases run in
`tests/xcom/tool_gateway/grpc_generated_client_tests.cpp` against the production adapter.

| Requirement unit | Successor cases | Purpose |
| --- | --- | --- |
| `T031-SR-012-U` | `XcomGrpcGeneratedClient.StaleReleaseIdentityDoesNotReleaseLaterAllocation`, `XcomGrpcGeneratedClient.RepeatedAllocationOfSameEndpointGetsFreshIdentity` | Every successful allocation receives a fresh public identity; a stale release cannot release a later allocation, including a different endpoint at an equal generation, and repeated allocation of one endpoint receives a new identity. |
| `T031-SR-013-U` | `XcomGrpcGeneratedClient.StaleReleaseIdentityDoesNotReleaseLaterAllocation` | A rejected stale release leaves the authoritative registry entry and exact-session ownership intact, so cleanup semantics remain unambiguous. |

**Successor allocation-identity boundary (`T039-F08`).** A release is validated against the exact
successful allocation. The public identity of an allocation is session-scoped and strictly
monotonic, drawn from a bounded sequence that never wraps, and is never reused after that lease is
released. A delayed or repeated release for an earlier allocation is rejected without changing the
held lease, the registry entry, or the session; the allocating identity still releases its own
entry. When the bounded identity sequence is exhausted, the acquisition is declined before the
registry is touched, with no wraparound and no lease or registry side effect. The generation-bound
registry delegation, `LEASE_CONFLICT` single-owned-lease boundary, and disconnect cleanup are
unchanged.
