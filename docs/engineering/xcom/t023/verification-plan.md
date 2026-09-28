# T023 Verification Plan — Named Checks, Commands, Negative Cases, and Evidence (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T023 (capability 007, slice `T-OBS`) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `d455c70816eb784066740427a70df9235cd1287d` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope, plus the repository-owned Fabro gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
T023's executable checks are the extended `xcom_observation_unit` fixture (four added cases), the extended
`xcom_observation_integration` fixture (one added case), the unchanged
`xcom_observation_disabled_benchmark`, the full-suite `ctest` run, and the source inspections that prove
counters, isolation, authority, concurrency, offline behavior, additivity, and public safety; the
governance checks are the deterministic gate and the T007–T010 register validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T023 d455c70816eb784066740427a70df9235cd1287d
```

For T023 this gate requires:

- the six work products
  `docs/engineering/xcom/t023/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T023 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- at least one changed path that starts with `src/xverse/xcom/` (satisfied by `observation.hpp` and
  `observation.cpp`);
- `cmake -S . -B build/fabro-t023 -G Ninja -DCMAKE_BUILD_TYPE=Debug`,
  `cmake --build build/fabro-t023 --parallel 4`, a non-empty `ctest --test-dir build/fabro-t023 -N`, and
  `ctest --test-dir build/fabro-t023 --output-on-failure --parallel 4` all exit 0;
