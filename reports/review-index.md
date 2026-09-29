# T020 review index — accumulated X-COM candidate

Candidate: T020 on baseline `1e289bfe6234553df94eb25065371f7d423fad88` (reviewed T019 terminal package), queue
`xcom-t007-t010-t017-t020`, queued run `01M3H4QN7Y1HC152JH0D4ZKMJ1`.

This candidate is a queue-run candidate only. External Codex acceptance, the trusted
unit/integration/validation/static measures, and the delivery package are separate gates;
none is claimed complete by this index.

## Reviewed T020 change set (baseline diff)

Documentation and work products (`docs/engineering/xcom/t020/`):

- `requirements.md`, `architecture.md`, `detailed-design.md`, `unit-specifications.md`,
  `verification-plan.md`, `implementation.md`
- `internal-review.json` (untracked; written by the separate reviewer, not reviewed here)

Implementation and shared wiring:

- `tests/xcom/activation_plan/t020_support.hpp`
- `tests/xcom/activation_plan/t020_ordering_equivalence_tests.cpp`
- `tests/xcom/activation_plan/t020_malformed_plan_tests.cpp`
- `tests/xcom/activation_plan/t020_drift_tests.cpp`
- `tests/xcom/activation_plan/t020_bound_matrix_tests.cpp`
- `tests/xcom/activation_plan/t020_regression_tests.cpp`
- `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py`
- `src/xverse/xcom/CMakeLists.txt` (shared; only the T020 `foreach` block adding the five
  `t020`-labelled targets)
- `specs/007-xcom-core/tasks.md` (shared; T020 checkbox line only)

## Engineering project and traceability records (this stage)

- `engineering/project.json` — project `xverse-platform`, engineered assurance profile,
  accepted baseline `1e289bfe6234553df94eb25065371f7d423fad88`, explicit-argv verification profile matching the trusted policy.
- `engineering/requirements/` — 5 stakeholder, 6 X-Verse system, 7 feature software requirements.
- `engineering/architecture/components/` — 5 components (`T020-CMP-001..005`), one per unit.
- `engineering/unit-specifications/` — 5 unit specifications (`T020-U-01..05`) with 52 actual
  CTest unit cases and static checks per unit.
- `engineering/verification/measures/` — `unit`, `integration`, `validation`, `static_analysis`.
- `engineering/validation/scenarios/` — 5 intended-use scenarios (`T020-VS-01..05`).
- `engineering/trace/links.json` — requirement/design/code/test/evidence trace links.
- `engineering/stage-results/` — `requirements`, `architecture`, `verification-design`,
  `implementation`, `integration`, `validation`, `documentation` stage results. The separate
  reviewer adds `internal_review.json`.

## Closure of the prior findings

- `T020-IR-003` (major, out-of-scope T025 change): the rev-4 candidate leaves
  `xcom_observation_disabled_benchmark` at its baseline registration
  (`PROPERTIES LABELS "performance;observation"`). `git diff 1e289bfe6234553df94eb25065371f7d423fad88 -- src/xverse/xcom/CMakeLists.txt`
  contains only the T020 `foreach` block, and `ctest --show-only=json-v1` reports no `RUN_SERIAL`
  property for that test.
- `T020-IR-004` (low, stale scope statements): the T020 work products now state that the T019/T025
  wiring is unchanged and the `xcom_observation_disabled_benchmark` registration is unchanged,
  consistent with the diff.

## Verification state and open limitations

- Trusted measures (`engineering-checks verify --measure unit|integration|validation|static_analysis`)
  and the delivery matrix are executed by the workflow gates after this stage; this index does not
  claim they passed. Provisional test-ID discovery was taken from the local `build/fabro-t020`
  (52 `t020` CTest cases / 246 total) and `pytest --collect-only` (136 collected).
- **L-A1 (admitted offline inputs).** `run_xcom_system_tests.py` performs a fresh CMake configure
  for the unit and integration measures and requires `XVERSE_XCOM_TOOLCHAIN`,
  `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` (or an equivalent admitted
  CMake cache seed). If the gate process environment does not carry them, the configure fails in
  `xverse_xcom_admit_offline_dependencies` before any T020 suite builds. This is an external
  environment prerequisite (A-1), not a T020 defect. The candidate unit-measure build directory
  `build/fabro-t020-system-unit` was seeded once with those admitted inputs as CMake cache values
  (the documented A-1 resolution; `build/` is git-ignored and not a candidate artifact), so the
  trusted unit measure's fresh configure reuses the admitted cache. The whole-system integration
  measure's build directory is recreated after the assembly clean and therefore still requires the
  gate process environment to provide the inputs.
- **Local discovery exercise (not trusted evidence).** The trusted unit and validation measure
  commands were exercised locally in the candidate checkout only to enumerate and confirm the exact
  discovered test IDs (52 `t020` CTest cases, `136 passed` pytest). This is not the trusted measure
  and no trusted evidence record is claimed.
- **L-A2 (pre-existing T025 timing benchmark).** The full-suite integration measure runs the whole
  CTest suite, which includes the pre-existing `xcom_observation_disabled_benchmark`
  (`performance;observation`, owned by T025). That test is host-timing sensitive and can fail
  intermittently; it is not a T020 artifact and is not modified by this candidate. Any remedy
  belongs in a separate T025 successor candidate.
