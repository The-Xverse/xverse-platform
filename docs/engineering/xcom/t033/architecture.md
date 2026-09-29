# T033 Architecture — Reusable Provider, Observer, Stimulation-Tool, and Gateway Contract Suites

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T033 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → architecture |
| Revision | 1 (reusable contract-suite slice) |
| Baseline revision | `2fd395e39e44e1f6fe9547998b47499d996b1756` |
| Affected source paths | `tests/xcom/contract_suites/**` (new reusable suites and drivers); `src/xverse/xcom/CMakeLists.txt` (edit, additive `t033-<kind>` test registration); engineering trace/verification records |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-005`/`006`/`007` provider/route boundary, `XCOM-CMP-010` local tool gateway, `XCOM-CMP-011` synthetic sink/tools, `XCOM-XLC-002` external-rpc contract, `XCOM-XB-004`/`009`/`010`); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-007` provider boundary, `XCOM-DU-020` gateway session, `XCOM-DU-021` synthetic tool client); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-CORE-007`, `XCOM-SW-CORE-009`, `XCOM-SW-GW-002`); accepted T016/T021–T029/T031 test fixtures; `specs/007-xcom-core/contracts/provider.md`; `specs/007-xcom-core/spec.md` (User Story 4); ADR-0016, ADR-0018, ADR-0019, ADR-0020 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T033 is the **reusable contract-suite** task of the `T-CORE`/GW family. T030 defined the versioned
`XCOM-XLC-002` contract, T031 realized the bounded local-IPC-only gateway, and T032 added the separate-process
synthetic client. T033 extracts the provider, observer, stimulation-tool, and gateway conformance obligations
into four reusable, implementation-agnostic suite drivers so that a later conforming implementation — notably
the T034 second synthetic provider — is validated by the *same* suites without editing them.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013/T-CORE vocabulary (read-only)
   → T017–T020 XDL Profile + activation-plan digest binding (read-only)
   → T021–T024 observation boundary (read-only) → T025–T029 stimulation boundary (read-only)
   → T030 versioned external-tool contract (read-only) → T031 bounded local-IPC-only gateway (read-only)
   → T032 separate-process synthetic client + generated-client suites (read-only)
   → T033 reusable provider/observer/stimulation-tool/gateway contract suites (this slice)
   → T034 second provider → T035–T041 evidence/review/acceptance
```

T033 changes exactly one additive build registration and adds a new test-support directory. It changes no
production runtime source, no accepted test, target, label, command, or expected value, and no accepted register.

## 3. Boundary and context

### 3.1 System context

```text
   ┌────────────── accepted capability-007 anchors (read-only) ──────────────┐
   │  spec.md FR-006/007/010/011/012/013/014/015/016/017/018/021/022/026/027/ │
   │    028/029/030/032/034/035 · SC-011 · contracts/provider.md ·          │
   │    contracts/observation.md · contracts/tool-gateway.md                │
   │  t009 XCOM-CMP-005/006/007/010/011 · XCOM-XLC-002 · XCOM-XB-004/009/010 │
   │  t010 XCOM-DU-007 · XCOM-DU-020 · XCOM-DU-021                           │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ realized by
   ┌──────── accepted implementations and fixtures (read-only, consumed) ────┐
   │  T016 core_matrix test_support (loopback provider + ProbeProvider)        │
   │  T021–T024 ObservationHub · T025–T028 stimulation path/guard/journal     │
   │  T029 stimulation_matrix test_support · T031 gateway_support fixture     │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ validated by
   ┌──────────────────── T033 owned artifacts (this slice) ────────────────────────┐
   │  tests/xcom/contract_suites/suite_support.hpp                                │
   │  tests/xcom/contract_suites/provider_contract_suite.hpp                      │
   │  tests/xcom/contract_suites/observer_contract_suite.hpp                      │
   │  tests/xcom/contract_suites/stimulation_tool_contract_suite.hpp              │
   │  tests/xcom/contract_suites/gateway_contract_suite.hpp                       │
   │  tests/xcom/contract_suites/{provider,observer,stimulation_tool,gateway}_    │
   │      suite_tests.cpp (four t033-<kind> executables)                          │
   │  guarantee : implementation-agnostic subject seams, reusable checks,         │
   │      bounded reports, additive registration, no runtime-target change        │
   └──────────────────────────────────┬──────────────────────────────────────────────┘
                                      ▼
              T034 second provider · T035–T041 evidence/review/acceptance
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T33-XB-1` Suite vs implementation | the four suite bodies and their abstract subject seams | a concrete provider, hub, stimulation composition, or gateway fixture | Each suite names only an accepted interface or accepted fixture helper; the concrete implementation is supplied through the subject (`T033-DD-01`). |
| `T33-XB-2` Reuse vs duplication | one suite body instantiated by several subjects | a per-implementation copy of the suite | A second conforming implementation is validated by a new subject; the suite header is unchanged (`T033-SR-014`). |
| `T33-XB-3` Candidate vs accepted predecessor | the new `tests/xcom/contract_suites/**` paths and the additive `CMakeLists.txt` registration | any accepted `src/` runtime byte, accepted test, target, label, command, or expected value | Only the declared T033 paths change; the runtime-target inventory is unchanged (`T033-SR-015`). |
| `T33-XB-4` Synthetic vs external | owned in-process fixtures and bounded local IPC | any legacy binary, external peer, TCP listener, DNS, resolver, TLS, or production workload | The suites reuse only owned synthetic fixtures; no network or legacy resource is contacted (`XCOM-INV-13`, FR-028). |
| `T33-XB-5` Authorization vs observation | the exact validation permit required by the stimulation/gateway suites | transport access, socket access, or an unarmed session | The suites observe zero emission for an unarmed/out-of-window/non-active request (`XCOM-INV-08`, FR-016). |
| `T33-XB-6` Evidence vs content | stable codes, phase, logical identity, size, timing, and outcome | payload bytes, permit contents, secrets, private addresses, host paths | Committed files and bounded logs contain none of the excluded content (`T033-SR-015`, FR-027). |
| `T33-XB-7` Reuse vs later task | the reusable suites T033 owns | the T034 second provider and its replaceability proof | T033 provides the provider suite; it does not add a second provider (`T033-SR-016`). |
| `T33-XB-8` Suite vs abstraction drift | the reusable suites as the single conformance definition | a competing interface, RPC, or configuration language | The suites bind to the accepted `CommunicationProvider`/`ObservationHub`/`StimulationActionPath`/`GatewaySession` interfaces; no competing vocabulary is introduced. |

