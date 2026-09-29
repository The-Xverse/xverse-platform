# T034 Verification Plan — Second Minimal Synthetic Provider and Replaceability / Version-Rejection / Failure-Isolation Proof

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T034 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → verification design |
| Revision | 1 (second-provider replaceability slice) |
| Baseline revision | `f63491101aed1c4f7db57fa7c506ad5c0510038f` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

"Verified" means the named test case or inspection exists, is deterministic, and passes at the recorded
candidate revision. It is not a deployed-service, remote-tool, compatibility, or production-readiness claim.

## 2. Verification environment

- Offline admitted X-COM build envelope (T011): admitted `protoc` 3.12.4, admitted GTest prefix, admitted
  standard library and in-process libraries; no network, DNS, TLS, legacy binary, or production workload.
- C++20, warning-as-error (T012), Ninja build, GoogleTest discovery per `t034-<kind>` label.
- CTest cases are executed through the three drivers; the second provider is validated by the reused T033
  `ProviderContractSuite`.

## 3. Requirements-to-check matrix

| Requirement | Primary checks | Verification measure |
| --- | --- | --- |
| T034-STK-001 | CHK-01, CHK-02, CHK-03, CHK-04 | unit / integration / validation |
| T034-STK-002 | CHK-05, CHK-06 | unit / integration / validation |
| T034-STK-003 | CHK-07, CHK-08, CHK-09, CHK-10 | unit / validation |
| T034-STK-004 | CHK-11, CHK-12, CHK-13 | unit / validation |
| T034-STK-005 | CHK-14, CHK-15, CHK-19, CHK-20 | unit / validation / gate |
| T034-SR-001 | CHK-02 | unit |
| T034-SR-002 | CHK-05, CHK-06 | unit |
| T034-SR-003 | CHK-03 | unit |
| T034-SR-004 | CHK-04 | unit |
| T034-SR-005 | CHK-07 | unit |
| T034-SR-006 | CHK-08 | unit |
| T034-SR-007 | CHK-09, CHK-10 | unit |
| T034-SR-008 | CHK-11 | unit |
| T034-SR-009 | CHK-12, CHK-13 | unit |
| T034-SR-010 | CHK-05, CHK-16 | unit / validation |
| T034-SR-011 | CHK-16, CHK-17 | validation |
| T034-SR-012 | CHK-18, CHK-19 | validation |
| T034-SR-013 | CHK-14, CHK-21, CHK-22 | validation / gate |
| T034-SR-014 | CHK-01, CHK-20 | validation |

## 4. Named checks

| Check | Description | Requirement |
| --- | --- | --- |
| CHK-01 | the second provider and its drivers use only in-process owned storage; the forbidden-API/public-safety inspection finds no TCP/`AF_INET`/DNS/TLS/legacy/external token | T034-SR-014 |
| CHK-02 | `SyntheticProvider` implements the accepted `CommunicationProvider` interface with a valid descriptor, a storage-bounded `descriptor_compatible()`, and a nonzero identity distinct from loopback (source/case inspection) | T034-SR-001 |
| CHK-03 | provider checks `P-02`, `P-06`, `P-07`, `P-08` pass on the second provider (registration, accepted, `queue_saturated`, bounded active state) | T034-SR-003 |
| CHK-04 | provider checks `P-05`, `P-09`…`P-13` pass on the second provider (activate, reconcile, FIFO receive, empty, drain, close) | T034-SR-004 |
| CHK-05 | the unchanged `ProviderContractSuite::run` returns `ok()` with `P-01`…`P-13` on the second provider | T034-SR-002, T034-SR-010 |
| CHK-06 | the T033 suite header and `ProviderSubject` seam are unmodified and the second provider is supplied only through a new adapter | T034-SR-002, T034-SR-010 |
| CHK-07 | a `2.0.0` second provider is rejected at registration with `unsupported_contract_version` and no handle is issued | T034-SR-005 |
| CHK-08 | a request naming `9.9.9` over a registered `1.0.0` second provider is rejected before activation with `unsupported_contract_version` | T034-SR-006 |
| CHK-09 | a descriptor beyond the finite storage is rejected with `invalid_descriptor` | T034-SR-007 |
| CHK-10 | an unsupported requested capability is rejected before activation with the matching stable `unsupported_*` outcome | T034-SR-007 |
| CHK-11 | a configured provider failure returns the exact stable outcome and emits no item | T034-SR-008 |
| CHK-12 | the unrelated active route stays active, accepts a further item, and keeps `queued_items()`/`queue_capacity()` unchanged | T034-SR-009 |
| CHK-13 | the unrelated route's snapshot and reconcile outcome stay observable and consistent after the failure/rejection | T034-SR-009 |
| CHK-14 | every T034 requirement refines a stakeholder requirement and is covered by at least one case or named inspection; the trace validates | T034-SR-013 |
| CHK-15 | no case verdict depends on ambient wall-clock time; repeated runs are equal | T034-SR-013 |
| CHK-16 | three additive `t034-<kind>` targets exist; the fixture source is compiled into them; no existing target/label/value changes; the runtime-target inventory is unchanged | T034-SR-010, T034-SR-011 |
| CHK-17 | `git diff --check` is clean and the changed-path set is exactly the declared T034 paths | T034-SR-011 |
| CHK-18 | every changed unit carries the X-COM file block (`@file`, `@brief`, `@ownership`, `@lifetime`, `@thread_safety`, `@failure`, `@par Traceability`) | T034-SR-012 |
| CHK-19 | the committed fixture, drivers, and bounded logs contain no payload byte, permit content, secret, private address, or host path | T034-SR-012 |
| CHK-20 | the full inherited suite (`ctest -L "t0(16|20|2[6-9]|3[0-4])-"`) and the Python suite still pass | T034-SR-014 |
| CHK-21 | the T007–T010 register validators pass; REF-002 stays `unchanged` with an empty `promoted` list | T034-SR-013 |
| CHK-22 | `xcom_phase7_gate.py verify T034 <baseline>` passes with a `t034-`-labelled discovered case; the T034 checkbox is marked complete only at implementation | T034-SR-013 |

