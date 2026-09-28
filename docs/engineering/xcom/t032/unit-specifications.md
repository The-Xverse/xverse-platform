# T032 Unit Specifications — Separate-Process Synthetic Client and Generated-Client Contract Tests

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T032 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → unit specifications |
| Revision | 1 (separate-process synthetic-client conformance slice) |
| Baseline revision | `e6197c67868213ffb6523d8bf62ed4c2c4e3b0af` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit framework | GoogleTest over the T011-admitted offline envelope and the T012 subtree build contract, plus the deterministic Phase 7 gate and the T007–T010 register validators for governance |
| Classification | Public-safe engineering work product |

T032 realizes one separate-process synthetic-client fixture (`src/xverse/xcom/fixtures/synthetic_tool.cpp`) and proves
it with five additive `t032-<kind>` suites. Each requirement `T032-SR-###` owns one unit specification
`T032-SR-###-U` whose cases are named `T32-TS-###`. "Verified" means the test or named inspection exists, is
deterministic, and passes at the recorded candidate revision; it is not a deployed-service, remote-tool, or
compatibility claim.

## 2. Unit inventory

| Unit | Component | Source of truth | Kind | Cases |
| --- | --- | --- | --- | --- |
| `T032-SR-001-U` | `T032-SR-001-CMP` | `src/xverse/xcom/fixtures/synthetic_tool.cpp` | client interface | T32-TS-014 |
| `T032-SR-002-U` | `T032-SR-002-CMP` | `src/xverse/xcom/fixtures/synthetic_tool.cpp` | client operation surface | T32-TS-014 |
| `T032-SR-003-U` | `T032-SR-003-CMP` | `tests/xcom/tool_gateway/synthetic_client_support.hpp` | separate-process launch | T32-TS-001, T32-TS-019 |
| `T032-SR-004-U` | `T032-SR-004-CMP` | `tests/xcom/tool_gateway/synthetic_client_negative_tests.cpp` | local-only transport | T32-TS-015, T32-TS-019 |
| `T032-SR-005-U` | `T032-SR-005-CMP` | `tests/xcom/tool_gateway/synthetic_client_observation_tests.cpp` | bounded observation | T32-TS-002, T32-TS-003, T32-TS-004 |
| `T032-SR-006-U` | `T032-SR-006-CMP` | `tests/xcom/tool_gateway/synthetic_client_observation_tests.cpp` | observed traffic | T32-TS-005 |
| `T032-SR-007-U` | `T032-SR-007-CMP` | `tests/xcom/tool_gateway/synthetic_client_stimulation_tests.cpp` | stimulation conformance | T32-TS-006, T32-TS-007, T32-TS-008, T32-TS-009 |
| `T032-SR-008-U` | `T032-SR-008-CMP` | `tests/xcom/tool_gateway/synthetic_client_stimulation_tests.cpp` | emulation lease | T32-TS-010 |
| `T032-SR-009-U` | `T032-SR-009-CMP` | `tests/xcom/tool_gateway/synthetic_client_negative_tests.cpp` | permit/zero-emission | T32-TS-016, T32-TS-017 |
| `T032-SR-010-U` | `T032-SR-010-CMP` | `tests/xcom/tool_gateway/synthetic_client_negative_tests.cpp` | version rejection | T32-TS-018 |
| `T032-SR-011-U` | `T032-SR-011-CMP` | `src/xverse/xcom/fixtures/synthetic_tool.cpp` | explicit client bounds | T32-TS-020, T32-TS-021, T32-TS-022 |
| `T032-SR-012-U` | `T032-SR-012-CMP` | `tests/xcom/tool_gateway/synthetic_client_bounds_tests.cpp` | failure semantics | T32-TS-017, T32-TS-022 |
| `T032-SR-013-U` | `T032-SR-013-CMP` | `tests/xcom/tool_gateway/synthetic_client_contract_tests.cpp` | evidence safety | T32-TS-011 |
| `T032-SR-014-U` | `T032-SR-014-CMP` | `tests/xcom/tool_gateway/synthetic_client_observation_tests.cpp` | determinism | T32-TS-001 |
| `T032-SR-015-U` | `T032-SR-015-CMP` | `tests/xcom/tool_gateway/synthetic_client_contract_tests.cpp` | generated message fidelity | T32-TS-012, T32-TS-013 |
| `T032-SR-016-U` | `T032-SR-016-CMP` | `src/xverse/xcom/CMakeLists.txt` | build contract | build/discovery inspection; contributory `XcomSyntheticClientContract.ClientOperationTableMatchesGeneratedDescriptor` |
| `T032-SR-017-U` | `T032-SR-017-CMP` | `src/xverse/xcom/fixtures/synthetic_tool.cpp` | envelope decision | T32-TS-014, T32-TS-019 |
| `T032-SR-018-U` | `T032-SR-018-CMP` | `docs/engineering/xcom/t032/**` | governance | register validators; contributory `XcomSyntheticClientContract.ClientOperationTableMatchesGeneratedDescriptor` |
| `T032-SR-019-U` | `T032-SR-019-CMP` | `docs/engineering/xcom/t032/**` | deterministic gate | Phase 7 gate; contributory `XcomSyntheticClientBounds.DeadlineBoundEnforced` |
| `T032-SR-020-U` | `T032-SR-020-CMP` | `tests/xcom/tool_gateway/synthetic_client_*.cpp` | scope/handoff | changed-path inspection; contributory `XcomSyntheticClientContract.ClientOperationTableMatchesGeneratedDescriptor` |
| `T032-SR-021-U` | `T032-SR-021-CMP` | `src/xverse/xcom/fixtures/synthetic_tool.cpp` | documentation obligation | file-block inspection (CHK-03) |

