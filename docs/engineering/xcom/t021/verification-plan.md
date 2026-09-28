# T021 Verification Plan — Named Checks, Commands, Negative Cases, and Evidence (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T021 (capability 007, slice `T-OBS`) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope, plus the repository-owned Fabro gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
T021's executable checks are the extended `xcom_observation_unit` fixture, the unchanged
`xcom_observation_integration` and `xcom_observation_disabled_benchmark` cases, the full-suite `ctest` run,
and the source inspections that prove bounds, immutability, authority, concurrency, offline behaviour,
additivity, and public safety; the governance checks are the deterministic gate and the T007–T010 register
validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T021 8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda
```

For T021 this gate requires:

- the six work products
  `docs/engineering/xcom/t021/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T021 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- at least one changed path that starts with `src/xverse/xcom/` (satisfied by `observation.hpp` and
  `observation.cpp`);
- `cmake -S . -B build/fabro-t021 -G Ninja -DCMAKE_BUILD_TYPE=Debug`,
  `cmake --build build/fabro-t021 --parallel 4`, a non-empty `ctest --test-dir build/fabro-t021 -N`, and
  `ctest --test-dir build/fabro-t021 --output-on-failure --parallel 4` all exit 0;
- `git diff --check 8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the admitted offline inputs. As accepted
for T012–T016 and T019/T020, if the gate's plain configure fails closed at the T025 test-toolchain
admission check, the only permitted resolution is the narrow A-1 cache seeding already recorded by those
slices: one configure carrying `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously admitted cache values seeds the gate's own
git-ignored `build/fabro-t021` cache; the gate's unmodified configure/build/`ctest` sequence then reuses it.
The hash-verified preflight is unchanged, no ambient path or network resolution is added, no admission
check is weakened, and the admitted input **values** are recorded by name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse 8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only 8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda --
git diff --check 8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t021 -N
ctest --test-dir build/fabro-t021 -R "xcom_observation" --output-on-failure
ctest --test-dir build/fabro-t021 -R "xcom_core_types|xcom_lifecycle|xcom_provider_loopback|xcom_activation_plan|xcom_validation" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with
the shared T007–T010 artifacts unchanged in substance. The existing core, lifecycle, provider, activation-
plan, validation, and observation suites must pass unchanged, proving additivity. Executed
sanitizer/static-analysis/Doxygen/benchmark measures and the delivery bundle remain with T035–T040; this
plan requires the T021 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T021 entry exists and states the immutable-record/filter/payload-policy/tap-handle scope |
| CHK-02 | Changed-path boundary | `git diff --name-only <baseline> --`; `git ls-files --others --exclude-standard` | only `observation.hpp`, `observation.cpp`, `tests/xcom/observation/core/unit_tests.cpp`, `tests/xcom/observation/integration/{test_support.hpp,integration_tests.cpp}`, the T021 work products, the one-line `tasks.md` checkbox, and the package record appear; no `CMakeLists.txt`/`*.cmake`, `xdl/`, `proto/`, `src/xverse_xdl/`, `contracts/`, `activation_plan.*`, `provider.*`, `loopback_provider.*`, `endpoint_route_lifecycle.*`, `contract.hpp`, `item.hpp`, `value.hpp`, `result.hpp`, `diagnostic.hpp`, `validation_session.*`, `stimulation_journal.*`, `disabled_tap_benchmark.cpp`, or another task's path |
| CHK-03 | Single accepted observation-contract version | run `xcom_observation_unit`; inspect `kObservationContractVersion` | `"1.0.0"` remains the only accepted version; T021 adds no second version, header, or vocabulary |
| CHK-04 | Declared observation point is mandatory | run `xcom_observation_unit` (`test_declared_tap_binding`, `test_declared_tap_rejections`) | a declaration without a valid `tap_id` yields no policy value; a valid declared identity is accepted |
| CHK-05 | Declared identity bounds | run `xcom_observation_unit` | 1- and 128-byte identities accepted; 129-byte, control-byte, and whitespace-padded identities rejected |
| CHK-06 | Filter declaration accessors | run `xcom_observation_unit` (`test_filter_declared_constraints`) | each accessor returns the exact declared constraint; unconstrained fields return `std::nullopt`; the `matches()` matrix for the same inputs is unchanged |
| CHK-07 | Declared route point, one source of truth | run `xcom_observation_unit`; inspect the policy declaration | `declared_route_point()` equals the filter's declared route identity; a tap cannot declare a route point that contradicts its filter |
| CHK-08 | Policy vocabularies and external text | run `xcom_observation_unit` (`test_validity_effect_vocabulary`, `test_declared_tap_rejections`) | payload modes, overflow policies, and validity effects accept exactly the declared values; `to_string` returns `"none"`, `"degrade-on-loss"`, `"invalidate-on-loss"`; unknown values are rejected |
| CHK-09 | Payload policy mode/bound matrix | run `xcom_observation_unit` (`test_payload_policy_bounds`, `test_controlled_payload_states`) | bounds 1 and 1024 and capacities 1 and 16 accepted; a zero-byte source yields `complete` with zero bytes; source == bound yields `complete`, source > bound yields `truncated` with exactly the bound bytes; `redacted` yields zero bytes and `redacted`; schema state stays `undecoded` |
| CHK-10 | Record self-description | run `xcom_observation_unit` (`test_record_self_description`) | the pulled record reports the declared `tap_id()` of its producing tap and every accepted baseline field unchanged; the record is a copy independent of hub storage |
| CHK-11 | Record counter projection | run `xcom_observation_unit` (`test_record_counter_projection`) | a retained record reports the post-retention `queued`/`accepted`/`dropped`/`coalesced` values; a coalesced replacement reports `coalesced == 1` with `queued` preserved; a dropped or backpressured submission produces no record |
| CHK-12 | Snapshot reports the declaration | run `xcom_observation_unit` (`test_snapshot_reports_declaration`) | the snapshot reports the declared `tap_id`, the declared `validity_effect`, and unchanged counters for the exact handle; no snapshot exists for a foreign or stale handle |
| CHK-13 | Exact handle authority unchanged | run `xcom_observation_unit` (`test_exact_tap_handles`, `test_repeated_declaration_capacity`) | capacity is 8 exact slots; foreign, stale, and closed handles produce only the accepted stable outcomes with no unrelated mutation; a duplicate close reports `tap_closed`; a recreated slot has a new generation; two taps may declare the same observation point without sharing a slot, generation, or counters |
| CHK-14 | Bounds, constants, and no allocation | inspect `observation.hpp`/`observation.cpp` and the new cases | `kMaximumObservationTaps == 8`, `kMaximumObservationRecordsPerTap == 16`, `kMaximumObservedPayloadBytes == 1024`, declared capacity 1–16, and no dynamic allocation, unbounded queue, retry, quota, or timer on any T021 path |
| CHK-15 | Metadata-only zero payload (`XCOM-INV-06`) | run `xcom_observation_unit` (`test_metadata_only`, `test_payload_policy_bounds`) | the default mode exposes zero payload bytes while retaining identity, timing, origin, correlation, route, provider, size, outcome, and the declared tap identity |
| CHK-16 | Concurrency, isolation, and no callback | run `xcom_observation_unit` (`test_synthetic_sink_concurrency`, `test_competing_reservation_interleaving`); source scan | publication and pull remain serialized with no callback under a lock; the sink disconnect/reconnect behaviour is unchanged; the new accessors introduce no shared mutable state |
| CHK-17 | Offline and domain-neutral | forbidden-API source scan; successful offline configure/build | no network/socket/resolver/TLS, ambient/secret lookup, filesystem, process, dynamic-load, or legacy access; no new dependency beyond the C++ standard library; no domain-specific, export, dashboard, storage, or query primitive |
| CHK-18 | Public safety and test bounds | scan the changed sources and work products; inspect the new cases | no credential, private address, real or proprietary payload, environment-specific absolute host path, or sensitive deployment value; fixture payloads are synthetic and ≤ 4 bytes; ≤ 4 threads, ≤ 64 iterations, no wall-clock threshold |
| CHK-19 | Doxygen for new declarations | inspect the changed headers; run the existing documentation validator | every new/changed public declaration carries a `@brief` plus the applicable ownership/lifetime/thread-safety/failure tags in the `xcom_obs` group; the admitted configuration is unchanged |
| CHK-20 | Registers and REF-002 | run the §3 register validators; inspect the REF-002 disposition | the validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; the T021/T022 attribution nuance and the legacy SESN identifiers are recorded and nothing is rewritten |
| CHK-21 | Additivity / no weakening | `git diff --name-only <baseline> -- tests/xcom`; inspect the existing suites; `ctest -N` | no existing test case, assertion, target, label, command, or expected result is removed, renamed, reordered, or weakened; the discovered test count remains 306 with the same names; the only production paths changed are the two observation units |
| CHK-22 | Deterministic gate, diff hygiene, stage rule | run the §2 gate; `git diff --check <baseline> --`; `git diff --name-only <baseline> -- specs/007-xcom-core` | exit 0 with a `ctest:` count; the diff is whitespace-clean; the only capability-document change is the T021 checkbox line, marked complete **only** at the implementation stage |
| CHK-23 | Work-product completeness and consistency | read the five plan documents; recompute file hashes | the five plan documents exist, identify T021 and the baseline, and agree on scope, vocabulary, cases, outcomes, bounds, and boundary; every §3–§4 requirement maps to ≥ 1 check |
| CHK-24 | Observation-only boundary (no export/storage) | source scan and unit inspection | the boundary exposes normalized in-process records only: no Argus, dashboard, OpenTelemetry, file, database, socket, or query element, and no `FR-023` presentation/storage claim |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no
partial value, no mutation of any tap slot, counter, generation, or retained record where the accepted
design requires rejection before mutation, no emitted normal-route item, and no output claiming acceptance.
NEG-01…NEG-19 are executable cases; NEG-20…NEG-24 are inspection/repository probes.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | declared observation-contract version `2.0.0` | no policy value; no second version accepted |
| NEG-02 | empty declared observation-point identity | no policy value; no partial declaration |
| NEG-03 | 129-byte `tap_id`, `tap_id` containing `0x1F`, or `tap_id` with leading/trailing whitespace | no policy value |
| NEG-04 | malformed non-empty filter identity (over-bound or with a control byte) | no filter or policy value; no unrelated state change |
| NEG-05 | attempt to declare a route point that contradicts the filter's route constraint | structurally impossible: the declared route point is the filter's route constraint only; the probe confirms a single source of truth |
| NEG-06 | unknown `ObservationPayloadMode` value (`static_cast`) | no policy value |
| NEG-07 | `bounded_prefix` with bound 0 or 1025 | no policy value |
| NEG-08 | non-zero bound with `metadata_only`/`redacted`; capacity 0 or 17 | no policy value |
| NEG-09 | unknown `ObservationOverflowPolicy` value | no policy value; retention vocabulary unchanged |
| NEG-10 | unknown `ObservationValidityEffect` value | no policy value; no default substituted |
| NEG-11 | foreign-hub or closed handle for poll/snapshot/acknowledge/detach | `invalid_tap_handle`; absent snapshot; no mutation of another hub's or slot's state |
| NEG-12 | stale handle after slot recreation | `invalid_tap_handle`; the recreated generation stays active and untouched |
| NEG-13 | duplicate close of an already detached tap; detach while a lossless claim is in flight | `tap_closed`; `tap_busy` with no record, counter, or slot mutation |
| NEG-14 | attach beyond the 8 fixed tap slots | `tap_capacity_exhausted`; existing taps, generations, and counters unchanged |
| NEG-15 | lossless validation with capacity unavailable before provider submission | `observation_backpressure`; provider not invoked; `backpressure_rejections` incremented and the degraded marker still under `acknowledge` control |
| NEG-16 | `drop_newest` submission against a full queue | `accepted` with `dropped` incremented; no new record; every retained record and the FIFO order unchanged |
| NEG-17 | `coalesce_latest` submission with no matching logical key | `accepted` with `dropped` incremented; no retained record replaced |
| NEG-18 | empty/invalid observation clock domain, or `commit` with an item that is not the reserved item | no record; `invalid_argument`/`invalid_reservation`; counters unchanged except the reserving tap's claim released safely |
| NEG-19 | retain a reference/view into hub storage beyond the call, or invoke a consumer callback under the lock | not constructible in the candidate: records and snapshots are value copies returned after unlock and the boundary has no callback path; the probe fails the candidate if such a path is introduced |
| NEG-20 | introduce a network/socket/TLS/ambient/filesystem/process/dynamic-load/legacy access, a new dependency, or a domain-specific or export/storage primitive in the T021 surface | CHK-17/CHK-24 scans fail; the candidate is rejected |
| NEG-21 | bind the observation boundary to a TCP listener or an external peer path | CHK-17 scan fails; the candidate is rejected |
| NEG-22 | introduce an environment-specific absolute host path, credential, or sensitive value into a committed file | CHK-18 public-safety scan fails; the candidate is rejected |
| NEG-23 | weaken, rename, or remove an existing observation test/case/assertion, change a non-T021 path, or implement T022/T023/T024 behaviour | CHK-02/CHK-21 fail; the candidate exceeds the T021 boundary |
| NEG-24 | mark the T021 checkbox complete in the plan stage, or claim an accepted/promoted REF-002 or capability requirement | CHK-20/CHK-22 fail; the candidate exceeds the T021 stage or maturity boundary |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline SHA
  `8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda`;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting
  command;