## 5. Executable suites and negative cases

| Driver (`t034-<kind>`) | Cases | Negative cases |
| --- | --- | --- |
| replaceability | `ReusedProviderContractSuitePasses`, `ProviderIsIndependentOfLoopback`, `BoundedCapabilitiesAndSaturation`, `CompletesFullBoundedLifecycle` | NEG-02 |
| version | `MisreportedContractVersionRejectedAtRegistration`, `UnsupportedRequestedVersionRejectedBeforeActivation`, `MisreportedCapabilityRejectedAtRegistration`, `UnsupportedRequestedCapabilityRejectedBeforeActivation`, `RejectionEmitsNothing` | NEG-03 |
| isolation | `ProviderFailureYieldsStableOutcomeNoEmission`, `UnrelatedRouteRemainsActiveAndBounded`, `UnrelatedRouteStateStaysObservable`, `RejectedAdapterLeavesUnrelatedRouteIntact` | NEG-04 |

- **NEG-01** — a change to an accepted provider/composition/loopback byte or the runtime-target inventory:
  the changed-path inspection and CHK-16 fail closed.
- **NEG-02** — the T033 suite is copied or edited, or a competing conformance interface is introduced: CHK-05
  and CHK-06 fail closed.
- **NEG-03** — an unsupported version or capability reaches activation: CHK-07…CHK-10 fail.
- **NEG-04** — a provider/route failure perturbs an unrelated route: CHK-12 and CHK-13 fail.
- **NEG-05** — a TCP/`AF_INET`/DNS/TLS/legacy/external token, a payload, permit, secret, private address, or host
  path is committed: CHK-01 and CHK-19 fail.
- **NEG-06** — a runtime library is added, an existing target/label/value changes, or the checkbox is marked in
  the plan stage: CHK-16, CHK-17, and CHK-22 fail closed.
- **NEG-07** — a missing unit case (empty `unit_cases`) is declared: the trusted unit gate fails closed.
- **NEG-08** — a missing suite check is silently skipped: `SuiteReport::ok()` is false and the case fails.

## 6. Traceability to the accepted anchors

| T034 check | Accepted anchor |
| --- | --- |
| CHK-01 | `XCOM-SW-CORE-007`, FR-026/FR-028 |
| CHK-02/CHK-03/CHK-04/CHK-05/CHK-06 | `XCOM-SW-CORE-004/005/007/009`, `XCOM-DU-007/008`, `XCOM-CMP-006/007`, FR-007/FR-010/FR-028/FR-030 |
| CHK-07/CHK-08/CHK-09/CHK-10 | `XCOM-SW-CORE-003`, FR-006/FR-022 |
| CHK-11/CHK-12/CHK-13 | `XCOM-SW-CORE-005`, FR-010/FR-014 |
| CHK-14/CHK-15 | User Story 4 independent test; ADR-0020 |
| CHK-16/CHK-17 | T012 build contract; FR-030 |
| CHK-18/CHK-19/CHK-20 | FR-027/FR-029; ADR-0020 |
| CHK-21/CHK-22 | Constitution VII/IX/X; ADR-0020 |

## 7. Measurement plan and evidence binding

- The trusted `unit` measure builds the isolated target checkout and runs the thirteen `t034-` cases with the
  preserved `T016`/`T020`/`T026`–`T033` suites; the trusted `integration`/`validation` measures assemble the
  pinned target revision and run the full CTest and Python suites.
- Evidence is bound to the exact T034 candidate revision; commands, tool/environment identity, exit status,
  bounded logs, and hashes are retained in the repository-owned or referenced evidence bundle (T035).
- No stale, skipped, mismatched, or failed evidence supports acceptance; whole-system integration and static
  analysis run separately from the isolated checkout.

## 8. Definition of done (verification view)

T034 is verified for a candidate revision when all thirteen `t034-` cases pass under the admitted offline build,
the preserved `T016`/`T020`/`T026`–`T033` suites still pass, `git diff --check` is clean, the changed-path set is
exactly the declared T034 paths, the T007–T010 register validators pass with REF-002 `unchanged`, and
`xcom_phase7_gate.py verify T034 <baseline>` passes. User acceptance remains T041.