## 3. Unit specifications

### T032-SR-001-U — Single synthetic-client boundary

- **Inputs:** the committed fixture source and its interface.
- **Outputs:** the declared client interface, the bounded result lines, and the component allocation.
- **Invariants:** exactly one fixture realizes the accepted `XCOM-XLC-002` generated message contract; no competing
  contract, RPC, or configuration language.
- **Cases:** `XcomSyntheticClientContract.ClientOperationTableMatchesGeneratedDescriptor`.
- **Static checks:** the fixture compiles under the accepted warning-as-error profile.

### T032-SR-002-U — Generated operation surface

- **Inputs:** `synthetic_client_operation_names()` and the generated `ToolGateway` service descriptor.
- **Outputs:** the operation-table equality verdict.
- **Invariants:** the committed client operation table equals the generated descriptor method set in order; a mismatch
  fails closed.
- **Cases:** `T32-TS-014`.

### T032-SR-003-U — Separate-process launch

- **Inputs:** the fixture executable path, the bounded argv, and the scrubbed admitted environment.
- **Outputs:** the bounded child exit status and captured result lines.
- **Invariants:** the client runs as its own process with an explicit bounded argv and a scrubbed environment; no
  ambient/secret value, legacy binary, production workload, or external peer is used.
- **Cases:** `T32-TS-001`, `T32-TS-019`.

### T032-SR-004-U — Host-protected local-only transport

- **Inputs:** the `AF_UNIX` socket path and the client source.
- **Outputs:** the endpoint-family, no-TCP, and forbidden-API verdicts.
- **Invariants:** only `AF_UNIX` is connected; no `AF_INET`/`AF_INET6`, DNS, resolver, TLS, or remote peer is
  referenced or contacted; the runtime family is `AF_UNIX`.
- **Cases:** `T32-TS-015`, `T32-TS-019`.

### T032-SR-005-U — Bounded observation stream

- **Inputs:** open/read/close requests and the accepted observation boundary.
- **Outputs:** the bounded record count and the delivered/dropped counters.
- **Invariants:** a read returns at most the granted record count before the deadline; records are metadata-only; close
  returns bounded counters.
- **Cases:** `T32-TS-002`, `T32-TS-003`, `T32-TS-004`.

### T032-SR-006-U — Observed emitted traffic

- **Inputs:** an emitted stimulation item and the client's observation stream.
- **Outputs:** the observed metadata-only record.
- **Invariants:** an emitted item is observed exactly once as a metadata-only record with logical identity only.
- **Cases:** `T32-TS-005`.

### T032-SR-007-U — Four allowed stimulation actions

- **Inputs:** the four `SubmitStimulationRequest` action kinds and the accepted guard/journal/action path.
- **Outputs:** the emitted outcome per action and the emission count.
- **Invariants:** all four allowed actions route through the accepted boundary; accepted items carry persistent
  synthetic provenance; a rejected or failed request emits zero normal-route items.
