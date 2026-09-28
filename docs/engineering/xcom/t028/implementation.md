# T028 Implementation Record — Guarded Actions and the Exclusive Service-Emulation Lease

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T028 (capability 007, slice `T-STIM`) |
| Stage / role | implementation → implementation record |
| Revision | 1 (guarded actions and exclusive service-emulation lease) |
| Authorized baseline | `c518c5e4fcb2055666db25cb62018769e7f56ae4` |
| Predecessors | T025 accepted bounded time authority, immutable validation permit, and session lifecycle; T026 bounded durable stimulation intent/outcome journal (present at the baseline, consumed read-only); T027 fail-closed pre-emission guard (present at the baseline, consumed read-only) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned at the workflow checkpoint) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | `docs/engineering/xcom/t028/internal-review.json` (separate read-only DeepSeek review, §12) |
| Package record | `reports/xcom-queue/t028-package.json` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC006`, `ACC010`, `ACC011`, `ACC014`, `ACC015`); ADR-0016; ADR-0018; ADR-0019; ADR-0020; `specs/007-xcom-core/tasks.md` T028 |
| Maturity | Prototype-only bounded guarded action path and exclusive service-emulation lease implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T028 implements the bounded slice required by the T028 task entry: *"Implement guarded
signal/message injection, service invocation, and exclusive generation-bound service emulation, plus
drain, close, revoke, expiry, and evidence-incomplete lifecycle completion."*

The candidate adds one additive C++20 production unit, `xverse_xcom_stimulation_actions`
(`stimulation_actions.hpp`/`.cpp`), and twenty-two GoogleTest cases across five additive executables. The
action path evaluates one declared `StimulationRequest` against the accepted T027 guard exactly once,
acquires the exclusive generation-bound emulation lease for an `EmulateService` action, journals the
payload-free intent durably through the accepted T026 journal **before** invoking the host
`ActionEmitter` seam exactly once, records an explicit bounded outcome, bounds its own emission-time
reinjection lineage, schedules authorized work in a bounded ordered pending queue, and completes the
lifecycle with `drain`, `close`, `revoke`, `expire`, and `mark_evidence_incomplete`. Every decline
emits nothing, journals nothing, and mutates no accepted guard, lease, queue, lineage, or durable
journal record in the declined dimension.

T028 authors **no** transport, provider, route, endpoint, tap, observation record, gateway, Protocol
Buffers/gRPC, IPC, or separate process, and it re-implements, weakens, or bypasses no accepted guard
or journal check.

`XCOM-SW-STIM-005` (loop bounding and conflict rejection), `XCOM-SW-STIM-006` (scheduling, clock
authority, and tolerance), and `XCOM-SW-STIM-008` (exclusive service-emulation lease) are
**implemented** by this task. `XCOM-SW-STIM-003` (persistent synthetic provenance) and
`XCOM-SW-STIM-009` (owned action conformance and lifecycle completion) remain **partial**: T028
carries the synthetic classification and exact identity on the emitted descriptor and implements the
four owned action kinds and the completion mechanics, while the routed/restarted provenance proof and
the complete owned-fixture matrix remain T029 (T028-GAP-02, T028-GAP-03).

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/stimulation_actions.hpp` | add | Public action-path and lease interface: closed `ActionStatus`/`LeaseStatus`/`LeaseState`/`OrderingRule`/`LateItemPolicy`/`DrainState`/`EmissionStatus`/`CompletionOutcome`/`QuarantineReason` vocabularies with stable names and ranks; bounded payload-free `ActionPathConfig`/`EndpointGeneration`/`EmulationLease`/`PendingAction`/`SyntheticStimulationItem`/`ActionDiagnostic`/`ActionPathSnapshot`/`LeaseSnapshot`/`CompletionRequest`/`CompletionReport`; the host `ActionEmitter` seam; `ServiceEmulationRegistry`; `StimulationActionPath`; and a compile-time payload-free/size rule |
| `src/xverse/xcom/src/stimulation_actions.cpp` | add | Deterministic check order (closed → malformed → lineage → capacity/precheck → session → guard → lease → queue/emit), non-mutating lease `precheck` with unconditional post-guard acquisition, atomic lease release/quarantine/expire, bounded pending queue and lineage window, journal-before-emission emission with the emitter invoked outside every lock, explicit emission-outcome surfacing, drop surfacing at completion, and bounded deterministic completion |
| `src/xverse/xcom/CMakeLists.txt` | edit | Add `xverse_xcom_stimulation_actions` to `XVERSE_XCOM_RUNTIME_TARGETS`; define the library linked to the accepted guard, journal, validation-session, and core-types targets; add five additive test executables with `t028-<kind>` labels; pass the committed header and source as build-time read-only paths to the suites |
| `tests/xcom/stimulation_actions/action_tests.cpp` | add | `T28-TS-001`…`T28-TS-005` |
| `tests/xcom/stimulation_actions/lease_tests.cpp` | add | `T28-TS-006`…`T28-TS-010` |
| `tests/xcom/stimulation_actions/lifecycle_tests.cpp` | add | `T28-TS-011`…`T28-TS-015` |
| `tests/xcom/stimulation_actions/negative_tests.cpp` | add | `T28-TS-016`…`T28-TS-018` |
| `tests/xcom/stimulation_actions/concurrency_tests.cpp` | add | `T28-TS-019`, `T28-TS-020` |
| `docs/engineering/xcom/t010/unit-design.json` | edit | Flip the three realized `XCOM-DU-018` artifact-path status values from `planned` to `established` (status projection only; see §7.1) |
| `docs/engineering/xcom/t010/design-units.md` | edit | Deterministic projection regenerated from the model (see §7.1) |
| `engineering/trace/links.json` | edit | Refresh the inherited `T020-L-046` `implemented_by` target revision to the new `src/xverse/xcom/CMakeLists.txt` content digest (see §7.7) |
| `engineering/stage-results/{documentation,implementation,integration,internal-review}.json` | edit | Refresh the inherited artifact digests for `engineering/trace/links.json` and `src/xverse/xcom/CMakeLists.txt` (see §7.7) |
| `docs/engineering/xcom/t028/requirements.md` | add | Plan-stage work product (unchanged) |
| `docs/engineering/xcom/t028/architecture.md` | add | Plan-stage work product (unchanged) |
| `docs/engineering/xcom/t028/detailed-design.md` | add | Plan-stage work product, with implementation-stage reconciliations recorded in §7 |
| `docs/engineering/xcom/t028/unit-specifications.md` | add | Plan-stage work product, with two implementation-stage reconciliations recorded in §7 |
| `docs/engineering/xcom/t028/verification-plan.md` | add | Plan-stage work product (unchanged) |
| `docs/engineering/xcom/t028/implementation.md` | add | This record |
| `docs/engineering/xcom/t028/internal-review.json` | add (review stage) | DeepSeek internal review |
| `specs/007-xcom-core/tasks.md` | edit | T028 checkbox marked complete (implementation stage only) |
| `reports/xcom-queue/t028-package.json` | add (package stage) | Exact-candidate package record |

