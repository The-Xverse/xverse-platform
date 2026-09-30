# T038 delivery envelope — T039 R4 lease-identity repair

This is the T039 R4 successor repair record for the T038 delivery envelope. It closes `T039-F08` on
the exact R3 candidate `cee2fc0581008002d1ac8269eb194848c8b719e8` (direct parent
`b15936781995ef188db30d7f99fc462701662b90`; accepted baseline
`a9c6e5d41e65625ed2b8c6f5a4457e10c6fcb090`). It preserves the `T039-F01`–`T039-F07` corrections and
the `T040-E01`–`T040-E03` reconciliation, and it keeps the R3 record as historical evidence. It does
not mark T039, T040, or T041 complete, accept, or merge anything, and `engineering/project.json` stays
at `task_id` `T038`.

Nothing in this record is a successor execution of the retained R3 inputs; the R4 evidence is
generated only for this successor assembly.

## 1. Authorization and identity boundary

| Field | Value |
| --- | --- |
| Task | T038 (capability 007, Phase 8 delivery envelope) |
| Accepted platform baseline | `a9c6e5d41e65625ed2b8c6f5a4457e10c6fcb090` |
| R3 candidate (reviewed, input) | `cee2fc0581008002d1ac8269eb194848c8b719e8` |
| R3 candidate parent | `b15936781995ef188db30d7f99fc462701662b90` |
| Repair owner | pinned DeepSeek Flash, high reasoning effort (Fabro stage policy, no fallback) |
| External T039/T040 inspection | separate workflow; not performed here |
| T041 user acceptance and main merge | separate gates; not authorized or performed here |

## 2. T039-F08 repair — non-aliasing allocation identity

**Finding (major).** The public lease identifier encoded only the endpoint generation, and release
compared only that reused identifier before releasing the session's currently stored key. A legitimate
session could therefore acquire `svc.alpha` at generation 3, release it, acquire `svc.beta` at the
same generation 3, and then replay the first release identity, which released the second allocation's
current registry entry. This is a correctness/lifecycle failure within one session; no cross-process
authentication bypass is claimed.

**Root cause and repair.** `GatewaySession` now keeps a session-scoped, strictly monotonic allocation
sequence. Each successful allocation consumes the next sequence value, and both the public identity and
the registry owner identity are derived from it, so a released identity can never name a later
allocation of any endpoint in the same session. The candidate allocation is computed locally and the
sequence advances only on `LeaseStatus::Ok`, so a declined acquisition consumes nothing. The bounded
sequence is never wrapped: at the maximum value the acquisition is declined with `LEASE_CONFLICT`
before the registry is touched, leaving no lease, registry entry, or consumed sequence value behind.

| File | Change |
| --- | --- |
| `src/xverse/xcom/src/tool_gateway.cpp` | `AcquireLease` computes `allocation = lease_sequence_ + 1U`, passes it to `leases->acquire` as the owner identity, and only on `Ok` advances `lease_sequence_ = allocation` and sets the public `lease_id_` to `gw-lease-<generation>-<allocation>`. A bounded-space exhaustion guard declines with diagnostic `gw.lease.exhausted` before any registry call. `ReleaseLease` documents that the exact held allocation identity is required. |
| `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` | `AcquireLease`/`ReleaseLease` documentation states the fresh, non-aliasing, never-wrapping allocation-identity contract and the exhaustion decline; the new `lease_sequence_` member is declared. |

The generation-bound registry delegation, exact-session check, the T039-F07 single-owned-lease
boundary with its retained original identity on decline, `LEASE_CONFLICT` on a further acquisition,
and the disconnect/quarantine cleanup are unchanged. The ten `ToolGateway` methods and the separate
`GatewayLiveness` contract are unchanged; no API, protocol, or dependency was added.

**Requirement IDs:** `T031-SR-012` (exclusive generation-bound lease delegation; no ambiguous
ownership) and `T031-SR-013` (disconnect/idle cleanup of validation-owned resources).