- **L-A3 (candidate-local vs integration).** The unit and validation measures run in the candidate
  checkout and are candidate-local; only the trusted policy integration measure (assembled pinned
  X-Verse checkout) is whole-system integration. This index does not report candidate-local checks
  as integration.
- **L-A4 (no runtime claim).** The suites prove the derived-plan chain's equivalence, fail-closed
  rejection, drift resistance, bounds, and regression only; they bind nothing and emit no
  communication item. No activation, transport, compatibility, or production-readiness claim is made.
- **L-A5 (deferred external review).** External Codex review and explicit user acceptance remain
  pending; the reported DeepSeek stage model is `deepseek-v4-flash` as pinned by the workflow.

---

# T030 review index — versioned external-tool contract candidate

Candidate: T030 on baseline `80c236638e160c5e991e5a537e29d407e7462dc6` (accepted T026–T029 merge), queue
`xcom-t030-t034-20260928`. The T020 index above is retained as historical predecessor evidence and is not rewritten.

This candidate was implemented on the baseline and locally verified in the offline admitted build. External Codex
acceptance, the trusted target-repository integration measure, and the delivery package are separate gates; none is
claimed complete by this index, and external review and acceptance are deferred until the ordered backlog
`xcom-t030-t034-20260928` completes. A separate internal DeepSeek review is recorded in
`docs/engineering/xcom/t030/internal-review.json`.

## Declared T030 change set (implementation stage)

Contract and generated artifacts:

- `proto/xverse/xcom/v1/tool_gateway.proto` — the single versioned external-tool contract (`XCOM-XLC-002`,
  `XCOM-DU-019`).
- `src/xverse/xcom/CMakeLists.txt` (shared) — additive `protoc`/`grpc_cpp_plugin` generation, the
  `xverse_xcom_tool_gateway_proto` generated-message library (one declared `XVERSE_XCOM_RUNTIME_TARGETS` addition),
  and four additive `t030-<kind>` test targets; no existing target, label, command, or value changes.

Tests:

- `tests/xcom/tool_gateway/contract_support.hpp` — bounded test-local descriptor helpers and the pinned field manifest.
- `tests/xcom/tool_gateway/contract_tests.cpp` — `T30-TS-001`…`T30-TS-011`.
- `tests/xcom/tool_gateway/evolution_tests.cpp` — `T30-TS-012`…`T30-TS-016`.
- `tests/xcom/tool_gateway/negative_tests.cpp` — `T30-TS-017`…`T30-TS-021`.
- `tests/xcom/tool_gateway/provenance_tests.cpp` — `T30-TS-022`…`T30-TS-024`.

Work products and records:

- `docs/engineering/xcom/t030/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`.
- `docs/engineering/xcom/t030/internal-review.json` — the separate internal DeepSeek review record.
- `engineering/project.json`, `engineering/requirements/T030-*.json` and the referenced system anchors,
  `engineering/architecture/components/T030-SR-*-CMP.json`, `engineering/unit-specifications/T030-SR-*-U.json`,
  `engineering/validation/scenarios/T030-VS-ACCUMULATED.json`, `engineering/trace/links.json`.
- `engineering/verification/measures/{unit,integration,validation}.json` — refreshed to the 24 discovered T030 cases and
  the admitted measure commands.
- `engineering/stage-results/*.json` inherited `links.json`/`CMakeLists.txt` provenance-digest refresh.
- `docs/engineering/xcom/t009/architecture-model.{json,md}` and `docs/engineering/xcom/t010/unit-design.{json,md}` —
  required planned→established path-status reconciliation for the six now-present T030 paths (status field only).
- `specs/007-xcom-core/tasks.md` (shared; T030 checkbox line only, implementation stage).
- `reports/xcom-queue/t030-package.json` (implementation stage).

## Observed implementation result

- `proto/xverse/xcom/v1/tool_gateway.proto` SHA-256 `cbb65f901b8522120da6333c4e569d4d8fa00db601abd7effaf70abe925dbb2d`;
  generated `tool_gateway.pb.h`/`.pb.cc` and provenance-only `tool_gateway.grpc.pb.h`/`.grpc.pb.cc` recorded in
  `docs/engineering/xcom/t030/implementation.md` §5.
- Offline build and CTest: `ctest -N -L t030-` discovered 24 cases; `ctest -L t030-` reported
  `100% tests passed, 0 tests failed out of 24`; the preserved subset `ctest -L "t0(2[6-9]|3[0-4])-"` reported
  `100% tests passed, 0 tests failed out of 123`; the full suite reported `100% tests passed, 0 tests failed out of 429`.
- The generated gRPC stubs are not compiled or linked; the admitted envelope lacks the gRPC runtime transitive
  libraries (`T030-GAP-02`).

## Verification state and open limitations

- Trusted measures and the delivery matrix are executed by the workflow gates after implementation; this index does
  not claim they passed.
- **L-T030-1 (admitted offline inputs).** The Phase 7 runner requires `XVERSE_XCOM_TOOLCHAIN`,
  `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` (or the documented A-1 cache seed). If the gate
  process environment does not carry them, the configure fails closed in `xverse_xcom_admit_offline_dependencies`
  before any T030 target builds. This is an external environment prerequisite, not a T030 defect.
- **L-T030-2 (gRPC runtime out of envelope).** The admitted prefix provides the gRPC generation tools but not the gRPC
  runtime transitive libraries; T030 generates the gRPC stubs for provenance and does not link them (`T030-GAP-02`).
  Completing the runtime envelope is T031's recorded decision.
