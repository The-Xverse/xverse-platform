# T021 Implementation Record — Declared Observation Records, Filters, Payload Policy, and Tap Handles

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T021 (capability 007, slice `T-OBS`) |
| Stage / role | implementation → implementation record |
| Revision | 1 |
| Authorized baseline | `8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda` |
| Predecessor | T016 reviewed terminal package (`docs/engineering/xcom/t016/`) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned at the workflow checkpoint) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | `docs/engineering/xcom/t021/internal-review.json` (separate read-only DeepSeek review, produced by the review stage) |
| Package record | `reports/xcom-queue/t021-package.json` (produced by the deterministic package action) |
| Authorization | ACC005/ACC010/ACC011/ACC014/ACC015; ADR-0016; ADR-0018; ADR-0019; ADR-0020; `specs/007-xcom-core/tasks.md` T021 |
| Maturity | Prototype-only declared observation boundary implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T021 implements the bounded slice required by the T021 task entry: *"Implement immutable observation
records, filters, payload policy, and tap handles."*

The candidate realizes the **declaration half** of the accepted observation boundary described by
`XCOM-SW-OBS-001` (FR-011, design unit `XCOM-DU-012`): a validated, mandatory declared observation-point
identity on the immutable tap policy; read-only declared-constraint accessors on the filter; a declared
`validityEffect` vocabulary copied textually from the accepted `io.xverse.xcom` `observation-policy` form;
a single-source-of-truth declared route point; and a self-describing immutable record that carries the
producing tap's declared identity and a retention-time queue-counter projection. Every accepted baseline
behaviour — contract-version check, filter matching, payload mode/bound validation, record capacity,
overflow vocabulary, retention drop/coalesce/lossless rules, counter update points, attach/authentication/
generation/capacity, snapshot, acknowledgement, detach, synthetic-sink behaviour, and the enumerated
outcome vocabulary — is preserved byte-for-byte. T021 implements **no** T022/T023/T024 behaviour: no loss,
degradation, or invalidation rule is applied, and no payload allow-list or decoder is added.

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/observation.hpp` | edit | Add `ObservationValidityEffect` + `to_string`; `ObservationFilter` declared-constraint accessors; mandatory `tap_id` and declared `validity_effect` on `ObservationTapSpecInput`/`ObservationTapSpec`; `declared_tap_id()`, `declared_route_point()`, `validity_effect()`; `ObservationRecordCounters`; `ObservationRecord::tap_id()`/`counters()`; trailing `declared_tap_id`/`validity_effect` on `ObservationSnapshot`; Doxygen and traceability note |
| `src/xverse/xcom/src/observation.cpp` | edit | `known_validity_effect`, `to_string(ObservationValidityEffect)`, ordered `ObservationTapSpec::create` validation (version, declared identity, filter, mode, overflow, capacity, validity effect, bound), record stamping of declared identity and post-retention counters, snapshot declaration reporting |
| `tests/xcom/observation/core/unit_tests.cpp` | edit | Nine focused T021 cases; fixture helper and shared item builder updated to declare a valid observation point; the three pre-existing direct declarations updated; every original assertion preserved |
| `tests/xcom/observation/integration/test_support.hpp` | edit | Shared `make_tap_spec` helper declares a valid observation point (`tap.integration`) |
| `tests/xcom/observation/integration/integration_tests.cpp` | edit | The one direct `ObservationTapSpec::create` rejection site declares a valid observation point so its rejection stays attributable to the version |
| `docs/engineering/xcom/t021/*.md` | add | Five plan-stage work products plus this implementation record |
| `docs/engineering/xcom/t021/internal-review.json` | add (review stage) | DeepSeek internal review |
| `reports/xcom-queue/t021-package.json` | add (package stage) | Exact-candidate package record |
| `specs/007-xcom-core/tasks.md` | edit | T021 checkbox marked complete (implementation stage only) |

No `CMakeLists.txt` or `cmake/*.cmake`, no `src/xverse_xdl/`, `xdl/`, `proto/`, or `contracts/` path, no
other production unit (`activation_plan.*`, `provider.*`, `loopback_provider.*`,
`endpoint_route_lifecycle.*`, `contract.hpp`, `item.hpp`, `value.hpp`, `result.hpp`, `diagnostic.hpp`,
`validation_session.*`, `stimulation_journal.*`), and no `disabled_tap_benchmark.cpp` is changed. No CTest
target, test name, or label is added, renamed, or removed.

### 3.1 Changed public symbols

- New: `ObservationValidityEffect` (`none`, `degrade_on_loss`, `invalidate_on_loss`),
  `to_string(ObservationValidityEffect)`, `ObservationRecordCounters`.
- Extended: `ObservationFilter` (`contract_id`, `interface_id`, `endpoint_id`, `route_id`, `provider_id`,
  `interaction_kind`, `origin`); `ObservationTapSpecInput` (`tap_id`, `validity_effect`);
  `ObservationTapSpec` (`declared_tap_id`, `declared_route_point`, `validity_effect`);
  `ObservationRecord` (`tap_id`, `counters`); `ObservationSnapshot` (`declared_tap_id`,
  `validity_effect`).
- Unchanged: `ObservationOutcome` vocabulary, `ObservationTapHandle` surface (opaque hub/slot/generation
  only; no accessor added), `ObservationHub` operation signatures, retention rule, synthetic sink.
- New/changed public declarations carry `@brief` plus the applicable ownership/lifetime/thread-safety/
  failure Doxygen tags in the existing file-block style; the admitted documentation configuration is
  unchanged.

### 3.2 Changed artifact hashes (SHA-256, this candidate)

| Path | SHA-256 |
| --- | --- |
| `src/xverse/xcom/include/xverse/xcom/observation.hpp` | `25a59e1cda36e16bcdcb96adfdfbdfad5b3461131077325f629faf73b06d391d` |
| `src/xverse/xcom/src/observation.cpp` | `1aad1b4ed001895807284eda01e64d5f77d50bd4b902e7c5a64a23ff15d7741b` |
| `tests/xcom/observation/core/unit_tests.cpp` | `8f2e5c85325f8e67e6f84cd00a427ce726be524adc1753540c0295f31c8b379d` |
| `tests/xcom/observation/integration/test_support.hpp` | `e2c05633cc00b2924af27152787a7df5a4ee343d0f5e4587f2c0da3ad2c0bf4c` |
| `tests/xcom/observation/integration/integration_tests.cpp` | `2b5c003b02eff2fa62c7c3a67eae3f7df1c936fb9df74b6691541fcb1c47e749` |

The work-product and package hashes are recorded by the deterministic package action in
`reports/xcom-queue/t021-package.json`.

## 4. Deterministic gate

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T021 8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda
```

Observed result (implementation stage): `ok`, with the six T021 work products present, the T021 checkbox
marked complete, at least one `src/xverse/xcom/` path changed, the configure/build/discovery/full-`ctest`
sequence exiting 0, and `git diff --check` clean. The gate's configure reuses the T021 build cache seeded
with the previously admitted A-1 `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN` values (named by role only; no ambient path or network resolution was
added, and no admission check was weakened).

### 4.1 Build and test environment

| Item | Value |
| --- | --- |
| Configure | `cmake -S . -B build/fabro-t021 -G Ninja -DCMAKE_BUILD_TYPE=Debug` (exit 0) |
| Build | `cmake --build build/fabro-t021 --parallel 4` (exit 0) |
| Toolchain | host GNU C++ (`-std=c++20`) under the T012 `-Wall -Wextra -Wpedantic -Werror` contract |
| Discovery | `ctest --test-dir build/fabro-t021 -N` → `Total Tests: 306` |
| Full suite | `ctest --test-dir build/fabro-t021 --output-on-failure --parallel 4` → `100% tests passed, 0 tests failed out of 306` |
| Diff hygiene | `git diff --check 8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda --` → clean |

The discovered count matches the baseline 306, proving no target, name, or label was added, renamed, or
removed.

### 4.2 Observation evidence

| Target | Command | Result |
| --- | --- | --- |
| `xcom_observation_unit` | `ctest -R xcom_observation` / direct executable | Passed (exit 0); nine added cases plus eight preserved cases in one executable |
| `xcom_observation_integration` | `ctest -R xcom_observation` / direct executable | Passed (exit 0); all accepted cases with the shared helper declaring `tap.integration` |
| `xcom_observation_disabled_benchmark` | `ctest -R xcom_observation` | Passed; not edited |

Added unit cases: `test_filter_declared_constraints`, `test_declared_tap_binding`,
`test_declared_tap_rejections`, `test_validity_effect_vocabulary`, `test_payload_policy_bounds`,
`test_record_self_description`, `test_record_counter_projection`, `test_snapshot_reports_declaration`,
`test_repeated_declaration_capacity`. Preserved unit cases: `test_values_filters_and_versions` (declared
observation point added only), `test_metadata_only`, `test_controlled_payload_states`,
`test_best_effort_overflow`, `test_lossless_reservations`, `test_competing_reservation_interleaving`,
`test_exact_tap_handles`, `test_synthetic_sink_concurrency`.

### 4.3 Governance checks

```sh
python3 scripts/validate_xcom_task_ownership.py --verify          # passed
python3 scripts/validate_xcom_task_ownership.py --check-human     # passed
python3 scripts/validate_xcom_requirements_traceability.py --verify   # passed
python3 scripts/validate_xcom_architecture_contracts.py --verify      # passed
python3 scripts/validate_xcom_unit_design.py --verify                 # passed
```

`git rev-parse 8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda` resolves to the authorized baseline. The
capability `ref002.disposition` stays `unchanged` with an empty `promoted` list; no REF-002 or capability
requirement is promoted and no register, contract, schema, ADR, or another task's path is rewritten.

## 5. Requirement-to-change-to-check traceability

| Requirement | Realized by | Check(s) |
| --- | --- | --- |
| T021-SR-001 | single accepted `kObservationContractVersion`; strict version branch in `create` | CHK-03, NEG-01 |
| T021-SR-002 | mandatory `tap_id` validated by `Identity::create`; accessor `declared_tap_id()` | CHK-04, CHK-05, NEG-02…NEG-04 |
| T021-SR-003 | `declared_route_point()` returns `filter().route_id()`; no separate field | CHK-07, NEG-05 |
| T021-SR-004 | seven read-only filter accessors; `matches()` unchanged | CHK-06, CHK-21 |
| T021-SR-005 | unchanged mode/bound/capacity validation; `bounded_prefix` bound echo | CHK-09, CHK-15, NEG-06…NEG-08 |
| T021-SR-006 | unchanged overflow vocabulary and retention rules | CHK-08, CHK-21, NEG-09 |
| T021-SR-007 | `ObservationValidityEffect` + stable text; declared only, no behaviour | CHK-08, NEG-10 |
| T021-SR-008 | `ObservationRecord::tap_id()` stamped from the authenticated producing tap's policy | CHK-10 |
| T021-SR-009 | `ObservationRecordCounters` stamped post-retention in `retain` | CHK-11 |
| T021-SR-010 | value-owned record/snapshot copies; no view escapes; private record constructor | CHK-10, CHK-21, NEG-19 |
| T021-SR-011 | `ObservationTapHandle` surface unchanged; declared identity confers no authority | CHK-13, NEG-11…NEG-13 |
| T021-SR-012 | snapshot reports `declared_tap_id`/`validity_effect`; absent for invalid handle | CHK-12, NEG-11 |
| T021-SR-013 | declared identity is not a uniqueness rule; two taps share one point independently | CHK-13 |
| T021-SR-014 | new accessors/factories `noexcept`, call-local, no shared mutable state | CHK-14, CHK-16 |
| T021-SR-015 | unchanged fixed bounds; no dynamic allocation/timer/retry/quota on the T021 path | CHK-14, CHK-18 |
| T021-SR-016 | hub serialization, copy-after-unlock, and no-callback path unchanged | CHK-16, NEG-19 |
| T021-SR-017 | standard-library-only, offline, domain-neutral scan; successful offline build | CHK-17, NEG-20, NEG-21 |
| T021-SR-018 | public-safety scan of committed sources/tests/work products | CHK-18, NEG-22 |
| T021-SR-019 | Doxygen on every new/changed declaration; admitted configuration unchanged | CHK-19 |
| T021-SR-020 | additive-only diff; no removed/renamed/weakened case or target | CHK-02, CHK-21, NEG-23, NEG-24 |
| T021-SR-021 | deterministic gate, clean diff, checkbox marked only in this stage | CHK-22 |
| T021-SR-022 | registers re-validated; REF-002 unchanged; attribution recorded in §7 | CHK-20, CHK-23 |

Check and negative-case identifiers are the accepted [`verification-plan.md`](verification-plan.md) §4–§5.

## 6. Negative cases realized

| NEG | Defect injected | Realized case | Observed result |
| --- | --- | --- | --- |
| NEG-01 | contract version `2.0.0` | `test_values_filters_and_versions`, `test_declared_tap_rejections` | no policy value |
| NEG-02 | empty declared identity | `test_declared_tap_rejections` | no policy value |
| NEG-03 | 129-byte, control-byte, or whitespace-padded `tap_id` | `test_declared_tap_rejections` | no policy value |
| NEG-04 | malformed non-empty filter identity | `test_values_filters_and_versions`, `test_declared_tap_rejections` | no filter/policy value |
| NEG-05 | contradictory declared route point | structurally impossible; `test_declared_tap_binding` single-source assertion | filter is the only route source |
| NEG-06 | unknown payload mode (`static_cast`) | `test_declared_tap_rejections` | no policy value |
| NEG-07 | `bounded_prefix` bound 0 or 1025 | `test_declared_tap_rejections` | no policy value |
| NEG-08 | non-zero bound on metadata mode; capacity 0 or 17 | `test_declared_tap_rejections` | no policy value |
| NEG-09 | unknown overflow policy | `test_declared_tap_rejections` | no policy value; retention vocabulary unchanged |
| NEG-10 | unknown validity effect | `test_validity_effect_vocabulary`, `test_declared_tap_rejections` | no policy value; no default substituted |
| NEG-11 | foreign/closed handle | `test_exact_tap_handles`, `test_snapshot_reports_declaration`, `test_lossless_reservations` | stable outcome; absent snapshot; no mutation |
| NEG-12 | stale handle after recreation | `test_exact_tap_handles` | `invalid_tap_handle`; recreated generation untouched |
| NEG-13 | duplicate close; detach while claimed | `test_exact_tap_handles`, `test_lossless_reservations` | `tap_closed`; `tap_busy` with no mutation |
| NEG-14 | attach beyond eight slots | `test_exact_tap_handles` | `tap_capacity_exhausted`; existing taps unchanged |
| NEG-15 | lossless capacity unavailable | `test_lossless_reservations`, `test_record_counter_projection` | `observation_backpressure`; no record |
| NEG-16 | `drop_newest` against a full queue | `test_best_effort_overflow`, `test_record_counter_projection` | `accepted` with `dropped` incremented; no new record |
| NEG-17 | `coalesce_latest` with no matching key | `test_best_effort_overflow` | `accepted` with `dropped` incremented; no replacement |
| NEG-18 | invalid observation clock domain / mismatched reservation | `test_lossless_reservations` | `invalid_argument`/`invalid_reservation`; no record |
| NEG-19 | view/callback escaping the lock | `test_record_self_description` post-mutation read; source has no callback | value copies returned after unlock |
| NEG-20…NEG-24 | boundary, offline, public-safety, additivity, stage/maturity probes | §4.1, §4.3 scans and the deterministic gate | no forbidden element; boundary and maturity preserved |

## 7. Recorded attribution observation (not resolved here)

`docs/engineering/xcom/t008/requirements-register.json` attributes `XCOM-SW-OBS-001` to T021 and
`XCOM-SW-OBS-002`/`-003` to T022, while `docs/engineering/xcom/t010/unit-design.json` links
`XCOM-DU-012` (owning task T021) to `XCOM-SW-OBS-001`, `-002`, and `-005`. T021 implements the
**declaration and projection** half (the payload/validity policy vocabulary and the record projection) and
implements no T022 retention/validity behaviour. The registers are **not** rewritten and no maturity is
promoted. The historical SESN-era identifiers `XCOM-OBS-001…009` are retained as evidence only, and
`scripts/validate_xcom_observation.py` (legacy SESN tooling that binds `SESN_CANDIDATE_REVISION`) is
neither executed nor edited by this repository-owned workflow.

## 8. Limitations and gaps

- `T021-LIM-01` — Prototype only: no runtime, telemetry, transport, timing, compatibility, parity, or
  production-readiness claim; not user-accepted (T041).
- `T021-LIM-02` — Per-record queue counters are a retention-time projection, not a durable log.
- `T021-LIM-03` — The declared validity effect is vocabulary and reporting only; no loss/degradation/
  invalidation behaviour is applied (T022), and `experiment_validity_degraded` keeps its accepted meaning.
- `T021-LIM-04` — Payload identity allow-listing is not implemented; the explicit mode-plus-bound policy is
  unchanged and never exposes more than the declared prefix.
- `T021-LIM-05` — Schema interpretation remains `PayloadSchemaState::undecoded`; no decoder is introduced.
- `T021-LIM-06` — `scripts/validate_xcom_observation.py` is legacy SESN-era tooling, not used as evidence.
- `T021-LIM-07` — Each fixed record carries a 1024-byte payload buffer plus the item projection; the
  bounded-storage tradeoff is inherited unchanged from the baseline.
- `T021-LIM-08` — Declaring a tap identity does not bind a tap to a decoded activation plan; the
  plan-to-attachment binding of a decoded `ObservationPoint` remains downstream work.
- Gaps `T021-GAP-01`…`-06` (retention/validity application, payload allow-list/decoder, sink isolation,
  observation matrix, T008/T010 attribution nuance, acceptance) remain with their owning tasks and are
  **not** claimed here.

## 9. Definition of done (implementation view)

The implementation stage is complete when the six work products exist, the T021 checkbox is marked, the
deterministic gate and named checks pass at the candidate revision with no existing case weakened, this
record is written, and a separate DeepSeek internal review records a passing verdict with no findings.
This is **not** user acceptance, which remains T041; external Codex review and acceptance are deferred
until the `xcom-t011-t016-t021-t024` backlog completes.
