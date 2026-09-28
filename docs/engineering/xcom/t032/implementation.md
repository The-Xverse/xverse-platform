# T032 Implementation Record — Separate-Process Synthetic Client and Generated-Client Contract Tests

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T032 (capability 007, slice `T-CORE`/GW) |
| Stage / role | implementation |
| Revision | 1 (separate-process synthetic-client conformance slice) |
| Baseline revision | `e6197c67868213ffb6523d8bf62ed4c2c4e3b0af` |
| Candidate | this repository working tree on the baseline, with the §3 change set only |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 1 |
| Model / reasoning profile | `deepseek-v4-flash`, pinned by the queue workflow |
| Classification | Public-safe engineering work product |

This record is a repository-owned work product (ADR-0020). It records what the implementation stage
actually changed and measured against the exact baseline. It does not accept or integrate the
candidate; external Codex review and explicit user acceptance are deferred until the ordered backlog
`xcom-t030-t034-20260928` completes.

## 2. Implemented boundary

T032 authors exactly one bounded, separate-process synthetic tool client
(`src/xverse/xcom/fixtures/synthetic_tool.cpp`, executable `xverse_xcom_synthetic_client`) realizing the
accepted T030 `xverse.xcom.v1.ToolGateway` generated message and method contract over the accepted T031
host-protected `AF_UNIX` local-IPC framing, and proves it with five additive `t032-<kind>` suites. It
authors **no** TCP listener or non-local address-family socket, no external network peer, no legacy
binary or production workload, no compiled or linked transport runtime, no new admitted dependency, no
reusable contract-suite abstraction (T033), and no second provider (T034). The client connects only to
a host-protected local endpoint, recognizes the ten accepted `ToolGateway` operations by their exact
committed names, declares explicit maximum-message-size, per-request-deadline, and transport-timeout
bounds, acquires/releases the accepted exclusive generation-bound lease, and reports only bounded,
payload-free, logical-identity/scalar result lines.

## 3. Changed-path inventory (candidate)

| Path | Change | SHA-256 |
| --- | --- | --- |
| `src/xverse/xcom/fixtures/synthetic_tool.cpp` | add | `4bad964d0968036171c37daea8a92956eaf871b4611b413c9ff8d24df2d6ca73` |
| `src/xverse/xcom/CMakeLists.txt` | edit (additive) | `f61405daf1c27068808f9cb45f2e75afe35d49fc53c90cb123cfec68c5f324ee` |
| `tests/xcom/tool_gateway/synthetic_client_support.hpp` | add | `79a6a76ff6035479ecced8b9713dd5e9954b2fb1f63abd5a20e9c7e1aad798d8` |
| `tests/xcom/tool_gateway/synthetic_client_observation_tests.cpp` | add | `731ebe75204bfb47ceb31e8e381110069dd9ab2bd89f8a14872a1a32c78d9f66` |
| `tests/xcom/tool_gateway/synthetic_client_stimulation_tests.cpp` | add | `845e39c26300638b852f9409b70a9783ab044cc688b3b126468d5841826425c5` |
| `tests/xcom/tool_gateway/synthetic_client_contract_tests.cpp` | add | `c3a52c3b0efc546445a372fdb85076fcd97a4891c95fef8b276aed14002fe976` |
| `tests/xcom/tool_gateway/synthetic_client_negative_tests.cpp` | add | `8d0769c8fc219a7dc754fac87638669edbfe8986a452da3ecdfdd1089655bd6b` |
| `tests/xcom/tool_gateway/synthetic_client_bounds_tests.cpp` | add | `45c6ace8790ec73727e7b8373f98e16d043b6e293933794be445d4bca6b61ee1` |
| `docs/engineering/xcom/t009/architecture-model.json` | edit | `XCOM-CMP-011` planned→established path status only |
| `docs/engineering/xcom/t010/unit-design.json` | edit | `XCOM-DU-021` planned→established path status only |
| `docs/engineering/xcom/t010/design-units.md` | edit | `XCOM-DU-021` planned→established path status only |