- **L-T030-3 (contract-only).** The suites prove the contract at the descriptor and generated-source level; they
  establish no deployed-service, transport, IPC, compatibility, or production-readiness claim. The separate-process
  proof (`SC-011`) is T032.
- **L-T030-4 (deferred external review).** External Codex review and explicit user acceptance remain pending; the
  reported DeepSeek stage model is `deepseek-v4-flash` as pinned by the workflow.

## Repair closure — whole-system integration trace (successor candidate)

Strict delivery over the successor candidate reported seven T030 software requirements without a
whole-system integration test and integration test ID (`T030-SR-011`, `-014`, `-015`, `-017`, `-018`,
`-019`, `-020`). The cause was seven missing `verified_by -> integration` trace edges, not missing
executed coverage: the other thirteen T030 software requirements already carried that edge, and the
whole-system integration measure (`run_xcom_phase7_tests.py integration`) already assembled the pinned
target checkout, built the complete platform, and passed `100%` of its tests.

The repair adds exactly seven additive trace links in `engineering/trace/links.json` —
`T030-L-0251`…`T030-L-0257` — each pointing at the trusted whole-system integration measure whose
declared `test_ids` are the twenty-four executed `t030-` cases. The exact requirement-to-case mapping
is recorded in `docs/engineering/xcom/t030/implementation.md` §13 and
`docs/engineering/xcom/t030/verification-plan.md` §8.1. No requirement text, acceptance criterion,
contract, production source, test, verification measure, or `test_ids` list changed; the inherited
Phase 6 (`T026`–`T029`) integration and conformance trace links are untouched. The `implemented_by`
endpoint digest for this record's target links (`T030-L-0228`/`T030-L-0229`) and the inherited
`links.json`/`review-index.md` stage-result digests are refreshed in the same change. A fresh separate
DeepSeek internal review and the trusted measures (unit, static analysis, whole-system integration,
validation, and inherited conformance) re-run on the repaired candidate; external Codex acceptance
remains separate.

---

# T031 review index — bounded local-IPC-only gateway candidate

Candidate: T031 on baseline `4dded2317f895978cce0331ae88e34ac28b3a609` (accepted T030 versioned contract), queue
`xcom-t030-t034-20260928`. The T020 and T030 indexes above are retained as historical predecessor evidence and are
not rewritten.

This section records the T031 **plan-stage** work products. The implementation, its local verification, and the
separate internal DeepSeek review are produced by their own stages. External Codex acceptance, the trusted
target-repository integration measure, and the delivery package are separate gates; none is claimed complete by this
index, and external review and acceptance are deferred until the ordered backlog `xcom-t030-t034-20260928` completes.

## Declared T031 plan-stage work products

- `docs/engineering/xcom/t031/requirements.md` — 5 stakeholder and 21 software requirements (`T031-STK-001`…`-005`,
  `T031-SR-001`…`-021`) with accepted system anchors, the recorded gRPC-runtime-envelope decision (`T031-SR-021`),
  and the REF-002 disposition (`unchanged`, empty `promoted`).
- `docs/engineering/xcom/t031/architecture.md` — trust boundaries `T31-XB-1`…`-010`, components
  `T31-CMP-{CONFIG,SESSION,OPS,IPC,LOG,TESTS,BUILD,WP}`, and the negative-case map.
- `docs/engineering/xcom/t031/detailed-design.md` — the gateway interface, the ten-operation mapping onto the
  accepted T025–T029 and T021–T024 boundaries, the bounded method-name-addressed local-IPC framing, the
  deadline/flow-control/cleanup design, and the six test suites.
- `docs/engineering/xcom/t031/unit-specifications.md` — 21 unit specifications and the 24-case index
  (`T31-TS-001`…`T31-TS-024`).
- `docs/engineering/xcom/t031/verification-plan.md` — `CHK-01`…`CHK-22`, `NEG-01`…`NEG-10`, evidence retention,
  exit criteria, and the T-CORE slice evidence mapping.

## Declared T031 engineering records (plan stage)

- `engineering/project.json` — project `xverse-platform`, task `T031`, capability `007`, accepted baseline
  `4dded2317f895978cce0331ae88e34ac28b3a609`.
- `engineering/requirements/T031-STK-00{1..5}.json` and `engineering/requirements/T031-SR-0{01..21}.json`.
- `engineering/architecture/components/T031-SR-0{01..21}-CMP.json`.
- `engineering/unit-specifications/T031-SR-0{01..21}-U.json`.
- `engineering/validation/scenarios/T031-VS-ACCUMULATED.json` — 24 `t031-` cases validating `T031-SR-001`…`-021`.

## Declared T031 implementation change set (expected at the implementation stage)

- `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` (new) and `src/xverse/xcom/src/tool_gateway.cpp` (new) —
  the bounded local-IPC-only gateway session (`XCOM-DU-020`, `XCOM-CMP-010`).
- `src/xverse/xcom/CMakeLists.txt` (shared) — additive `xverse_xcom_tool_gateway` runtime library (one declared
  `XVERSE_XCOM_RUNTIME_TARGETS` addition) and six additive `t031-<kind>` test targets; no existing target, label,
  command, or value changes.
