# T022 Verification Plan — Named Checks, Commands, Negative Cases, and Evidence (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T022 (capability 007, slice `T-OBS`) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `7be8b9718e42e58bb1a05a486ff62e520f94567c` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope, plus the repository-owned Fabro gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
T022's executable checks are the extended `xcom_observation_unit` fixture, the unchanged
`xcom_observation_integration` and `xcom_observation_disabled_benchmark` cases, the full-suite `ctest` run,
and the source inspections that prove bounds, ordering, authority, concurrency, offline behaviour,
additivity, and public safety; the governance checks are the deterministic gate and the T007–T010 register
validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T022 7be8b9718e42e58bb1a05a486ff62e520f94567c
```

For T022 this gate requires:

- the six work products
  `docs/engineering/xcom/t022/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T022 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- at least one changed path that starts with `src/xverse/xcom/` (satisfied by `observation.hpp` and
  `observation.cpp`);
- `cmake -S . -B build/fabro-t022 -G Ninja -DCMAKE_BUILD_TYPE=Debug`,
  `cmake --build build/fabro-t022 --parallel 4`, a non-empty `ctest --test-dir build/fabro-t022 -N`, and
  `ctest --test-dir build/fabro-t022 --output-on-failure --parallel 4` all exit 0;
- `git diff --check 7be8b9718e42e58bb1a05a486ff62e520f94567c --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the admitted offline inputs. As accepted
for T012–T016, T019–T021, if the gate's plain configure fails closed at the T025 test-toolchain admission
check, the only permitted resolution is the narrow A-1 cache seeding already recorded by those slices: one
configure carrying `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously admitted cache values seeds the gate's own
git-ignored `build/fabro-t022` cache; the gate's unmodified configure/build/`ctest` sequence then reuses it.
The hash-verified preflight is unchanged, no ambient path or network resolution is added, no admission
check is weakened, and the admitted input **values** are recorded by name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse 7be8b9718e42e58bb1a05a486ff62e520f94567c
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only 7be8b9718e42e58bb1a05a486ff62e520f94567c --
git diff --check 7be8b9718e42e58bb1a05a486ff62e520f94567c --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t022 -N
ctest --test-dir build/fabro-t022 -R "xcom_observation" --output-on-failure
ctest --test-dir build/fabro-t022 -R "xcom_core_types|xcom_lifecycle|xcom_provider_loopback|xcom_activation_plan|xcom_validation" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with
the shared T007–T010 artifacts unchanged in substance. The existing core, lifecycle, provider,
activation-plan, validation, and observation suites must pass unchanged, proving additivity. Executed
sanitizer/static-analysis/Doxygen/benchmark measures and the delivery bundle remain with T035–T040; this
plan requires the T022 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T022 entry exists and states the bounded drop/coalesce/lossless-validation scope |
| CHK-02 | Changed-path boundary | `git diff --name-only <baseline> --`; `git ls-files --others --exclude-standard` | only `observation.hpp`, `observation.cpp`, `tests/xcom/observation/core/unit_tests.cpp`, the T022 work products, the one-line `tasks.md` checkbox, and the package record appear; no `CMakeLists.txt`/`*.cmake`, `xdl/`, `proto/`, `src/xverse_xdl/`, `contracts/`, `activation_plan.*`, `provider.*`, `loopback_provider.*`, `endpoint_route_lifecycle.*`, `contract.hpp`, `item.hpp`, `value.hpp`, `result.hpp`, `diagnostic.hpp`, `validation_session.*`, `stimulation_journal.*`, `disabled_tap_benchmark.cpp`, or another task's path |
| CHK-03 | Single accepted observation-contract version | run `xcom_observation_unit`; inspect `kObservationContractVersion` | `"1.0.0"` remains the only accepted version; T022 adds no second version, header, or vocabulary |
| CHK-04 | Retention vocabulary preserved | run `xcom_observation_unit`; inspect `ObservationOverflowPolicy` | exactly `drop_newest`, `coalesce_latest`, `lossless_validation`; no enumerator added, renamed, or removed; unknown value yields no policy |
| CHK-05 | Bounded `drop_newest` | run `xcom_observation_unit` (`test_drop_newest_bounded_loss`) | the queue never exceeds capacity; the oldest records are retained in FIFO order; each dropped matching submission increments `dropped` by exactly one and adds no record; the outcome is `accepted`; `experiment_validity_degraded`/`validity_state` follow the declared effect |
| CHK-06 | Bounded `coalesce_latest` | run `xcom_observation_unit` (`test_coalesce_latest_key_selection`) | a matching-key submission replaces only the newest matching record and increments `coalesced`; a no-match submission increments `dropped` and replaces nothing; unrelated FIFO order is preserved; the queue stays within capacity |
| CHK-07 | Explicit lossless reservation exactness | run `xcom_observation_unit` (`test_lossless_backpressure_pre_dispatch`, `test_lossless_reservations`) | a reservation authenticates exactly, is consumed/released exactly once, and a foreign/moved-from/completed reservation returns `invalid_reservation` |
| CHK-08 | Lossless pre-dispatch backpressure | run `xcom_observation_unit` (`test_lossless_backpressure_pre_dispatch`, `test_validity_effect_on_lossless_backpressure`) | capacity unavailable → `observation_backpressure` before provider mutation, no record, `backpressure_rejections` + 1, `experiment_validity_degraded` true; capacity recovered after cancel |
| CHK-09 | Applied validity effect on best-effort loss | run `xcom_observation_unit` (`test_validity_effect_on_best_effort_loss`, `test_validity_state_vocabulary`) | `none` → `valid`, `degrade_on_loss` → `degraded`, `invalidate_on_loss` → `invalid` for drop and coalesce loss; no status raised without a matching loss |
| CHK-10 | Lossless realizes at least degraded | run `xcom_observation_unit` (`test_validity_effect_on_lossless_backpressure`, `test_acknowledge_closes_validity_interval`) | `none`/`degrade_on_loss` → `degraded`, `invalidate_on_loss` → `invalid`; acknowledgement resets a `degraded` status to `valid` and `backpressure_rejections` to 0; an `invalid` status persists |
| CHK-11 | Realized status vocabulary and projection | run `xcom_observation_unit` (`test_validity_state_vocabulary`) | `to_string` returns `"valid"`, `"degraded"`, `"invalid"`; ordering is `valid < degraded < invalid`; `ObservationSnapshot::validity_state` is reported for an exact handle and `experiment_validity_degraded == (validity_state != valid)` |
| CHK-12 | Concurrency, isolation, and no callback | run `xcom_observation_unit` (`test_synthetic_sink_concurrency`, `test_competing_reservation_interleaving`) and `xcom_observation_integration` (concurrent/publication cases); source scan | publication, pull, retention, and validity updates stay serialized with no callback under a lock; the sink disconnect/reconnect behaviour is unchanged; the new vocabulary introduces no shared mutable state |
| CHK-13 | Bounds, constants, and no allocation | inspect `observation.hpp`/`observation.cpp` and the new cases | `kMaximumObservationTaps == 8`, `kMaximumObservationRecordsPerTap == 16`, `kMaximumObservedPayloadBytes == 1024`, declared capacity 1–16, coalescing scan ≤ capacity, and no dynamic allocation, unbounded queue, retry, rate, quota, or timer on any T022 path |
| CHK-14 | Payload boundary unchanged | diff the payload-view code; run `xcom_observation_unit`/`xcom_observation_integration` payload cases | `metadata_only`/`bounded_prefix`/`redacted` and `undecoded` schema state are byte-identical; no identity allow-list, redaction profile, or decoder is added |
| CHK-15 | Ordering preserved | run `xcom_observation_unit` (`test_drop_newest_bounded_loss`, `test_coalesce_latest_key_selection`) and the unchanged concurrent cases | retained records keep insertion order under drop/coalesce/lossless; no best-effort observer reorders the normal route |
| CHK-16 | Reservation/pull serialization | run `xcom_observation_unit` (`test_competing_reservation_interleaving`) and `xcom_observation_integration` (`test_concurrent_publication`) | competing publishers are serialized; no lost or duplicated claim; counters and status remain consistent |
| CHK-17 | Offline and domain-neutral | forbidden-API source scan; successful offline configure/build | no network/socket/resolver/TLS, ambient/secret lookup, filesystem, process, dynamic-load, or legacy access; no new dependency beyond the C++ standard library; no domain-specific, export, dashboard, storage, or query primitive |
| CHK-18 | Public safety and test bounds | scan the changed sources and work products; inspect the new cases | no credential, private address, real or proprietary payload, environment-specific absolute host path, or sensitive deployment value; fixture payloads are synthetic and ≤ 4 bytes; ≤ 4 threads, ≤ 16 record slots, no wall-clock threshold |
| CHK-19 | Doxygen for new declarations | inspect the changed headers; run the existing documentation validator | every new/changed public declaration (`ObservationValidityState`, `to_string(ObservationValidityState)`, `ObservationSnapshot::validity_state`) carries a `@brief` plus the applicable ownership/lifetime/thread-safety/failure tags in the `xcom_obs` group; the admitted configuration is unchanged |
| CHK-20 | Registers, REF-002, and preserved marker | run the §3 register validators; inspect the REF-002 disposition and the accepted lossless-marker assertions | the validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; the T022 attribution nuance and the legacy SESN identifiers are recorded and nothing is rewritten; `test_lossless_reservations`/`test_lossless_pre_dispatch_reservation` still observe the accepted degraded-marker behavior |
| CHK-21 | Deterministic gate, diff hygiene, stage rule | run the §2 gate; `git diff --check <baseline> --`; `git diff --name-only <baseline> -- specs/007-xcom-core` | exit 0 with a `ctest:` count; the diff is whitespace-clean; the only capability-document change is the T022 checkbox line, marked complete **only** at the implementation stage |
| CHK-22 | Work-product completeness and consistency | read the five plan documents; recompute file hashes | the five plan documents exist, identify T022 and the baseline, and agree on scope, vocabulary, cases, outcomes, bounds, and boundary; every §3–§4 requirement maps to ≥ 1 check |
| CHK-23 | Additivity / no weakening | `git diff --name-only <baseline> -- tests/xcom`; inspect the existing suites; `ctest -N` | no existing test case, assertion, target, label, command, or expected result is removed, renamed, reordered, or weakened; the discovered test count remains 306 with the same names; the only production paths changed are the two observation units |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behavior with no
partial value, no mutation of any tap slot, counter, generation, or retained record where the accepted
design requires rejection before mutation, no emitted normal-route item, and no output claiming acceptance.
NEG-01…NEG-04 and NEG-06…NEG-15 are executable cases; NEG-05 is a **non-constructible defensive
guard** documented by a reachability argument (see its row); NEG-16…NEG-19 are inspection/repository
probes.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | `drop_newest` submission against a full queue | `accepted` with `dropped` + 1; no new record; every retained record and the FIFO order unchanged; no route effect |
| NEG-02 | `coalesce_latest` submission with no matching logical key | `accepted` with `dropped` + 1; no retained record replaced; queue within bound |
| NEG-03 | `coalesce_latest` submission with a matching logical key | `accepted` with `coalesced` + 1; only the newest matching record replaced; unrelated records and order unchanged |
| NEG-04 | lossless capacity unavailable before provider submission | `observation_backpressure`; no reservation; no record; no provider mutation; `backpressure_rejections` + 1; realized status ≥ `degraded` |
| NEG-05 | lossless tap full at retention after a valid claim | **not constructible in the candidate**: the `reserve` precondition `size + reserved_lossless >= record_capacity` and the `commit` `--reserved_lossless` before `retain` maintain `size + reserved_lossless <= record_capacity`, so a claimed lossless slot always reaches `retain` with `size <= record_capacity - 1 < record_capacity` and `retain` always appends; the defensive `retain` backpressure branch is retained unchanged as an **uncovered guard** and no executable case exercises it |
| NEG-06 | declared `none` plus a best-effort drop/coalesce | realized status stays `valid`; `experiment_validity_degraded == false`; no inferred degradation |
| NEG-07 | declared `degrade_on_loss` plus a best-effort drop | realized status `degraded`; `experiment_validity_degraded == true` |
| NEG-08 | declared `invalidate_on_loss` plus a best-effort drop | realized status `invalid`; a further loss does not lower it |
| NEG-09 | unknown `ObservationOverflowPolicy` or `ObservationValidityEffect` value (`static_cast`) | the declaration yields no policy value; no retention or vocabulary change |
| NEG-10 | acknowledge a `degraded` interval, then a further loss; or acknowledge an `invalid` status | `degraded` → `valid` with `backpressure_rejections == 0`; `invalid` persists and is not lowered by a further loss |
| NEG-11 | foreign-hub, stale, or closed handle for snapshot/acknowledge/detach | `invalid_tap_handle` / `tap_closed` / absent snapshot; no counter or status reset on the real tap |
| NEG-12 | detach while a lossless claim is in flight, or a foreign/moved-from/completed reservation | `tap_busy`; `invalid_reservation`; no record, counter, or slot mutation |
| NEG-13 | FIFO order under drop/coalesce | the retained records keep their insertion order; the replaced record is the newest matching one |
| NEG-14 | saturation under any policy | the queue never exceeds the declared bound; `accepted + dropped + coalesced` equals the matching committed submissions |
| NEG-15 | retain a reference/view into hub storage beyond the call, or invoke a consumer callback under the lock | not constructible in the candidate: records and snapshots are value copies returned after unlock and the boundary has no callback path; the probe fails the candidate if such a path is introduced |
| NEG-16 | introduce a network/socket/TLS/ambient/filesystem/process/dynamic-load/legacy access, a new dependency, or a domain-specific or export/storage primitive in the T022 surface | CHK-17 scan fails; the candidate is rejected |
| NEG-17 | introduce an environment-specific absolute host path, credential, or sensitive value into a committed file | CHK-18 public-safety scan fails; the candidate is rejected |
| NEG-18 | weaken, rename, or remove an existing observation test/case/assertion, change a non-T022 path, change the accepted `experiment_validity_degraded` semantics, or implement T023/T024 behavior | CHK-02/CHK-20/CHK-23 fail; the candidate exceeds the T022 boundary |
| NEG-19 | implement the payload identity allow-list, a decoder, or any payload-view behavior change; or mark the T022 checkbox complete in the plan stage and claim an accepted/promoted REF-002 or capability requirement | CHK-14/CHK-20/CHK-21 fail; the candidate exceeds the T022 scope, stage, or maturity boundary |

