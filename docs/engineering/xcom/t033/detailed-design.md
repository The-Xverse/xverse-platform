# T033 Detailed Design — Reusable Provider, Observer, Stimulation-Tool, and Gateway Contract Suites

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T033 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → detailed design |
| Revision | 1 (reusable contract-suite slice) |
| Baseline revision | `2fd395e39e44e1f6fe9547998b47499d996b1756` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

T033 realizes four reusable, implementation-agnostic contract suites over the accepted provider, observation,
stimulation-tool, and gateway boundaries, and proves them with four additive `t033-<kind>` drivers. The design is
written **before** implementation; the implementation must realize it exactly or record a design change and
re-review.

## 2. Design decisions

| ID | Decision | Rationale | Requirement |
| --- | --- | --- | --- |
| `T33-DD-01` | Each suite is parameterized by a small subject seam (`ProviderSubject`, `ObserverSubject`, `StimulationToolSubject`, `GatewaySubject`) and names only accepted interfaces or accepted fixture helpers | Makes the suite reusable: a different conforming implementation is validated by a different subject without editing the suite | T033-SR-001, T033-SR-014 |
| `T33-DD-02` | Reuse is evidenced by running the provider suite against two independently implemented providers and the other suites against independent subject instances | Directly realizes the accepted User Story 4 independent test at the suite boundary | T033-SR-014 |
| `T33-DD-03` | The provider suite drives the accepted `ProviderComposition` through the accepted `CoreStackFixture` with a reject-new queue capacity of one item | Deterministic, bounded saturation evidence without unbounded storage | T033-SR-003 |
| `T33-DD-04` | The observer suite publishes through the accepted provider/observation composition, submits two items before polling, then polls, detaches, and re-submits | Proves overflow counters, metadata-only records, exact-handle detach, and route isolation deterministically | T033-SR-004, T033-SR-005, T033-SR-006 |
| `T33-DD-05` | The stimulation-tool suite drives the accepted T029 fixture over the accepted journal/guard/action-path/lease composition | Reuses the accepted permit/policy/action semantics without re-implementing them | T033-SR-007, T033-SR-008 |
| `T33-DD-06` | The gateway suite constructs a **fresh** accepted fixture per arming group | The accepted permit is single-session; a fresh fixture per group avoids cross-group single-session interference | T033-SR-009…T033-SR-013 |
| `T33-DD-07` | Every suite records one bounded `SuiteCheck` per obligation in a `SuiteReport`; a missing check is a failure | Makes the suite outcome auditable and non-skippable | T033-SR-001…T033-SR-016 |
| `T33-DD-08` | Four additive `t033-<kind>` test targets; the runtime-target inventory is unchanged | T012 build contract and additivity | T033-SR-015 |
| `T33-DD-09` | The suites consume only the admitted offline test toolchain and the accepted in-process libraries; no admitted dependency is added and no gRPC runtime is linked | Offline/no-new-dependency rule (`T032-GAP-01`) | T033-SR-015 |
| `T33-DD-10` | The committed suites and drivers retain no payload byte, permit content, secret, private address, or host path | Public-safety rule | T033-SR-015 |
| `T33-DD-11` | T033 authors no production runtime source and no second provider; the provider suite is handed to T034 | Ownership and maturity separation | T033-SR-016 |

## 3. Shared suite vocabulary (`suite_support.hpp`)

```cpp
namespace xverse::xcom::contract_suites {

struct SuiteCheck final { std::string id; bool passed; std::string detail; };

class SuiteReport final {
 public:
  void add(std::string id, bool passed, std::string detail = {});
  [[nodiscard]] bool ok() const noexcept;                 // false unless >=1 check and all pass
  [[nodiscard]] bool passed(std::string_view id) const noexcept;   // false if absent
  [[nodiscard]] std::size_t failures() const noexcept;
  [[nodiscard]] const std::vector<SuiteCheck>& checks() const noexcept;
  [[nodiscard]] std::string failure_detail() const;       // bounded, non-sensitive
 private:
  std::vector<SuiteCheck> checks_;
};

}  // namespace xverse::xcom::contract_suites
```

## 4. Reusable provider suite (`provider_contract_suite.hpp`)

Subject seam: `class ProviderSubject { virtual CommunicationProvider& provider() noexcept = 0; };`.

Driver body: `ProviderContractSuite::run(ProviderSubject&, std::string_view suffix)` builds a
`test::CoreStackFixture` with `activate_now=false`, `queue_capacity=1`, `maximum_payload_bytes=1`, the subject's
provider as the external provider, and `provider_id` from the provider's own descriptor, then records:

