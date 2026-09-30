# T030–T038 terminal-repair record (R1–R9)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T038 repair stage over the accumulated T030–T038 candidate |
| Rejected baseline | `fe923fe21d2c9116940c7f83f22ef274ebe818c1` |
| Review authority | `docs/reviews/t030-t038-astra-terminal-review-2026-09-29.md` (SHA-256 `df03c9da…`) |
| External probes | `automation/reviews/t030-t038-20260929/gateway_probes.cpp` (read-only host input) |
| Classification | Public-safe engineering work product |

This record describes the repair of the nine terminal-review findings R1–R9. It does not accept or
integrate the successor candidate; external acceptance, terminal re-review, and the strict
target-repository integration gate remain separate graph stages. Human-readable run records and the
evidence report itself are intentionally excluded from the report material inventory.

## 2. Findings, changes, and closure tests

### R1 — P1 required gRPC service: BLOCKED (concrete missing offline dependency)

**Disposition: blocked, not substituted.** The accepted contract requires a versioned gRPC service
over host-protected local IPC with generated-client contract tests. The repair attempted to compile
and link the generated gRPC stubs against the admitted offline prefix.

**Concrete blocker.** The admitted prefix provides `libgrpc++.so.1.30.2` and `libgrpc.so.10.0.0`,
but neither can be loaded: the dynamic loader resolves a `NEEDED` entry `libcares.so.2` that is
absent from the admitted package envelope and from the host. The admitted package manifest lists no
`libc-ares2` package, and the admitted-input manifest hash is pinned by the trusted runner, so the
missing package cannot be added offline. Reproduction (public-safe, no host path recorded): resolve
the admitted prefix from the `XVERSE_XCOM_TOOLCHAIN` input, then run `ldd` on the admitted
`libgrpc++.so.1.30.2` and observe `libcares.so.2 => not found`; a direct `dlopen` of the same library
fails with the same unresolved soname. Linking these libraries into the gateway runtime would make
every gateway and synthetic-client test fail to start, so no transport was silently substituted. The
existing custom framing remains only as the accepted T031/T032 floor and is explicitly **not**
claimed as the contracted gRPC service. Closing R1 requires admitting the complete pinned gRPC
runtime (at minimum the `libc-ares2` runtime) into the offline envelope, which is a host dependency
change outside this offline repair.

**Closure test:** the `ldd`/`dlopen` probe above; no generated-client test is claimed.

### R2 — P1 invalid stimulation wire semantics normalized: CLOSED

**Changed paths:** `src/xverse/xcom/src/tool_gateway.cpp`, `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp`.

`SubmitStimulation` now validates the declared wire interaction, direction, schedule mode, clock
domain, and contract identity against the bound session before any side effect, and preserves the
declared interaction through the accepted guard/action path instead of rewriting it from the action.
An incompatible interaction, non-outbound direction, unknown/unspecified schedule mode, unmapped
clock domain, or contract mismatch is rejected with zero emission and no queue retention.

**Closure tests:** external probes `RejectMismatchedWireInteraction`, `RejectMismatchedWireDirection`,
`RejectUnknownScheduleMode`, `RejectUnmappedWireClock` all pass; candidate regressions
`XcomToolGatewayNegative.IncompatibleInteractionRejectedZeroSideEffects`,
`…IncompatibleDirectionRejectedZeroSideEffects`, `…UnknownScheduleModeRejectedZeroSideEffects`,
`…UnmappedClockRejectedZeroSideEffects`, `…ContractMismatchRejectedZeroSideEffects`.

### R3 — P1 counter-only scheduled work: CLOSED

**Changed path:** `src/xverse/xcom/src/tool_gateway.cpp`.

The scheduled branch no longer acknowledges work with a counter. Scheduled requests are validated
(including target authorization and clock mapping) before enqueueing, retained in the accepted
action path's bounded executable queue, and executed by the accepted scheduler through
`drain`, producing real terminal journal outcomes. Pending capacity is enforced before enqueue,
independent of transient flow-credit replenishment, and disconnect cancels retained work.

**Closure tests:** external probes `RejectUnauthorizedScheduledTarget` and
`PendingQueueRemainsBoundedAcrossTicks` pass; candidate regressions
`XcomToolGatewayBounds.ScheduledQueueBoundedAcrossCreditReplenishment`,
`…ScheduledActionExecutesWhenDue`, `…ScheduledActionExpiresPastLateWindow`.

### R4 — P2 per-request deadlines anchored to session creation: CLOSED

**Changed paths:** `src/xverse/xcom/src/tool_gateway.cpp`, `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp`.

Admission now anchors each request deadline to the request's own declared arrival using the bound
domain, so a long-lived session accepts a fresh request while the permit is valid. Idle timeout is
measured from the most recent declared activity, not from session creation. A declared schedule that
cannot complete within the request's own deadline window is rejected before enqueue.

**Closure tests:** external probe `EachRequestReceivesItsOwnDeadline` passes; candidate regressions
`XcomToolGatewayBounds.RequestDeadlineAnchoredToRequestArrival`,
`…ScheduleBeyondRequestDeadlineRejected`, `XcomToolGatewayLifecycle.IdleTimeoutTracksLastActivity`.

### R5 — P2 observation ownership overwritten: CLOSED

**Changed paths:** `src/xverse/xcom/src/tool_gateway.cpp`, `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp`.

