# T038 delivery envelope — T039 R3 repair and T040 reconciliation

This is the T039 R3 successor repair record for the T038 delivery envelope. It repairs `T039-F07`
and reconciles `T040-E01`, `T040-E02`, and `T040-E03` on the exact R2 candidate
`b15936781995ef188db30d7f99fc462701662b90` (R2 independent-review baseline
`a9c6e5d41e65625ed2b8c6f5a4457e10c6fcb090`). It preserves the R2 `T039-F01`–`T039-F06` corrections and
does not mark T039, T040, or T041 complete, accept, or merge anything. `engineering/project.json`
stays at `task_id` `T038`.

The historical R2 review results, the R2 evidence manifest, and the accepted-baseline evidence remain
immutable inputs at their pinned identity. Nothing in this record is a successor execution of those
inputs; the R3 evidence is generated only for this successor assembly.

## 1. Authorization and identity boundary

| Field | Value |
| --- | --- |
| Task | T038 (capability 007, Phase 8 delivery envelope) |
| Accepted platform baseline | `a9c6e5d41e65625ed2b8c6f5a4457e10c6fcb090` |
| R2 candidate (reviewed) | `b15936781995ef188db30d7f99fc462701662b90` |
| R2 repair input | `9d6e10943de4619f9c868bcbcc0f642e90420628` |
| Repair owner | pinned DeepSeek Flash, high reasoning effort (Fabro stage policy, no fallback) |
| External T039/T040 inspection | separate workflow; not performed here |
| T041 user acceptance and main merge | separate gates; not authorized or performed here |

## 2. T039-F07 repair — single-owned service-emulation lease

**Finding (major).** Repeated successful `AcquireLease` calls overwrote the session's sole
`lease_key_` and reused the same public lease identifier, so an owner disconnect released or
quarantined only the last key and left an earlier lease active in the authoritative registry. The
`QuerySession` lease fields could then report no held lease while the registry still retained one.

**Root cause and repair.** `GatewaySession::AcquireLease` admitted another allocation while a lease
was held and assigned the request identity before the registry call. The repair enforces the declared
single-owned-lease boundary before any further allocation and computes the candidate request identity
locally, so a declined acquisition never mutates the held identity:

| File | Change |
| --- | --- |
| `src/xverse/xcom/src/tool_gateway.cpp` | Before a second registry allocation, decline with `LEASE_CONFLICT` and diagnostic `gw.lease.held`, report the retained original `lease_id` in the response, increment the rejected counter, and log a rejected lease outcome. The registry `acquire` is not called and no member is mutated. The request identity is computed into a local and assigned to `lease_request_id_` only on `LeaseStatus::Ok`. |
| `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` | `AcquireLease` documentation now states the single-owned-lease boundary and the preserved original identity. |

An expanded bounded ownership set is explicitly out of scope; it would require its own design and is
not needed for this narrow repair. Normal first acquisition, `LEASE_ACTIVE`, and exact-identity
release behavior are unchanged.

**Requirement IDs:** `T031-SR-012` (exclusive generation-bound lease delegation; no ambiguous
ownership) and `T031-SR-013` (disconnect/idle cleanup of validation-owned resources).

**Named regressions (generated clients).** `tests/xcom/tool_gateway/grpc_generated_client_tests.cpp`
(`xverse_xcom_grpc_generated_client_tests`, label `t030-grpc`):