The remainder of the candidate change set is the T032 repository-owned work products
(`docs/engineering/xcom/t032/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`),
the T032 engineering requirement/component/unit/validation records, `engineering/trace/links.json`, the
refreshed `engineering/verification/measures/{unit,integration,validation}.json`, the refreshed
inherited `engineering/stage-results/*.json` digests, `engineering/project.json`, the T032 checkbox line
in `specs/007-xcom-core/tasks.md`, `reports/review-index.md`, and the generated
`reports/xcom-queue/t032-package.json` and `docs/engineering/xcom/t032/internal-review.json`. No
accepted predecessor byte under `src/`, `tests/`, `xdl/`, or `docs/engineering/xcom/t0{07..31}/` other
than the additive `src/xverse/xcom/CMakeLists.txt` wiring and the status-only path reconciliation was
changed.

## 4. Design realization notes

The implementation realizes the accepted plan. The following bounded, additive notes record how the
illustrative interface listing in `detailed-design.md` §3 was realized; the authoritative content is
the accepted message/method contract and the accepted T021–T031 boundaries:

1. **Single committed operation table.** `synthetic_client_operation_names()` returns one committed
   `std::array<std::string_view, 10U>`; the client self-test resolves the generated `ToolGateway`
   service descriptor from the generated pool and asserts equality in order, so the framing method
   vocabulary is bound 1:1 to the accepted contract. A mismatch exits non-zero and emits no operation
   line pair beyond the committed table.
2. **Bounded local-only channel.** `LocalClientChannel::connect` sets a bounded non-blocking connect
   with a `poll` wait and a `SO_ERROR` check, binds only `AF_UNIX`, and asserts `is_local_endpoint()`
   (`getsockname` family) before any exchange. It references no non-local address family, resolver, or
   transport-security facility and exposes no listening socket.
3. **Explicit bounds.** `SyntheticClientConfig` is validated by `make_client_config`; the maximum
   message size, per-request deadline, and transport timeout each have a floor and a ceiling and no
   implicit default. The `over_message` and `over_deadline` exercises build one genuinely over-bound
   request, assert the bound is exceeded, and reject before any peer contact.
4. **Framing reuse.** The client encodes the accepted T031 request-frame layout
   (`uint32 total_length` big-endian, `uint16 method_name_length`, method name, serialized request) and
   reads the accepted response-frame layout (`uint32 total_length` then payload) so it introduces no
   competing transport vocabulary. Observation reads consume bounded record frames until the zero-length
   terminator.
5. **Parent-owned session.** The separate-process client never holds a `GatewaySession`; the test-local
   harness (`synthetic_client_support.hpp`) owns the accepted `GatewaySession`, performs the declared
   supported-major negotiation, serves exactly one peer, and maps each decoded frame 1:1 onto the
   accepted T031 operation.
6. **Fail-closed outcomes.** A connect failure, an unexpected peer close, and an exhausted transport
   wait all report `failed`; an over-bound frame/deadline reports `rejected` locally; a rejection never
   reports `accepted` and emits no item. The client always exits `0` when the declared exercise ran and
   reported a bounded outcome, and non-zero only when it fails closed before the exercise.
7. **Bounded test-local provenance recorder.** `ProvenanceEmitter` (T032-local) records the accepted
   `SyntheticStimulationItem::origin`, so the stimulation cases assert the accepted persistent synthetic
   provenance (`OriginType validation_tool`) as well as the emitted outcome and count.

No accepted requirement, contract byte, accepted test, register row, ADR, or REF-002 disposition was
changed or weakened.

## 4.1 Required register path-status reconciliation

Creating `src/xverse/xcom/fixtures/synthetic_tool.cpp` makes the accepted T009/T010 planned path present
in the tree, so the T009 and T010 validators require the planned→established path-status transition
(status field only; the same minimal normalization T030/T031 applied to their owned paths):

- `XCOM-CMP-011`: `src/xverse/xcom/fixtures/synthetic_tool.cpp`;
- `XCOM-DU-021`: `src/xverse/xcom/fixtures/synthetic_tool.cpp`.

Only the `status` field changes (`planned`→`established`); no path, component/unit identity, maturity,
requirement link, or governing ADR changes. Unit `XCOM-DU-021` remains `allocated`.

## 5. Generated-code provenance (inherited T030 contract)

T032 adds **no** generated code. It consumes the T030-generated Protocol Buffers messages and service
descriptor and independently re-verified that the offline admitted build regenerates the exact T030
outputs from the committed schema:

