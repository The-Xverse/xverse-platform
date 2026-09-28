# T027 Verification Plan — Named Checks, Commands, Negative Cases, and Evidence (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T027 (capability 007, slice `T-STIM`) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 (fail-closed pre-emission guard) |
| Baseline revision | `bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope, plus the repository-owned Fabro gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
T027's executable checks are five new GoogleTest executables under `tests/xcom/stimulation_guard/`, the
unchanged existing suites that prove additivity, and the source inspections that prove the check order,
non-mutation, zero-emission surface, bounds, determinism, offline behaviour, public safety, and governance;
the governance checks are the deterministic gate and the T007–T010 register validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 ${XVERSE_FABRIC_ROOT}/automation/xcom_feature_gate.py verify T027 bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f
```

For T027 this gate requires:

- the six work products
  `docs/engineering/xcom/t027/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T027 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- at least one changed path under `src/xverse/xcom/` and at least one changed path under `tests/`
  (satisfied by the new guard unit and its suites);
- `cmake -S . -B build/fabro-t027 -G Ninja -DCMAKE_BUILD_TYPE=Debug`,
  `cmake --build build/fabro-t027 --parallel 4`, a non-empty `ctest --test-dir build/fabro-t027 -N`, and
  `ctest --test-dir build/fabro-t027 --output-on-failure --parallel 4` all exit 0;
- `git diff --check bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the admitted offline inputs. As accepted
for T012–T016 and T019–T026, if the gate's plain configure fails closed at the T025 test-toolchain
admission check, the only permitted resolution is the narrow A-1 cache seeding already recorded by those
slices: one configure carrying `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously admitted cache values seeds the gate's own
git-ignored `build/fabro-t027` cache; the gate's unmodified configure/build/`ctest` sequence then reuses it.
The hash-verified preflight is unchanged, no ambient path or network resolution is added, no admission check
is weakened, and the admitted input **values** are recorded by name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f --
git diff --check bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t027 -N
ctest --test-dir build/fabro-t027 -R "xcom_stimulation_guard" --output-on-failure
ctest --test-dir build/fabro-t027 -R "xcom_core_types|xcom_lifecycle|xcom_provider_loopback|xcom_activation_plan|xcom_validation|xcom_observation|xcom_core_matrix|xcom_stimulation_journal" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with
the shared T007–T010 artifacts unchanged in substance. The existing core, lifecycle, provider,
activation-plan, validation, observation, core-matrix, and stimulation-journal suites must pass unchanged,
proving additivity. Executed sanitizer/static-analysis/Doxygen/benchmark measures and the delivery bundle
remain with T035–T040; this plan requires the T027 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T027 entry exists and states the fail-closed pre-emission guard scope |
| CHK-02 | Changed-path boundary | `git diff --name-only <baseline> --`; `git ls-files --others --exclude-standard` | only the §7.1 paths appear; no T025/T026 source/test byte, no `xdl/`, `proto/`, `src/xverse_xdl/`, `cmake/*.cmake`, or root `CMakeLists.txt` change; no other task's path |
| CHK-03 | Dependency and contract reuse | inspect `stimulation_guard.hpp` includes and the CMake link line | the unit includes only the C++ standard library plus `validation_session.hpp`, `contract.hpp`, and `result.hpp`; no new third-party dependency; no identity/digest/diagnostic/interaction type is redefined |
| CHK-04 | Build wiring, discovery, additivity | build; `ctest -N`; run the five T027 executables and the preserved suites | `xverse_xcom_stimulation_guard` is the only new runtime target; the five new executables discover 20 cases; every existing target/test name/label/command and the discovered count of existing tests are preserved |
| CHK-05 | Bounded payload-free values | inspect the value types; run `T27-TS-001`, `T27-TS-018` | every value type exposes no payload/value/address/free-form/unbounded member by declaration inspection; a non-vacuous compile-time negative assertion fails the build if a payload-accepting constructor or an unbounded value is added |
| CHK-06 | Policy/open validation | run `T27-TS-005`, `T27-TS-006`, `T27-TS-018` | every row of `detailed-design.md` §5.1 matches; an invalid/zero/over-maximum/inconsistent policy or an identity/plan mismatch is `RejectedConfiguration`/`PermitMismatch` with no authorization and no mutation |
| CHK-07 | Lifecycle revocation and expiry | run `T27-TS-007` | every row of `detailed-design.md` §5.2 matches; `revoked`→`Revoked`, `expired`→`Expired`, every other non-`active` state→`NotActive`; only `active` continues; no rejection mutates a tally |
| CHK-08 | Schema and target validation | run `T27-TS-008` | an undeclared/invalid schema is `SchemaMismatch`; a target/interface mismatch is `TargetMismatch`; every rejection appends nothing and mutates no byte |
| CHK-09 | Action, interaction, and direction validation | run `T27-TS-002`, `T27-TS-009` | every row of `detailed-design.md` §5.3 matches; a defined-but-disallowed action is `ActionMismatch`; an inconsistent interaction/direction is `InteractionMismatch`/`DirectionMismatch`; a zero/composite/out-of-vocabulary action (including a single undefined bit) is `RejectedConfiguration` at rank 1; no rejection mutates state |
| CHK-10 | Quota bounds | run `T27-TS-011` | every per-session and per-window row of `detailed-design.md` §5.4 matches; exhaustion is `QuotaExhausted` with no mutation; `window_actions` resets at `action_window`; the tally advances only on `Authorized` |
| CHK-11 | Service-ownership declaration | run `T27-TS-010` | a missing/mismatched/ambiguous owner or generation is `OwnershipConflict` with no mutation; emulation without a declared owner is rejected; the guard holds no lease |
| CHK-12 | Loop bound | run `T27-TS-012` | a prohibited reinjection is `LoopBound` with no mutation; `causation_id == 0` is never a loop; the loop window never exceeds `loop_window` and evicts the oldest |
| CHK-13 | Time policy and unmapped clocks | run `T27-TS-013`, `T27-TS-014`, `T27-TS-015` | every row of `detailed-design.md` §5.5 matches; an absent/unmapped/out-of-tolerance resolution is `Failed`/`TimeUnmapped`; an out-of-window time is `Rejected`/`TimeOutOfWindow`; an immediate request with a non-validity clock domain is `RejectedConfiguration`; the guard calls no time authority and compares no raw mismatched clocks |
| CHK-14 | Zero mutation on rejection | run `T27-TS-016`, `T27-TS-020` | for every rejection family the pre/post snapshot is byte-identical except the declared evaluation/rejection counters, and the action tallies and loop window are unchanged; a rejection never reports `Authorized` |
| CHK-15 | Zero-emission surface and closed guard | run `T27-TS-016`, `T27-TS-017`; inspect the header | the guard exposes no emission/callback/route/injection/invocation/emulation/lease member; `authorize` before `open` is `Failed`/`NotOpen` with no mutation |
| CHK-16 | Identity and plan binding | run `T27-TS-006` | every row of `detailed-design.md` §5.6 matches; a foreign/absent session or permit identity or a plan-digest mismatch is `PermitMismatch` before any mutation (`XCOM-INV-07`) |
| CHK-17 | Determinism and closed vocabularies | run `T27-TS-003`, `T27-TS-004` | the action/outcome/reason/status vocabularies are closed with stable names, ranks, and a total `outcome_of`; repeated bounded runs produce identical decisions, reasons, and snapshots |
| CHK-18 | Bounds, concurrency, and no-callback | run `T27-TS-019`, `T27-TS-020`; inspect `detailed-design.md` §7 and the tests | ≤ 4 threads, ≤ 64 bounded evaluations per case, ≤ `max_actions_per_session` authorized actions, ≤ `loop_window` entries, no callback, no wall-clock verdict; 4 independent guards match the single-threaded golden sequence across three runs; concurrent rejections do not mutate state; concurrent authorizations against one declared per-session quota commit exactly the quota and never an over-quota action |
| CHK-19 | Offline, local-only, no I/O, no new dependency | forbidden-API source scan; successful offline configure/build; inspect the guard | no network/socket/resolver/TLS, ambient/secret lookup, dynamic-load, subprocess, filesystem, or legacy access; the guard calls no time authority and owns no I/O boundary; no TCP listener; no new admitted dependency |
| CHK-20 | No unrestricted logging or export primitive | forbidden-vocabulary scan of the changed source/tests | no payload/value log, decoder, redaction profile, dashboard, storage, query, presentation, export, OpenTelemetry, or adapter primitive appears in the T027 surface |
| CHK-21 | Public safety and path hygiene | scan the changed source, tests, and work products | no credential, private address, real or proprietary payload, environment-specific absolute host path, or sensitive deployment value |
| CHK-22 | Doxygen declarations | inspect `stimulation_guard.hpp`; run the existing documentation configuration check | every public declaration carries `\brief` plus `\ownership`, `\lifetime`, `\thread_safety`, and `\failure` where applicable; the file block names T027 and `\ingroup xcom_stim`; the admitted configuration is unchanged |
| CHK-23 | Registers, REF-002, and maturity honesty | run the §3 validators; inspect the recorded maturity | validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; `XCOM-SW-STIM-004` is recorded implemented and `XCOM-SW-STIM-005`/`XCOM-SW-STIM-006` partial with the lease/end-to-end loop/scheduling portions deferred to T028/T029; no requirement is promoted |
| CHK-24 | Deterministic gate, diff hygiene, stage rule | run the §2 gate; `git diff --check <baseline> --`; `git diff --name-only <baseline> -- specs/007-xcom-core` | exit 0 with a `ctest:` count; the diff is whitespace-clean; the only capability-document change is the T027 checkbox line, marked complete **only** at the implementation stage |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no
partial value, no mutation of operational state, no emitted normal-route item, and no output claiming
success. NEG-01…NEG-36 are executable or source-inspection cases realized by the named checks and the case
assertions; NEG-01/NEG-32 are the additivity/stage repository probes.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | change a non-T027 path, weaken/rename an existing test, or change a non-additive build element | CHK-02/CHK-04 fail; the candidate exceeds the T027 boundary |
| NEG-02 | add a dependency or redefine a T025/T-CORE identity/digest/diagnostic/interaction type | CHK-03/CHK-19 fail |
| NEG-03 | add a payload-accepting constructor, grow a value past its size bound, or add a payload-bearing member | CHK-05/CHK-20 fail (the compile-time assertion catches the constructor and size cases; the member-shape case is caught by the CHK-05 declaration inspection) |
| NEG-04 | accept a zero, composite, or out-of-vocabulary stimulation action | CHK-09 fails |
| NEG-05 | accept an empty, over-long, or non-printable schema/target/interface tag | CHK-05/CHK-08 fail |
| NEG-06 | authorize a request whose session or permit identity differs from the bound permit | CHK-06/CHK-16 fail |
| NEG-07 | authorize a request or policy whose plan digest differs from the bound permit | CHK-06/CHK-16 fail |
| NEG-08 | authorize a request addressed to a revoked session | CHK-07 fails |
| NEG-09 | authorize a request addressed to an expired session | CHK-07 fails |
| NEG-10 | authorize a request outside the `active` state | CHK-07 fails |
| NEG-11 | authorize a request with an undeclared schema | CHK-08 fails |
| NEG-12 | authorize a direction inconsistent with the action/interaction table | CHK-09 fails |
| NEG-13 | authorize an interaction kind inconsistent with the action or excluded by the policy | CHK-09 fails |
| NEG-14 | authorize a request whose target or interface tag differs from the permit | CHK-08 fails |
| NEG-15 | authorize a defined action not declared allowed | CHK-09 fails |
| NEG-16 | authorize a request past the per-session budget | CHK-10 fails |
| NEG-17 | authorize a request past the per-window budget, or fail to reset the window at `action_window` | CHK-10 fails |
| NEG-18 | authorize a prohibited reinjection (`causation_id` present in the loop window) | CHK-12 fails |
| NEG-19 | accept a zero/over-maximum loop window or an over-full schema table at open | CHK-06/CHK-18 fail |
| NEG-20 | authorize a service action with a missing or mismatched declared owner or generation | CHK-11 fails |
| NEG-21 | authorize an ambiguous/conflicting service-emulation declaration without a declared owner | CHK-11 fails |
| NEG-22 | authorize a scheduled request with an invalid or absent clock domain | CHK-13 fails |
| NEG-23 | authorize a request whose time resolution is absent, unmapped, or outside tolerance | CHK-13 fails (it must be `Failed`/`TimeUnmapped`) |
| NEG-24 | authorize a request whose resolved time is outside the validity interval | CHK-13 fails |
| NEG-25 | mislabel a scheduled request as immediate or authorize an immediate request outside the validity domain | CHK-13 fails |
| NEG-26 | mutate the action tally, window tally, or loop window on a `Rejected`/`Failed` evaluation | CHK-14/CHK-18 fail |
| NEG-27 | emit, route, inject, invoke, emulate, or lease on a rejection, or expose such an entry point | CHK-15/CHK-21 fail |
| NEG-28 | produce a non-deterministic decision/reason/name/rank or different snapshots across runs | CHK-17 fails |
| NEG-29 | use an unbounded thread/iteration/wait, or invoke a callback under the guard mutex | CHK-18 fails |
| NEG-30 | introduce network/socket/TLS/ambient/secret/process/dynamic-load/legacy access, filesystem I/O, or a new dependency | CHK-19 fails |
| NEG-31 | introduce an absolute host path, credential, or sensitive value into a committed file | CHK-21 fails |
| NEG-32 | change a non-T027 path, weaken an accepted requirement/test, implement a later task, promote a REF-002/capability requirement, or mark the T027 checkbox in the plan stage | CHK-02/CHK-23/CHK-24 fail; the candidate exceeds the T027 scope, stage, or maturity boundary |
| NEG-33 | accept an invalid/zero/inconsistent policy bound (zero budget, zero/over-maximum loop window, inconsistent plan/interface/target/validity) | CHK-06/CHK-18 fail |
| NEG-34 | authorize a request before the guard is open | CHK-15 fails |
| NEG-35 | perform a time-authority call, a raw cross-domain clock comparison, or any I/O inside the guard | CHK-13/CHK-19 fail |
| NEG-36 | count a rejected/failed evaluation as an authorized action, or exceed a declared bound under concurrency | CHK-10/CHK-14/CHK-18 fail |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline SHA `bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f`;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting
  command;
- the configure/build/CTest results, including the `ctest -N` discovered counts (T027 adds 20 cases; the
  existing counts are preserved) and the `100% tests passed` line;
- the per-case results for `xverse_xcom_stimulation_guard_unit_tests`,
  `xverse_xcom_stimulation_guard_mismatch_tests`, `xverse_xcom_stimulation_guard_time_tests`,
  `xverse_xcom_stimulation_guard_negative_tests`, and
  `xverse_xcom_stimulation_guard_concurrency_tests`, plus the unchanged preserved suites that prove
  additivity;
- the decision-matrix evidence: the policy/open table, the lifecycle table, the action/interaction/direction
  table, the identity/plan table, the quota and loop tables, and the time table from `detailed-design.md`
  §5;
- the non-mutation evidence: for each rejection family the pre/post snapshot equality (except the declared
  counters) and the unchanged action tallies and loop window, and the concurrent-rejection non-mutation case;
- the zero-emission evidence: the guard header/type exposes no emission/callback/route/injection/invocation/
  emulation/lease member, and every non-`Authorized` decision is the only output of `authorize`;
- the time evidence: a non-`Ok` resolution and a domain-mismatch resolution both return
  `Failed`/`TimeUnmapped`, an out-of-window time returns `Rejected`/`TimeOutOfWindow`, and no case calls a
  time authority inside the guard;
- the determinism evidence: repeated bounded runs producing identical decisions, reasons, and snapshots;
- the bounded deterministic-concurrency evidence: 4 independent guards × ≤ 16 evaluations × 3 runs matching
  the single-threaded golden sequence;
- the negative-case list with each NEG-ID, its realizing check, and its exact observed outcome;
- the changed-path list and the package record `reports/xcom-queue/t027-package.json` with per-file SHA-256;
- the register-validator results, the unchanged REF-002 disposition, and the recorded `XCOM-SW-STIM-005`/
  `XCOM-SW-STIM-006` partial disposition.

Public evidence omits host-specific, prefix, manifest, test-toolchain, scratch, temporary, and private-store
absolute paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T027 verification is complete when: the deterministic gate passes (CHK-24); every nominal check in §4 has
its expected result; every negative case in §5 fails closed as stated; the permit/identity/lifecycle/schema/
target/direction/action/ownership/quota/loop/time fail-closed behaviours and the zero-mutation/
zero-emission-on-rejection behaviour are proven; `XCOM-SW-STIM-004` is implemented and `XCOM-SW-STIM-005`/
`XCOM-SW-STIM-006` are recorded partial; no accepted requirement, test, ADR, contract, register, or
T025/T026 byte is weakened; the register validators still pass with REF-002 unchanged and nothing promoted;
and a separate DeepSeek internal review records a passing verdict with no unresolved blocking finding.
This does not constitute user acceptance, which remains T041.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T027-STK-001 | CHK-01, CHK-02, CHK-04 | CHK-24 |
| T027-STK-002 | CHK-07, CHK-08, CHK-09, CHK-10, CHK-12, CHK-13, CHK-14 | CHK-06, CHK-11, CHK-15 |
| T027-STK-003 | CHK-02, CHK-03, CHK-23 | NEG-01, NEG-32 |
| T027-STK-004 | CHK-17, CHK-18, CHK-19, CHK-21 | NEG-28, NEG-29, NEG-30, NEG-31 |
| T027-STK-005 | CHK-23, CHK-24 | NEG-32 |
| T027-SR-001 | CHK-02, CHK-04, CHK-18 | NEG-01 |
| T027-SR-002 | CHK-03, CHK-19 | NEG-02 |
| T027-SR-003 | CHK-17, CHK-20 | NEG-28 |
| T027-SR-004 | CHK-05, CHK-20 | NEG-03 |
| T027-SR-005 | CHK-06, CHK-16 | NEG-06, NEG-07 |
| T027-SR-006 | CHK-07 | NEG-08, NEG-09, NEG-10 |
| T027-SR-007 | CHK-08, CHK-09 | NEG-05, NEG-11, NEG-12, NEG-13, NEG-14 |
| T027-SR-008 | CHK-09 | NEG-04, NEG-15 |
| T027-SR-009 | CHK-10 | NEG-16, NEG-17, NEG-36 |
| T027-SR-010 | CHK-12 | NEG-18, NEG-19 |
| T027-SR-011 | CHK-11 | NEG-20, NEG-21 |
| T027-SR-012 | CHK-13, CHK-19 | NEG-22, NEG-23, NEG-24, NEG-25, NEG-35 |
| T027-SR-013 | CHK-14, CHK-15 | NEG-26, NEG-34 |
| T027-SR-014 | CHK-17 | NEG-28 |
| T027-SR-015 | CHK-18 | NEG-29, NEG-36 |
| T027-SR-016 | CHK-19 | NEG-30 |
| T027-SR-017 | CHK-21 | NEG-31 |
| T027-SR-018 | CHK-22 | — |
| T027-SR-019 | CHK-23 | NEG-32 |
| T027-SR-020 | CHK-24 | NEG-32 |
| T027-SR-021 | CHK-06, CHK-18 | NEG-19, NEG-33 |
| T027-SR-022 | CHK-15 | NEG-27, NEG-34 |

No requirement is left without at least one check, and no check claims acceptance.

## 9. T-STIM slice evidence mapping (T007 register)

The T007 ownership register requires eleven evidence names for the whole `T-STIM` slice (T025–T029). T027
contributes to four and closes the guard-level half of the mismatch matrix, without claiming any name beyond
its own exact-candidate evidence.

| Slice evidence | T027 contribution | Owning check/case |
| --- | --- | --- |
| `permit-action-mismatch-matrix` | guard-level identity/lifecycle/schema/target/direction/action/ownership mismatch matrix | CHK-06, CHK-08, CHK-09, CHK-11, CHK-16; `T27-TS-002`, `T27-TS-005`…`T27-TS-010`, `T27-TS-018` |
| `zero-emission-after-rejection` | guard-level: every non-`Authorized` decision is the only `authorize` output; no emission surface; no mutation | CHK-14, CHK-15, CHK-21; `T27-TS-004`, `T27-TS-016`, `T27-TS-017`, `T27-TS-020` |
| `quotas` | guard-level per-session and per-window action budgets | CHK-10; `T27-TS-011`, `T27-TS-019` |
| `unmapped-clocks` | guard-level pre-emission time-policy check; unmapped/out-of-tolerance resolution fails closed; no raw-clock comparison; no authority mutation | CHK-13; `T27-TS-013`, `T27-TS-014`, `T27-TS-015` |
| `loop-bounds` | guard-level bounded loop window and declaration-level reinjection rejection (partial) | CHK-12; `T27-TS-012` |
| `deterministic-concurrency` | guard-level bounded deterministic decisions and concurrent non-mutation | CHK-17, CHK-18; `T27-TS-003`, `T27-TS-004`, `T27-TS-019`, `T27-TS-020` |
| `lease-conflicts`, `drain-terminal` | none; remain T028/T029 | — |
| `synthetic-provenance` | none; the journal/restart half is T026 and the routed half is T028/T029 | — |
| `journal-before-emission`, `journal-failure-recovery` | none; T026 | — |

No evidence name above is claimed beyond what its own exact-candidate evidence shows; `loop-bounds` and
`unmapped-clocks` are explicitly partial for T027 (the guard-level portion only), and `lease-conflicts`/
`drain-terminal`/`synthetic-provenance` remain with T028/T029.
