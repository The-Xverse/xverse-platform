# T023 Implementation Record — Synthetic Sink, Failure/Disconnect Isolation, and Visible Counters

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T023 (capability 007, slice `T-OBS`) |
| Stage / role | implementation → implementation record |
| Revision | 1 |
| Authorized baseline | `d455c70816eb784066740427a70df9235cd1287d` |
| Predecessor | T022 reviewed terminal package (`docs/engineering/xcom/t022/`) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned at the workflow checkpoint) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | `docs/engineering/xcom/t023/internal-review.json` (separate read-only DeepSeek review, produced by the review stage) |
| Package record | `reports/xcom-queue/t023-package.json` (produced by the deterministic package action) |
| Authorization | ACC005/ACC010/ACC011/ACC014/ACC015; ADR-0016; ADR-0018; ADR-0019; ADR-0020; `specs/007-xcom-core/tasks.md` T023 |
| Maturity | Prototype-only synthetic-sink counter/isolation layer implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T023 implements the bounded slice required by the T023 task entry: *"Implement the synthetic sink and
prove failure/disconnect isolation and visible counters."*

The candidate realizes the **consumer-sink half** of the accepted observation boundary described by
`XCOM-SW-OBS-004` (FR-014/SC-005, design unit `XCOM-DU-013`, component `XCOM-CMP-011`): the
`SyntheticObservationSink` gains one immutable, value-owned consumer counter projection
(`SyntheticSinkCounters`: `pulled`, `empty`, `disconnected`, `failed`) that makes the consumer's own pull
outcomes visible without a durable log, a callback, or a view into hub storage. `pull()` now maintains the
projection on the actual outcome (one counter per call), and `connect()` re-validates the copied exact
handle through the const authentication path. The focused cases prove three isolation rules:

- **Local disconnect isolation** — a disconnected sink returns the stable `sink_disconnected`, consumes no
  record, and leaves every tap, tap counter, generation, and the normal route unchanged.
- **Failure isolation** — a stale, foreign, or closed exact handle returns the stable `invalid_tap_handle`
  and is counted in `failed`, while every tap and the normal route remain unchanged; a stale/foreign
  `connect()` is refused and leaves the sink disabled.
- **Blocking (non-pulling) isolation** — a connected sink that never pulls does not block, delay, reorder,
  or change a submission; the observed tap stays within its declared bound with deterministic
  `dropped`/`coalesced` counters visible through the exact-handle `ObservationSnapshot`, and the sink's own
  counters stay zero until it pulls.

