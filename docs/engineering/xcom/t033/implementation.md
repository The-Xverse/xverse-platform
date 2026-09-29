# T033 Implementation Record — Reusable Provider, Observer, Stimulation-Tool, and Gateway Contract Suites

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T033 (capability 007, slice `T-CORE`/GW) |
| Stage / role | implementation |
| Revision | 1 |
| Accepted baseline revision | `2fd395e39e44e1f6fe9547998b47499d996b1756` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 1 |
| Classification | Public-safe engineering work product |

This record describes what the T033 candidate implements. It does not accept or integrate the candidate; user
acceptance remains T041 and is deferred until the ordered backlog `xcom-t030-t034-20260928` completes.

## 2. Implemented boundary

T033 implements four **reusable, implementation-agnostic contract suites** and four additive `t033-<kind>`
drivers:

- `ProviderContractSuite` over a `ProviderSubject` seam — descriptor identity/compatibility, explicit
  registration, duplicate rejection, fail-closed unsupported-version rejection, prepare/activate/submit/
  receive/drain/close, bounded reject-new saturation, and bounded reconcile reporting.
- `ObserverContractSuite` over an `ObserverSubject` seam — metadata-only attachment, normalized metadata-only
  records with identity preservation, bounded drop-newest counters, exact-handle drain, detach, and normal-route
  isolation.
- `StimulationToolContractSuite` over a `StimulationToolSubject` seam — exact-permit/policy open, four allowed
  actions emitting exactly once with persistent synthetic provenance and journal-before-emission ordering, and
  zero emission for out-of-window and non-active requests.
- `GatewayContractSuite` over a `GatewaySubject` factory seam — version negotiation and the ten-operation surface,
  exact-permit arming, unarmed zero emission, four action emissions, the exclusive lease round trip, bounded
  metadata-only observation, bounded framing, and bounded counters.

It adds no production runtime source, no second provider, no admitted dependency, and no gRPC-runtime link.

## 3. Changed-path inventory (candidate)

Documentation and work products (`docs/engineering/xcom/t033/`):

- `requirements.md`, `architecture.md`, `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`,
  and this `implementation.md`.

Implementation and shared wiring:

- `tests/xcom/contract_suites/suite_support.hpp` (new)
- `tests/xcom/contract_suites/provider_contract_suite.hpp` (new)
- `tests/xcom/contract_suites/observer_contract_suite.hpp` (new)
- `tests/xcom/contract_suites/stimulation_tool_contract_suite.hpp` (new)
- `tests/xcom/contract_suites/gateway_contract_suite.hpp` (new)
- `tests/xcom/contract_suites/provider_suite_tests.cpp` (new)
- `tests/xcom/contract_suites/observer_suite_tests.cpp` (new)
- `tests/xcom/contract_suites/stimulation_tool_suite_tests.cpp` (new)
- `tests/xcom/contract_suites/gateway_suite_tests.cpp` (new)
- `src/xverse/xcom/CMakeLists.txt` (shared; only the additive T033 `foreach` block adding the four
  `t033-<kind>` targets)
- `specs/007-xcom-core/tasks.md` (shared; T033 checkbox line only)

Engineering records:

- `engineering/project.json` — current task T033 and accepted baseline
  `2fd395e39e44e1f6fe9547998b47499d996b1756`.
- `engineering/requirements/T033-STK-00{1..5}.json`, `engineering/requirements/T033-SR-0{01..16}.json`.
- `engineering/architecture/components/T033-SR-0{01..16}-CMP.json`.
- `engineering/unit-specifications/T033-SR-0{01..16}-U.json`.
- `engineering/validation/scenarios/T033-VS-ACCUMULATED.json`.
- `engineering/trace/links.json` — 198 additive T033 links and the inherited `src/xverse/xcom/CMakeLists.txt`
  `implemented_by` digest refresh.
- `engineering/verification/measures/{unit,integration,validation}.json` — refreshed to the eight discovered
  T033 cases.
- `engineering/stage-results/*.json` — inherited `src/xverse/xcom/CMakeLists.txt`,
  `engineering/trace/links.json`, and measure digest refresh only.
- `reports/review-index.md` — T033 candidate section appended.

## 4. Design realization notes

- `T33-DD-01`/`-02` — each suite names only an accepted interface (or accepted fixture helper) plus its subject
  seam. The provider suite is instantiated over the accepted `LoopbackProvider` and the accepted T016 probe
  provider; the observer, stimulation-tool, and gateway suites are instantiated over two independent subjects
  each. No suite header changes between instantiations.