- **Cases:** `T32-TS-006`, `T32-TS-007`, `T32-TS-008`, `T32-TS-009`.

### T032-SR-008-U — Service-emulation lease

- **Inputs:** acquire/release requests and the accepted lease registry.
- **Outputs:** the lease state observed by the client.
- **Invariants:** the lease is exclusive and generation-bound; conflict is reported without ambiguous ownership;
  release is observed through the client.
- **Cases:** `T32-TS-010`.

### T032-SR-009-U — Invalid and expired zero emission

- **Inputs:** an invalid/substituted permit and an expired session.
- **Outputs:** the emitted-item count and the reported outcome.
- **Invariants:** an invalid or expired session emits zero normal-route items and the client reports a non-success
  outcome; transport access does not authorize.
- **Cases:** `T32-TS-016`, `T32-TS-017`.

### T032-SR-010-U — Fail-closed version rejection

- **Inputs:** the declared protocol major and the production compatibility predicate.
- **Outputs:** the rejection verdict and the emission count.
- **Invariants:** the supported major is accepted; any other major is rejected before any other operation and emits no
  item.
- **Cases:** `T32-TS-018`.

### T032-SR-011-U — Explicit client bounds

- **Inputs:** `SyntheticClientConfig` (maximum message size, request deadline, transport timeout).
- **Outputs:** the declared-bound inventory and the over-bound/timeout verdicts.
- **Invariants:** every client bound is explicit; an over-bound message or deadline, or an exhausted timeout, is
  handled fail-closed and deterministically.
- **Cases:** `T32-TS-020`, `T32-TS-021`, `T32-TS-022`.

### T032-SR-012-U — Deterministic failure semantics

- **Inputs:** a failed peer, an exhausted transport wait, and a disconnect after an intent.
- **Outputs:** the stable reported outcome.
- **Invariants:** failure maps to `failed`, expiry to `expired`, and disconnect-after-intent to `evidence-incomplete`;
  an unknown outcome is never reported as success.
- **Cases:** `T32-TS-017`, `T32-TS-022`.

### T032-SR-013-U — Safe evidence boundary

- **Inputs:** the captured client result lines and the harness log records.
- **Outputs:** the safety verdict.
- **Invariants:** only codes/phase/logical identity/size/timing/outcome appear; no payload byte, permit content,
  secret, private address, or host path is present.
- **Cases:** `T32-TS-011`.

### T032-SR-014-U — Determinism

- **Inputs:** fixed client arguments and fixed gateway fixtures.
- **Outputs:** the repeatability verdict.
- **Invariants:** the exchange is deterministic and bounded; no verdict depends on ambient wall-clock time,
  randomness, or environment.
- **Cases:** `T32-TS-001`.

### T032-SR-015-U — Generated message fidelity

- **Inputs:** generated request messages, including one with an unknown field.
- **Outputs:** the round-trip and unknown-field verdicts.
- **Invariants:** a generated message round-trips through the client unchanged; an unknown field survives the round
  trip.
- **Cases:** `T32-TS-012`, `T32-TS-013`.

### T032-SR-016-U — Additive build wiring

- **Inputs:** the build files and the discovered test inventory.
- **Outputs:** the discovered test count and the unchanged runtime-target inventory.
- **Invariants:** one additive fixture executable and five additive `t032-<kind>` test targets; the runtime-target
  inventory is unchanged; no existing target, test name, label, command, or expected value changes.
- **Cases:** changed-path and discovered-count inspection (CHK-19); contributory
  `XcomSyntheticClientContract.ClientOperationTableMatchesGeneratedDescriptor`.

### T032-SR-017-U — gRPC runtime envelope decision

- **Inputs:** the admitted envelope fact and the client operation table.
- **Outputs:** the recorded envelope decision and the forbidden-API scan verdict.
- **Invariants:** the generated messages/methods are realized over the accepted bounded local-IPC framing; no admitted
  dependency is added; no gRPC runtime link is claimed; the transport gap is recorded as `T032-GAP-01`.
- **Cases:** `T32-TS-014`, `T32-TS-019`.

### T032-SR-018-U — Governance reconciliation

