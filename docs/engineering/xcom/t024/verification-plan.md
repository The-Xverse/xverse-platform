# T024 Verification Plan — Named Checks, Commands, Negative Cases, and Evidence (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T024 (capability 007, slice `T-OBS`) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 (observation acceptance matrix) |
| Repair revision | 3 — terminal review R-01 governance repair (see §10) |
| Baseline revision | `76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6` |
| Repair baseline | `d50bb48f45e422b8a7018710b1ac50cdadbcf8ed` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope, plus the repository-owned Fabro gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
T024's executable checks are the extended `xcom_observation_unit` fixture (seven added cases), the extended
`xcom_observation_integration` fixture (two added cases), the unchanged `xcom_observation_disabled_benchmark`,
the full-suite `ctest` run, and the source inspections that prove payload safety, bounds, ordering, validity,
detach, neutrality, offline behavior, additivity, and public safety; the governance checks are the
deterministic gate and the T007–T010 register validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T024 76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6
```

For T024 this gate requires:

- the six work products
  `docs/engineering/xcom/t024/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T024 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- at least one changed path that starts with `tests/` (satisfied by the two edited observation fixtures);
- `cmake -S . -B build/fabro-t024 -G Ninja -DCMAKE_BUILD_TYPE=Debug`,
  `cmake --build build/fabro-t024 --parallel 4`, a non-empty `ctest --test-dir build/fabro-t024 -N`, and
  `ctest --test-dir build/fabro-t024 --output-on-failure --parallel 4` all exit 0;
