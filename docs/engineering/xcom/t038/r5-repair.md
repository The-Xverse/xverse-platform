# T038 delivery envelope — T039 R5 strict-documentation and evidence repair

This is the T039 R5 successor repair record for the T038 delivery envelope. It closes `T039-F09` on the
exact R4 candidate `67e38e5974f2dd827b4d7fb902343c347341c796` (direct parent
`cee2fc0581008002d1ac8269eb194848c8b719e8`; accepted platform main
`a9c6e5d41e65625ed2b8c6f5a4457e10c6fcb090`). It preserves the `T039-F01`–`T039-F08` corrections, the
`T040-E01`–`T040-E03` reconciliation, and the R3/R4 records as historical evidence at their original
identities. It does not mark T039, T040, or T041 complete, accept, or merge anything, and
`engineering/project.json` stays at `task_id` `T038`.

Nothing in this record is a successor execution of the retained R3/R4 inputs; the R5 evidence is generated
only for this successor assembly. Historical success is not current execution.

**Validation-repair successor (baseline `88cf30b16adbe4b48c5c79935dd21af605480c98`).** A later trusted
validation of the R5 successor commit `88cf30b16adbe4b48c5c79935dd21af605480c98` — the direct child of the
R5 candidate `67e38e5974f2dd827b4d7fb902343c347341c796` recorded below — rejected
`docs/engineering/xcom/t038/internal-review.json` with `PUBLIC_SAFETY_INVALID` because it retained two
absolute host paths. Section 12 records that deterministic failure, the exact scope of this successor
repair, and the regenerated evidence. Sections 1–11 remain the historical R5 record at their original
identity and are not relabelled as current.

## 1. Authorization and identity boundary

| Field | Value |
| --- | --- |
| Task | T038 (capability 007, Phase 8 delivery envelope) |
| Accepted platform baseline | `a9c6e5d41e65625ed2b8c6f5a4457e10c6fcb090` |
| Admitted R4 candidate (reviewed, input) | `67e38e5974f2dd827b4d7fb902343c347341c796` |
| Admitted R4 candidate parent | `cee2fc0581008002d1ac8269eb194848c8b719e8` |
| Repair owner | pinned DeepSeek Flash, high reasoning effort (Fabro stage policy, no fallback) |
| External T039/T040 inspection | separate workflow; not performed here |
| T041 user acceptance and main merge | separate gates; not authorized or performed here |

## 2. T039-F09 repair — owned gateway gRPC adapter documentation

**Finding (major).** `src/xverse/xcom/include/xverse/xcom/tool_gateway_grpc.hpp` and
`src/xverse/xcom/src/tool_gateway_grpc.cpp` carried no mandatory Doxygen file block, so the required strict
owned-C++ route failed:

```text
$ python3 scripts/check_doxygen.py --strict-cpp
documentation validation failed:
- src/xverse/xcom/include/xverse/xcom/tool_gateway_grpc.hpp: missing mandatory file block 'file'
- src/xverse/xcom/include/xverse/xcom/tool_gateway_grpc.hpp: missing mandatory file block 'brief'
- src/xverse/xcom/include/xverse/xcom/tool_gateway_grpc.hpp: missing mandatory file block 'ingroup'
- src/xverse/xcom/src/tool_gateway_grpc.cpp: missing mandatory file block 'file'
- src/xverse/xcom/src/tool_gateway_grpc.cpp: missing mandatory file block 'brief'
- src/xverse/xcom/src/tool_gateway_grpc.cpp: missing mandatory file block 'ingroup'
```

**Provenance.** The adapter files were introduced in accepted baseline `a9c6e5d` and were untouched by the
R3/R4 repairs. The gap is an inherited current-delivery documentation gap classified by the R4 independent
review, not an R4 regression.

**Repair (documentation comments).** Both files now carry the mandatory `@file`/`@brief`/`@ingroup` file
block with `@details`, `@ownership`, `@lifetime`, `@thread_safety`, `@failure`, and traceability clauses.
Every public declaration of `GatewayGrpcService` and `GatewayGrpcServer` carries `@brief`, `@param`, and
`@return` documentation plus the ownership, lifetime, thread-safety, failure, and watch/session semantics.
The task-visible `XCOM_GRPC_UNARY` macro is documented with `@brief`/`@param`.