- `git diff --check d455c70816eb784066740427a70df9235cd1287d --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the admitted offline inputs. As accepted
for T012–T016, T019–T022, if the gate's plain configure fails closed at the T025 test-toolchain admission
check, the only permitted resolution is the narrow A-1 cache seeding already recorded by those slices: one
configure carrying `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously admitted cache values seeds the gate's own
git-ignored `build/fabro-t023` cache; the gate's unmodified configure/build/`ctest` sequence then reuses it.
The hash-verified preflight is unchanged, no ambient path or network resolution is added, no admission
check is weakened, and the admitted input **values** are recorded by name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse d455c70816eb784066740427a70df9235cd1287d
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only d455c70816eb784066740427a70df9235cd1287d --
git diff --check d455c70816eb784066740427a70df9235cd1287d --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t023 -N
ctest --test-dir build/fabro-t023 -R "xcom_observation" --output-on-failure
ctest --test-dir build/fabro-t023 -R "xcom_core_types|xcom_lifecycle|xcom_provider_loopback|xcom_activation_plan|xcom_validation" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with
the shared T007–T010 artifacts unchanged in substance. The existing core, lifecycle, provider,
activation-plan, validation, and observation suites must pass unchanged, proving additivity. Executed
sanitizer/static-analysis/Doxygen/benchmark measures and the delivery bundle remain with T035–T040; this
plan requires the T023 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T023 entry exists and states the synthetic-sink/failure-disconnect-isolation/visible-counters scope |
| CHK-02 | Changed-path boundary | `git diff --name-only <baseline> --`; `git ls-files --others --exclude-standard` | only `observation.hpp`, `observation.cpp`, `tests/xcom/observation/core/unit_tests.cpp`, `tests/xcom/observation/integration/integration_tests.cpp`, the T023 work products, the one-line `tasks.md` checkbox, and the package record appear; no `CMakeLists.txt`/`*.cmake`, `xdl/`, `proto/`, `src/xverse_xdl/`, `contracts/`, `activation_plan.*`, `provider.*`, `loopback_provider.*`, `endpoint_route_lifecycle.*`, `contract.hpp`, `item.hpp`, `value.hpp`, `result.hpp`, `diagnostic.hpp`, `validation_session.*`, `stimulation_journal.*`, `test_support.hpp`, `disabled_tap_benchmark.cpp`, or another task's path |
| CHK-03 | Single accepted observation-contract version | run `xcom_observation_unit`; inspect `kObservationContractVersion` | `"1.0.0"` remains the only accepted version; T023 adds no second version, header, or vocabulary |
| CHK-04 | Sink surface and copy semantics preserved | diff the sink declarations; run `xcom_observation_unit` | the constructor, `connect`, `disconnect`, `pull`, `connected` signatures and `noexcept` are unchanged; the sink is still copy-constructible and non-assignable; the new `counters()` accessor and counter members are additive only |
| CHK-05 | Outcome and policy vocabulary preserved | run `xcom_observation_unit`; inspect the enums | exactly the accepted `ObservationOutcome`, `ObservationOverflowPolicy`, `ObservationValidityEffect`, and `ObservationValidityState` values; no enumerator added, renamed, or removed; disconnect uses `sink_disconnected`, an empty pull uses `no_record`, and a stale/foreign/closed handle uses `invalid_tap_handle` |
| CHK-06 | Visible consumer counters | run `xcom_observation_unit` (`test_synthetic_sink_visible_counters`) | `counters()` reports exactly `pulled` = successful record pulls, `empty` = `no_record` pulls, `disconnected` = locally disconnected pulls, `failed` = `invalid_tap_handle` pulls; the accounting identity `pulled + empty + disconnected + failed == pull attempts` holds; `connect()`/`disconnect()` do not change the counters; records are returned in FIFO order |
| CHK-07 | Disconnect and reconnect isolation | run `xcom_observation_unit` (`test_synthetic_sink_disconnect_isolation`) | a disconnected sink returns `sink_disconnected`, consumes no record, and leaves its tap's retained records, `size`/`queued`, and counters unchanged; an unrelated sink and its tap are unaffected; `connect()` on a valid exact handle re-enables pulls (`accepted`); `connect()` on a stale/foreign/closed handle returns `invalid_tap_handle` and leaves the sink disabled without touching any tap |
| CHK-08 | Failure isolation | run `xcom_observation_unit` (`test_synthetic_sink_failure_isolation`) | a pull after the observed tap is detached/recreated, or with a foreign handle, returns `invalid_tap_handle`, increments `failed` by exactly one, and leaves the disconnected/recreated tap and every unrelated tap unchanged |
| CHK-09 | Blocking isolation and route neutrality | run `xcom_observation_unit` (`test_synthetic_sink_blocking_isolation`) and `xcom_observation_integration` (`test_synthetic_sink_route_isolation_counters`) | a connected non-pulling sink does not block, delay, reorder, or change a submission; the tap queue stays within its declared capacity with deterministic `dropped`/`coalesced` counters visible on the snapshot; the loopback route keeps its item count, order, and outcomes after a disconnect and after observer removal; the sink counters stay zero until it pulls and then reflect only its own pulls |
| CHK-10 | Read-only sink authority | source inspection of the sink; run `xcom_observation_unit` | the sink calls only `poll` and the const authentication used by `connect`; it never calls `detach`, `acknowledge`, `reserve`, `commit`, or `cancel`, and never mutates a tap, generation, counter, or record |
| CHK-11 | Concurrency and no callback | run `xcom_observation_unit` (`test_synthetic_sink_concurrency`, preserved) and `xcom_observation_integration` (concurrent cases); source scan | publication and pull remain serialized by the hub mutex; no consumer callback exists or runs under a lock; the sink counters are updated on the calling thread only |
| CHK-12 | Serialized pull/publication accounting | run `xcom_observation_unit` (`test_synthetic_sink_concurrency`) | concurrent publication and pulling produce no lost or duplicated claim, no unstable outcome, and a consistent counter/queue state |
| CHK-13 | Bounds, constants, and no allocation | inspect `observation.hpp`/`observation.cpp` and the new cases | `SyntheticSinkCounters` is four fixed 64-bit values; the sink stores one pointer, one copied handle, one bool, and four counters; `kMaximumObservationTaps == 8`, `kMaximumObservationRecordsPerTap == 16`, `kMaximumObservedPayloadBytes == 1024`, declared capacity 1–16; no dynamic allocation, unbounded queue, retry, rate, quota, or timer on any T023 path |
| CHK-14 | Accepted behavior unchanged | diff the T021/T022 regions; run `xcom_observation_unit`/`xcom_observation_integration` | contract version, filter matching, payload modes/bounds/views, schema state, record self-description, declared identities, attach/authentication/generation/capacity, retention drop/coalesce/lossless rules, the applied validity effect, the realized validity status, and the snapshot projection are byte-identical; no vocabulary value is added |
| CHK-15 | Sink counters vs tap counters | inspect `counters()` and `ObservationSnapshot`; run the new cases | the sink counters describe the consumer's pull outcomes only; the tap loss counters (`queued`/`accepted`/`dropped`/`coalesced`/`backpressure_rejections`) remain on the exact-handle snapshot and are not duplicated or reinterpreted |
| CHK-16 | Exact handle authority preserved | run `xcom_observation_unit` (`test_exact_tap_handles`, `test_synthetic_sink_failure_isolation`) | a stale/foreign/closed handle yields the accepted stable outcome; declared identity confers no authority; the sink uses only the copied exact handle |
| CHK-17 | Offline and domain-neutral | forbidden-API source scan; successful offline configure/build | no network/socket/resolver/TLS, ambient/secret lookup, filesystem, process, dynamic-load, or legacy access; no new dependency beyond the C++ standard library; no domain-specific, export, dashboard, storage, or query primitive |
| CHK-18 | Public safety and test bounds | scan the changed sources and work products; inspect the new cases | no credential, private address, real or proprietary payload, environment-specific absolute host path, or sensitive deployment value; fixture payloads are synthetic and ≤ 4 bytes; ≤ 4 threads, ≤ 16 record slots, no wall-clock threshold |
| CHK-19 | Doxygen for new declarations | inspect the changed headers; run the existing documentation validator | every new/changed public declaration (`SyntheticSinkCounters`, its four fields, `SyntheticObservationSink::counters`, the updated `pull`/`connect`/`disconnect` contract) carries a `@brief` plus the applicable ownership/lifetime/thread-safety/failure tags in the `xcom_obs` group; the admitted configuration is unchanged |
| CHK-20 | Registers, REF-002, and attribution | run the §3 register validators; inspect the REF-002 disposition and the recorded attribution | the validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; the T021-GAP-03/T022-GAP-02 handoff, the `XCOM-SW-OBS-004` attribution nuance, and the legacy SESN identifiers are recorded and nothing is rewritten |
| CHK-21 | Deterministic gate, diff hygiene, stage rule | run the §2 gate; `git diff --check <baseline> --`; `git diff --name-only <baseline> -- specs/007-xcom-core` | exit 0 with a `ctest:` count; the diff is whitespace-clean; the only capability-document change is the T023 checkbox line, marked complete **only** at the implementation stage |
| CHK-22 | Work-product completeness and consistency | read the five plan documents; recompute file hashes | the five plan documents exist, identify T023 and the baseline, and agree on scope, vocabulary, cases, outcomes, bounds, and boundary; every §3–§4 requirement maps to ≥ 1 check |
| CHK-23 | Additivity / no weakening | `git diff --name-only <baseline> -- tests/xcom`; inspect the existing suites; `ctest -N` | no existing test case, assertion, target, label, command, or expected result is removed, renamed, reordered, or weakened; the discovered test count remains 306 with the same names; the only production paths changed are the two observation units |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behavior with no
partial value, no mutation of any tap slot, counter, generation, or retained record where the accepted
design requires rejection before mutation, no emitted normal-route item, and no output claiming acceptance.
NEG-01…NEG-09 are executable cases; NEG-10…NEG-13 are inspection/repository probes.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | a pull sequence mixing records, empty pulls, a disconnect, and a stale handle | the exact counter for each outcome increments by one and the accounting identity `pulled + empty + disconnected + failed == pull attempts` holds; no counter is raised without a matching pull |
| NEG-02 | a successful pull is miscounted or an empty pull is counted as `pulled` | `test_synthetic_sink_visible_counters` fails; the candidate is rejected |
| NEG-03 | local `disconnect()` then `pull()`, then `connect()` on a valid handle | `sink_disconnected` with `disconnected` + 1 and no record consumed; the tap and unrelated sink are unchanged; reconnect restores pulls; a stale/foreign `connect()` returns `invalid_tap_handle` and mutates no tap |
| NEG-04 | pull after the observed tap is detached or its slot recreated | `invalid_tap_handle` with `failed` + 1; no record; the recreated/unrelated slot is unchanged |
| NEG-05 | a foreign-hub handle, or a tap mutated by the sink | `invalid_tap_handle` for the foreign pull with no slot mutation in either hub; CHK-10 fails if the sink detaches/acknowledges/reserves/commits/cancels |
| NEG-06 | a connected sink that never pulls while the writer saturates the tap | the route is unaffected and the queue stays within the declared bound; the sink counters stay zero until it pulls |
| NEG-07 | a saturated tap hides its loss, or a coalesce/drop counter is not visible | `test_synthetic_sink_blocking_isolation` fails to observe the bounded `dropped`/`coalesced` counters on the snapshot; the candidate is rejected |
| NEG-08 | a view/reference into hub or sink storage escaping a call, or a consumer callback under the lock | not constructible in the candidate: records and counter projections are value copies returned after unlock and the boundary has no callback path; the probe fails the candidate if such a path is introduced |
| NEG-09 | a pull call not serialized through the hub, or a counter updated off the calling thread | CHK-11/CHK-12 fail; the candidate is rejected |
| NEG-10 | introduce a network/socket/TLS/ambient/filesystem/process/dynamic-load/legacy access, a new dependency, or a domain-specific or export/storage primitive in the T023 surface | CHK-17 scan fails; the candidate is rejected |
| NEG-11 | introduce an environment-specific absolute host path, credential, or sensitive value into a committed file | CHK-18 public-safety scan fails; the candidate is rejected |
| NEG-12 | weaken, rename, or remove an existing observation test/case/assertion, change a non-T023 path, change the accepted T021/T022 retention/validity/payload behavior, add or rename an `ObservationOutcome` value, or implement T024 behavior | CHK-02/CHK-14/CHK-20/CHK-23 fail; the candidate exceeds the T023 boundary |
| NEG-13 | mark the T023 checkbox complete in the plan stage, or claim an accepted/promoted REF-002 or capability requirement, or claim the broad observation matrix / benchmark / gateway evidence | CHK-14/CHK-20/CHK-21 fail; the candidate exceeds the T023 scope, stage, or maturity boundary |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:
- the exact candidate revision and the baseline SHA
  `d455c70816eb784066740427a70df9235cd1287d`;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting
  command;