- `tests/xcom/tool_gateway/gateway_support.hpp` and the six `gateway_<kind>_tests.cpp` suites.
- `docs/engineering/xcom/t009/architecture-model.{json,md}` and `docs/engineering/xcom/t010/unit-design.{json,md}` —
  required planned→established path-status reconciliation for the now-present `tool_gateway.hpp`/`.cpp` paths
  (status field only).
- `engineering/trace/links.json`, `engineering/verification/measures/*.json`, and inherited
  `engineering/stage-results/*.json` digest refresh; `engineering/project.json` current-task pointer; the T031
  checkbox line in `specs/007-xcom-core/tasks.md`; `reports/xcom-queue/t031-package.json`;
  `docs/engineering/xcom/t031/{implementation.md,internal-review.json}`.

## Verification state and open limitations

- Trusted measures and the delivery matrix are executed by the workflow gates after implementation; this index does
  not claim they passed.
- **L-T031-1 (admitted offline inputs).** The Phase 7 runner requires `XVERSE_XCOM_TOOLCHAIN`,
  `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` (or the documented A-1 cache seed). If the
  gate process environment does not carry them, the configure fails closed before any T031 target builds. This is an
  external environment prerequisite, not a T031 defect.
- **L-T031-2 (gRPC runtime out of envelope).** The admitted prefix provides the gRPC generation tools but not the
  gRPC runtime transitive libraries; T031 records the delegated decision (`T031-GAP-01`) and realizes the accepted
  message/method contract over bounded host-protected `AF_UNIX` local-IPC framing. No new dependency is added and no
  gRPC-runtime link is claimed.
- **L-T031-3 (gateway-side proof only).** T031 proves the gateway-side absence of a TCP listener; the
  separate-process client and the end-to-end `SC-011` demonstration are T032.
- **L-T031-4 (deferred external review).** External Codex review and explicit user acceptance remain pending; the
  reported DeepSeek stage model is `deepseek-v4-flash` as pinned by the workflow.

## T031 implementation-stage record (candidate)

The implementation stage realized the plan in the working tree on the same baseline. The bounded
local-IPC-only gateway is authored in `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` and
`src/xverse/xcom/src/tool_gateway.cpp`; `src/xverse/xcom/CMakeLists.txt` adds one runtime-target
(`xverse_xcom_tool_gateway`) and six additive `t031-<kind>` suites
(`tests/xcom/tool_gateway/gateway_{session,bounds,lifecycle,local_ipc,negative,logging}_tests.cpp` plus
`gateway_support.hpp`). The T009/T010 planned→established path-status reconciliation was applied.
`docs/engineering/xcom/t031/implementation.md` records the change set, generated-code provenance
(digests equal the accepted T030 record byte-for-byte), the executed commands and observed results, the
requirement-to-case table, maintenance notes, and limitations.

Local verification observed `ctest -N -L t031-` = `Total Tests: 24` and `ctest -L t031-` =
`100% tests passed, 0 tests failed out of 24`; the T007–T010 register validators pass; and
`git diff --check` is clean. The separate internal DeepSeek review, recorded in
`docs/engineering/xcom/t031/internal-review.json`, reports verdict `pass` with no blocking findings.
`reports/xcom-queue/t031-package.json` carries the per-file SHA-256 package record with
`external_review: deferred_until_backlog_completion`. The trusted target-repository assembly-based
integration measure, external Codex review, and explicit user acceptance run separately by the workflow
gates and are not claimed by this index.

## T031 repair-stage record (successor)

The reviewed predecessor candidate (run `01M3MYT7KWWX3MJXTTDS4FJG48`, reviewed candidate commit
`e7817beba8a9b4f6cd1aa7d49307e4b8034195e4`) passed implementation verification, the independent internal
review, the review gate, packaging, and candidate sealing, but the trusted unit gate then failed before
running the test command with `unit specification: missing unit_cases`. The trusted engineering inventory
treats an empty `unit_cases` list as absent, so the three governance/build unit records
`T031-SR-017-U`, `T031-SR-019-U`, and `T031-SR-020-U` failed closed.

This successor repair keeps the original reviewed candidate as its seed and changes only the three
records plus their disclosure and the dependent digest refresh: each of the three records now declares one
contributory unit case that reuses an already-discovered `t031-` GoogleTest case, with its `expected` text
stating the case contributes behavioural context only and the requirement is checked by its named
inspection (the accepted T030 mechanism). No unit case ID is new, so the declared T031 discovery still
equals the 24 executed `t031-` cases; the gateway, its tests, the accepted requirements, the trace
identity, and the original review are unchanged. `docs/engineering/xcom/t031/unit-specifications.md`
discloses the three contributory cases, and `docs/engineering/xcom/t031/implementation.md` §13 records the
closure with fresh, current evidence. The original internal review is preserved as historical evidence; a
fresh independent DeepSeek review and the trusted measures cover this successor, and T039/T041 acceptance
remains separate.

# T032 review index — separate-process synthetic client and generated-client contract tests candidate

Candidate: T032 on baseline `e6197c67868213ffb6523d8bf62ed4c2c4e3b0af` (accepted T031 bounded local-IPC-only gateway),
queue `xcom-t030-t034-20260928`. The T020, T030, and T031 indexes above are retained as historical predecessor
evidence and are not rewritten.

This section records the T032 **plan-stage** work products. The implementation, its local verification, and the
separate internal DeepSeek review are produced by their own stages. External Codex acceptance, the trusted
target-repository integration measure, and the delivery package are separate gates; none is claimed complete by this
index, and external review and acceptance are deferred until the ordered backlog `xcom-t030-t034-20260928` completes.