**Contract correction (comments only).** The R5 independent review recorded that two new public `@return`
clauses and one `@lifetime` clause were inaccurate against the implementation. They are corrected here and no
other comment is affected:

- `WatchSession` now documents the actual single exit: the call holds after the ready frame is written until
  the client cancels or the watch is marked failed, and it returns `CANCELLED` once the watch closes —
  including when that ready frame cannot be delivered. `ALREADY_EXISTS`/`FAILED_PRECONDITION`/`UNAVAILABLE`
  reject a second, terminal, or unidentifiable watch.
- `AcquireLease` now documents that the unary call returns `OK` whenever it is admitted and watched and that
  the acquisition outcome — including `LEASE_CONFLICT` when a lease is already held or the allocation space
  is exhausted — is carried by `AcquireLeaseResponse.state`, not by the gRPC status.
- The `GatewayGrpcService` `@lifetime` clause no longer requires the configuration to outlive the service:
  the caller's `GatewayConfig` is copied by value, while the referenced `GatewaySession` must outlive it.

**Declaration clarification (explicit, inert).** Per-parameter `@param` clauses require parameter
identifiers: Doxygen binds `@param` to a name and, under `WARN_NO_PARAMDOC = YES`, warns when a named
parameter is undocumented, while an unnamed parameter carries no `@param` binding. The adapter overrides were
previously declared with unnamed parameters, so supplying the identifiers is the minimal change that lets the
accepted repository documentation convention (named parameters with `@param`, as used throughout the other
owned `src/xverse/xcom` headers) apply to the adapter. This is the sole deviation from the comments-only C++
boundary, and it is recorded here explicitly as an intentional, bounded, inert declaration clarification:
parameter names are not part of a function's type or mangled name, so no function type, return type,
`override` relationship, ABI, compiled statement, control flow, test, CMake, proto, or runtime behavior
changed.

**Focused outcome.**

```text
$ python3 scripts/check_doxygen.py --strict-cpp
strict C++ documentation passed: 35 indexed files, 0 warnings, 0 coverage gaps
```

**External fixture preserved.** `tests/xcom/tool_gateway/gateway_support.hpp` is byte-identical
(SHA-256 `2559ead663bb0c25d5190bc949a3fb18b6096a2e49c90512e8a81ba3fa1a3aa5`), so the immutable external
closure fixture remains valid.

## 3. Documentation checker metadata readmission

`scripts/check_doxygen.py` previously hard-coded the old T037 baseline `8757a79d4e6b2630124d774fcba2a55d6342a879`
and the superseded offline dependency envelope. Only its two top-level metadata assignments changed, and
only to the admitted values: `BASELINE_REVISION = "67e38e5974f2dd827b4d7fb902343c347341c796"` and
`ADMITTED_INPUTS` resolved to the admitted linked-gRPC prefix, package manifest, and GTest prefix. A local
AST comparison against `git show 67e38e5:scripts/check_doxygen.py` (the same comparison the trusted host
performs) confirms that every other statement, the CLI, `MATERIAL_GLOBS`, `MATERIAL_EXCLUDES`,
`STRICT_CPP_EXCLUSIONS`, and the strict flags are unchanged; only those two assignments differ. Checker
logic, material scope, exclusions, negative checks, and fail-closed behavior are not weakened.

The refreshed report is bound to the admitted baseline and the admitted manifest SHA-256
`9879911b35058e8c8e0ee78ad5faef258c34d9e490b78b2121d6b9565c92945c`.

For the validation-repair successor the metadata was readmitted once more: `BASELINE_REVISION` is now
`88cf30b16adbe4b48c5c79935dd21af605480c98`, while `ADMITTED_INPUTS` already resolved to the admitted
linked-gRPC prefix, package manifest, and GTest prefix and is unchanged. The same AST comparison confirms
that only those two top-level assignments may differ; see §12.

## 4. Execution locations and provenance (R4 correction and R5 statement)

The R4 record's blanket statement that all trusted measures ran from the target checkout is inaccurate.
Faithfully recorded locations:

| Revision | Integration measure | Source measures (unit, static, validation/documentation, sanitizer, conformance) |
| --- | --- | --- |
| R4 | assembled and executed in the isolated target `xt39r4i` | sanitizer and validation/documentation executed in the source checkout `xt39r4q` |
| R5 | the integration measure assembles and executes in the declared isolated target `xt39r5i` | unit, static, validation/documentation, sanitizer, and conformance run in the source worker checkout `xt39r5q` |

These rows are declared measure-location assignments for the successor workflow's trusted gates. Except for
the R5 integration measure, which is assembled and executed in the isolated target, every R5 measure runs in
the source worker checkout; only the integration measure assembles a target. This section does not claim that
the not-yet-run trusted measures have executed. Only the checks listed in §6.1 were executed in this repair,
in the source worker checkout.

The isolated targets and the source worker checkout are directories named `xt39r4i`, `xt39r4q`, `xt39r5i`,
and `xt39r5q` under the worker temporary root; the leading host temporary-root prefix is intentionally
omitted so this retained artifact stays public-safe. Historical success is not current execution: the R4
record is evidence only for the R4 candidate, and the R5 outcomes in §5 and §6 are the current results for
the admitted R4 baseline with the R5 repair.

## 5. Regenerated exact-candidate evidence

All three repository-owned reports were regenerated with their existing scripts at `HEAD == baseline`
(`67e38e5`), the measured working-tree successor. Each binds `baseline_revision` plus the sorted
material-input inventory, the material digest, and per-file SHA-256 hashes, and each accepts either
`HEAD == baseline_revision` or `HEAD` as the direct child of `baseline_revision` and rejects every other
revision.

| Report | Command | Material inputs | Material digest |
| --- | --- | --- | --- |
| `reports/xcom-queue/t037-doxygen.json` | `python3 scripts/check_doxygen.py --report reports/xcom-queue/t037-doxygen.json` | 82 | `087b71b5001d245513a0dd85be96db00e3375588087bb7ab67c54656a29ca9f0` |
| `reports/xcom-queue/t036-benchmark.json` | `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` | 53 | `1618336b055249e41a2c96f5bdda077e39d3c9d6b72f8e7afdb2ca06ead93a19` |
| `reports/xcom-queue/t038-traceability.json` | `python3 engineering/check_xcom_traceability.py --report reports/xcom-queue/t038-traceability.json` | 54 | `166fd62a8849fbed26d92edaaf32726800d463af342298f4b794ab10b43966f3` |

T037 report result: repository route exit `0` with `0` warnings and `173` indexed files; strict C++ route
exit `0`, `35` indexed files, `0` warnings, `0` coverage gaps; both generated HTML/XML indices present;
`warnings.log` empty. The admitted-input identity records the linked-gRPC prefix, the package manifest
(SHA-256 `9879911b…`), and the GTest prefix by name only.

T036 report result: `outcome` `pass`, disabled-tap latency regression `1.315350741034571%` and throughput
regression `1.2982738858563048%`, within the accepted 2% threshold.

T038 report result: `322` requirements, `2780` resolved edges, `0` unresolved, `20` REF-002 IDs with
`promoted` empty, public-safety verdict `pass`.

The trace `implemented_by` pins for the two changed adapter files, the documentation checker, and
`docs/engineering/xcom/t037/detailed-design.md` were refreshed to the exact successor file digests; every
other pin still resolves to the exact bytes it pins, no edge was removed, and no predecessor scope was
weakened.

This section records the R5 generation at `HEAD == baseline` (`67e38e5`). Section 12 records the
validation-repair regeneration at the successor baseline `88cf30b`; the R5 digests above remain evidence
only for the R5 candidate identity and are not relabelled as current.

## 6. Commands and evidence provenance

### 6.1 Executed in this repair (source worker checkout `xt39r5q`)