- `T33-DD-03` — the provider suite uses `test::CoreStackFixture` with `activate_now=false`, a reject-new queue
  capacity of one item, and a one-byte payload bound, so saturation is observable deterministically.
- `T33-DD-04` — the observer suite publishes two items before polling so the capacity-one tap overflows, then
  polls, detaches, and re-submits to prove counters, metadata-only records, detach, and isolation.
- `T33-DD-05` — the stimulation-tool suite drives the accepted T029 `MatrixFixture` over the accepted
  journal/guard/action-path/lease composition.
- `T33-DD-06` — the gateway suite constructs a fresh accepted fixture per arming group because the accepted
  permit is single-session.
- `T33-DD-07` — every obligation is recorded as one bounded `SuiteCheck`; `SuiteReport::ok()` is false unless at
  least one check exists and every check passed, so a missing check is a failure.

No accepted production source, header, contract, schema, or register was changed.

## 5. Generated-code provenance (inherited T030 contract)

T033 adds no generated code and no admitted dependency. It consumes the T030-generated Protocol Buffers
messages through the accepted T031 gateway fixture; the committed input is
`proto/xverse/xcom/v1/tool_gateway.proto` (unchanged) generated offline by the T011-admitted `libprotoc 3.12.4`.
The generated outputs were re-hashed in this stage and equal the accepted T030/T031/T032 records byte-for-byte:

| Provenance item | Value |
| --- | --- |
| Input schema identity | `proto/xverse/xcom/v1/tool_gateway.proto`, SHA-256 `cbb65f901b8522120da6333c4e569d4d8fa00db601abd7effaf70abe925dbb2d` |
| Protocol Buffers generator | admitted `libprotoc 3.12.4`; runtime header reports `GOOGLE_PROTOBUF_VERSION 3012004` |
| gRPC stub generator | admitted `grpc_cpp_plugin` 1.30.2 (provenance-only; not compiled or linked) |
| Output `tool_gateway.pb.h` | `80e886ea5f01b25274ee16ba0b395a354dec1145ff409fb3951b7af968edd8ad` |
| Output `tool_gateway.pb.cc` | `bcff542624d4638b3619e8c5d5601166e53493d259df90171cd348e1036009d8` |
| Output `tool_gateway.grpc.pb.h` (provenance-only) | `be80b0c71edf2a8d4a1f51fcbf9179352cd8b1643c2264ce933377a3a69e13c2` |
| Output `tool_gateway.grpc.pb.cc` (provenance-only) | `474b4f1c7b8fb05e66b47ac77e5b93af6589880d3da18f085d2edf552080bd4f` |

The generated outputs live under the git-ignored build tree; the committed `.proto` remains the single source of
truth. T033 preserves the accepted `XCOM-XLC-002` additive evolution rules; `G-02` binds the committed operation
table to the ten accepted methods and `G-04` proves unsupported-major rejection.

## 6. Build wiring and runtime inventory

Four additive `t033-<kind>` test targets (`provider`, `observer`, `stimulation-tool`, `gateway`) are registered in
`src/xverse/xcom/CMakeLists.txt` under the warning-as-error policy. No existing target, test name, label,
command, or expected value changes and no existing discovery count is reduced. `XVERSE_XCOM_RUNTIME_TARGETS` is
unchanged (the suites are test executables, not runtime libraries). The committed suite headers are reached
through the `${PROJECT_SOURCE_DIR}/tests/xcom` include root; the bounded build-tree scratch definition
`XCOM_T031_SCRATCH_DIR` is supplied for the accepted T031 fixture header and is never printed into public
evidence.

## 7. Verification performed (candidate working tree)

Offline admitted build; commands and outcomes retained in the T033 evidence bundle (T035):

- `python3 automation/run_xcom_phase7_tests.py unit` (isolated checkout) — `100% tests passed, 0 tests failed
  out of 229`; the inherited `T020`/`T026`–`T033` suites plus the eight `t033-` cases.
- `ctest --test-dir build/fabro-t030-t034-system-unit -L t033-` — `100% tests passed, 0 tests failed out of 8`
  (2 provider, 2 observer, 2 stimulation-tool, 2 gateway).
- `ctest -N -L t033-` — `Total Tests: 8`.
- `python3 -m pytest -q` — `150 passed, 24 subtests passed`.
- `python3 scripts/validate_xcom_task_ownership.py --verify` — passed.
- `python3 scripts/validate_xcom_requirements_traceability.py --verify` — passed.
- `python3 scripts/validate_xcom_architecture_contracts.py --verify` — passed.
- `python3 scripts/validate_xcom_unit_design.py --verify` — passed.
- `git diff --check <baseline> --` — clean.

