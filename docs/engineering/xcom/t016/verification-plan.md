# T016 Verification Plan — Named Checks, Commands, and Negative Cases (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T016 (capability 007, slice `T-CORE`) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `44d2001d48dd42dc9ed489a40d2a5f908b734501` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope plus the repository-owned Fabro gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with
the stated expected result. Weakening an expected result is a verification-contract change requiring
review. T016's executable checks are the new `core_matrix` CTest suites, the external consumer, a
full-suite `ctest` run, and the source inspections that prove bounds, ownership, determinism, the
CORE-008 boundary, neutrality, offline behaviour, additivity, and public safety; the governance checks
are the deterministic gate and the T007–T010 register validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T016 44d2001d48dd42dc9ed489a40d2a5f908b734501
```

For T016 this gate requires:

- the six work products `docs/engineering/xcom/t016/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T016 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- at least one changed path that starts with `tests/`;
- `cmake -S . -B build/fabro-t016 -G Ninja -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build/fabro-t016 --parallel 4`,
  a non-empty `ctest --test-dir build/fabro-t016 -N`, and
  `ctest --test-dir build/fabro-t016 --output-on-failure --parallel 4` all exit 0;
- `git diff --check 44d2001d48dd42dc9ed489a40d2a5f908b734501 --` clean.