| Command | Outcome |
| --- | --- |
| `python3 scripts/check_doxygen.py --strict-cpp` | pass; exit `0`, `35` indexed files, `0` warnings, `0` coverage gaps |
| `python3 scripts/check_doxygen.py --report reports/xcom-queue/t037-doxygen.json` | pass; exit `0`; both routes exit `0`, `0` warnings, digest `087b71b5…` |
| `python3 ${XVERSE_FABRIC_ROOT}/automation/check_xcom_t039_r5_doxygen.py` | pass; `82` material inputs, digest `087b71b5…`, six negative evidence probes, synthetic omission self-test passed |
| `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` | pass; digest `1618336b…`, latency `1.315350741034571%`, throughput `1.2982738858563048%` |
| `python3 engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json` | pass; working-tree candidate state |
| `python3 engineering/check_xcom_traceability.py --report reports/xcom-queue/t038-traceability.json` | pass; digest `166fd62a…` |
| `python3 engineering/check_xcom_traceability.py --verify reports/xcom-queue/t038-traceability.json` | pass; `322` requirements, `2780` resolved edges, `20` REF-002 IDs, no promoted ID |
| `python3 engineering/check_xcom_traceability.py --self-test` | pass; positive fixture and NEG-01…NEG-07 behave as declared |
| `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_t039_r5_tests.py unit` | pass; normal `build/f8u`, `ctest` `100% tests passed, 0 tests failed out of 526`, six closure probes exit `0` |

### 6.2 Executed by the deterministic workflow gates on this candidate

The `verify` gate re-runs the strict Doxygen route, the current-evidence verifier, and the unit suite in the
source worker checkout; the `closure_gate` re-runs the six independent immutable closure probes in the
source worker checkout. These gates execute after this repair, so their records belong to the successor
candidate rather than to any retained R4 run.

### 6.3 Executed by the trusted successor gates (not asserted as complete here)

The successor workflow measures unit, static analysis, integration, validation, sanitizer, and conformance
after packaging. Only the integration measure assembles and executes in the isolated target `xt39r5i`; the
other five measures run in the source worker checkout `xt39r5q`. This record declares their locations and
does not claim their outcomes.

## 7. Preserved findings and T040 reconciliation

- **F01–F08 preserved.** The R3/R4 corrections are untouched: sanitizer instrumentation with
  `GRPC_ASAN_SUPPRESSED=1` and no `-fno-sanitize` site (F01), the single-matching-watch logical-owner
  boundary (F02), post-commit reconciliation and pre-dispatch transport probes (F03), signed deadline
  saturation (F04), explicit transport status for rejected observation reads (F05), live-watch shutdown
  (F06), the single-owned-lease boundary with the retained original identity (F07), and the session-scoped
  strictly monotonic non-aliasing allocation identity with the `gw.lease.exhausted` exhaustion decline
  (F08). `src/xverse/xcom/src/tool_gateway.cpp`, `tests/`, `proto/`, and the CMake inputs are byte-unchanged,
  and the executed unit suite and all six immutable closure modes pass for this assembly. Exhaustion
  reasoning remains source inspection; no runtime test drives the counter to its maximum.
- **T040-E01 preserved.** The refreshed trace graph resolves `322` requirements and `2780` edges with no
  stale hash pin and no trusted trace gap.
- **T040-E02 preserved.** The benchmark and traceability reports are regenerated at this successor material
  digest with unchanged validators, same-revision/direct-child identity rules, stale-input rejection, and all
  negative checks. The retained historical failures keep their original identity and are not relabelled as
  current.
- **T040-E03 preserved.** The component-scoped successor dispositions for the linked gateway remain
  accurate; the separate T032 synthetic client keeps its framed local-IPC transport and its own limitation.
  No allocated or deferred REF-002 target is promoted.

The named regressions `XcomGrpcGeneratedClient.StaleReleaseIdentityDoesNotReleaseLaterAllocation` and
`XcomGrpcGeneratedClient.RepeatedAllocationOfSameEndpointGetsFreshIdentity` remain covered by the unchanged
generated-client suite together with the other generated-client cases; the monotonic allocation identity,
abrupt cleanup, queued cancellation/deadline outcomes, and the bounded unread-watch shutdown probes remain
green.

## 8. Generated-service provenance

The committed `.proto` inputs are unchanged and the generation is unchanged, so both generated services
remain reproducible:

| Generated service | Input | Input SHA-256 |
| --- | --- | --- |
| `ToolGateway` | `proto/xverse/xcom/v1/tool_gateway.proto` | `90e56f82d1251f04732dfaa5003597dfc43b7cfe3212e33b5507cd9e04cf289f` |
| `GatewayLiveness` | `proto/xverse/xcom/v1/gateway_liveness.proto` | `a649602b5de394da89eebdd1135f67583ff76a24c11ad86f9a1060f25f1da527` |

