# T031 Implementation Record — Bounded Local-IPC-Only Tool Gateway

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T031 (capability 007, slice `T-CORE`/GW) |
| Stage / role | implementation |
| Revision | 1 (local-IPC gateway session slice) |
| Baseline revision | `4dded2317f895978cce0331ae88e34ac28b3a609` |
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

T031 authors exactly one bounded, host-protected, local-IPC-only gateway session realizing the accepted
`XCOM-XLC-002` message and method contract, and proves it with six additive `t031-<kind>` suites. It
authors **no** TCP listener or non-local address-family socket, no separate process or synthetic client
(T032), no reusable contract suite (T033), no second provider (T034), no compiled/linked gRPC runtime,
and no new admitted dependency. The gateway binds one `AF_UNIX` stream socket under a restricted
directory with `0600` socket-file permissions, delegates the ten operations onto the accepted T025–T028
and T021–T024 in-process boundaries, enforces explicit bounds, per-request deadlines against the
accepted T025 time authority, and a bounded in-flight/rate budget, performs deterministic
disconnect/idle cleanup, and logs only bounded payload-free records.

## 3. Changed-path inventory (candidate)

| Path | Change | SHA-256 |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` | add | `2783be288ab5bca6c9d1cdccec8ecffd4e36b95af24159e0c3f018221bf40723` |
| `src/xverse/xcom/src/tool_gateway.cpp` | add | `57f2a95ec3db4999b6549fcb21192a6afe89ced02e82ce5a7e79d220e640a94c` |
| `src/xverse/xcom/CMakeLists.txt` | edit (additive) | `77ffda2ba7d9ebc1308d32352d22e01b370295cf263ab1c1ce3a33484b95f88e` |
| `tests/xcom/tool_gateway/gateway_support.hpp` | add | `0cda5e1ce36bc71ab0913a336a6f0f66e309502c3596731d900a28c71679fc31` |
| `tests/xcom/tool_gateway/gateway_session_tests.cpp` | add | `027a96764aceef120ca8a810142224071dab922722328a91db17cdcfc35c33ec` |
| `tests/xcom/tool_gateway/gateway_bounds_tests.cpp` | add | `56c6afeee3c9460e62610ece57cf15b221d498212ad9987cdb7982e7c5692ab1` |
| `tests/xcom/tool_gateway/gateway_lifecycle_tests.cpp` | add | `30411c26cbe30d0f6d3817bd774cf4ee354be3242c61f29ba48da746dc4293d8` |
| `tests/xcom/tool_gateway/gateway_local_ipc_tests.cpp` | add | `b5a844ca0fbf2f45929e16a473bfb0d1965dd740ad659721c18b0db80f89cc87` |
| `tests/xcom/tool_gateway/gateway_negative_tests.cpp` | add | `dff291f0ec025de19ab456c3e77bd3ff14f27c42776e6d27defce3111f8d79f6` |
| `tests/xcom/tool_gateway/gateway_logging_tests.cpp` | add | `fa4a0187c4c96debdc8fd51ca88e2aedd8e2c5a7b3f05fb4517159f10f3ee8d2` |
| `docs/engineering/xcom/t009/architecture-model.json` | edit | `XCOM-CMP-010` planned→established path status only |
| `docs/engineering/xcom/t010/unit-design.json` | edit | `XCOM-DU-020` planned→established path status only |
| `docs/engineering/xcom/t010/design-units.md` | edit | `XCOM-DU-020` planned→established path status only |

The remainder of the candidate change set is the T031 repository-owned work products, the T031
engineering requirement/architecture/unit/validation records, `engineering/trace/links.json`, the
refreshed `engineering/verification/measures/{unit,integration,validation}.json`, the refreshed
inherited `engineering/stage-results/*.json` digests, `engineering/project.json`, the T031 checkbox line
in `specs/007-xcom-core/tasks.md`, `reports/review-index.md`, and the generated
`reports/xcom-queue/t031-package.json` and `docs/engineering/xcom/t031/internal-review.json`. No
accepted predecessor byte under `src/`, `tests/`, `xdl/`, or `docs/engineering/xcom/t0{07..30}/` other
than the additive `src/xverse/xcom/CMakeLists.txt` wiring and the status-only path reconciliation was
changed.

## 4. Design realization notes

The implementation realizes the accepted plan. The following bounded, additive deviations from the
**illustrative** interface listing in `detailed-design.md` §3 are recorded (the authoritative content is
the accepted message/method contract and the accepted T021–T029 boundaries):

1. **Negotiation entry point.** `GatewaySession::negotiate(const v1::ProtocolVersion&)` is the production
   fail-closed compatibility predicate; `QueryVersion` is informational because the v1
   `QueryVersionRequest` carries no version field. An unsupported major is rejected before any other
   operation.
2. **Resolved session binding.** `GatewaySessionBinding` carries the exact accepted T025
   `Permit`/`SessionContext`/controller and the logical wire identities. The wire contract carries only
   logical strings, so the gateway maps a wire request onto the accepted in-process objects through this
   binding; no field bypasses the permit.
3. **Arm/activate collapse.** The accepted wire `SessionState` vocabulary has no `ACTIVE` value and the
   accepted T027 guard authorizes stimulation only for an active session, so `ArmSession` applies the
   accepted `Arm` then `Activate` transition and reports `SESSION_ARMED`. This is the wire contract's own
   collapse of declared→armed→active.
4. **Deadline model.** The declared arrival tick (`GatewaySessionBinding::arrival_tick`, a deterministic
   declared value, never an ambient wall clock) computes the absolute due tick; the dispatch tick is read
   from the accepted T025 `TimeAuthority`. An over-bound deadline is rejected; an overdue request returns
   `expired` and emits no item.
5. **Flow control.** The bounded in-flight/rate budget is initialized to
   `GatewayConfig::max_pending_requests()`; each admitted request consumes one token, saturation rejects
   deterministically and increments a visible counter, `on_idle_tick` replenishes the budget, and no
   queue grows beyond the configured bound.
6. **Framing seam.** `GatewayFrameStatus`, `GatewayFrameView`, and `gateway_decode_request_frame`
   realize the bounded method-name-addressed framing of `detailed-design.md` §5 and are covered by
   `T31-TS-007`; `LocalIpcChannel` remains the in-process read/write seam.
7. **Action pairing.** The submitted `interaction`/`direction` are derived from the declared action's
   canonical accepted pairing (the wire `Direction` vocabulary is inbound/outbound/bidirectional and does
   not name the accepted `request`/`respond` directions); the declared action kind is otherwise mapped
   1:1.
8. **Observation mode.** Observation taps are attached metadata-only with payload exposure off, matching
   `T031-SR-010` and the accepted observation policy.

No accepted requirement, contract byte, accepted test, register row, ADR, or REF-002 disposition was
changed or weakened.

## 4.1 Required register path-status reconciliation

Creating `tool_gateway.hpp`/`tool_gateway.cpp` makes the accepted T009/T010 planned paths present in the
tree, so the T009 and T010 validators require the planned→established path-status transition (status
field only; the same minimal normalization T030 applied to the T030-owned paths):

- `XCOM-CMP-010`: `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp`,
  `src/xverse/xcom/src/tool_gateway.cpp`;
- `XCOM-DU-020`: `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp`,
  `src/xverse/xcom/src/tool_gateway.cpp`.

Only the `status` field changes (`planned`→`established`); no path, component/unit identity, maturity,
requirement link, or governing ADR changes. Unit `XCOM-DU-020` remains `allocated`.

## 5. Generated-code provenance (inherited T030 contract)

T031 adds **no** generated code. It consumes the T030-generated Protocol Buffers messages and
independently re-verified that the offline admitted build regenerates the exact T030 outputs from the
committed schema:

| Provenance item | Value |
| --- | --- |
| Input schema identity | `proto/xverse/xcom/v1/tool_gateway.proto`, SHA-256 `cbb65f901b8522120da6333c4e569d4d8fa00db601abd7effaf70abe925dbb2d` |
| Protocol Buffers generator | admitted `libprotoc 3.12.4`; runtime header reports `GOOGLE_PROTOBUF_VERSION 3012004` |
| gRPC stub generator | admitted `grpc_cpp_plugin` 1.30.2 (provenance-only; not compiled or linked) |
| Output `tool_gateway.pb.h` | `80e886ea5f01b25274ee16ba0b395a354dec1145ff409fb3951b7af968edd8ad` |
| Output `tool_gateway.pb.cc` | `bcff542624d4638b3619e8c5d5601166e53493d259df90171cd348e1036009d8` |
| Output `tool_gateway.grpc.pb.h` (provenance-only) | `be80b0c71edf2a8d4a1f51fcbf9179352cd8b1643c2264ce933377a3a69e13c2` |
| Output `tool_gateway.grpc.pb.cc` (provenance-only) | `474b4f1c7b8fb05e66b47ac77e5b93af6589880d3da18f085d2edf552080bd4f` |

The digests equal the accepted T030 §5 record byte-for-byte, proving T031 consumed the pinned generated
contract unchanged. The generated outputs live under the git-ignored build tree; the committed `.proto`
remains the single source of truth. The gateway links only the compiled message library; the gRPC runtime
is not linked (`T031-GAP-01`).

## 6. Build wiring and runtime inventory

`src/xverse/xcom/CMakeLists.txt` is extended additively:

- one gateway runtime library `xverse_xcom_tool_gateway` (alias `xverse::xcom_tool_gateway`), routed
  through `xverse_xcom_apply_runtime_rules`, linking only the accepted in-process T021–T028 libraries,
  the T030 generated-message library, and the standard library;
- one declared `XVERSE_XCOM_RUNTIME_TARGETS` addition (`xverse_xcom_tool_gateway`), which the generated
  `xcom_build_contract` expectation moves with in the same change;
- six additive test executables with one hyphenated label each: `t031-session`, `t031-bounds`,
  `t031-lifecycle`, `t031-local-ipc`, `t031-negative`, `t031-logging`, each with a bounded build-tree
  working directory for the local-IPC scratch socket.

The admitted protobuf and generated headers are system includes, so third-party and generated-header
warnings are suppressed while the X-COM warning-as-error policy still governs every T031-owned source
line. No existing target, test name, label, command, or expected value changed, and no predecessor
discovery count was reduced.

## 7. Verification performed (candidate working tree)

Admitted offline inputs (environment, values recorded by name only): `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, `XVERSE_XCOM_T025_TEST_TOOLCHAIN`.

```sh
cmake -S . -B build/fabro-t030-t034-system-unit -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/fabro-t030-t034-system-unit --parallel 4
ctest --test-dir build/fabro-t030-t034-system-unit -N -L t031-
ctest --test-dir build/fabro-t030-t034-system-unit -L t031- --output-on-failure
ctest --test-dir build/fabro-t030-t034-system-unit -L "t0(2[6-9]|3[0-4])-" --output-on-failure
ctest --test-dir build/fabro-t030-t034-system-unit -R xcom_build_contract --output-on-failure
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
python3 ${XVERSE_FABRIC_ROOT}/automation/xcom_phase7_gate.py verify T031 4dded2317f895978cce0331ae88e34ac28b3a609
```

| Command | Observed result |
| --- | --- |
| `ctest -N -L t031-` | `Total Tests: 24` (6 session, 4 bounds, 4 lifecycle, 3 local-ipc, 5 negative, 2 logging) |
| `ctest -L t031-` | `100% tests passed, 0 tests failed out of 24` |
| `ctest -L "t0(2[6-9]|3[0-4])-"` | `100% tests passed` (24 T031 + preserved T026–T030) |
| `ctest -R xcom_build_contract` | `100% tests passed, 0 tests failed out of 1` |
| register validators | ownership, requirements traceability, architecture contracts, and unit design all pass |
| `git diff --check <baseline> --` | clean |

The T031 suites are in-process, offline, and deterministic; they use only the C++ standard library,
GTest, the accepted in-process T021–T028 libraries, and the T030 generated messages. The only file reads
are the bounded reads of the committed T031 header/source in `T31-TS-022`, and the only socket is the
bounded `AF_UNIX` bind/connect in `T31-TS-015`/`T31-TS-016` under the git-ignored build tree. No case
opens a network peer, a non-local address family, a resolver, a TLS session, a dynamic library, a
subprocess, or a legacy repository.

## 8. Requirement-to-case result

| Requirement | Cases | Result |
| --- | --- | --- |
| T031-SR-001 | `T31-TS-003` | pass |
| T031-SR-002 | `T31-TS-003` | pass |
| T031-SR-003 | `T31-TS-001`, `T31-TS-002`, `T31-TS-020` | pass |
| T031-SR-004 | `T31-TS-004`, `T31-TS-019`, `T31-TS-021` | pass |
| T031-SR-005 | `T31-TS-007`, `T31-TS-018`, `T31-TS-010` | pass |
| T031-SR-006 | `T31-TS-008` | pass |
| T031-SR-007 | `T31-TS-009`, `T31-TS-010` | pass |
| T031-SR-008 | `T31-TS-015`, `T31-TS-016`, `T31-TS-022` | pass |
| T031-SR-009 | `T31-TS-017`, `T31-TS-021` | pass |
| T031-SR-010 | `T31-TS-010`, `T31-TS-011` | pass |
| T031-SR-011 | `T31-TS-004`, `T31-TS-008`, `T31-TS-018`, `T31-TS-019` | pass |
| T031-SR-012 | `T31-TS-012`, `T31-TS-021` | pass |
| T031-SR-013 | `T31-TS-005`, `T31-TS-011`, `T31-TS-012`, `T31-TS-013`, `T31-TS-014` | pass |
| T031-SR-014 | `T31-TS-023`, `T31-TS-024` | pass |
| T031-SR-015 | `T31-TS-006` | pass |
| T031-SR-016 | `T31-TS-009`, `T31-TS-010` | pass |
| T031-SR-017 | build/discovery inspection (CHK-19); contributory `XcomToolGatewaySession.OperationSurfaceMatchesContract` | pass |
| T031-SR-018 | `T31-TS-022`; forbidden-API scan and offline build | pass |
| T031-SR-019 | register validators (CHK-21); contributory `XcomToolGatewaySession.OperationSurfaceMatchesContract` | pass |
| T031-SR-020 | Phase 7 gate (CHK-22); contributory `XcomToolGatewayBounds.DeadlineEnforcedBeforeEmission` | pass |
| T031-SR-021 | `T31-TS-001`, `T31-TS-003`; envelope decision inspection | pass |

Negative cases: NEG-01 (non-local address family / forbidden API) by `T31-TS-016`/`T31-TS-022`;
NEG-02 (competing interface / rejected method / claimed gRPC link) by `T31-TS-003`; NEG-03 (permit
bypass) by `T31-TS-004`/`T31-TS-021`; NEG-04 (unknown outcome as success) by
`T31-TS-013`/`T31-TS-019`; NEG-05 (implicit version acceptance) by `T31-TS-002`/`T31-TS-020`; NEG-06
(omitted bound / ambient clock / post-emission rejection) by `T31-TS-007`/`T31-TS-008`/`T31-TS-009`/
`T31-TS-018`; NEG-07 (new dependency or gRPC-runtime link) by the offline build; NEG-08 (payload/permit
logged) by `T31-TS-023`/`T31-TS-024`; NEG-09/NEG-10 (register/scope/additivity) by CHK-21/CHK-22.

## 9. Inherited provenance refresh

`src/xverse/xcom/CMakeLists.txt` changed, so the inherited `implemented_by` content digests for the
links that target it (`T020-L-046`, `T030-L-0210`, `T030-L-0211`, `T030-L-0213`, `T030-L-0214`) are
refreshed to the new SHA-256 in `engineering/trace/links.json`; link identity, relation, source, and
target are unchanged. The declared `engineering/trace/links.json` artifact digest in the inherited
`engineering/stage-results/*.json` is refreshed in the same change. No requirement, link identity,
relation, stage result, register row, or REF-002 disposition changes. The T031
`engineering/verification/measures/{unit,integration,validation}.json` descriptors are refreshed to the
24 discovered T031 cases and the three admitted measure commands, following the T020→T026–T030
precedent.

## 10. Maintenance notes

- The operation table in `gateway_operation_names()` is pinned to the accepted T030 descriptor method
  set by `T31-TS-003`; an accepted service change must update the table and the pinning case in the same
  change.
- Bounds are explicit `GatewayConfigInput` fields validated by `GatewayConfig::create`; adding a bound
  requires a validator, a `GatewayCapabilities` field, and a discovery case.
- The `AF_UNIX` endpoint applies `0600` socket-file permissions and fails closed on a missing/weak
  permission; keep the scratch socket path short (the `sockaddr_un` path is at most 108 bytes) and under
  the build tree.
- The gRPC transport runtime remains deferred (`T031-GAP-01`); a future link must not weaken the
  local-IPC-only boundary or add an admitted dependency without an ADR and a new task.
- The gateway logs only code/phase/logical-identity/size/timing/outcome; never add a payload or permit
  field to `GatewayLogRecord`.

## 11. Limitations

- **T031-GAP-01 — gRPC transport runtime deferred.** The admitted envelope cannot link the gRPC runtime;
  the accepted message/method contract is realized over bounded `AF_UNIX` framing bound 1:1 to the T030
  method names. No new dependency is added and no gRPC-runtime link is claimed.
- **T031-GAP-02 — gateway-side no-TCP proof only.** The separate-process client and the end-to-end
  `SC-011` demonstration are T032.
- **T031-GAP-03 — no reusable abstraction.** The gateway suites are T031-local and are not the T033
  reusable contract suite.
- **T031-GAP-04 — generated-code documentation.** The generated Protocol Buffers documentation policy
  remains `DOX-GAP-02` (T037); T031 documents only the hand-written gateway interface.
- **T031-GAP-05 — no deployed-service or compatibility claim.** The gateway is a bounded prototype
  validated with owned local fixtures.
- **L-T031-1 — admitted offline inputs.** The Phase 7 runner requires `XVERSE_XCOM_TOOLCHAIN`,
  `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` (or the documented A-1 cache
  seed); without them configure fails closed before any T031 target builds.
- **L-T031-2 — strict target-repository integration is separate.** The whole-system integration measure
  assembles the candidate into the pinned target checkout and runs separately from this stage; this
  record does not claim its result.
- **L-T031-3 — external review deferred.** External Codex review and user acceptance remain T039/T041 and
  are deferred until backlog `xcom-t030-t034-20260928` completes.

## 12. Maturity

`XCOM-SW-GW-002` "Local-IPC-only bounded gateway" is recorded **implemented** for the gateway slice by
T031. `XCOM-SW-GW-003` (T032), T033, T034, and T035–T041 remain allocated. The capability REF-002
disposition stays `unchanged` with an empty `promoted` list; `XVE-SYS-0141` remains deferred and
unpromoted.

## 13. Repair closure — empty unit cases at the reviewed predecessor candidate

The reviewed predecessor candidate (run `01M3MYT7KWWX3MJXTTDS4FJG48`, reviewed candidate commit
`e7817beba8a9b4f6cd1aa7d49307e4b8034195e4`) passed implementation verification, the independent internal
review, the review gate, packaging, and candidate sealing, but the trusted unit gate then failed before
running the test command with `unit specification: missing unit_cases`. The trusted engineering inventory
validates each unit record with a required-fields check that treats an empty `unit_cases` list as absent,
so the three governance/build records `T031-SR-017-U`, `T031-SR-019-U`, and `T031-SR-020-U` — whose
verification is a named inspection rather than a behavioural case — failed closed.

This successor repair resolves the finding at the root cause without changing the gateway, its tests, an
accepted requirement, the trace, or the original review:

- Each of the three records now declares exactly one unit case that reuses an already-discovered `t031-`
  GoogleTest case, with its `expected` text stating that the case contributes behavioural context only and
  that the requirement is checked by its named inspection. The mechanism and wording follow the accepted
  T030 precedent for the same class of governance/gate requirements.
  - `T031-SR-017-U`: `XcomToolGatewaySession.OperationSurfaceMatchesContract` (additive wiring inspection, CHK-19).
  - `T031-SR-019-U`: `XcomToolGatewaySession.OperationSurfaceMatchesContract` (register/maturity inspection, CHK-21).
  - `T031-SR-020-U`: `XcomToolGatewayBounds.DeadlineEnforcedBeforeEmission` (Phase 7 gate, CHK-22).
- No unit case ID is new: the declared T031 unit-case set remains exactly the 24 committed `t031-` cases
  executed by `ctest -L t031-`, so the declared discovery still equals the executed discovery and the
  trusted unit-measure expected IDs are unchanged. No coverage is invented and no accepted requirement or
  test is weakened.
- `docs/engineering/xcom/t031/unit-specifications.md` discloses the same three contributory cases.

Closure evidence at this successor revision: the trusted engineering inventory passes; the capability-007
trace graph validates with fresh endpoint digests; the T007–T010 register validators pass;
`ctest -L t031-` reports `100% tests passed, 0 tests failed out of 24`; and
`xcom_phase7_gate.py verify T031 4dded2317f895978cce0331ae88e34ac28b3a609` passes. The original internal
review is preserved unchanged as historical evidence for the predecessor candidate; a fresh independent
review covers this successor, and T039/T041 acceptance remains separate.

Because `docs/engineering/xcom/t031/implementation.md` is an `implemented_by` trace endpoint, its two
`target_revision` digests in `engineering/trace/links.json`, and the inherited `engineering/trace/links.json`
declared digest in the legacy `engineering/stage-results/{integration,documentation,internal-review}.json`,
are refreshed in this change; no link identity, relation, source, or target changes.