### 7.1 Candidate artifact content hashes (SHA-256)

The nine T033-owned contract-suite artifacts and the shared additive build file were re-hashed in this stage:

| Artifact | SHA-256 |
| --- | --- |
| `tests/xcom/contract_suites/suite_support.hpp` | `a5877eb0066d687f0e157917467da60be7642d86a02c1a647c4cfe3a0e474854` |
| `tests/xcom/contract_suites/provider_contract_suite.hpp` | `97967b89fbab5d8acfd5ae5ca774df361c14b9286cb56cf872df34cdf669cc8b` |
| `tests/xcom/contract_suites/provider_suite_tests.cpp` | `b8e3c58215ae7dd00738e09ba3f577e32f81cd976c5bf1969e27f98aab307098` |
| `tests/xcom/contract_suites/observer_contract_suite.hpp` | `e188db25609942f0775952a6dd128f233333669643f3fe4679baa6cf366c7563` |
| `tests/xcom/contract_suites/observer_suite_tests.cpp` | `fb51cd9b97d4a613c9b0ce39c8c595848bb17dbc3389d252defb8b7fab813e6a` |
| `tests/xcom/contract_suites/stimulation_tool_contract_suite.hpp` | `8b0a0caf688ca626d63e5a8eb1effa6db317f26d797e64786823cbf77ed219c3` |
| `tests/xcom/contract_suites/stimulation_tool_suite_tests.cpp` | `b4493a9bd88efd888d052b6ed5d8c0648e40b6b20475c7bfda527075e024e693` |
| `tests/xcom/contract_suites/gateway_contract_suite.hpp` | `42baaec9b921ba39b312902d4c71130cdbe0e519173f551a5112960f1a0812f1` |
| `tests/xcom/contract_suites/gateway_suite_tests.cpp` | `7c17f9fa8e84eb11663e7d715c6a22219105db315a7e4de345bed618b5827ce3` |
| `src/xverse/xcom/CMakeLists.txt` (additive T033 block) | `79f8d8a4e0c3838e9e36f2ef4e2b7b05d45945b3698939943155250b38b083d4` |

The complete candidate hash manifest, including the work products and engineering records, is emitted at
package time in `reports/xcom-queue/t033-package.json` and is the authoritative inventory for the candidate.

## 8. Requirement-to-case result