| Provenance item | Value |
| --- | --- |
| Input schema identity | `proto/xverse/xcom/v1/tool_gateway.proto`, SHA-256 `cbb65f901b8522120da6333c4e569d4d8fa00db601abd7effaf70abe925dbb2d` |
| Protocol Buffers generator | admitted `libprotoc 3.12.4`; runtime header reports `GOOGLE_PROTOBUF_VERSION 3012004` |
| gRPC stub generator | admitted `grpc_cpp_plugin` 1.30.2 (provenance-only; not compiled or linked) |
| Output `tool_gateway.pb.h` | `80e886ea5f01b25274ee16ba0b395a354dec1145ff409fb3951b7af968edd8ad` |
| Output `tool_gateway.pb.cc` | `bcff542624d4638b3619e8c5d5601166e53493d259df90171cd348e1036009d8` |
| Output `tool_gateway.grpc.pb.h` (provenance-only) | `be80b0c71edf2a8d4a1f51fcbf9179352cd8b1643c2264ce933377a3a69e13c2` |
| Output `tool_gateway.grpc.pb.cc` (provenance-only) | `474b4f1c7b8fb05e66b47ac77e5b93af6589880d3da18f085d2edf552080bd4f` |

The digests equal the accepted T030 §5 record and the T031 §5 record byte-for-byte, proving T032
consumed the pinned generated contract unchanged. The generated outputs live under the git-ignored
build tree; the committed `.proto` remains the single source of truth. The client links only the
compiled message library through the accepted gateway target; the transport runtime is not linked
(`T032-GAP-01`).

## 6. Build wiring and runtime inventory

`src/xverse/xcom/CMakeLists.txt` is extended additively:

- one fixture executable `xverse_xcom_synthetic_client` built from
  `src/xverse/xcom/fixtures/synthetic_tool.cpp`, routed through `xverse_xcom_apply_runtime_rules`,
  linking only the accepted gateway target (which supplies the accepted in-process T021–T029
  libraries and the T030 generated-message library) and the standard library;
- **no** `XVERSE_XCOM_RUNTIME_TARGETS` change: the fixture executable is not a runtime library, so the
  declared runtime-target inventory and the `xcom_build_contract` expectation are unchanged;
- five additive test executables with one hyphenated label each: `t032-observation`,
  `t032-stimulation`, `t032-contract`, `t032-negative`, `t032-bounds`, each with a bounded build-tree
  working directory and the bounded `XCOM_T032_SYNTHETIC_CLIENT_PATH` /
  `XCOM_T032_CLIENT_SOURCE_PATH` / `XCOM_T032_SCRATCH_DIR` build-time definitions.

The admitted protobuf and generated headers are system includes, so third-party and generated-header
warnings are suppressed while the X-COM warning-as-error policy still governs every T032-owned source
line. No existing target, test name, label, command, or expected value changed, and no predecessor
discovery count was reduced.

## 7. Verification performed (candidate working tree)

