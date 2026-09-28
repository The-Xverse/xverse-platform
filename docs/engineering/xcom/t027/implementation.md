# T027 Implementation Record — Fail-Closed Pre-Emission Guard

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T027 (capability 007, slice `T-STIM`) |
| Stage / role | implementation → implementation record |
| Revision | 1 (fail-closed pre-emission guard) |
| Authorized baseline | `bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f` |
| Predecessors | T025 accepted bounded time authority, immutable validation permit, and session lifecycle; T026 bounded durable stimulation intent/outcome journal (present at the baseline, consumed read-only) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned at the workflow checkpoint) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | `docs/engineering/xcom/t027/internal-review.json` (separate read-only DeepSeek review, §12) |
| Package record | `reports/xcom-queue/t027-package.json` (produced by the deterministic package action) |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC006`, `ACC010`, `ACC011`, `ACC014`, `ACC015`); ADR-0016; ADR-0018; ADR-0019; ADR-0020; `specs/007-xcom-core/tasks.md` T027 |
| Maturity | Prototype-only bounded fail-closed pre-emission guard implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T027 implements the bounded slice required by the T027 task entry: *"Implement the fail-closed
pre-emission guard for schema, target, direction, action, time, quota, loop, service ownership,
permit/session identity, revocation, and expiry; rejection must not mutate operational state or emit a
normal-route item."*

The candidate adds one additive C++20 production unit, `xverse_xcom_stimulation_guard`
(`stimulation_guard.hpp`/`.cpp`), and twenty GoogleTest cases across five additive executables. The guard
evaluates one declared `StimulationRequest` against the immutable T025 `Permit` it was opened from and a
bounded declared `StimulationPolicy`, and returns exactly one of `Authorized`, `Rejected`, or `Failed`
with a closed `GuardReason`. It rejects a permit/session/plan identity, lifecycle, schema, direction,
interaction, target, action, service-ownership, quota, loop, or time mismatch; a rejection or failure
mutates no action tally, window tally, loop entry, permit, or policy byte and exposes no emission,
callback, route, injection, invocation, service-emulation, or lease entry point. Only `Authorized`
commits the bounded tallies and records the request lineage.

T027 implements **no** injection, service invocation, service emulation, exclusive lease, drain, close,
revoke, expiry, routing, observation tap, gateway, Protocol Buffers/gRPC, payload decoder, benchmark, or
later task. It emits nothing on a normal route.

`XCOM-SW-STIM-004` (fail-closed pre-emission validation) is **implemented** by this task.
`XCOM-SW-STIM-005` (loop bounding and conflict rejection) and `XCOM-SW-STIM-006` (scheduling, clock
authority, and tolerance) remain **partial**: only the guard-level, declaration-time bounded loop window,
declared-ownership check, and pre-emission time-policy check are realized; the atomic exclusive
service-emulation lease, the end-to-end reinjection loop, scheduled ordering/late-item behavior, and the
full unmapped-clock/loop matrix remain `XCOM-DU-018`/T028 and their matrix is T029 (`T027-GAP-01`…
`T027-GAP-05`).

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/stimulation_guard.hpp` | add | Public guard interface: closed `StimulationAction`/`GuardOutcome`/`GuardReason`/`GuardStatus` vocabularies with stable names/ranks and a total `outcome_of`; bounded payload-free `SchemaKey`/`ServiceOwner`/`StimulationPolicy`/`StimulationRequest`/`ResolvedTime`/`GuardDiagnostic`/`GuardSnapshot`; the closed action→interaction→direction bit table; and the `StimulationGuard` class with a compile-time payload-free/size rule |
| `src/xverse/xcom/src/stimulation_guard.cpp` | add | Deterministic check order (`NotOpen` → malformed → identity → lifecycle → schema → direction → interaction → target → action → ownership → quota → loop → time → commit), the bounded tallies and loop window, bounded diagnostic mapping, and the single-mutex check-then-commit |
| `src/xverse/xcom/CMakeLists.txt` | edit | Add `xverse_xcom_stimulation_guard` to `XVERSE_XCOM_RUNTIME_TARGETS`; define the library linked to `xverse::xcom_validation_session` and `xverse::xcom_core_types`; add five additive test executables with `t027-<kind>` labels; pass the committed header as a build-time read-only path to the negative suite |
| `tests/xcom/stimulation_guard/unit_tests.cpp` | add | `T27-TS-001`…`T27-TS-005` |
| `tests/xcom/stimulation_guard/mismatch_tests.cpp` | add | `T27-TS-006`…`T27-TS-012` |
| `tests/xcom/stimulation_guard/time_tests.cpp` | add | `T27-TS-013`…`T27-TS-015` |
| `tests/xcom/stimulation_guard/negative_tests.cpp` | add | `T27-TS-016`…`T27-TS-018` |
| `tests/xcom/stimulation_guard/concurrency_tests.cpp` | add | `T27-TS-019`, `T27-TS-020` |
| `docs/engineering/xcom/t010/unit-design.json` | edit | Flip the three realized `XCOM-DU-017` artifact-path status values from `planned` to `established` (status projection only; see §7.1) |
| `docs/engineering/xcom/t010/design-units.md` | edit | Deterministic projection regenerated from the model (see §7.1) |
| `docs/engineering/xcom/t027/requirements.md` | add | Plan-stage work product (unchanged) |
| `docs/engineering/xcom/t027/architecture.md` | add | Plan-stage work product (unchanged) |
| `docs/engineering/xcom/t027/detailed-design.md` | add | Plan-stage work product, with two implementation-stage reconciliations recorded in §7.2 |
| `docs/engineering/xcom/t027/unit-specifications.md` | add | Plan-stage work product (unchanged) |
| `docs/engineering/xcom/t027/verification-plan.md` | add | Plan-stage work product (unchanged) |
| `docs/engineering/xcom/t027/implementation.md` | add | This record |
| `docs/engineering/xcom/t027/internal-review.json` | add (review stage) | DeepSeek internal review |
| `specs/007-xcom-core/tasks.md` | edit | T027 checkbox marked complete (implementation stage only) |
| `reports/xcom-queue/t027-package.json` | add (package stage) | Exact-candidate package record |