Every accepted baseline behaviour that T023 does not own — contract version `1.0.0`, filter matching,
payload modes/bounds/views, `undecoded` schema state, declared identities, record self-description,
attach/authentication/generation/capacity, the coalescing key, the retention drop/coalesce/lossless rules,
the applied declared validity effect, the realized validity status, the enumerated `ObservationOutcome`
vocabulary, reservation single-use semantics, and the single-mutex copy-after-unlock concurrency model — is
preserved byte-identically. T023 implements **no** T024 broad matrix, payload identity allow-list, decoder,
rate limit, temporization, retry, quota, persistence, transport, gateway, or storage behaviour.

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/observation.hpp` | edit | Add `SyntheticSinkCounters` (four fixed `std::uint64_t` fields), the sink's read-only `noexcept counters()` accessor, and four fixed counter members; update the sink class/file-block Doxygen and the traceability note to name `XCOM-SW-OBS-004`/T023; no existing declaration or enumerator removed, renamed, or narrowed |
| `src/xverse/xcom/src/observation.cpp` | edit | `SyntheticObservationSink::pull` maintains the visible counters on the actual outcome (`pulled`/`empty`/`failed`/`disconnected`); `connect` re-validates the copied exact handle and never changes the counters; the T021/T022 declaration, retention, validity, payload, record, and handle behaviour is otherwise byte-identical |
| `tests/xcom/observation/core/unit_tests.cpp` | edit | Add four focused T023 cases and register them in `main()`; update the file-block traceability note; every existing assertion and case preserved |
| `tests/xcom/observation/integration/integration_tests.cpp` | edit | Add one focused route-level sink failure/disconnect isolation case and register it in `main()`; every existing case and assertion preserved |
| `docs/engineering/xcom/t023/*.md` | add | Five plan-stage work products plus this implementation record |
| `docs/engineering/xcom/t023/internal-review.json` | add (review stage) | DeepSeek internal review |
| `reports/xcom-queue/t023-package.json` | add (package stage) | Exact-candidate package record |
| `specs/007-xcom-core/tasks.md` | edit | T023 checkbox marked complete (implementation stage only) |

No `CMakeLists.txt` or `cmake/*.cmake`, no `src/xverse_xdl/`, `xdl/`, `proto/`, or `contracts/` path, no other
production unit (`activation_plan.*`, `provider.*`, `loopback_provider.*`, `endpoint_route_lifecycle.*`,
`contract.hpp`, `item.hpp`, `value.hpp`, `result.hpp`, `diagnostic.hpp`, `validation_session.*`,
`stimulation_journal.*`), no `tests/xcom/observation/integration/{test_support.hpp,disabled_tap_benchmark.cpp}`,
and no other task's ownership path is changed. The build file needs no edit: the existing
`xverse::xcom_observation` target compiles `observation.cpp` and the existing observation executables compile
the two edited fixtures, so the new cases are discovered without adding or renaming a target, test, or label.

### 3.1 Changed public symbols

- New: `SyntheticSinkCounters` — immutable value-owned consumer counter projection with `pulled`, `empty`,
  `disconnected`, and `failed` (four fixed `std::uint64_t` fields, all defaulting to zero).
- Extended (additive only): `SyntheticObservationSink` gains one trailing `noexcept` accessor
  `counters()` and four private counter members; the constructor, copy constructor, non-assignment,
  `connect`, `disconnect`, `pull`, and `connected` signatures are unchanged. `pull()` now increments exactly
  one counter per call; `connect()` and `disconnect()` change no counter.
- Unchanged: `ObservationOutcome`, `ObservationOverflowPolicy`, `ObservationValidityEffect`, and
  `ObservationValidityState` vocabularies; `ObservationSnapshot`; `ObservationRecord`;
  `ObservationTapHandle`; every `ObservationHub` operation signature; the reserve/commit/cancel claim
  protocol; the retention ordering, coalescing key, and payload-view rules.
- New/changed public declarations carry `@brief` plus the applicable ownership/lifetime/thread-safety/
  failure Doxygen tags in the existing file-block style; the admitted documentation configuration is
  unchanged.

### 3.2 Changed artifact hashes (SHA-256, this candidate)

| Path | SHA-256 |
| --- | --- |
| `src/xverse/xcom/include/xverse/xcom/observation.hpp` | `eda631bd4062ec213b49ef196823b4c4608bb88633ffeab03a8b1413c530ef3d` |
| `src/xverse/xcom/src/observation.cpp` | `3385ab0dc897609445bf30729b7ddfe149ae7931554268eb1fb80207f0e15979` |
| `tests/xcom/observation/core/unit_tests.cpp` | `eebe44068ff41d64b610181556d5e8f5732ec6641367f84937301ef3d27fe72a` |
| `tests/xcom/observation/integration/integration_tests.cpp` | `3e54ff46fd75a27017d30870d90919ccd4ac52998adcf007931438cd46aa37b8` |

The work-product and package hashes are recorded by the deterministic package action in
`reports/xcom-queue/t023-package.json`.

## 4. Deterministic gate

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T023 d455c70816eb784066740427a70df9235cd1287d
```

Observed result (implementation stage): `ok`, with `changed_paths: 11` and `ctest:306` — the six T023 work
products present, the T023 checkbox marked complete, at least one `src/xverse/xcom/` path changed, the
configure/build/discovery/full-`ctest` sequence exiting 0, and `git diff --check` clean. The gate's
configure reuses the T023 build cache seeded with the previously admitted A-1 `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` values (named by role only; no
ambient path or network resolution was added, and no admission check was weakened).

### 4.1 Build and test environment

| Item | Value |
| --- | --- |
| Configure (A-1 cache seed) | `cmake -S . -B build/fabro-t023 -G Ninja -DCMAKE_BUILD_TYPE=Debug -D<three admitted A-1 inputs>` (exit 0) |
| Configure (plain, reused by the gate) | `cmake -S . -B build/fabro-t023 -G Ninja -DCMAKE_BUILD_TYPE=Debug` (exit 0) |
| Build | `cmake --build build/fabro-t023 --parallel 4` (exit 0) |
| Toolchain | host GNU C++ 11.4.0 (`-std=c++20`) under the T012 `-Wall -Wextra -Wpedantic -Werror` contract |
| Discovery | `ctest --test-dir build/fabro-t023 -N` → `Total Tests: 306` |
| Full suite | `ctest --test-dir build/fabro-t023 --output-on-failure --parallel 4` → `100% tests passed, 0 tests failed out of 306` |
| Diff hygiene | `git diff --check d455c70816eb784066740427a70df9235cd1287d --` → clean |

The discovered count matches the baseline 306, proving no target, name, or label was added, renamed, or
removed.

### 4.2 Observation evidence

| Target | Command | Result |
| --- | --- | --- |
| `xcom_observation_unit` | `ctest -R xcom_observation` / direct executable | Passed (exit 0); four added cases plus twenty-four preserved cases in one executable |
| `xcom_observation_integration` | `ctest -R xcom_observation` | Passed (exit 0); one added case plus seven preserved cases |
| `xcom_observation_disabled_benchmark` | `ctest -R xcom_observation` | Passed (exit 0); not edited |
| core/lifecycle/provider/validation/activation-plan suites | full `ctest` run | Passed; additivity confirmed |

Added unit cases (base 24 → 28 test functions): `test_synthetic_sink_visible_counters`,
`test_synthetic_sink_disconnect_isolation`, `test_synthetic_sink_failure_isolation`,
`test_synthetic_sink_blocking_isolation`. Added integration case (base 7 → 8):
`test_synthetic_sink_route_isolation_counters`. Preserved unit case `test_synthetic_sink_concurrency` (and
every other case) is unchanged in behaviour.

### 4.3 Source inspections

- **Visible counters (CHK-06, CHK-15)** — `SyntheticSinkCounters` is four fixed 64-bit values; the sink
  updates exactly one counter per `pull()` call on the actual outcome and keeps the accounting identity
  `pulled + empty + disconnected + failed == pull attempts`; the tap loss counters
  (`queued`/`accepted`/`dropped`/`coalesced`/`backpressure_rejections`) remain on the exact-handle
  `ObservationSnapshot` and are neither duplicated nor reinterpreted.
- **Read-only authority (CHK-10)** — the sink calls only `hub_->poll(handle_)` and the const
  authentication reached through `hub_->snapshot(handle_)` in `connect()`; a scan of `observation.cpp`
  finds no sink call to `detach`, `acknowledge`, `reserve`, `commit`, or `cancel` (the only
  `hub_->cancel_from_destructor` match is in the unrelated `ObservationReservation` destructor).
- **Bounds (CHK-13)** — `kObservationContractVersion{"1.0.0"}`, `kMaximumObservationTaps{8U}`,
  `kMaximumObservationRecordsPerTap{16U}`, and `kMaximumObservedPayloadBytes{1024U}` are unchanged; the sink
  footprint is one non-owning pointer, one copied handle, one bool, and four counters. A scan of
  `observation.cpp` finds no `new`/`delete`/`malloc`/`std::vector`/`make_unique`/`make_shared` and no timer,
  retry, rate, quota, or wall-clock input on any T023 path.
- **Offline and domain-neutral (CHK-17)** — a forbidden-API scan of the two changed production files finds
  no network/socket/resolver/TLS, ambient/secret lookup, filesystem, process, dynamic-load, or legacy
  access; the only `connect`/`disconnect` matches are the in-process `SyntheticObservationSink` methods. The
  candidate adds no dependency beyond the C++ standard library and contains no domain-specific, export,
  dashboard, storage, or query primitive; the offline configure/build succeeds.
- **Public safety (CHK-18)** — a scan of the changed sources, tests, and work products finds no credential,
  private address, real or proprietary payload, environment-specific absolute host path, or sensitive
  deployment value; the fixture payloads remain synthetic and ≤ 4 bytes and the concurrency fixtures remain
  ≤ 4 threads with no wall-clock threshold. The only `/home/...` match is the accepted workflow command path
  for the deterministic gate, identical in form to the predecessor slices.
- **Doxygen (CHK-19)** — every new/changed public declaration (`SyntheticSinkCounters`, its four fields, the
  sink's `counters()` accessor, and the updated `connect`/`pull`/`disconnect` contract) carries `@brief`
  plus the applicable ownership/lifetime/thread-safety/failure tags; the admitted configuration is
  unchanged. The existing documentation validator (`scripts/check_doxygen.py`) fails **pre-existing** on
  Python docstring coverage in unchanged files (`scripts/**`, `src/xverse_xdl/xcom_plan.py`); that coverage
  gap is DOX-GAP-01, owned by T011/T037, and is not introduced or worsened by T023 (`T023-LIM-08`).

### 4.4 Governance checks

```sh
python3 scripts/validate_xcom_task_ownership.py --verify          # passed
python3 scripts/validate_xcom_task_ownership.py --check-human     # passed
python3 scripts/validate_xcom_requirements_traceability.py --verify   # passed
python3 scripts/validate_xcom_architecture_contracts.py --verify      # passed
python3 scripts/validate_xcom_unit_design.py --verify                 # passed
```

`git rev-parse d455c70816eb784066740427a70df9235cd1287d` resolves to the authorized baseline. The
capability `ref002.disposition` stays `unchanged` with an empty `promoted` list; no REF-002 or capability
requirement is promoted and no register, contract, schema, ADR, or another task's path is rewritten.

## 5. Requirement-to-change-to-check traceability

| Requirement | Realized by | Check(s) |
| --- | --- | --- |
| T023-SR-001 | `SyntheticSinkCounters` + `counters()` value copy; monotonic per-sink projection, no hub view | CHK-06, CHK-15, NEG-01, NEG-02 |
| T023-SR-002 | `pull` success → `pulled` + 1 with value-owned record; `no_record` → `empty` + 1; no other field changes | CHK-06, NEG-01 |
| T023-SR-003 | `pull` while disconnected → `sink_disconnected`, `disconnected` + 1, no `poll`, no tap/route mutation | CHK-07, NEG-03, NEG-05 |
| T023-SR-004 | `pull` on a stale/foreign/closed handle → `invalid_tap_handle`, `failed` + 1, no slot mutation | CHK-08, NEG-04, NEG-05 |
| T023-SR-005 | `connect` re-validates via the const authentication path; valid → `accepted`, else `invalid_tap_handle` with the sink disabled; counters unchanged | CHK-07, NEG-03, NEG-04 |
| T023-SR-006 | non-pulling connected sink: tap stays bounded, `dropped`/`coalesced` visible on the snapshot, sink counters zero until it pulls; route count/order unchanged | CHK-09, NEG-06, NEG-07 |
| T023-SR-007 | sink calls only `poll`/const authentication; no detach/acknowledge/reserve/commit/cancel | CHK-10, NEG-05, NEG-08 |
| T023-SR-008 | single hub mutex serialization; counters updated on the calling thread only; value copies returned; no callback | CHK-11, CHK-12, NEG-09 |
| T023-SR-009 | fixed pointers/handle/bool/four counters; no allocation, timer, retry, rate, or quota | CHK-13, CHK-18 |
| T023-SR-010 | standard-library-only, offline, domain-neutral scan; successful offline build | CHK-17, NEG-10 |
| T023-SR-011 | public-safety scan of committed sources/tests/work products | CHK-18, NEG-11 |
| T023-SR-012 | Doxygen on every new/changed declaration; admitted configuration unchanged (§4.3) | CHK-19 |
| T023-SR-013 | additive-only diff; no removed/renamed/weakened case, target, vocabulary, or accepted behaviour | CHK-02, CHK-14, CHK-20, CHK-23, NEG-12, NEG-13 |
| T023-SR-014 | deterministic gate, clean diff, checkbox marked only in this stage (§4) | CHK-21 |
| T023-SR-015 | registers re-validated; REF-002 unchanged; attribution recorded in §7 | CHK-20, CHK-22 |
| T023-SR-016 | no `ObservationOutcome` value added/renamed/reordered; disconnect/empty/failure use only the accepted values | CHK-05, CHK-14 |

Check and negative-case identifiers are the accepted [`verification-plan.md`](verification-plan.md) §4–§5.

## 6. Negative cases realized

| NEG | Defect injected | Realized case | Observed result |
| --- | --- | --- | --- |
| NEG-01 | a pull sequence mixing records, empty pulls, a disconnect, and a stale handle | `test_synthetic_sink_visible_counters` | each counter increments once for its outcome; `pulled + empty + disconnected + failed == 5` attempts |
| NEG-02 | a successful pull miscounted, or an empty pull counted as `pulled` | `test_synthetic_sink_visible_counters` | `pulled == 2`, `empty == 1` after two records and one empty pull; a miscount fails the case |
| NEG-03 | local `disconnect()` then `pull()`, then `connect()` on a valid handle | `test_synthetic_sink_disconnect_isolation` | `sink_disconnected` with `disconnected` + 1; tap `queued`/`accepted` unchanged; reconnect restores the retained record |
| NEG-04 | pull after the observed tap is detached or its slot recreated | `test_synthetic_sink_failure_isolation`, `test_synthetic_sink_visible_counters` | `invalid_tap_handle` with `failed` + 1; the recreated slot keeps `accepted`/`queued` at zero; stale `connect()` refused and sink disabled |
| NEG-05 | a foreign-hub handle, or a tap mutated by the sink | `test_synthetic_sink_failure_isolation` | `invalid_tap_handle` for the foreign pull with no slot mutation in either hub; source scan confirms no detach/acknowledge/reserve/commit/cancel |
| NEG-06 | a connected sink that never pulls while the writer saturates the tap | `test_synthetic_sink_blocking_isolation` | submissions stay best-effort and bounded; sink counters stay zero until it pulls |
| NEG-07 | a saturated tap hides its loss, or a drop/coalesce counter is not visible | `test_synthetic_sink_blocking_isolation` | `dropped == 3` (drop-newest) and `coalesced == 3` (coalesce-latest) are visible on the exact-handle snapshot within `queued == 2` |
| NEG-08 | a view/reference into hub or sink storage escaping a call, or a callback under the lock | source scan plus the preserved concurrency case | records and counter projections are value copies returned after unlock; the boundary has no callback path |
| NEG-09 | a pull not serialized through the hub, or a counter updated off the calling thread | `test_synthetic_sink_concurrency` (preserved), source scan | serialized pull/publication; counters updated on the calling thread only |
| NEG-10 | network/socket/TLS/ambient/filesystem/process/dynamic-load/legacy access, a new dependency, or a domain-specific primitive | §4.3 scan | no forbidden element; offline build succeeds |
| NEG-11 | an environment-specific absolute host path, credential, or sensitive value into a committed file | §4.3 scan | no forbidden content; the only absolute path is the accepted gate command |
| NEG-12 | weaken/rename/remove an existing observation test, change a non-T023 path, change accepted T021/T022 behaviour, or add/rename an `ObservationOutcome` value | `git diff --name-only`, `git diff`, vocabulary inspection | the production delta is limited to the sink counters; no existing case or vocabulary changed; T021/T022 regions byte-identical |
| NEG-13 | mark the checkbox in the plan stage, or claim an accepted/promoted REF-002 or capability requirement, or claim the broad matrix/benchmark/gateway evidence | §4 gate and §7 | the checkbox is marked only in this implementation stage; REF-002 stays `unchanged` and no matrix/benchmark/gateway evidence is claimed |

## 7. Recorded attribution observation (not resolved here)

`docs/engineering/xcom/t008/requirements-register.json` attributes `XCOM-SW-OBS-004` "Observer isolation and
safe detach" to T023, while `docs/engineering/xcom/t010/unit-design.json` links `XCOM-DU-013`
(owning tasks T022/T023) to `XCOM-SW-OBS-003`/`-004` and `XCOM-CMP-011` (owning tasks T023/T032/T033) to
`XCOM-SW-OBS-005`/`XCOM-SYS-FR-023`. T023 therefore implements the **synthetic-sink counter/isolation**
half of `XCOM-SW-OBS-004` and the `XCOM-CMP-011` synthetic-sink responsibility, preserves the accepted
T021/T022 declaration, retention, and validity behaviour unchanged, and rewrites nothing. The payload-view
`payloadAccess: allow-listed` identity allow-list and any decoder/schema status beyond
`PayloadSchemaState::undecoded` remain unimplemented and partial (`T023-LIM-04`, `T023-GAP-04`). The
registers are **not** rewritten and no maturity is promoted. The historical SESN-era identifiers
`XCOM-OBS-001…009` are retained as evidence only, and `scripts/validate_xcom_observation.py` (legacy SESN
tooling that binds `SESN_CANDIDATE_REVISION`) is neither executed nor edited by this repository-owned
workflow (`T023-LIM-06`).

## 8. Limitations and gaps

- `T023-LIM-01` — Prototype only: no runtime, telemetry, transport, timing, compatibility, parity, or
  production-readiness claim; not user-accepted (T041).
- `T023-LIM-02` — The consumer counters are an in-process, per-sink projection; they are not a durable log
  and are discarded with the sink. Durable experiment evidence and presentation belong to T035/Argus and are
  not implemented here.
- `T023-LIM-03` — The sink counters describe the consumer's own pull outcomes only; the tap's deterministic
  loss counters remain on `ObservationHub::snapshot` and are not duplicated by the sink.
- `T023-LIM-04` — Observer failure is modeled as the accepted stale/foreign/closed exact-handle outcome
  (`invalid_tap_handle`); no new failure-injection API or `ObservationOutcome` value is introduced.
- `T023-LIM-05` — The separate-process synthetic client and the external tool-gateway observation stream
  remain T032/T033; T023 realizes only the in-process sink.
- `T023-LIM-06` — `scripts/validate_xcom_observation.py` is legacy SESN-era tooling in the T-OBS path set;
  it is neither executed nor edited and is not T023 evidence.
- `T023-LIM-07` — The sink retains a non-owning hub reference, so the referenced hub must outlive the sink;
  this is the accepted precondition and is not enforced at runtime.
- `T023-LIM-08` — The documentation-coverage gate `scripts/check_doxygen.py` fails pre-existing on unchanged
  Python sources (DOX-GAP-01, owned by T011/T037); T023 adds tagged Doxygen to its declarations but does not
  run or repair that gate's unrelated coverage debt.
- Gaps `T023-GAP-01`…`-06` (broad observation matrix, benchmark threshold, gateway consumer, payload
  allow-list/decoder, executed sanitizer/delivery evidence, T008/T010 attribution nuance) remain with their
  owning tasks and are **not** claimed here.

## 9. Definition of done (implementation view)

The implementation stage is complete when the six work products exist, the T023 checkbox is marked, the
deterministic gate and named checks pass at the candidate revision with no existing case weakened, this
record is written, and a separate DeepSeek internal review records a passing verdict with no findings.
This is **not** user acceptance, which remains T041; external Codex review and acceptance are deferred
until the `xcom-t011-t016-t021-t024` backlog completes.