## Declared T032 plan-stage work products

- `docs/engineering/xcom/t032/requirements.md` — 5 stakeholder and 21 software requirements (`T032-STK-001`…`-005`,
  `T032-SR-001`…`-021`) with accepted system anchors, the recorded gRPC-runtime-envelope decision (`T032-SR-017`),
  and the REF-002 disposition (`unchanged`, empty `promoted`).
- `docs/engineering/xcom/t032/architecture.md` — trust boundaries `T32-XB-1`…`-010`, components
  `T32-CMP-{CLIENT,TRANSPORT,SERVER,LAUNCH,TESTS,BUILD,WP}`, and the negative-case map.
- `docs/engineering/xcom/t032/detailed-design.md` — the synthetic-client interface, the exercise mapping onto the
  accepted T030 generated messages and T031 gateway, the bounded method-name-addressed local-IPC framing reuse, the
  separate-process launch, the bounds/deadline/failure design, and the five test suites.
- `docs/engineering/xcom/t032/unit-specifications.md` — 21 unit specifications and the 22-case index
  (`T32-TS-001`…`T32-TS-022`).
- `docs/engineering/xcom/t032/verification-plan.md` — `CHK-01`…`CHK-22`, `NEG-01`…`NEG-10`, evidence retention,
  exit criteria, and the T-CORE slice evidence mapping.

## Declared T032 engineering records (plan stage)

- `engineering/project.json` — project `xverse-platform`, task `T032`, capability `007`, accepted baseline
  `e6197c67868213ffb6523d8bf62ed4c2c4e3b0af`.
- `engineering/requirements/T032-STK-00{1..5}.json` and `engineering/requirements/T032-SR-0{01..21}.json`.
- `engineering/architecture/components/T032-SR-0{01..21}-CMP.json`.
- `engineering/unit-specifications/T032-SR-0{01..21}-U.json`.
- `engineering/validation/scenarios/T032-VS-ACCUMULATED.json` — 22 `t032-` cases validating `T032-SR-001`…`-021`.

## Declared T032 implementation change set (expected at the implementation stage)

- `src/xverse/xcom/fixtures/synthetic_tool.cpp` (new) — the separate-process synthetic tool client
  (`xverse_xcom_synthetic_client`, `XCOM-DU-021`, `XCOM-CMP-011`).
- `src/xverse/xcom/CMakeLists.txt` (shared) — additive `xverse_xcom_synthetic_client` fixture executable and five
  additive `t032-<kind>` test targets; the runtime-target inventory is unchanged and no existing target, label,
  command, or value changes.
- `tests/xcom/tool_gateway/synthetic_client_support.hpp` and the five
  `synthetic_client_{observation,stimulation,contract,negative,bounds}_tests.cpp` suites.
- `docs/engineering/xcom/t009/architecture-model.{json,md}` and
  `docs/engineering/xcom/t010/{unit-design.json,design-units.md}` —
  required planned→established path-status reconciliation for the now-present
  `src/xverse/xcom/fixtures/synthetic_tool.cpp` path (status field only).
- `engineering/trace/links.json`, `engineering/verification/measures/*.json`, and inherited
  `engineering/stage-results/*.json` digest refresh; `engineering/project.json` current-task pointer; the T032
  checkbox line in `specs/007-xcom-core/tasks.md`; `reports/xcom-queue/t032-package.json`;
  `docs/engineering/xcom/t032/{implementation.md,internal-review.json}`.

## Verification state and open limitations

- Trusted measures and the delivery matrix are executed by the workflow gates after implementation; this index does
  not claim they passed.
- **L-T032-1 (admitted offline inputs).** The Phase 7 runner requires `XVERSE_XCOM_TOOLCHAIN`,
  `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` (or the documented A-1 cache seed). If the
  gate process environment does not carry them, the configure fails closed before any T032 target builds. This is an
  external environment prerequisite, not a T032 defect.
- **L-T032-2 (gRPC runtime out of envelope).** The admitted prefix provides the gRPC generation tools but not the
  gRPC runtime transitive libraries; T032 records its own decision (`T032-GAP-01`) and realizes the accepted generated
  message/method contract over the accepted bounded host-protected `AF_UNIX` framing. No new dependency is added and
  no gRPC-runtime link is claimed.
- **L-T032-3 (owned separate-process proof only).** T032 proves conformance with an owned, self-built separate-process
  synthetic client over an owned local endpoint; it makes no remote-tool or third-party-client compatibility claim.
- **L-T032-4 (deferred external review).** External Codex review and explicit user acceptance remain pending; the
  reported DeepSeek stage model is `deepseek-v4-flash` as pinned by the workflow.

The implementation-stage record, its local verification, and the separate internal DeepSeek review follow in their own
stages and are not claimed by this plan-stage section.

## T032 implementation-stage candidate (separate-process synthetic client)

### Candidate identity

- Task `T032` (capability `007`, slice `T-CORE`/GW) on accepted baseline
  `e6197c67868213ffb6523d8bf62ed4c2c4e3b0af`; pinned stage model `deepseek-v4-flash`.
- The candidate implements the accepted `XCOM-DU-021` separate-process synthetic tool client
  (`src/xverse/xcom/fixtures/synthetic_tool.cpp`, executable `xverse_xcom_synthetic_client`) and its five
  additive `t032-<kind>` generated-client contract suites, over the accepted T030 generated message/method
  contract and the accepted T031 host-protected `AF_UNIX` local-IPC gateway.