No existing production header, source, target, test, label, command, or expected value is changed apart
from the derived T010 status projection. No `xdl/`, `proto/`, `src/xverse_xdl/`, `cmake/*.cmake`, root
`CMakeLists.txt`, `contracts/`, T025 `validation_session.*`, T026 `stimulation_journal.*`, or other task's
path is changed. No new admitted dependency is added; the unit links only the C++ standard library plus the
accepted T025 `xverse::xcom_validation_session` and T-CORE `xverse::xcom_core_types` contracts.

### 3.1 Changed symbols

- **New public enums**: `StimulationAction`, `GuardOutcome`, `GuardReason`, `GuardStatus`.
- **New public constants**: `kGuardMaxSchemas`, `kGuardMaxLoopWindow`, `kGuardMaxActionsPerSession`,
  `kGuardMaxActionsPerWindow`, `kDefinedStimulationActions`.
- **New public types**: `StimulationActionMask`, `SchemaKey`, `ServiceOwner`, `StimulationPolicy`,
  `StimulationRequest`, `ResolvedTime`, `GuardDiagnostic`, `GuardSnapshot`.
- **New public functions**: `to_stimulation_mask`, `is_defined_stimulation_action`,
  `is_single_stimulation_action`, `stimulation_action_name`, `precedence_rank(GuardReason)`,
  `outcome_of`, `reason_name`, `outcome_name`, `guard_status_name`, `interaction_bit`, `direction_bit`,
  `paired_interaction_bit`, `paired_direction_bit`.
- **New public class**: `StimulationGuard` with `open`, `authorize`, `snapshot`, `is_open`, `status`, and
  the nested alias `StimulationGuard::GuardSnapshot`.
- **No accepted symbol** is renamed, removed, or redefined; `validation::precedence_rank(Result)` and the
  T025/T-CORE vocabulary are reused read-only.

### 3.2 Realized check order and vocabulary

`GuardReason` is a closed, ordered vocabulary whose declaration index is its precedence rank: `NotOpen`
(0, `Failed`), `RejectedConfiguration` (1), `PermitMismatch` (2), `Revoked` (3), `Expired` (4),
`NotActive` (5), `SchemaMismatch` (6), `DirectionMismatch` (7), `InteractionMismatch` (8),
`TargetMismatch` (9), `ActionMismatch` (10), `OwnershipConflict` (11), `QuotaExhausted` (12), `LoopBound`
(13), `TimeOutOfWindow` (14), `TimeUnmapped` (15, `Failed`), `None` (16, `Authorized`). `authorize`
evaluates the checks in rank order under one per-guard mutex and commits only on success; a closed guard
returns `Failed`/`NotOpen` before any counter changes.

The closed action→interaction→direction table is `InjectSignal`↔`signal_state_update`/`produce`,
`InjectMessage`↔`message_event`/`produce`, `InvokeService`↔`service_request`/`request`,
`EmulateService`↔`service_response`/`respond`. The bounded constants are `kGuardMaxSchemas = 16`,
`kGuardMaxLoopWindow = 64`, `kGuardMaxActionsPerSession = 4096`, `kGuardMaxActionsPerWindow = 4096`, and
`kDefinedStimulationActions = 0x0F`.

### 3.3 Test units added