- `git diff --check 76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6 --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the admitted offline inputs. As accepted
for T012–T016 and T019–T023, if the gate's plain configure fails closed at the T025 test-toolchain admission
check, the only permitted resolution is the narrow A-1 cache seeding already recorded by those slices: one
configure carrying `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously admitted cache values seeds the gate's own
git-ignored `build/fabro-t024` cache; the gate's unmodified configure/build/`ctest` sequence then reuses it.
The hash-verified preflight is unchanged, no ambient path or network resolution is added, no admission
check is weakened, and the admitted input **values** are recorded by name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse 76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only 76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6 --
git diff --check 76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6 --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t024 -N
ctest --test-dir build/fabro-t024 -R "xcom_observation" --output-on-failure
ctest --test-dir build/fabro-t024 -R "xcom_core_types|xcom_lifecycle|xcom_provider_loopback|xcom_activation_plan|xcom_validation" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with
the shared T007–T010 artifacts unchanged in substance. The existing core, lifecycle, provider,
activation-plan, validation, and observation suites must pass unchanged, proving additivity. Executed
sanitizer/static-analysis/Doxygen/benchmark measures and the delivery bundle remain with T035–T040; this
plan requires the T024 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T024 entry exists and states the metadata-only/payload-view/redaction/truncation/ordering/saturation/degraded-validity/safe-detach test scope |
| CHK-02 | Changed-path boundary | `git diff --name-only <baseline> --`; `git ls-files --others --exclude-standard` | only `tests/xcom/observation/core/unit_tests.cpp`, `tests/xcom/observation/integration/integration_tests.cpp`, the T024 work products, the one-line `tasks.md` checkbox, and the package record appear; no `.hpp`/`.cpp` production unit, `CMakeLists.txt`/`*.cmake`, `xdl/`, `proto/`, `src/xverse_xdl/`, `contracts/`, `test_support.hpp`, `disabled_tap_benchmark.cpp`, or another task's path |
| CHK-03 | Case inventory and harness | read the two edited fixtures; inspect `main()` | the seven new unit cases and two new integration cases exist, each with a `@brief` naming its requirement/evidence; every case is registered in `main()`; the helpers construct policies through `ObservationTapSpec::create` |
| CHK-04 | Discovery and additivity of the executable surface | build; `ctest -N`; run `xcom_observation_unit`/`xcom_observation_integration` | `Total Tests: 306` is unchanged; the observation executables pass as one CTest test each; no target, test name, label, or command changed; unit case count grows 28 → 35 and integration 8 → 10 with all existing cases preserved |
| CHK-05 | Metadata-only zero-payload matrix | run `xcom_observation_unit` (`test_observation_metadata_and_payload_view_matrix`) | every `metadata_only` record exposes zero bytes with `omitted` and `undecoded`, reports the full `source_payload_size`, preserves every normalized identity for all four families and 0/1/4-byte sources; `accepted == 12` and `queued == 12` for the 12-item batch; 100 % of emitted records pulled exactly once |
| CHK-06 | Controlled payload-view matrix | run `xcom_observation_unit` (`test_observation_metadata_and_payload_view_matrix`) | every row of `detailed-design.md` §5.1 matches exactly (complete/truncated/redacted/omitted, exact leading bytes, `undecoded`); bound 1 and `kMaximumObservedPayloadBytes` accepted; bound 0, bound > maximum, and a non-zero bound on a non-prefix mode rejected |
| CHK-07 | Observation vocabulary preserved | inspect the enums; run both observation executables | exactly the accepted `ObservationOutcome`, `ObservationOverflowPolicy`, `ObservationValidityEffect`, `ObservationValidityState`, and `PayloadViewState` values; no enumerator added, renamed, or removed |
| CHK-08 | Ordering matrix | run `xcom_observation_unit` (`test_observation_ordering_matrix`) | `drop_newest` returns `1,2,3,4`; `coalesce_latest` returns `1,2,3,5` with `coalesced == 1`; the pulled sequence is strictly increasing; two taps on one hub keep independent FIFO order and counters |
| CHK-09 | Saturation bound matrix | run `xcom_observation_unit` (`test_observation_saturation_bound_matrix`) | §5.3 rows match exactly; every queue stays at or below its declared capacity; accounting identities hold; `coalesce_latest` replaces only the newest matching key; lossless rejection precedes any mutation and recovery commits |
| CHK-10 | Lossless pre-mutation rejection and recovery | run `xcom_observation_unit` (`test_observation_saturation_bound_matrix`) and `xcom_observation_integration` (`test_observation_route_saturation_safe_detach_matrix`) | a matching submission when capacity is unavailable returns `observation_backpressure` with `backpressure_rejections == 1`, `queued` unchanged, and no route mutation; after cancel/acknowledge/drain the capacity recovers and a later commit succeeds |
| CHK-11 | Degraded-validity effect matrix | run `xcom_observation_unit` (`test_observation_validity_interval_matrix`) | §5.2 rows match exactly; the lossless required loss realizes at least `degraded`; `experiment_validity_degraded == (validity_state != valid)` |
| CHK-12 | Validity interval and discard semantics | run `xcom_observation_unit` (`test_observation_validity_interval_matrix`) | the realized status never decreases without acknowledgement/detach; `acknowledge` closes a `degraded` interval to `valid` and `invalid` persists; detach/recreation discards the status and counters and starts `valid` |
| CHK-13 | Safe-detach and ownership matrix | run `xcom_observation_unit` (`test_observation_safe_detach_matrix`) | detach discards only its own records; `tap_closed` on a repeated close; `tap_busy` while a claim is in flight; `invalid_tap_handle` for a stale/foreign/unknown handle; a recreated generation is independent; no unrelated tap is mutated |
| CHK-14 | Route ordering and neutrality (SC-005) | run `xcom_observation_integration` (`test_observation_route_ordering_neutrality_matrix`, `test_observation_route_saturation_safe_detach_matrix`) | the route item count, `per_route_fifo` receive order, and every delivery outcome are unchanged while an observer is blocked, removed, disconnected, or fails; a detached handle no longer authenticates |
| CHK-15 | Batch completeness and counter projection | run `xcom_observation_unit` (`test_observation_metadata_and_payload_view_matrix`, `test_observation_record_edge_value_matrix`) | every matched record is retained and pulled exactly once while within bound; `accepted`/`queued` report the batch exactly; the pulled record's `counters()` equals the retention-time projection |
| CHK-16 | Normalized-record matrix (`XCOM-SW-OBS-005`) | run `xcom_observation_unit` (`test_observation_normalized_record_matrix`, `test_observation_record_edge_value_matrix`) | for every family × origin × provider outcome the full normalized field set round-trips exactly; records are value copies; an absent sequence is not defaulted; source/observation clocks are preserved independently |
| CHK-17 | Argus boundary / no export primitive | forbidden-vocabulary scan of the changed tests; inspect the public surface | no dashboard, storage, query, presentation, export, OpenTelemetry, adapter, or provider-specific/address/transport accessor is introduced or required |
| CHK-18 | Matrix self-bounds and deterministic concurrency | inspect `detailed-design.md` §6 and the test sources; run the `test_observation_saturation_bound_matrix` concurrency sub-check (`T24-TS-003`) | ≤ 4 threads, ≤ 64 items, ≤ 16 record slots, ≤ 4-byte payloads; no unbounded loop/wait/retry; no wall-clock verdict; four competing lossless publishers over a capacity-4 tap yield exactly four commits and twelve backpressure rejections with four distinct retained sequences and a consistent counter/queue state across three repeated bounded runs |
| CHK-19 | No callback under an X-COM lock | source inspection plus the `T24-TS-003` concurrency sub-check | the boundary is pull-only; the new cases install no callback and observe consistent counter/queue state |
| CHK-20 | Additivity / no weakening | `git diff --name-only <baseline> --`; `git diff`; inspect the existing cases | the production delta is empty; the only test changes are appended cases and their `main()` wiring; no existing case, assertion, target, label, command, threshold, or accepted value is removed, renamed, reordered, or weakened |
| CHK-21 | Offline and domain-neutral | forbidden-API source scan; successful offline configure/build | no network/socket/resolver/TLS, ambient/secret lookup, filesystem, process, dynamic-load, or legacy access; only the C++ standard library plus the admitted test dependencies; no domain-specific, export, dashboard, storage, or query primitive |
| CHK-22 | Public safety and test bounds | scan the changed tests and work products | no credential, private address, real or proprietary payload, environment-specific absolute host path, or sensitive deployment value; fixture payloads are synthetic and ≤ 4 bytes |
| CHK-23 | Doxygen for new cases | inspect the changed fixtures; run the existing documentation validator | every new case/helper carries a `@brief` (and the applicable tags) in the existing file style; the file-block traceability note names T024; the admitted configuration is unchanged |
| CHK-24 | Deterministic gate, diff hygiene, stage rule | run the §2 gate; `git diff --check <baseline> --`; `git diff --name-only <baseline> -- specs/007-xcom-core` | exit 0 with a `ctest:` count; the diff is whitespace-clean; the only capability-document change is the T024 checkbox line, marked complete **only** at the implementation stage |
| CHK-25 | Work-product completeness, registers, and REF-002 | read the five plan documents; run the §3 register validators; inspect the REF-002 disposition | the five plan documents exist, identify T024 and the baseline, and agree on scope/cases/outcomes/bounds/boundary; every §3–§4 requirement maps to ≥ 1 check; the validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no
partial value, no mutation of any tap slot, counter, generation, or retained record where the accepted
design requires rejection before mutation, no emitted normal-route item, and no output claiming acceptance.
NEG-01…NEG-28 are executable or source-inspection cases realized by the named checks and the case
assertions; NEG-29 is the additivity/stage repository probe.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | change a non-T024 path, weaken/rename/remove an existing observation case/target/label, or change a build file | CHK-02/CHK-04/CHK-20 fail; the candidate exceeds the T024 boundary |
| NEG-02 | a metadata policy leaks payload bytes or reports a non-`omitted` view/schema state | CHK-05 fails; the candidate is rejected |
| NEG-03 | a metadata record omits a normalized identity, miscounts `source_payload_size`, or a matched record is not retained/pulled | CHK-05/CHK-15 fail |
| NEG-04 | `bounded_prefix` reports `complete` when the source exceeds the bound, or copies the wrong prefix | CHK-06 fails |
| NEG-05 | a prefix bound of zero or above `kMaximumObservedPayloadBytes` is accepted | CHK-06 fails |
| NEG-06 | `redacted` exposes bytes or reports a non-`redacted` view | CHK-06 fails |
| NEG-07 | a decode/schema success (`state != undecoded`) is reported | CHK-06 fails |
| NEG-08 | retained records are not FIFO, or a coalesced replacement does not move to the newest position | CHK-08 fails |
| NEG-09 | pulling from one tap reorders or consumes another tap's records | CHK-08 fails |
| NEG-10 | a `drop_newest` queue exceeds its declared bound | CHK-09 fails |
| NEG-11 | a dropped record is not reflected in `dropped`, or the accounting identity fails | CHK-09 fails |
| NEG-12 | `coalesce_latest` replaces a non-matching logical key | CHK-09 fails |
| NEG-13 | a coalesce loss is not counted in `coalesced` | CHK-09 fails |
| NEG-14 | `lossless_validation` mutates the provider/queue before rejecting | CHK-10 fails |
| NEG-15 | a lossless rejection is not visible in `backpressure_rejections`/validity, or capacity does not recover | CHK-10 fails |
| NEG-16 | the declared validity effect is not applied on a best-effort loss | CHK-11 fails |
| NEG-17 | a lossless backpressure is not raised to at least `degraded` | CHK-11 fails |
| NEG-18 | the realized validity status decreases without acknowledgement/detach | CHK-11/CHK-12 fail |
| NEG-19 | acknowledgement does not close a `degraded` interval or lowers `invalid`, or detach/recreation does not discard the status | CHK-12 fails |
| NEG-20 | detach discards another tap's records, or a stale/foreign/claimed/closed handle is handled wrongly | CHK-13 fails |
| NEG-21 | a stale-generation or foreign handle still authenticates after detach | CHK-13 fails |
| NEG-22 | removing/blocking/disconnecting/failing an observer changes the route item count, FIFO order, or delivery outcome | CHK-14 fails |
| NEG-23 | the route accepts or reorders differently after observer removal | CHK-14 fails |
| NEG-24 | a normalized-record field is lost or renamed, or a record is not a value copy | CHK-16 fails |
| NEG-25 | a dashboard/storage/query/presentation/export/OpenTelemetry/adapter primitive appears in the T024 surface | CHK-17 fails |
| NEG-26 | the matrix uses an unbounded loop/thread/wait/retry or a wall-clock verdict | CHK-18 fails |
| NEG-27 | introduce network/socket/TLS/ambient/filesystem/process/dynamic-load/legacy access, a new dependency, or a domain-specific primitive into the T024 surface | CHK-21 fails |
| NEG-28 | introduce an environment-specific absolute host path, credential, or sensitive value into a committed file | CHK-22 fails |
| NEG-29 | change a non-T024 path, change an accepted T021–T023 behavior or vocabulary, implement a later task, promote a REF-002/capability requirement, or mark the T024 checkbox in the plan stage | CHK-02/CHK-20/CHK-24/CHK-25 fail; the candidate exceeds the T024 scope, stage, or maturity boundary |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline SHA
  `76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6`;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting
  command;