No existing production header, source, target, test, label, command, or expected value is changed
apart from the derived T010 status projection and the inherited provenance refresh. No `xdl/`,
`proto/`, `src/xverse_xdl/`, `cmake/*.cmake`, root `CMakeLists.txt`, `contracts/`, T025
`validation_session.*`, T026 `stimulation_journal.*`, T027 `stimulation_guard.*`, or other task's
path is changed. No new admitted dependency is added; the unit links only the C++ standard library
plus the accepted `xverse::xcom_stimulation_guard`, `xverse::xcom_stimulation_journal`,
`xverse::xcom_validation_session`, and `xverse::xcom_core_types` contracts.

### 3.1 Changed symbols

- **New public enums**: `ActionStatus`, `LeaseStatus`, `LeaseState`, `OrderingRule`,
  `LateItemPolicy`, `DrainState`, `EmissionStatus`, `CompletionOutcome`, `QuarantineReason`.
- **New public constants**: `kActionPathMaxPendingActions`, `kActionPathMaxLineage`,
  `kActionPathMaxDrainSteps`, `kActionPathMaxPayloadBytes`, `kActionPathMaxActiveLeases`.
- **New public types**: `ActionPathConfig`, `EndpointGeneration`, `EmulationLease`, `PendingAction`,
  `SyntheticStimulationItem`, `ActionDiagnostic`, `ActionPathSnapshot`, `LeaseSnapshot`,
  `CompletionRequest`, `CompletionReport`.
- **New public functions**: `action_status_name`, `lease_status_name`, `lease_state_name`,
  `ordering_rule_name`, `late_item_policy_name`, `drain_state_name`, `emission_status_name`,
  `completion_outcome_name`, `quarantine_reason_name`, `precedence_rank(ActionStatus)`,
  `precedence_rank(LeaseStatus)`.
- **New public classes**: `ActionEmitter` (host seam), `ServiceEmulationRegistry` (`precheck`,
  `acquire`, `release`, `quarantine`, `expire_key`, `expire_elapsed`, `holds`, `state_of`, `snapshot`,
  `capacity`), `StimulationActionPath` (`open`, `execute`, `drain`, `close`, `revoke`, `expire`,
  `mark_evidence_incomplete`, `snapshot`, `is_open`).
- **No accepted symbol** is renamed, removed, or redefined; the accepted T025/T026/T027/T-CORE
  vocabulary and the T027 `StimulationAction`/`GuardOutcome`/`GuardReason` are reused read-only.

### 3.2 Realized decision order and vocabulary

`execute` evaluates in a fixed order under one action-path mutex: (1) closed path → `NotOpen`;
(2) malformed `request_id` or over-bound payload → `RejectedConfiguration`; (3) a bounded-lineage
reinjection → `Rejected`/`LoopBound`; (4) pending-queue capacity or a non-mutating emulation lease
`precheck` (identity and capacity) → `CapacityExhausted`/`LeaseConflict` with the matching `LeaseStatus`;
(5) non-active session → `NotActive`; (6) the accepted T027 guard evaluated exactly once → `Rejected`/
`Failed` with the guard reason and **no lease acquired**; (7) unconditional atomic emulation-lease
acquisition for an authorized action → `LeaseConflict` with the matching `LeaseStatus` on any collision;
(8) an authorized scheduled action → `Queued`; (9) an authorized immediate action → journal-before-emission
and exactly one emitter call, classified as `Emitted` only for a durable host `Delivered` outcome, or
`EmissionRejected`/`EmissionUnavailable` for a durable non-delivery, or `EvidenceIncomplete` when the
intent is durable without an outcome, or `JournalFailed`/`CapacityExhausted`/`RejectedConfiguration` per
the mapping in the detailed design. Only a durable intent, a single host-`Delivered` emission, and a
durable outcome produce `Emitted`.

The closed action table is reused from T027: `InjectSignal`↔`signal_state_update`/`produce`,
`InjectMessage`↔`message_event`/`produce`, `InvokeService`↔`service_request`/`request`,
`EmulateService`↔`service_response`/`respond`. The declared bounds are
`kActionPathMaxPendingActions = 64`, `kActionPathMaxLineage = 64`, `kActionPathMaxDrainSteps = 64`,
`kActionPathMaxPayloadBytes = 4096`, and `kActionPathMaxActiveLeases = 64`.