### 3.3 Prohibited elements (must remain absent)

No production runtime source change; no second synthetic provider; no TCP listener or `AF_INET`/`AF_INET6`
socket, DNS, resolver, or TLS use; no external network peer; no legacy binary, legacy repository, or production
workload; no compiled or linked gRPC runtime; no new admitted dependency; no unbounded queue, stream, or frame;
no permit bypass; no payload, permit, secret, private address, or host path in a log record or committed file;
no ambient wall-clock-dependent verdict; no change to an accepted predecessor `src/`, `tests/`, `xdl/`, or
`docs/engineering/xcom/t0{07..32}/` byte; no rewrite or weakening of an accepted ADR, requirement, contract,
schema, register, or REF-002 disposition; no acceptance or integration of the candidate.

## 4. Components

`T33-*` names are local to this document; the accepted `XCOM-DU-007`, `XCOM-DU-020`, `XCOM-DU-021`,
`XCOM-CMP-005`/`006`/`007`, `XCOM-CMP-010`, `XCOM-CMP-011`, `XCOM-XLC-002`, and `XCOM-XB-004`/`009`/`010`
identifiers are the authorized units/contracts.

### 4.1 New T033 components

- **`T33-CMP-SUPPORT` Shared suite vocabulary** (`suite_support.hpp`): the bounded `SuiteCheck`/`SuiteReport`
  value vocabulary shared by every suite; owns copied checks only and never borrows subject storage.
- **`T33-CMP-PROVIDER` Reusable provider suite** (`provider_contract_suite.hpp`): the
  `ProviderSubject` seam and the `ProviderContractSuite::run` driver over the accepted `CommunicationProvider`
  and `ProviderComposition` interfaces.
- **`T33-CMP-OBSERVER` Reusable observer suite** (`observer_contract_suite.hpp`): the `ObserverSubject` seam and
  the `ObserverContractSuite::run` driver over the accepted observation boundary and integration fixture.
- **`T33-CMP-STIM` Reusable stimulation-tool suite** (`stimulation_tool_contract_suite.hpp`): the
  `StimulationToolSubject` seam and the `StimulationToolContractSuite::run` driver over the accepted guarded
  action path.
- **`T33-CMP-GATEWAY` Reusable gateway suite** (`gateway_contract_suite.hpp`): the `GatewaySubject` factory seam
  and the `GatewayContractSuite::run` driver over the accepted `GatewaySession` and T031 fixture helpers.
- **`T33-CMP-DRIVERS` Suite drivers** (`tests/xcom/contract_suites/*_suite_tests.cpp`): the four additive
  `t033-<kind>` test executables that instantiate each suite against the accepted implementations.
- **`T33-CMP-BUILD`** (T012): the subtree build extended additively by four `t033-<kind>` test targets; the
  runtime-target inventory is unchanged.
- **`T33-WP`** — the T033 repository-owned work-product set.

### 4.2 Consumed components (read-only)