| Case | Assertion |
| --- | --- |
| `XcomGrpcGeneratedClient.RepeatedAcquireLeaseDeclinesSecondAllocation` | First acquisition is `LEASE_ACTIVE`; a second acquisition of a different endpoint and a repeat of the held endpoint both return `LEASE_CONFLICT` with the original `lease_id`; the authoritative registry stays at one active lease; owner cancellation leaves zero active leases and a terminal session. |
| `XcomGrpcGeneratedClient.RepeatedAcquireLeaseOriginalIdentityStillReleases` | After a declined repeated acquisition, the original `lease_id` releases the lease (`LEASE_RELEASED`) and the registry reports `active == 0`, `released == 1`. |
| `XcomGrpcGeneratedClient.WatchCancellationReleasesLiveResources` | (strengthened) owner cancellation also empties the authoritative registry. |
| `XcomGrpcGeneratedClient.AbruptClientExitReleasesLiveResources` | (strengthened) abrupt owner exit also empties the authoritative registry. |
| `XcomGrpcGeneratedClient.ShutdownTerminatesLiveWatchAndCleansResources` | (strengthened) server shutdown with a live watch, lease, and stream also empties the authoritative registry. |

The shared fixture `tests/xcom/tool_gateway/gateway_support.hpp` is unchanged, so the immutable
external probe fixture remains valid. The R2 failing probe mode `two-leases` now yields
`registry_active == 0` after owner disconnect; the disposition record does not re-run it here.

**Negative self-check.** With the new guard temporarily disabled, both new cases fail
(`registry.active == 2` after two acquisitions and `1` after cancellation; the second state is
`LEASE_ACTIVE` instead of `LEASE_CONFLICT`); with the guard restored all ten generated-client cases
pass. This demonstrates the regression detects the defect instead of rejecting all acquisitions.

**Focused outcome.** Normal build `build/gi` (`cmake -S . -B build/gi -G Ninja
-DCMAKE_BUILD_TYPE=Debug`), `xverse_xcom_grpc_generated_client_tests` 10/10 pass; full normal
`ctest --test-dir build/gi` 524/524 pass (522 predecessor cases plus the two new cases).

## 3. T040-E01 — current trace graph reconciliation

**Finding.** `engineering/trace/links.json` held 79 stale `implemented_by` SHA-256 pins across eight
files, and six changed paths had no target edge.

**Resolution.**

- All 79 stale pins were refreshed to the exact current file digests after the material edits
  (`src/xverse/xcom/CMakeLists.txt` 13, `proto/xverse/xcom/v1/tool_gateway.proto` 26,
  `include/xverse/xcom/tool_gateway.hpp` 6, `src/tool_gateway.cpp` 6,
  `gateway_session_tests.cpp` 6, `gateway_bounds_tests.cpp` 8, `gateway_lifecycle_tests.cpp` 4,
  `gateway_contract_suite.hpp` 10).
- 28 new `implemented_by` edges represent the six previously unlinked changed paths. The edge sources
  are the requirement and unit records the successor repairs, so the relationship is a claim, not a
  bare file listing:
  - `docs/engineering/xcom/t039/transport-repair.md` — `T031-SR-012`, `T031-SR-012-U`, `T031-SR-013`, `T031-SR-013-U` (design/finding narrative for the repaired requirements).
  - `proto/xverse/xcom/v1/gateway_liveness.proto` — `T031-SR-012`, `T031-SR-012-U`, `T031-SR-013`, `T031-SR-013-U` (the watch contract that binds the logical owner).
  - `src/xverse/xcom/include/xverse/xcom/tool_gateway_grpc.hpp` and `src/xverse/xcom/src/tool_gateway_grpc.cpp` — `T031-SR-012`, `T031-SR-012-U`, `T031-SR-013`, `T031-SR-013-U` (the production adapter).
  - `tests/xcom/tool_gateway/grpc_generated_client_tests.cpp` — `T031-SR-006`, `T031-SR-006-U`, `T031-SR-010`, `T031-SR-010-U`, `T031-SR-011`, `T031-SR-011-U`, `T031-SR-012`, `T031-SR-012-U`, `T031-SR-013`, `T031-SR-013-U` (the generated-client regression harness).
  - `tests/xcom/tool_gateway/gateway_support.hpp` — `T031-SR-012-U`, `T031-SR-013-U` (the shared bounded fixture).
