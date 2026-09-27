# T024 Implementation Record — Observation Acceptance Matrix (Metadata-Only, Payload Views, Ordering, Saturation, Degraded Validity, Safe Detach)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T024 (capability 007, slice `T-OBS`) |
| Stage / role | implementation → implementation record |
| Revision | 1 |
| Repair revisions | 2 (closes `T024-IR-F01`; see §10); 3 — terminal review R-01 governance repair (see §11) |
| Authorized baseline | `76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6` |
| Repair baseline | `d50bb48f45e422b8a7018710b1ac50cdadbcf8ed` (terminal-review R-01 successor; accumulated T011–T016/T021–T024 candidate) |
| Predecessor | T023 reviewed terminal package (`docs/engineering/xcom/t023/`) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned at the workflow checkpoint) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | `docs/engineering/xcom/t024/internal-review.json` (separate read-only DeepSeek review, produced by the review stage) |
| Package record | `reports/xcom-queue/t024-package.json` (produced by the deterministic package action) |
| Authorization | ACC005/ACC010/ACC011/ACC014/ACC015; ADR-0016; ADR-0018; ADR-0019; ADR-0020; `specs/007-xcom-core/tasks.md` T024 |
| Maturity | Prototype-only observation acceptance matrix implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T024 implements the bounded slice required by the T024 task entry: *"Test metadata-only zero-payload
behavior, controlled payload views, redaction/truncation state, ordering, saturation, degraded validity,
and safe detach."*

The candidate is **test-only**. It adds a consolidated observation acceptance matrix to the two existing
T-OBS observation fixtures and changes no production source, build file, contract, schema, register, ADR,
or another task's path. The matrix exercises the accepted observation surface (`ObservationHub`,
`ObservationTapSpec`, `ObservationFilter`, `ObservationRecord`, `ObservationSnapshot`,
`SyntheticObservationSink`) plus the accepted owned loopback provider composition, and proves the accepted
success criteria `SC-003`, `SC-004`, and `SC-005` and `XCOM-SW-OBS-005` (`FR-023`) across nine named
matrix cases:

- **Metadata-only zero-payload completeness** — every emitted record for a 4-family × {0,1,4}-byte batch
  exposes zero payload bytes with `omitted`/`undecoded`, reports the complete `source_payload_size`, and
  preserves every normalized identity; all twelve records are retained, pulled exactly once in FIFO order,
  and reported exactly by `accepted`/`queued`.
- **Controlled payload views and redaction/truncation** — the `bounded_prefix` boundary table
  (`source < / == / >` bound, minimum and maximum declared bound) and explicit `redacted` produce the exact
  leading bytes and `complete`/`truncated`/`redacted`/`omitted` states; `PayloadSchemaState::undecoded` is
  never upgraded; out-of-bound prefix policies and a non-zero bound on a non-prefix mode are rejected.
- **Ordering** — `drop_newest` retains the oldest records (`1,2,3,4`) with a strictly increasing pulled
  sequence; `coalesce_latest` keeps unrelated records in order and yields `1,2,3,5`; two taps on one hub
  keep independent FIFO order and counters.
- **Saturation** — `drop_newest` at the minimum (1) and maximum (16) capacity never exceeds the declared
  bound, reports exact `accepted`/`dropped`, and satisfies `accepted + dropped == submissions`;
  `coalesce_latest` replaces only the newest matching logical key; `lossless_validation` rejects before any
  provider or queue mutation.
- **Bounded deterministic concurrency (`T024-SR-018`)** — over one capacity-4 `lossless_validation` tap,
  four publisher threads each perform four bounded reserve/commit attempts with atomic flags; exactly four
  commits and twelve `observation_backpressure` rejections occur independently of thread interleaving, with
  four distinct retained sequences, a consistent counter/queue state, degraded `none`-effect validity, no
  callback, and three identical repeated runs.
- **Degraded validity** — the declared `ObservationValidityEffect` selects the realized
  `ObservationValidityState` (`none → valid`, `degrade_on_loss → degraded`, `invalidate_on_loss → invalid`),
  the `experiment_validity_degraded` projection equals `state != valid`, a lossless backpressure realizes at
  least `degraded`, the status is monotonic within an interval, acknowledgement closes a `degraded` interval
  while `invalid` persists, and detach/recreation discards the status and counters.
- **Safe detach** — detach discards only its own records, a repeated close returns `tap_closed`, a claimed
  tap returns `tap_busy`, a stale/foreign/unknown handle returns `invalid_tap_handle` with no mutation, and a
  recreated generation starts clean and invalidates the old handle.
- **Route neutrality (SC-005)** — over the owned loopback, the route item count, `per_route_fifo` receive
  order, and every delivery outcome are unchanged while a best-effort observer is blocked, removed,
  disconnected, or failed.
- **Normalized-record completeness (`XCOM-SW-OBS-005`)** — for each family × origin × provider outcome the
  complete record is self-describing and value-owned, and edge values (absent sequence, distinct observation
  clock, zero-length payload, retention-time counter projection) round-trip exactly.

Every accepted baseline behaviour that T024 does not own — contract version `1.0.0`, filter matching,
payload modes/bounds/views, `undecoded` schema state, declared identities, record self-description,
attach/authentication/generation/capacity, the coalescing key, the retention drop/coalesce/lossless rules,
the applied declared validity effect, the realized validity status, the enumerated `ObservationOutcome`
vocabulary, reservation single-use semantics, the synthetic-sink counters, and the single-mutex
copy-after-unlock concurrency model — is consumed read-only and re-verified unchanged. T024 implements
**no** payload identity allow-list, decoder, rate limit, stimulation, journaling, gateway, benchmark
execution, or durable/presentation behavior, and no T025+ task.

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `tests/xcom/observation/core/unit_tests.cpp` | edit | Add seven T024 matrix cases and three additive case-local helpers (`kT024Families`, `emit_absent_sequence`, `poll_all`, `expect_metadata_record`); register the seven cases in the existing `main()`; update the file-block traceability note to name T024; every existing case and assertion preserved |
| `tests/xcom/observation/integration/integration_tests.cpp` | edit | Add two route-level T024 matrix cases and one additive case-local helper (`make_named_tap_spec`); register the two cases in the existing `main()`; update the file-block traceability note to name T024; every existing case and assertion preserved; `test_support.hpp` is not edited |
| `docs/engineering/xcom/t024/*.md` | add | Five plan-stage work products plus this implementation record |
| `docs/engineering/xcom/t024/internal-review.json` | add (review stage) | DeepSeek internal review |
| `reports/xcom-queue/t024-package.json` | add (package stage) | Exact-candidate package record |
| `specs/007-xcom-core/tasks.md` | edit | T024 checkbox marked complete (implementation stage only) |