| Check | Assertion |
| --- | --- |
| `P-01` | descriptor identity non-empty, `descriptor_compatible()`, nonzero instance identity |
| `P-02` | explicit registration succeeds (`fixture.ready()`) |
| `P-03` | re-registering the same provider yields `duplicate_provider` |
| `P-04` | preparing with contract version `9.9.9` yields `unsupported_contract_version` |
| `P-05` | `prepare_and_activate()` returns a value and the route is active |
| `P-06` | first submit is `accepted` |
| `P-07` | second submit is `queue_saturated` (reject-new, no earlier item lost) |
| `P-08` | route state is `active` with `queued_items()==1` and `queue_capacity()==1` |
| `P-09` | `reconcile()` returns `reconciled` |
| `P-10` | `receive()` returns the exact earlier item (`received`) |
| `P-11` | a further `receive()` reports `queue_empty` |
| `P-12` | `drain()` reports `draining` |
| `P-13` | `close()` reports `closed` |

Reuse driver: the suite is run once over a `LoopbackProvider` subject and once over a `ProbeProvider` subject (an
independently implemented accepted T016 test provider), proving the suite is provider-agnostic.

## 5. Reusable observer suite (`observer_contract_suite.hpp`)

Subject seam: `class ObserverSubject { virtual ObservationHub& hub() noexcept = 0; };`.

Driver body: `ObserverContractSuite::run(ObserverSubject&, std::string_view suffix)` attaches one
metadata-only tap (capacity one) to the subject hub, composes an accepted `observation_test::Scenario` with a
provider queue capacity of three and the subject hub, then records:

| Check | Assertion |
| --- | --- |
| `O-01` | a valid metadata-only tap policy is created |
| `O-02` | the free tap attaches with an exact handle |
| `O-03` | the composed route with an enabled hub is ready |
| `O-04` | the first publish is `accepted` |
| `O-05` | the second publish (before polling) is `accepted` |
| `O-06` | the snapshot reports `queued==1` and `dropped>=1` |
| `O-07` | the polled record has no payload, `payload_view_state()==omitted`, exact route/correlation identity, and the complete source payload size |
| `O-08` | the next poll reports `no_record` |
| `O-09` | detach succeeds |
| `O-10` | a detached handle is rejected by poll and `snapshot()` |
| `O-11` | a further publish is `accepted` (normal route unaffected) |

Reuse driver: the suite is run over two independent `OwnedHubSubject` instances.

## 6. Reusable stimulation-tool suite (`stimulation_tool_contract_suite.hpp`)

Subject seam exposes the action path, the exact permit, emission-call count, last-emission provenance, and
durable-intent-before-emission ordering.

Driver body: `StimulationToolContractSuite::run(StimulationToolSubject&)` records:

| Check | Assertion |
| --- | --- |
| `S-01` | the guard/action path is open over the exact permit/policy |
| `S-02-0`…`S-02-3` | each of `InjectSignal`, `InjectMessage`, `InvokeService`, `EmulateService` returns `Emitted`, increments emission calls by one, keeps synthetic provenance, and preserves the request identity |
| `S-03` | an out-of-window request is not `Emitted` and emits nothing |
| `S-04` | a non-active session request is not `Emitted` and emits nothing |
| `S-05` | the most recent emission observed a durable intent before the host call |

Reuse driver: the suite is run over two independent `MatrixStimulationSubject` instances.

## 7. Reusable gateway suite (`gateway_contract_suite.hpp`)

Subject seam: `class GatewaySubject { virtual std::unique_ptr<GatewayFixture> make_fixture() = 0; };`.

Driver body: `GatewayContractSuite::run(GatewaySubject&)` constructs fresh accepted fixtures per group and
records:

| Check | Assertion |
| --- | --- |
| `G-01` | an opened accepted fixture is ready (`ready()` and `open_path()`) |
| `G-02` | `gateway_operation_names()` has exactly ten names |
| `G-03` | the supported major is negotiated and `QueryVersion` reports `1.0` |
| `G-04` | an unsupported major is rejected and a following submission is rejected with no emission |
| `G-05` | the exact permit arms the session |
| `G-06` | all four allowed actions emit exactly once (`emitted==4`) |
| `G-07` | the lease acquires `LEASE_ACTIVE`, releases `LEASE_RELEASED`, and `lease_held` is false |
| `G-08` | an unarmed session emits nothing and reports a non-success outcome |
| `G-09` | observation open/read/close is bounded by the granted record count |
| `G-10` | framing accepts a valid frame and rejects an over-bound and an unknown-method frame |
| `G-11` | bounded counters include an explicit `evidence_incomplete` count |

Reuse driver: the suite is run over two independent `FactoryGatewaySubject` instances.