- The affected unit specifications now name the successor cases and source paths:
  `T031-SR-006-U`, `T031-SR-010-U`, `T031-SR-011-U`, `T031-SR-012-U`, `T031-SR-013-U`, and
  `T035-SR-005-U` (F01 sanitizer-coverage disposition). The human-readable
  `docs/engineering/xcom/t031/unit-specifications.md` gains a successor addendum; no `T31-TS-###` case
  is renamed, removed, or weakened.
- Existing passing case names alone were not treated as justification: each added unit case is tied to
  a requirement it verifies, and `T031-SR-012-U`/`T031-SR-013-U` carry the F07 ownership claim.
- REF-002 dispositions are unchanged; no allocated or deferred SADS target is promoted.

## 4. T040-E02 — inherited report identities

**Finding.** The retained historical T038 verifier report carried the 79 stale links and the
inherited T036 benchmark verification failure, and its positive self-test failed. Copying an R2 report
is insufficient because both verifiers bind `engineering/trace/links.json` and
`specs/007-xcom-core/tasks.md` in their material inventories.

**Resolution and ordering.** All source, trace, task, and disposition edits were completed first.
Then, on the same working-tree successor revision:

1. `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json`
   regenerated the inherited T036 evidence (outcome `pass`; disabled-tap latency regression
   `1.1256%`, throughput regression `1.1131%`, both within the accepted 2% threshold).
2. `python3 engineering/check_xcom_traceability.py --report reports/xcom-queue/t038-traceability.json`
   regenerated the T038 traceability evidence at the successor material digest.
3. `python3 engineering/check_xcom_traceability.py --verify reports/xcom-queue/t038-traceability.json`
   and `--self-test` were then run without weakening either gate.

Both scripts keep their same-revision/direct-child identity checks, stale-input rejection, public-safe
scans, predecessor-completeness checks, and negative self-tests. The historical failed outcomes remain
historical evidence and are not promoted: the direct historical Phase 6 script still fails its
original Doxyfile-immutability check, and the authorized inherited Phase 6 replay is recorded
separately with its limited scope.

## 5. T040-E03 — predecessor transport decisions and successor dispositions

**Finding.** Inherited requirements, architecture, detailed design, and verification plans still
described the generated gRPC stubs as provenance-only and the transport runtime as deferred.

**Resolution.** The historical decisions are preserved verbatim as historical evidence; explicit,
component-scoped successor dispositions were added without weakening accepted scope:

| Work product | Historical item | Successor disposition |
| --- | --- | --- |
| `docs/engineering/xcom/t030/detailed-design.md` | `T30-DD-03`, `T30-GAP-02` | Superseded for the linked gateway component only; the earlier provenance-only slice remains historical. `T30-DD-02`/`T30-DD-04` still hold. |
| `docs/engineering/xcom/t031/architecture.md` | `T31-XB-9`, `T031-GAP-01` | Superseded for the linked gateway component; the in-process core still links no gRPC runtime. |
| `docs/engineering/xcom/t031/detailed-design.md` | `T31-DD-01` | The "cannot link the gRPC runtime" premise is superseded for the linked gateway component; the framing decision stands. |
| `docs/engineering/xcom/t031/verification-plan.md` | `CHK-03`, `CHK-20` | Partially superseded for the linked gateway component; offline/local-only/no-new-dependency still hold; the T032 synthetic client keeps its restriction. |
| `docs/engineering/xcom/t032/detailed-design.md`, `docs/engineering/xcom/t032/verification-plan.md` | `T32-DD-01`, `T32-DD-13`, `CHK-03`, `CHK-20` | The T032 separate-process synthetic client retains its framed local-IPC transport and `T032-GAP-01`; the linked successor gateway is a distinct component. |
| `engineering/requirements/T032-SR-017.json` | accepted, revision 1 | Additive `successor_disposition` field; requirement text and revision unchanged; the successor gateway supersedes the deferred-transport premise for the platform gateway only, and no REF-002 target is promoted. |
| `docs/engineering/xcom/t031/unit-specifications.md` | T031 unit inventory | Successor addendum naming the generated-client cases, the F07 single-owned-lease boundary, and the declared limits. |

