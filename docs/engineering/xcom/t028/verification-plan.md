# T028 Verification Plan — Named Checks, Commands, Negative Cases, and Evidence (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T028 (capability 007, slice `T-STIM`) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 (guarded actions and exclusive service-emulation lease) |
| Baseline revision | `c518c5e4fcb2055666db25cb62018769e7f56ae4` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope, plus the repository-owned Fabro gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
T028's executable checks are five new GoogleTest executables under `tests/xcom/stimulation_actions/`, the
unchanged existing suites that prove additivity, and the source inspections that prove the guarded decision
order, journal-before-emission ordering, exclusive lease behaviour, completion mechanics, non-mutation,
zero emission, bounds, determinism, offline behaviour, public safety, and governance; the governance checks
are the deterministic gate and the T007–T010 register validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 ${XVERSE_FABRIC_ROOT}/automation/xcom_feature_gate.py verify T028 c518c5e4fcb2055666db25cb62018769e7f56ae4
```

For T028 this gate requires:

- the six work products
  `docs/engineering/xcom/t028/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T028 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- at least one changed path under `src/xverse/xcom/` and at least one changed path under `tests/`
  (satisfied by the new action-path/lease unit and its suites);
- `cmake -S . -B build/fabro-t028 -G Ninja -DCMAKE_BUILD_TYPE=Debug`,
  `cmake --build build/fabro-t028 --parallel 4`, a non-empty `ctest --test-dir build/fabro-t028 -N`, and
  `ctest --test-dir build/fabro-t028 --output-on-failure --parallel 4` all exit 0;