Because the gate only requires a `tests/` change, the additive `src/xverse/xcom/CMakeLists.txt`
registration is required to make the new suites discoverable and must change no existing entry.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the three admitted offline inputs. As
accepted for T012/T013/T014/T015/T019/T020, if the gate's plain configure fails closed at the T025
test-toolchain admission check, the only permitted resolution is the narrow A-1 cache seeding already
recorded by those slices: one configure carrying `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously admitted
cache values seeds the gate's own git-ignored `build/fabro-t016` cache; the gate's unmodified
configure/build/`ctest` sequence then reuses it. The hash-verified preflight is unchanged, no ambient
path or network resolution is added, no admission check is weakened, and the admitted input **values**
are recorded by name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse 44d2001d48dd42dc9ed489a40d2a5f908b734501
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only 44d2001d48dd42dc9ed489a40d2a5f908b734501 --
git diff --check 44d2001d48dd42dc9ed489a40d2a5f908b734501 --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t016 -L "t016" --output-on-failure
ctest --test-dir build/fabro-t016 -R "xcom_core_types|xcom_lifecycle|xcom_provider_loopback|xcom_observation|xcom_activation_plan|xcom_validation" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass
with the shared T007–T010 artifacts unchanged in substance. The existing core suites must pass
unchanged, proving additivity. The integration policy's `unit`, `integration`, `validation`, and
`static_analysis` measures are executed by the later T035–T040 stages; this plan requires the T016
candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T016 entry exists and states the interaction-kind/capability/policy/ownership/lifecycle/queue-bound/diagnostics/recovery test scope |
| CHK-02 | Changed-path boundary | `git diff --name-only <baseline> --` | only `tests/xcom/core_matrix/**`, the additive `src/xverse/xcom/CMakeLists.txt` block, the T016 work products, the one-line `tasks.md` checkbox, and the package record appear; no `.hpp`/`.cpp` production unit, `cmake/*.cmake`, root `CMakeLists.txt`, `xdl/`, `proto/`, `src/xverse_xdl/`, another task's test source, or another task's path |
| CHK-03 | Public-surface consumer | run `xcom_core_matrix_external_consumer`; inspect `consumer/main.cpp` | the accepted public headers compile, link, and run in a separate translation unit; the minimal round trip succeeds; the consumer uses no other task's test-support header |
| CHK-04 | Harness, registration, and gate discovery | build; `ctest -N`; `ctest -L t016` | `xcom_core_matrix_{unit,negative,recovery,concurrency,fault_boundary}` plus `xcom_core_matrix_external_consumer` are discovered and pass; `Total Tests` ≥ baseline (248) and the existing names are unchanged; the `t016*` labels select the matrix |
| CHK-05 | Interaction-kind nominal matrix | run `xcom_core_matrix_unit` | all four families round-trip end to end with contract/kind/endpoints/schema/origin/timestamp/clock/correlation/causation/route/provider preserved and payload bytes returned unchanged |
| CHK-06 | Capability nominal matrix | run `xcom_core_matrix_unit` | `interaction_capability_bit` = 1/2/4/8; delivery/ordering bits stable; descriptor rejects zero/unknown masks; requested claims must be advertised; `at_least_once → reliable` prepares and activates against a `reliable`-advertising provider |
| CHK-07 | Declared-policy nominal matrix | run `xcom_core_matrix_unit` | declared `best_effort`/`fifo`/`reject`/`0`/`0` matching request prepares and activates; an unbound three-argument route is unaffected (additivity) |
| CHK-08 | Policy identity discrimination | run `xcom_core_matrix_unit` | two routes with the same identity/digest/provider/endpoints differing only in declared `FlowPolicy` compare unequal (T014 review strengthening) |
| CHK-09 | Ownership nominal matrix | run `xcom_core_matrix_unit` | copied handles/snapshots/values compare equal and remain readable after source destruction/rvalue construction; no public operation mutates without an exact handle |
| CHK-10 | Lifecycle nominal matrix | run `xcom_core_matrix_unit` | accepted declare→validate→activate→drain→close transitions and idempotence hold; wrong-order transitions are rejected with a stable outcome |
| CHK-11 | Provider route lifecycle and drain/close | run `xcom_core_matrix_unit`/`_recovery` | `prepared → active → draining → closed` holds; a draining route rejects new submissions; close rejects a non-empty route and releases only an empty drained route |
| CHK-12 | Queue-bound matrix | run `xcom_core_matrix_unit`; inspect constants | `kMaximumRoutes == 4`, `kMaximumQueueItems == 8`, `kMaximumProviders == 8`, descriptor payload ≤ 65,536 / routes ≤ 32 / queue ≤ 32; reject-new saturation preserves every queued item and FIFO index |
| CHK-13 | Deterministic-diagnostic matrix | run `xcom_core_matrix_unit` | core diagnostics carry the exact code/severity/phase/identity/reason/correction; equivalent inputs in different construction order serialize byte-identically; diagnostics are locale-independent; every provider outcome maps to its exact text/code/message including `unsupported_policy` = `XCOM-PROV-E030` |
| CHK-14 | Recovery matrix | run `xcom_core_matrix_recovery` | saturation-then-drain recovers FIFO; a rejected operation leaves state reusable; a closed route recreated as a new generation rejects stale handles; reconcile mismatch reports `interrupted_resource`; empty receive reports `queue_empty` |
| CHK-15 | Concurrency matrix | run `xcom_core_matrix_concurrency` | concurrent submit/receive delivers each accepted item exactly once with per-route FIFO; repeated bounded runs are deterministic; registration re-entry completes with no callback under a registry/provider lock |
| CHK-16 | Consolidated negative matrix (`SC-001`) | run `xcom_core_matrix_negative` | ≥ 20 (here 27) individually named rejection cases pass across malformed/incompatible/over-capacity/unauthorized classes and all four families; each asserts an exact stable outcome and no mutation |
| CHK-17 | Fault-hook boundary (`XCOM-SW-CORE-008`) | run `xcom_core_matrix_fault_boundary`; forbidden-vocabulary scan | no domain-specific fault campaign/taxonomy/mutation primitive; only bounded controlled seams; no uncontrolled mutation/injection entry point |
| CHK-18 | Matrix self-bounds | inspect `detailed-design.md` §6 and the test sources | ≤ 4 threads, ≤ 32 iterations, finite items, bounded payloads; no unbounded loop, allocation, wait, or wall-clock threshold |
| CHK-19 | Additivity / no-weakening | `git diff --name-only <baseline> -- tests/xcom`; inspect existing suites | only new `tests/xcom/core_matrix/**` paths appear; no existing test source, target, label, command, threshold, or expected result is removed, renamed, weakened, or reordered; no production unit changed |
| CHK-20 | Offline and domain-neutral | forbidden-API source scan; successful offline build | no network/socket/resolver/TLS, ambient/secret lookup, filesystem, process/subprocess, dynamic-load, or legacy access; only the C++ standard library plus admitted GTest/Threads; no domain-specific primitive |
| CHK-21 | Public safety | scan new test sources and work products | no credential, private address, unrestricted or real payload, proprietary excerpt, environment-specific absolute host path, or sensitive deployment value; fixture payload bytes are synthetic and bounded |
| CHK-22 | Doxygen for new files/units | inspect the changed files; run the existing documentation validator | every new file has a `@file`/`@brief` block and every helper/class has `@brief` plus the applicable ownership/lifetime/thread-safety/failure tags; the admitted configuration is unchanged |
| CHK-23 | Registers and REF-002 | run the §3 register validators; inspect the REF-002 disposition | the validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; the five work products exist and are mutually consistent |
| CHK-24 | Deterministic gate, diff hygiene, stage rule | run the §2 gate; `git diff --check <baseline> --`; `git diff --name-only <baseline> -- specs/007-xcom-core` | exit 0 with a `ctest:` count; the diff is whitespace-clean; the only capability-document change is the T016 checkbox line, marked complete **only** at the implementation stage |
| CHK-25 | Work-product completeness and consistency | read the five plan documents; recompute file hashes | the five plan documents exist, identify T016 and the baseline, and agree on scope/cases/outcomes/bounds/boundary; every §3–§4 requirement maps to ≥ 1 check |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no
partial value, no provider dispatch where the accepted design requires rejection before dispatch, no
mutation of any registry/provider/route/queue/lifecycle record, no emitted normal-route item, and no
output claiming acceptance. NEG-01…NEG-27 are executable cases; NEG-28…NEG-30 are
inspection/repository probes.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | empty, over-bound, or non-canonical contract identity/interface/schema field | `required_field`/`bound_exceeded`; no contract value |
| NEG-02 | incompatible interaction/direction tuple (e.g. service request with produce/consume) | `incompatible_direction`; no contract value |
| NEG-03 | item missing route/provider/clock, or over-long correlation | `required_field`/`bound_exceeded` (item phase); no item |
| NEG-04 | payload over the per-route prepared bound | `payload_limit_exceeded` (`XCOM-PROV-E018`); queue unchanged |
| NEG-05 | invalid `FlowPolicy` field (out-of-vocabulary or zero `queue_depth`) | `invalid_policy` (policy phase), sorted set; no policy value |
| NEG-06 | requested interaction not advertised | `unsupported_interaction` (`XCOM-PROV-E015`); `prepare_calls() == 0` |
| NEG-07 | requested delivery not advertised | `unsupported_delivery` (`XCOM-PROV-E016`); no dispatch |
| NEG-08 | requested ordering not advertised | `unsupported_ordering` (`XCOM-PROV-E017`); no dispatch |
| NEG-09 | requested provider contract version ≠ admitted version | `unsupported_contract_version` (`XCOM-PROV-E014`); no dispatch |
| NEG-10 | declared claim unmappable (`at_most_once`/`exactly_once`/`priority`) | `unsupported_delivery`/`unsupported_ordering`; `prepare_calls() == 0` |
| NEG-11 | declared non-`reject` overflow, or nonzero deadline/retry | `unsupported_policy` (`XCOM-PROV-E030`); no dispatch; no mutation |
| NEG-12 | requested queue capacity > declared `queue_depth` | `queue_limit_exceeded` (`XCOM-PROV-E019`); no dispatch |
| NEG-13 | route declaring an unregistered provider | `provider_mismatch` (`XCOM-PROV-E025`); no dispatch |
| NEG-14 | provider advertises fewer bits than the declared claim requires | `unsupported_delivery`/`unsupported_ordering`; no dispatch |
| NEG-15 | duplicate provider identity/instance | `duplicate_provider` (`XCOM-PROV-E012`); no slot replaced |
| NEG-16 | provider registry full | `provider_capacity_exhausted` (`XCOM-PROV-E013`); existing slots unchanged |
| NEG-17 | loopback route storage exhausted | `route_capacity_exhausted` (`XCOM-PROV-E020`); existing routes unchanged |
| NEG-18 | submit beyond configured queue capacity | `queue_saturated` (`XCOM-PROV-E010`); every queued item and FIFO index preserved |
| NEG-19 | submit payload over the prepared provider bound | `payload_limit_exceeded` (`XCOM-PROV-E018`); queue unchanged |
| NEG-20 | close a draining route retaining items | `queued_items_remain` (`XCOM-PROV-E027`); resource retained |
| NEG-21 | stale generation handle after recreation | `invalid_handle`/`invalid_provider_route_handle` (`XCOM-PROV-E021`); no mutation |
| NEG-22 | handle from a foreign composition/provider instance | `invalid_provider_route_handle` (`XCOM-PROV-E021`)/`provider_mismatch` (`XCOM-PROV-E025`); no mutation |
| NEG-23 | submit/receive on a non-active route | `inactive_route` (`XCOM-PROV-E023`); no delivery |
| NEG-24 | item bound to a different route/provider/endpoint | `item_mismatch` (`XCOM-PROV-E026`); queue unchanged |
| NEG-25 | reconcile after provider/lifecycle divergence | `interrupted_resource` (`XCOM-PROV-E028`); never success |
| NEG-26 | `signal_state_update` route requesting a family the descriptor does not advertise | `unsupported_interaction` (`XCOM-PROV-E015`); `prepare_calls() == 0`; not prepared; not activated |
| NEG-27 | `service_response` route submitted an item bound to a different route | `item_mismatch` (`XCOM-PROV-E026`); `queued_items() == 0`; route still `active` |
| NEG-28 | introduce a domain-specific fault primitive, or a network/DNS/socket/TLS/ambient/filesystem/process/dynamic-load/legacy access or new dependency in the T016 surface | CHK-17/CHK-20 scans fail; the candidate is rejected |
| NEG-29 | introduce an environment-specific absolute host path, credential, or sensitive value into a committed file | CHK-21 public-safety scan fails; the candidate is rejected |
| NEG-30 | weaken/rename/remove an existing test, change a non-T016 path, implement a later task, or mark the T016 checkbox complete in the plan stage | CHK-19/CHK-24 fail; the candidate exceeds the T016 boundary |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline SHA;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each
  supporting command;
- the configure/build/CTest results, including the `ctest -N` discovered count (baseline 248 plus the
  T016 cases) and the `100% tests passed` line;
- the per-suite results for `xcom_core_matrix_unit`, `xcom_core_matrix_negative`,
  `xcom_core_matrix_recovery`, `xcom_core_matrix_concurrency`, `xcom_core_matrix_fault_boundary`, and
  `xcom_core_matrix_external_consumer`;
- the negative-case list with each NEG-ID, its discovered test name, and its exact observed outcome
  (including `XCOM-PROV-E030` for NEG-11);
- the existing-suite results proving additivity (core types, lifecycle, provider loopback, observation,
  activation plan, validation session);
- the changed-path list and the package record `reports/xcom-queue/t016-package.json` with per-file
  SHA-256;
- the register-validator results and the unchanged REF-002 disposition.

Public evidence omits host-specific, prefix, manifest, test-toolchain, temporary, and private-store
absolute paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T016 verification is complete when: the deterministic gate passes (CHK-24); every nominal check in §4
has its expected result; every negative case in §5 fails closed as stated; `SC-001` is satisfied with
≥ 20 named rejections across all four families (CHK-16); the CORE-008 boundary is proven (CHK-17); the
register validators still pass with REF-002 unchanged (CHK-23); the change is confined to the T016 test
and work-product boundary and no existing test is weakened (CHK-02, CHK-19); and a separate DeepSeek
internal review records a passing verdict with no findings. This does not constitute user acceptance,
which remains T041.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T016-STK-001 | CHK-02, CHK-04, CHK-25 | CHK-19 |
| T016-STK-002 | CHK-05, CHK-16, NEG-01…NEG-27 | CHK-13 |
| T016-STK-003 | CHK-09, CHK-12, CHK-15, CHK-18 | CHK-10 |
| T016-STK-004 | CHK-17, NEG-28 | CHK-20 |
| T016-STK-005 | CHK-02, CHK-19, CHK-23, CHK-24 | NEG-30 |
| T016-SR-001 | CHK-04, CHK-19, NEG-30 | CHK-03 |
| T016-SR-002 | CHK-03, CHK-05, NEG-01, NEG-02, NEG-03 | CHK-09 |
| T016-SR-003 | CHK-06, NEG-06, NEG-07, NEG-08, NEG-09, NEG-14, NEG-16, NEG-26 | CHK-13 |
| T016-SR-004 | CHK-07, CHK-08, NEG-05, NEG-10, NEG-11, NEG-12, NEG-13 | CHK-13 |
| T016-SR-005 | CHK-09, NEG-21, NEG-22, NEG-24, NEG-27 | CHK-03 |
| T016-SR-006 | CHK-10, CHK-11, NEG-18, NEG-20 | CHK-14 |
| T016-SR-007 | CHK-12, CHK-18, NEG-04, NEG-15, NEG-17, NEG-18, NEG-19 | CHK-11 |
| T016-SR-008 | CHK-13, NEG-05, NEG-11 | CHK-16 |
| T016-SR-009 | CHK-14, NEG-20, NEG-21, NEG-25 | CHK-11 |
| T016-SR-010 | CHK-15, NEG-18, NEG-22 | CHK-18 |
| T016-SR-011 | CHK-16, NEG-01…NEG-27 | CHK-05 |
| T016-SR-012 | CHK-17, NEG-28 | CHK-20 |
| T016-SR-013 | CHK-18, NEG-15, NEG-22 | CHK-15 |
| T016-SR-014 | CHK-19, NEG-30 | CHK-02 |
| T016-SR-015 | CHK-20, NEG-28 | CHK-02 |
| T016-SR-016 | CHK-21, NEG-29 | CHK-25 |
| T016-SR-017 | CHK-22 | CHK-25 |
| T016-SR-018 | CHK-23, NEG-30 | CHK-02 |
| T016-SR-019 | CHK-24, NEG-30 | CHK-04 |
| T016-SR-020 | CHK-25 | CHK-23 |