**Maintained client guidance carried forward.** The watch identifier is a logical lifecycle
association, not OS process authentication; clients must keep it private and must not share it. A
running host action callback must return before its resources can be destroyed; shutdown does not
preempt arbitrary callback code. Durable lookup reconciles a committed immediate outcome; the absence
of a scheduled intent remains explicitly uncertain and does not authorize a retry.

## 6. Generated-service provenance (both generated services)

The committed `.proto` files are the source of truth; both generated services are produced in one
build-tree generation step. Inputs and outputs are bound by SHA-256 (identical for the normal and
instrumented configurations at this candidate):

| Generated service | Input | Input SHA-256 |
| --- | --- | --- |
| `ToolGateway` | `proto/xverse/xcom/v1/tool_gateway.proto` | `90e56f82d1251f04732dfaa5003597dfc43b7cfe3212e33b5507cd9e04cf289f` |
| `GatewayLiveness` | `proto/xverse/xcom/v1/gateway_liveness.proto` | `a649602b5de394da89eebdd1135f67583ff76a24c11ad86f9a1060f25f1da527` |

| Generated output (build tree) | SHA-256 |
| --- | --- |
| `xverse/xcom/v1/tool_gateway.pb.h` | `c6b52b13e83a58897f73a88019e0f477ac9597c0d91f02614fda7233e96cdb47` |
| `xverse/xcom/v1/tool_gateway.pb.cc` | `1b230e4a7bacf66ecb69117987e71c26a9c81049fd153fa78374748aa42c82ee` |
| `xverse/xcom/v1/tool_gateway.grpc.pb.h` | `be80b0c71edf2a8d4a1f51fcbf9179352cd8b1643c2264ce933377a3a69e13c2` |
| `xverse/xcom/v1/tool_gateway.grpc.pb.cc` | `474b4f1c7b8fb05e66b47ac77e5b93af6589880d3da18f085d2edf552080bd4f` |
| `xverse/xcom/v1/gateway_liveness.pb.h` | `85dbb66d6cddf482de62070da7c90171d1950bb3b65bed31d5d3c23d49447a09` |
| `xverse/xcom/v1/gateway_liveness.pb.cc` | `c3b3841bd37527b46b100b12ee84d1090385dfa0d3d976aa7d64d8ad539e1cdc` |
| `xverse/xcom/v1/gateway_liveness.grpc.pb.h` | `9b595be70a61fce933bbd2c5c648de25ac18859ca3902db6fd977b0f470af423` |
| `xverse/xcom/v1/gateway_liveness.grpc.pb.cc` | `f44ed2fb72a59b25ad181e17aa93e194840ef708e6b7f2d2004dee1e47247bd4` |

| Field | Value |
| --- | --- |
| Admitted generators | `protoc` 3.12.4 (`libprotoc 3.12.4`), `grpc_cpp_plugin` 1.30.2, from the admitted linked gRPC prefix |
| Generation command | `cmake -E env LD_LIBRARY_PATH=<admitted prefix library directory> <protoc> -I<proto root> --cpp_out=<build tree>/t030-proto-gen --grpc_out=<build tree>/t030-proto-gen --plugin=protoc-gen-grpc=<grpc_cpp_plugin> xverse/xcom/v1/tool_gateway.proto xverse/xcom/v1/gateway_liveness.proto` (declared in `src/xverse/xcom/CMakeLists.txt`; runs offline with no ambient discovery) |
| Reproduction | Regenerated by the normal build at this candidate; digests match the retained T040 audit `gi` digests, so generation is reproducible. |

## 7. Dependency identity