- `git diff --check c518c5e4fcb2055666db25cb62018769e7f56ae4 --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the admitted offline inputs. As accepted
for T012–T016 and T019–T027, if the gate's plain configure fails closed at the T025 test-toolchain
admission check, the only permitted resolution is the narrow A-1 cache seeding already recorded by those
slices: one configure carrying `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously admitted cache values seeds the gate's own
git-ignored `build/fabro-t028` cache; the gate's unmodified configure/build/`ctest` sequence then reuses it.
The hash-verified preflight is unchanged, no ambient path or network resolution is added, no admission check
is weakened, and the admitted input **values** are recorded by name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse c518c5e4fcb2055666db25cb62018769e7f56ae4
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only c518c5e4fcb2055666db25cb62018769e7f56ae4 --
git diff --check c518c5e4fcb2055666db25cb62018769e7f56ae4 --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t028 -N
ctest --test-dir build/fabro-t028 -R "XcomStimulationActions" --output-on-failure
ctest --test-dir build/fabro-t028 -R "xcom_core_types|xcom_lifecycle|xcom_provider_loopback|xcom_activation_plan|xcom_validation|xcom_observation|xcom_core_matrix|xcom_stimulation_journal|xcom_stimulation_guard" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with
the shared T007–T010 artifacts unchanged in substance. The existing core, lifecycle, provider,
activation-plan, validation, observation, core-matrix, stimulation-journal, and stimulation-guard suites
must pass unchanged, proving additivity. Executed sanitizer/static-analysis/Doxygen/benchmark measures and
the delivery bundle remain with T035–T040; this plan requires the T028 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T028 entry exists and states the guarded injection/invocation/emulation and lifecycle-completion scope |
| CHK-02 | Changed-path boundary | `git diff --name-only <baseline> --`; `git ls-files --others --exclude-standard` | only the §7.1 paths appear; no T025/T026/T027 source/test byte, no `xdl/`, `proto/`, `src/xverse_xdl/`, `cmake/*.cmake`, or root `CMakeLists.txt` change; no other task's path |
| CHK-03 | Dependency and contract reuse | inspect `stimulation_actions.hpp` includes and the CMake link line | the unit includes only the C++ standard library plus `validation_session.hpp`, `stimulation_journal.hpp`, `stimulation_guard.hpp`, and the accepted core headers; no new third-party dependency; no identity/digest/diagnostic/interaction/origin/action type is redefined |
| CHK-04 | Build wiring, discovery, additivity | build; `ctest -N`; run the five T028 executables and the preserved suites | `xverse_xcom_stimulation_actions` is the only new runtime target; the five new executables discover 22 cases (the 20 declared test units plus the two additional lifecycle case functions `LifecycleTerminalEvidenceIncompleteNeverClosed` and `LifecycleNonActiveCompletionFailsClosed`); every existing target/test name/label/command and the discovered count of existing tests are preserved |
| CHK-05 | Bounded payload-free values | inspect the value types; run `T28-TS-018` | every value type exposes no payload/value/address/free-form/unbounded member by declaration inspection; a non-vacuous compile-time negative assertion fails the build if a payload-accepting constructor or an unbounded value is added; no value retains a payload |
| CHK-06 | Open, config, and precondition | run `T28-TS-005`, `T28-TS-017` | every row of `detailed-design.md` §5.1 matches; a closed path, invalid config, malformed request, capacity exhaustion, and non-active session decline before any guard call, journal record, or emission |
| CHK-07 | Guard-decision mapping | run `T28-TS-002` | every guard `Rejected`/`Failed` maps to a non-emitting, non-journaling `ActionStatus` with the guard reason preserved; a guard decline acquires no lease, so the lease table (including its acquisition and release accounting) is byte-identical; the guard is evaluated exactly once |
| CHK-08 | Journal-before-emission and outcomes | run `T28-TS-001`, `T28-TS-014` | the intent is durable before the single emitter call; only a durable *delivered* outcome maps to `Emitted`; a durable host `Rejected`/`Unavailable` maps to `EmissionRejected`/`EmissionUnavailable`; an intent without a durable outcome maps to `EvidenceIncomplete` and is never reported as success |
| CHK-09 | Synthetic provenance | run `T28-TS-003` | every emitted item carries `OriginKind::validation_tool` and the exact tool/permit/session/plan/request/correlation/causation identity; no path emits a differently classified item |
| CHK-10 | Lease identity binding | run `T28-TS-006`, `T28-TS-010` | the lease key binds session, endpoint, generation, and plan digest; a foreign/superseded identity is `LeaseConflict` with `SessionMismatch`/`GenerationMismatch`/`PlanMismatch`; a superseded generation neither authorizes nor conflict-blocks |
| CHK-11 | Lease conflict and capacity | run `T28-TS-007`, `T28-TS-020` | a same-generation or same-`(endpoint, session)` conflict and an over-capacity acquisition return `Conflict`/`CapacityExhausted` with no mutation; a concurrent race yields exactly one winner |
| CHK-12 | Lease release and quarantine | run `T28-TS-008` | an exact-owner release succeeds; unknown/`NotHeld`/`AlreadyReleased` and quarantine handle correctly; a failed release/quarantine mutates no entry |
| CHK-13 | Lease expiry and clock domain | run `T28-TS-009`, `T28-TS-015` | an elapsed lease becomes inactive and no longer blocks; a foreign-domain value is never compared; an unmapped/out-of-tolerance resolution fails closed before emission and before journaling; no authority call |
| CHK-14 | Loop bounding | run `T28-TS-012`, `T28-TS-016` | a prohibited reinjection is `Rejected` with no emission and no journal; `causation_id == 0` is never a loop; the lineage window never exceeds its declared bound and evicts the oldest |
| CHK-15 | Scheduling, ordering, and late policy | run `T28-TS-011`, `T28-TS-012` | a scheduled action enters the bounded queue in the declared order; a full queue is `CapacityExhausted` before any guard call; `drain` completes at most `max_drain_steps` due actions; `RejectLate`/`DiscardLate` emit nothing |
| CHK-16 | Lifecycle completion | run `T28-TS-013`, `T28-TS-014` | `drain`/`close`/`revoke`/`expire`/`mark_evidence_incomplete` return the declared outcomes; pending actions are cancelled or drained as declared; every held lease is released or quarantined; an incomplete intent forces `EvidenceIncomplete` and never `Closed`; a due action whose intent append fails is surfaced in `CompletionReport.failed` and never reported as a clean `Drained`/`Closed`; a non-active, non-terminal `drain`/`close` cancels every pending action with zero emission and never returns `Drained`/`Closed` |
| CHK-17 | Determinism and closed vocabularies | run `T28-TS-004` | every vocabulary is closed with stable names, ranks, and totals; repeated bounded runs produce identical statuses, lease states, completion outcomes, and snapshots |
| CHK-18 | Bounds, concurrency, and no-callback | run `T28-TS-019`, `T28-TS-020`; inspect `detailed-design.md` §7 and the tests | ≤ 4 threads, ≤ 64 bounded operations per case, ≤ `max_pending_actions` pending, ≤ `max_active_leases` leases, ≤ `max_lineage_entries` lineage, no callback under a lock, no wall-clock verdict; a declared guard quota is never exceeded under concurrency; a lease race has exactly one winner |
| CHK-19 | Offline, local-only, no I/O, no new dependency | forbidden-API source scan; successful offline configure/build; inspect the unit | no network/socket/resolver/TLS, ambient/secret lookup, dynamic-load, subprocess, filesystem, or legacy access; the action path calls no time authority and owns no I/O boundary; no TCP listener; no new admitted dependency |
| CHK-20 | No payload retention or export primitive | forbidden-vocabulary scan of the changed source/tests; run `T28-TS-018` | no payload/value log, decoder, redaction profile, dashboard, storage, query, presentation, export, OpenTelemetry, or adapter primitive appears in the T028 surface; the call-scoped payload view is retained nowhere |
| CHK-21 | Non-mutation, zero emission, and public safety | run `T28-TS-016`, `T28-TS-017`; scan the changed source, tests, and work products | for every decline family the pre/post snapshot is byte-identical except declared counters, the lease table (including its acquisition and release accounting on a guard decline) and pending queue are unchanged, and the recording emitter observed no call; no credential, private address, real or proprietary payload, environment-specific absolute host path, or sensitive deployment value |
| CHK-22 | Doxygen declarations | inspect `stimulation_actions.hpp`; run the existing documentation configuration check | every public declaration carries `\brief` plus `\ownership`, `\lifetime`, `\thread_safety`, and `\failure` where applicable; the file block names T028 and `\ingroup xcom_stim`; the admitted configuration is unchanged |
| CHK-23 | Registers, REF-002, and maturity honesty | run the §3 validators; inspect the recorded maturity | validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; `XCOM-SW-STIM-005`/`XCOM-SW-STIM-006`/`XCOM-SW-STIM-008` are recorded implemented and `XCOM-SW-STIM-003`/`XCOM-SW-STIM-009` partial with T029 owning routed provenance and the complete matrix; no requirement is promoted beyond its recorded disposition |
| CHK-24 | Deterministic gate, diff hygiene, stage rule | run the §2 gate; `git diff --check <baseline> --`; `git diff --name-only <baseline> -- specs/007-xcom-core` | exit 0 with a `ctest:` count; the diff is whitespace-clean; the only capability-document change is the T028 checkbox line, marked complete **only** at the implementation stage |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no
partial value, no mutation of operational state, no emitted normal-route item, and no output claiming
success. NEG-01…NEG-36 are executable or source-inspection cases realized by the named checks and the case
assertions; NEG-01/NEG-32 are the additivity/stage repository probes.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | change a non-T028 path, weaken/rename an existing test, or change a non-additive build element | CHK-02/CHK-04 fail; the candidate exceeds the T028 boundary |
| NEG-02 | add a dependency or redefine an accepted T025/T026/T027/T-CORE identity/digest/diagnostic/interaction/origin/action type | CHK-03/CHK-19 fail |
| NEG-03 | add a payload-retaining member, a payload-accepting constructor, or grow a value past its size bound | CHK-05/CHK-20 fail (the compile-time assertion catches the constructor and size cases; the member-shape case is caught by the CHK-05/CHK-20 declaration inspection) |
| NEG-04 | expose an open vocabulary or an unstable precedence/name/rank | CHK-17 fails |
| NEG-05 | accept an empty, over-long, or non-printable tool/schema/target/tag at open or execute | CHK-05/CHK-06 fail |
| NEG-06 | emit or journal on a guard `Rejected`/`Failed` decision | CHK-07/CHK-21 fail |
| NEG-07 | emit before the durable intent, or report an incomplete outcome as `Emitted`/`Closed` | CHK-08/CHK-16 fail |
| NEG-08 | emit an item with a non-synthetic classification or a missing identity | CHK-09 fails |
| NEG-09 | acquire a lease under a foreign session | CHK-10 fails |
| NEG-10 | acquire or reuse a lease under a foreign/superseded generation | CHK-10 fails |
| NEG-11 | allow two active leases for one endpoint generation, or two `Ok` acquisitions in a race | CHK-11/CHK-18 fail |
| NEG-12 | release a lease owned by another session or an unknown key | CHK-12 fails |
| NEG-13 | leave a revoked/released lease conflict-blocking or an expired lease active | CHK-12/CHK-10 fail |
| NEG-14 | compare or order two raw mismatched clock domains in the lease/expiry path | CHK-13 fails |
| NEG-15 | authorize a prohibited reinjection (`causation_id` present in the lineage window) | CHK-14 fails |
| NEG-16 | let the lineage window exceed its declared bound | CHK-14 fails |
| NEG-17 | exceed the bounded pending queue or complete more than `max_drain_steps` per call | CHK-15/CHK-18 fail |
| NEG-18 | emit a late action under either late-item policy | CHK-15 fails |
| NEG-19 | emit or journal an immediate request that is mislabeled or outside the validity domain | CHK-13 fails |
| NEG-20 | complete a session without cancelling every pending action | CHK-16 fails |
| NEG-21 | complete a session without releasing/quarantining every held lease | CHK-16 fails |
| NEG-22 | convert an evidence-incomplete intent into `Emitted`/`Closed` | CHK-16 fails |
| NEG-23 | compare a lease/action value in a foreign clock domain, or perform a time-authority call | CHK-13/CHK-19 fail |
| NEG-24 | authorize an action whose time resolution is absent, unmapped, or outside tolerance | CHK-13 fails |
| NEG-25 | mutate a lease, queue, lineage, or journal record on a decline | CHK-21 fails |
| NEG-26 | mutate accepted guard state or accepted T025/T026 state on a decline | CHK-21/CHK-07 fail |
| NEG-27 | emit, route, or invoke a callback on a decline, or invoke the emitter under a lock | CHK-21/CHK-18 fail |
| NEG-28 | produce a non-deterministic status/state/outcome/name/rank or different snapshots across runs | CHK-17 fails |
| NEG-29 | use an unbounded thread/iteration/wait, or invoke a callback under a lock | CHK-18 fails |
| NEG-30 | introduce network/socket/TLS/ambient/secret/process/dynamic-load/legacy access, filesystem I/O, or a new dependency | CHK-19 fails |
| NEG-31 | introduce an absolute host path, credential, or sensitive value into a committed file | CHK-21 fails |
| NEG-32 | change a non-T028 path, weaken an accepted requirement/test, implement a later task, promote a REF-002/capability requirement, or mark the T028 checkbox in the plan stage | CHK-02/CHK-23/CHK-24 fail; the candidate exceeds the T028 scope, stage, or maturity boundary |
| NEG-33 | accept an invalid/zero/over-maximum declared configuration at open | CHK-06 fails |
| NEG-34 | execute a request before the action path is open, or with a malformed request identity | CHK-06 fails |
| NEG-35 | re-implement, weaken, or bypass an accepted guard or journal check | CHK-03/CHK-07 fail |
| NEG-36 | count a declined action as emitted, or exceed a declared queue/lease/quota/lineage bound under concurrency | CHK-15/CHK-18/CHK-21 fail |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline
  `c518c5e4fcb2055666db25cb62018769e7f56ae4`;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting
  command;