**Named regressions (generated clients).** `tests/xcom/tool_gateway/grpc_generated_client_tests.cpp`
(`xverse_xcom_grpc_generated_client_tests`, label `t030-grpc`):

| Case | Assertion |
| --- | --- |
| `XcomGrpcGeneratedClient.StaleReleaseIdentityDoesNotReleaseLaterAllocation` | After releasing `svc.alpha` at generation 3 and acquiring a different endpoint `svc.beta` at the same generation, the reacquired identity differs, replaying the released identity is rejected, the authoritative registry stays at one active lease, `QuerySession` still reports the new identity, and the new allocation's own identity releases it. |
| `XcomGrpcGeneratedClient.RepeatedAllocationOfSameEndpointGetsFreshIdentity` | Repeated allocation of `svc.alpha` at the same generation after an explicit release receives a fresh identity; the released identity is rejected and the current identity releases the entry. |

The shared fixture `tests/xcom/tool_gateway/gateway_support.hpp` is byte-identical, so the immutable
external probe fixture remains valid.

**Negative self-check.** With only the public identity temporarily reverted to the generation-only
form (single-owned-lease guard and allocation-based registry identity intact), the two new cases fail:
the stale replay is accepted instead of rejected and tears down the current allocation, so the
authoritative registry active count drops to zero, `QuerySession` no longer reports a held lease, and
the new allocation's own identity is then rejected (`LEASE_QUARANTINED`, `state=3`). With the repair
restored both cases pass and all twelve generated-client cases pass. This demonstrates the regressions
detect the F08 defect rather than rejecting all acquisitions.

**External closure probe.** The immutable independent probe and runner under
`automation/reviews/t039-r3-independent-review-20260930/` (probe source SHA-256
`3af625160481f11a5471d2c52f5ce5a992006f1c23d3ab7d75814ada7734579b`) were recompiled against this
assembly and executed per process by `automation/check_xcom_t039_r4.py` (fixture SHA-256
`2559ead663bb0c25d5190bc949a3fb18b6096a2e49c90512e8a81ba3fa1a3aa5` unchanged). All six modes —
`two-leases`, `identity-release`, `stale-release`, `cancel-queued`, `deadline-queued`, and
`unread-shutdown` — report `verdict=pass` and actual child process exit `0` in both the normal target
`build/f8u` and the admitted-instrumentation target `build/f8s`, as measured by the actual child
process exit status rather than the runner's own exit code. The former failing `stale-release` mode
now reports `acquire svc.alpha generation=3 id=gw-lease-3-1`, `release id=gw-lease-3-1 state=2
active=0`, `acquire svc.beta generation=3 id=gw-lease-3-2 active=1`, a rejected stale replay
`release id=gw-lease-3-1 state=3 active=1 released=0`, and a successful release by the new identity
`release id=gw-lease-3-2 state=2 active=0`.

**Focused outcome.** The trusted gates build the normal target `build/f8u` (Debug) and the
admitted-instrumentation target `build/f8s` (single admitted `-fsanitize=address,undefined` compile
flag, no `-fno-sanitize` exclusion site). `xverse_xcom_grpc_generated_client_tests` reports 12/12 in
each build; `ctest` reports 526/526 in each (524 predecessor cases plus the two R4 generated-client
cases). The instrumented run executes under `detect_leaks=1:abort_on_error=1` and
`halt_on_error=1` undefined-behavior settings. A separate `XVERSE_XCOM_SANITIZERS=address,undefined`
build (`build/gs`) also passes 526/526, but because that route emits split `-fsanitize=address`
`-fsanitize=undefined` flags it is not the admitted combined-flag build accepted by the closure
helper and is not used as closure evidence.

## 3. Preserved findings and T040 reconciliation