The exclusive lease key is exactly `(session, endpoint, generation, plan_digest)`. A non-mutating
`precheck` classifies the emulation precondition before the guard, and acquisition is an unconditional
atomic check-then-insert under one registry mutex after an authorized decision; a second emulation action
for the same endpoint generation, or a request under a foreign session, generation, or plan, is rejected
with `Conflict`/`SessionMismatch`/`GenerationMismatch`/`PlanMismatch` and no mutation and no emission. A
released, quarantined, or expired lease is retained as a bounded tombstone and no longer conflict-blocks.

### 3.3 Test units added

| Unit | Case | Suite | Label |
| --- | --- | --- | --- |
| `T28-TS-001` | `ActionPathExecutesNominalActionKinds` | `action` | `t028-action` |
| `T28-TS-002` | `ActionPathGuardDecisionMapping` | `action` | `t028-action` |
| `T28-TS-003` | `ActionPathSyntheticProvenance` | `action` | `t028-action` |
| `T28-TS-004` | `ActionPathVocabularyAndDeterminism` | `action` | `t028-action` |
| `T28-TS-005` | `ActionPathConfigAndPreconditionMatrix` | `action` | `t028-action` |
| `T28-TS-006` | `LeaseAcquireIdentityBindingMatrix` | `lease` | `t028-lease` |
| `T28-TS-007` | `LeaseConflictAndCapacityMatrix` | `lease` | `t028-lease` |
| `T28-TS-008` | `LeaseReleaseQuarantineMatrix` | `lease` | `t028-lease` |
| `T28-TS-009` | `LeaseExpiryAndDomainMatrix` | `lease` | `t028-lease` |
| `T28-TS-010` | `LeaseGenerationSupersessionMatrix` | `lease` | `t028-lease` |
| `T28-TS-011` | `LifecycleScheduledQueueAndOrdering` | `lifecycle` | `t028-lifecycle` |
| `T28-TS-012` | `LifecycleLateItemPolicyMatrix` | `lifecycle` | `t028-lifecycle` |
| `T28-TS-013` | `LifecycleDrainCloseRevokeExpire` | `lifecycle` | `t028-lifecycle` |
| `T28-TS-013` | `LifecycleNonActiveCompletionFailsClosed` | `lifecycle` | `t028-lifecycle` |
| `T28-TS-014` | `LifecycleEvidenceIncompleteCompletion` | `lifecycle` | `t028-lifecycle` |
| `T28-TS-014` | `LifecycleTerminalEvidenceIncompleteNeverClosed` | `lifecycle` | `t028-lifecycle` |
| `T28-TS-015` | `LifecycleImmediateAndUnmappedClock` | `lifecycle` | `t028-lifecycle` |
| `T28-TS-016` | `ActionPathDeclineZeroMutationAndZeroEmission` | `negative` | `t028-negative` |
| `T28-TS-017` | `ActionPathClosedAndCapacityReject` | `negative` | `t028-negative` |
| `T28-TS-018` | `ActionPathPayloadFreeDeclarationInspection` | `negative` | `t028-negative` |
| `T28-TS-019` | `ActionPathBoundedDeterministicConcurrency` | `concurrency` | `t028-concurrency` |
| `T28-TS-020` | `LeaseConcurrentRaceSingleWinner` | `concurrency` | `t028-concurrency` |

## 4. Deterministic gate and build evidence

```sh
python3 ${XVERSE_FABRIC_ROOT}/automation/xcom_feature_gate.py verify T028 c518c5e4fcb2055666db25cb62018769e7f56ae4
```

The gate's configure reuses the `build/fabro-t028` cache seeded (A-1) with the previously admitted
`XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` cache
values (named by role only; no ambient path or network resolution was added and no admission check
was weakened). Observed result at the implementation stage: `ok` with the six T028 work products
present, the T028 checkbox marked complete, at least one `src/xverse/xcom/` and one `tests/` path
changed, the configure/build/discovery/full-`ctest` sequence exiting 0, and `git diff --check` clean.

| Item | Value |
| --- | --- |
| Configure (A-1 cache seed) | `cmake -S . -B build/fabro-t028 -G Ninja -DCMAKE_BUILD_TYPE=Debug -D<three admitted A-1 cache values>` (exit 0) |
| Configure (plain, reused by the gate) | `cmake -S . -B build/fabro-t028 -G Ninja -DCMAKE_BUILD_TYPE=Debug` (exit 0) |
| Build | `cmake --build build/fabro-t028 --parallel 4` (exit 0, no warning emitted under `-Werror`) |
| Toolchain | host GNU C++ 11.4.0 (`-std=c++20`) under the T012 `-Wall -Wextra -Wpedantic -Werror` contract |
| Discovery | `ctest --test-dir build/fabro-t028 -N` → `Total Tests: 367` (T027 baseline 345 + 22) |
| Full suite | `ctest --test-dir build/fabro-t028 --output-on-failure --parallel 4` → `100% tests passed, 0 tests failed out of 367` |
| T028 suites | `ctest -L t028` → `100% tests passed, 0 tests failed out of 22` across `t028-action` (5), `t028-lease` (5), `t028-lifecycle` (7), `t028-negative` (3), `t028-concurrency` (2) |
| Preserved suites | `t025` 144, `t026` 18, `t027` 21, `t016` 58, `t019` 39, `t020` 52 all pass unchanged |
| Build contract | `xcom_build_contract` passes with the added runtime target |
| Diff hygiene | `git diff --check c518c5e4fcb2055666db25cb62018769e7f56ae4 --` → clean |

Additivity: the discovered count is the T027 baseline 345 plus exactly the 22 new T028 cases; every
pre-existing target, test name, label, command, and expected value is preserved, and the T012
build-contract verifier accepts the one-target inventory extension.

### 4.1 Supporting checks