- **`T33-CMP-T016`** — accepted core-matrix test support (`CoreStackFixture`, `ProbeProvider`,
  `make_descriptor`, `loopback_descriptor`) and the accepted owned `LoopbackProvider`. Consumed read-only.
- **`T33-CMP-T024`** — accepted observation integration support (`Scenario`, `make_tap_spec`) and the accepted
  `ObservationHub`. Consumed read-only.
- **`T33-CMP-T029`** — accepted stimulation-matrix support (`MatrixFixture`, `make_permit`, `make_policy`,
  `make_config`, `make_request`, `in_window`, `out_of_window`) and the accepted journal/guard/action-path/lease
  composition. Consumed read-only.
- **`T33-CMP-T031`** — accepted gateway fixture (`GatewayFixture`, `arm_request`, `stimulation_request`,
  `make_config`) and the accepted `GatewaySession`/`GatewayConfig`/`gateway_decode_request_frame`. Consumed
  read-only.
- **`T33-CMP-T030`/`T31-T032`** — the accepted generated messages, the accepted T031 gateway, and the accepted
  T032 client. Consumed read-only, unchanged.
- **`T33-CMP-T011`/`T012`** — the admitted offline envelope and the subtree build/test contract. No rule is
  weakened and no dependency is added.

## 5. Data flow (ordered)

1. **Build the drivers.** The subtree build compiles the accepted libraries and the four `t033-<kind>` test
   executables under the warning-as-error policy. The runtime-target inventory is unchanged.
2. **Construct a subject.** Each driver builds a small subject adapter over an accepted implementation (a
   loopback or probe provider, an observation hub, a stimulation-matrix fixture, or a gateway fixture factory).
3. **Run the suite.** The suite drives the subject through its named conformance checks, creating fresh fixtures
   where state is single-use (the gateway permit), and records one bounded `SuiteCheck` per obligation.
4. **Assert the report.** The driver asserts `SuiteReport::ok()` and the key check identities, printing a bounded
   failure detail on any mismatch.
5. **Reuse.** A second driver case (or, for the provider, a second provider implementation) runs the *same*
   suite body through a different subject; no suite header changes.
6. **Register additively.** The build registers four `t033-<kind>` test targets; the runtime-target inventory is
   unchanged and no existing target, label, command, or value changes.

## 6. Interfaces

### 6.1 Suite interfaces (`tests/xcom/contract_suites/**`)

| Element | Contract |
| --- | --- |
| `SuiteReport`/`SuiteCheck` | bounded owned report; `ok()` false unless at least one check exists and every check passed; a missing check is never a pass |
| `ProviderSubject::provider()` | returns the `CommunicationProvider&` under test |
| `ObserverSubject::hub()` | returns the `ObservationHub&` under test |
| `StimulationToolSubject` | returns the action path, permit, emission counters, provenance, and durable-intent-before-emission observations |
| `GatewaySubject::make_fixture()` | returns a fresh accepted gateway fixture per conformance group (single-session permit) |
| `ProviderContractSuite::run`, `ObserverContractSuite::run`, `StimulationToolContractSuite::run`, `GatewayContractSuite::run` | the four reusable, implementation-agnostic drivers |

Ownership/lifetime: a subject owns its concrete implementation and must outlive the suite call; each suite owns
only its bounded report and any fresh fixture it constructs. Thread-safety: one caller per suite; the accepted
components serialize their own state. Failure: a missing or failing check is reported, never skipped, and a
decline never emits an item and is never reported as success.

### 6.2 Consumed contract (read-only, unchanged)

| Interface | Contract consumed (unchanged) |
| --- | --- |
| `CommunicationProvider`, `ProviderComposition`, `ProviderDescriptor` | provider-descriptor, registration, capability, and lifecycle semantics |
| `ObservationHub`, `ObservationTapSpec`, `ObservationFilterInput` | bounded metadata-only observation, counters, and exact-handle detach |
| `validation::StimulationActionPath`, `Permit`, `StimulationPolicy`, `ServiceEmulationRegistry` | permit-enforced, journaled, guarded, provenance-preserving action semantics |
| `GatewaySession`, `GatewayConfig`, `gateway_decode_request_frame`, `gateway_operation_names()` | the ten-operation local-IPC gateway and bounded framing |
| GTest and the accepted offline fixtures | the admitted offline test framework and owned synthetic fixtures |

## 7. Concurrency and resource bounds