### 5.1 Repair closure (T022-IR-F-01)

The internal review's T022-IR-F-01 finding — NEG-05 was presented as an executable negative case even
though the post-claim `retain` backpressure branch is unreachable — is closed by reclassifying NEG-05 as a
**non-constructible defensive guard** and recording its reachability argument: `reserve` claims only while
`size + reserved_lossless < record_capacity`, and `commit` decrements `reserved_lossless` before calling
`retain`, so `size + reserved_lossless <= record_capacity` is an invariant and a claimed lossless slot
always reaches `retain` with `size <= record_capacity - 1 < record_capacity`; the guard is therefore never
taken by any protocol sequence. No requirement, check, test, production behavior, or accepted scope is
weakened: the production guard is retained unchanged, and the corrected NEG-05 row, the aligned
T022-SR-003 mappings here / in `requirements.md` / `unit-specifications.md` / `implementation.md` /
`detailed-design.md` / `architecture.md`, and the re-run validators and `ctest` are the closure evidence.

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:
- the exact candidate revision and the baseline SHA
  `7be8b9718e42e58bb1a05a486ff62e520f94567c`;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting
  command;
- the configure/build/CTest results, including the `ctest -N` discovered count (baseline 306) and the
  `100% tests passed` line;
- the per-case results for `xcom_observation_unit` (the seven added cases plus the seventeen preserved
  cases), `xcom_observation_integration`, `xcom_observation_disabled_benchmark`, and the unchanged
  core-types/lifecycle/provider/activation-plan/validation suites that prove additivity;