```sh
python3 scripts/validate_xcom_task_ownership.py --verify        # exit 0
python3 scripts/validate_xcom_task_ownership.py --check-human   # exit 0
python3 scripts/validate_xcom_requirements_traceability.py --verify     # exit 0
python3 scripts/validate_xcom_requirements_traceability.py --check-human # exit 0
python3 scripts/validate_xcom_architecture_contracts.py --verify        # exit 0
python3 scripts/validate_xcom_architecture_contracts.py --check-human   # exit 0
python3 scripts/validate_xcom_unit_design.py --verify                   # exit 0
python3 scripts/validate_xcom_unit_design.py --check-human              # exit 0
```

## 5. Source inspections

- **Guarded action execution and decision order (CHK-06, CHK-07, NEG-33, NEG-34)** — `execute`
  evaluates the fixed order in §3.2 and returns on the first failing step; `T28-TS-005` and
  `T28-TS-017` prove that a closed path, a malformed request, an over-bound payload, a full pending
  queue, and a non-active session decline **before** any guard evaluation (a quota of one remains
  available for a later valid request), and `T28-TS-002` proves every guard decline maps to the
  declared `ActionStatus` with the guard reason preserved, no emission, no journal, and **no lease
  acquired** (the full lease snapshot, including `acquisitions` and `released`, is byte-identical).
- **Exclusive generation-bound lease (CHK-10, CHK-11, CHK-12, NEG-09…NEG-13)** — `T28-TS-006`
  proves the key binds session, endpoint, generation, and plan digest and that a foreign identity is
  `Conflict`/`SessionMismatch`/`GenerationMismatch`/`PlanMismatch`; `T28-TS-007` proves the same-
  generation conflict and the active-lease capacity bound with a byte-identical pre/post snapshot;
  `T28-TS-008` proves exact-owner release, `NotFound`, `AlreadyReleased`, and quarantine;
  `T28-TS-010` proves a superseded generation neither authorizes nor conflict-blocks, that a second
  request for an already-held generation is `LeaseConflict`/`Conflict` with no second-owner emission,
  and `T28-TS-020` proves a four-thread race has exactly one winner.
- **Journal-before-emission and explicit outcome (CHK-08, NEG-07)** — `T28-TS-001` and `T28-TS-003`
  record the durable intent byte count observed inside the single emitter call (it is non-zero and
  precedes the call); `T28-TS-001` also proves a durable host `Rejected`/`Unavailable` outcome maps to
  `EmissionRejected`/`EmissionUnavailable` (reporting `emission_status`, the matching snapshot counter,
  and `emitted == 0`), never `Emitted`; `T28-TS-014` injects one failed outcome append and proves the
  action is `EvidenceIncomplete`, never `Emitted`/`Closed`, with one durable orphan intent surfaced.
- **Synthetic provenance (CHK-09, NEG-08)** — `T28-TS-003` asserts the emitted descriptor carries
  `OriginKind::validation_tool` and the exact permit/session/plan/request/correlation/causation,
  tool, target, and action identity, and that the recovered durable intent equals the emitted intent;
  the concurrency suite additionally asserts zero foreign-origin emissions.
- **Loop bounding (CHK-14, NEG-15, NEG-16)** — `T28-TS-012` proves a retained-lineage causal parent
  is `Rejected` with no emission and no journal, that a `causation_id` of zero is never a loop, that
  the bounded lineage window evicts the oldest identity, and that the declared bound holds.
- **Scheduling, ordering, and late policy (CHK-15, NEG-17, NEG-18)** — `T28-TS-011` proves bounded
  enqueue, the declared `(scheduled_at, request_id)` order, deterministic drain order, and the drain
  becoming `Drained` when the queue empties; `T28-TS-012` proves both late-item policies emit
  nothing and that the drain budget bounds each call.
- **Lifecycle completion (CHK-16, NEG-20…NEG-22)** — `T28-TS-013` proves `drain` terminal cancels
  with zero emission, `close` drains then releases every held lease, `revoke` cancels and releases,
  `expire` cancels and expires, a foreign completion domain mutates nothing, and a non-active,
  non-terminal (`declared`/`armed`) `drain`/`close` cancels every due pending action with zero emission
  and never returns `Drained`/`Closed`; `T28-TS-014` proves an evidence-incomplete intent is never
  `Closed` for both a non-terminal and a terminal `closed` `close`/`drain`, and that a due action whose
  drain-time intent append fails is surfaced as `CompletionReport.failed` with an `EvidenceIncomplete`
  outcome rather than a clean `Drained`.
- **Non-mutation and zero emission on decline (CHK-21, NEG-25…NEG-27)** — `T28-TS-016` brackets
  every decline family (closed, malformed, over-bound, loop, capacity, non-active, guard rejection,
  guard failure, guard quota exhaustion on emulation, lease conflict, journal-write decline) with an
  operational snapshot comparison, the unchanged durable journal bytes, the unchanged lease table
  (including its acquisition and release accounting on a guard decline), and a zero emitter-call
  count.
- **Determinism and bounded concurrency (CHK-17, CHK-18, NEG-28, NEG-29, NEG-36)** — `T28-TS-004`
  proves closed stable names/ranks and three identical repeated runs; `T28-TS-019` proves a declared
  guard quota of seven is never exceeded by four threads submitting sixty-four bounded evaluations
  and that three runs match the golden result; the emitter is invoked outside every lock, so no host
  callback runs under a lock.
- **Offline and local-only (CHK-19, CHK-20, NEG-02, NEG-30)** — the unit includes only the C++
  standard library plus the accepted T025/T026/T027 headers and the accepted T-CORE `item.hpp`;
  `T28-TS-018` reads the committed header and source, strips comments, and asserts that no
  network/socket/resolver/TLS, ambient/secret, dynamic-load, subprocess, filesystem, retention, or
  export vocabulary appears; the action path calls no time authority and owns no I/O boundary.
