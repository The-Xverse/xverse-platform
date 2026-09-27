# T022 Implementation Record — Bounded Best-Effort Drop/Coalesce, Explicit Lossless Validation, and Applied Validity Effect

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T022 (capability 007, slice `T-OBS`) |
| Stage / role | implementation → implementation record |
| Revision | 1 |
| Authorized baseline | `7be8b9718e42e58bb1a05a486ff62e520f94567c` |
| Predecessor | T021 reviewed terminal package (`docs/engineering/xcom/t021/`) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned at the workflow checkpoint) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | `docs/engineering/xcom/t022/internal-review.json` (separate read-only DeepSeek review, produced by the review stage) |
| Package record | `reports/xcom-queue/t022-package.json` (produced by the deterministic package action) |
| Authorization | ACC005/ACC010/ACC011/ACC014/ACC015; ADR-0016; ADR-0018; ADR-0019; ADR-0020; `specs/007-xcom-core/tasks.md` T022 |
| Maturity | Prototype-only retention-and-validity layer implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T022 implements the bounded slice required by the T022 task entry: *"Implement bounded best-effort
drop/coalesce and explicit lossless-validation modes."*

The candidate realizes the **retention and validity half** of the accepted observation boundary described
by `XCOM-SW-OBS-003` (FR-013/SC-004, design unit `XCOM-DU-013`): the declared `drop_newest`,
`coalesce_latest`, and `lossless_validation` overflow policies keep every tap queue within its declared
finite capacity; every matching drop or coalesce loss is counted and reflected in validation status; and
the declared `ObservationValidityEffect` is now **applied** to a realized `ObservationValidityState`
(`valid < degraded < invalid`) exposed as an immutable, value-owned projection on the exact-handle
`ObservationSnapshot`. A lossless-validation backpressure realizes at least `degraded`, exactly preserving
the accepted `experiment_validity_degraded` marker semantics; acknowledging the exact handle closes a
`degraded` interval while an `invalid` status persists until detach or slot recreation.

