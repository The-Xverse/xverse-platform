# T029 Verification Plan — Named Checks, Commands, Negative Cases, and Evidence (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T029 (capability 007, slice `T-STIM`) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 (complete T-STIM cross-cutting verification matrix) |
| Baseline revision | `4d3985855ef7a62b68aa4c66d3b7df032b29f5e9` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope, plus the repository-owned Fabro gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
T029's executable checks are six new GoogleTest executables under `tests/xcom/stimulation_matrix/`, the
unchanged existing suites that prove additivity, and the source inspections that prove the owned fixture,
additivity, zero emission, provenance, bounds, determinism, offline behaviour, and governance; the governance
checks are the deterministic gate and the T007–T010 register validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 ${XVERSE_FABRIC_ROOT}/automation/xcom_feature_gate.py verify T029 4d3985855ef7a62b68aa4c66d3b7df032b29f5e9
```

For T029 this gate requires:

- the six work products
  `docs/engineering/xcom/t029/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T029 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- at least one changed path under `tests/` (satisfied by the six new suites; T029 does not require a
  production-source change);
- `cmake -S . -B build/fabro-t029 -G Ninja -DCMAKE_BUILD_TYPE=Debug`,
  `cmake --build build/fabro-t029 --parallel 4`, a non-empty `ctest --test-dir build/fabro-t029 -N`, and
  `ctest --test-dir build/fabro-t029 --output-on-failure --parallel 4` all exit 0;