- **Public safety (CHK-21, NEG-31)** — a scan of the changed files finds no credential, private
  address, real or proprietary payload, environment-specific absolute path, or sensitive value; the
  only absolute paths live inside git-ignored build output and are never committed as evidence.
- **Doxygen (CHK-22)** — every public declaration carries `\brief` plus `\ownership`, `\lifetime`,
  `\thread_safety`, and `\failure` where applicable; the file block names T028 and `\ingroup
  xcom_stim`; the admitted documentation configuration is unchanged.

## 6. Requirement-to-change-to-check traceability

| Requirement | Realized by | Check(s) |
| --- | --- | --- |
| T028-SR-001 | one new additive unit + one new runtime target + five additive test executables | CHK-02, CHK-04, CHK-18 |
| T028-SR-002 | includes only standard headers plus `stimulation_guard.hpp`/`stimulation_journal.hpp`/`validation_session.hpp`/`item.hpp`; links the accepted targets | CHK-03, CHK-19 |
| T028-SR-003 | closed action/lease/state/ordering/late/drain/emission/completion/quarantine vocabularies with stable names and ranks | CHK-17, CHK-20 |
| T028-SR-004 | bounded payload-free values + compile-time constructor/size rule + declaration inspection | CHK-05, CHK-20 |
| T028-SR-005 | closed/malformed/capacity/session preconditions before any guard evaluation | CHK-06, CHK-18 |
| T028-SR-006 | one accepted guard evaluation with the decline mapping | CHK-07, CHK-14 |
| T028-SR-007 | journal-before-emission ordering and explicit outcome classification | CHK-08, CHK-16 |
| T028-SR-008 | synthetic origin and exact intent identity on every emitted descriptor | CHK-09 |
| T028-SR-009 | exact `(session, endpoint, generation, plan)` lease key and foreign-identity rejection | CHK-10 |
| T028-SR-010 | atomic check-then-insert acquire with the active-lease capacity bound | CHK-11, CHK-18 |
| T028-SR-011 | exact-owner release, quarantine, and bounded tombstones | CHK-12 |
| T028-SR-012 | `expire_key`/`expire_elapsed` and declared-domain-only comparison | CHK-13 |
| T028-SR-013 | bounded emission-time lineage window and prohibited-reinjection rejection | CHK-14 |
| T028-SR-014 | bounded ordered pending queue, drain budget, and late-item policy | CHK-15 |
| T028-SR-015 | immediate labeling and unmapped/out-of-tolerance fail-before-emission | CHK-13, CHK-19 |
| T028-SR-016 | bounded deterministic drain/close/revoke/expire/evidence-incomplete completion | CHK-16 |
| T028-SR-017 | non-mutating decline paths and commit-only success | CHK-21 |
| T028-SR-018 | closed deterministic vocabulary and repeated-run equality | CHK-17 |
| T028-SR-019 | one mutex per component, no callback under a lock, bounded threads | CHK-18 |
| T028-SR-020 | standard-library + accepted-header includes; no I/O; no payload retention | CHK-19, CHK-20 |
| T028-SR-021 | public-safe source, tests, and work products | CHK-21 |
| T028-SR-022 | Doxygen on every public declaration; `\ingroup xcom_stim` | CHK-22 |
| T028-SR-023 | registers re-validated; `XCOM-SW-STIM-005`/`-006`/`-008` implemented; `-003`/`-009` partial; REF-002 unchanged | CHK-23 |
| T028-SR-024 | deterministic gate; clean diff; checkbox marked only in this stage | CHK-24 |

Check and negative-case identifiers are the accepted [`verification-plan.md`](verification-plan.md)
§4–§5.

## 7. Plan-stage reconciliation (recorded, not silently edited)

The pre-code work products are the accepted plan for this task. The implementation required several
honest, recorded reconciliations rather than editing an accepted predecessor or silently departing
from the plan. No requirement or check is weakened.

### 7.1 T010 `XCOM-DU-018` artifact-path status projection

`docs/engineering/xcom/t028/requirements.md` §7.2 listed `docs/engineering/xcom/t010/**` as consumed
read-only. Implementing the unit realizes the three `XCOM-DU-018` paths that the T010 model recorded
as `planned`, and `scripts/validate_xcom_unit_design.py --verify` fails closed when a `planned` path
exists on disk. Following the repository convention precedented by T026 and commit `c518c5e`, the
three `artifact_paths` status values were flipped from `planned` to `established` in
`unit-design.json`, and `design-units.md` was re-projected to match; no unit identity, ownership,
lifetime, thread-safety, bound, failure semantics, planned evidence, or Doxygen obligation is
changed.

### 7.2 Bounded `PendingAction` retains the declared request (provenance for scheduled work)

`detailed-design.md` §3.5 listed `PendingAction` with five bounded fields and no declaration body.
A queued action is emitted at drain time, after the call-scoped payload and request have left scope,
so the full bounded payload-free `StimulationRequest` is retained in the pending descriptor to
reconstruct the exact intent identity and the exact lease key (`XCOM-INV-03`, `T028-SR-008`). The
retained value is bounded and payload-free; the call-scoped payload view is still retained nowhere
and is forwarded to the emitter only for an immediate action. A scheduled action therefore emits
with an empty payload view, recorded as `T028-OPEN-02`.

### 7.3 Lease identity-mismatch statuses are classified atomically in `acquire`

`detailed-design.md` §4.6 described `acquire` returning `Conflict` for a same-generation or
same-`(endpoint, session)` collision, while `verification-plan.md` CHK-10 and `T028-SR-009` require
`SessionMismatch`/`GenerationMismatch`/`PlanMismatch` for a foreign identity. The requirement and its
named checks take precedence (`requirements.md` §1.2): a single atomic check classifies an active
lease with the same endpoint into `PlanMismatch`, `SessionMismatch`, `GenerationMismatch`, or
`Conflict`, so the action path maps every collision to `LeaseConflict` with the exact lease status
and consumes no guard quota. No expected value or test is weakened.