- the configure/build/CTest results, including the `ctest -N` discovered count (baseline 306) and the
  `100% tests passed` line;
- the per-case results for `xcom_observation_unit` (the seven added cases plus every preserved case),
  `xcom_observation_integration` (the two added cases plus every preserved case),
  `xcom_observation_disabled_benchmark`, and the unchanged core-types/lifecycle/provider/activation-plan/
  validation suites that prove additivity;
- the `T24-TS-003` concurrency sub-check evidence: four publishers × four bounded attempts over a
  capacity-4 lossless tap yielding exactly four commits and twelve `observation_backpressure` rejections,
  four distinct retained sequences, a consistent counter/queue state, and three identical repeated-run
  outcomes;
- the evidence-name mapping: `metadata-only-zero-payload` (TS-001, TS-006), `controlled-payload-view`
  (TS-001, TS-007), `ordering` (TS-002, TS-008), `saturation` (TS-003, TS-009), `degraded-validity`
  (TS-004, TS-009), `safe-detach` (TS-005, TS-008, TS-009);
- the negative-case list with each NEG-ID, its realizing check, and its exact observed outcome;
- the changed-path list and the package record `reports/xcom-queue/t024-package.json` with per-file
  SHA-256;
- the register-validator results and the unchanged REF-002 disposition.