Admitted offline inputs (environment, values recorded by name only): `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, `XVERSE_XCOM_T025_TEST_TOOLCHAIN`.

```sh
python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase7_tests.py unit
ctest --test-dir build/fabro-t030-t034-system-unit -N -L t032-
ctest --test-dir build/fabro-t030-t034-system-unit -L t032- --output-on-failure
ctest --test-dir build/fabro-t030-t034-system-unit -L "t0(20|2[6-9]|3[0-4])-" --output-on-failure
ctest --test-dir build/fabro-t030-t034-system-unit -R xcom_build_contract --output-on-failure
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
python3 ${XVERSE_FABRIC_ROOT}/automation/xcom_phase7_gate.py verify T032 e6197c67868213ffb6523d8bf62ed4c2c4e3b0af
```

| Command | Observed result |
| --- | --- |
| `run_xcom_phase7_tests.py unit` | configure/build succeeded; inherited-label CTest `100% tests passed` |
| `ctest -N -L t032-` | `Total Tests: 22` (5 observation, 5 stimulation, 4 contract, 5 negative, 3 bounds) |
| `ctest -L t032-` | `100% tests passed, 0 tests failed out of 22` |
| `ctest -L "t0(20|2[6-9]|3[0-4])-"` | `100% tests passed, 0 tests failed out of 221` |
| `ctest -N` (full discovery) | `Total Tests: 475` (T031 recorded 453; +22 additive T032 cases) |
| `ctest -R xcom_build_contract` | `100% tests passed, 0 tests failed out of 1` |
| register validators | ownership, requirements traceability, architecture contracts, and unit design all pass |
| `git diff --check <baseline> --` | clean |

The T032 suites are offline and deterministic; they use only the C++ standard library, GTest, the
accepted in-process T021–T029 libraries, and the T030 generated messages. The only file read is the
bounded read of the committed T032 client source in `T32-TS-019`, and the only sockets are the bounded
`AF_UNIX` bind/connect exchanges under the git-ignored build tree. No case opens a network peer, a
non-local address family, a resolver, a transport-security session, a dynamic library, or a legacy
repository; the only child process is the owned `xverse_xcom_synthetic_client` fixture, launched with
an explicit bounded argument vector and an empty (scrubbed) environment and reaped within a bounded
wait.

## 8. Requirement-to-case result

| Requirement | Cases | Result |
| --- | --- | --- |
| T032-SR-001 | `T32-TS-014` | pass |
| T032-SR-002 | `T32-TS-014` | pass |
| T032-SR-003 | `T32-TS-001`, `T32-TS-019` | pass |
| T032-SR-004 | `T32-TS-015`, `T32-TS-019` | pass |
| T032-SR-005 | `T32-TS-002`, `T32-TS-003`, `T32-TS-004` | pass |
| T032-SR-006 | `T32-TS-005` | pass |
| T032-SR-007 | `T32-TS-006`, `T32-TS-007`, `T32-TS-008`, `T32-TS-009` | pass |
| T032-SR-008 | `T32-TS-010` | pass |
| T032-SR-009 | `T32-TS-016`, `T32-TS-017` | pass |
| T032-SR-010 | `T32-TS-018` | pass |
| T032-SR-011 | `T32-TS-020`, `T32-TS-021`, `T32-TS-022` | pass |
| T032-SR-012 | `T32-TS-017`, `T32-TS-022` | pass |
| T032-SR-013 | `T32-TS-011` | pass |
| T032-SR-014 | `T32-TS-001` | pass |
| T032-SR-015 | `T32-TS-012`, `T32-TS-013` | pass |
| T032-SR-016 | build/discovery inspection (CHK-19); contributory `XcomSyntheticClientContract.ClientOperationTableMatchesGeneratedDescriptor` | pass |
| T032-SR-017 | `T32-TS-014`, `T32-TS-019` | pass |
| T032-SR-018 | register validators (CHK-21); contributory `XcomSyntheticClientContract.ClientOperationTableMatchesGeneratedDescriptor` | pass |
| T032-SR-019 | Phase 7 gate (CHK-22); contributory `XcomSyntheticClientBounds.DeadlineBoundEnforced` | pass |
| T032-SR-020 | changed-path inspection (CHK-02, CHK-19); contributory `XcomSyntheticClientContract.ClientOperationTableMatchesGeneratedDescriptor` | pass |
| T032-SR-021 | file-block inspection (CHK-03) | pass |

Negative cases: NEG-01 (non-local family / forbidden API / external peer) by `T32-TS-019` and the
`AF_UNIX`-only endpoints in `T32-TS-015`; NEG-02 (competing interface / rejected method / claimed
runtime link) by `T32-TS-014` and the operation-table self-test; NEG-03 (permit bypass) by
`T32-TS-016`; NEG-04 (unknown/expired outcome as success) by `T32-TS-017`/`T32-TS-022`; NEG-05
(implicit version acceptance) by `T32-TS-018`; NEG-06 (omitted bound / ambient clock) by
`T32-TS-020`/`T32-TS-021`; NEG-07 (new dependency or linked runtime) by the offline build and
`T32-TS-019`; NEG-08 (payload/permit logged) by `T32-TS-011`; NEG-09/NEG-10 (register/scope/additivity)
by CHK-21/CHK-22.

## 9. Inherited provenance refresh

`src/xverse/xcom/CMakeLists.txt` changed, so the inherited `implemented_by` content digests for every
link that targets it are refreshed to the new SHA-256 in `engineering/trace/links.json`; link identity,
relation, source, and target are unchanged. The declared `engineering/trace/links.json` and
`src/xverse/xcom/CMakeLists.txt` artifact digests in the inherited `engineering/stage-results/*.json`
are refreshed in the same change. No requirement, link identity, relation, stage result, register row,
or REF-002 disposition changes. The T032 `engineering/verification/measures/{unit,integration,validation}.json`
descriptors are refreshed to the 22 discovered T032 cases and the three admitted measure commands,
following the T020→T027–T031 precedent. `engineering/trace/links.json` carries the new T032
requirement/component/unit/validation links, and every accepted T032 software requirement carries
`allocated_to`, `implemented_by`, `verified_by` (unit, integration, validation), and its component/unit
decomposition and static-analysis edges.

## 10. Maintenance notes

- The committed client operation table is pinned to the accepted T030 descriptor method set by
  `T32-TS-014`; an accepted service change must update the table and the pinning case in the same
  change.
- The client bounds are explicit `SyntheticClientConfig` values validated by `make_client_config`;
  adding a bound requires a validator and a discovered case.
- The `AF_UNIX` endpoint path must stay under the build-tree scratch directory and short enough for
  `sockaddr_un` (at most 108 bytes); `XCOM_T032_SCRATCH_DIR` uses the short build root for this reason.
- The accepted gateway session must be negotiated before serving; the harness performs the declared
  supported-major negotiation and the client's own declared major is evaluated fail-closed on the
  first operation.
- The transport runtime remains deferred (`T032-GAP-01`); a future link must not weaken the
  local-IPC-only boundary or add an admitted dependency without an ADR and a new task.
- The client and its tests record only code/phase/logical-identity/size/timing/outcome; never add a
  payload, permit, secret, private-address, or host-path field to a result line or log record.

## 11. Limitations

- **T032-GAP-01 — transport runtime deferred.** The admitted envelope cannot link the transport
  runtime (`T030-GAP-02`, `T031-GAP-01`); the accepted message/method contract is realized over
  bounded local-IPC framing bound 1:1 to the T030 method names. No new dependency is added and no
  runtime link is claimed.
- **T032-GAP-02 — owned separate-process proof only.** T032 proves conformance with an owned,
  self-built separate-process client over an owned local endpoint. It makes no remote-tool,
  distributed-authorization, or third-party-client compatibility claim.
- **T032-GAP-03 — no reusable abstraction.** The T032 suites are T032-local and are not the T033
  reusable contract suite; the client is one implementation and not the T034 replaceability proof.
- **T032-GAP-04 — generated-code documentation.** The generated Protocol Buffers documentation policy
  remains `DOX-GAP-02`; T032 documents only its hand-written client seam.
- **T032-GAP-05 — no deployed-service or compatibility claim.** The client is a bounded prototype
  validated with owned local fixtures; it makes no production-readiness or parity claim.
- **L-T032-1 — admitted offline inputs.** The Phase 7 runner requires `XVERSE_XCOM_TOOLCHAIN`,
  `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` (or the documented A-1 cache
  seed); without them configure fails closed before any T032 target builds.
- **L-T032-2 — strict target-repository integration is separate.** The whole-system integration measure
  assembles the candidate into the pinned target checkout and runs separately from this stage; this
  record does not claim its result.
- **L-T032-3 — external review deferred.** External Codex review and user acceptance remain T039/T041
  and are deferred until backlog `xcom-t030-t034-20260928` completes.

## 12. Maturity

`XCOM-SW-GW-003` "Separate-process synthetic client conformance" is recorded **implemented** for the
conformance-client slice by T032. T033, T034, and T035–T041 remain allocated. The capability REF-002
disposition stays `unchanged` with an empty `promoted` list; `XVE-SYS-0141` remains deferred and
unpromoted.

## 13. Trace-repair closure (successor)

### 13.1 Finding

The reviewed predecessor candidate (`9c5f6d2837562a2bbcb1bbcd375ee1385c198970`) passed scope, checkpoint, unit,
static-analysis, target-repository integration, validation, and inherited conformance, and its separate DeepSeek
review recorded `verdict: pass`. Strict delivery then reported the traceability report
`traceability-matrix.json` with exactly five incomplete rows: `T032-STK-001`…`T032-STK-005` each listed `missing:
["refining software requirement", "validation scenario"]`. The accepted T032 software requirements already existed,
were executed, and passed; only the explicit `refines` links from each software requirement to its stakeholder
requirement were absent, so the matrix could not attach a refining requirement or a validating scenario to a
stakeholder row.

### 13.2 Correction

The successor adds the 24 missing `refines` links to `engineering/trace/links.json` (IDs `T032-L-0258`…`T032-L-0281`)
with no change to any requirement, component, unit, validation scenario, test, measure, or accepted predecessor byte.
The mapping and its statement-level justification are recorded in `requirements.md` §5.1. Each added link relates a
T032 software requirement to the stakeholder requirement whose statement it actually refines:

| Stakeholder | Added `refines` links |
| --- | --- |
| `T032-STK-001` | `T032-L-0258`, `-0260`, `-0262`, `-0264`, `-0265`, `-0266`, `-0268`, `-0270`, `-0271`, `-0272`, `-0273`, `-0274`, `-0277`, `-0281` |
| `T032-STK-002` | `T032-L-0261`, `-0263` |
| `T032-STK-003` | `T032-L-0267`, `-0269` |
| `T032-STK-004` | `T032-L-0259`, `-0275` |
| `T032-STK-005` | `T032-L-0276`, `-0278`, `-0279`, `-0280` |

No gate, checker, or measure is weakened: `fabro_engineering.core.validate_trace` passes with the corrected link
graph; every accepted T032 software requirement still carries `allocated_to`, `implemented_by`, and `verified_by`
(unit, integration, validation); and every added endpoint revision matches its requirement record (`revision` `1`).
The validating scenario is the already-executed `T032-VS-ACCUMULATED`, whose 22 test IDs are exactly those selected
and run by the trusted `engineering/verification/measures/validation.json` measure and re-checked by the
target-repository integration measure; the successor adds no test because the existing cases already assert the
stakeholder behaviours (separate-process `fork`/`execve` launch with an empty scrubbed environment; `AF_UNIX`-only
no-TCP endpoint with `0600` socket permissions and a forbidden-API scan; invalid and substituted-permit zero
emission; expired-session zero emission; generated operation-table equality; and generated round-trip and
unknown-field preservation).

### 13.3 Recomputed identity and evidence

- `engineering/trace/links.json` — 1928 links (24 added stakeholder-refinement links plus the refreshed
  `implemented_by` endpoint digests for `requirements.md` and `implementation.md`). The exact current digest is
  recorded by the trusted traceability report and `reports/review-index.md`; it is deliberately not written here,
  because `T032-L-0230`/`T032-L-0231` pin this file's own SHA-256 as their `target_revision`.
- `fabro_engineering.core.validate_trace(root, "xverse-platform")` → `{"artifacts": 551, "links": 1928}` (pass).
- The four `implemented_by` links that target the two edited work products (`T032-L-0220`, `T032-L-0221` →
  `requirements.md`; `T032-L-0230`, `T032-L-0231` → `implementation.md`) carry the refreshed file SHA-256 in
  `target_revision`, so the live endpoint hashes match the files after the §5.1/§13 edits; no requirement source
  revision changes (`source_revision` stays `1`).
- `write_traceability_matrix` dry-run over the current inventory → 214 rows, zero gaps (the five `T032-STK-###` rows
  now report `status: complete` with their refining software requirements and `T032-VS-ACCUMULATED`).
- The inherited `engineering/stage-results/{documentation,integration,internal-review}.json` artifact digests for the
  changed shared `engineering/trace/links.json` (and `reports/review-index.md`) are refreshed to the successor values;
  the `phase7-t032-*` stage results are regenerated from the successor artifacts by the candidate-sealing gate and are
  not hand-edited.

The original reviewed candidate and its review remain preserved as historical evidence (checkpoint commit
`9c5f6d2837562a2bbcb1bbcd375ee1385c198970`). A fresh independent DeepSeek review and every trusted measure — including
the target-repository integration and inherited Phase 6 conformance — cover this successor; external Codex review and
explicit user acceptance remain separate, and no acceptance, compatibility, or production-readiness claim is made.