The generated build-tree outputs remain the R4 record's eight hashes, and the normal and instrumented build
trees remain byte-identical to each other and to the retained R4 record.

## 9. Dependency identity

| Field | Value |
| --- | --- |
| `XVERSE_XCOM_TOOLCHAIN` | admitted linked-gRPC prefix, resolved by name only |
| `XVERSE_XCOM_PACKAGE_MANIFEST` | SHA-256 `9879911b35058e8c8e0ee78ad5faef258c34d9e490b78b2121d6b9565c92945c` |
| `XVERSE_XCOM_T025_TEST_TOOLCHAIN` | admitted GTest prefix, resolved by name only |
| ABI preservation | `GRPC_ASAN_SUPPRESSED=1` preserves the admitted unsanitized gRPC binary's POSIX mutex layout; compiler ASan/UBSan, leak, and Boolean instrumentation remain fully enabled, with no `-fno-sanitize` workaround |
| Dependency admission | no new third-party dependency and no network fetch |

## 10. Work-product relationships refreshed

| Work product | Change |
| --- | --- |
| `engineering/requirements/T037-SR-001.json`, `T037-SR-002.json` | Additive `successor_disposition` records the F09 adapter-documentation completion; requirement text and revision are unchanged. |
| `docs/engineering/xcom/t037/detailed-design.md` | Additive §5.1 records the R5 successor completion of the adapter file blocks, declarations, and the reconciled return/lifetime contracts; the original obligations are unchanged. |
| `docs/engineering/xcom/t037/implementation.md` | Additive §11 records the R5 successor commands, outcome, and provenance; the historical sections retain their original measured identity. |
| `engineering/trace/links.json` | The affected `implemented_by` pins for `tool_gateway_grpc.hpp`, `tool_gateway_grpc.cpp`, `scripts/check_doxygen.py`, and `docs/engineering/xcom/t037/detailed-design.md` were refreshed to the exact successor file digests; no edge was removed and no predecessor scope was weakened. |

Client guidance is maintained: the lease identity is an opaque, session-scoped logical lifecycle
association; clients must not synthesize, guess, or reuse it after release, and must keep the watch
identifier private. The absence of a scheduled intent remains explicitly uncertain and does not authorize a
retry.

## 11. Remaining limitations

- This repair addresses `T039-F09` only. It does not complete T039 or T040, does not perform the external
  T039/T040 inspection, and does not accept or merge the candidate.
- The adapter change adds parameter identifiers to previously unnamed declarations; it changes no compiled
  type, statement, or behavior and is recorded above as an explicit, inert declaration clarification.
- The lease identity is a logical session-scoped lifecycle association, not an OS process identity or an
  authorization primitive; the exact permit and host permissions remain required.
- The watch identifier is a logical lifecycle association, not OS process authentication; clients must keep
  it private, and arbitrary host callbacks are not preempted by shutdown.
- The strict declaration-level route remains scoped to the owned `src/xverse/xcom` C++ inputs; the
  repository-wide route keeps `WARN_IF_UNDOCUMENTED = NO`/`WARN_NO_PARAMDOC = NO` because it also covers
  out-of-scope Python and test inputs (`T037-GAP-02`), and generated/system headers remain deferred to the
  admitted exclusion list (`T037-GAP-03`).
- The inherited global Python docstring coverage findings remain the `T037-OPEN-06` limitation, and the
  exploratory global `--self-test --coverage-only` route is not reported as passing.
- No production-readiness, compatibility, parity, deployed-service, or certification claim is made, and no
  REF-002 target is promoted.

## 12. Validation-repair successor — public-safety failure and re-baselining

**Validation failure (deterministic).** The R5 successor commit
`88cf30b16adbe4b48c5c79935dd21af605480c98` had already passed DeepSeek review, packaging, unit, static
analysis, and target-repository integration, then failed trusted validation:
`engineering/check_xcom_traceability.py --verify` reported `PUBLIC_SAFETY_INVALID` (exit 5):

```text
T038 traceability validation FAILED: PUBLIC_SAFETY_INVALID (exit 5)
- [PUBLIC_SAFETY_INVALID] docs/engineering/xcom/t038/internal-review.json matches excluded content: absolute host path
```

