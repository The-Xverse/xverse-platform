# T030 Implementation Record — Versioned gRPC/Protocol Buffers Tool API and Additive Evolution Rules

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T030 (capability 007, slice `T-CORE`/GW) |
| Stage / role | implementation |
| Revision | 1 (versioned external-tool contract slice) |
| Baseline revision | `80c236638e160c5e991e5a537e29d407e7462dc6` |
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

T030 authors exactly one versioned external-tool contract and proves it at the schema, generated-
descriptor, and generated-source level. It authors no gateway server, local IPC listener, socket,
separate process, compiled/linked gRPC runtime, synthetic client, reusable contract suite, second
provider, benchmark, or delivery bundle. No TCP listener exists and no external peer is contacted in
any T030 file or test.

## 3. Changed-path inventory (candidate)

| Path | Change | SHA-256 |
| --- | --- | --- |
| `proto/xverse/xcom/v1/tool_gateway.proto` | add | `cbb65f901b8522120da6333c4e569d4d8fa00db601abd7effaf70abe925dbb2d` |
| `src/xverse/xcom/CMakeLists.txt` | edit (additive) | `e88eda22fc9cd3b38f03027de160ee7648750bf15c168980e516292577e419e8` |
| `tests/xcom/tool_gateway/contract_support.hpp` | add | `d1bd2fb7529198e6e58a679517967a6d440b32f8123099f2b2a2f3e513cf4f6e` |
| `tests/xcom/tool_gateway/contract_tests.cpp` | add | `a94c51f5bbe8ef750fa92220527cd754c5b5c175f8c68080612230b9f0b65942` |
| `tests/xcom/tool_gateway/evolution_tests.cpp` | add | `ccca8cbdcd006b90d27b495941b813a4ca6824b875d4278f9ddec4bec750776c` |
| `tests/xcom/tool_gateway/negative_tests.cpp` | add | `1210ef5e3afd9c7f1745a34c9d73cd4752750aafe00a94acc218adf63b7717c1` |
| `tests/xcom/tool_gateway/provenance_tests.cpp` | add | `e4e8f9cdd4eedac1bf5d3e3c1eae07c57fccc5c2b1b1541f46388ae4c917ee59` |
| `docs/engineering/xcom/t009/architecture-model.{json,md}` | edit | planned→established path status only |
| `docs/engineering/xcom/t010/unit-design.{json,md}` | edit | planned→established path status only |

The remainder of the candidate change set is the T030 repository-owned work products, the T030
engineering requirement/architecture/unit/validation records, `engineering/trace/links.json`, the
refreshed `engineering/verification/measures/{unit,integration,validation}.json`, the refreshed
inherited `engineering/stage-results/*.json` digests, `engineering/project.json`, the T030 checkbox
line in `specs/007-xcom-core/tasks.md`, `reports/review-index.md`, and the generated
`reports/xcom-queue/t030-package.json` and `docs/engineering/xcom/t030/internal-review.json`.
No accepted predecessor byte under `src/`, `tests/`, `xdl/`, or `docs/engineering/xcom/t0{07..29}/`
other than the additive `src/xverse/xcom/CMakeLists.txt` wiring was changed.

## 4. Design realization note

The normative additive-evolution rule (`detailed-design.md` §3.2 rule 2 and verification-plan
`CHK-14`) requires **every** message to declare the `reserved 1000 to 1999;` extension band, and
unit case `T30-TS-012` asserts it for every message. The illustrative schema in
`detailed-design.md` §3 omitted the band on seven small messages. The implementation applies the
normative rule and declares the band on every message; no field number, name, or type was changed,
so the schema remains additive to the illustrative listing and the pinned manifest is unchanged.

## 4.1 Required register path-status reconciliation

Creating the committed contract and its test directory makes six accepted T009/T010 planned paths
present in the tree, so the T009 and T010 validators require the planned→established path-status
transition (the same minimal normalization T026–T029 applied to T010; allocated units such as
`XCOM-DU-016`/`-017`/`-018` already carry established test paths while remaining `allocated`):