No production source under `src/xverse/xcom/` is changed: the matrix consumes `observation.hpp`/`observation.cpp`
and the accepted core/provider headers read-only. No `CMakeLists.txt` or `cmake/*.cmake`, no `xdl/`,
`proto/`, `src/xverse_xdl/`, or `contracts/` path, no `tests/xcom/observation/integration/test_support.hpp`
or `disabled_tap_benchmark.cpp`, and no other task's ownership path is changed. The build file needs no edit:
the existing `xverse_xcom_observation_unit_tests` and `xverse_xcom_observation_integration_tests` targets
compile the two edited fixtures, so the new cases are discovered without adding or renaming a target, test,
name, label, command, or threshold.

### 3.1 Changed test units added

- **Unit (`tests/xcom/observation/core/unit_tests.cpp`, base 28 → 35 test functions):**
  `test_observation_metadata_and_payload_view_matrix`, `test_observation_ordering_matrix`,
  `test_observation_saturation_bound_matrix`, `test_observation_validity_interval_matrix`,
  `test_observation_safe_detach_matrix`, `test_observation_normalized_record_matrix`,
  `test_observation_record_edge_value_matrix`.
- **Integration (`tests/xcom/observation/integration/integration_tests.cpp`, base 8 → 10 test functions):**
  `test_observation_route_ordering_neutrality_matrix`, `test_observation_route_saturation_safe_detach_matrix`.
- **Unchanged public surface:** no `.hpp`/`.cpp` signature, enumerator, accepted value, or another task's
  helper is changed. Every new case constructs its policy through `ObservationTapSpec::create` (directly or
  through the existing `make_spec`/`make_tap_spec` helpers and the additive `make_named_tap_spec`). Every new
  case function carries a `@brief` naming the evidence name and T024 requirement it realizes.
- **Bounded concurrency sub-check:** `test_observation_saturation_bound_matrix` (`T24-TS-003`) adds the
  deterministic four-publisher/twelve-rejection block over one capacity-4 lossless tap described in §2
  (≤ 4 threads, ≤ 16 bounded attempts, atomic flags, three repeated runs, no callback or wall-clock wait),
  realizing T024-SR-018 and CHK-18/CHK-19 inside an existing T024 case with no new case, target, or label.
- **Design-helper reconciliation:** `detailed-design.md` §3.2 planned `make_effect_spec`; the accepted
  `make_spec` already accepts the `validity_effect` parameter, so `make_effect_spec` was unnecessary and the
  matrix uses `make_spec` directly. `emit_absent_sequence` and `poll_all` were realized as planned.

### 3.2 Changed artifact hashes (SHA-256, this candidate)

| Path | SHA-256 |
| --- | --- |
| `tests/xcom/observation/core/unit_tests.cpp` | `5802fd35b40fe131648a5629d3d0888f0d433a04a2e377f0f17e440ea2c4dbf9` |
| `tests/xcom/observation/integration/integration_tests.cpp` | `5a6d63f8a9e9b4b898069cf911b57d6f7160ae1365854dbc90788b6aabf32009` |

The deterministic package action records the candidate work-product hashes — these two test artifacts and
the six T024 work products — in `reports/xcom-queue/t024-package.json`. The generated review and package
records are bound by the terminal collector and the reviewed-checkpoint record, not by the package manifest
itself.