- the configure/build/CTest results, including the `ctest -N` discovered count (baseline 306) and the
  `100% tests passed` line;
- the per-case results for `xcom_observation_unit` (the nine added cases plus the eight preserved cases),
  `xcom_observation_integration`, `xcom_observation_disabled_benchmark`, and the unchanged
  core-types/lifecycle/provider/activation-plan/validation suites that prove additivity;
- the negative-case list with each NEG-ID, its discovered test name, and its exact observed outcome;
- the changed-path list and the package record `reports/xcom-queue/t021-package.json` with per-file
  SHA-256;
- the register-validator results and the unchanged REF-002 disposition.

Public evidence omits host-specific, prefix, manifest, test-toolchain, temporary, and private-store
absolute paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T021 verification is complete when: the deterministic gate passes (CHK-22); every nominal check in §4 has
its expected result; every negative case in §5 fails closed as stated; the declared observation point, the
declared route point, the declared validity-effect vocabulary, and the self-describing immutable record are
implemented and exercised (`XCOM-SW-OBS-001`, FR-011); the exact handle authority, retention policy, and
sink behaviour are unchanged (CHK-13, CHK-21); the register validators still pass with REF-002 unchanged
and nothing promoted (CHK-20); the change is confined to the T021 boundary (CHK-02) and no existing test is
weakened (CHK-21); and a separate DeepSeek internal review records a passing verdict with no findings. This
does not constitute user acceptance, which remains T041.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T021-STK-001 | CHK-02, CHK-03, CHK-22 | CHK-23 |
| T021-STK-002 | CHK-04, CHK-09, CHK-15, NEG-02…NEG-10 | CHK-14 |
| T021-STK-003 | CHK-10, CHK-12, CHK-13, CHK-16 | CHK-11 |
| T021-STK-004 | CHK-17, CHK-18, CHK-24 | NEG-20, NEG-21 |
| T021-STK-005 | CHK-02, CHK-20, CHK-21, CHK-23 | NEG-23, NEG-24 |
| T021-SR-001 | CHK-03 | NEG-01 |
| T021-SR-002 | CHK-04, CHK-05 | NEG-02, NEG-03 |
| T021-SR-003 | CHK-07 | NEG-05 |
| T021-SR-004 | CHK-06 | CHK-21 |
| T021-SR-005 | CHK-09, CHK-15 | NEG-06, NEG-07, NEG-08 |
| T021-SR-006 | CHK-08 | NEG-09, CHK-21 |
| T021-SR-007 | CHK-08 | NEG-10 |
| T021-SR-008 | CHK-10 | CHK-11 |
| T021-SR-009 | CHK-11 | CHK-13 |
| T021-SR-010 | CHK-10, CHK-21 | NEG-19 |
| T021-SR-011 | CHK-13 | NEG-11, NEG-12, NEG-13 |
| T021-SR-012 | CHK-12 | NEG-11 |
| T021-SR-013 | CHK-13 | CHK-14 |
| T021-SR-014 | CHK-14, CHK-16 | NEG-19 |
| T021-SR-015 | CHK-14, CHK-18 | CHK-09 |
| T021-SR-016 | CHK-16 | NEG-15, NEG-19 |
| T021-SR-017 | CHK-17 | NEG-20, NEG-21 |
| T021-SR-018 | CHK-18 | NEG-22 |
| T021-SR-019 | CHK-19 | CHK-23 |
| T021-SR-020 | CHK-02, CHK-21 | NEG-23 |
| T021-SR-021 | CHK-22 | NEG-24 |
| T021-SR-022 | CHK-20, CHK-23 | NEG-24 |

