# T034 Architecture — Second Minimal Synthetic Provider and Replaceability / Version-Rejection / Failure-Isolation Proof

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T034 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → architecture |
| Revision | 1 (second-provider replaceability slice) |
| Baseline revision | `f63491101aed1c4f7db57fa7c506ad5c0510038f` |
| Affected source paths | `src/xverse/xcom/fixtures/synthetic_provider.{hpp,cpp}` (new second provider); `tests/xcom/contract_suites/second_provider_{suite,version,isolation}_tests.cpp` (new `t034-<kind>` drivers); `src/xverse/xcom/CMakeLists.txt` (edit, additive); engineering trace/verification records |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-006` provider boundary and composition, `XCOM-CMP-007` owned synthetic provider that proves replaceability, `XCOM-CMP-011` synthetic sink and tools); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-007` provider boundary and composition, `XCOM-DU-008` owned synthetic provider); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-CORE-003`/`-004`/`-005`/`-007`/`-009`); accepted T016 `tests/xcom/core_matrix/test_support.hpp`; accepted T033 `tests/xcom/contract_suites/provider_contract_suite.hpp`; `specs/007-xcom-core/contracts/provider.md`; `specs/007-xcom-core/spec.md` (User Story 4); ADR-0016, ADR-0018, ADR-0019, ADR-0020 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T034 is the **second-provider replaceability** task of the `T-CORE`/GW family. T015 realized the provider
boundary, composition, and the owned loopback provider; T016 consolidated the core matrix; T033 extracted the
reusable provider contract suite behind a `ProviderSubject` seam. T034 adds a *second* minimal synthetic
provider implementation and validates it with the *same* T033 suite body, then proves that an unsupported
contract version or capability is rejected fail-closed and that a provider/route failure does not affect an
unrelated route.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013/T-CORE vocabulary (read-only)
   → T015 provider boundary, composition, owned loopback provider (read-only)
   → T016 core matrix fixtures and negative cases (read-only)
   → T017–T020 XDL Profile + activation-plan digest binding (read-only)
   → T021–T024 observation boundary (read-only) → T025–T029 stimulation boundary (read-only)
   → T030 versioned external-tool contract (read-only) → T031 bounded local-IPC-only gateway (read-only)
   → T032 separate-process synthetic client (read-only)
   → T033 reusable provider/observer/stimulation-tool/gateway contract suites (read-only)
   → T034 second minimal synthetic provider + replaceability/version-rejection/failure-isolation (this slice)
   → T035–T041 evidence/review/acceptance
```

T034 adds one new fixture provider and three additive test drivers. It changes no accepted production
provider/composition/loopback source, no accepted T033 suite body, no other accepted test, target, label,
command, or expected value, and no accepted register.

## 3. Boundary and context

### 3.1 System context