### 7.4 `CompletionReport.expired_leases` and the `expire_key` registry operation

`detailed-design.md` §3.6 listed six `CompletionReport` fields, none of which reports an expired held
lease, while §4.5 requires `expire` to expire every held lease. A seventh bounded field,
`expired_leases`, and one bounded registry operation, `expire_key`, were added so `expire` can expire
each held lease deterministically regardless of the caller-supplied time and report the count. The
`expire_elapsed(domain, now)` primitive remains the declared-domain comparison used by the lease
matrix. This public-surface addition is recorded under `T028-OPEN-01`; no ownership, lifetime,
thread-safety, or failure semantics is changed.

### 7.5 Drain and close outcome semantics

`detailed-design.md` §4.4 step 4 returned `Drained` only "when the queue is empty and no action was
cancelled", while §5.5 and CHK-16 expect `Drained` when the due queue empties. The requirement and
its named table take precedence: `drain` returns `Drained` when the pending queue is empty after the
bounded step budget and `None` while work remains; `close` returns `EvidenceIncomplete` when any
durable intent has no durable outcome (from the accepted journal's recovered orphan index) and
`Closed` otherwise. A terminal-state `drain`/`close` cancels every pending action and releases every
held lease with zero emission; a terminal `closed` state whose journal holds a durable intent without a
durable outcome returns `EvidenceIncomplete`, never `Closed` (see §7.10).

### 7.6 The action-path reinjection lineage is a precondition

`T028-SR-013` requires the action path's own bounded emission-time lineage window in addition to the
accepted guard's loop window. The lineage check is evaluated as an early precondition (step 3 in
§3.2) so a prohibited reinjection consumes no accepted guard quota and journals nothing; when both
windows would decline, the action-path status is `Rejected` with `GuardReason::LoopBound` and the
guard is not evaluated. `T28-TS-012` proves the eviction and the zero-emission decline.

### 7.7 Inherited trace and stage provenance refresh

Changing `src/xverse/xcom/CMakeLists.txt` invalidates the inherited `T020-L-046` `implemented_by`
target digest in `engineering/trace/links.json`, and changing `links.json` invalidates the declared
`engineering/trace/links.json` artifact digests in `engineering/stage-results/{documentation,
integration,internal-review}.json`; `engineering/stage-results/implementation.json` also declares the
`CMakeLists.txt` artifact digest. Following the T026/T027 precedent, those inherited digests were
refreshed to the new content digests. A full iteration found zero stale `implemented_by` target
digests and zero stale stage artifacts afterwards. No requirement, link identity, relation, or stage
result is changed.

### 7.8 Bound source and public-element count versus `XCOM-DU-018` (`T028-OPEN-01`)

The accepted T010 `XCOM-DU-018` records the active-lease capacity as declared in the activation plan,
the drain deadline and drain queue depth as declared in the validation permit, and six
documented/public elements. The accepted T025 `Permit` exposes neither an active-lease capacity nor a
drain declaration. T028 therefore supplies a bounded `ActionPathConfig` derived by the caller from
the digest-bound plan and cross-checked against the immutable permit at open, and its realized public
surface (vocabularies, bounded values, the emitter seam, the registry, and the action path) is larger
than the six-element plan. This delta is recorded here rather than by editing the accepted T010
artifact, consistent with `T028-OPEN-01`; no accepted bound, ownership, lifetime, or thread-safety
model is changed.

### 7.9 Repair pass after the fresh independent review (T028-IR2-F01…F04)

A separate fresh read-only review of the first candidate (`internal-review.json`, review revision 2)
recorded four blocking findings that the repair pass resolved without weakening an accepted
requirement, check, or test:

- **F01 (guard decline acquired a lease).** `execute` previously acquired the exclusive lease before
  the guard and released it on a decline, leaving a `Released` tombstone and advancing `acquisitions`.
  The order is now: a non-mutating `ServiceEmulationRegistry::precheck` classifies the emulation
  precondition (step 4), the accepted guard is evaluated exactly once (step 6), and only an
  authorized action acquires the lease unconditionally (step 7). A `Rejected`/`Failed` decision now
  acquires no lease, so `T28-SR-006`, the accepted data-flow order, and NEG-25 hold. `T28-TS-002`
  now compares the whole lease snapshot (including `acquisitions` and `released`) on a
  guard-declined `EmulateService`, and `T28-TS-016` does the same for a guard quota decline. The
  `verification-plan.md` CHK-07 carve-out ("except a same-call acquire/release pair") is removed.
- **F02 (second owner emitted under a held lease).** The acquisition was gated by
  `!registry.holds(key)`, so a second request for an already-held endpoint generation bypassed
  `acquire` and emitted as a second owner. Acquisition is now unconditional after the guard, and the
  non-mutating `precheck` already rejects an exact-key holder with `LeaseStatus::Conflict` before the
  guard; `T28-TS-010` now proves the second request is `LeaseConflict`/`Conflict` with the emitter
  called at most once and the lease owner unchanged (`acquisitions == 1`).
- **F03 (host non-delivery reported as success).** `classify_locked` mapped `JournalStatus::Ok`
  unconditionally to `Emitted`. `ActionDiagnostic` now carries `emission_status`, `ActionPathSnapshot`
  carries `emission_rejected`/`emission_unavailable`, and a durable host `Rejected`/`Unavailable`
  outcome maps to the new closed-status `ActionStatus::EmissionRejected`/`EmissionUnavailable`, never
  `Emitted`; `T28-SR-007`, `T28-STK-002`, CHK-08, and the emitter contract are thereby reconciled.
  `T28-TS-001` exercises both non-delivery statuses and asserts `emitted == 0` and the matching
  snapshot counter.