### Implementation change set

- `src/xverse/xcom/fixtures/synthetic_tool.cpp` (new) — the bounded separate-process client.
- `src/xverse/xcom/CMakeLists.txt` (additive) — the fixture executable and five `t032-<kind>` test targets; the
  runtime-target inventory is unchanged and no existing target, label, command, or value changes.
- `tests/xcom/tool_gateway/synthetic_client_support.hpp` and the five
  `synthetic_client_{observation,stimulation,contract,negative,bounds}_tests.cpp` suites (22 cases,
  `T32-TS-001`…`T32-TS-022`).
- `docs/engineering/xcom/t009/architecture-model.json`, `docs/engineering/xcom/t010/unit-design.json`, and
  `docs/engineering/xcom/t010/design-units.md` — planned→established path status only for
  `src/xverse/xcom/fixtures/synthetic_tool.cpp`.
- T032 engineering requirement/component/unit/validation records (plan stage), `engineering/trace/links.json`,
  `engineering/verification/measures/{unit,integration,validation}.json`, inherited
  `engineering/stage-results/*.json` digest refresh, `engineering/project.json`, the T032 checkbox line in
  `specs/007-xcom-core/tasks.md`, and `docs/engineering/xcom/t032/implementation.md`.

### Local verification (candidate working tree)

- `ctest -L t032-` — `100% tests passed, 0 tests failed out of 22` (5 observation, 5 stimulation, 4 contract,
  5 negative, 3 bounds).
- `ctest -L "t0(20|2[6-9]|3[0-4])-"` — `100% tests passed, 0 tests failed out of 221`; full discovery `475`.
- `ctest -R xcom_build_contract` — `100% tests passed, 0 tests failed out of 1`.
- T007–T010 register validators pass; `git diff --check` is clean.

### Review state

A separate read-only DeepSeek internal review covers every tracked and untracked candidate file and is recorded
in `docs/engineering/xcom/t032/internal-review.json`. External Codex review and explicit user acceptance remain
T039/T041 and are deferred until the ordered backlog `xcom-t030-t034-20260928` completes; no acceptance or
integration is claimed by this index.

## T032 trace-repair-stage record (successor)

The reviewed predecessor candidate (checkpoint commit `9c5f6d2837562a2bbcb1bbcd375ee1385c198970`, baseline
`e6197c67868213ffb6523d8bf62ed4c2c4e3b0af`) passed scope, checkpoint, unit, static-analysis, target-repository
integration, validation, and inherited Phase 6 conformance, and its separate DeepSeek review recorded a passing
verdict. Strict delivery then found exactly five incomplete stakeholder trace rows: `T032-STK-001` through
`T032-STK-005` each lacked a refining software requirement and an executed validation scenario in
`traceability-matrix.json`.

This successor keeps the reviewed candidate as its seed and adds only the missing `refines` links in
`engineering/trace/links.json` (`T032-L-0258`…`T032-L-0281`, 24 links), disclosed with their statement-level
justification in `docs/engineering/xcom/t032/requirements.md` §5.1 and closed with exact evidence in
`docs/engineering/xcom/t032/implementation.md` §13. The successor also refreshes the four `implemented_by`
endpoint digests that pin `requirements.md` and `implementation.md`. The resulting `engineering/trace/links.json`
carries 1928 links and SHA-256
`66a1b17c9c63427e098bdc281a8b3323e86f11f405a8b000ea72ba73d27aac83`; `validate_trace` passes. Every T032 software
requirement now refines the stakeholder requirement whose statement it actually satisfies, so each stakeholder row
inherits `T032-VS-ACCUMULATED` — whose 22 cases are exactly those selected and executed by the trusted validation
measure — plus its refining software requirements. No requirement, component, unit, validation case, test, measure,
register, or accepted predecessor byte changes; no trace checker is weakened. The original internal review is
preserved as historical evidence; a fresh independent DeepSeek review and every trusted measure cover this successor,
and T039/T041 acceptance remains separate.

## T033 reusable contract-suite candidate

- Task `T033` (capability `007`, slice `T-CORE`/GW) on accepted baseline
  `2fd395e39e44e1f6fe9547998b47499d996b1756`; pinned stage model `deepseek-v4-flash`.
- The candidate implements the reusable provider, observer, stimulation-tool, and gateway contract suites as
  four implementation-agnostic drivers behind narrow subject seams, instantiated against the accepted T016
  loopback/probe providers, T024 observation hub, T029 stimulation composition, and T031 gateway fixture.

### Implementation change set

- `tests/xcom/contract_suites/suite_support.hpp` (new) — the bounded `SuiteReport`/`SuiteCheck` vocabulary.
- `tests/xcom/contract_suites/{provider,observer,stimulation_tool,gateway}_contract_suite.hpp` (new) — the four
  reusable suites and their `*Subject` seams; each names only accepted interfaces and accepted fixture helpers.
- `tests/xcom/contract_suites/{provider,observer,stimulation_tool,gateway}_suite_tests.cpp` (new) — the four
  additive drivers (eight cases).
- `src/xverse/xcom/CMakeLists.txt` (additive) — four `t033-<kind>` test targets; the runtime-target inventory is
  unchanged and no existing target, label, command, or value changes.