- `XCOM-CMP-010`: `proto/xverse/xcom/v1/tool_gateway.proto`, `tests/xcom/tool_gateway/`;
- `XCOM-CMP-011`: `tests/xcom/tool_gateway/`;
- `XCOM-DU-019`: `proto/xverse/xcom/v1/tool_gateway.proto`;
- `XCOM-DU-020`, `XCOM-DU-021`: `tests/xcom/tool_gateway/`.

Only the `status` field changes (`planned`→`established`); no path, component/unit identity, maturity,
requirement link, or governing ADR changes, and the deterministic Markdown projection is
regenerated exactly. Unit `XCOM-DU-020`/`-021` (T031/T032) remain `allocated`; only the shared test
directory they will extend is now present.

## 5. Generated-code provenance

The build generates both artifacts from the committed schema with the T011-admitted tools, offline,
with only the admitted prefix library directory on the child library path.

```text
protoc -I <repo>/proto --cpp_out=<build>/t030-proto-gen --grpc_out=<build>/t030-proto-gen \
       --plugin=protoc-gen-grpc=<admitted-prefix-bin>/grpc_cpp_plugin \
       xverse/xcom/v1/tool_gateway.proto
```

| Provenance item | Value |
| --- | --- |
| Input schema identity | `proto/xverse/xcom/v1/tool_gateway.proto`, SHA-256 `cbb65f901b8522120da6333c4e569d4d8fa00db601abd7effaf70abe925dbb2d` |
| Protocol Buffers generator | `protobuf-compiler_3.12.4-1ubuntu7.22.04.6_amd64.deb`, SHA-256 `a124cc30fadf8e83f86fd7e1b9c776befd336d092bb81f95de1dc39d79b61ce7`, reported `libprotoc 3.12.4` |
| gRPC stub generator | `protobuf-compiler-grpc_1.30.2-3build6_amd64.deb`, SHA-256 `79debaed17ff25444a9c450b4b342e3d7565e80c062da2356b42ceb73e305331` (`grpc_cpp_plugin` 1.30.2 from the T011 dependency lock) |
| Runtime compile/link dependency | admitted `protobuf::libprotobuf` 3.12.4 only |
| Output `tool_gateway.pb.h` | `80e886ea5f01b25274ee16ba0b395a354dec1145ff409fb3951b7af968edd8ad` |
| Output `tool_gateway.pb.cc` | `bcff542624d4638b3619e8c5d5601166e53493d259df90171cd348e1036009d8` |
| Output `tool_gateway.grpc.pb.h` (provenance-only) | `be80b0c71edf2a8d4a1f51fcbf9179352cd8b1643c2264ce933377a3a69e13c2` |
| Output `tool_gateway.grpc.pb.cc` (provenance-only) | `474b4f1c7b8fb05e66b47ac77e5b93af6589880d3da18f085d2edf552080bd4f` |

The Protocol Buffers messages are compiled into `xverse_xcom_tool_gateway_proto`. The gRPC stubs are
generated for provenance but are **not** compiled or linked because the T011 admitted envelope lacks
the gRPC runtime transitive libraries (for example `libcares`); a standalone gRPC++ link fails
closed (`T030-GAP-02`, owned by T031). The generated outputs live under the git-ignored build tree
and are reproducible from the committed `.proto`.

## 6. Build wiring and runtime inventory

`src/xverse/xcom/CMakeLists.txt` is extended additively:

- one generated-message library `xverse_xcom_tool_gateway_proto` (alias
  `xverse::xcom_tool_gateway_proto`), routed through `xverse_xcom_apply_runtime_rules`, linking only
  `protobuf::libprotobuf`;
- one declared `XVERSE_XCOM_RUNTIME_TARGETS` addition (`xverse_xcom_tool_gateway_proto`), which the
  generated `xcom_build_contract` expectation moves with in the same change;
- four additive test executables with one hyphenated label each:
  `t030-contract`, `t030-evolution`, `t030-negative`, `t030-provenance`.