- **F01–F07 preserved.** The R3 corrections are untouched: sanitizer instrumentation with
  `GRPC_ASAN_SUPPRESSED=1` and no `-fno-sanitize` site (F01), the single-matching-watch logical-owner
  boundary (F02), post-commit reconciliation and pre-dispatch transport probes (F03), signed deadline
  saturation (F04), explicit transport status for rejected observation reads (F05), live-watch
  shutdown (F06), and the single-owned-lease boundary with the retained original identity (F07). The
  complete normal and instrumented C++ suites and all six closure modes pass for this assembly.
- **T040-E01 preserved.** The refreshed trace graph resolves 322 requirements and 2780 edges with no
  stale hash pin and no trusted trace gap.
- **T040-E02 preserved.** The benchmark and traceability reports are regenerated at this successor
  material digest with unchanged validators, same-revision/direct-child identity rules, stale-input
  rejection, and all negative checks. The retained historical failures keep their original identity
  and are not relabelled as current.
- **T040-E03 preserved.** The component-scoped successor dispositions for the linked gateway remain
  accurate; the separate T032 synthetic client keeps its framed local-IPC transport and its own
  limitation. No allocated or deferred REF-002 target is promoted.

## 4. Work-product relationships refreshed

| Work product | Change |
| --- | --- |
| `engineering/requirements/T031-SR-012.json` | Additive `successor_disposition` records the F08 identity clarification; requirement text and revision are unchanged. |
| `engineering/unit-specifications/T031-SR-012-U.json` | Two successor unit cases name the new generated-client regressions and their assertions. |
| `docs/engineering/xcom/t031/unit-specifications.md` | Additive T039 R4 addendum records the successor cases and the allocation-identity boundary; no `T31-TS-###` case is renamed, removed, or weakened. |
| `docs/engineering/xcom/t031/detailed-design.md` | Additive T039 R4 successor disposition records the exact-allocation release validation and the session-scoped, never-wrapping allocation identity, and states that the R3 lease/session/registry decisions are unchanged. |
| `docs/engineering/xcom/t039/transport-repair.md` | Client-facing behavior now documents the allocation-identity semantics, the exact-identity release, the exhaustion decline, and the new regressions. |
| `engineering/trace/links.json` | The affected `implemented_by` pins for `tool_gateway.cpp` (6), `tool_gateway.hpp` (6), the generated-client test source (10), and `docs/engineering/xcom/t039/transport-repair.md` (4) were refreshed to the exact successor file digests; no edge was removed and no predecessor scope was weakened. |

Client guidance is maintained: the lease identity is an opaque logical lease-lifecycle association
within one session, clients must not synthesize, guess, or reuse it after the named lease is released,
and they must keep the watch identifier private. The durable `QuerySession` lookup still reconciles a
committed outcome, and the absence of a scheduled intent remains explicitly uncertain and does not
authorize a retry.

## 5. Generated-service provenance (both generated services)

The committed `.proto` files remain the source of truth; both generated services are produced in one
build-tree generation step with the admitted generators. The input digests are unchanged, and the
normal and instrumented build-tree outputs are byte-identical to each other and to the retained R3
record, so generation remains reproducible.

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

## 6. Dependency identity

| Field | Value |
| --- | --- |
| Admitted toolchain input | `XVERSE_XCOM_TOOLCHAIN` (linked gRPC prefix; resolved by name only) |
| Admitted package manifest | `XVERSE_XCOM_PACKAGE_MANIFEST`; SHA-256 `9879911b35058e8c8e0ee78ad5faef258c34d9e490b78b2121d6b9565c92945c` |
| Admitted test toolchain | `XVERSE_XCOM_T025_TEST_TOOLCHAIN` (GTest prefix) |
| ABI preservation | `GRPC_ASAN_SUPPRESSED=1` preserves the admitted unsanitized gRPC binary's POSIX mutex layout; compiler ASan/UBSan and leak/Boolean checks remain fully enabled, with no `-fno-sanitize` workaround |
| Dependency admission | `python3 scripts/xcom_dependency_preflight.py --verify-toolchain` passed; no new third-party dependency, no network fetch |

## 7. Commands and outcomes at this successor assembly