```text
   ┌────────────── accepted capability-007 anchors (read-only) ──────────────┐
   │  spec.md FR-006/007/010/014/022/026/027/028/029/030/035 · US4 ·           │
   │    contracts/provider.md ("remain replaceable by another conforming       │
   │    provider"; "reject unsupported semantics before activation")           │
   │  t009 XCOM-CMP-006/007/011 · t010 XCOM-DU-007/008                         │
   │  t008 XCOM-SW-CORE-003/004/005/007/009                                     │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ realized by
   ┌──────── accepted implementations and fixtures (read-only, consumed) ────┐
   │  T015 provider.hpp CommunicationProvider / ProviderComposition            │
   │  T016 core_matrix test_support (CoreStackFixture, ProbeProvider,          │
   │      make_descriptor, loopback_descriptor)                                │
   │  T033 contract_suites/provider_contract_suite.hpp (ProviderSubject,       │
   │      ProviderContractSuite::run)                                          │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ validated by
   ┌──────────────────── T034 owned artifacts (this slice) ────────────────────────┐
   │  src/xverse/xcom/fixtures/synthetic_provider.hpp (SyntheticProvider)           │
   │  src/xverse/xcom/fixtures/synthetic_provider.cpp                                │
   │  tests/xcom/contract_suites/second_provider_suite_tests.cpp   (t034-replaceability) │
   │  tests/xcom/contract_suites/second_provider_version_tests.cpp (t034-version)   │
   │  tests/xcom/contract_suites/second_provider_isolation_tests.cpp (t034-isolation) │
   │  src/xverse/xcom/CMakeLists.txt (additive registration only)                    │
   │  guarantee : independent bounded provider storage, unchanged reused suite,      │
   │      fail-closed version/capability rejection, unrelated-route isolation,       │
   │      no runtime-target inventory change, no network/legacy access               │
   └──────────────────────────────────┬──────────────────────────────────────────────┘
                                      ▼
                     T035–T041 evidence/review/acceptance
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T34-XB-1` Second provider vs accepted provider implementation | the new `SyntheticProvider` and its independent storage | the accepted `provider.hpp` boundary, composition, and loopback provider | The second provider implements only the accepted interface and changes no accepted provider/composition/loopback byte (`T034-SR-001`). |
| `T34-XB-2` Reuse vs a second conformance definition | the unchanged T033 suite body and its `ProviderSubject` seam | a per-provider copy of the suite or a competing conformance interface | The second provider is validated through a new subject; the suite header is not edited (`T034-SR-002`, `T034-SR-010`). |
| `T34-XB-3` Candidate vs accepted predecessor | the new fixture/driver paths and the additive `CMakeLists.txt` registration | any accepted `src/` or `tests/` byte, target, label, command, or expected value | Only the declared T034 paths change; the runtime-target inventory is unchanged (`T034-SR-011`). |
| `T34-XB-4` Synthetic vs external | owned in-process fixtures and bounded local storage | any legacy binary, external peer, TCP listener, DNS, resolver, TLS, or production workload | The second provider is in-process only; no network or legacy resource is contacted (`T034-SR-014`, FR-028). |
| `T34-XB-5` Version/capability gate vs provider dispatch | the accepted registration and preparation gates | an unsupported version/capability reaching a provider | A misreported version/capability or an unsupported request is rejected fail-closed before activation with zero emission (`T034-SR-005`…`-007`). |
| `T34-XB-6` Failure containment vs unrelated routes | one route/provider failure | an unrelated active route's activity, bounds, and observable state | A failure or rejection on one route leaves unrelated routes active, bounded, and observable (`T034-SR-008`, `T034-SR-009`). |
| `T34-XB-7` Evidence vs content | stable codes, phase, logical identity, size, timing, and outcome | payload bytes, permit contents, secrets, private addresses, host paths | Committed files and bounded logs contain none of the excluded content (`T034-SR-012`, FR-027). |
| `T34-XB-8` Fixture target vs runtime inventory | a fixture source compiled into the additive `t034-<kind>` test executables | `XVERSE_XCOM_RUNTIME_TARGETS` and any accepted runtime library | No runtime library is added or changed; the inventory is unchanged (`T034-SR-011`, T032 precedent). |

### 3.3 Prohibited elements (must remain absent)

No change to the accepted provider boundary, composition, loopback provider, T030 contract, T031 gateway, T032
client, or T033 suites; no TCP listener or `AF_INET`/`AF_INET6` socket, DNS, resolver, or TLS use; no external
network peer; no legacy binary, legacy repository, or production workload; no compiled or linked gRPC runtime;
no new admitted dependency; no unbounded queue, route, or storage; no version/capability/permit bypass; no
payload, permit, secret, private address, or host path in a log record or committed file; no ambient
wall-clock-dependent verdict; no change to an accepted predecessor `src/`, `tests/`, `xdl/`, or
`docs/engineering/xcom/t0{07..33}/` byte; no rewrite or weakening of an accepted ADR, requirement, contract,
schema, register, or REF-002 disposition; no acceptance or integration of the candidate.

## 4. Components

`T34-*` names are local to this document; the accepted `XCOM-DU-007`, `XCOM-DU-008`, `XCOM-CMP-006`,
`XCOM-CMP-007`, and `XCOM-CMP-011` identifiers are the authorized units/components.

### 4.1 New T034 components

- **`T34-CMP-PROVIDER` Second minimal synthetic provider** (`src/xverse/xcom/fixtures/synthetic_provider.hpp`
  and `.cpp`): the `SyntheticProvider` implementation over the accepted `CommunicationProvider` interface with
  independent finite route/queue storage, its own nonzero instance identity, a storage-bounded
  `descriptor_compatible()` predicate, and a test seam for a configured forced failure.
- **`T34-CMP-SUITE` Replaceability driver** (`tests/xcom/contract_suites/second_provider_suite_tests.cpp`): a
  new `ProviderSubject` adapter that runs the *unchanged* T033 `ProviderContractSuite` against the second
  provider and proves bounded capability/saturation and lifecycle behavior.
- **`T34-CMP-VERSION` Version/capability rejection driver**
  (`tests/xcom/contract_suites/second_provider_version_tests.cpp`): proves fail-closed rejection of a
  misreported contract version at registration, an unsupported requested version before activation, a
  misreported capability at registration, an unsupported requested capability before activation, and zero
  emission on every rejection.
- **`T34-CMP-ISOLATION` Failure-isolation driver**
  (`tests/xcom/contract_suites/second_provider_isolation_tests.cpp`): proves a provider/route failure yields a
  stable non-success with no emission and that an unrelated active route stays active, bounded, and observable.