Every accepted baseline behaviour that T022 does not own — contract version `1.0.0`, filter matching,
payload mode/bound validation, payload views, `undecoded` schema state, the fixed tap/record/payload
bounds, attach/authentication/generation/capacity, coalescing key, counter meanings, exact handle
outcomes, the enumerated `ObservationOutcome` vocabulary, reservation single-use semantics, the synthetic
sink, and the single-mutex copy-after-unlock concurrency model — is preserved. T022 implements **no**
T023/T024 behaviour: no synthetic-sink or isolation change, no payload identity allow-list, no decoder,
no benchmark or broad-matrix change, and no rate/temporization/retry/quota/persistence.

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/observation.hpp` | edit | Add `ObservationValidityState` + `to_string(ObservationValidityState)`; add the trailing `ObservationSnapshot::validity_state`; document `experiment_validity_degraded` as its compatibility projection; add the private `ObservationHub::raise_realized_validity`; replace the slot marker with `realized_validity`; update the applied-effect, interval, and traceability documentation |
| `src/xverse/xcom/src/observation.cpp` | edit | Add `to_string(ObservationValidityState)`; add `raise_realized_validity` (declared-effect target plus the lossless "at least degraded" rule, monotonic within the interval); apply it on every matching drop/coalesce/lossless loss; derive the marker from the realized state; reset a `degraded` interval on `acknowledge` while `invalid` persists; report `validity_state` in `snapshot` |
| `tests/xcom/observation/core/unit_tests.cpp` | edit | Add seven focused T022 cases and register them in `main()`; update the file-block traceability note; every existing case and assertion preserved |
| `docs/engineering/xcom/t022/*.md` | add | Five plan-stage work products plus this implementation record |
| `docs/engineering/xcom/t022/internal-review.json` | add (review stage) | DeepSeek internal review |
| `reports/xcom-queue/t022-package.json` | add (package stage) | Exact-candidate package record |
| `specs/007-xcom-core/tasks.md` | edit | T022 checkbox marked complete (implementation stage only) |

No `CMakeLists.txt` or `cmake/*.cmake`, no `src/xverse_xdl/`, `xdl/`, `proto/`, or `contracts/` path, no
other production unit (`activation_plan.*`, `provider.*`, `loopback_provider.*`,
`endpoint_route_lifecycle.*`, `contract.hpp`, `item.hpp`, `value.hpp`, `result.hpp`, `diagnostic.hpp`,
`validation_session.*`, `stimulation_journal.*`), and no `disabled_tap_benchmark.cpp` is changed. The
integration fixtures (`tests/xcom/observation/integration/{test_support.hpp,integration_tests.cpp}`) are
**not** edited because they declare the default `none` validity effect; their observable behavior and
lossless/degraded-marker expectations are unchanged. No CTest target, test name, or label is added,
renamed, or removed.

### 3.1 Changed public symbols

- New: `ObservationValidityState` (`valid = 0`, `degraded = 1`, `invalid = 2`; numeric values encode the
  monotonic ordering `valid < degraded < invalid`), `to_string(ObservationValidityState)` returning
  `"valid"`, `"degraded"`, `"invalid"`.
- Extended: `ObservationSnapshot` gains one **trailing** field
  `ObservationValidityState validity_state{ObservationValidityState::valid}`; `experiment_validity_degraded`
  is retained with the derived value `validity_state != valid`; `ObservationHub::acknowledge` now closes
  the realized validity interval (degraded → valid, invalid persists) as well as resetting
  `backpressure_rejections`.
- Documentation-only edits (no signature/semantic change): `ObservationValidityEffect` failure note,
  `ObservationTapSpecInput::validity_effect`, `ObservationTapSpec::validity_effect()`.
- Unchanged: `ObservationOutcome` vocabulary (no new value), `ObservationOverflowPolicy` and
  `ObservationValidityEffect` enumerators, `ObservationTapHandle` surface, every `ObservationHub`
  operation signature, the reserve/commit/cancel claim protocol, the retention ordering rules, the
  coalescing key, and `SyntheticObservationSink`.
- New/changed public declarations carry `@brief` plus the applicable ownership/lifetime/thread-safety/
  failure Doxygen tags in the existing file-block style; the admitted documentation configuration is
  unchanged.

### 3.2 Changed artifact hashes (SHA-256, this candidate)

| Path | SHA-256 |
| --- | --- |
| `src/xverse/xcom/include/xverse/xcom/observation.hpp` | `6a9953aeee25d47d38c24bc752b2d2e8e0eb9f8bdc0b6c796f3e629dd5df1ea6` |
| `src/xverse/xcom/src/observation.cpp` | `20c76d3090b4b7f812d7bfddd3fe1bda625429b2350a674355825f36cc78e17d` |
| `tests/xcom/observation/core/unit_tests.cpp` | `dbd56e74ca0e5c4a686de2169686ff83ff8ddae1fd70235bb6110b0d99c4fa19` |

The work-product and package hashes are recorded by the deterministic package action in
`reports/xcom-queue/t022-package.json`.

## 4. Deterministic gate

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T022 7be8b9718e42e58bb1a05a486ff62e520f94567c
```

Observed result (implementation stage): `ok`, with `changed_paths: 10` and `ctest:306` — the six T022 work
products present, the T022 checkbox marked complete, at least one `src/xverse/xcom/` path changed, the
configure/build/discovery/full-`ctest` sequence exiting 0, and `git diff --check` clean. The gate's
configure reuses the T022 build cache seeded with the previously admitted A-1 `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` values (named by role only; no
ambient path or network resolution was added, and no admission check was weakened).

### 4.1 Build and test environment

| Item | Value |
| --- | --- |
| Configure (A-1 cache seed) | `cmake -S . -B build/fabro-t022 -G Ninja -DCMAKE_BUILD_TYPE=Debug -D<three admitted A-1 inputs>` (exit 0) |
| Configure (plain, reused by the gate) | `cmake -S . -B build/fabro-t022 -G Ninja -DCMAKE_BUILD_TYPE=Debug` (exit 0) |
| Build | `cmake --build build/fabro-t022 --parallel 4` (exit 0) |
| Toolchain | host GNU C++ 11.4.0 (`-std=c++20`) under the T012 `-Wall -Wextra -Wpedantic -Werror` contract |
| Discovery | `ctest --test-dir build/fabro-t022 -N` → `Total Tests: 306` |
| Full suite | `ctest --test-dir build/fabro-t022 --output-on-failure --parallel 4` → `100% tests passed, 0 tests failed out of 306` |
| Diff hygiene | `git diff --check 7be8b9718e42e58bb1a05a486ff62e520f94567c --` → clean |

The discovered count matches the baseline 306, proving no target, name, or label was added, renamed, or
removed.

### 4.2 Observation evidence

| Target | Command | Result |
| --- | --- | --- |
| `xcom_observation_unit` | `ctest -R xcom_observation` / direct executable | Passed (exit 0); seven added cases plus seventeen preserved cases in one executable |
| `xcom_observation_integration` | `ctest -R xcom_observation` | Passed (exit 0); all accepted cases unchanged |
| `xcom_observation_disabled_benchmark` | `ctest -R xcom_observation` | Passed (exit 0); not edited |
| core/lifecycle/provider/validation/activation-plan suites | full `ctest` run | Passed; additivity confirmed |

Added unit cases: `test_drop_newest_bounded_loss`, `test_coalesce_latest_key_selection`,
`test_lossless_backpressure_pre_dispatch`, `test_validity_effect_on_best_effort_loss`,
`test_validity_effect_on_lossless_backpressure`, `test_validity_state_vocabulary`,
`test_acknowledge_closes_validity_interval`. Preserved unit cases:
`test_values_filters_and_versions`, `test_filter_declared_constraints`, `test_declared_tap_binding`,
`test_declared_tap_rejections`, `test_validity_effect_vocabulary`, `test_payload_policy_bounds`,
`test_record_self_description`, `test_record_counter_projection`, `test_snapshot_reports_declaration`,
`test_repeated_declaration_capacity`, `test_metadata_only`, `test_controlled_payload_states`,
`test_best_effort_overflow`, `test_lossless_reservations`, `test_competing_reservation_interleaving`,
`test_exact_tap_handles`, `test_synthetic_sink_concurrency`.

### 4.3 Source inspections

- **Bounds (CHK-13)** — `kObservationContractVersion{"1.0.0"}`,
  `kMaximumObservationTaps{8U}`, `kMaximumObservationRecordsPerTap{16U}`,
  `kMaximumObservedPayloadBytes{1024U}` are unchanged; the declared capacity is validated to 1…16; the
  coalescing scan is bounded by the declared capacity; a scan of `observation.cpp` finds no `new`/`delete`/
  `malloc`/`std::vector`/`make_unique`/`make_shared` and no timer, retry, rate, quota, or wall-clock input
  on the T022 path.
- **Offline and domain-neutral (CHK-17)** — a forbidden-API scan of the three changed files finds no
  network/socket/resolver/TLS, ambient/secret lookup, filesystem, process, dynamic-load, or legacy access;
  the only `connect`/`disconnect` matches are the in-process `SyntheticObservationSink` methods. The
  candidate adds no dependency beyond the C++ standard library and contains no domain-specific, export,
  dashboard, storage, or query primitive; the offline configure/build succeeds.
- **Public safety (CHK-18)** — a scan of the changed sources, tests, and work products finds no credential,
  private address, real or proprietary payload, environment-specific absolute host path, or sensitive
  deployment value; the fixture payloads remain synthetic and ≤ 4 bytes and the concurrency fixtures remain
  ≤ 4 threads with no wall-clock threshold.
- **Doxygen (CHK-19)** — every new/changed public declaration (`ObservationValidityState`,
  `to_string(ObservationValidityState)`, `ObservationSnapshot::validity_state`, the extended `acknowledge`
  contract) carries `@brief` plus the applicable ownership/lifetime/thread-safety/failure tags; the
  admitted configuration is unchanged. The existing documentation validator
  (`scripts/check_doxygen.py`) fails **pre-existing** on Python docstring coverage in unchanged files
  (`scripts/**`, `src/xverse_xdl/xcom_plan.py`); that coverage gap is DOX-GAP-01, owned by T011/T037, and is
  not introduced or worsened by T022 (`T022-LIM-08`).

### 4.4 Governance checks

```sh
python3 scripts/validate_xcom_task_ownership.py --verify          # passed
python3 scripts/validate_xcom_task_ownership.py --check-human     # passed
python3 scripts/validate_xcom_requirements_traceability.py --verify   # passed
python3 scripts/validate_xcom_architecture_contracts.py --verify      # passed
python3 scripts/validate_xcom_unit_design.py --verify                 # passed
```

`git rev-parse 7be8b9718e42e58bb1a05a486ff62e520f94567c` resolves to the authorized baseline. The
capability `ref002.disposition` stays `unchanged` with an empty `promoted` list; no REF-002 or capability
requirement is promoted and no register, contract, schema, ADR, or another task's path is rewritten.

## 5. Requirement-to-change-to-check traceability

| Requirement | Realized by | Check(s) |
| --- | --- | --- |
| T022-SR-001 | `retain` drop-newest branch: `++dropped` + `raise_realized_validity` + stable `accepted`; FIFO retention unchanged | CHK-05, NEG-01, NEG-13 |
| T022-SR-002 | `retain` coalesce branch: newest matching key replaced with `++coalesced`, else `++dropped`; balanced ring buffer unchanged | CHK-06, NEG-02, NEG-03 |
| T022-SR-003 | unchanged `reserve`/`commit`/`cancel` claim protocol; pre-dispatch backpressure counted and realized; the post-claim full-at-retention `retain` branch is a non-constructible defensive guard (see §6 NEG-05) | CHK-07, CHK-08, NEG-04, NEG-12 (NEG-05 is a guard, uncovered) |
| T022-SR-004 | declared capacity 1…16 enforced; `0 ≤ queued ≤ record_capacity`; insertion order preserved under drop/coalesce | CHK-05, CHK-13, NEG-14 |
| T022-SR-005 | `raise_realized_validity(slot, false)` on drop and coalesce loss selects `none`/`degrade_on_loss`/`invalidate_on_loss` | CHK-09, NEG-06, NEG-07, NEG-08 |
| T022-SR-006 | `raise_realized_validity(slot, true)` on lossless pre-dispatch backpressure realizes at least `degraded`; the post-claim call site is an uncovered defensive guard (see §6 NEG-05) | CHK-08, CHK-10, NEG-04 |
| T022-SR-007 | `ObservationValidityState` values + `to_string`; `ObservationSnapshot::validity_state`; monotonic raise | CHK-09, CHK-11, NEG-12 |
| T022-SR-008 | `acknowledge` resets `backpressure_rejections` and `degraded → valid`; `invalid` persists; foreign/stale returns `invalid_tap_handle` | CHK-10, NEG-10, NEG-11 |
| T022-SR-009 | all raises/updates under the single hub mutex; snapshot copied after unlock; `to_string`/accessors pure `noexcept`; no callback | CHK-12, CHK-16, NEG-15 |
| T022-SR-010 | fixed 8/16/1024 bounds and one fixed validity enumerator; no dynamic allocation/timer/retry/rate/quota | CHK-13, CHK-18 |
| T022-SR-011 | standard-library-only, offline, domain-neutral scan; successful offline build | CHK-17, NEG-16 |
| T022-SR-012 | public-safety scan of committed sources/tests/work products | CHK-18, NEG-17 |
| T022-SR-013 | Doxygen on every new/changed declaration; admitted configuration unchanged (§4.3) | CHK-19 |
| T022-SR-014 | additive-only diff; no removed/renamed/weakened case, target, or marker semantics | CHK-02, CHK-14, CHK-20, NEG-18, NEG-19 |
| T022-SR-015 | deterministic gate, clean diff, checkbox marked only in this stage (§4) | CHK-21 |
| T022-SR-016 | registers re-validated; REF-002 unchanged; attribution recorded in §7 | CHK-20, CHK-22 |
| T022-SR-017 | payload-view, schema-state, and sink code byte-identical; no allow-list or decoder added | CHK-14, NEG-19 |

Check and negative-case identifiers are the accepted [`verification-plan.md`](verification-plan.md) §4–§5.

## 6. Negative cases realized

| NEG | Defect injected | Realized case | Observed result |
| --- | --- | --- | --- |
| NEG-01 | `drop_newest` submission against a full queue | `test_drop_newest_bounded_loss`, `test_best_effort_overflow` | `accepted` with `dropped` + 1; no new record; retained order unchanged |
| NEG-02 | `coalesce_latest` submission with no matching key | `test_coalesce_latest_key_selection` | `accepted` with `dropped` + 1; nothing replaced; queue within bound |
| NEG-03 | `coalesce_latest` submission with a matching key | `test_coalesce_latest_key_selection` | `accepted` with `coalesced` + 1; only the newest matching record replaced; oldest and unrelated order preserved |
| NEG-04 | lossless capacity unavailable before provider submission | `test_lossless_backpressure_pre_dispatch`, `test_validity_effect_on_lossless_backpressure` | `observation_backpressure`; no reservation/record; `backpressure_rejections` + 1; realized ≥ `degraded` |
| NEG-05 | lossless tap full at retention after a valid claim (**non-constructible defensive guard**) | none: not constructible under the `size + reserved_lossless <= record_capacity` invariant; the `retain` backpressure branch is retained unchanged and uncovered | unreachable by construction — `reserve` rejects at `size + reserved_lossless >= record_capacity` and `commit` decrements `reserved_lossless` before `retain`, so a claimed lossless slot always has `size <= record_capacity - 1 < record_capacity`; no test exercises it |
| NEG-06 | declared `none` plus a best-effort drop/coalesce | `test_validity_effect_on_best_effort_loss` | status stays `valid`; `experiment_validity_degraded == false`; no inferred degradation |
| NEG-07 | declared `degrade_on_loss` plus a best-effort drop | `test_validity_effect_on_best_effort_loss` | status `degraded`; marker true |
| NEG-08 | declared `invalidate_on_loss` plus a best-effort drop | `test_validity_effect_on_best_effort_loss`, `test_acknowledge_closes_validity_interval` | status `invalid`; a further loss does not lower it |
| NEG-09 | unknown overflow/validity-effect value (`static_cast`) | `test_declared_tap_rejections`, `test_validity_effect_vocabulary` | no policy value; no retention or vocabulary change |
| NEG-10 | acknowledge a `degraded` interval, then a further loss; acknowledge an `invalid` status | `test_acknowledge_closes_validity_interval` | `degraded → valid` with `backpressure_rejections == 0`; `invalid` persists and is not lowered |
| NEG-11 | foreign/stale/closed handle for snapshot/acknowledge/detach | `test_acknowledge_closes_validity_interval`, `test_exact_tap_handles`, `test_snapshot_reports_declaration` | `invalid_tap_handle`/`tap_closed`/absent snapshot; no reset or mutation on the real tap |
| NEG-12 | detach while a lossless claim is in flight, or a foreign/moved-from/completed reservation | `test_lossless_reservations`, `test_lossless_backpressure_pre_dispatch` | `tap_busy`; `invalid_reservation`; no record, counter, or slot mutation |
| NEG-13 | FIFO order under drop/coalesce | `test_drop_newest_bounded_loss`, `test_coalesce_latest_key_selection` | retained records keep insertion order; the newest matching record is the one replaced |
| NEG-14 | saturation under any policy | `test_drop_newest_bounded_loss`, `test_coalesce_latest_key_selection` | queue never exceeds the declared bound; accounting identity holds |
| NEG-15 | view/callback escaping the lock | source scan plus the unchanged concurrency cases | value copies returned after unlock; the boundary has no callback path |
| NEG-16…NEG-19 | boundary, offline, public-safety, additivity/stage/maturity probes | §4.1, §4.3 scans and the deterministic gate | no forbidden element; boundary and maturity preserved |

## 7. Recorded attribution observation (not resolved here)

`docs/engineering/xcom/t008/requirements-register.json` attributes `XCOM-SW-OBS-002` and
`XCOM-SW-OBS-003` to T022, while `docs/engineering/xcom/t008/traceability-matrix.json` allocates them to
the `XCOM-DU-OBS-BASELINE` locator and `docs/engineering/xcom/t010/unit-design.json` links `XCOM-DU-013`
(owning tasks T022/T023) to `XCOM-SW-OBS-003`/`-004`. T022 implements the **bounded queue/validity**
half (`XCOM-SW-OBS-003`) and leaves every `XCOM-SW-OBS-002` payload-view behavior unchanged: the
`payloadAccess: allow-listed` identity allow-list and any decoder/schema status beyond
`PayloadSchemaState::undecoded` remain unimplemented and partial (`T022-LIM-02`, `T022-GAP-01`). The
registers are **not** rewritten and no maturity is promoted. The historical SESN-era identifiers
`XCOM-OBS-001…009` are retained as evidence only, and `scripts/validate_xcom_observation.py` (legacy
SESN tooling that binds `SESN_CANDIDATE_REVISION`) is neither executed nor edited by this
repository-owned workflow (`T022-LIM-06`).

## 8. Limitations and gaps

- `T022-LIM-01` — Prototype only: no runtime, telemetry, transport, timing, compatibility, parity, or
  production-readiness claim; not user-accepted (T041).
- `T022-LIM-02` — The payload identity allow-list and any decoder/schema status beyond `undecoded` remain
  unimplemented; `XCOM-SW-OBS-002` therefore stays partial.
- `T022-LIM-03` — The realized validity status is an in-process, per-tap projection held only until
  detach/recreation; durable experiment-result validity, storage, and presentation belong to
  Argus/Faults and are not implemented here.
- `T022-LIM-04` — `bounds.maxRateHz` is accepted by the Profile but is not realized; the declared record
  capacity is the only enforced bound.
- `T022-LIM-05` — Coalescing keeps the accepted exact logical key set and an insertion-order newest-match
  scan; no windowed coalesce quota is introduced.
- `T022-LIM-06` — `scripts/validate_xcom_observation.py` is legacy SESN-era tooling; it is neither
  executed nor edited and is not T022 evidence.
- `T022-LIM-07` — Every retained record still carries a fixed 1024-byte payload buffer plus the item
  projection; the bounded-storage tradeoff is inherited unchanged.
- `T022-LIM-08` — The documentation-coverage gate `scripts/check_doxygen.py` fails pre-existing on
  unchanged Python sources (DOX-GAP-01, owned by T011/T037); T022 adds tagged Doxygen to its declarations
  but does not run or repair that gate's unrelated coverage debt.
- Gaps `T022-GAP-02`…`-06` (synthetic-sink/isolation, observation matrix, benchmark threshold, executed
  sanitizer/static/Doxygen/delivery evidence, T008/T010 attribution nuance) remain with their owning tasks
  and are **not** claimed here.

## 9. Definition of done (implementation view)

The implementation stage is complete when the six work products exist, the T022 checkbox is marked, the
deterministic gate and named checks pass at the candidate revision with no existing case weakened, this
record is written, and a separate DeepSeek internal review records a passing verdict with no findings.
This is **not** user acceptance, which remains T041; external Codex review and acceptance are deferred
until the `xcom-t011-t016-t021-t024` backlog completes.

## 10. Internal-review closure (T022-IR-F-01)

The separate read-only internal review (revision 2) recorded one low-severity evidence/traceability finding,
T022-IR-F-01: NEG-05 and the post-claim full-at-retention `retain` backpressure branch were presented as an
executable, test-realized negative case, but that branch is unreachable by construction and no test
exercises it. No functional defect was found and the production guard itself is harmless.

Closure applied in this repair (documentation only, no production or test change):

- `verification-plan.md` §5 now classifies NEG-05 as a **non-constructible defensive guard** with the
  reachability argument, moves it outside the executable `NEG-01…NEG-04`/`NEG-06…NEG-15` range, and §5.1
  records the closure; the T022-SR-003 mapping in §8 is aligned.
- §5 and §6 above re-map T022-SR-003 / T022-SR-006 and the NEG-05 row so no test is named as exercising the
  post-claim branch; the branch is recorded as an uncovered defensive guard.
- `detailed-design.md` §4.3/§6, `unit-specifications.md` §3.2/§7, `requirements.md` §4.1/§10, and
  `architecture.md` §5/§8 describe the post-claim branch as a defensive guard, not a verified behavior.
- The production guard in `observation.cpp::retain` is retained unchanged; no requirement, check, test,
  target, expected result, accepted behavior, or scope is weakened or removed.

Reachability argument: `reserve` claims a lossless slot only while `size + reserved_lossless <
record_capacity`, and `commit` decrements `reserved_lossless` before calling `retain`, so the invariant
`size + reserved_lossless <= record_capacity` holds and a claimed lossless slot always reaches `retain` with
`size <= record_capacity - 1 < record_capacity`; `retain` therefore always appends and never takes its
backpressure branch.

Closure evidence: the corrected records above plus the re-run five register validators
(`validate_xcom_task_ownership.py --verify`/`--check-human`, `validate_xcom_requirements_traceability.py
--verify`, `validate_xcom_architecture_contracts.py --verify`, `validate_xcom_unit_design.py --verify`),
`ctest --test-dir build/fabro-t022 -N` (306 tests), and `ctest --test-dir build/fabro-t022 -R
xcom_observation --output-on-failure`. Every T022 requirement still maps to at least one check.
