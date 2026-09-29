# T034 Implementation Record — Second Minimal Synthetic Provider and Replaceability / Version-Rejection / Failure-Isolation Proof

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T034 (capability 007, slice `T-CORE`/GW) |
| Stage / role | implementation |
| Revision | 1 |
| Accepted baseline revision | `f63491101aed1c4f7db57fa7c506ad5c0510038f` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 1 |
| Classification | Public-safe engineering work product |

This record describes what the T034 candidate implements. It does not accept or integrate the
candidate; user acceptance remains T041 and is deferred until the ordered backlog
`xcom-t030-t034-20260928` completes. External Codex review is likewise deferred.

## 2. Implemented boundary

T034 implements one **second minimal synthetic provider** (`SyntheticProvider`) and three additive
`t034-<kind>` drivers:

- `src/xverse/xcom/fixtures/synthetic_provider.{hpp,cpp}` — an independently written fixed-array
  provider over the accepted `CommunicationProvider` interface with two route slots, a fixed
  reject-new queue prefix of eight items, a nonzero per-instance identity disjoint from the loopback
  provider, a storage-bounded `descriptor_compatible()` predicate, and a bounded forced-failure test
  seam (`configure_forced_failure`).
- `tests/xcom/contract_suites/second_provider_suite_tests.cpp` (`t034-replaceability`) — runs the
  **unchanged** accepted T033 `ProviderContractSuite` against the second provider through a new
  `SyntheticProviderSubject` adapter and checks bounded capability/saturation and full lifecycle.
- `tests/xcom/contract_suites/second_provider_version_tests.cpp` (`t034-version`) — fail-closed
  version and capability rejection at explicit registration and before activation, with zero
  emission on every rejection path.
- `tests/xcom/contract_suites/second_provider_isolation_tests.cpp` (`t034-isolation`) — a
  provider/route failure or rejected adapter emits nothing and leaves an unrelated active route
  active, bounded, and observable with its exact retained items.

It adds no production runtime source, no runtime library, no admitted dependency, and no gRPC
runtime link, and it changes no accepted provider, composition, loopback, T030 contract, T031
gateway, T032 client, or T033 suite byte.

### 2.1 Design realization notes

- `T34-DD-01`/`T34-DD-02` — the second provider is validated by the unchanged T033
  `ProviderContractSuite` through the new `SyntheticProviderSubject`; the suite header and
  `ProviderSubject` seam are consumed read-only. Its fixed route slots and reject-new queue are
  written independently of the accepted loopback storage.
- `T34-DD-03` — `descriptor_compatible()` checks only nonzero capability masks and finite storage.
  It deliberately does not check the contract version, so a `2.0.0` descriptor is rejected by the
  accepted composition registration gate with `unsupported_contract_version` rather than as
  `invalid_descriptor`; a descriptor beyond the finite storage is rejected as `invalid_descriptor`.
- `T34-DD-04` — `configure_forced_failure(ProviderOutcome)` returns the configured stable outcome
  from `prepare`/`submit` without mutating route state. It is used to prove both a prepare-path and a
  submit-path failure with zero emission.
- `T34-DD-05` — the version driver exercises rejection both at explicit registration (a misreporting
  provider) and at preparation (an unsupported request), matching the accepted User Story 4
  independent test.
- `T34-DD-06` — isolation is proven for an independently composed failing route and for a rejected
  provider registered into the **same** composition as the unrelated active route.
- `T34-DD-07`/`T34-DD-08` — the fixture source is compiled directly into each `t034-<kind>` test
  executable (no new library target) and the three drivers carry the distinct labels
  `t034-replaceability`, `t034-version`, and `t034-isolation`.

### 2.2 Recorded design refinement

The second provider exposes three bounded, non-sensitive observation accessors —
`prepare_dispatch_count()`, `submit_dispatch_count()`, and `accepted_item_count()` — in addition to
the design's `configure_forced_failure` seam. They are required to assert the "emission count" output
of `T034-SR-008` and the "zero emission" criterion deterministically (the accepted `ProviderComposition`
exposes no provider-internal counter, and no provider-route handle exists on a rejected preparation).
They mutate no route state, do not weaken any accepted contract, and mirror the accepted T016
`ProbeProvider` call-counter precedent. No requirement statement, check, expected value, component,
unit case, or label changed.