- `git diff --check 4d3985855ef7a62b68aa4c66d3b7df032b29f5e9 --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the admitted offline inputs. As accepted for
T012–T016 and T019–T028, if the gate's plain configure fails closed at the T025 test-toolchain admission check,
the only permitted resolution is the narrow A-1 cache seeding already recorded by those slices: one configure
carrying `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` as
explicit, previously admitted cache values seeds the gate's own git-ignored `build/fabro-t029` cache; the gate's
unmodified configure/build/`ctest` sequence then reuses it. The hash-verified preflight is unchanged, no ambient
path or network resolution is added, no admission check is weakened, and the admitted input **values** are
recorded by name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse 4d3985855ef7a62b68aa4c66d3b7df032b29f5e9
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only 4d3985855ef7a62b68aa4c66d3b7df032b29f5e9 --
git diff --check 4d3985855ef7a62b68aa4c66d3b7df032b29f5e9 --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t029 -N
ctest --test-dir build/fabro-t029 -R "xverse_xcom_stimulation_matrix" --output-on-failure
ctest --test-dir build/fabro-t029 -L "t029" --output-on-failure
ctest --test-dir build/fabro-t029 -R "xcom_core_types|xcom_lifecycle|xcom_provider_loopback|xcom_activation_plan|xcom_validation|xcom_observation|xcom_core_matrix|xcom_stimulation_journal|xcom_stimulation_guard|xcom_stimulation_actions" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with the
shared T007–T010 artifacts unchanged in substance. Every pre-existing suite must pass unchanged, proving
additivity. Executed sanitizer/static-analysis/Doxygen/benchmark measures and the delivery bundle remain with
T035–T040; this plan requires the T029 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T029 entry exists and states the complete matrix scope |
| CHK-02 | Test-only changed-path boundary | `git diff --name-only <baseline> --`; `git ls-files --others --exclude-standard` | only the §7.1 paths appear; no production header/source/runtime target change, no existing test change, no `xdl/`, `proto/`, `src/xverse_xdl/`, `cmake/*.cmake`, or root `CMakeLists.txt` change, no other task's path |
| CHK-03 | Dependency and contract reuse | inspect the fixture and suite includes and the CMake link line | includes only the C++ standard library, GTest, the accepted T025/T026/T027/T028 headers, and the accepted T-CORE/T-OBS/provider headers; no new third-party dependency; no accepted identity/vocabulary type is redefined |
| CHK-04 | Build wiring, discovery, additivity | build; `ctest -N`; run the six T029 executables and the preserved suites | six new executables `xverse_xcom_stimulation_matrix_*_tests` are the only new test targets; the T029 suites discover 20 cases; no runtime target is added; every existing target/test name/label/command and the discovered count of existing tests are preserved |
| CHK-05 | Owned-fixture bounds and payload-free declaration inspection | inspect `test_support.hpp`; run `T29-TS-011` | the fixture declares every bound (durable bytes, injection points, operations, threads, tap capacity) and retains no payload/value/address/free-form member; the bridging item carries no payload byte |
| CHK-06 | Complete permit/action mismatch matrix | run `T29-TS-001`, `T29-TS-002` | every row M-01…M-16 of `detailed-design.md` §5.1 matches: the declared `ActionStatus` and preserved `GuardReason`, zero emitter calls, zero durable appends; lifecycle preconditions return `NotActive`; the direct closed guard returns `Failed`/`NotOpen` |
| CHK-07 | Quotas | run `T29-TS-003` | rows Q-01/Q-02 of §5.2: the budget is committed exactly once per authorization; a budget-exhausted request is `Rejected`/`QuotaExhausted` with zero emission; no run exceeds the declared budget |
| CHK-08 | Loop bounds and lease conflicts | run `T29-TS-004`, `T29-TS-016` | rows L-01…L-04 of §5.3 and L-01…L-10 of §5.8: a retained causal parent is `Rejected`/`LoopBound`; `causation_id == 0` is never a loop; the lineage window never exceeds its bound; a second owner or foreign identity is rejected with no mutation and zero second-owner emission |
| CHK-09 | Unmapped clocks and lease expiry domains | run `T29-TS-005`, `T29-TS-016` | rows C-01…C-07 of §5.4 and L-08 of §5.8: unmapped/out-of-tolerance fails closed before emission and journaling; an out-of-window value is `Rejected`/`TimeOutOfWindow`; a foreign-domain value is never compared; no time authority is called; an elapsed lease becomes inactive |
| CHK-10 | Journal-before-emission ordering | run `T29-TS-006` | rows J-01…J-03 of §5.5: the durable intent precedes the single emitter call for every action kind; a durable non-delivery maps to `EmissionRejected`/`EmissionUnavailable`, never `Emitted` |
| CHK-11 | Journal failure/recovery and evidence-incomplete | run `T29-TS-007`, `T29-TS-008`, `T29-TS-009`, `T29-TS-010` | rows J-04…J-09 of §5.5: intent append/sync failure emits nothing and commits no record; outcome failure is `EvidenceIncomplete`, never `Emitted`; restart recovers the exact intent identity and the explicit orphan; over-capacity is `CapacityExhausted` with zero emission |
| CHK-12 | Zero emission and non-mutation | run `T29-TS-011` | rows Z-01…Z-11 of §5.6: for each decline family the emitter observed zero calls, the durable byte delta is zero, and the operational snapshot is unchanged apart from declared counters |
| CHK-13 | Persistent synthetic provenance | run `T29-TS-012`, `T29-TS-013`, `T29-TS-014`, `T29-TS-015` | rows P-01…P-05 of §5.7: every emitted descriptor carries `OriginKind::validation_tool` and the exact identity; the accepted provider route and observation tap preserve origin and correlation/causation identity; a `validation_tool` filter matches only synthetic records; the restarted identity equals the emitted identity; no path relabels or drops provenance |
| CHK-14 | Drain/terminal/evidence-incomplete completion | run `T29-TS-017`, `T29-TS-018` | rows D-01…D-09 of §5.9: declared outcomes; pending actions drained or cancelled; held leases released/quarantined/expired; an orphan intent forces `EvidenceIncomplete` and never `Closed`; a dropped due action surfaces `failed` |
| CHK-15 | Guard evaluated exactly once per request | run `T29-TS-001`; inspect `detailed-design.md` §4.2 | every mismatch row asserts exactly one accepted guard evaluation per submitted request and no lease acquisition on a guard decline |
| CHK-16 | Deterministic conduct and bounded concurrency | run `T29-TS-019`, `T29-TS-020`; inspect `detailed-design.md` §7 | ≤ 4 threads, ≤ 64 bounded operations per case, ≤ `max_pending_actions` pending, ≤ `max_active_leases` leases, ≤ `max_lineage_entries` lineage, no callback under a lock, no wall-clock verdict; the declared quota is never exceeded; a lease race has exactly one winner; repeated runs are identical |
| CHK-17 | Lease exclusivity end-to-end | run `T29-TS-016` | rows L-01…L-10 of §5.8: at most one active lease per endpoint generation; superseded generations neither authorize nor conflict-block; release/quarantine/expiry relinquish ownership without ambiguous ownership |
| CHK-18 | Ordering, drain budget, and late policy | run `T29-TS-018` | rows D-01/D-02/D-08 of §5.9 and rows of §5.3/§5.2: due actions drain in declared order within `max_drain_steps`; a full queue fails closed; both late-item policies emit nothing; an immediate request is explicitly labeled |
| CHK-19 | Offline, local-only, no new dependency, determinism | forbidden-API source scan; successful offline configure/build; run `T29-TS-019`; inspect the fixture | no network/socket/resolver/TLS, ambient/secret lookup, dynamic-load, subprocess, production filesystem, or legacy access; only the test-local injected storage seam is used; no time-authority call; no new admitted dependency; repeated runs produce identical statuses/states/outcomes/snapshots |
| CHK-20 | No payload retention or export primitive | forbidden-vocabulary scan of the changed tests; run `T29-TS-011` | no payload/value log, decoder, redaction profile, dashboard, storage, query, presentation, export, OpenTelemetry, or adapter primitive appears in the T029 surface; the bridging item is payload-free and no payload view is retained |
| CHK-21 | Public safety | scan the changed tests, fixture, and work products | no credential, private address, real or proprietary payload, environment-specific absolute host path, or sensitive deployment value |
| CHK-22 | Doxygen file blocks | inspect the fixture header and each suite | every file carries `\file`, `\brief`, `\ownership`, `\lifetime`, `\thread_safety`, `\bounds`, and `\failure`; helpers carry `\brief`; the admitted documentation configuration is unchanged |
| CHK-23 | Registers, REF-002, and maturity honesty | run the §3 validators; inspect the recorded maturity | validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; `XCOM-SW-STIM-009` and `XCOM-SW-STIM-003` are recorded implemented by T029, `XCOM-SW-STIM-005`/`-006`/`-008` remain implemented, and T030–T041 remain allocated; no requirement is promoted beyond its recorded disposition |
| CHK-24 | Deterministic gate, diff hygiene, stage rule | run the §2 gate; `git diff --check <baseline> --`; `git diff --name-only <baseline> -- specs/007-xcom-core` | exit 0 with a `ctest:` count; the diff is whitespace-clean; the only capability-document change is the T029 checkbox line, marked complete **only** at the implementation stage; the inherited `engineering/trace/links.json` and `engineering/stage-results/*.json` provenance digests are refreshed and consistent |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no
partial value, no mutation of operational state, no emitted normal-route item, and no output claiming
success. NEG-01…NEG-37 are executable or source-inspection cases realized by the named checks and the case
assertions; NEG-01 is the additivity/test-only repository probe.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | change a non-T029 path (production source/target, another task, or an existing test), or add a non-additive build element | CHK-02/CHK-04 fail; the candidate exceeds the T029 boundary |
| NEG-02 | add a dependency or redefine an accepted T025/T026/T027/T028/T-CORE/T-OBS identity/vocabulary type | CHK-03/CHK-19 fail |
| NEG-03 | re-implement or bypass an accepted guard/journal/provider/observation check, or retain a payload byte in the fixture | CHK-05/CHK-20 fail |
| NEG-04 | emit or journal on a malformed request | CHK-06/CHK-12 fail |
| NEG-05 | emit or journal on a declaration mismatch (`PermitMismatch`…`OwnershipConflict`) | CHK-06/CHK-12 fail |
| NEG-06 | emit or journal on a lifecycle precondition or a closed guard | CHK-06/CHK-12 fail |
| NEG-07 | authorize a budget-exhausted request, or exceed a journal/quota bound | CHK-07/CHK-11 fail |
| NEG-08 | exceed the declared quota under concurrency | CHK-16 fails |
| NEG-09 | authorize a prohibited reinjection (`causation_id` present in a loop/lineage window) | CHK-08 fails |
| NEG-10 | let the lineage window exceed its declared bound | CHK-08 fails |
| NEG-11 | emit or journal an unmapped/out-of-tolerance resolved time | CHK-09 fails |
| NEG-12 | compare or order two raw mismatched clock domains, or call a time authority | CHK-09/CHK-19 fail |
| NEG-13 | emit before the durable intent, or invoke the emitter more than once | CHK-10 fails |
| NEG-14 | emit after an intent append failure | CHK-11 fails |
| NEG-15 | emit after an intent sync/partial-write failure | CHK-11 fails |
| NEG-16 | report an incomplete outcome as `Emitted`/success | CHK-11 fails |
| NEG-17 | report an orphan intent as `Closed` | CHK-14 fails |
| NEG-18 | emit on a full pending queue | CHK-12 fails |
| NEG-19 | emit on an emulation-lease conflict | CHK-12 fails |
| NEG-20 | emit a loop-bound or late action | CHK-08/CHK-12 fail |
| NEG-21 | emit or observe a non-synthetic descriptor | CHK-13 fails |
| NEG-22 | relabel or drop provenance through route/observation | CHK-13 fails |
| NEG-23 | match a foreign origin in the synthetic filter, or lose the identity across restart | CHK-13 fails |
| NEG-24 | allow two active leases for one endpoint generation, or two `Ok` acquisitions in a race | CHK-08/CHK-16/CHK-17 fail |
| NEG-25 | leave a released/quarantined/expired lease active or conflict-blocking | CHK-17 fails |
| NEG-26 | compare a foreign-domain lease value | CHK-09 fails |
| NEG-27 | complete more than `max_drain_steps` per call, or exceed the pending bound | CHK-18/CHK-16 fail |
| NEG-28 | emit a late action under either late-item policy | CHK-18 fails |
| NEG-29 | complete a session without cancelling every pending action or releasing every held lease | CHK-14 fails |
| NEG-30 | report a dropped due action as a clean `Drained`/`Closed` | CHK-14/CHK-18 fail |
| NEG-31 | produce a non-deterministic status/state/outcome/snapshot across repeated runs | CHK-16/CHK-19 fail |
| NEG-32 | produce two winners in a lease race | CHK-16 fails |
| NEG-33 | invoke a host callback under a lock, or use an unbounded thread/iteration/wait | CHK-16/CHK-19 fail |
| NEG-34 | introduce network/socket/TLS/ambient/secret/process/dynamic-load/legacy access or a production filesystem boundary | CHK-19 fails |
| NEG-35 | introduce an absolute host path, credential, or sensitive value into a committed file | CHK-21 fails |
| NEG-36 | weaken an accepted requirement/test, change a register, or promote a REF-002/capability requirement | CHK-23 fails |
| NEG-37 | mark the T029 checkbox in the plan stage, change no `tests/` path, or skip the inherited provenance refresh | CHK-24 fails; the candidate exceeds the T029 scope or stage boundary |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline `4d3985855ef7a62b68aa4c66d3b7df032b29f5e9`;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting
  command;
- the configure/build/CTest results, including the `ctest -N` discovered counts (T029 adds 20 cases; the
  existing counts are preserved) and the `100% tests passed` line;
- the per-case results for `xverse_xcom_stimulation_matrix_permit_action_matrix_tests`,
  `xverse_xcom_stimulation_matrix_journal_recovery_tests`,
  `xverse_xcom_stimulation_matrix_zero_emission_tests`,
  `xverse_xcom_stimulation_matrix_provenance_tests`,
  `xverse_xcom_stimulation_matrix_lease_drain_tests`, and
  `xverse_xcom_stimulation_matrix_concurrency_tests`, plus the unchanged preserved suites that prove
  additivity;
- the mismatch-matrix evidence: the row table M-01…M-16 with each observed status/reason, zero emitter calls,
  and zero durable appends;
- the journal evidence: the durable byte count inside the single emitter call per action kind; the injected
  intent/outcome failure outcomes; the restart recovery summary and the recovered orphan identity;
- the zero-emission evidence: the Z-01…Z-11 table with zero emitter calls, zero durable delta, and the
  snapshot delta;
- the provenance evidence: the emitted descriptor classification and identity, the retained observation record
  origin and identity, the filter result, and the restarted identity equality;
- the lease evidence: the L-01…L-10 table with the exact lease statuses and the pre/post snapshots;
- the completion evidence: the D-01…D-09 table with the exact `CompletionReport` outcomes and counts;
- the determinism evidence: repeated bounded runs producing identical statuses, states, outcomes, and
  snapshots, and the bounded deterministic-concurrency evidence (≤ 4 threads, ≤ 16 evaluations per thread,
  3 runs);
- the negative-case list with each NEG-ID, its realizing check, and its exact observed outcome;
- the changed-path list and the package record `reports/xcom-queue/t029-package.json` with per-file SHA-256;
- the register-validator results, the unchanged REF-002 disposition, and the recorded
  `XCOM-SW-STIM-009`/`XCOM-SW-STIM-003` implemented disposition;
- the inherited provenance refresh evidence (`engineering/trace/links.json` and
  `engineering/stage-results/*.json` digests).

Public evidence omits host-specific, prefix, manifest, test-toolchain, scratch, temporary, and private-store
absolute paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T029 verification is complete when: the deterministic gate passes (CHK-24); every nominal check in §4 has its
expected result; every negative case in §5 fails closed as stated; the complete permit/action mismatch matrix,
journal-before-emission ordering and journal failure/recovery, zero emission after every rejection, persistent
synthetic provenance (descriptor, routed/observed, and restarted), unmapped clocks, quotas, loop bounds, lease
conflicts, drain/terminal behavior, and deterministic concurrency are proven; `XCOM-SW-STIM-009` and
`XCOM-SW-STIM-003` are recorded implemented and `XCOM-SW-STIM-005`/`-006`/`-008` remain implemented; no accepted
requirement, test, ADR, contract, register, or production byte is weakened; the register validators still pass
with REF-002 unchanged and nothing promoted; and a separate DeepSeek internal review records a passing verdict
with no unresolved blocking finding. This does not constitute user acceptance, which remains T041; external
Codex review and acceptance are deferred until the ordered backlog `xcom-t026-t029-20260928` completes.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T029-STK-001 | CHK-01, CHK-02, CHK-04 | CHK-24 |
| T029-STK-002 | CHK-06, CHK-08, CHK-11, CHK-12, CHK-14, CHK-17, CHK-18 | CHK-05, CHK-15 |
| T029-STK-003 | CHK-02, CHK-03, CHK-24 | NEG-01, NEG-36 |
| T029-STK-004 | CHK-16, CHK-19, CHK-20, CHK-21 | NEG-31, NEG-33, NEG-34, NEG-35 |
| T029-STK-005 | CHK-23, CHK-24 | NEG-36 |
| T029-SR-001 | CHK-02, CHK-04 | NEG-01 |
| T029-SR-002 | CHK-03, CHK-19 | NEG-02 |
| T029-SR-003 | CHK-05, CHK-20 | NEG-03 |
| T029-SR-004 | CHK-06, CHK-15 | NEG-04, NEG-05, NEG-18, NEG-19 |
| T029-SR-005 | CHK-06 | NEG-06 |
| T029-SR-006 | CHK-07, CHK-16 | NEG-07, NEG-08 |
| T029-SR-007 | CHK-08 | NEG-09, NEG-10, NEG-20 |
| T029-SR-008 | CHK-09 | NEG-11, NEG-12 |
| T029-SR-009 | CHK-10 | NEG-13 |
| T029-SR-010 | CHK-11 | NEG-14, NEG-15 |
| T029-SR-011 | CHK-11, CHK-14 | NEG-16, NEG-17 |
| T029-SR-012 | CHK-12 | NEG-04, NEG-05, NEG-06, NEG-18, NEG-19, NEG-20 |
| T029-SR-013 | CHK-13 | NEG-21 |
| T029-SR-014 | CHK-13 | NEG-22 |
| T029-SR-015 | CHK-13 | NEG-23 |
| T029-SR-016 | CHK-08, CHK-17 | NEG-24, NEG-25 |
| T029-SR-017 | CHK-09, CHK-17 | NEG-26 |
| T029-SR-018 | CHK-18 | NEG-27, NEG-28 |
| T029-SR-019 | CHK-14, CHK-18 | NEG-29, NEG-30 |
| T029-SR-020 | CHK-16 | NEG-08, NEG-31, NEG-32, NEG-33 |
| T029-SR-021 | CHK-16, CHK-19 | NEG-31 |
| T029-SR-022 | CHK-19, CHK-20 | NEG-03, NEG-34 |
| T029-SR-023 | CHK-21 | NEG-35 |
| T029-SR-024 | CHK-23 | NEG-36 |
| T029-SR-025 | CHK-24 | NEG-01, NEG-37 |

No requirement is left without at least one check, and no check claims acceptance.

## 9. T-STIM slice evidence mapping (T007 register)

The T007 ownership register requires eleven evidence names for the whole `T-STIM` slice (T025–T029). T029 closes
the cross-cutting matrix and completes the eleven names without claiming any name beyond its own exact-candidate
evidence.

| Slice evidence | T029 contribution | Owning check/case |
| --- | --- | --- |
| `permit-action-mismatch-matrix` | every request-evaluation guard reason and lifecycle precondition through the accepted action path | CHK-06, CHK-15; `T29-TS-001`, `T29-TS-002` |
| `quotas` | per-session/per-window budget commit, exhaustion, and the bounded concurrent bound | CHK-07, CHK-16; `T29-TS-003`, `T29-TS-019` |
| `loop-bounds` | guard loop window + action-path lineage window, `causation_id == 0`, eviction under bound | CHK-08; `T29-TS-004` |
| `unmapped-clocks` | fail-closed resolution, out-of-window rejection, declared-domain lease expiry, no authority call | CHK-09; `T29-TS-005`, `T29-TS-016` |
| `journal-before-emission` | durable intent precedes the single emitter call for every action kind | CHK-10; `T29-TS-006` |
| `journal-failure-recovery` | intent/outcome failure surfacing, restart recovery, capacity fail-closed | CHK-11; `T29-TS-007`, `T29-TS-008`, `T29-TS-009`, `T29-TS-010` |
| `zero-emission-after-rejection` | every decline family with zero emitter calls and no declined-dimension mutation | CHK-12; `T29-TS-011` |
| `synthetic-provenance` | descriptor classification/identity, routed/observed preservation, restart identity | CHK-13; `T29-TS-012`, `T29-TS-013`, `T29-TS-014`, `T29-TS-015` |
| `lease-conflicts` | conflict, identity mismatch, supersession, release/quarantine/expiry, capacity, race | CHK-08, CHK-16, CHK-17; `T29-TS-016`, `T29-TS-020` |
| `drain-terminal` | ordering, drain budget, late policy, and terminal lifecycle completion | CHK-14, CHK-18; `T29-TS-017`, `T29-TS-018` |
| `deterministic-concurrency` | bounded threads, deterministic total order, identical repeated runs | CHK-16; `T29-TS-019`, `T29-TS-020` |

No evidence name above is claimed beyond what its own exact-candidate evidence shows. The routed/observed
provenance is proven at the accepted provider/observation boundary; the gateway/IPC provenance and the reusable
contract suites remain T032/T033 (`T029-GAP-02`, `T029-GAP-05`).