| Field | Value |
| --- | --- |
| Admitted toolchain input | `XVERSE_XCOM_TOOLCHAIN` (linked gRPC prefix; resolved by name only) |
| Admitted package manifest | `XVERSE_XCOM_PACKAGE_MANIFEST`; SHA-256 `9879911b35058e8c8e0ee78ad5faef258c34d9e490b78b2121d6b9565c92945c` |
| Admitted test toolchain | `XVERSE_XCOM_T025_TEST_TOOLCHAIN` (GTest prefix) |
| ABI preservation | `GRPC_ASAN_SUPPRESSED=1` preserves the admitted unsanitized gRPC binary's POSIX mutex layout; compiler ASan/UBSan and leak/Boolean checks remain fully enabled, with no `-fno-sanitize` workaround |
| Dependency admission | `python3 scripts/xcom_dependency_preflight.py --verify-toolchain` → passed (`XCOM-BLD-I000`); no new third-party dependency, no network fetch |

## 8. Commands and outcomes at this successor assembly

| Command | Outcome |
| --- | --- |
| `cmake -S . -B build/gi -G Ninja -DCMAKE_BUILD_TYPE=Debug` | pass |
| `cmake --build build/gi -j4` | pass (157 targets) |
| `ctest --test-dir build/gi` | pass, 524/524 (522 predecessor + 2 successor cases) |
| `cmake -S . -B build/gs ... -fsanitize=address,undefined` and `cmake --build build/gs -j4` | pass (155 targets) |
| `ctest --test-dir build/gs -j2` (`ASAN_OPTIONS=detect_leaks=1:abort_on_error=1`, `UBSAN_OPTIONS=halt_on_error=1`) | pass, 524/524 |
| `python3 scripts/xcom_dependency_preflight.py --verify-toolchain` | pass |
| `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` | pass, outcome `pass` |
| `python3 engineering/check_xcom_traceability.py --report reports/xcom-queue/t038-traceability.json` | pass; regenerated at successor material digest `d8181788b9d42cb58f46126f1a9e7b922e6f57e6b0f76be29d85610b38ea0249` |
| `python3 engineering/check_xcom_traceability.py --verify reports/xcom-queue/t038-traceability.json` | pass; 322 requirements, 2780 resolved edges, 20 REF-002 IDs, no promoted ID, `working-tree` candidate state |
| `python3 engineering/check_xcom_traceability.py --self-test` | pass; positive fixture and NEG-01..NEG-07 all behave as declared |
| `python3 -m pytest -q` (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`) | pass, 150 tests + 24 subtests |
| `python3 scripts/validate_xcom_requirements_traceability.py --verify` and `--check-human` | pass |
| `xverse_xcom_grpc_generated_client_tests` under ASan/UBSan with `detect_leaks=1`, `halt_on_error=1` | pass, 10/10; adapter, generated glue, and client harness compiled with `-DGRPC_ASAN_SUPPRESSED=1 -fsanitize=address,undefined`, no `-fno-sanitize` site |

The trusted target-repository runner repeats the full normal and instrumented C++ suites, sanitizer
checks, Python tests, benchmark/trace verification, and negative checks from the pinned target
assembly. The local outcomes above are focused successor checks; they do not substitute for the
trusted delivery evidence, which is bound to the exact candidate revision when the successor commit
is prepared. No failed gate was replaced with a claim, and no validator was weakened.

## 9. Remaining limitations

- This repair addresses `T039-F07` and `T040-E01`–`T040-E03` only. It does not complete T039 or T040,
  does not perform the external T039/T040 inspection, and does not accept or merge the candidate.
- The watch identifier is a logical lifecycle association, not OS process authentication; clients must
  keep it private. Arbitrary host callbacks are not preempted by shutdown.
- The single-owned-lease repair deliberately declines a second allocation; a bounded multi-lease
  ownership set is out of scope and requires explicit design.
- The inherited T036 verifier report and the direct historical Phase 6 Doxyfile-immutability failure
  are preserved as historical evidence at their pinned identity; the direct Phase 6 script is not
  claimed as passing, and the authorized inherited replay keeps its separate, limited scope.
- The T037 Doxygen evidence report is bound to an earlier material digest and is not re-verified by
  this record; the strict documentation check is part of the trusted runner.
- No production-readiness, compatibility, parity, deployed-service, or certification claim is made.