- T033 engineering requirement/component/unit/validation records, `engineering/trace/links.json` (198 additive
  links plus the nine repair-pass `implemented_by` links `T033-L-0199`…`T033-L-0207`; inherited
  `src/xverse/xcom/CMakeLists.txt` digest refreshed), `engineering/verification/measures/`
  refreshed to the eight T033 cases, inherited `engineering/stage-results/*.json` digest refresh,
  `engineering/project.json`, the T033 checkbox line in `specs/007-xcom-core/tasks.md`, and
  `docs/engineering/xcom/t033/{implementation,requirements,verification-plan}.md`.

### Repair pass (REV-T033-001, REV-T033-002)

The first read-only DeepSeek internal review recorded `verdict: fail` with two annotation-only findings: an off-by-one
`@par Traceability` requirement-range shift across the four reusable suite headers and four drivers
(`REV-T033-001`), and bare SESN-era observation plus undefined stimulation requirement anchors
(`REV-T033-002`). The successor corrects every range to the authoritative `engineering/requirements/T033-SR-*.json`
mapping, replaces the anchors with their accepted `docs/engineering/xcom/t008/requirements-register.json` ids, adds the
nine driver `implemented_by` links that make each cited range a subset of the ids linked to its file, and drops the
unused `XCOM_T033_SUITE_HEADER_ROOT` compile definition. The change is annotation-only: `ctest -L t033-` still reports
8/8, `validate_trace` passes at 605 artifacts and 2135 links, the T007–T010 register validators pass, and the
deterministic gate passes. A fresh independent DeepSeek review and repeated affected verification remain required.


### Repair pass 2 (REV-T033-003, REV-T033-004, REV-T033-005, REV-T033-006)

The second read-only DeepSeek internal review of the REV-T033-001/-002 successor recorded `verdict: fail` with four
low documentation-consistency findings and no executed-behaviour finding. The successor corrects a truncated
context-diagram label in `architecture.md` §3.1 (`lo`→`loopback`), the `reports/review-index.md` full-discovery count
(`476`→`483`, the reproducible `ctest -N` value), the `requirements.md` §4.3 `T033-SR-007` verification intent
(`S-01`…`S-03`, `S-05` → the action-emission set `S-01`, `S-02-0`…`S-02-3`, `S-05`, so `S-03` is owned only by
`T033-SR-008`), and the `unit-specifications.md` `T033-SR-009-U` inputs (the `gateway_operation_names()` operation
table plus the generated `ProtocolVersion`/`QueryVersionRequest`/`QueryVersionResponse` messages actually consumed by
`G-02`…`G-04`, replacing the unconsumed "generated descriptor method set"). The change is documentation-only: no
requirement, check, expected value, test, target, label, or measure changes; `ctest -L t033-` still reports 8/8; the
refreshed `implemented_by` pins `T033-L-0189`…`T033-L-0192` and the inherited `engineering/trace/links.json` plus
`reports/review-index.md` stage artifact digests match the current bytes. A fresh independent DeepSeek review and
repeated affected verification remain required. The closure is recorded in `implementation.md` §14 and
`verification-plan.md` §10.


### Local verification (candidate working tree)

- `ctest -L t033-` — `100% tests passed, 0 tests failed out of 8` (2 provider, 2 observer, 2 stimulation-tool,
  2 gateway).
- `ctest -L "t0(20|2[6-9]|3[0-4])-"` — `100% tests passed, 0 tests failed out of 229`; full discovery `483`.
- T007–T010 register validators pass; `git diff --check` is clean.

### Review state

A separate read-only DeepSeek internal review covers every tracked and untracked candidate file and is recorded
in `docs/engineering/xcom/t033/internal-review.json`. External Codex review and explicit user acceptance remain
T039/T041 and are deferred until the ordered backlog `xcom-t030-t034-20260928` completes; no acceptance or
integration is claimed by this index.

# T034 review index — second minimal synthetic provider and replaceability/version-rejection/failure-isolation candidate

Candidate: T034 on baseline `f63491101aed1c4f7db57fa7c506ad5c0510038f` (accepted T033 reusable contract suites),
queue `xcom-t030-t034-20260928`. The T020, T030, T031, T032, and T033 indexes above are retained as historical
predecessor evidence and are not rewritten.

This section records the T034 **plan-stage** work products. The implementation, its local verification, and the
separate internal DeepSeek review are produced by their own stages. External Codex acceptance, the trusted
target-repository integration measure, and the delivery package are separate gates; none is claimed complete by
this index, and external review and acceptance are deferred until the ordered backlog `xcom-t030-t034-20260928`
completes.

## Declared T034 plan-stage work products

- `docs/engineering/xcom/t034/requirements.md` — 5 stakeholder and 14 software requirements (`T034-STK-001`…`-005`,
  `T034-SR-001`…`-014`) with accepted system anchors, the reused-suite replaceability decision, and the REF-002
  disposition (`unchanged`, empty `promoted`; T035–T041 allocated).
- `docs/engineering/xcom/t034/architecture.md` — trust boundaries `T34-XB-1`…`-008`, components
  `T34-CMP-{PROVIDER,SUITE,VERSION,ISOLATION,BUILD,WP}`, and the negative-case map.
- `docs/engineering/xcom/t034/detailed-design.md` — the `SyntheticProvider` interface and bounded behavior, the
  unchanged T033 `ProviderContractSuite` reuse through a new `ProviderSubject`, the version/capability
  fail-closed gates, the failure-isolation composition, and the three `t034-<kind>` drivers.