- the configure/build/CTest results, including the `ctest -N` discovered count (baseline 306) and the
  `100% tests passed` line;
- the per-case results for `xcom_observation_unit` (the four added cases plus every preserved case),
  `xcom_observation_integration` (the one added case plus every preserved case),
  `xcom_observation_disabled_benchmark`, and the unchanged core-types/lifecycle/provider/activation-plan/
  validation suites that prove additivity;
- the negative-case list with each NEG-ID, its discovered test name, and its exact observed outcome;
- the changed-path list and the package record `reports/xcom-queue/t023-package.json` with per-file
  SHA-256;
- the register-validator results and the unchanged REF-002 disposition.

Public evidence omits host-specific, prefix, manifest, test-toolchain, temporary, and private-store
absolute paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T023 verification is complete when: the deterministic gate passes (CHK-21); every nominal check in §4 has
its expected result; every negative case in §5 fails closed as stated; the synthetic sink's visible
consumer counters and the disconnect/failure/blocking isolation behavior are implemented and exercised
(`XCOM-SW-OBS-004`, FR-014/SC-005); the accepted declaration, retention, validity, payload, record, and
handle behavior and every accepted vocabulary value are unchanged (CHK-05, CHK-14, CHK-20, CHK-23); the
sink is read-only and bounded and adds no allocation, timer, retry, rate, or quota (CHK-10, CHK-13); the
register validators still pass with REF-002 unchanged and nothing promoted (CHK-20); the change is confined
to the T023 boundary (CHK-02) and no existing test is weakened (CHK-23); and a separate DeepSeek internal
review records a passing verdict with no findings. This does not constitute user acceptance, which remains
T041.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T023-STK-001 | CHK-02, CHK-03, CHK-21 | CHK-22 |
| T023-STK-002 | CHK-06, CHK-07, CHK-08, CHK-09 | NEG-01…NEG-07 |
| T023-STK-003 | CHK-10, CHK-11, CHK-12 | CHK-16 |
| T023-STK-004 | CHK-17, CHK-18 | NEG-10 |
| T023-STK-005 | CHK-02, CHK-14, CHK-20 | NEG-12, NEG-13 |
| T023-SR-001 | CHK-06 | NEG-01, NEG-02, CHK-15 |
| T023-SR-002 | CHK-06 | NEG-01 |
| T023-SR-003 | CHK-07 | NEG-03, NEG-05, CHK-09 |
| T023-SR-004 | CHK-08 | NEG-04, NEG-05 |
| T023-SR-005 | CHK-07 | NEG-03, NEG-04 |
| T023-SR-006 | CHK-09 | NEG-06, NEG-07 |
| T023-SR-007 | CHK-10 | NEG-05, NEG-08, CHK-16 |
| T023-SR-008 | CHK-11, CHK-12 | NEG-09 |
| T023-SR-009 | CHK-13 | CHK-18 |
| T023-SR-010 | CHK-17 | NEG-10 |
| T023-SR-011 | CHK-18 | NEG-11 |
| T023-SR-012 | CHK-19 | CHK-22 |
| T023-SR-013 | CHK-02, CHK-14, CHK-20, CHK-23 | NEG-12 |
| T023-SR-014 | CHK-21 | NEG-13 |
| T023-SR-015 | CHK-20, CHK-22 | NEG-13 |
| T023-SR-016 | CHK-05, CHK-14 | NEG-12, CHK-15 |