| Requirement | Suite checks | Executed cases |
| --- | --- | --- |
| T033-SR-001 | `P-01`…`P-03` | `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |
| T033-SR-002 | `P-04` | `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |
| T033-SR-003 | `P-05`…`P-13` | `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |
| T033-SR-004 | `O-01`…`O-04`, `O-07` | `T033ObserverContractSuite.AcceptedObservationHubConforms` |
| T033-SR-005 | `O-05`, `O-06`, `O-08` | `T033ObserverContractSuite.SuiteIsReusableAcrossHubInstances` |
| T033-SR-006 | `O-09`…`O-11` | `T033ObserverContractSuite.AcceptedObservationHubConforms` |
| T033-SR-007 | `S-01`, `S-02-0`…`S-02-3`, `S-05` | `T033StimulationToolContractSuite.AcceptedStimulationPathConforms` |
| T033-SR-008 | `S-03`, `S-04` | `T033StimulationToolContractSuite.SuiteIsReusableAcrossFixtures` |
| T033-SR-009 | `G-02`…`G-04` | `T033GatewayContractSuite.AcceptedGatewaySessionConforms` |
| T033-SR-010 | `G-05`, `G-08` | `T033GatewayContractSuite.AcceptedGatewaySessionConforms` |
| T033-SR-011 | `G-09` | `T033GatewayContractSuite.AcceptedGatewaySessionConforms` |
| T033-SR-012 | `G-01`, `G-06`, `G-07` | `T033GatewayContractSuite.SuiteIsReusableAcrossFixtures` |
| T033-SR-013 | `G-10`, `G-11` | `T033GatewayContractSuite.SuiteIsReusableAcrossFixtures` |
| T033-SR-014 | the four `SuiteIsReusable…` cases | all four reuse cases |
| T033-SR-015 | build/discovery inspection | CHK-16, CHK-19, CHK-20 |
| T033-SR-016 | register validators, gate, file-block inspection | CHK-03, CHK-21, CHK-22 |

## 9. Inherited provenance refresh

Editing `src/xverse/xcom/CMakeLists.txt`, `engineering/trace/links.json`, and the three
`engineering/verification/measures/*.json` records invalidated inherited artifact digests. Following the
T020/T026–T032 precedent, this stage refreshed only the affected `sha256`/`target_revision` values in
`engineering/stage-results/*.json` and the inherited `implemented_by` digests for
`src/xverse/xcom/CMakeLists.txt` in `engineering/trace/links.json`. No requirement, link identity, relation,
measure, or stage result changed.

## 10. Maintenance notes

- Add a new conforming implementation by implementing one `*Subject` adapter in a driver; do not edit the suite
  headers.
- The reuse demonstration currently covers two providers and two instances per remaining suite; T034 adds the
  production second provider.
- Generated Protocol Buffers documentation remains `DOX-GAP-02` (T037).

## 11. Limitations

- **T033-GAP-01** — reuse is proven for provider implementations and for suite instances; no third-party
  implementation or compatibility claim is made.
- **T033-GAP-02** — the gRPC transport runtime remains deferred (`T032-GAP-01`); the gateway suite validates the
  accepted local-IPC framing, not a gRPC server.
- **T033-GAP-03** — generated-code documentation remains `DOX-GAP-02`.
- **T033-GAP-04** — no deployed-service or production-readiness claim.

## 12. Maturity

The reusable contract suites are implemented for the T033 slice. `XCOM-SW-CORE-007`, `XCOM-SW-CORE-009`, and
`XCOM-SW-GW-002` remain unchanged accepted text; the per-task projection records the suite contribution. T034
(second provider) through T041 (acceptance) remain allocated, and the REF-002 disposition stays `unchanged` with
an empty `promoted` list.

## 13. Repair-pass closure (REV-T033-001, REV-T033-002)

### 13.1 Findings

The separate read-only DeepSeek internal review of the predecessor working-tree candidate recorded
`verdict: fail` with two annotation-only findings and no executed-behaviour finding:

- **REV-T033-001 (medium)** — the `@par Traceability` requirement range in all four reusable suite headers and all
  four drivers was shifted by one relative to the authoritative `engineering/requirements/T033-SR-*.json` records
  and the `implemented_by` links, so each file claimed a requirement it does not implement and omitted one it does.
- **REV-T033-002 (low)** — the observer and stimulation-tool headers plus `requirements.md` §4.3 cited bare SESN-era
  observation anchors and undefined stimulation anchors that do not exist in the accepted
  `docs/engineering/xcom/t008/requirements-register.json`.

Neither finding implicated a requirement statement, a check, a measure, or an executed test.

### 13.2 Correction

Each `@par Traceability` line was corrected to the authoritative mapping and each anchor replaced with its accepted
register id:

| Corrected file(s) | `@par Traceability` range | Accepted anchors |
| --- | --- | --- |
| `provider_contract_suite.hpp`, `provider_suite_tests.cpp` | `T033-SR-001`…`T033-SR-003` | `XCOM-DU-007`, `XCOM-DU-021` |
| `observer_contract_suite.hpp`, `observer_suite_tests.cpp` | `T033-SR-004`…`T033-SR-006` | `XCOM-SW-OBS-001`, `XCOM-SW-OBS-004` |
| `stimulation_tool_contract_suite.hpp`, `stimulation_tool_suite_tests.cpp` | `T033-SR-007`, `T033-SR-008` | `XCOM-SW-STIM-001/004/007/008` |
| `gateway_contract_suite.hpp`, `gateway_suite_tests.cpp` | `T033-SR-009`…`T033-SR-013` | `XCOM-SW-GW-002` |
| `suite_support.hpp` | `T033-SR-014` | `XCOM-DU-021` |
| `requirements.md` §4.3 (`T033-SR-008`) | — | `XCOM-SW-STIM-002`, `XCOM-SW-STIM-004` |

To keep the trace graph truthful for the corrected driver ranges, nine `implemented_by` links were added to
`engineering/trace/links.json` (`T033-L-0199`…`T033-L-0207`): `T033-SR-002`/`-003` → `provider_suite_tests.cpp`;
`T033-SR-005`/`-006` → `observer_suite_tests.cpp`; `T033-SR-008` → `stimulation_tool_suite_tests.cpp`;
`T033-SR-010`…`-013` → `gateway_suite_tests.cpp`. The corrected header ranges were already covered by their existing
links. The reviewer's closure test — each `tests/xcom/contract_suites/*.{hpp,cpp}` file's cited `T033-SR` set is a
subset of the ids whose `implemented_by` links target that file — now holds for all nine files.

The unused `XCOM_T033_SUITE_HEADER_ROOT` compile definition recorded as an observation was removed from the additive
T033 `foreach` block in `src/xverse/xcom/CMakeLists.txt`; no target, label, command, value, or
`XVERSE_XCOM_RUNTIME_TARGETS` entry changed.

### 13.3 Recomputed identity and evidence

- `engineering/trace/links.json` carries the refreshed `target_revision` digests for all nine edited
  `tests/xcom/contract_suites/*` files, `docs/engineering/xcom/t033/requirements.md`, and
  `docs/engineering/xcom/t033/implementation.md`, plus the nine new links; the exact link count and trace-validation
  result are recorded by the trusted successor report and `reports/review-index.md` rather than here, because the
  `implemented_by` links that target these T033 work products pin their own SHA-256 (`T033-L-0189` pins this file).
- The four `t033-<kind>` targets still build and `ctest -L t033-` still reports 8/8 passing; the annotation-only edits
  change no compiled behavior.
- The deterministic gate `xcom_phase7_gate.py verify T033 2fd395e39e44e1f6fe9547998b47499d996b1756` passes with a
  `t033-`-labelled discovered case, and `git diff --check` is clean.

The predecessor review remains preserved as historical evidence; the successor requires a fresh independent DeepSeek
review and repeated affected verification under ADR-0020. External Codex review and explicit user acceptance remain
separate (T039/T041), and no acceptance, compatibility, or production-readiness claim is made.

## 14. Repair-pass closure 2 (REV-T033-003, REV-T033-004, REV-T033-005, REV-T033-006)

The separate read-only DeepSeek internal review of the REV-T033-001/-002 successor recorded `verdict: fail` with
four documentation-consistency findings and no executed-behaviour finding. Each is closed on this successor without
weakening a requirement, check, measure, test, or traceability link.

- **REV-T033-003 (low)** — the accepted-implementation context cell in `architecture.md` §3.1 rendered the word
  "loopback" as the truncated token "lo" (padded with spaces to the cell width). The cell now reads the full
  `T016 core_matrix test_support (loopback provider + ProbeProvider)`; the replacement preserves the diagram column
  width (the two-character token plus seven spaces becomes "loopback" plus one space), and a re-scan of the diagram
  finds no other truncated or padded-token cell.
- **REV-T033-004 (low)** — `reports/review-index.md` recorded `full discovery 476`. The admitted offline
  configuration reproducibly reports `Total Tests: 483` (`ctest --test-dir build/fabro-t030-t034-system-unit -N`),
  with 8 `t033-` cases and 229 inherited-label cases; the index now records `483`. No other count changed, and the
  historical T032 section retains its own measured `475`.
- **REV-T033-005 (low)** — the `requirements.md` §4.3 `T033-SR-007` verification intent listed `S-01`…`S-03`,
  `S-05`, assigning the out-of-window check `S-03` (owned by `T033-SR-008`) to `T033-SR-007`. The intent now reads
  `S-01`, `S-02-0`…`S-02-3`, `S-05`, so the `T033-SR-007`/`T033-SR-008` check sets are disjoint and equal the
  `verification-plan.md` §4 named checks `CHK-09`/`CHK-10`, the §5 case/negative-case split, and this record §8.
- **REV-T033-006 (low)** — `unit-specifications.md` `T033-SR-009-U` named "the generated descriptor method set" as an
  input, but `G-02` only asserts `gateway_operation_names().size() == 10U` and never consumes that set. The input is
  corrected to the values the suite actually consumes: the committed gateway operation-name table exposed by
  `gateway_operation_names()` (consumed by `G-02`) and the generated `ProtocolVersion`, `QueryVersionRequest`, and
  `QueryVersionResponse` messages (consumed by `G-03`/`G-04`). `G-02` is unchanged, so no accepted check is altered.

All four corrections are documentation-only. No requirement id, statement, acceptance criterion, component, unit
case, validation scenario, check id, expected value, test body, target, or label changed. The `t033-<kind>` suites
still build and `ctest -L t033-` still reports 8/8. The `implemented_by` digests that pin `requirements.md`,
`unit-specifications.md`, and this record (`T033-L-0189`…`T033-L-0192`) and the inherited `engineering/trace/links.json`
and `reports/review-index.md` artifact digests in the T020 stage results are refreshed to the new bytes. A fresh
independent DeepSeek review and the repeated affected verification remain required; T039/T041 acceptance is separate.