- the negative-case list with each NEG-ID, its discovered test name, and its exact observed outcome;
- the changed-path list and the package record `reports/xcom-queue/t022-package.json` with per-file
  SHA-256;
- the register-validator results and the unchanged REF-002 disposition.

Public evidence omits host-specific, prefix, manifest, test-toolchain, temporary, and private-store
absolute paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T022 verification is complete when: the deterministic gate passes (CHK-21); every nominal check in §4 has
its expected result; every negative case in §5 fails closed as stated; the bounded best-effort drop and
coalesce modes, the explicit lossless-validation mode, the applied declared validity effect, and the
observable realized validity status are implemented and exercised (`XCOM-SW-OBS-003`, FR-013/SC-004); the
accepted payload views, schema state, exact handle authority, sink behaviour, and
`experiment_validity_degraded` lossless semantics are unchanged (CHK-08, CHK-14, CHK-20, CHK-23); the queue
bound, ordering, and accounting invariants hold (CHK-05, CHK-06, CHK-13, CHK-15); the register validators
still pass with REF-002 unchanged and nothing promoted (CHK-20); the change is confined to the T022
boundary (CHK-02) and no existing test is weakened (CHK-23); and a separate DeepSeek internal review
records a passing verdict with no findings. This does not constitute user acceptance, which remains T041.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T022-STK-001 | CHK-02, CHK-03, CHK-21 | CHK-22 |
| T022-STK-002 | CHK-05, CHK-06, CHK-09, CHK-10 | NEG-01…NEG-04, NEG-06…NEG-10, CHK-13 |
| T022-STK-003 | CHK-08, CHK-10, CHK-11 | CHK-12 |
| T022-STK-004 | CHK-17, CHK-18 | NEG-16 |
| T022-STK-005 | CHK-02, CHK-20, CHK-23 | NEG-18, NEG-19 |
| T022-SR-001 | CHK-05 | NEG-01, NEG-13, CHK-15 |
| T022-SR-002 | CHK-06 | NEG-02, NEG-03, CHK-15 |
| T022-SR-003 | CHK-07, CHK-08 | NEG-04, NEG-12 (NEG-05 is a non-constructible defensive guard, not an exercised case) |
| T022-SR-004 | CHK-13, CHK-15 | NEG-14 |
| T022-SR-005 | CHK-09 | NEG-06, NEG-07, NEG-08 |
| T022-SR-006 | CHK-08, CHK-10 | NEG-04 |
| T022-SR-007 | CHK-09, CHK-11 | NEG-12 |
| T022-SR-008 | CHK-10 | NEG-10, NEG-11 |
| T022-SR-009 | CHK-12, CHK-16 | NEG-15 |
| T022-SR-010 | CHK-13, CHK-18 | CHK-05, CHK-06 |
| T022-SR-011 | CHK-17 | NEG-16 |
| T022-SR-012 | CHK-18 | NEG-17 |
| T022-SR-013 | CHK-19 | CHK-22 |
| T022-SR-014 | CHK-02, CHK-20, CHK-23 | NEG-18 |
| T022-SR-015 | CHK-21 | NEG-19 |
| T022-SR-016 | CHK-20, CHK-22 | NEG-19 |
| T022-SR-017 | CHK-14 | NEG-19 |