Public evidence omits host-specific, prefix, manifest, test-toolchain, temporary, and private-store
absolute paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T024 verification is complete when: the deterministic gate passes (CHK-24); every nominal check in §4 has
its expected result; every negative case in §5 fails closed as stated; `SC-003`, `SC-004`, and `SC-005` are
satisfied with the seven `T-OBS` evidence names completed (`disabled-tap-performance` excepted, T036); the
accepted `metadata_only`/`bounded_prefix`/`redacted`, retention, validity, detach, and normalized-record
behavior and every accepted vocabulary value are unchanged (CHK-07, CHK-20); the register validators still
pass with REF-002 unchanged and nothing promoted (CHK-25); the change is confined to the `tests/`
boundary (CHK-02) and no existing test is weakened (CHK-04, CHK-20); and a separate DeepSeek internal
review records a passing verdict with no findings. This does not constitute user acceptance, which remains
T041.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T024-STK-001 | CHK-02, CHK-04, CHK-25 | CHK-03 |
| T024-STK-002 | CHK-05, CHK-07, CHK-08, CHK-09, CHK-11, CHK-13, CHK-14 | CHK-10, CHK-12 |
| T024-STK-003 | CHK-16, CHK-17 | CHK-15 |
| T024-STK-004 | CHK-18, CHK-21, CHK-22 | CHK-19 |
| T024-STK-005 | CHK-02, CHK-20, CHK-24 | NEG-01, NEG-29 |
| T024-SR-001 | CHK-02, CHK-04, CHK-20 | NEG-01 |
| T024-SR-002 | CHK-03, CHK-04 | CHK-23 |
| T024-SR-003 | CHK-05 | NEG-02, NEG-03 |
| T024-SR-004 | CHK-05, CHK-15 | NEG-03 |
| T024-SR-005 | CHK-06 | NEG-04, NEG-05 |
| T024-SR-006 | CHK-06 | NEG-06, NEG-07 |
| T024-SR-007 | CHK-08 | NEG-08, NEG-09 |
| T024-SR-008 | CHK-09 | NEG-10, NEG-11 |
| T024-SR-009 | CHK-09 | NEG-12, NEG-13 |
| T024-SR-010 | CHK-10 | NEG-14, NEG-15 |
| T024-SR-011 | CHK-11 | NEG-16, NEG-17 |
| T024-SR-012 | CHK-11, CHK-12 | NEG-18, NEG-19 |
| T024-SR-013 | CHK-13 | NEG-20, NEG-21 |
| T024-SR-014 | CHK-14 | NEG-22, NEG-23 |
| T024-SR-015 | CHK-16 | NEG-24, CHK-15 |
| T024-SR-016 | CHK-17 | NEG-25 |
| T024-SR-017 | CHK-18 | NEG-26 |
| T024-SR-018 | CHK-18, CHK-19 | NEG-26 |
| T024-SR-019 | CHK-21 | NEG-27 |
| T024-SR-020 | CHK-22 | NEG-28 |
| T024-SR-021 | CHK-02, CHK-20 | NEG-01, NEG-29 |
| T024-SR-022 | CHK-23 | CHK-25 |
| T024-SR-023 | CHK-24 | NEG-29 |
| T024-SR-024 | CHK-25 | NEG-29 |