- **F04 (drain/close silently dropped a due action).** `drain`/`close` counted only `Emitted`,
  `Cancelled`, and `EvidenceIncomplete`, so a journal append failure during drain dropped a due,
  previously authorized action behind a clean `Drained`/`Closed` outcome. `CompletionReport` now
  carries a bounded `failed` count, and a completion with a dropped due action returns
  `EvidenceIncomplete`, never `Drained`/`Closed`; `T28-SR-016` and CHK-16 are updated. `T28-TS-014`
  injects a drain-time intent-append failure and asserts `failed == 1` with an `EvidenceIncomplete`
  outcome and zero emission.

All four repairs are confined to the T028 source, its tests, and the T028 work products; no accepted
T025/T026/T027 byte, shared build element, or other task path is touched, and the deterministic gate
still discovers 367 tests with the five `t028-*` suites at 22/22.

### 7.10 Repair pass after the second fresh independent review (T028-IR4-F01, T028-IR4-F02)

A second fresh read-only review of the repaired candidate (`internal-review.json`, review revision 4)
confirmed the four earlier findings closed and recorded two remaining completion-contract defects. The
repair pass resolves both without weakening an accepted requirement, check, or test:

- **T028-IR4-F01 (terminal completion masked an orphan intent).** The terminal branch of `close()` and
  `drain()` returned `CompletionOutcome::Closed` for a `closed` session even when the journal reported a
  durable intent without a durable outcome (`report.evidence_incomplete > 0`), contradicting the `close`
  header contract ("`EvidenceIncomplete` when a durable intent has no durable outcome, never `Closed`"),
  `detailed-design.md` §4.5, CHK-16, and NEG-22. The `closed` case now returns `EvidenceIncomplete` whenever
  `evidence_incomplete > 0` and `Closed` only otherwise; `expired`/`revoked`/`evidence_incomplete` retain
  their terminal mapping. `T28-TS-014` gains `LifecycleTerminalEvidenceIncompleteNeverClosed`, which forces
  an orphan intent through the fault-injecting storage seam and asserts `close(closed)` and `drain(closed)`
  both return `EvidenceIncomplete` with `evidence_incomplete >= 1`, and that a terminal completion with no
  orphan intent still returns `Closed`. The existing non-terminal `T28-TS-014` assertions are retained.
- **T028-IR4-F02 (non-active completion emitted).** `drain()` and `close()` branched only on `is_terminal`,
  so a caller-supplied `declared`/`armed` state drained and emitted a due pending action, diverging from
  `detailed-design.md` §4.4 step 3. Both operations now validate the completion session state: for a
  non-active, non-terminal state they cancel every pending action with zero emission, leave the lease table
  unchanged (no action is authorized in that state), set `DrainState::Cancelled`, and return `None` (or
  `EvidenceIncomplete` when the journal already holds an orphan intent). `T28-TS-013` gains
  `LifecycleNonActiveCompletionFailsClosed`, which queues a due action and asserts `drain`/`close` under
  `declared` and `armed` emit nothing, cancel the pending action, and never return `Drained`/`Closed`.

`detailed-design.md` §4.4/§4.5 and `verification-plan.md` CHK-16 were reconciled to state the terminal
`EvidenceIncomplete` rule and the non-active fail-closed rule; `unit-specifications.md` `T28-TS-013`/
`T28-TS-014` were updated accordingly. An independent out-of-repo probe compiled against the built
archives reproduced both defects before the repair and confirmed closure after it: `close(closed)` and
`drain(closed)` with an orphan intent return `EvidenceIncomplete` with `evidence_incomplete >= 1` and not
`Closed`, `drain`/`close` under `declared`/`armed` emit nothing and never return `Drained`/`Closed`, and
the `active`/`closed`-without-orphan regression paths are unchanged. Both repairs are confined to the T028
source, its tests, and the T028 work products; no accepted T025/T026/T027 byte, shared build element, or
other task path is touched, and the deterministic gate discovers 367 tests with the five `t028-*` suites
at 22/22.

## 8. Negative cases realized