- the configure/build/CTest results, including the `ctest -N` discovered counts (T028 adds 22 cases; the
  existing counts are preserved) and the `100% tests passed` line;
- the per-case results for `xverse_xcom_stimulation_actions_action_tests`,
  `xverse_xcom_stimulation_actions_lease_tests`,
  `xverse_xcom_stimulation_actions_lifecycle_tests`,
  `xverse_xcom_stimulation_actions_negative_tests`, and
  `xverse_xcom_stimulation_actions_concurrency_tests`, plus the unchanged preserved suites that prove
  additivity;
- the decision-matrix evidence: the config/precondition table, the action-kind table, the lease table, the
  scheduling/loop/late table, and the completion table from `detailed-design.md` §5;
- the journal-order evidence: for each nominal action the durable intent precedes the single emitter call,
  and an intent without a durable outcome maps to `EvidenceIncomplete`;
- the provenance evidence: the emitted descriptor carries `OriginKind::validation_tool` and the exact
  identity;
- the exclusive-lease evidence: the acquire/release/quarantine/expire matrix, the generation/session/plan
  binding, and the concurrent single-winner race;
- the non-mutation evidence: for each decline family the pre/post snapshot equality (except the declared
  counters), the unchanged lease table and pending queue, and a zero emitter-call count;