Two absolute host paths were retained in that review record — a host checker path in check `IRV-03` and a
host temporary-checkout path in check `IRV-10`. The reviewed source and evidence were already committed in
the baseline, so the defect was documentation/evidence only: no source, test, proto, CMake, generated
service, or runtime behavior changed.

**Repair scope (this successor).**

- `docs/engineering/xcom/t038/internal-review.json` now cites only repository-relative paths and public-safe
  descriptions; the two host paths are replaced by repository-relative wording while the record keeps its
  original R5 review identity. The successor record itself is written by the separate reviewer stage and
  must keep the same rule: repository-relative references only, never a temporary or host absolute path.
- `scripts/check_doxygen.py` was readmitted to the new baseline: only the top-level `BASELINE_REVISION`
  assignment changed (`67e38e5974f2dd827b4d7fb902343c347341c796` →
  `88cf30b16adbe4b48c5c79935dd21af605480c98`); `ADMITTED_INPUTS` was already the admitted linked-gRPC
  prefix, package manifest, and GTest prefix and is unchanged. `MATERIAL_GLOBS`, `MATERIAL_EXCLUDES`,
  `STRICT_CPP_EXCLUSIONS`, the strict overrides, the fail-closed checks, the negative checks, and the CLI are
  byte-unchanged.
- The `implemented_by` pins for `scripts/check_doxygen.py` in `engineering/trace/links.json` were refreshed
  to the successor digest `31b5e4dd751d5a74656b1b6165dda37377e7f0f13984433b97bbb8e6814e9f36`; no edge was
  removed and no predecessor scope was weakened.

**Regenerated evidence at baseline `88cf30b`.** All three repository-owned reports were regenerated with
their existing scripts at `HEAD == baseline` (`88cf30b`), the measured working-tree successor:

| Report | Material inputs | Material digest |
| --- | --- | --- |
| `reports/xcom-queue/t037-doxygen.json` | 82 | `fec3fce9d41caffb2515252efce1905db4b7a57259f6e0c79120d2ce5d6969f3` |
| `reports/xcom-queue/t036-benchmark.json` | 53 | `1ea295ba19e274471c8297394ac6ad08d517eaf441280513571ec18953b91709` |
| `reports/xcom-queue/t038-traceability.json` | 54 | `de75b90649a095240319cb5fad0fac45134e7b3e33f29cdfa3a18eef5a3a0168` |

T037 result: repository route exit `0` with `0` warnings and `173` indexed files; strict C++ route exit `0`
with `35` indexed files, `0` warnings, and `0` coverage gaps. The trusted host Doxygen evidence verifier
accepts the regenerated report — `82` material inputs, digest `fec3fce9…`, six negative evidence probes, and
the synthetic omission self-test passed.

T036 result: `outcome` `pass`, disabled-tap latency regression `-0.11317691944101593%` and throughput
regression `-0.1133051547246966%`, within the accepted 2% threshold.

T038 result: `322` requirements, `2780` resolved edges, `0` unresolved, `20` REF-002 IDs with `promoted`
empty, and public-safety verdict `pass`.

**Faithful execution provenance.** The T037/T036/T038 evidence above was generated and verified in the
source worker checkout at baseline `88cf30b`; the `verify` and `closure_gate` nodes re-execute the strict
documentation route, the current-evidence verifier, and the unit suite on this successor, and the six
immutable closure probes are re-run there. The trusted integration measure is a downstream successor gate
that assembles and executes in the isolated target-repository worktree declared by the integration policy
and named by its repository-relative target id only; it is neither executed nor asserted here. Host checker
commands are named through the `${XVERSE_FABRIC_ROOT}` placeholder and no absolute host path is recorded.

**Preserved boundaries.** `T039-F01`–`T039-F08` runtime behavior, generated-service provenance,
`T037-OPEN-06`, the REF-002 `unchanged` disposition with no promoted target, and the historical R3/R4/R5
review identities are preserved. `tests/xcom/tool_gateway/gateway_support.hpp` remains byte-identical
(SHA-256 `2559ead663bb0c25d5190bc949a3fb18b6096a2e49c90512e8a81ba3fa1a3aa5`). T039/T040 external review and
T041 user acceptance remain separate and open, and the platform-main merge is not performed.