| NEG | Realized case | Observed result |
| --- | --- | --- |
| NEG-01 | `git diff --name-only`, `ctest -N` | only T028 paths plus the T010 status projection and the inherited provenance refresh; existing targets/tests unchanged |
| NEG-02 | include/link inspection + `T28-TS-018` | only the standard library plus the accepted headers; no redefined identity/digest/interaction/origin/action type; no new dependency |
| NEG-03 | header `static_assert`s + `negative_tests.cpp` compile-time rules + declaration inspection | a payload-accepting constructor or unbounded value fails the build; no payload member by declaration inspection |
| NEG-04 | `T28-TS-004` | every vocabulary is closed with stable names and ranks; an out-of-vocabulary value yields an empty name |
| NEG-05 | `T28-TS-005` | an invalid tool tag or an out-of-range declared bound is `RejectedConfiguration` at open |
| NEG-06 | `T28-TS-002`, `T28-TS-016` | a guard rejection or failure emits nothing and journals nothing |
| NEG-07 | `T28-TS-014` | a durable intent without a durable outcome is `EvidenceIncomplete`, never `Emitted`/`Closed` |
| NEG-08 | `T28-TS-003` | every emitted item carries `OriginKind::validation_tool` and the exact identity |
| NEG-09 | `T28-TS-006` | a foreign session is `SessionMismatch` with no mutation |
| NEG-10 | `T28-TS-006`, `T28-TS-010` | a foreign/superseded generation is `GenerationMismatch` and neither authorizes nor conflict-blocks |
| NEG-11 | `T28-TS-007`, `T28-TS-020` | one active lease per endpoint generation; a race has exactly one winner |
| NEG-12 | `T28-TS-008` | a non-owner or unknown release is `NotHeld`/`NotFound` with no mutation |
| NEG-13 | `T28-TS-008`, `T28-TS-009` | a released/quarantined/expired lease is not active and a re-acquire succeeds |
| NEG-14 | `T28-TS-009` | a foreign-domain value is never compared or ordered |
| NEG-15 | `T28-TS-012`, `T28-TS-016` | a retained-lineage reinjection is `Rejected` with no emission and no journal |
| NEG-16 | `T28-TS-012` | the lineage window never exceeds its declared bound and evicts the oldest |
| NEG-17 | `T28-TS-005`, `T28-TS-012`, `T28-TS-017` | a full pending queue is `CapacityExhausted` and the drain budget bounds each call |
| NEG-18 | `T28-TS-012` | both late-item policies emit nothing |
| NEG-19 | `T28-TS-015` | an unmapped/out-of-tolerance resolution fails before emission and before journaling |
| NEG-20 | `T28-TS-013` | `revoke`/`expire` cancel every pending action |
| NEG-21 | `T28-TS-013` | `close`/`revoke`/`expire` release or expire every held lease |
| NEG-22 | `T28-TS-014` | an evidence-incomplete intent is never `Closed`, including from a terminal `closed` `close`/`drain` |
| NEG-23 | `T28-TS-009`, `T28-TS-015` | no raw cross-domain comparison and no time-authority call |
| NEG-24 | `T28-TS-015` | an absent/unmapped/out-of-tolerance time is `Failed`/`TimeUnmapped` |
| NEG-25 | `T28-TS-016` | a decline mutates no lease, queue, lineage, or journal record |
| NEG-26 | `T28-TS-016` | a decline mutates no accepted guard or T025/T026 state |
| NEG-27 | `T28-TS-016`, `T28-TS-019` | a decline invokes no host callback; the emitter is invoked outside every lock |
| NEG-28 | `T28-TS-004` | stable names/ranks and three identical repeated runs |
| NEG-29 | `T28-TS-019`, `T28-TS-020` | ≤ 4 threads, ≤ 16 evaluations per thread, no callback under a lock, no wall-clock verdict |
| NEG-30 | forbidden-API inspection + offline build | no forbidden element; no new dependency |
| NEG-31 | public-safety scan | no forbidden content in committed files |
| NEG-32 | gate + diff + §7 | no non-T028 path beyond the recorded projections; checkbox marked only in this stage; REF-002 unchanged |
| NEG-33 | `T28-TS-005`, `T28-TS-017` | every zero/over-maximum/invalid declared bound is `RejectedConfiguration` with the path left closed |
| NEG-34 | `T28-TS-017` | a closed path returns `NotOpen`, and a malformed request is rejected before any guard call |
| NEG-35 | read-only consumption + `T28-TS-002` | the accepted guard and journal are consumed through their public surfaces and never re-implemented or weakened |
| NEG-36 | `T28-TS-019` | only a guard-authorized action is emitted; concurrent runs never exceed the declared quota |

## 9. Limitations and gaps

- `T028-LIM-01` — Prototype only: passing the tests proves no runtime, end-to-end route,
  compatibility, parity, or production-readiness claim; not user-accepted (T041) and not externally
  reviewed.
- `T028-LIM-02` — `XCOM-SW-STIM-003` is **partial**: T028 carries the synthetic classification and
  exact identity on the emitted descriptor; routed/restarted provenance through observation and the
  gateway is T029/T033 (`T028-GAP-02`).
- `T028-LIM-03` — `XCOM-SW-STIM-009` is **partial**: T028 implements and tests the four action kinds
  and the completion mechanics; the complete owned-fixture conformance matrix is T029
  (`T028-GAP-03`).
- `T028-LIM-04` — The transport realization is the host-supplied `ActionEmitter` seam; T028 authors
  no route, provider, endpoint, or routed item (`T028-GAP-01`).
- `T028-LIM-05` — A scheduled action emits with an empty payload view because the call-scoped payload
  is retained nowhere; the accepted observation policy for scheduled payload views is T030–T034
  (`T028-OPEN-02`).
- `T028-LIM-06` — The action path consumes a caller-resolved time and calls no time authority, so a
  decline can never mutate the authority's regression baseline; the end-to-end wiring is T029/T032
  (`T028-OPEN-03`).
- `T028-LIM-07` — The lease table is single-process and single-writer; shared or multi-process
  arbitration is unsupported and unclaimed (`T028-GAP-05`).
- `T028-LIM-08` — Strict declaration-level Doxygen execution remains `DOX-GAP-01` (T011/T037); T028
  supplies the declarations only.

## 10. Definition of done (implementation view)

The implementation stage is complete when the six work products exist, the T028 checkbox is marked,
the deterministic gate and named checks pass at the candidate revision with no existing case
weakened, `XCOM-SW-STIM-005`/`-006`/`-008` are recorded implemented and `XCOM-SW-STIM-003`/`-009`
partial, the register validators pass with REF-002 unchanged and nothing promoted, this record is
written, and a separate DeepSeek internal review records a passing verdict with no unresolved
blocking finding. This is **not** user acceptance, which remains T041; external Codex review and
acceptance are deferred until the `xcom-t026-t029-20260928` backlog completes.

## 11. External review and acceptance

External Codex review and user acceptance are deferred until the ordered backlog
`xcom-t026-t029-20260928` completes. This record makes no external-review or acceptance claim.

## 12. Internal review

A separate read-only DeepSeek internal review is recorded in
[`internal-review.json`](internal-review.json). The review re-derives the exact candidate inventory,
re-runs the deterministic gate and the focused suites, reads the production unit and the five test
suites, and records findings before any repair. Any repair would create a successor candidate and
require repeated verification and review; this record does not itself claim a passing re-review
beyond the recorded verdict.