| Unit | Case | Suite | Label |
| --- | --- | --- | --- |
| `T27-TS-001` | `GuardAuthorizesNominalRequestAndSnapshot` | `unit` | `t027-unit` |
| `T27-TS-002` | `GuardActionInteractionDirectionTable` | `unit` | `t027-unit` |
| `T27-TS-003` | `GuardClosedVocabularyAndPrecedence` | `unit` | `t027-unit` |
| `T27-TS-004` | `GuardStatusDeterminismAndNoMutation` | `unit` | `t027-unit` |
| `T27-TS-005` | `GuardPolicyValidationMatrix` | `unit` | `t027-unit` |
| `T27-TS-006` | `GuardIdentityAndPlanMatrix` | `mismatch` | `t027-mismatch` |
| `T27-TS-007` | `GuardLifecycleMatrix` | `mismatch` | `t027-mismatch` |
| `T27-TS-008` | `GuardSchemaAndTargetMatrix` | `mismatch` | `t027-mismatch` |
| `T27-TS-009` | `GuardActionDirectionMatrix` | `mismatch` | `t027-mismatch` |
| `T27-TS-010` | `GuardServiceOwnershipMatrix` | `mismatch` | `t027-mismatch` |
| `T27-TS-011` | `GuardQuotaMatrix` | `mismatch` | `t027-mismatch` |
| `T27-TS-012` | `GuardLoopBoundMatrix` | `mismatch` | `t027-mismatch` |
| `T27-TS-013` | `GuardScheduledTimeWindowMatrix` | `time` | `t027-time` |
| `T27-TS-014` | `GuardUnmappedClockFailsClosed` | `time` | `t027-time` |
| `T27-TS-015` | `GuardImmediateLabelingMatrix` | `time` | `t027-time` |
| `T27-TS-016` | `GuardRejectionZeroMutationAndNoEmission` | `negative` | `t027-negative` |
| `T27-TS-017` | `GuardClosedGuardRejects` | `negative` | `t027-negative` |
| `T27-TS-018` | `GuardBoundsConfigMatrix` | `negative` | `t027-negative` |
| `T27-TS-019` | `GuardBoundedDeterministicConcurrency` | `concurrency` | `t027-concurrency` |
| `T27-TS-020` | `GuardConcurrentRejectionNoMutation` | `concurrency` | `t027-concurrency` |