| Aspect | T033 decision |
| --- | --- |
| Production footprint | five new test-support headers and four additive test executables; no runtime library |
| Build inventory | four `t033-<kind>` test targets (`provider`, `observer`, `stimulation-tool`, `gateway`); `XVERSE_XCOM_RUNTIME_TARGETS` unchanged |
| Processes | none; all suites run in-process against owned fixtures; no legacy, external, or production process |
| Writers | one caller per suite; the accepted components own their own state |
| Threads | single declared user per suite; no unbounded thread or queue |
| Operations per suite | finite and declared (`P-01`…`P-13`, `O-01`…`O-11`, `S-01`…`S-05`, `G-01`…`G-11`) |
| Transport | none beyond the accepted in-process fixtures; no network, DNS, TLS, or legacy access |
| Time | no verdict depends on ambient wall-clock time; the stimulation/gateway suites use the accepted injected time authority |
| Determinism | the checks, bounds enforcement, and outcomes are deterministic for fixed inputs; repeated runs are equal |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Reusable, implementation-agnostic suites | one suite body per family behind a small subject seam; no concrete implementation type named | `T033-SR-014`; the four reuse cases |
| Provider conformance | descriptor/registration/duplicate/version/lifecycle/saturation/reconcile | `T033-SR-001`…`-003`; `P-01`…`P-13` |
| Observer conformance | metadata-only records, bounded counters, detach, isolation | `T033-SR-004`…`-006`; `O-01`…`O-11` |
| Stimulation-tool conformance | four actions, provenance, journal ordering, zero emission | `T033-SR-007`, `T033-SR-008`; `S-01`…`S-05` |
| Gateway conformance | version, permit, observation, actions, lease, framing, counters | `T033-SR-009`…`-013`; `G-01`…`G-11` |
| Additive delivery | four new test targets; no existing target/label/value changed; runtime-target inventory unchanged | `T033-SR-015` |
| Public-safe evidence | no payload/permit/secret/private-address/host-path in a committed file or log | `T033-SR-015` |
| Governance and envelope honesty | registers re-validated; REF-002 unchanged; T034–T041 allocated | `T033-SR-016` |

## 9. Consistency and constraints

- **Dependency direction preserved.** T033 consumes the accepted T007–T032 design and fixtures; it introduces no
  dependency on a later slice, an external peer, or a legacy repository, and adds no admitted dependency.
- **Domain neutrality preserved.** Only generic X-COM vocabulary appears (provider, observation, stimulation,
  lease, identity, generation, bound, provenance); no automotive, product, protocol, or configuration primitive
  is introduced.
- **XDL centrality preserved.** T033 neither parses nor authors XDL; plan/graph digests appear only as opaque
  logical identities already bound by the accepted plan.
- **Logical/physical separation preserved.** The suites carry logical identities only; the local socket is a
  realization detail and no address or port enters an accepted message contract.
- **Ownership preserved.** Only the declared T033 paths change; every accepted production byte and existing test
  is preserved except the additive `CMakeLists.txt` registration.
- **Maturity preserved.** The slice implements the reusable suites only; the second provider, executed evidence,
  and acceptance remain T034–T041.

## 10. Traceability

| Architecture element | T033 requirements |
| --- | --- |
| `T33-XB-1`, `T33-CMP-SUPPORT`, `T33-CMP-DRIVERS` | T033-SR-001, T033-SR-014, T033-SR-015 |
| `T33-XB-2`, `T33-CMP-PROVIDER` | T033-SR-001, T033-SR-002, T033-SR-003, T033-SR-014 |
| `T33-CMP-OBSERVER` | T033-SR-004, T033-SR-005, T033-SR-006 |
| `T33-CMP-STIM` | T033-SR-007, T033-SR-008 |
| `T33-CMP-GATEWAY` | T033-SR-009, T033-SR-010, T033-SR-011, T033-SR-012, T033-SR-013 |
| `T33-XB-4`, `T33-XB-5` | T033-SR-002, T033-SR-008, T033-SR-010 |
| `T33-XB-6` | T033-SR-015 |
| `T33-XB-7`, `T33-CMP-BUILD`, `T33-WP` | T033-SR-015, T033-SR-016 |
| `T33-XB-8` | T033-SR-009, T033-SR-014 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are listed
in `verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T33-XB-1` | name a concrete implementation inside the suite body | NEG-02 |
| `T33-XB-2` | copy the suite per implementation instead of a subject | NEG-02 |
| `T33-XB-3` | change an accepted runtime/test byte or the runtime-target inventory | NEG-01, NEG-06 |
| `T33-XB-4` | bind/use TCP/`AF_INET`, DNS, TLS, or a legacy/external peer | NEG-01 |
| `T33-XB-5` | let an unarmed/out-of-window/non-active request emit | NEG-03, NEG-04 |
| `T33-XB-6` | log a payload, permit, secret, private address, or host path | NEG-05 |
| `T33-XB-7` | add a second provider or pre-empt T034 | NEG-07 |
| `T33-XB-8` | introduce a competing interface, RPC, or configuration language | NEG-02 |
| Governance | mark the checkbox in the plan stage or skip the inherited provenance refresh | NEG-06 |