- the zero-emission evidence: no decline reaches the emitter or the durable journal;
- the determinism evidence: repeated bounded runs producing identical statuses, states, outcomes, and
  snapshots;
- the bounded deterministic-concurrency evidence: ≤ 4 threads, ≤ 16 evaluations per thread, 3 runs, and a
  golden-sequence comparison;
- the negative-case list with each NEG-ID, its realizing check, and its exact observed outcome;
- the changed-path list and the package record `reports/xcom-queue/t028-package.json` with per-file
  SHA-256;
- the register-validator results, the unchanged REF-002 disposition, and the recorded
  `XCOM-SW-STIM-003`/`XCOM-SW-STIM-009` partial disposition.

Public evidence omits host-specific, prefix, manifest, test-toolchain, scratch, temporary, and private-store
absolute paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T028 verification is complete when: the deterministic gate passes (CHK-24); every nominal check in §4 has
its expected result; every negative case in §5 fails closed as stated; the four action kinds, the
guard-decision mapping, the journal-before-emission ordering, the exclusive generation-bound lease
acquire/release/quarantine/expire behaviour, the loop/late/unmapped-clock fail-closed behaviours, the
drain/close/revoke/expiry/evidence-incomplete completion, and the zero-mutation/zero-emission-on-decline
behaviour are proven; `XCOM-SW-STIM-005`, `XCOM-SW-STIM-006`, and `XCOM-SW-STIM-008` are recorded
implemented and `XCOM-SW-STIM-003`/`XCOM-SW-STIM-009` partial; no accepted requirement, test, ADR,
contract, register, or T025/T026/T027 byte is weakened; the register validators still pass with REF-002
unchanged and nothing promoted; and a separate DeepSeek internal review records a passing verdict with no
unresolved blocking finding. This does not constitute user acceptance, which remains T041.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T028-STK-001 | CHK-01, CHK-02, CHK-04 | CHK-24 |
| T028-STK-002 | CHK-07, CHK-10, CHK-11, CHK-14, CHK-15, CHK-16, CHK-21 | CHK-06, CHK-08, CHK-09 |
| T028-STK-003 | CHK-02, CHK-03, CHK-23 | NEG-01, NEG-32 |
| T028-STK-004 | CHK-17, CHK-18, CHK-19, CHK-20, CHK-21 | NEG-28, NEG-29, NEG-30, NEG-31 |
| T028-STK-005 | CHK-23, CHK-24 | NEG-32 |
| T028-SR-001 | CHK-02, CHK-04, CHK-18 | NEG-01 |
| T028-SR-002 | CHK-03, CHK-19 | NEG-02 |
| T028-SR-003 | CHK-17, CHK-20 | NEG-04 |
| T028-SR-004 | CHK-05, CHK-20 | NEG-03 |
| T028-SR-005 | CHK-06, CHK-18 | NEG-33, NEG-34 |
| T028-SR-006 | CHK-07, CHK-14 | NEG-06, NEG-26, NEG-27 |
| T028-SR-007 | CHK-08, CHK-16 | NEG-07, NEG-25 |
| T028-SR-008 | CHK-09 | NEG-08 |
| T028-SR-009 | CHK-10 | NEG-09, NEG-10 |
| T028-SR-010 | CHK-11, CHK-18 | NEG-11, NEG-29, NEG-36 |
| T028-SR-011 | CHK-12 | NEG-12, NEG-13 |
| T028-SR-012 | CHK-13 | NEG-14, NEG-23 |
| T028-SR-013 | CHK-14 | NEG-15, NEG-16 |
| T028-SR-014 | CHK-15 | NEG-17, NEG-18 |
| T028-SR-015 | CHK-13, CHK-19 | NEG-19, NEG-24 |
| T028-SR-016 | CHK-16 | NEG-20, NEG-21, NEG-22 |
| T028-SR-017 | CHK-21 | NEG-25, NEG-26, NEG-27 |
| T028-SR-018 | CHK-17 | NEG-28 |
| T028-SR-019 | CHK-18 | NEG-29, NEG-36 |
| T028-SR-020 | CHK-19, CHK-20 | NEG-30 |
| T028-SR-021 | CHK-21 | NEG-31 |
| T028-SR-022 | CHK-22 | — |
| T028-SR-023 | CHK-23 | NEG-32 |
| T028-SR-024 | CHK-24 | NEG-32 |