## 9. T-OBS slice evidence mapping (T007 register)

The T007 ownership register requires seven evidence names for the whole `T-OBS` slice (T021–T024). T024
completes six of them and leaves the benchmark with T036.

| Slice evidence | T024 contribution | Owning check/case |
| --- | --- | --- |
| `metadata-only-zero-payload` | zero payload bytes with every normalized identity for all families and source sizes | CHK-05; `test_observation_metadata_and_payload_view_matrix`, `test_observation_normalized_record_matrix` |
| `controlled-payload-view` | `complete`/`truncated`/`redacted`/`omitted` boundary table with no decode claim | CHK-06; `test_observation_metadata_and_payload_view_matrix`, `test_observation_record_edge_value_matrix` |
| `ordering` | per-tap FIFO under drop/coalesce, multi-tap independence, route FIFO invariance | CHK-08, CHK-14; `test_observation_ordering_matrix`, `test_observation_route_ordering_neutrality_matrix` |
| `saturation` | min/max-bound drop, coalesce key selection, lossless pre-mutation rejection/recovery with exact counters | CHK-09, CHK-10; `test_observation_saturation_bound_matrix`, `test_observation_route_saturation_safe_detach_matrix` |
| `degraded-validity` | applied declared effect, lossless at-least-degraded, monotonicity, acknowledgement, discard on detach | CHK-11, CHK-12; `test_observation_validity_interval_matrix`, `test_observation_route_saturation_safe_detach_matrix` |
| `safe-detach` | detach/ownership matrix and route neutrality after removal/blocking/failure | CHK-13, CHK-14; `test_observation_safe_detach_matrix`, `test_observation_route_ordering_neutrality_matrix`, `test_observation_route_saturation_safe_detach_matrix` |
| `disabled-tap-performance` | none; the benchmark is re-run unchanged under the gate | T036 |