## 3. Changed-path inventory (candidate)

Implementation:

- `src/xverse/xcom/fixtures/synthetic_provider.hpp` (new)
- `src/xverse/xcom/fixtures/synthetic_provider.cpp` (new)
- `tests/xcom/contract_suites/second_provider_suite_tests.cpp` (new)
- `tests/xcom/contract_suites/second_provider_version_tests.cpp` (new)
- `tests/xcom/contract_suites/second_provider_isolation_tests.cpp` (new)
- `src/xverse/xcom/CMakeLists.txt` (shared; only the additive T034 `foreach` block adding the three
  `t034-<kind>` targets)
- `specs/007-xcom-core/tasks.md` (shared; T034 checkbox line only)

Work products (`docs/engineering/xcom/t034/`): `requirements.md`, `architecture.md`,
`detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, and this `implementation.md`.

Engineering records:

- `engineering/project.json` — current task T034 and accepted baseline
  `f63491101aed1c4f7db57fa7c506ad5c0510038f`.
- `engineering/requirements/T034-STK-00{1..5}.json`, `engineering/requirements/T034-SR-0{01..14}.json`.
- `engineering/architecture/components/T034-SR-0{01..14}-CMP.json`.
- `engineering/unit-specifications/T034-SR-0{01..14}-U.json`.
- `engineering/validation/scenarios/T034-VS-ACCUMULATED.json`.
- `engineering/trace/links.json` — additive T034 links and the inherited
  `src/xverse/xcom/CMakeLists.txt` `implemented_by` digest refresh.
- `engineering/verification/measures/{unit,integration,validation}.json` — refreshed to the thirteen
  discovered T034 cases.
- `engineering/stage-results/*.json` — inherited `src/xverse/xcom/CMakeLists.txt` and
  `engineering/trace/links.json` digest refresh only.
- `reports/review-index.md` — T034 candidate section appended.

No accepted production source, header, contract, schema, register, or predecessor work product was
changed.

## 4. Generated-code provenance (inherited T030 contract)

T034 adds **no** generated code and **no** admitted dependency. It does not touch
`proto/xverse/xcom/v1/tool_gateway.proto` or any `XCOM-XLC-002` message and links no transport
runtime. The committed protocol input and the admitted offline generator identity are unchanged from
the accepted T030/T031/T032/T033 records:

| Provenance item | Value |
| --- | --- |
| Input schema identity | `proto/xverse/xcom/v1/tool_gateway.proto`, SHA-256 `cbb65f901b8522120da6333c4e569d4d8fa00db601abd7effaf70abe925dbb2d` |
| Protocol Buffers generator | admitted offline `libprotoc 3.12.4` (T011 admission) |
| Source of truth | the committed `.proto`; generated outputs live only under the git-ignored build tree |
| gRPC transport runtime | not compiled, not linked (`T032-GAP-01` unchanged) |

The generated-code version checks and the committed operation-table binding remain exactly as the
accepted T030/T031/T032/T033 evidence records them; T034 consumes no generated symbol.

## 5. Build wiring and runtime inventory

The three additive `t034-<kind>` test targets are registered in `src/xverse/xcom/CMakeLists.txt`
under the inherited warning-as-error policy. The second-provider fixture source is compiled directly
into each test executable, so **no** runtime library is added and `XVERSE_XCOM_RUNTIME_TARGETS` is
byte-for-byte unchanged. No existing target, test name, label, command, or expected value changes and
no existing discovery count is reduced. Each driver carries one hyphenated label (CMake 3.22 label
workaround). The fixture header is reached through the `${CMAKE_CURRENT_SOURCE_DIR}/fixtures` include
root; the accepted T033 suite and T016 fixtures are consumed read-only through the
`${PROJECT_SOURCE_DIR}/tests/xcom` include root.

## 6. Verification performed (candidate working tree)

Offline admitted build with the T011 toolchain and the T025 GTest prefix; commands and outcomes
retained in the T034 evidence bundle (T035). Measured on the candidate working tree:

- `cmake --build build/fabro-t030-t034-system-unit` — clean under `-Werror`; `ninja: no work to do`
  after the first build.
- `ctest --test-dir build/fabro-t030-t034-system-unit -L t034-` — `100% tests passed, 0 tests failed
  out of 13` (4 replaceability, 5 version, 4 isolation).
- `ctest --test-dir build/fabro-t030-t034-system-unit -N -L t034-` — `Total Tests: 13`.
- `ctest --test-dir build/fabro-t030-t034-system-unit -L 't0(20|2[6-9]|3[0-4])-'` — `100% tests
  passed, 0 tests failed out of 242` (the preserved inherited suites plus the thirteen `t034-` cases).
- `ctest --test-dir build/fabro-t030-t034-system-unit -N` — `Total Tests: 496`.
- `python3 -m pytest -q` — `150 passed, 24 subtests passed`.
- Forbidden-API/public-safety scan of the new fixture and drivers — no `AF_INET`/`AF_INET6` socket,
  listener, DNS, resolver, TLS, external peer, legacy binary, or production-workload use.
- `git diff --check f63491101aed1c4f7db57fa7c506ad5c0510038f --` — clean.

### 6.1 Candidate artifact content hashes (SHA-256)

| Artifact | SHA-256 |
| --- | --- |
| `src/xverse/xcom/fixtures/synthetic_provider.hpp` | `e8778efb68ee2b2811efe2c7fb73ee1d4543aed185c39856383ea5618671bc71` |
| `src/xverse/xcom/fixtures/synthetic_provider.cpp` | `7cfcce758e43feda52766eae87591f2b6bda2f527f421f1113e5b8c5fc437665` |
| `tests/xcom/contract_suites/second_provider_suite_tests.cpp` | `d6bb3906275495d27e44ace9f4a6ad078022945ec48091cf4dc035e1aef2eddc` |
| `tests/xcom/contract_suites/second_provider_version_tests.cpp` | `354bfa2f6734e12f863e5d365774a068a749d59d0d0e9f75f0cde64623279af6` |
| `tests/xcom/contract_suites/second_provider_isolation_tests.cpp` | `cd629acc69fef76f593bb89297de74cee80fb8c62e27d2a8563adc92ad43618b` |
| `src/xverse/xcom/CMakeLists.txt` (additive T034 block) | `3e20b31a48e8339a2065563b9a4f02cbdb01346b27ee8a9ecd317d44ac869469` |

The complete candidate hash manifest, including the work products and engineering records, is
emitted at package time in `reports/xcom-queue/t034-package.json` and is the authoritative inventory
for the candidate. The `engineering/trace/links.json` `implemented_by` digests that pin these files
and the T034 work products are refreshed to the same bytes.

## 7. Requirement-to-case result

| Requirement | Primary checks | Executed cases |
| --- | --- | --- |
| T034-SR-001 | CHK-02 | `T034SecondProviderSuite.ProviderIsIndependentOfLoopback` |
| T034-SR-002 | CHK-05, CHK-06 | `T034SecondProviderSuite.ReusedProviderContractSuitePasses` |
| T034-SR-003 | CHK-03 | `T034SecondProviderSuite.BoundedCapabilitiesAndSaturation` |
| T034-SR-004 | CHK-04 | `T034SecondProviderLifecycle.CompletesFullBoundedLifecycle` |
| T034-SR-005 | CHK-07 | `T034VersionRejection.MisreportedContractVersionRejectedAtRegistration` |
| T034-SR-006 | CHK-08 | `T034VersionRejection.UnsupportedRequestedVersionRejectedBeforeActivation` |
| T034-SR-007 | CHK-09, CHK-10 | `T034VersionRejection.MisreportedCapabilityRejectedAtRegistration`, `T034VersionRejection.UnsupportedRequestedCapabilityRejectedBeforeActivation` |
| T034-SR-008 | CHK-11 | `T034FailureIsolation.ProviderFailureYieldsStableOutcomeNoEmission` |
| T034-SR-009 | CHK-12, CHK-13 | `T034FailureIsolation.UnrelatedRouteRemainsActiveAndBounded`, `T034FailureIsolation.UnrelatedRouteStateStaysObservable`, `T034FailureIsolation.RejectedAdapterLeavesUnrelatedRouteIntact` |
| T034-SR-010 | CHK-05, CHK-16 | `T034SecondProviderSuite.ReusedProviderContractSuitePasses` plus the unchanged-header inspection |
| T034-SR-011 | CHK-16, CHK-17 | build/discovery inspection plus the contributory `T034SecondProviderSuite.BoundedCapabilitiesAndSaturation` |
| T034-SR-012 | CHK-18, CHK-19 | file-block/public-safety inspection plus the contributory `T034FailureIsolation.UnrelatedRouteRemainsActiveAndBounded` |
| T034-SR-013 | CHK-14, CHK-21, CHK-22 | register/trace validators and the deterministic Phase 7 gate plus the contributory `T034SecondProviderSuite.ProviderIsIndependentOfLoopback` |
| T034-SR-014 | CHK-01, CHK-20 | forbidden-API/public-safety inspection plus the contributory `T034SecondProviderSuite.ReusedProviderContractSuitePasses` |

`T034VersionRejection.RejectionEmitsNothing` contributes to `T034-SR-005`, `T034-SR-006`, and
`T034-SR-007` by asserting zero emission after each rejection path.

## 8. Inherited provenance refresh

Editing `src/xverse/xcom/CMakeLists.txt` and `engineering/trace/links.json` invalidated inherited
digests. Following the T020/T026–T033 precedent, this stage refreshed only the affected values:
every `implemented_by` link in `engineering/trace/links.json` whose target is
`src/xverse/xcom/CMakeLists.txt`, and every `sha256` in `engineering/stage-results/*.json` whose path
is `src/xverse/xcom/CMakeLists.txt` or `engineering/trace/links.json`. No requirement, link
identity, relation, measure, stage result, or expected value changed.

## 9. Maintenance notes

- Add a further conforming provider by implementing one new `ProviderSubject` adapter in a driver and
  a new fixture; do not edit the T033 suite headers or the accepted provider boundary.
- The second provider is a fixture compiled into the `t034-<kind>` test executables. A future
  production provider must not be added to a runtime library without an explicit capability
  authorization and a `XVERSE_XCOM_RUNTIME_TARGETS` update.
- Generated Protocol Buffers documentation remains `DOX-GAP-02` (T037).
- The forced-failure seam and the three bounded counters are test-only observability; they must not be
  treated as a production control surface.

## 10. Limitations

- **T034-GAP-01** — replaceability is proven only against owned, in-process synthetic providers; no
  third-party, network, transport, or legacy-provider compatibility claim is made.
- **T034-GAP-02** — isolation is demonstrated for an unrelated route on an independently composed
  provider and for a rejected provider registered into the same composition; the accepted composition
  model owns one registry and one active route per fixture, so an arbitrary multi-route topology is
  not exercised.
- **T034-GAP-03** — the admitted T011 envelope still cannot link the gRPC transport runtime
  (`T032-GAP-01`); T034 validates the in-process provider boundary only.
- **T034-GAP-04** — no deployed-service, runtime-success, or production-readiness claim is made.

## 11. Maturity

The second minimal synthetic provider and its replaceability, version-rejection, and failure-isolation
proof are implemented for the T034 slice. `XCOM-SW-CORE-003`, `-004`, `-005`, `-007`, and `-009`
remain unchanged accepted text; the per-task projection records this slice's contribution. T035–T041
(evidence, static analysis, Doxygen, review, acceptance) remain allocated, and the REF-002 disposition
stays `unchanged` with an empty `promoted` list.