## 9. T-OBS slice evidence mapping (T007 register)

The T007 ownership register requires seven evidence names for the whole `T-OBS` slice (T021–T024). T023
contributes the synthetic-sink visible-counter and observer-isolation evidence against `SC-005`; the
remaining matrix evidence stays with its owning tasks and is **not** claimed here. The slice's required
names do not include a separate "sink-isolation" name, so T023's isolation proof is reported against the
accepted success criterion `SC-005` and contributes to `safe-detach`/`ordering`, which T024 completes.

| Slice evidence | T023 contribution | Owner of the complete evidence |
| --- | --- | --- |
| `saturation` | CHK-09/NEG-06/NEG-07: a non-pulling sink keeps the tap bounded and its loss counters visible | T024 completes the matrix |
| `degraded-validity` | none; T023 preserves the accepted T022 validity behavior unchanged (CHK-14) | T022/T024 |
| `metadata-only-zero-payload` | none; the accepted default is re-verified unchanged (CHK-14) | T024 |
| `controlled-payload-view` | none; the accepted mode/bound policy is re-verified unchanged (CHK-14) | T024 |
| `safe-detach` | CHK-08/NEG-04: a detached/recreated tap makes the copied handle fail safely without mutation, and the route continues | T024 completes the matrix |
| `ordering` | CHK-06/CHK-09: pulled records keep FIFO order and a blocked/failed sink does not reorder the route | T024 |
| `disabled-tap-performance` | none; the benchmark is re-run unchanged under the gate | T036 |

Observer isolation against `SC-005` is proven by CHK-07, CHK-08, and CHK-09 (disconnect, failure/removal,
and blocking respectively). No evidence name above is reported as satisfied by T023 alone, and no slice
evidence is claimed for a task that has not produced its own exact-candidate evidence.