- **Inputs:** the T007–T010 registers, the status-only path reconciliation, and the work products.
- **Outputs:** the validator verdict and the recorded maturity.
- **Invariants:** registers unchanged in substance; REF-002 `unchanged` with an empty `promoted` list;
  `XCOM-SW-GW-003` recorded implemented for the conformance-client slice; T033–T041 remain allocated.
- **Cases:** register validators (CHK-21); contributory
  `XcomSyntheticClientContract.ClientOperationTableMatchesGeneratedDescriptor`.

### T032-SR-019-U — Deterministic gate

- **Inputs:** the candidate revision and the Phase 7 gate.
- **Outputs:** the gate verdict.
- **Invariants:** the gate passes with a `t032-`-labelled discovered case; the checkbox is marked complete only at
  implementation; the diff is whitespace-clean.
- **Cases:** `xcom_phase7_gate.py verify T032 <baseline>` (CHK-22); contributory
  `XcomSyntheticClientBounds.DeadlineBoundEnforced`.

### T032-SR-020-U — Scope and handoff

- **Inputs:** the changed-path list and the preserved accepted suites.
- **Outputs:** the boundary verdict.
- **Invariants:** the accepted T030 contract, T031 gateway, and every accepted test are unchanged; the T032 suites
  remain T032-local (not the T033 abstraction, no T034 second provider).
- **Cases:** changed-path inspection (CHK-02, CHK-19); contributory
  `XcomSyntheticClientContract.ClientOperationTableMatchesGeneratedDescriptor`.

### T032-SR-021-U — Documentation obligation

- **Inputs:** the fixture source and its Doxygen file block.
- **Outputs:** the documentation verdict.
- **Invariants:** the fixture carries the `xcom_gw` file block and the ownership/lifetime/thread-safety/failure tags
  accepted `XCOM-DU-021` requires; generated Protocol Buffers documentation remains `DOX-GAP-02`.
- **Cases:** file-block inspection (CHK-03).

## 4. Case index

| Case | Suite | Primary requirement |
| --- | --- | --- |
| T32-TS-001 | XcomSyntheticClientObservation | T032-SR-003, T032-SR-014 |
| T32-TS-002 | XcomSyntheticClientObservation | T032-SR-005 |
| T32-TS-003 | XcomSyntheticClientObservation | T032-SR-005 |
| T32-TS-004 | XcomSyntheticClientObservation | T032-SR-005 |
| T32-TS-005 | XcomSyntheticClientObservation | T032-SR-006 |
| T32-TS-006 | XcomSyntheticClientStimulation | T032-SR-007 |
| T32-TS-007 | XcomSyntheticClientStimulation | T032-SR-007 |
| T32-TS-008 | XcomSyntheticClientStimulation | T032-SR-007 |
| T32-TS-009 | XcomSyntheticClientStimulation | T032-SR-007 |
| T32-TS-010 | XcomSyntheticClientStimulation | T032-SR-008 |
| T32-TS-011 | XcomSyntheticClientContract | T032-SR-013 |
| T32-TS-012 | XcomSyntheticClientContract | T032-SR-015 |
| T32-TS-013 | XcomSyntheticClientContract | T032-SR-015 |
| T32-TS-014 | XcomSyntheticClientContract | T032-SR-001, T032-SR-002, T032-SR-017 |
| T32-TS-015 | XcomSyntheticClientNegative | T032-SR-004 |
| T32-TS-016 | XcomSyntheticClientNegative | T032-SR-009 |
| T32-TS-017 | XcomSyntheticClientNegative | T032-SR-009, T032-SR-012 |
| T32-TS-018 | XcomSyntheticClientNegative | T032-SR-010 |
| T32-TS-019 | XcomSyntheticClientNegative | T032-SR-003, T032-SR-004, T032-SR-017 |
| T32-TS-020 | XcomSyntheticClientBounds | T032-SR-011 |
| T32-TS-021 | XcomSyntheticClientBounds | T032-SR-011 |
| T32-TS-022 | XcomSyntheticClientBounds | T032-SR-011, T032-SR-012 |

## 5. Coverage

Every `T032-SR-###` requirement is covered by at least one unit case or named inspection; every case belongs to one
listed requirement and one suite. Unit cases are contributory; the exact acceptance decision remains T039/T041.