## 9. T-OBS slice evidence mapping (T007 register)

The T007 ownership register requires seven evidence names for the whole `T-OBS` slice (T021–T024). Only
three are contributed by T021; the remainder stay with their owning tasks and are **not** claimed here.

| Slice evidence | T021 contribution | Owner of the complete evidence |
| --- | --- | --- |
| `metadata-only-zero-payload` | CHK-15: the default mode exposes zero payload bytes while retaining every declared identity and the declared observation point | T024 completes the matrix |
| `controlled-payload-view` | CHK-09: the declared mode/bound policy and the `complete`/`truncated`/`redacted` states are validated and reported | T024 completes the matrix |
| `safe-detach` | CHK-13: duplicate close, in-flight claim, stale generation, and foreign authority are re-verified unchanged | T024 completes the matrix |
| `degraded-validity` | CHK-08/CHK-12: the declared `validityEffect` vocabulary and the unchanged degraded marker are reported only | T022 applies the effect; T024 verifies it |
| `saturation` | CHK-11: the retained-record counter projection is visible; no saturation rule changes | T022/T024 |
| `ordering` | none; CHK-21 proves FIFO/queue order is unchanged | T024 |
| `disabled-tap-performance` | none; the benchmark is re-run unchanged under the gate | T036 |

No evidence name above is reported as satisfied by T021 alone, and no slice evidence is claimed for a task
that has not produced its own exact-candidate evidence.