No requirement is left without at least one check, and no check claims acceptance.

## 9. T-STIM slice evidence mapping (T007 register)

The T007 ownership register requires eleven evidence names for the whole `T-STIM` slice (T025–T029). T028
contributes to seven and closes the action-path implementation half of the slice, without claiming any name
beyond its own exact-candidate evidence. T029 closes the complete cross-cutting matrix.

| Slice evidence | T028 contribution | Owning check/case |
| --- | --- | --- |
| `lease-conflicts` | exclusive generation-bound lease acquire/release/quarantine/expire, identity binding, capacity, and the concurrent single-winner race | CHK-10, CHK-11, CHK-12; `T28-TS-006`…`T28-TS-010`, `T28-TS-020` |
| `drain-terminal` | bounded scheduled queue/ordering, drain budget, and drain/close/revoke/expiry/evidence-incomplete completion | CHK-15, CHK-16; `T28-TS-011`…`T28-TS-014` |
| `loop-bounds` | emission-time bounded lineage window and prohibited-reinjection rejection (action-path half; the guard half is T027) | CHK-14; `T28-TS-012` |
| `synthetic-provenance` | synthetic classification and exact identity on the emitted descriptor (descriptor half; routed/restarted half is T029/T033) | CHK-09; `T28-TS-003` |
| `unmapped-clocks` | immediate labeling and unmapped/out-of-tolerance fail-before-emission on the action path, and no raw-clock comparison in lease expiry (action-path half; the guard half is T027) | CHK-13; `T28-TS-009`, `T28-TS-015` |
| `zero-emission-after-rejection` | every decline emits nothing and journals nothing; the recording emitter observes no call (action-path half) | CHK-07, CHK-21; `T28-TS-002`, `T28-TS-016`, `T28-TS-017` |
| `deterministic-concurrency` | bounded deterministic action execution and the concurrent lease single-winner race | CHK-17, CHK-18; `T28-TS-004`, `T28-TS-019`, `T28-TS-020` |
| `journal-before-emission`, `journal-failure-recovery` | consumed from the accepted T026 journal read-only; T028 proves the ordering at the action-path boundary and the evidence-incomplete outcome | CHK-08, CHK-16; `T28-TS-001`, `T28-TS-014` (the journal's own failure/recovery matrix is T026/T029) |
| `permit-action-mismatch-matrix`, `quotas` | consumed from the accepted T027 guard read-only; T028 exercises the guard mapping and quota bound | CHK-07, CHK-18; `T28-TS-002`, `T28-TS-019` |

No evidence name above is claimed beyond what its own exact-candidate evidence shows; `synthetic-provenance`,
`unmapped-clocks`, `loop-bounds`, and `zero-emission-after-rejection` are explicitly partial for T028 (the
action-path portion only), and the complete cross-cutting matrix remains T029.