## 9. T-OBS slice evidence mapping (T007 register)

The T007 ownership register requires seven evidence names for the whole `T-OBS` slice (T021–T024). T022
contributes the saturation and degraded-validity evidence; the remainder stay with their owning tasks and
are **not** claimed here.

| Slice evidence | T022 contribution | Owner of the complete evidence |
| --- | --- | --- |
| `saturation` | CHK-05/CHK-06/CHK-13/CHK-15: bounded drop/coalesce, the accounting identity, and FIFO order under a full queue | T024 completes the matrix |
| `degraded-validity` | CHK-09/CHK-10/CHK-11: the applied declared effect, the lossless "at least degraded" rule, and the realized status projection | T024 verifies the matrix |
| `metadata-only-zero-payload` | none; the accepted default is re-verified unchanged (CHK-14) | T024 |
| `controlled-payload-view` | none; the accepted mode/bound policy is re-verified unchanged (CHK-14) | T024 |
| `safe-detach` | CHK-10/NEG-11: the realized status is discarded with the slot and a stale handle cannot reset it | T024 completes the matrix |
| `ordering` | CHK-15: FIFO order under drop and coalesce is preserved | T024 |
| `disabled-tap-performance` | none; the benchmark is re-run unchanged under the gate | T036 |

No evidence name above is reported as satisfied by T022 alone, and no slice evidence is claimed for a task
that has not produced its own exact-candidate evidence.