- **`T34-CMP-BUILD`** (T012): the subtree build extended additively by the fixture compilation and three
  `t034-<kind>` test targets; the runtime-target inventory is unchanged.
- **`T34-WP`** — the T034 repository-owned work-product set.

### 4.2 Consumed components (read-only)

- **`T34-CMP-T015`** — the accepted `provider.hpp` `CommunicationProvider` interface, `ProviderComposition`,
  `ProviderDescriptor`, `ProviderRouteRequirements`, `ProviderOutcome`, and the accepted owned `LoopbackProvider`.
  Consumed read-only, unchanged.
- **`T34-CMP-T016`** — accepted core-matrix test support (`CoreStackFixture`, `ProbeProvider`, `make_descriptor`,
  `loopback_descriptor`, `kAllInteractions`). Consumed read-only.
- **`T34-CMP-T033`** — the accepted reusable provider suite (`ProviderContractSuite`, `ProviderSubject`) and its
  `SuiteReport` vocabulary. Consumed read-only, unchanged.
- **`T34-CMP-T011`/`T012`** — the admitted offline envelope and the subtree build/test contract. No rule is
  weakened and no dependency is added.

## 5. Data flow (ordered)

1. **Build the drivers.** The subtree build compiles the accepted libraries, the second-provider fixture source,
   and the three `t034-<kind>` test executables under the warning-as-error policy. The runtime-target inventory
   is unchanged.
2. **Construct the second provider.** A driver builds a `SyntheticProvider` over a caller-supplied descriptor
   within its finite storage and supplies it through a `ProviderSubject`.
3. **Run the reused suite.** The unchanged `ProviderContractSuite::run` drives the second provider through
   `P-01`…`P-13` and records one bounded `SuiteCheck` per obligation.
4. **Exercise version/capability gates.** A misreporting descriptor is rejected at registration; an unsupported
   requested version or capability is rejected before activation; each rejection issues no handle and emits no
   item.
5. **Exercise failure isolation.** A second provider configured to fail yields a stable non-success with no
   emission; an unrelated active route on an independently composed provider (and a rejected provider registered
   into the same composition) leaves that route active, bounded, and observable.
6. **Register additively.** The build compiles the fixture into three `t034-<kind>` test targets; the
   runtime-target inventory is unchanged and no existing target, label, command, or value changes.

## 6. Interfaces

### 6.1 New interfaces (`src/xverse/xcom/fixtures/synthetic_provider.hpp`)

| Element | Contract |
| --- | --- |
| `SyntheticProvider(const ProviderDescriptor&)` | retains a caller-validated descriptor; storage fits at most `kMaximumRoutes` routes and `kMaximumQueueItems` items per route |
| `descriptor()` | returns the immutable retained descriptor |
| `descriptor_compatible()` | true only for nonzero masks within the finite storage limits; false makes explicit registration fail with `invalid_descriptor` |
| `instance_id()` | returns an opaque nonzero per-instance identity distinct from the loopback provider |
| `configure_forced_failure(ProviderOutcome)` | test seam: the configured stable outcome is returned by `prepare`/`submit` without mutating route state |
| private `prepare`/`activate`/`submit`/`receive`/`drain`/`close`/`state`/`reconcile` | overrides of the accepted `CommunicationProvider` private virtuals; invoked only by `ProviderComposition` |

### 6.2 Reused test interfaces (`tests/xcom/contract_suites/**`)

| Element | Contract |
| --- | --- |
| `ProviderSubject` (T033) | `provider()` returns the `CommunicationProvider&` under test; T034 supplies a new adapter and does not edit the seam |
| `ProviderContractSuite::run` (T033) | the unchanged reusable driver; T034 invokes it against the second provider |
| `SuiteReport`/`SuiteCheck` (T033) | bounded report vocabulary; `ok()` is false unless at least one check exists and every check passed |

### 6.3 Consumed contract (read-only, unchanged)

| Interface | Contract consumed (unchanged) |
| --- | --- |
| `CommunicationProvider`, `ProviderComposition`, `ProviderDescriptor`, `ProviderRouteRequirements` | descriptor validation, explicit registration, version/capability negotiation, and lifecycle dispatch |
| `ProviderOutcome`, `ProviderRouteState`, `ProviderRouteSnapshot` | stable outcomes, bounded route state, and queue disposition |
| `test::CoreStackFixture` (T016) | one-route bounded fixture with an external provider and caller-selected requirements |
| GTest and the accepted offline fixtures | the admitted offline test framework and owned synthetic fixtures |

## 7. Concurrency and resource bounds