## 4. Deterministic gate and build evidence

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T027 bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f
```

The gate's configure reuses the `build/fabro-t027` cache seeded (A-1) with the previously admitted
`XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` cache
values (named by role only; no ambient path or network resolution was added and no admission check was
weakened). Observed result at the implementation stage: `ok` with the six T027 work products present, the
T027 checkbox marked complete, at least one `src/xverse/xcom/` and one `tests/` path changed, the
configure/build/discovery/full-`ctest` sequence exiting 0, and `git diff --check` clean.

| Item | Value |
| --- | --- |
| Configure (A-1 cache seed) | `cmake -S . -B build/fabro-t027 -G Ninja -DCMAKE_BUILD_TYPE=Debug -D<three admitted A-1 cache values>` (exit 0) |
| Configure (plain, reused by the gate) | `cmake -S . -B build/fabro-t027 -G Ninja -DCMAKE_BUILD_TYPE=Debug` (exit 0) |
| Build | `cmake --build build/fabro-t027 --parallel 4` (exit 0, no warning emitted under `-Werror`) |
| Toolchain | host GNU C++ 11.4.0 (`-std=c++20`) under the T012 `-Wall -Wextra -Wpedantic -Werror` contract |
| Discovery | `ctest --test-dir build/fabro-t027 -N` → `Total Tests: 344` (baseline 324 + 20) |
| Full suite | `ctest --test-dir build/fabro-t027 --output-on-failure --parallel 4` → `100% tests passed, 0 tests failed out of 344` |
| T027 suites | `ctest -R XcomStimulationGuard` → `100% tests passed, 0 tests failed out of 20` across the five `t027-*` labels |
| Build contract | `xcom_build_contract` passes with the added runtime target |
| Diff hygiene | `git diff --check bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f --` → clean |

Additivity: the discovered count is the T027 baseline 324 plus exactly the 20 new T027 cases; every
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

- **Fail-closed decision and precedence (CHK-06…CHK-13, NEG-04…NEG-25)** — `authorize` evaluates the
  closed `GuardReason` rank order and returns on the first failing check; only the full-pass path reaches
  the commit. `T27-TS-005`…`T27-TS-015` realize the policy/open, identity, lifecycle, schema/target,
  action/direction, ownership, quota, loop, and time rows of `detailed-design.md` §5; every non-matching
  row asserts the exact reason.
- **Zero mutation on rejection (CHK-14, NEG-26)** — `authorize` advances `actions_authorized_`,
  `window_actions_`, and the loop window only after every check passes. The `reject`/`fail` paths advance
  only the observable `evaluations_`/`rejections_`/`failures_` counters; `T27-TS-016` and `T27-TS-020`
  assert the pre/post snapshot is operationally identical for every rejection family and under concurrent
  rejection. A closed guard returns before any counter changes (`T27-TS-017`).
- **Zero emission surface (CHK-15, CHK-21, NEG-27)** — the guard header declares no emission, callback,
  route, injection, invocation, service-emulation, or lease member; `T27-TS-016` reads the committed
  header **and implementation source**, strips comments, and asserts that no forbidden emission vocabulary
  appears at a word boundary, and asserts the bounded payload-free sizes. The guard produces a decision
  only.
- **Closed open precondition (CHK-06, CHK-18, NEG-33, `T027-SR-021`)** — a guard opened from an invalid,
  zero, or permit-inconsistent policy returns `RejectedConfiguration` and is left closed with zero
  tallies, so it authorizes no request; a rejected re-open of an already-open guard closes it rather than
  retaining the prior binding. `open` additionally rejects a declared service owner whose endpoint tag is
  not a valid tag. `T27-TS-005`, `T27-TS-018` realize every row.
- **Exact identity and plan binding (CHK-16, NEG-06, NEG-07)** — session, permit, and plan identity and
  the bound policy digest are compared to the immutable permit before any other work; `T27-TS-006`
  realises every row of `detailed-design.md` §5.6 and the policy-digest mismatch is `RejectedConfiguration`
  at open (`T027-SR-021`).
- **Payload-free bounded values (CHK-05, CHK-20, NEG-03)** — every value type exposes no payload, address,
  or free-form member by declaration inspection; the header `static_assert`s reject constructibility from
  a byte container or free-form text and bound each value's size, and `negative_tests.cpp` replicates them
  as a non-vacuous compile-time negative test that fails the build if a payload-accepting constructor or an
  unbounded value is added. The absence of a payload-bearing member is established by declaration
  inspection, not claimed by the compile-time assertions.
- **Bounded time policy (CHK-13, CHK-19, NEG-22…NEG-25, NEG-35)** — `authorize` consumes a caller-resolved
  `ResolvedTime`; a non-`Ok` resolution or a domain that differs from the permit validity domain is
  `Failed`/`TimeUnmapped`, an out-of-window value is `Rejected`/`TimeOutOfWindow`, and an immediate request
  is explicitly labeled and interpreted in the validity domain. The guard calls no `TimeAuthority`, compares
  no raw mismatched clocks, and performs no I/O (`T27-TS-013`…`T27-TS-015`, `T27-TS-014` lineage).
- **Determinism and bounded concurrency (CHK-17, CHK-18, NEG-28, NEG-29, NEG-36)** — the vocabulary is
  closed with stable names/ranks and a total `outcome_of`; `T27-TS-004` proves three identical repeated
  runs and a non-mutating rejection; `T27-TS-019` proves four independent guards reproduce the
  single-threaded golden sequence and final snapshot across three runs; `T27-TS-020` proves concurrent
  rejections of one guard leave the operational snapshot unchanged and never exceed the declared bound
  (≤ 4 threads, ≤ 16 evaluations per guard, no wall-clock verdict, no callback).
- **Offline and local-only (CHK-19, NEG-30)** — the unit includes only the C++ standard library plus
  `validation_session.hpp`, `contract.hpp`, and `result.hpp`; a forbidden-API inspection finds no
  network/socket/resolver/TLS, ambient/secret, dynamic-load, subprocess, filesystem, or legacy access; the
  guard performs no I/O.
- **Public safety (CHK-21, NEG-31)** — a scan of the changed files finds no credential, private address,
  real or proprietary payload, environment-specific absolute path, or sensitive value; the only absolute
  paths are inside git-ignored build output and never appear in committed evidence.
- **Doxygen (CHK-22)** — every public declaration carries `\brief` plus `\ownership`, `\lifetime`,
  `\thread_safety`, and `\failure` where applicable; the file block names T027 and `\ingroup xcom_stim`;
  the admitted documentation configuration is unchanged.

## 6. Requirement-to-change-to-check traceability

| Requirement | Realized by | Check(s) |
| --- | --- | --- |
| T027-SR-001 | new additive unit + one new runtime target + five additive test executables | CHK-02, CHK-04, CHK-18 |
| T027-SR-002 | includes only standard headers plus `validation_session.hpp`/`contract.hpp`/`result.hpp`; links `xverse::xcom_validation_session` + `xverse::xcom_core_types` | CHK-03, CHK-19 |
| T027-SR-003 | closed `StimulationAction`/`GuardOutcome`/`GuardReason`/`GuardStatus` with stable names/ranks and total `outcome_of` | CHK-17, CHK-20 |
| T027-SR-004 | bounded payload-free values + compile-time constructor/size rule + declaration inspection | CHK-05, CHK-20 |
| T027-SR-005 | identity/plan checks at rank 2 | CHK-06, CHK-16 |
| T027-SR-006 | lifecycle checks at ranks 3–5 | CHK-07 |
| T027-SR-007 | schema/direction/interaction/target checks at ranks 6–9 | CHK-08, CHK-09 |
| T027-SR-008 | action check at rank 10 | CHK-09 |
| T027-SR-009 | per-session/per-window quota check at rank 12 with commit-only tally advance | CHK-10 |
| T027-SR-010 | bounded loop-detection window at rank 13 with commit-only lineage | CHK-12 |
| T027-SR-011 | declaration-level ownership check at rank 11 with no lease | CHK-11 |
| T027-SR-012 | time policy at ranks 14–15 with no authority call | CHK-13, CHK-19 |
| T027-SR-013 | non-mutating `reject`/`fail` paths and commit-only success | CHK-14, CHK-15 |
| T027-SR-014 | closed deterministic vocabulary and precedence | CHK-17 |
| T027-SR-015 | one per-guard mutex; bounded deterministic concurrency | CHK-18 |
| T027-SR-016 | standard-library + accepted-header includes; no I/O | CHK-19 |
| T027-SR-017 | public-safe source, tests, and work products | CHK-21 |
| T027-SR-018 | Doxygen on every public declaration; `\ingroup xcom_stim` | CHK-22 |
| T027-SR-019 | registers re-validated; `XCOM-SW-STIM-004` implemented, `XCOM-SW-STIM-005`/`-006` partial; REF-002 unchanged | CHK-23 |
| T027-SR-020 | deterministic gate; clean diff; checkbox marked only in this stage | CHK-24 |
| T027-SR-021 | independent `open` policy validation with no guaranteed authorisation | CHK-06, CHK-18 |
| T027-SR-022 | no emission/callback/route/injection/invocation/emulation/lease surface | CHK-15 |

Check and negative-case identifiers are the accepted [`verification-plan.md`](verification-plan.md)
§4–§5.

## 7. Plan-stage reconciliation (recorded, not silently edited)

The pre-code work products are the accepted plan for this task. Three implementation facts required an
honest, recorded reconciliation rather than editing an accepted predecessor or silently departing from
the plan. No requirement or check is weakened.

### 7.1 T010 `XCOM-DU-017` artifact-path status projection

`docs/engineering/xcom/t027/requirements.md` §7.2 listed `docs/engineering/xcom/t010/**` as consumed
read-only. Implementing the unit realizes the three `XCOM-DU-017` paths that the T010 model recorded as
`planned`, and `scripts/validate_xcom_unit_design.py --verify` fails closed with `PATH_INVALID` when a
`planned` path exists (CHK-23 requires the validators to pass). Following the repository convention
precedented by T026 (commit `c4c8225` family) and commit `2f08355`, T027 flipped the status field of
exactly those three entries in `docs/engineering/xcom/t010/unit-design.json` from `planned` to
`established` and regenerated `docs/engineering/xcom/t010/design-units.md` from the model; no unit
identity, ownership, lifetime, thread-safety, bounds, failure semantics, planned evidence, or Doxygen
obligation is changed. This is a derived status projection update, not a design rewrite or weakening.

### 7.2 Schema/target reason precedence over the undifferentiated malformed clause

`detailed-design.md` §4.2 step 2 originally assigned `RejectedConfiguration` to an invalid schema or
target/interface tag, while `T027-SR-007` and `verification-plan.md` CHK-08/NEG-05 require
`SchemaMismatch` for an empty/over-long/undeclared schema and `TargetMismatch` for a target/interface
that differs from the permit. The requirement and its named checks take precedence (`requirements.md`
§1.2): `authorize` validates schema at rank 6 and target/interface at rank 9 with those specific reasons,
and `RejectedConfiguration` (rank 1) is reserved for an undefined/composite/out-of-vocabulary action, a
zero `request_id`, and an invalid or immediate-mismatched clock domain. §4.2 step 2 was amended to record
this reconciliation; no requirement, check, expected value, or test was weakened. The related §5.6 row for
a policy plan-digest mismatch was split: a request-digest mismatch is `PermitMismatch` at authorize, while
a policy-digest mismatch is `RejectedConfiguration` at open (`T027-SR-021`).

### 7.3 Policy-bound source and public-surface size versus `XCOM-DU-017` (`T027-OPEN-01`)

The accepted T010 `XCOM-DU-017` records the loop-detection window and the per-session/per-interval action
limits as "declared in validation permit" and counts six documented/public elements. The accepted T025
`Permit` exposes `allowed_actions` over the lifecycle `Action` vocabulary and a `Quota` list, and carries
no stimulation-action, schema, interface, or loop-window declaration. T027 therefore supplies a bounded
session-scoped `StimulationPolicy` value, derived by the caller from the digest-bound plan, whose
`plan_digest`, interface, target, and validity domain are cross-checked against the immutable permit at
open. The realized public surface (vocabularies, bounded values, table helpers, and the guard class) is
larger than the six-element T010 plan; this delta is recorded here rather than by editing the accepted
T010 artifact, consistent with `T027-OPEN-01`. No accepted bound, ownership, lifetime, or thread-safety
model is changed.

## 8. Negative cases realized

| NEG | Realized case | Observed result |
| --- | --- | --- |
| NEG-01 | `git diff --name-only`, `ctest -N` | only T027 paths plus the T010 status projection; existing targets/tests unchanged |
| NEG-02 | include/link inspection | only the standard library plus `validation_session.hpp`/`contract.hpp`/`result.hpp`; no redefined identity/digest/interaction type; no new dependency |
| NEG-03 | header `static_assert`s + `negative_tests.cpp` compile-time rule + declaration inspection | a payload-accepting constructor or unbounded value fails the build; no payload member by declaration inspection |
| NEG-04 | `T27-TS-009` | a zero action is `RejectedConfiguration`; a composite action is `RejectedConfiguration`; a single out-of-vocabulary action bit (`0x10`) is `RejectedConfiguration` at rank 1, never `DirectionMismatch` |
| NEG-05 | `T27-TS-005`, `T27-TS-008`, `T27-TS-018` | empty/over-long schema tags are `SchemaMismatch`; invalid policy schema tags are `RejectedConfiguration` at open |
| NEG-06, NEG-07 | `T27-TS-006` | a foreign session/permit identity is `PermitMismatch`; a request plan-digest mismatch is `PermitMismatch`; a policy plan-digest mismatch is `RejectedConfiguration` at open |
| NEG-08 | `T27-TS-007` | a revoked session is `Revoked` with no mutation |
| NEG-09 | `T27-TS-007` | an expired session is `Expired` with no mutation |
| NEG-10 | `T27-TS-007` | every other non-`active` state is `NotActive` with no mutation |
| NEG-11 | `T27-TS-008` | an undeclared schema is `SchemaMismatch` |
| NEG-12 | `T27-TS-002`, `T27-TS-009` | an inconsistent direction is `DirectionMismatch` |
| NEG-13 | `T27-TS-002`, `T27-TS-009` | an inconsistent or policy-excluded interaction is `InteractionMismatch` |
| NEG-14 | `T27-TS-008` | a target/interface mismatch is `TargetMismatch` |
| NEG-15 | `T27-TS-009` | a defined action outside the policy is `ActionMismatch` |
| NEG-16 | `T27-TS-011`, `T27-TS-016` | per-session exhaustion is `QuotaExhausted` with no mutation |
| NEG-17 | `T27-TS-011` | per-window exhaustion is `QuotaExhausted`; the window resets at `action_window` |
| NEG-18 | `T27-TS-012`, `T27-TS-016` | a prohibited reinjection is `LoopBound` with no mutation |
| NEG-19 | `T27-TS-005`, `T27-TS-018` | a zero/over-maximum loop window or an over-full schema table is `RejectedConfiguration` |
| NEG-20 | `T27-TS-010` | a missing/mismatched owner or generation is `OwnershipConflict` |
| NEG-21 | `T27-TS-010` | an emulation without a declared owner or with emulation disabled is `OwnershipConflict` |
| NEG-22 | `T27-TS-015` | an immediate request with a non-validity clock domain or a scheduled request with an invalid domain is `RejectedConfiguration` |
| NEG-23 | `T27-TS-014`, `T27-TS-016` | an absent/unmapped/out-of-tolerance or domain-mismatch resolution is `Failed`/`TimeUnmapped` |
| NEG-24 | `T27-TS-013` | an out-of-window resolved time is `Rejected`/`TimeOutOfWindow` |
| NEG-25 | `T27-TS-015`, `T27-TS-013` | a mislabeled immediate or out-of-domain request is `RejectedConfiguration`; an immediate out-of-window time is `TimeOutOfWindow` |
| NEG-26 | `T27-TS-004`, `T27-TS-016`, `T27-TS-020` | the operational snapshot is unchanged on every rejection, including concurrently |
| NEG-27 | `T27-TS-016` | the comment-stripped guard header exposes no emission/action/lease vocabulary |
| NEG-28 | `T27-TS-003`, `T27-TS-004` | stable names/ranks/`outcome_of`; three identical repeated runs |
| NEG-29 | `T27-TS-019`, `T27-TS-020` | ≤ 4 threads, ≤ 16 evaluations per guard, no callback, no wall-clock verdict |
| NEG-30 | forbidden-API inspection + offline build | no forbidden element; no new dependency |
| NEG-31 | public-safety scan | no forbidden content in committed files |
| NEG-32 | gate + diff + §7 | no non-T027 path beyond the recorded T010 projection; checkbox marked only in this stage; REF-002 unchanged |
| NEG-33 | `T27-TS-005`, `T27-TS-018` | every zero/over-maximum/inconsistent policy bound is `RejectedConfiguration` with the guard left closed |
| NEG-34 | `T27-TS-017` | a closed guard returns `Failed`/`NotOpen` with no mutation |
| NEG-35 | `T27-TS-014` + inspection | the guard calls no time authority, compares no raw clocks, and performs no I/O |
| NEG-36 | `T27-TS-011`, `T27-TS-019`, `T27-TS-020` | only `Authorized` advances a tally; concurrent runs never exceed the declared bounds |

## 9. Limitations and gaps

- `T027-LIM-01` — Prototype only: passing the tests proves no runtime, end-to-end route, compatibility,
  parity, or production-readiness claim; not user-accepted (T041) and not externally reviewed.
- `T027-LIM-02` — `XCOM-SW-STIM-005` is **partial**: only the guard-level declaration-time bounded loop
  window and declared-ownership check are realized; the exclusive service-emulation lease and end-to-end
  reinjection-loop enforcement are `XCOM-DU-018`/T028 and their matrix is T029 (`T027-GAP-01`,
  `T027-GAP-04`).
- `T027-LIM-03` — `XCOM-SW-STIM-006` is **partial**: only the guard-level pre-emission time-policy check
  is realized; scheduled ordering, late-item behavior, and the end-to-end unmapped-clock/tolerance
  behavior are T028/T029 (`T027-GAP-02`).
- `T027-LIM-04` — The guard produces a decision and exposes no emission path; the end-to-end
  "zero normal-route item after rejection" proof requires the T028 action path and is closed by T029
  (`T027-GAP-03`).
- `T027-LIM-05` — Concurrency is a single declared writer per guard; shared or multi-process guards are
  unsupported and unclaimed (`T027-GAP-05`).
- `T027-LIM-06` — Strict declaration-level Doxygen execution remains `DOX-GAP-01` (T011/T037); T027
  supplies the declarations only.
- `T027-LIM-07` — Service-ownership validation is declaration-level; the guard acquires, holds, releases,
  drains, and quarantines no lease (`T027-GAP-04`).

## 10. Definition of done (implementation view)

The implementation stage is complete when the six work products exist, the T027 checkbox is marked, the
deterministic gate and named checks pass at the candidate revision with no existing case weakened,
`XCOM-SW-STIM-004` is implemented and `XCOM-SW-STIM-005`/`XCOM-SW-STIM-006` are recorded partial, the
register validators pass with REF-002 unchanged and nothing promoted, this record is written, and a
separate DeepSeek internal review records a passing verdict with no unresolved blocking finding. This is
**not** user acceptance, which remains T041; external Codex review and acceptance are deferred until the
`xcom-t026-t029-20260928` backlog completes.

## 11. External review and acceptance

External Codex review and user acceptance are deferred until the ordered backlog
`xcom-t026-t029-20260928` completes. This record makes no external-review or acceptance claim.

## 12. Internal review

A separate read-only DeepSeek internal review is recorded in
[`internal-review.json`](internal-review.json) (see §12 of the run goal and `T027-SR-020`). The review
re-derives the exact candidate inventory, re-runs the gate and the focused suites, reads the production
unit and the five test suites, and records findings before any repair. Any repair would create a
successor candidate and require repeated verification and review; this record does not itself claim a
passing re-review beyond the recorded verdict.

## 13. Repair record (review revision 2, `T027-IR2-F01` and observations)

Review revision 2 returned `fail` with one medium finding (`T027-IR2-F01`) and three non-blocking
observations. This repair closes the finding without weakening any accepted requirement, check, or test,
and keeps the baseline `bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f` lineage.

### 13.1 `T027-IR2-F01` — rank-1 malformed-action check did not bind an out-of-vocabulary bit

- **Root cause.** The rank-1 malformed-request check tested only `is_single_stimulation_action`, not
  `is_defined_stimulation_action`. A single undefined action bit (for example
  `static_cast<StimulationAction>(0x10U)`) therefore passed rank 1 and reached rank 7, where
  `paired_direction_bit` returns `0`, so the guard reported `DirectionMismatch` instead of the declared
  `RejectedConfiguration`.
- **Correction.** `authorize` now rejects unless the action mask is both defined and single:
  `if (!is_defined_stimulation_action(action_mask) || !is_single_stimulation_action(action_mask))` →
  `reject(GuardReason::RejectedConfiguration)`. A zero, composite, or out-of-vocabulary action is now
  classified as malformed at rank 1 and is never reported as a later direction/interaction/action-table
  mismatch, so the declared precedence (`T027-SR-014`) holds. Fail-closed behaviour is unchanged: the
  outcome is `Rejected` with no mutation and no emission.
- **Reason-vocabulary reconciliation (`T027-IR2-OBS-01`).** The design, implementation, and tests already
  assigned `RejectedConfiguration` to a zero/composite/out-of-vocabulary action, and the `GuardReason`
  declaration documents `ActionMismatch` as "the action is defined but not declared allowed". The
  outlier was the `T027-SR-008` prose, which assigned `ActionMismatch` to an undefined/composite action.
  `T027-SR-008` was therefore reconciled to the single realized reason: a zero/composite/out-of-vocabulary
  action is `RejectedConfiguration`; a defined action not declared allowed is `ActionMismatch`. No
  requirement, check, expected value, or test is weakened; the fail-closed obligation is unchanged.
- **Coverage.** `tests/xcom/stimulation_guard/mismatch_tests.cpp` (`T27-TS-009`) now authorizes a request
  with action `static_cast<StimulationAction>(0x10U)` and asserts `Rejected` +
  `GuardReason::RejectedConfiguration` with an unchanged operational snapshot. `requirements.md`
  (`T027-SR-008`), `detailed-design.md` (§4.2 step 2 and §5.3), `verification-plan.md` (CHK-09),
  `unit-specifications.md` (`T27-TS-009`), and this record were updated to the same reason.

### 13.2 `T027-IR2-OBS-02` — per-window budget semantics documented

The per-window budget binds only while `max_actions_per_window < action_window`; when
`max_actions_per_window >= action_window` the ordinal `window_actions` tally resets at `action_window`
before the window bound can be reached, so only the per-session budget caps authorizations. The
per-session budget always bounds every authorized action, so no combination is unbounded, and policy
validation is intentionally left unchanged (rejecting the non-binding combination would break the
accepted `T27-TS-011` cases and weaken them). `detailed-design.md` §5.4 now records the invariant and the
host obligation (`action_window > max_actions_per_window` for the per-window budget to bind).

### 13.3 `T027-IR2-OBS-03` — in-tree concurrent-authorization bound

`tests/xcom/stimulation_guard/concurrency_tests.cpp` adds
`XcomStimulationGuardConcurrency.GuardConcurrentAuthorizationWithinQuota` (`T27-TS-019`, CHK-18): four
joined threads submit 16 bounded evaluations each against one guard with a declared per-session quota of
`7`; exactly `7` outcomes are `Authorized`, the remaining `25` are `Rejected`, and
`snapshot().actions_authorized == 7` with `evaluations == 64`. This directly evidences the CHK-18
"≤ `max_actions_per_session` authorized actions" bound rather than inferring it.

### 13.4 Closure evidence

- Deterministic gate at this candidate: `xcom_feature_gate.py verify T027
  bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f` reports `ok` (see the package record for the exact
  `changed_paths`/`checks`).
- Focused `ctest -L t027-` at this candidate: **21/21 cases pass** across `t027-unit` (5),
  `t027-mismatch` (7), `t027-time` (3), `t027-negative` (3), and `t027-concurrency` (3, including the new
  quota case). No prior case was removed or weakened.
- Independent out-of-repo probe (compiled with `-std=c++20 -Wall -Wextra -Wpedantic -Werror`, linked
  against the built `xverse_xcom_stimulation_guard`/`xverse_xcom_validation_session`/
  `xverse_xcom_core_types` archives) now reports
  `undefined single-bit action -> outcome=Rejected reason=RejectedConfiguration`,
  `concurrent: authorized=7 rejected=25 snapshot_actions=7`, and `T027 IR probe: all checks passed`;
  this is the same probe that exposed `T027-IR2-F01` at review revision 2.
- Candidate file digests (SHA-256) at this repair:
  - `src/xverse/xcom/src/stimulation_guard.cpp` —
    `38ad7f9b4311ffbd3e71cb447fbff7c8ee7b5f30e12ddbbabd89e4c27546caf4`
  - `src/xverse/xcom/include/xverse/xcom/stimulation_guard.hpp` —
    `54c72c81ca08d77ac34b2a0bf00902b38f035ad041b1fc8acf1cf3cb91c4c7ad` (unchanged)
  - `tests/xcom/stimulation_guard/mismatch_tests.cpp` —
    `0db5f08faa2821350f05c4c1a9c77dc5fb9fa350bc1e467e6ec3ca4b1f664140`
  - `tests/xcom/stimulation_guard/concurrency_tests.cpp` —
    `fd406180ddeaa47eb9876a06ba37af26e7a1291085a41cd7dc6bef6831931eef`

This repair creates a successor candidate; repeated independent verification and a fresh read-only
internal review are required, and no acceptance is claimed here (external Codex review and user
acceptance remain deferred until the backlog completes).