- `docs/engineering/xcom/t034/unit-specifications.md` — 14 unit specifications and the thirteen-case index.
- `docs/engineering/xcom/t034/verification-plan.md` — `CHK-01`…`CHK-22`, `NEG-01`…`NEG-08`, evidence retention,
  exit criteria, and the accepted-anchor traceability.

## Declared T034 engineering records (plan stage)

- `engineering/project.json` — project `xverse-platform`, task `T034`, capability `007`, accepted baseline
  `f63491101aed1c4f7db57fa7c506ad5c0510038f`.
- `engineering/requirements/T034-STK-00{1..5}.json` and `engineering/requirements/T034-SR-0{01..14}.json`.
- `engineering/architecture/components/T034-SR-0{01..14}-CMP.json`.
- `engineering/unit-specifications/T034-SR-0{01..14}-U.json`.
- `engineering/validation/scenarios/T034-VS-ACCUMULATED.json` — thirteen `t034-` cases validating
  `T034-SR-001`…`-014`.

## Declared T034 implementation change set (expected at the implementation stage)

- `src/xverse/xcom/fixtures/synthetic_provider.hpp` (new) and `src/xverse/xcom/fixtures/synthetic_provider.cpp`
  (new) — the second minimal synthetic provider (`SyntheticProvider`, `XCOM-DU-007`/`XCOM-DU-008`,
  `XCOM-CMP-006`/`007`/`011`).
- `src/xverse/xcom/CMakeLists.txt` (shared) — the fixture source compiled into three additive `t034-<kind>`
  test targets; no runtime library is added and `XVERSE_XCOM_RUNTIME_TARGETS` is unchanged.
- `tests/xcom/contract_suites/second_provider_suite_tests.cpp` (`t034-replaceability`),
  `second_provider_version_tests.cpp` (`t034-version`), and `second_provider_isolation_tests.cpp`
  (`t034-isolation`) — the thirteen cases, reusing the unchanged T033 `ProviderContractSuite`.
- `engineering/trace/links.json`, `engineering/verification/measures/*.json`, and inherited
  `engineering/stage-results/*.json` digest refresh; `engineering/project.json` current-task pointer; the T034
  checkbox line in `specs/007-xcom-core/tasks.md` (implementation stage only); `reports/xcom-queue/t034-package.json`;
  `docs/engineering/xcom/t034/{implementation.md,internal-review.json}`.

## Verification state and open limitations

- Trusted measures and the delivery matrix are executed by the workflow gates after implementation; this index
  does not claim they passed.
- **L-T034-1 (admitted offline inputs).** The Phase 7 runner requires `XVERSE_XCOM_TOOLCHAIN`,
  `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` (or the documented A-1 cache seed). If the
  gate process environment does not carry them, the configure fails closed before any T034 target builds. This is
  an external environment prerequisite, not a T034 defect.
- **L-T034-2 (owned synthetic providers only).** T034 proves replaceability and failure isolation against owned
  in-process synthetic providers over the accepted composition; it makes no network, transport, third-party
  provider, or legacy-provider compatibility claim.
- **L-T034-3 (bounded isolation model).** The accepted composition owns one provider registry and one active
  route per fixture; isolation is proven for an unrelated route on an independently composed provider and for a
  rejected provider registered into the same composition (`T034-GAP-02`).
- **L-T034-4 (deferred external review).** External Codex review and explicit user acceptance remain pending; the
  reported DeepSeek stage model is `deepseek-v4-flash` as pinned by the workflow.

The implementation-stage record, its local verification, and the separate internal DeepSeek review follow in their
own stages and are not claimed by this plan-stage section.

## T034 implementation-stage verification (candidate working tree)

The implementation stage realized the declared change set exactly. Measured locally on the candidate working tree
in the admitted offline build (`build/fabro-t030-t034-system-unit`); the trusted measures and the strict
target-repository integration gate remain separate and are not claimed here:

- `ctest -L t034-` — `100% tests passed, 0 tests failed out of 13` (4 `t034-replaceability`, 5 `t034-version`,
  4 `t034-isolation`); `ctest -N -L t034-` reports `Total Tests: 13`.
- `ctest -L 't0(20|2[6-9]|3[0-4])-'` — `100% tests passed, 0 tests failed out of 242` (the preserved inherited
  suites plus the thirteen `t034-` cases); full discovery `ctest -N` reports `Total Tests: 496`.
- `python3 -m pytest -q` — `150 passed, 24 subtests passed`.
- `git diff --check f63491101aed1c4f7db57fa7c506ad5c0510038f --` — clean.
- Trace validation (`fabro_engineering.core.validate_trace`, project `xverse-platform`) — passes with 653
  artifacts and 2329 links; every accepted `T034-SR-0{01..14}` carries `allocated_to`, `implemented_by`, and
  `verified_by`, and every unit carries `decomposes_to`, `implemented_by`, `verified_by`, and `analyzed_by`.

The T034-owned artifacts and inherited build/links digests are recorded in `docs/engineering/xcom/t034/implementation.md`
§6.1 and in the package manifest `reports/xcom-queue/t034-package.json` (emitted at package time). This is a
candidate-stage result only; external Codex review, the trusted whole-system integration measure, and explicit user
acceptance await T039/T041 and the completion of the ordered backlog `xcom-t030-t034-20260928`.