## 8. Test design (drivers)

| Driver | Suite | `t033-<kind>` label | Cases |
| --- | --- | --- | --- |
| `provider_suite_tests.cpp` | provider | `t033-provider` | `AcceptedLoopbackProviderConforms`, `SuiteIsReusableAcrossProviderImplementations` |
| `observer_suite_tests.cpp` | observer | `t033-observer` | `AcceptedObservationHubConforms`, `SuiteIsReusableAcrossHubInstances` |
| `stimulation_tool_suite_tests.cpp` | stimulation-tool | `t033-stimulation-tool` | `AcceptedStimulationPathConforms`, `SuiteIsReusableAcrossFixtures` |
| `gateway_suite_tests.cpp` | gateway | `t033-gateway` | `AcceptedGatewaySessionConforms`, `SuiteIsReusableAcrossFixtures` |

Each case asserts `report.ok()` with the bounded `failure_detail()` and the key check identities. All cases use
only the standard library, the accepted in-process libraries, the accepted fixtures, and GTest.

## 9. Failure semantics

| Condition | Outcome |
| --- | --- |
| a required suite check is absent | `SuiteReport::passed` returns false; the case fails closed |
| a provider rejects an unsupported version | `unsupported_contract_version`, no dispatch (`P-04`) |
| a provider queue is full | `queue_saturated`, earlier items preserved (`P-07`) |
| an observer overflows | drop-newest counter increments (`O-06`) |
| an observer detaches | the exact handle is rejected with no route effect (`O-09`…`O-11`) |
| a stimulation request is out of window / non-active | non-emitting rejection, zero emission (`S-03`, `S-04`) |
| a gateway session is unarmed / unsupported major | non-success outcome, zero emission (`G-04`, `G-08`) |
| a gateway frame is over-bound / unknown | `over_bound` / `unknown_method`, no dispatch (`G-10`) |
| the subject is incompatible | a failing check is reported; no implementation is substituted |

## 10. Determinism and safety

- Every check, submit, poll, detach, and fixture construction is finite and bounded; no case depends on ambient
  wall-clock time, randomness, or environment.
- The suites perform only in-process operations over owned synthetic fixtures; no network, DNS, TLS, dynamic
  load, legacy access, or production workload occurs.
- Committed files and evidence contain no credential, private address, real or proprietary payload, or
  environment-specific host path.

## 11. Traceability

| Design element | Requirement | Checks |
| --- | --- | --- |
| `T33-DD-01`/`-02` subject seams and reuse | T033-SR-001, T033-SR-014 | `P-01`, reuse cases |
| `T33-DD-03` provider lifecycle | T033-SR-003 | `P-05`…`P-13` |
| `T33-DD-04` observer | T033-SR-004…`-006` | `O-01`…`O-11` |
| `T33-DD-05` stimulation | T033-SR-007, T033-SR-008 | `S-01`…`S-05` |
| `T33-DD-06` gateway fresh fixture | T033-SR-009…`-013` | `G-01`…`G-11` |
| `T33-DD-07` bounded report | T033-SR-001…`-016` | every check identity |
| `T33-DD-08`/`-09` additive offline delivery | T033-SR-015 | build/discovery inspection |
| `T33-DD-10`/`-11` safety and scope | T033-SR-015, T033-SR-016 | public-safety and changed-path inspection |

## 12. Doxygen and documentation

- The new suite headers carry the X-COM file block (`@file`, `@brief`, `@ownership`, `@lifetime`,
  `@thread_safety`, `@failure`, `@par Traceability`) that the changed test units require; the drivers carry the
  same file block.
- Generated Protocol Buffers documentation remains `DOX-GAP-02` (T037); T033 documents only its hand-written
  suites and drivers.

## 13. Generated-code provenance and compatibility contract

- T033 adds **no** generated code and **no** admitted dependency. It consumes the T030-generated Protocol Buffers
  messages through the accepted gateway fixture, whose committed input is
  `proto/xverse/xcom/v1/tool_gateway.proto` and whose generator is the T011-admitted `libprotoc 3.12.4`. The
  generated outputs live under the git-ignored build tree; the committed `.proto` remains the single source of
  truth.
- **Compatibility contract.** T033 preserves the accepted `XCOM-XLC-002` additive evolution rules (immutable
  package and published field numbers/names; only additive fields/messages/enums/methods; unsupported major
  rejected fail-closed). The gateway suite's `G-02` binds the committed operation table to the ten accepted
  methods and `G-04` proves unsupported-major rejection, so an accepted additive contract change is visible in
  the same change that updates the suites. T033 defines no competing contract, RPC, or configuration language.