| Aspect | T034 decision |
| --- | --- |
| Production footprint | one new fixture provider header/source and three additive test executables; no new runtime library |
| Build inventory | three `t034-<kind>` test targets (`replaceability`, `version`, `isolation`); `XVERSE_XCOM_RUNTIME_TARGETS` unchanged |
| Processes | none; the second provider is in-process; no legacy, external, or production process |
| Writers | one mutex per second-provider instance serializes route and queue mutation |
| Threads | single declared user per driver; no unbounded thread or queue |
| Operations per provider | finite and declared (prepare/activate/submit/receive/drain/close/state/reconcile) |
| Storage | fixed route slots and a fixed reject-new queue prefix; saturation reports `queue_saturated` without allocation |
| Transport | none beyond the accepted in-process composition; no network, DNS, TLS, or legacy access |
| Time | no verdict depends on ambient wall-clock time |
| Determinism | the checks, bounds enforcement, and outcomes are deterministic for fixed inputs; repeated runs are equal |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Replaceability | a second independently written provider validated by the unchanged T033 suite body | `T034-SR-001`, `T034-SR-002`; `T034SecondProviderSuite.*` |
| Bounded provider semantics | finite route/queue storage with reject-new saturation | `T034-SR-003`, `T034-SR-004`; provider checks `P-05`…`P-13` |
| Fail-closed version/capability rejection | registration and preparation gates reject before activation with zero emission | `T034-SR-005`…`-008`; `T034VersionRejection.*` |
| Failure containment | a route/provider failure cannot change an unrelated route | `T034-SR-009`; `T034FailureIsolation.*` |
| Additive delivery | three new test targets, no runtime library added; inventory unchanged | `T034-SR-011` |
| Public-safe evidence | no payload/permit/secret/private-address/host-path in a committed file or log | `T034-SR-012` |
| Governance and envelope honesty | registers re-validated; REF-002 unchanged; T035–T041 allocated | `T034-SR-013` |
| In-process honesty | no network, DNS, TLS, legacy, or production resource | `T034-SR-014` |

## 9. Consistency and constraints

- **Dependency direction preserved.** T034 consumes the accepted T007–T033 design and fixtures; it introduces
  no dependency on a later slice, an external peer, or a legacy repository, and adds no admitted dependency.
- **Domain neutrality preserved.** Only generic X-COM vocabulary appears (provider, route, descriptor,
  capability, identity, generation, bound, outcome); no automotive, product, protocol, or configuration
  primitive is introduced.
- **XDL centrality preserved.** T034 neither parses nor authors XDL; plan/graph digests appear only as opaque
  logical identities already bound by the accepted plan.
- **Logical/physical separation preserved.** The second provider is a logical realization; no address, port, or
  physical transport enters the provider boundary.
- **Ownership preserved.** Only the declared T034 paths change; every accepted production byte and existing test
  is preserved except the additive `CMakeLists.txt` registration.
- **Maturity preserved.** The slice implements the second provider and its proof only; executed evidence and
  acceptance remain T035–T041.

## 10. Traceability

| Architecture element | T034 requirements |
| --- | --- |
| `T34-XB-1`, `T34-CMP-PROVIDER` | T034-SR-001, T034-SR-003, T034-SR-004, T034-SR-008, T034-SR-014 |
| `T34-XB-2`, `T34-CMP-SUITE`, `T34-CMP-T033` | T034-SR-002, T034-SR-010 |
| `T34-XB-3`, `T34-CMP-BUILD`, `T34-WP` | T034-SR-011, T034-SR-013 |
| `T34-XB-4` | T034-SR-014 |
| `T34-XB-5`, `T34-CMP-VERSION` | T034-SR-005, T034-SR-006, T034-SR-007 |
| `T34-XB-6`, `T34-CMP-ISOLATION` | T034-SR-008, T034-SR-009 |
| `T34-XB-7` | T034-SR-012 |
| `T34-XB-8` | T034-SR-011 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are listed
in `verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T34-XB-1` | change an accepted provider/composition/loopback byte or duplicate the interface | NEG-01, NEG-02 |
| `T34-XB-2` | copy the T033 suite or introduce a competing conformance interface | NEG-02 |
| `T34-XB-3` | change an accepted runtime/test byte or the runtime-target inventory | NEG-01, NEG-06 |
| `T34-XB-4` | bind/use TCP/`AF_INET`, DNS, TLS, or a legacy/external peer | NEG-05 |
| `T34-XB-5` | let an unsupported version or capability reach activation | NEG-03 |
| `T34-XB-6` | let a route/provider failure perturb an unrelated route | NEG-04 |
| `T34-XB-7` | log a payload, permit, secret, private address, or host path | NEG-05 |
| `T34-XB-8` | add a runtime library or change the runtime-target inventory | NEG-06 |
| Governance | mark the checkbox in the plan stage or skip the inherited provenance refresh | NEG-06 |