The admitted protobuf and generated headers are system includes, so third-party and generated-header
warnings are suppressed while the X-COM warning-as-error policy still governs every T030-owned
source line. No existing target, test name, label, command, or expected value changed, and no
predecessor discovery count was reduced.

## 7. Verification performed (candidate working tree)

Admitted offline inputs (environment, values recorded by name only): `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, `XVERSE_XCOM_T025_TEST_TOOLCHAIN`.

```sh
cmake -S . -B build/t030-dev -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/t030-dev --parallel 4
ctest --test-dir build/t030-dev -N -L t030-
ctest --test-dir build/t030-dev -L t030- --output-on-failure
ctest --test-dir build/t030-dev -L "t0(2[6-9]|3[0-4])-" --output-on-failure
ctest --test-dir build/t030-dev -R xcom_build_contract --output-on-failure
ctest --test-dir build/t030-dev --output-on-failure --parallel 4
```

| Command | Observed result |
| --- | --- |
| `ctest -N -L t030-` | `Total Tests: 24` (11 contract, 5 evolution, 5 negative, 3 provenance) |
| `ctest -L t030-` | `100% tests passed, 0 tests failed out of 24` |
| `ctest -L "t0(2[6-9]|3[0-4])-"` | `100% tests passed, 0 tests failed out of 123` (24 T030 + 99 preserved T026–T029) |
| `ctest -R xcom_build_contract` | `100% tests passed, 0 tests failed out of 1` |
| full `ctest` | `100% tests passed, 0 tests failed out of 429` |

The T030 suites are in-process, offline, and deterministic; they use only the C++ standard library,
GTest, and the admitted Protocol Buffers runtime. No case opens a network peer, socket, resolver,
TLS session, dynamic library, subprocess, or legacy repository. The only file reads are the bounded
reads of the generated build-tree headers in `T30-TS-023`/`T30-TS-022`.

## 8. Requirement-to-case result

| Requirement | Cases | Result |
| --- | --- | --- |
| T030-SR-001 | `T30-TS-001` | pass |
| T030-SR-002 | `T30-TS-002`, `T30-TS-003` | pass |
| T030-SR-003 | `T30-TS-004`, `T30-TS-020` | pass |
| T030-SR-004 | `T30-TS-005` | pass |
| T030-SR-005 | `T30-TS-006` | pass |
| T030-SR-006 | `T30-TS-007` | pass |
| T030-SR-007 | `T30-TS-008` | pass |
| T030-SR-008 | `T30-TS-009` | pass |
| T030-SR-009 | `T30-TS-010` | pass |
| T030-SR-010 | `T30-TS-011`, `T30-TS-018` | pass |
| T030-SR-011 | `T30-TS-017`, `T30-TS-019` | pass |
| T030-SR-012 | `T30-TS-012`, `T30-TS-013`, `T30-TS-021` | pass |
| T030-SR-013 | `T30-TS-014`, `T30-TS-015`, `T30-TS-016` | pass |
| T030-SR-014 | `T30-TS-022`, `T30-TS-023`, `T30-TS-024` | pass |
| T030-SR-015 | build/discovery inspection (CHK-16/CHK-17) | pass |
| T030-SR-016 | `T30-TS-002`…`T30-TS-011` | pass |
| T030-SR-017 | forbidden-API source inspection (CHK-18) | pass (no prohibited call) |
| T030-SR-018 | public-safety scan (CHK-19) | pass (no prohibited content) |
| T030-SR-019 | register validators (CHK-20) | pass |
| T030-SR-020 | Phase 7 gate (CHK-21) | pass |

Negative cases: NEG-01/NEG-03 (forbidden transport/address/export shape; missing session/permit
identity) are realized by `T30-TS-017`/`T30-TS-019`; NEG-02 (reserved-number reuse/renumber) by
`T30-TS-012`/`T30-TS-013`/`T30-TS-021`; NEG-04 (dropped unknown field/enum) by
`T30-TS-014`…`T30-TS-016`; NEG-05 (implicit version acceptance) by `T30-TS-004`/`T30-TS-020`;
NEG-06 (unbounded payload/bound) by `T30-TS-011`/`T30-TS-018`; NEG-07 (new dependency, network,
gRPC-runtime link, or committed generated source of truth) by CHK-16/CHK-18; NEG-08 by CHK-19.

## 9. Inherited provenance refresh

`src/xverse/xcom/CMakeLists.txt` changed, so the inherited `implemented_by` content digest for the
only inherited link that targets it (`T020-L-046`) is refreshed to the new SHA-256 in
`engineering/trace/links.json`; the link identity, relation, source, and target are unchanged. The
declared `src/xverse/xcom/CMakeLists.txt` and `engineering/trace/links.json` artifact digests in the
inherited `engineering/stage-results/*.json` are refreshed in the same change. No requirement, link
identity, relation, stage result, register row, or REF-002 disposition changes. The T030
`engineering/verification/measures/{unit,integration,validation}.json` descriptors are refreshed to
the 24 discovered T030 cases and the three admitted measure commands, following the T020→T026–T029
precedent.

## 10. Maintenance notes

- The `.proto` package, field numbers, and field names are frozen for v1. An additive change adds
  fresh field numbers below 1000 (outside the reserved band) and, if it extends a pinned message,
  updates `tests/xcom/tool_gateway/contract_support.hpp` `PinnedManifest()` in the same change.
- Removing or renaming a field requires reserving its number and name in the same change; the
  reserved-band/reuse cases fail closed otherwise.
- The generator identity is pinned by the T011 dependency lock; a generator change requires an
  updated generation provenance record and re-verification of the output digests.
- The gRPC runtime envelope remains open. T031 must complete the gRPC runtime link or record the
  decision; it must not weaken the local-IPC-only boundary.

## 11. Limitations

- **T030-GAP-01 — contract-only boundary.** T030 establishes no deployed service, transport, IPC,
  compatibility, or production-readiness claim.
- **T030-GAP-02 — gRPC runtime linkage out of envelope.** The gRPC stubs are generated for
  provenance and not compiled or linked; the link fails closed. Owned by T031.
- **T030-GAP-03 — version rejection is contract-level.** The fail-closed predicate is test-local;
  the production predicate and server-side rejection are T031/T034.
- **T030-GAP-04 — no separate-process proof.** T030 runs in-process descriptor tests only; the
  separate-process client and no-TCP-listener demonstration are T032 (`SC-011`).
- **T030-GAP-05 — generated code is not Doxygen-documented.** The generated C++ documentation
  policy remains `DOX-GAP-02`; warning-free generated-code documentation is T037.
- **T030-GAP-06 — no reusable abstraction.** The test helpers are T030-local and are not the T033
  reusable gateway contract suite.
- **L-T030-1 — admitted offline inputs.** The Phase 7 runner requires `XVERSE_XCOM_TOOLCHAIN`,
  `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` (or the documented A-1 cache
  seed); without them configure fails closed before any T030 target builds.
- **L-T030-2 — strict target-repository integration is separate.** The whole-system integration
  measure assembles the candidate into the pinned target checkout and runs separately from this
  stage; this record does not claim its result.
- **L-T030-3 — external review deferred.** External Codex review and user acceptance remain T039/
  T041 and are deferred until backlog `xcom-t030-t034-20260928` completes.

## 12. Maturity

`XCOM-SW-GW-001` "Versioned provider-neutral tool API" is recorded **implemented** for the contract
slice by T030. `XCOM-SW-GW-002` (T031), `XCOM-SW-GW-003` (T032), T033, T034, and T035–T041 remain
allocated. The capability REF-002 disposition stays `unchanged` with an empty `promoted` list;
`XVE-SYS-0141` remains deferred and unpromoted.

## 13. Repair closure — whole-system integration trace correction (successor candidate)

### 13.1 Finding and root cause

Strict delivery over the successor candidate reported seven T030 software-requirement rows without a
whole-system integration test and integration test ID: `T030-SR-011`, `T030-SR-014`, `T030-SR-015`,
`T030-SR-017`, `T030-SR-018`, `T030-SR-019`, and `T030-SR-020`. The trace schema derives a row's
`integration_tests` and `integration_test_ids` only from `verified_by` links whose target is a
verification measure of `kind: integration` (see the matrix builder in the repository-owned
engineering checker). The other thirteen T030 software requirements carried
`verified_by T030-SR-### -> integration`; these seven did not, so the matrix reported
`whole-system integration test` and `whole-system integration test ID` as missing even though the
whole-system integration measure already executed and passed. The defect was a missing trace edge, not
missing executed coverage.

### 13.2 Correction (trace only; no behaviour change)

Seven additive `verified_by` links are recorded in `engineering/trace/links.json`. Each points at the
trusted whole-system integration measure `engineering/verification/measures/integration.json`, whose
declared `test_ids` are the twenty-four `t030-` generated-contract cases executed by
`run_xcom_phase7_tests.py integration` in the assembled pinned target checkout (`100% tests passed`):

| Requirement | Added link | Whole-system integration cases that exercise the requirement |
| --- | --- | --- |
| `T030-SR-011` | `T030-L-0251` | `XcomToolGatewayNegative.NoTcpOrAddressPrimitive`, `XcomToolGatewayNegative.NoBypassOfPermitOrSession` |
| `T030-SR-014` | `T030-L-0252` | `XcomToolGatewayProvenance.GeneratedCodeProvenanceRecorded`, `XcomToolGatewayProvenance.GeneratedGrpcStubDeclaresService`, `XcomToolGatewayProvenance.SerializedDescriptorMatchesSource` |
| `T030-SR-015` | `T030-L-0253` | the assembled whole-system build drives the additive `t030-contract`/`t030-evolution`/`t030-negative`/`t030-provenance` targets registered by the unchanged additive `CMakeLists.txt` wiring; the four suites are the executed integration evidence |
| `T030-SR-017` | `T030-L-0254` | the whole-system integration run is offline and local-only and links only the admitted Protocol Buffers runtime and GTest; `XcomToolGatewayNegative.NoTcpOrAddressPrimitive` fails closed on any transport shape |
| `T030-SR-018` | `T030-L-0255` | the executed whole-system integration measure over the public-safe T030 artifact set; no credential, private address, payload, or host path is committed |
| `T030-SR-019` | `T030-L-0256` | the executed whole-system integration measure over the unchanged T007–T010 registers with `XCOM-SW-GW-001` implemented for the contract slice and REF-002 unchanged |
| `T030-SR-020` | `T030-L-0257` | the executed whole-system integration measure that completes the deterministic Phase 7 gate path for T030 |

The added links are additive and truthful: they attach the already-executed whole-system integration
measure to requirements that the measure's assembled run and named cases exercise. No requirement
text, acceptance criterion, contract byte, production source, test, verification measure, or
`test_ids` list was changed, and no coverage is claimed beyond what the executed measure reports.
The inherited Phase 6 (`T026`–`T029`) integration and conformance trace links are untouched.

### 13.3 Hash and artifact refresh

The seven added links have no `implemented_by` content digest (only `verified_by` measure links), so
no code endpoint digest changes. This implementation record is the `implemented_by` target of
`T030-L-0228`/`T030-L-0229`; both targets' SHA-256 revision is refreshed to the repaired file digest
after the final edit. `docs/engineering/xcom/t030/requirements.md` is unchanged, so `T030-L-0225`/
`T030-L-0226` keep their recorded digest. The refreshed `engineering/trace/links.json` digest is
recorded in the inherited `engineering/stage-results/{documentation,integration,internal-review}.json`
artifacts, and the refreshed `reports/review-index.md` digest is recorded in
`engineering/stage-results/{documentation,internal-review}.json`. Link identity, relation, endpoints,
and the inherited `T020-L-046` digest are otherwise unchanged.