## 4. Deterministic gate

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T024 76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6
```

Observed result (implementation stage): `ok`, with `changed_paths: 9` and `ctest:306` — the six T024 work
products present, the T024 checkbox marked complete, at least one `tests/` path changed, the
configure/build/discovery/full-`ctest` sequence exiting 0, and `git diff --check` clean. The gate's
configure reuses the T024 build cache seeded with the previously admitted A-1 `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` values (named by role only; no ambient
path or network resolution was added, and no admission check was weakened).

### 4.1 Build and test environment

| Item | Value |
| --- | --- |
| Configure (A-1 cache seed) | `cmake -S . -B build/fabro-t024 -G Ninja -DCMAKE_BUILD_TYPE=Debug -D<three admitted A-1 inputs>` (exit 0) |
| Configure (plain, reused by the gate) | `cmake -S . -B build/fabro-t024 -G Ninja -DCMAKE_BUILD_TYPE=Debug` (exit 0) |
| Build | `cmake --build build/fabro-t024 --parallel 4` (exit 0, no warning emitted under `-Werror`) |
| Toolchain | host GNU C++ 11.4.0 (`-std=c++20`) under the T012 `-Wall -Wextra -Wpedantic -Werror` contract |
| Discovery | `ctest --test-dir build/fabro-t024 -N` → `Total Tests: 306` |
| Full suite | `ctest --test-dir build/fabro-t024 --output-on-failure --parallel 4` → `100% tests passed, 0 tests failed out of 306` |
| Diff hygiene | `git diff --check 76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6 --` → clean |

The discovered count matches the baseline 306, proving no target, name, or label was added, renamed, or
removed.

### 4.2 Observation evidence

| Target | Command | Result |
| --- | --- | --- |
| `xcom_observation_unit` | `ctest -R xcom_observation` / direct executable | Passed (exit 0); seven added cases plus twenty-eight preserved cases (35 total) |
| `xcom_observation_integration` | `ctest -R xcom_observation` | Passed (exit 0); two added cases plus eight preserved cases (10 total) |
| `xcom_observation_disabled_benchmark` | `ctest -R xcom_observation` | Passed (exit 0); not edited and no `disabled-tap-performance` evidence claimed (T036) |
| core/lifecycle/provider/validation/activation-plan suites | full `ctest` run | Passed; additivity confirmed |
| Determinism | observation executables run ten consecutive times | Every repeated run returned exit 0 with the same observable outcome |
| Concurrency sub-check | `test_observation_saturation_bound_matrix` (`T24-TS-003`) | Three bounded runs each produced exactly four commits, twelve `observation_backpressure` rejections, four distinct retained sequences, `accepted == queued == 4`, `dropped == coalesced == 0`, `backpressure_rejections == 12`, degraded validity, and no unstable outcome |

### 4.3 Source inspections

- **Metadata-only and payload-view safety (CHK-05, CHK-06, NEG-02, NEG-06, NEG-07)** — the metadata and
  redacted rows assert an empty `payload_bytes()` span with `omitted`/`redacted`, and every payload row
  asserts `PayloadSchemaState::undecoded`; the prefix boundary table asserts the exact leading bytes for
  `source < / == / >` bound, and bound `0`, bound `> kMaximumObservedPayloadBytes`, and a non-zero bound on
  a non-prefix mode are rejected.
- **Bounds (CHK-09, CHK-18, NEG-10, NEG-11)** — capacities 1 and `kMaximumObservationRecordsPerTap` (16) are
  exercised; every emission step checks `queued <= declared capacity`; `accepted + dropped == submissions`
  and the coalesce accounting hold; the largest loop is 20 submissions. The `T24-TS-003` concurrency
  sub-check is the only T024 thread user (≤ 4 threads, ≤ 16 bounded reserve/commit attempts, three repeated
  runs, atomic flags, no callback). No unbounded loop, wall-clock wait, sleep, or retry is introduced.
- **No production mutation (CHK-02, CHK-20, NEG-01)** — `git diff --name-only <baseline>` shows only the two
  observation fixtures and the T024 ledger line; the production delta is empty. The accepted T021/T022/T023
  declaration, retention, validity, payload, record, handle, and sink behavior is byte-identical because no
  production file changed.
- **Route neutrality (CHK-14, NEG-22, NEG-23)** — the integration cases assert the route `queued_items()` and
  `per_route_fifo` receive order before, during, and after a blocked, removed, disconnected, and failed
  best-effort observer, and assert that a detached handle no longer authenticates.
- **Argus boundary / no export primitive (CHK-17, NEG-25)** — a forbidden-vocabulary scan of the two changed
  fixtures finds no dashboard, storage, query, presentation, export, OpenTelemetry, adapter, or
  provider-specific/address/transport accessor; the matrix exercises only the in-process normalized record
  and hub snapshot, and the candidate adds no such primitive.
- **Offline and domain-neutral (CHK-21, NEG-27)** — a forbidden-API scan of the changed fixtures finds no
  network/socket/resolver/TLS, ambient/secret lookup, filesystem, process, dynamic-load, or legacy access;
  the matrix uses only the C++ standard library plus the admitted test dependencies, and the offline
  configure/build succeeds.
- **Public safety (CHK-22, NEG-28)** — a scan of the changed fixtures and work products finds no credential,
  private address, real or proprietary payload, or sensitive deployment value; the fixture payloads remain
  synthetic and ≤ 4 bytes. The only absolute path is the accepted workflow command path for the deterministic
  gate, identical in form to the predecessor slices.
- **Doxygen (CHK-23)** — every new case function and helper carries a `@brief` naming its requirement or
  evidence, and the file-block traceability note in each edited fixture names T024; the admitted
  documentation configuration is unchanged. Strict declaration-level Doxygen remains `DOX-GAP-01`
  (T011/T037) and is not introduced or worsened by T024.

### 4.4 Governance checks

```sh
python3 scripts/validate_xcom_task_ownership.py --verify          # passed
python3 scripts/validate_xcom_task_ownership.py --check-human     # passed
python3 scripts/validate_xcom_requirements_traceability.py --verify   # passed
python3 scripts/validate_xcom_architecture_contracts.py --verify      # passed
python3 scripts/validate_xcom_unit_design.py --verify                 # passed
```

`git rev-parse 76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6` resolves to the authorized baseline. The
capability `ref002.disposition` stays `unchanged` with an empty `promoted` list; no REF-002 or capability
requirement is promoted and no register, contract, schema, ADR, or another task's path is rewritten.

## 5. Requirement-to-change-to-check traceability

| Requirement | Realized by | Check(s) |
| --- | --- | --- |
| T024-SR-001 | additive cases inside the two existing observation executables; no build-file change | CHK-02, CHK-04, CHK-20, NEG-01 |
| T024-SR-002 | nine independently named cases; every policy built through `ObservationTapSpec::create`; explicit expected values | CHK-03, CHK-04 |
| T024-SR-003 | `test_observation_metadata_and_payload_view_matrix` Part A; 4-family × {0,1,4}-byte batch with complete normalized fields | CHK-05, NEG-02, NEG-03 |
| T024-SR-004 | `test_observation_metadata_and_payload_view_matrix` Part A batch `accepted == 12 == queued`, pulled exactly once | CHK-05, CHK-15 |
| T024-SR-005 | `test_observation_metadata_and_payload_view_matrix` Part B prefix table and bound acceptance/rejection | CHK-06, NEG-04, NEG-05 |
| T024-SR-006 | `test_observation_metadata_and_payload_view_matrix` Parts B/C redaction and no-decode assertions | CHK-06, NEG-06, NEG-07 |
| T024-SR-007 | `test_observation_ordering_matrix` drop/coalesce FIFO, coalesce position, multi-tap independence | CHK-08, NEG-08, NEG-09 |
| T024-SR-008 | `test_observation_saturation_bound_matrix` min/max drop bound and accounting identity | CHK-09, NEG-10, NEG-11 |
| T024-SR-009 | `test_observation_saturation_bound_matrix` `coalesce_latest` key selection and counters | CHK-09, NEG-12, NEG-13 |
| T024-SR-010 | `test_observation_saturation_bound_matrix` and `test_observation_route_saturation_safe_detach_matrix` lossless rejection/recovery | CHK-10, NEG-14, NEG-15 |
| T024-SR-011 | `test_observation_validity_interval_matrix` effect table and at-least-degraded rule | CHK-11, NEG-16, NEG-17 |
| T024-SR-012 | `test_observation_validity_interval_matrix` monotonicity, acknowledgement, discard-on-recreation | CHK-11, CHK-12, NEG-18, NEG-19 |
| T024-SR-013 | `test_observation_safe_detach_matrix` detach/ownership matrix | CHK-13, NEG-20, NEG-21 |
| T024-SR-014 | `test_observation_route_ordering_neutrality_matrix` and `test_observation_route_saturation_safe_detach_matrix` route invariance | CHK-14, NEG-22, NEG-23 |
| T024-SR-015 | `test_observation_normalized_record_matrix` and `test_observation_record_edge_value_matrix` | CHK-16, NEG-24 |
| T024-SR-016 | forbidden-vocabulary scan; in-process record/snapshot only | CHK-17, NEG-25 |
| T024-SR-017 | fixed capacities, ≤ 4 threads, ≤ 20-item loops, ≤ 4-byte payloads, no wall-clock verdict | CHK-18, NEG-26 |
| T024-SR-018 | `test_observation_saturation_bound_matrix` (`T24-TS-003`) bounded four-publisher lossless concurrency sub-check over three repeated runs | CHK-18, CHK-19, NEG-26 |
| T024-SR-019 | standard-library-only, offline, domain-neutral scan; successful offline build | CHK-21, NEG-27 |
| T024-SR-020 | public-safety scan of the changed fixtures and work products | CHK-22, NEG-28 |
| T024-SR-021 | additive-only diff; no existing case, assertion, target, vocabulary, or accepted behaviour changed | CHK-02, CHK-20, NEG-01, NEG-29 |
| T024-SR-022 | Doxygen on every new case/helper; file-block traceability note names T024 | CHK-23 |
| T024-SR-023 | deterministic gate, clean diff, checkbox marked only in this stage (§4) | CHK-24, NEG-29 |
| T024-SR-024 | registers re-validated; REF-002 unchanged; attribution recorded in §7 | CHK-25, NEG-29 |

Check and negative-case identifiers are the accepted [`verification-plan.md`](verification-plan.md) §4–§5.

## 6. Negative cases realized

| NEG | Defect injected | Realized case | Observed result |
| --- | --- | --- | --- |
| NEG-01 | change a non-T024 path, weaken/rename/remove an existing observation case/target/label, or change a build file | `git diff --name-only`, `ctest -N` | only the two fixtures and the T024 ledger line change; `Total Tests: 306` unchanged; every existing case preserved |
| NEG-02 | a metadata policy leaks payload bytes or reports a non-`omitted` view/schema state | `test_observation_metadata_and_payload_view_matrix` | every metadata record exposes zero bytes with `omitted`/`undecoded` |
| NEG-03 | a metadata record omits a normalized identity, miscounts `source_payload_size`, or a matched record is not retained/pulled | `test_observation_metadata_and_payload_view_matrix` | 12 records retained, pulled once, every identity and size asserted |
| NEG-04 | `bounded_prefix` reports `complete` over the bound, or copies the wrong prefix | `test_observation_metadata_and_payload_view_matrix` | the boundary table asserts `truncated` and the exact leading bytes |
| NEG-05 | a prefix bound of zero or above `kMaximumObservedPayloadBytes` is accepted | `test_observation_metadata_and_payload_view_matrix` | both are rejected, as is a non-zero bound on a non-prefix mode |
| NEG-06 | `redacted` exposes bytes or reports a non-`redacted` view | `test_observation_metadata_and_payload_view_matrix` | redacted exposes zero bytes with `redacted` |
| NEG-07 | a decode/schema success is reported | `test_observation_metadata_and_payload_view_matrix` | every row asserts `undecoded` |
| NEG-08 | retained records are not FIFO, or a coalesced replacement does not take the newest matching position | `test_observation_ordering_matrix` | drop yields `1,2,3,4`; coalesce yields `1,2,3,5` with `coalesced == 1` |
| NEG-09 | pulling one tap reorders or consumes another tap's records | `test_observation_ordering_matrix` | pulling tap `a` leaves tap `b` at `queued == 2` with its own `1,2` order |
| NEG-10 | a `drop_newest` queue exceeds its declared bound | `test_observation_saturation_bound_matrix` | capacities 1 and 16 stay within bound at every step |
| NEG-11 | a dropped record is not counted, or the accounting identity fails | `test_observation_saturation_bound_matrix` | `accepted + dropped == 5` and `== 20` hold; counters are exact |
| NEG-12 | `coalesce_latest` replaces a non-matching logical key | `test_observation_saturation_bound_matrix` | only the matching `alpha` key is replaced (`alpha` seq 3 retained) |
| NEG-13 | a coalesce loss is not counted in `coalesced` | `test_observation_saturation_bound_matrix` | `coalesced == 1` with `dropped == 2` |
| NEG-14 | `lossless_validation` mutates the provider/queue before rejecting | `test_observation_saturation_bound_matrix` and `test_observation_route_saturation_safe_detach_matrix` | `queued == 0` after rejection; route `queued_items() == 1` unchanged |
| NEG-15 | a lossless rejection is not visible in `backpressure_rejections`/validity, or capacity does not recover | both saturation cases | `backpressure_rejections == 1`, degraded validity, and a recovered commit succeeds |
| NEG-16 | the declared validity effect is not applied on a best-effort loss | `test_observation_validity_interval_matrix` | `none→valid`, `degrade_on_loss→degraded`, `invalidate_on_loss→invalid` |
| NEG-17 | a lossless backpressure is not raised to at least `degraded` | `test_observation_validity_interval_matrix` | `none` + lossless realizes `degraded` |
| NEG-18 | the realized validity status decreases without acknowledgement/detach | `test_observation_validity_interval_matrix` | two reads stay `degraded`; only acknowledgement returns `valid` |
| NEG-19 | acknowledgement does not close a `degraded` interval or lowers `invalid`, or detach/recreation does not discard the status | `test_observation_validity_interval_matrix` | `degraded` closes to `valid`; `invalid` persists; recreation starts `valid` with zero counters |
| NEG-20 | detach discards another tap's records, or a stale/foreign/claimed/closed handle is handled wrongly | `test_observation_safe_detach_matrix` | the other tap keeps `queued == 2`; `tap_busy`/`tap_closed`/`invalid_tap_handle` are exact |
| NEG-21 | a stale-generation or foreign handle still authenticates after detach | `test_observation_safe_detach_matrix` | the old generation and the foreign handle are rejected |
| NEG-22 | removing/blocking/disconnecting/failing an observer changes the route item count, FIFO order, or delivery outcome | both integration matrix cases | the route count and `per_route_fifo` order are unchanged across every observer state |
| NEG-23 | the route accepts or reorders differently after observer removal | `test_observation_route_ordering_neutrality_matrix` | the route accepts `5,6,7` in order after removal and after a failed pull |
| NEG-24 | a normalized-record field is lost or renamed, or a record is not a value copy | `test_observation_normalized_record_matrix`, `test_observation_record_edge_value_matrix` | every field round-trips; a copied record is independent of later mutation |
| NEG-25 | an export/presentation/adapter primitive appears in the T024 surface | forbidden-vocabulary scan | no such primitive is introduced or required |
| NEG-26 | the matrix uses an unbounded loop/thread/wait/retry or a wall-clock verdict | `test_observation_saturation_bound_matrix` concurrency sub-check plus source inspection and the repeated runs | capacities, threads, iterations, and payloads are finite and declared (≤ 4 threads, ≤ 16 bounded attempts, three repeated runs, atomic flags, no sleep or callback); repeated runs are deterministic |
| NEG-27 | introduce network/socket/TLS/ambient/filesystem/process/dynamic-load/legacy access, a new dependency, or a domain-specific primitive | forbidden-API scan plus the offline build | no forbidden element; only the standard library and admitted test dependencies |
| NEG-28 | introduce an environment-specific absolute host path, credential, or sensitive value into a committed file | public-safety scan | no forbidden content; the only absolute path is the accepted gate command |
| NEG-29 | change a non-T024 path, change accepted T021–T023 behaviour or vocabulary, implement a later task, promote a REF-002/capability requirement, or mark the checkbox in the plan stage | §4 gate, diff, and §7 | the production delta is empty; no vocabulary changed; the checkbox is marked only in this implementation stage; REF-002 stays `unchanged` |

## 7. Recorded attribution observation (not resolved here)

`docs/engineering/xcom/t008/requirements-register.json` attributes `XCOM-SW-OBS-005` "Normalized records for
Argus consumers" (`FR-023`) to T024 and records it as `verified_by` `XCOM-T-OBS`
(`docs/engineering/xcom/t008/traceability-matrix.json`, `XCOM-L-0100/0101/0102`, all `planned`). T024
therefore implements the **verification** obligation the register assigns: it realizes the normalized-record
and metadata/payload/ordering/saturation/validity/detach acceptance matrix over the accepted observation
boundary, and it records the payload-view allocation (`XCOM-SW-OBS-002`, unclaimed allow-list half) honestly.
T024 closes the `T021-GAP-04`/`T022-GAP-03`/`T023-GAP-01` matrix handoff. The `disabled-tap-performance`
evidence name remains T036. The registers are **not** rewritten and no maturity is promoted. The historical
SESN-era identifiers `XCOM-OBS-001…009` are retained as evidence only, and
`scripts/validate_xcom_observation.py` (legacy SESN tooling that binds `SESN_CANDIDATE_REVISION`) is neither
executed nor edited by this repository-owned workflow (`T024-LIM-08`).

## 8. Limitations and gaps

- `T024-LIM-01` — Prototype only: passing the matrix proves no runtime, telemetry, transport, timing,
  compatibility, parity, or production-readiness claim; not user-accepted (T041).
- `T024-LIM-02` — The matrix exercises the in-process observation hub, the owned loopback provider, and the
  public headers only; no legacy binary, external peer, or out-of-process path (T030–T034).
- `T024-LIM-03` — The `payloadAccess: allow-listed` identity allow-list, a redaction profile, and any
  decoder/schema status beyond `PayloadSchemaState::undecoded` remain unimplemented and partial; T024 tests
  only the accepted `metadata_only`, `bounded_prefix`, and `redacted` behaviour (`T024-GAP-01`).
- `T024-LIM-04` — `bounds.maxRateHz` rate limiting remains a declared-but-unrealized Profile bound; T024 does
  not test a rate limit (`T024-GAP-05`).
- `T024-LIM-05` — Deterministic concurrency is asserted by the bounded, repeated competing-reservation
  sub-check in `T24-TS-003` (≤ 4 threads, atomic flags, three runs), not a formal race proof; executed
  sanitizer evidence is T035's obligation (`T024-GAP-04`).
- `T024-LIM-06` — The disabled-tap performance benchmark and its `SC-008` threshold remain T036
  (`T024-GAP-02`); T024 re-runs the benchmark unchanged under the gate but claims no
  `disabled-tap-performance` evidence.
- `T024-LIM-07` — Strict declaration-level Doxygen remains `DOX-GAP-01`, owned by T011/T037; T024 adds tagged
  documentation to its new cases but does not repair that unrelated coverage debt.
- `T024-LIM-08` — `scripts/validate_xcom_observation.py` is legacy SESN-era tooling in the T-OBS path set;
  the repository-owned workflow does not use it, and T024 neither depends on nor edits it.
- Gaps `T024-GAP-01`…`-05` (payload allow-list/decoder, benchmark threshold, gateway consumer, executed
  sanitizer/delivery evidence, rate limiting) remain with their owning tasks and are **not** claimed here.

## 9. Definition of done (implementation view)

The implementation stage is complete when the six work products exist, the T024 checkbox is marked, the
deterministic gate and named checks pass at the candidate revision with no existing case weakened, this
record is written, and a separate DeepSeek internal review records a passing verdict with no findings. This
is **not** user acceptance, which remains T041; external Codex review and acceptance are deferred until the
`xcom-t011-t016-t021-t024` backlog completes.

## 10. Repair closure — `T024-IR-F01` (concurrency sub-check realization)

The internal review revision 1 recorded one medium finding, `T024-IR-F01`: the plan work products located
the `T024-SR-018` / CHK-18 / CHK-19 deterministic concurrency sub-check inside `T24-TS-003`/`T24-TS-008`,
but the candidate contained no T024 concurrency construct, so the review work products were not mutually
consistent with the delivered revision. The accepted requirements, checks, and tests were **not** weakened.

**Repair (option (a) of the finding: realize the check).** The bounded deterministic concurrency sub-check
is now realized inside the existing `T24-TS-003` case `test_observation_saturation_bound_matrix`
(`tests/xcom/observation/core/unit_tests.cpp`); no case, target, label, or command was added. A fresh
capacity-4 `lossless_validation` tap receives four publisher threads that each perform four bounded
reserve/commit attempts. Because a lossless claim is taken before provider mutation and every successful
claim is committed, the finite-capacity rule fixes the totals at exactly four commits and twelve
`observation_backpressure` rejections independent of interleaving; after `join` the case asserts the atomic
counts, `accepted == queued == 4`, `dropped == coalesced == 0`, `backpressure_rejections == 12`, degraded
`none`-effect validity, and four distinct retained sequences (no lost or duplicated claim), and it repeats
the block three times requiring the same observable outcome. No callback and no wall-clock wait is used.

**Reconciliation.** `architecture.md` §4.1/§7/§10, `detailed-design.md` §4.1/§6/§7/§10,
`unit-specifications.md` §5/§12/§13, `verification-plan.md` CHK-18/CHK-19/§6, `requirements.md`
`T024-LIM-05`, and this record now name `T24-TS-003` as the single concurrency-sub-check location and agree
on its bounds and expected result. `T024-SR-018` and CHK-18/CHK-19 are unchanged in meaning and now point at
evidence that exists at the candidate revision.

**Closure evidence (candidate-bound).**

| Command / inspection | Observed result |
| --- | --- |
| `cmake --build build/fabro-t024 --parallel 4` | exit 0 under `-Werror`; `xverse_xcom_observation_unit_tests` rebuilt and linked |
| `ctest --test-dir build/fabro-t024 -R xcom_observation --output-on-failure` | `100% tests passed, 0 tests failed out of 3` (`xcom_observation_unit`, `xcom_observation_integration`, `xcom_observation_disabled_benchmark`) |
| `xverse_xcom_observation_unit_tests` run ten consecutive times | exit 0 on every run with the same observable outcome |
| `T24-TS-003` concurrency sub-check, three internal runs | four commits, twelve rejections, four distinct sequences, `accepted == queued == 4`, `dropped == coalesced == 0`, `backpressure_rejections == 12`, degraded validity, no unstable outcome |

This closure is a successor candidate over the same authorized baseline
`76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6`; the unaffected verification is repeated in the deterministic
gate, and a fresh read-only internal review follows. It remains prototype evidence and not user acceptance
(T041).

## 11. Repair closure — terminal review R-01 (governance reconciliation)

### 11.1 Finding and scope

Terminal review `docs/reviews/t011-t016-t021-t024-terminal-status-2026-09-27.md` recorded finding **R-01**:
in the accumulated T011–T016/T021–T024 candidate at baseline
`d50bb48f45e422b8a7018710b1ac50cdadbcf8ed`, `specs/007-xcom-core/tasks.md` checks T012–T016 and
T021–T024 complete, yet `docs/engineering/xcom/task-ownership.md` still recorded each as `unreconciled`
"because the capability task checkbox is open", and A12 in `specs/007-xcom-core/analysis.md` still asserted
that those checkboxes required reconciliation. The literal checkbox-open reason is false: each named task
was delivered as a reviewed terminal candidate at an exact revision.

This repair closes R-01 as a **governance-record** successor over the same baseline. It does **not** mark any
task user-accepted, change production semantics, or broaden capability maturity. External Codex review and
explicit user acceptance remain deferred until the backlog completes.

**Recorded plan-stage finding (before repair).** The revision-3 pre-code work products initially scoped the
repair to governance records only and excluded every `tests/` path. The deterministic T024 gate
(`xcom_feature_gate.py verify T024 <baseline>`) requires a candidate for the test task T024 to change at
least one `tests/` path, so the pre-code statement was not realizable as written. The repair therefore adds
exactly one offline governance regression test and reconciles `requirements.md` §11, `architecture.md`
§11, `detailed-design.md` §11.5, `unit-specifications.md` §15.6, and `verification-plan.md` §10 to the
realized change. No accepted requirement, check, or existing test is weakened.

### 11.2 Changed paths (12 candidate paths, bound to §11.5 of `requirements.md`)

The repair authors 12 candidate paths (11 tracked modifications plus the one new regression test). Two
further paths — `docs/engineering/xcom/t024/internal-review.json` and
`reports/xcom-queue/t024-package.json` — are generated by the review and package stages and are not authored
changes. The deterministic gate's `candidate_paths` is `sorted((tracked | untracked) - generated)`, so it
subtracts those two generated records from the tracked-and-untracked union and reports the same 12 paths even
though this repair baseline already tracks both generated records (see §11.4).

| Path | Change |
| --- | --- |
| `docs/engineering/xcom/task-ownership.json` | T012–T016, T021–T024 reconciliation → `delivered` with exact revision + pending-acceptance reason |
| `docs/engineering/xcom/task-ownership.md` | Regenerated deterministic projection (9 reconciliation lines) |
| `specs/007-xcom-core/analysis.md` | A12 disposed; dated `2026-09-27 terminal review R-01 repair` successor note |
| `scripts/validate_xcom_task_ownership.py` | `delivered` vocabulary + pin set; revision/reason/relabel gates; `NEG-21..25` fixtures |
| `scripts/validate_xcom_requirements_traceability.py` | `delivered` coverage branch; docstring/comment accuracy |
| `tests/test_xcom_task_ownership_reconciliation.py` | New offline governance regression test (7 cases) |
| `docs/engineering/xcom/t024/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md` | This repair's work products |

No `src/`, existing-`tests/`, `xdl/`, `cmake/`, `CMakeLists.txt`, `proto/`, contract, schema, ADR, or
accepted predecessor (`t008`/`t009`/`t010`) content is changed. `specs/007-xcom-core/tasks.md` is unchanged
because the T024 checkbox was already complete.

### 11.3 Delivered-state reconciliation

Each of the nine entries records `status = delivered`, its exact reviewed terminal candidate revision, and
a reason stating that external Codex review and explicit user acceptance remain pending. T025 remains the
only `accepted` entry; no task is relabelled accepted; every REF-002 disposition stays `unchanged` with an
empty `promoted` list. The accepted T008/T009/T010 predecessor work products keep their historical
open-checkbox language byte-unchanged and are superseded for the current state by the dated analysis note,
not rewritten.

### 11.4 Closure evidence (baseline `d50bb48f45e422b8a7018710b1ac50cdadbcf8ed`)

| Command / inspection | Observed result |
| --- | --- |
| `python3 scripts/validate_xcom_task_ownership.py --verify` | exit 0 (positive register) |
| `python3 scripts/validate_xcom_task_ownership.py --check-human` | exit 0 (byte-stable projection) |
| `python3 scripts/validate_xcom_task_ownership.py --self-test` | positive passes; `NEG-21..25` each rejected with `GATE_INVALID` (exit 8); `DET-02` with `DETERMINISM_INVALID` (exit 9) |
| `python3 scripts/validate_xcom_requirements_traceability.py --verify` / `--check-human` | exit 0 |
| `python3 scripts/validate_xcom_requirements_traceability.py --self-test` | positive passes; `NEG-17` (T012-owned requirement reason dropped) rejected with `MATURITY_INVALID` (exit 8); `NEG-28` with `BINDING_INVALID` (exit 9) |
| `python3 scripts/validate_xcom_architecture_contracts.py --verify` / `--check-human` / `--self-test` | all exit 0 (unchanged by this repair) |
| `python3 scripts/validate_xcom_unit_design.py --verify` / `--check-human` / `--self-test` | all exit 0 (unchanged by this repair) |
| `python3 -m pytest tests/test_xcom_task_ownership_reconciliation.py -q` | `7 passed` |
| `python3 -m pytest -q` (validation) | `147 passed, 24 subtests passed` (140 baseline + 7 new) |
| `run_xcom_system_tests.py unit` | `100% tests passed, 0 tests failed out of 52` |
| `run_xcom_system_tests.py integration` | `147 passed, 24 subtests passed` |
| `xcom_feature_gate.py verify T024 d50bb48…` | `{"ok": true, …, "changed_paths": 12, "checks": ["ctest:306"]}` |
| `git diff --check d50bb48… --` | clean |
| `git diff --name-only d50bb48… -- docs/engineering/xcom/t00{8,9} docs/engineering/xcom/t010` | empty (accepted predecessor preserved) |

The gate's `candidate_paths` is `sorted((tracked | untracked) - generated)`, where `generated` is exactly
`docs/engineering/xcom/t024/internal-review.json` and `reports/xcom-queue/t024-package.json`. The two
generated records are subtracted from the union, so the exact candidate inventory is 12 regardless of the
fact that this repair baseline already tracks both: the 11 tracked T024/R-01 modifications and the single
new untracked `tests/test_xcom_task_ownership_reconciliation.py`. The internal review's `reviewed_paths`,
`xcom_feature_gate.py review`, and `prepare_xcom_queue_candidate.py` (candidate gate) all resolve to the
same 12 paths. The two generated records are written by the review and package stages and are verified by
their own deterministic actions, not by the candidate inventory.

Changed-artifact SHA-256 (this successor candidate):

| Path | SHA-256 |
| --- | --- |
| `docs/engineering/xcom/task-ownership.json` | `6d5c6c668b7ca55a2ca7b349b770c054a4d493ea8889a380d735334cfa6a7d99` |
| `docs/engineering/xcom/task-ownership.md` | `5958068897aaf7276336d4c33e5665c23191f51045508f70a4e4b7b06a1427eb` |
| `specs/007-xcom-core/analysis.md` | `ee2ac8a879e409fc5d15b5550dff4de1b3625f8a1ce7e4c1b796815bc2d6b241` |
| `scripts/validate_xcom_task_ownership.py` | `30d6e11aeea5ec64c223e6fc68d38f45e76083e53a3a5cba8ed74fb011b98a01` |
| `scripts/validate_xcom_requirements_traceability.py` | `20fcc06be2c58fa825103f87cafbfe8357fddbfc58f715d7d9c3ec28d2785f8b` |
| `tests/test_xcom_task_ownership_reconciliation.py` | `c38edf25dc17672d663c5d6462a8dde4cf6fb66e75d27e1fc41cb71c164c39f9` |

The deterministic package action records the 12 candidate work-product hashes in
`reports/xcom-queue/t024-package.json`; the generated review and package hashes are bound by the terminal
collector and the reviewed-checkpoint record, not by the package manifest itself.

### 11.5 Failure semantics

A `delivered` entry with a missing or non-40-hex revision, an empty reason, a divergent pinned revision, a
required task reverted to another status, or a task relabelled `accepted` without an accepted record fails
`GATE_INVALID` (exit 8); a projection drift fails `DETERMINISM_INVALID` (exit 9); a requirement owned by a
`delivered` task that is made `implemented` or stripped of its reason fails `MATURITY_INVALID` (exit 8). No
failure path writes the candidate tree or mutates accepted evidence.

### 11.6 Limitations and pending gates

- The repaired state is `delivered`, **not** accepted. External Codex review and explicit user acceptance
  of this successor candidate remain pending (`T024-OPEN-R01-01`); no task in T012–T024 is closed by this
  repair.
- The accepted predecessor T008/T009/T010 work products still contain their historical open-checkbox
  sentences; they are preserved byte-unchanged and disposed by the dated analysis successor note.
- The repair is governance-only; it proves no runtime, compatibility, parity, or production-readiness claim.
- This repair baseline already tracks the two generated artifacts
  (`docs/engineering/xcom/t024/internal-review.json` and `reports/xcom-queue/t024-package.json`). The review
  stage regenerates the review record and the package stage regenerates the manifest, and the corrected
  deterministic `candidate_paths` subtracts both generated records from the tracked-and-untracked union. The
  exact candidate inventory is therefore the 12 authored changes of §11.2, and the review record's
  `reviewed_paths` is set to that same 12-path inventory so the review, package, and candidate gates agree;
  including either generated record would over-report the inventory and fail the corrected package gate.

### 11.7 Traceability (repair view)

| Requirement | Realized by |
| --- | --- |
| `T024-R01-SR-001` | register + projection `delivered` entries; task-ownership validator pin/gate |
| `T024-R01-SR-002` | `analysis.md` A12 and dated successor note |
| `T024-R01-SR-003` | unchanged T008/T009/T010 bytes; dated successor note |
| `T024-R01-SR-004` | task-ownership and requirements-traceability validator edits; self-test negatives |
| `T024-R01-SR-005` | T025 is the only accepted task; all REF-002 dispositions `unchanged` |
| `T024-R01-SR-006` | deterministic gate, validator modes, pytest, CTest re-runs |
| `T024-R01-SR-007` | changed-path inventory; accepted-predecessor diff empty |
| `T024-R01-SR-008` | public-safety scans in the validator modes |
| `T024-R01-SR-009` | `tests/test_xcom_task_ownership_reconciliation.py` |

### 11.8 Repair closure — internal review revision 3 findings (`T024-R01-IR-F01`..`F03`)

The first read-only internal review of this successor candidate returned verdict `fail` with three minor
documentation/traceability findings (`docs/engineering/xcom/t024/internal-review.json`, review revision 3).
The governance reconciliation, the register, the validators, and the tests were correct; only the new
work-product prose was inconsistent. No register value, validator behavior, test, or accepted requirement is
changed by this repair, and the changed-path inventory remains the same 12 paths as §11.2.

| Finding | Defect | Repair |
| --- | --- | --- |
| `T024-R01-IR-F01` | `architecture.md` §11.1 body said "Revision 2" under a "Revision 3" section title and header | changed the sentence to "Revision 3" |
| `T024-R01-IR-F02` | `unit-specifications.md` §15.3 recorded the requirements-traceability `NEG-17` self-test class as `exit 5` instead of the validator's `EXIT_MATURITY = 8` | corrected the parenthetical to `exit 8` |
| `T024-R01-IR-F03` | `R01-NEG-08` was cited as the predecessor-path guard and covered an unscanned `analysis.md` input, and its public-safety exit class was ambiguous | bound `R01-NEG-08` to the inputs `validate_xcom_task_ownership.py` actually scans (`task-ownership.json`/`task-ownership.md`, `exit 10`); removed the A12 and predecessor claims; relabelled `T024-R01-SR-003` / `T24-R01-TS-004` to the repository-inventory checks R01-CHK-05/R01-CHK-13 |

**Closure evidence (baseline `d50bb48f45e422b8a7018710b1ac50cdadbcf8ed`).**

| Command / inspection | Observed result |
| --- | --- |
| `rg -n 'Revision 3 is a \*\*governance-record repair\*\*' docs/engineering/xcom/t024/architecture.md` | exactly one match (line 266) |
| `rg -n 'Revision 2 is a' docs/engineering/xcom/t024/architecture.md` | no match |
| `rg -n 'exit 5' docs/engineering/xcom/t024/unit-specifications.md` | no match |
| `rg -n 'MATURITY_INVALID\` \(\`exit 8\`\)' docs/engineering/xcom/t024/unit-specifications.md` | one match (`T24-R01-TS-003`) |
| `python3 scripts/validate_xcom_requirements_traceability.py --self-test` | positive passes; `NEG-17: rejected with MATURITY_INVALID (exit 8)` |
| `rg -n 'R01-NEG-08' docs/engineering/xcom/t024/` | only the `R01-NEG-08` definition and its `T024-R01-SR-008` mapping plus the `T24-R01-TS-004` scoping note; no predecessor-path claim |
| `python3 scripts/validate_xcom_task_ownership.py --verify` / `--check-human` / `--self-test` | exit 0; positive passes; `NEG-21..25` reject `GATE_INVALID` (exit 8); `DET-02` rejects `DETERMINISM_INVALID` (exit 9) |
| `python3 -m pytest tests/test_xcom_task_ownership_reconciliation.py -q` | 7 passed (no test changed by this repair) |
| `git diff --name-only d50bb48… -- docs/engineering/xcom/t00{8,9} docs/engineering/xcom/t010` | empty (accepted predecessor bytes still unchanged) |

The repair produces a successor candidate over the same baseline; the unaffected verification is repeated
in the deterministic gate and a fresh read-only internal review follows. This still does not mark any task
user-accepted; external Codex review and explicit user acceptance remain pending (`T024-OPEN-R01-01`).

### 11.9 Corrected generated-record inventory

The prior reviewed run reached its delivery gates but terminal sealing failed: the regenerated
`reports/xcom-queue/t024-package.json` still carried its own pre-regeneration hash (and the tracked review
record) because, once this repair baseline already tracked both, the earlier gate counted the two generated
records as candidate changes. The deterministic candidate inventory and the terminal collector now subtract
`docs/engineering/xcom/t024/internal-review.json` and `reports/xcom-queue/t024-package.json` from the
tracked-and-untracked union, and the collector rejects any package manifest whose `files` map contains those
records. This successor candidate reconciles the work products to the corrected semantics: §11.2 and §11.4
record the 12-path `candidate_paths`, §11.6 records that the manifest cannot include itself, and §11.5 of
`requirements.md` marks the two generated records as excluded from the candidate inventory. The package
action regenerates the manifest with only the 12 candidate hashes, and the fresh read-only internal review
supersedes the retained revision-4 review record and sets `reviewed_paths` to the same 12 paths.