Each accepted observation stream now owns an independent bounded handle in a per-session ownership
list bounded by the configured stream maximum. Opening a second stream no longer overwrites the
first; read, close, and disconnect operate on the exact requested stream identity, and the active
stream counter reflects the retained handles.

**Closure tests:** external probe `FirstStreamSurvivesSecondOpen` passes; candidate regression
`XcomToolGatewayLifecycle.IndependentObservationStreamsClose`.

### R6 — P2 lease release ignored lease identity: CLOSED

**Changed path:** `src/xverse/xcom/src/tool_gateway.cpp`.

`ReleaseLease` now compares the supplied lease identity to the exact held lease identity and rejects
a mismatched or stale identity without changing lease or session state. The synthetic separate-process
client, which already sends the acquired identity, still releases successfully.

**Closure tests:** external probe `ReleaseRequiresExactLeaseIdentity` passes; candidate regression
`XcomToolGatewayLifecycle.LeaseReleaseRequiresExactIdentity`.

### R7 — P2 final-candidate benchmark evidence: CLOSED

**Changed paths:** `reports/xcom-queue/t036-benchmark.json`, `engineering/check_xcom_traceability.py`.

The T036 controlled benchmark was re-measured and regenerated on the assembled revision so its
`baseline_revision` is the measured revision and its material digest and per-file hashes match the
successor. In addition, the repository-owned traceability verifier now runs the inherited benchmark
verifier (`engineering/run_xcom_benchmarks.py --verify`) on every candidate, so an earlier task's
evidence cannot silently go stale during a later task. Identity checks were not weakened. Material-input
policy: the report binds the exact observed baseline revision, the sorted material-input inventory,
the material digest, and every hashed artifact; the verifier still accepts only `HEAD == baseline_revision`
or the direct child of `baseline_revision`, and any changed bound material input forces a re-measurement
rather than a re-pin.

**Closure tests:** `python3 engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json`
reports `ok: true`, `outcome: pass`, `candidate_revision_state: working-tree`; the regenerated report
is now a direct-child-compatible binding for the committed successor.

### R8 — P1 accumulated predecessor trace coverage: CLOSED

**Changed paths:** `engineering/check_xcom_traceability.py`, `engineering/trace/links.json`.

`load_records` now loads the entire retained capability-007 record set (T020, T026–T038) and every
validation scenario. A new accumulated-scope check resolves referential integrity for every trace
link and requires the full requirement/component/unit relationship set for **every** record, so a
deleted predecessor requirement or a removed predecessor relationship fails closed. The evidence
report now reports the whole-scope counts (322 requirements) and resolved edges.

**Closure tests:** the full command `--self-test` NEG-05 (deleted predecessor requirement record) and
NEG-06 (removed predecessor verification edge) both fail closed with `CHAIN_INVALID`, and the positive
fixture still passes.

### R9 — P2 public-safety scan inventory gap: CLOSED

**Changed path:** `engineering/check_xcom_traceability.py`.

The retained-evidence scan now covers the T038 review/typed JSON, the T038 package record, the
predecessor typed records and package manifests, the T038 stage results, and the review index, with a
bounded, self-checking exception list limited to immutable predecessor review JSON records. An
exception that does not name a predecessor review record, or that names the T038 review, fails
closed.

**Closure tests:** `--self-test` NEG-07 injects a synthetic forbidden host path into the retained
T038 review JSON and the full command fails closed with `PUBLIC_SAFETY_INVALID`; the positive fixture
still passes with the broadened inventory.

## 3. Verification executed in this repair

- Isolated subtree build (Ninja, admitted offline toolchain): success.
- `ctest` over the assembled subtree: 496/496 pass in this environment (the sandbox permits
  `AF_UNIX` binding, so no IPC test was skipped or substituted).
- Candidate regression tests added: 14 new cases across the T031 bounds, lifecycle, and negative
  suites (38 t031 cases total).
- External review probes `gateway_probes.cpp`: 10/10 pass.
- `engineering/run_xcom_benchmarks.py --verify`: passes.
- `engineering/check_xcom_traceability.py --verify reports/xcom-queue/t038-traceability.json`: passes
  (322 requirements, 2752 resolved edges).
- `engineering/check_xcom_traceability.py --self-test`: NEG-01…NEG-07 pass.

## 4. Journal lessons applied

- **J-054** (review at emission and bind evidence to scope): wire semantics and lease ownership are
  challenged at submission/emission, and the trace report now covers the accumulated scope.
- **J-056** (deferred paths and evidence meaning): scheduled work is executed through the accepted
  drain path with real terminal outcomes, and a green structural matrix is no longer treated as
  semantic coverage — predecessor deletion is a full-command negative.
- **J-075** (bind a precommit benchmark report to the sealed candidate): the benchmark is re-measured
  on the assembled revision and inherited by a later task's validator.
- **J-077** (keep regenerated stage records out of the reviewed package inventory): the repair adds no
  generated stage record to the reviewed inventory.
- **J-078** (additive-only inherited changes): gateway changes are additive behaviour at the
  documented interface plus corrected validation; no accepted predecessor module was redefined.
- **J-080** (challenge accumulated gateway semantics and evidence coverage): the repair directly
  addresses the accumulated-semantics and evidence-inventory gaps the review recorded.

## 5. Open state

R1 remains a concrete, recorded blocker requiring a host-side offline dependency change. External
acceptance, terminal re-review, and strict target-repository integration are not performed here.