| Command | Outcome |
| --- | --- |
| `python3 automation/xcom_t039_r4_gate.py verify T038 <R3 candidate>` | pass; configures and builds the normal target `build/f8u`, `ctest --test-dir build/f8u` 526/526, and the six immutable closure probes with actual process exit `0` |
| `python3 automation/run_xcom_t039_r4_tests.py unit` | pass (the same normal-target command the gate runs) |
| `python3 automation/run_xcom_t039_r4_tests.py sanitizer` | pass; admitted-instrumentation `build/f8s` (`-fsanitize=address,undefined`, no `-fno-sanitize`), `ctest --test-dir build/f8s` 526/526, six closure probes exit `0` under leak detection and halt-on-error undefined behavior |
| `python3 automation/check_xcom_t039_r4.py --build build/f8u` and `--build build/f8s` | pass; `6 independent successor closure probes passed`; `verdict=pass` for all six modes |
| `xverse_xcom_grpc_generated_client_tests` (normal `build/f8u` and instrumented `build/f8s`) | pass, 12/12 |
| `doxygen build/doxygen-r4/Doxyfile.r4` (`WARN_AS_ERROR = YES`) | pass |
| `python3 scripts/xcom_dependency_preflight.py --verify-toolchain` | pass |
| `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` | pass, outcome `pass`; disabled-tap latency regression 1.3927%, throughput regression 1.3736%, within the 2% local threshold |
| `python3 engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json` | pass, `working-tree` candidate state |
| `python3 engineering/check_xcom_traceability.py --report reports/xcom-queue/t038-traceability.json` | pass; material digest `4f703f5561126aefec4081a18064b759732b273bbfe7c657f941e047873cd3bd` |
| `python3 engineering/check_xcom_traceability.py --verify reports/xcom-queue/t038-traceability.json` | pass; 322 requirements, 2780 resolved edges, 20 REF-002 IDs, no promoted ID, `working-tree` candidate state |
| `python3 engineering/check_xcom_traceability.py --self-test` | pass; positive fixture and NEG-01…NEG-07 behave as declared |
| `python3 scripts/validate_xcom_requirements_traceability.py --verify` and `--check-human` | pass |
| `python3 -m pytest -q` (plugin autoload disabled) | pass, 150 tests and 24 subtests |

The trusted target-repository runner repeats the full normal and instrumented C++ suites, all six
external closure modes, sanitizer checks, the Python suite, benchmark/trace verification, and the
documentation/static/conformance checks from the pinned target assembly. The local outcomes above are
focused successor checks and do not substitute for that trusted delivery evidence, which is bound to
the exact candidate revision when the successor commit is prepared. No failed gate was replaced with
a claim and no validator was weakened.

## 8. Remaining limitations

- This repair addresses `T039-F08` only. It does not complete T039 or T040, does not perform the
  external T039/T040 inspection, and does not accept or merge the candidate.
- The lease identity is a logical session-scoped lifecycle association, not an OS process identity or
  an authorization primitive; the exact permit and host permissions remain required.
- The watch identifier is a logical lifecycle association, not OS process authentication; clients
  must keep it private. Arbitrary host callbacks are not preempted by shutdown.
- The single-owned-lease boundary deliberately declines a second concurrent allocation; a bounded
  multi-lease ownership set is out of scope and requires its own design.
- The inherited T036 verifier report and the direct historical Phase 6 Doxyfile-immutability failure
  are preserved as historical evidence at their pinned identity; the authorized inherited replay keeps
  its separate, limited scope.
- The repository-wide warning-as-error Doxygen route is clean for this assembly. The separate strict
  C++-scoped T037 route reports pre-existing mandatory-file-block gaps in the unchanged
  `tool_gateway_grpc.hpp`/`tool_gateway_grpc.cpp` adapter files; this R4 repair did not touch those
  files and does not promote the retained T037 report as current evidence.
- No production-readiness, compatibility, parity, deployed-service, or certification claim is made.