No evidence name above is claimed beyond what its own exact-candidate evidence shows; no slice evidence is
claimed for a task that has not produced its own exact-candidate evidence.

## 10. Revision 3 — R-01 governance-repair verification (baseline `d50bb48f45e422b8a7018710b1ac50cdadbcf8ed`)

This plan is written **before** the repair edits. It verifies that R-01 is closed: the current ownership
and analysis records no longer assert the false checkbox-open reason, the accepted predecessor artifacts
are preserved with a dated successor note, and the external-acceptance gate stays explicitly open. It does
not re-accept any task. Weakening an expected result below is a verification-contract change requiring a
successor candidate.

### 10.1 Deterministic gate (primary)

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T024 d50bb48f45e422b8a7018710b1ac50cdadbcf8ed
```

This requires the six T024 work products, the T024 checkbox `[X]`, and a changed-path inventory confined
to the R-01 scope. It exits `0`; the implementation record supplies the `ctest:` count for the re-run
observation suites.

### 10.2 Supporting commands (offline, repository-owned)

```sh
git rev-parse d50bb48f45e422b8a7018710b1ac50cdadbcf8ed
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_task_ownership.py --self-test
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_requirements_traceability.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --self-test
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --check-human
python3 scripts/validate_xcom_architecture_contracts.py --self-test
python3 scripts/validate_xcom_unit_design.py --verify
python3 scripts/validate_xcom_unit_design.py --check-human
python3 scripts/validate_xcom_unit_design.py --self-test
python3 /home/jefferson/x-verse_fabric/automation/run_xcom_system_tests.py unit
python3 /home/jefferson/x-verse_fabric/automation/run_xcom_system_tests.py integration
python3 /home/jefferson/x-verse_fabric/automation/run_xcom_system_tests.py validation
python3 -m pytest tests/test_xcom_task_ownership_reconciliation.py -q
git diff --name-only d50bb48f45e422b8a7018710b1ac50cdadbcf8ed --
git diff --check d50bb48f45e422b8a7018710b1ac50cdadbcf8ed --
```

Every register validator mode must exit `0`; `unit`/`integration` must report 100 % tests passed (306/306
CTest unchanged); `validation` must report a positive pytest pass count. `git rev-parse` must print the
repair baseline.

### 10.3 Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| R01-CHK-01 | Delivered status present | `validate_xcom_task_ownership.py --verify`; read the register | T012–T016 and T021–T024 read `delivered`; no entry for them reads `unreconciled` or claims the checkbox is open |
| R01-CHK-02 | Exact delivered revisions | read the register reconciliation entries | each delivered task records exactly the §11.3 revision |
| R01-CHK-03 | Projection integrity | `--check-human` | exit 0; Markdown is the byte-stable projection |
| R01-CHK-04 | Analysis disposition | read `specs/007-xcom-core/analysis.md` A12 and the dated successor note | A12 no longer says checkboxes require reconciliation; it records delivered + pending external acceptance |
| R01-CHK-05 | Accepted predecessor preserved | `git diff --name-only <baseline> -- docs/engineering/xcom/t008 docs/engineering/xcom/t009 docs/engineering/xcom/t010` | empty; predecessor bytes unchanged; the successor note supersedes their wording |
| R01-CHK-06 | Task-ownership validator self-test | `--self-test` | positive fixture passes; every negative fixture rejects with its declared class |
| R01-CHK-07 | Requirements validator self-test | `validate_xcom_requirements_traceability.py --self-test` | positive fixture passes; `NEG-17` rejects with `MATURITY_INVALID` via the delivered coverage branch |
| R01-CHK-08 | Adjacent validators unchanged | `validate_xcom_architecture_contracts.py --self-test`; `validate_xcom_unit_design.py --self-test` | both pass unchanged; neither needs a source edit |
| R01-CHK-09 | Acceptance / maturity preserved | read the register, T008 register, A12 | no task is `accepted` except the pre-existing T025; no maturity is promoted; `ref002_disposition == unchanged` |
| R01-CHK-10 | Deterministic gate | `xcom_feature_gate.py verify T024 <baseline>` | exit 0 with the re-run observation suite count |
| R01-CHK-11 | Unit / integration re-run | `run_xcom_system_tests.py unit`; `integration` | 100 % tests passed; 306/306 CTest; no target/name/label change |
| R01-CHK-12 | Validation re-run | `run_xcom_system_tests.py validation` | positive pytest pass count |
| R01-CHK-13 | Changed-path boundary | `git diff --name-only <baseline> --`; `git ls-files --others --exclude-standard` | only the §11.5 paths, including the single new `tests/test_xcom_task_ownership_reconciliation.py`; no other `tests/` path, and no `src/`, `xdl/`, `cmake/`, `CMakeLists.txt`, `proto/`, or `t008/t009/t010` content |
| R01-CHK-14 | Public safety and diff hygiene | `git diff --check <baseline> --`; scan register, projection, and A12 | whitespace-clean; no absolute host path, credential, private address, or sensitive value |
| R01-CHK-15 | Governance regression test | `python3 -m pytest tests/test_xcom_task_ownership_reconciliation.py -q`; `xcom_feature_gate.py verify T024 <baseline>` | seven passing cases; the gate finds the `tests/` change and reports the CTest count |

### 10.4 Negative cases

| ID | Injected defect | Expected |
| --- | --- | --- |
| R01-NEG-01 | a delivered task's `status` reverted to `unreconciled` | `GATE_INVALID` (`exit 8`) from the task-ownership validator |
| R01-NEG-02 | a delivered task's `revision` set to `null` | `GATE_INVALID` |
| R01-NEG-03 | a delivered task's `revision` set to a short/wrong SHA | `GATE_INVALID` |
| R01-NEG-04 | a delivered task's `reason` emptied | `GATE_INVALID` |
| R01-NEG-05 | a delivered task relabelled `accepted` with no accepted record | `GATE_INVALID` |
| R01-NEG-06 | `task-ownership.md` tampered by one byte | `DETERMINISM_INVALID` (`exit 9`) |
| R01-NEG-07 | `XCOM-SW-CORE-001` (owning task T012, delivered) reconciliation reason dropped | `MATURITY_INVALID` (`exit 8`) from the requirements validator |
| R01-NEG-08 | an absolute host path inserted into `docs/engineering/xcom/task-ownership.json` or its projected `task-ownership.md` reason | `PUBLIC_SAFETY_INVALID` (`exit 10`) from `validate_xcom_task_ownership.py` |
| R01-NEG-09 | a delivered entry's reason reverted to the old checkbox-open text | `pytest tests/test_xcom_task_ownership_reconciliation.py` fails its delivered-reason assertion |

R01-NEG-01..08 inject their defect into an input a validator actually scans: the task-ownership validator
scans `task-ownership.json` and `task-ownership.md`, and the requirements-traceability validator scans the
T008 register/matrix. The public-safety class is `PUBLIC_SAFETY_INVALID` = `exit 10` in
`validate_xcom_task_ownership.py` and `exit 11` in `validate_xcom_requirements_traceability.py`; R01-NEG-08 is
bound to the former. `specs/007-xcom-core/analysis.md` is not scanned by any validator, so its public-safety
disposition is the R01-CHK-14 inspection and is **not** claimed as a validator negative. R01-NEG-09 is a
governance-regression-test case (R01-CHK-15), not a validator fixture. Accepted-predecessor preservation
(`docs/engineering/xcom/t00{8,9,10}`) is a repository-inventory check (`git diff --name-only`, R01-CHK-05 and
R01-CHK-13) with no validator exit class, so it has no R01-NEG fixture.

### 10.5 Evidence retention

Retain the exact register/projection/A12 diffs, each validator mode's exit status and bounded output, the
`git rev-parse`/`git diff` inventories, and the feature-gate result, all bound to the successor candidate
revision. Record commands, tool versions, and environment identity in
`docs/engineering/xcom/t024/implementation.md`. Missing, stale, or mismatched evidence cannot support
acceptance.

### 10.6 Exit criteria

R-01 is closed for the successor candidate only when: R01-CHK-01..15 pass; every R01-NEG rejects with its
declared class; no production or accepted-predecessor path changed; and the analysis note records that
external Codex review and explicit user acceptance remain pending. Passing these checks does not accept
any task; acceptance remains a separate explicit user gate.

### 10.7 Requirement-to-check coverage (repair view)

| Requirement | Checks |
| --- | --- |
| `T024-R01-SR-001` | R01-CHK-01, R01-CHK-02, R01-CHK-03, R01-CHK-13; R01-NEG-01..05 |
| `T024-R01-SR-002` | R01-CHK-04, R01-CHK-14 |
| `T024-R01-SR-003` | R01-CHK-05, R01-CHK-13 (repository-inventory checks; no validator negative applies) |
| `T024-R01-SR-004` | R01-CHK-06, R01-CHK-07, R01-CHK-08; R01-NEG-01..05, R01-NEG-07 |
| `T024-R01-SR-005` | R01-CHK-09; R01-NEG-05 |
| `T024-R01-SR-006` | R01-CHK-10, R01-CHK-11, R01-CHK-12 |
| `T024-R01-SR-007` | R01-CHK-13 |
| `T024-R01-SR-008` | R01-CHK-14; R01-NEG-08 |
| `T024-R01-SR-009` | R01-CHK-15; R01-NEG-09 |

No repair requirement is left without at least one check, and no check claims acceptance.
