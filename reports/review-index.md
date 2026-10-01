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

# T035 review index — exact-candidate verification matrix and repository-owned results

Candidate: T035 on baseline `dab68568bd8d189b14c7a4a9e3a9c325085a7529` (accepted T034 second synthetic provider),
queue `xcom-t030-t034-20260928`. The T020, T030, T031, T032, T033, and T034 indexes above are retained as
historical predecessor evidence and are not rewritten.

This section records the T035 **plan-stage** work products. The implementation, its executed matrix, and the
separate internal DeepSeek review are produced by their own stages. External Codex acceptance, the trusted
measures, and the delivery package are separate gates; none is claimed complete by this index, and external
review and acceptance are deferred until the ordered backlog `xcom-t030-t034-20260928` completes.

## Declared T035 plan-stage work products

- `docs/engineering/xcom/t035/requirements.md` — 5 stakeholder and 16 software requirements (`T035-STK-001`…`-005`,
  `T035-SR-001`…`-016`) with accepted system anchors, the evidence-only boundary, and the REF-002 disposition
  (`unchanged`, empty `promoted`; T036–T041 allocated).
- `docs/engineering/xcom/t035/architecture.md` — trust boundaries `T35-XB-1`…`-008`, components
  `T35-CMP-{MATRIX,MEASURES,TRACE,WP}`, the ordered data flow, and the negative-case map.
- `docs/engineering/xcom/t035/detailed-design.md` — the exact verification route (`unit`, `integration`,
  `validation`, `static_analysis`, `conformance`, `sanitizer`, `python`), the
  `reports/xcom-queue/t035-verification.json` schema (`commands`, `outcomes`, `hashes`, `environment`, bounded
  logs, exact-candidate identity), the content-only measure refresh, and the already-discovered selected case set.
- `docs/engineering/xcom/t035/unit-specifications.md` — 16 contributory unit specifications and the selected-case
  index.
- `docs/engineering/xcom/t035/verification-plan.md` — `CHK-01`…`CHK-20`, `NEG-01`…`NEG-10`, the exact evidence
  report, the task-owned route, evidence binding, and exit criteria.

## Declared T035 engineering records (plan stage)

- `engineering/project.json` — project `xverse-platform`, task `T035`, capability `007`, accepted baseline
  `dab68568bd8d189b14c7a4a9e3a9c325085a7529`.
- `engineering/requirements/T035-STK-00{1..5}.json` and `engineering/requirements/T035-SR-0{01..16}.json`.
- `engineering/architecture/components/T035-SR-0{01..16}-CMP.json`.
- `engineering/unit-specifications/T035-SR-0{01..16}-U.json`.
- `engineering/validation/scenarios/T035-VS-ACCUMULATED.json` — the selected case set validating
  `T035-SR-001`…`-016` and `T035-STK-001`…`-005`.
- `engineering/verification/measures/{unit,integration,validation,static_analysis}.json` — content-only refresh to
  the Phase 8 route (each `id`, `revision`, and `kind` preserved) — and the new
  `engineering/verification/measures/sanitizer.json`.
- `engineering/trace/links.json` — 223 additive T035 links plus the inherited `engineering/project.json`
  `implemented_by` digest refresh (`T034-L-0168`); the trace validates with 708 artifacts and 2552 links.
- `docs/engineering/xcom/t010/unit-design.json` and `docs/engineering/xcom/t010/design-units.md` — the required
  planned→established path-status reconciliation for the now-present `docs/engineering/xcom/t035/` path
  (`XCOM-DU-024`; status field only); the T007–T010 register validators pass.

## Declared T035 implementation change set (expected at the implementation stage)

- `reports/xcom-queue/t035-verification.json` (new) — the exact-candidate verification evidence report with
  `commands`, `outcomes`, `hashes`, `environment`, bounded logs, and the exact-candidate identity.
- `docs/engineering/xcom/t035/implementation.md` (new) — the executed-matrix record, changed-path inventory,
  environment/tool identities, hashes, maintenance notes, and limitations.
- `specs/007-xcom-core/tasks.md` (shared; the one-line T035 checkbox, **implementation stage only**).
- `reports/xcom-queue/t035-package.json` — the implementation-stage package record.
- T035 changes no accepted production source, header, contract, schema, register, XDL profile, test, target,
  label, command, or expected value.

## Verification state and open limitations

- Trusted measures and the delivery matrix are executed by the workflow gates after implementation; this index
  does not claim they passed.
- **L-T035-1 (admitted offline inputs).** The Phase 8 runner requires `XVERSE_XCOM_TOOLCHAIN`,
  `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN`; the runner binds them to the admitted
  cache paths and otherwise fails closed before any target builds. This is an external environment prerequisite,
  not a T035 defect.
- **L-T035-2 (verification only).** T035 executes and records the accepted matrix; it makes no deployed-service,
  network, transport, timing, compatibility, performance, or production-readiness claim.
- **L-T035-3 (candidate-local vs whole-system).** Only the trusted target-repository integration measure is
  whole-system integration; the unit, static-analysis, sanitizer, and validation runs are candidate-local.
- **L-T035-4 (report is implementation-stage).** This plan stage records the report schema and the exact command
  route; it does not fabricate executed results. An unavailable input is recorded as `blocked`, never as `pass`.
- **L-T035-5 (deferred external review).** External Codex review and explicit user acceptance remain pending; the
  reported DeepSeek stage model is `deepseek-v4-flash` as pinned by the workflow.

The implementation-stage record, its executed evidence, and the separate internal DeepSeek review follow in their
own stages and are not claimed by this plan-stage section.

## T035 implementation-stage results

The T035 verification matrix executed against the exact candidate working tree on baseline
`dab68568bd8d189b14c7a4a9e3a9c325085a7529`; full detail, command argv, exit status, bounded public-safe logs,
hashes, and environment identity are in `reports/xcom-queue/t035-verification.json` and
`docs/engineering/xcom/t035/implementation.md`.

- **unit** — `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py unit`: `100% tests passed, 0
  tests failed out of 496` (candidate checkout).
- **integration** / **validation** — `run_xcom_phase8_tests.py integration|validation`: `100% tests passed, 0
  tests failed out of 496` and pytest `150 passed, 24 subtests passed` (short material-identical checkout;
  candidate-local).
- **sanitizer** — `run_xcom_phase8_tests.py sanitizer`: `100% tests passed, 0 tests failed out of 496` with
  `-fsanitize=address,undefined`.
- **static_analysis** — `cppcheck ... src/xverse/xcom/src`: exit `0`, no diagnostic output.
- **selected case set** — 16/16 named `T035` cases passed.
- **python** — `150 passed, 24 subtests passed`.
- **conformance** — **failed** at the accepted baseline (external, recorded): the pinned Phase 6 governance
  inspection requires `docs/engineering/xcom/t007..t009` unchanged since `1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d`,
  but accepted T030/T031/T032 changed `docs/engineering/xcom/t009/architecture-model.json`. T035 changes no
  protected Phase 6 path (`E-T035-2`, `L-T035-7`).

Recorded external environment issue: the pinned Phase 8 runner's default build directories
(`build/fabro-t035-t038-system-integration|validation|sanitizer`) make the T032 `AF_UNIX` fixture socket path
exceed the 108-byte `sun_path` limit on this host, so the default-root runs fail 14 `XcomSyntheticClient*` cases;
the identical commands from a material-identical short checkout pass all 496 tests (`E-T035-1`, `L-T035-6`). The
accepted Phase 7 runner avoids this with `build/f7i`/`build/f7v`. No accepted production source, test, target,
label, command, or expected value was changed.

This is a candidate-stage result only; the separate DeepSeek internal review, external Codex review, the trusted
whole-system integration measure, and explicit user acceptance await their own stages and the completion of the
ordered backlog `xcom-t030-t034-20260928`.

# T036 review index — controlled disabled/enabled-tap benchmarks and repository-owned results

Candidate: T036 on baseline `8ec69ddd34ed8c7a07adbcb631dcfb2da3faf15f` (reviewed T035 candidate),
queue `xcom-t030-t034-20260928`. The T020, T030, T031, T032, T033, T034, and T035 indexes above are retained
as historical predecessor evidence and are not rewritten.

This section records the T036 **plan-stage** work products. The implementation, its executed benchmark, and the
separate internal DeepSeek review are produced by their own stages. External Codex acceptance, the trusted
measures, and the delivery package are separate gates; none is claimed complete by this index, and external
review and acceptance are deferred until the ordered backlog `xcom-t030-t034-20260928` completes.

## Declared T036 plan-stage work products

- `docs/engineering/xcom/t036/requirements.md` — 5 stakeholder and 12 software requirements (`T036-STK-001`…`-005`,
  `T036-SR-001`…`-012`) with accepted system anchors, the evidence-plus-harness boundary, and the REF-002
  disposition (`unchanged`, empty `promoted`; T037–T041 allocated).
- `docs/engineering/xcom/t036/architecture.md` — trust boundaries `T36-XB-1`…`-007`, components
  `T36-CMP-{HARNESS,REPORT,TRACE,WP}`, the ordered data flow, and the negative-case map.
- `docs/engineering/xcom/t036/detailed-design.md` — the exact benchmark route (`B-1`…`B-4`), the
  `reports/xcom-queue/t036-benchmark.json` schema (`environment`, `uncertainty`, `baseline`, `tap_disabled`,
  `tap_enabled`, `limitations`, raw `samples`, `method`, exact-candidate identity), the fail-closed `--verify`
  contract, and the same-baseline comparison.
- `docs/engineering/xcom/t036/unit-specifications.md` — 12 contributory unit specifications and the selected-case
  index.
- `docs/engineering/xcom/t036/verification-plan.md` — `CHK-01`…`CHK-16`, `NEG-01`…`NEG-10`, the exact evidence
  report, the task-owned harness route, evidence binding, and exit criteria.

## Declared T036 engineering records (plan stage)

- `engineering/project.json` — project `xverse-platform`, task `T036`, capability `007`, accepted baseline
  `8ec69ddd34ed8c7a07adbcb631dcfb2da3faf15f`.
- `engineering/requirements/T036-STK-00{1..5}.json` and `engineering/requirements/T036-SR-0{01..12}.json`.
- `engineering/architecture/components/T036-SR-0{01..12}-CMP.json`.
- `engineering/unit-specifications/T036-SR-0{01..12}-U.json`.
- `engineering/validation/scenarios/T036-VS-ACCUMULATED.json` — the selected case set validating
  `T036-SR-001`…`-012` and `T036-STK-001`…`-005`.
- `engineering/trace/links.json` — 157 additive T036 links plus the inherited `engineering/project.json`
  `implemented_by` digest refresh; the trace validates with 750 artifacts and 2709 links.
- `docs/engineering/xcom/t010/unit-design.json` and `docs/engineering/xcom/t010/design-units.md` — the required
  planned→established path-status reconciliation for the now-present `docs/engineering/xcom/t036/` path
  (`XCOM-DU-024`; status field only).

## Declared T036 implementation change set (expected at the implementation stage)

- `engineering/run_xcom_benchmarks.py` (new) — the task-owned benchmark harness with the fail-closed `--verify`
  mode.
- `reports/xcom-queue/t036-benchmark.json` (new) — the exact-candidate benchmark evidence report with
  `environment`, `uncertainty`, `baseline`, `tap_disabled`, `tap_enabled`, `limitations`, raw samples, method,
  hashes, and the exact-candidate identity.
- `docs/engineering/xcom/t036/implementation.md` (new) — the executed-benchmark record, changed-path inventory,
  environment/tool identities, hashes, maintenance notes, and limitations.
- `specs/007-xcom-core/tasks.md` (shared; the one-line T036 checkbox, **implementation stage only**).
- `reports/xcom-queue/t036-package.json` — the implementation-stage package record.
- T036 changes no accepted production source, header, contract, schema, register, XDL profile, test, target,
  label, command, or expected value; the accepted `xcom_observation_disabled_benchmark` fixture is consumed
  read-only.

## Verification state and open limitations

- Trusted measures and the delivery matrix are executed by the workflow gates after implementation; this index
  does not claim they passed.
- **L-T036-1 (admitted offline inputs).** The harness requires the admitted `XVERSE_XCOM_TOOLCHAIN`,
  `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN`; it otherwise fails closed before any
  target builds. This is an external environment prerequisite, not a T036 defect.
- **L-T036-2 (benchmark only).** T036 records a bounded prototype benchmark; it makes no deployed-service,
  network, transport, timing, compatibility, performance, or production-readiness claim.
- **L-T036-3 (uncertainty is a declaration).** The uncertainty statement records the observed dispersion under an
  uncontrolled shared host; it is not a production confidence interval.
- **L-T036-4 (report/harness are implementation-stage).** This plan stage records the report schema and the exact
  route; it does not fabricate executed results. An unavailable input is recorded as `blocked`, never as `pass`.
- **L-T036-5 (deferred external review).** External Codex review and explicit user acceptance remain pending; the
  reported DeepSeek stage model is `deepseek-v4-flash` as pinned by the workflow.
- **L-T036-6 (SC-008 is the spec anchor, materialized as FR links).** The accepted register’s
  `XCOM-SYS-SC-008` success criterion is the benchmark’s spec anchor; because no `engineering/requirements/`
  record is materialized for it in the accepted baseline, T036 traces its `refines` links to the materialized
  `XCOM-SYS-FR-014`/`FR-030`/`FR-029`/`FR-027`/`FR-035`/`SC-007` anchors and records the SC-008 mapping in
  `requirements.md` §5, consistent with the accepted T035 precedent (T036-OPEN-07).
- **L-T036-7 (delivery-verifier revision).** The trusted `engineering-checks` console script resolves the
  admitted installed `fabro_engineering` revision; against the T036 candidate that verifier validates the trace
  (750 artifacts, 2709 links) and renders a complete 292-row traceability matrix with no gaps. The fabric
  source tree also carries an uncommitted, not-installed helper revision that adds an unrelated
  “stimulation code trace” rule requiring a scoped software requirement to trace to a source path containing
  “stimulation.” T036 is a benchmark task whose measured paths are the observation, provider, and loopback
  sources, so T036 does not fabricate a stimulation `implemented_by` edge. Recorded as an external verifier
  risk for T039/T040; if the installed verifier is updated to that revision, the trace semantics for
  evidence/benchmark tasks must be decided before delivery rather than worked around.

The implementation-stage record, its executed evidence, and the separate internal DeepSeek review follow in
their own stages and are not claimed by this plan-stage section.

## T036 implementation stage — executed controlled benchmark and candidate evidence

This section records the T036 **implementation-stage** artifacts executed against the accepted baseline
`8ec69ddd34ed8c7a07adbcb631dcfb2da3faf15f`. The plan-stage section above is retained as historical
evidence and is not rewritten. The implementation adds the harness, the executed evidence report, the
sixth work product, 7 implementation-stage trace links, the one-line T036 checkbox, and this index section.

### Implemented artifacts

- `engineering/run_xcom_benchmarks.py` (new) — the task-owned controlled benchmark harness. It compiles the
  accepted owned-loopback/observation sources plus a generated measurement driver into an isolated temporary
  build with `-std=c++20 -Wall -Wextra -Wpedantic -Werror -O2`, runs 21 interleaved paired samples of 5000
  submit/receive pairs for three cases (`baseline`, `tap_disabled`, `tap_enabled`), writes the report, and
  provides the failure-closed `--verify` mode. SHA-256
  `684f38132be21bf7d9c610af8e4acd53d0de0e2b5c797c4ca2e82a3428685e3e`.
- `reports/xcom-queue/t036-benchmark.json` (new) — the exact-candidate evidence report carrying
  `environment`, `method`, `uncertainty`, `baseline`, `tap_disabled`, `tap_enabled`, `regression`, raw
  `samples`, `hashes`, `limitations`, and the material binding. SHA-256
  `3b1c2f7a54fe074e918e15355c982227bc5e947a982ffa26d57414cf8440e5bf`; candidate material digest
  `f4c217e0e36ff00383a587fa8dc13e564410313dcad158211511657fae94ff50`.
- `docs/engineering/xcom/t036/implementation.md` (new) — the executed-benchmark record, changed-path
  inventory, environment identity, design realization notes, maintenance notes, and limitations.
- `engineering/trace/links.json` — 7 additive `implemented_by` links from `T036-SR-001/-002/-003/-007/-008/-009/-012`
  to the harness (pinning its SHA-256). The trace now validates with 750 artifacts and 2716 links.
- `specs/007-xcom-core/tasks.md` — the one-line T036 checkbox only.

### Executed results

- `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` → exit `0`.
  Gated `SC-008` comparison (`tap_disabled` versus `baseline`): median latency regression `-5.575%` (`pass`),
  median throughput regression `-5.904%` (`pass`); `regression.outcome = "pass"`.
- Recorded enabled-tap observation (`tap_enabled` versus `tap_disabled`): median latency regression `53.469%`,
  median throughput regression `34.840%`, `within_2_percent = false`, `gated = false`. The report states that
  the accepted `SC-008`/plan performance goal bounds the disabled-tap case; the enabled overhead is recorded
  honestly and no 2% bound is claimed for it (`implementation.md` §2.2, L-T036-5).
- `python3 engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json` → exit `0`.
  Negative probes (missing field, stale revision, empty limitations, changed hash, mismatched digest, wrong
  sample count) each exit nonzero.

### Verification state and open limitations

- The candidate-local harness run and `--verify` pass; the trusted Phase 8 measures and the delivery matrix
  are executed by the workflow gates after implementation, and this index does not claim they passed.
- **L-T036-1 (admitted offline inputs).** The harness requires `XVERSE_XCOM_TOOLCHAIN`,
  `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN`; it otherwise fails closed before any
  build. External environment prerequisite, not a T036 defect.
- **L-T036-2 (benchmark only).** No deployed-service, network, transport, timing, compatibility,
  performance, or production-readiness claim.
- **L-T036-3 (uncertainty is a declaration).** The uncertainty statement records observed dispersion under a
  shared, uncontrolled host; it is not a production confidence interval.
- **L-T036-4 (admitted envelope).** The workload uses the in-process owned loopback and observation boundary
  only (`T032-GAP-01`).
- **L-T036-5 (enabled-tap overhead).** The enabled case adds a measured ~53% median latency overhead; it is
  recorded as an ungated observation, not as an SC-008 failure or pass.
- **L-T036-6 (deferred external review).** External Codex review and explicit user acceptance remain pending.
- **L-T036-7 (delivery-verifier revision)** from the plan-stage section remains an external risk for
  T039/T040; the installed `engineering-checks` verifier validates this candidate trace (750 artifacts,
  2716 links). No stimulation `implemented_by` edge was fabricated for this benchmark task.

## T036 repair stage — internal-review findings closed on the same baseline

The separate read-only internal DeepSeek review recorded `verdict: fail` with four findings
(`T036-IR-01`…`-04`) against the implementation candidate; the `review` gate failed deterministically
because a reviewing record may not retain findings. This repair pass corrects the defects on the same
accepted baseline `8ec69ddd34ed8c7a07adbcb631dcfb2da3faf15f` and re-runs the affected measures. No
required check was weakened, and no benchmark or verification result was invented.

### Findings and corrections

- **T036-IR-01 (MAJOR) — gated comparison misdescribed.** The requirement, design, and architecture
  described the gated 2% comparison as enabled-versus-disabled, contradicting accepted `SC-008`
  (`XCOM-SW-INTG-003`) and the report, which gate `tap_disabled` versus the same owned-loopback baseline
  and record the enabled-versus-disabled regression as an ungated observation. Corrected in
  `requirements.md` (scope item 5 and `T036-SR-003`), `engineering/requirements/T036-SR-003.json`,
  `engineering/architecture/components/T036-SR-003-CMP.json`,
  `engineering/unit-specifications/T036-SR-003-U.json`, `verification-plan.md` (`CHK-04`, `B-1`, §8,
  `NEG-05`), `architecture.md` (boundary `T36-XB-2`, component, data flow, interfaces, `regression`
  field), `detailed-design.md` (schema, failure semantics), `unit-specifications.md`, and
  `engineering/validation/scenarios/T036-VS-ACCUMULATED.json`.
- **T036-IR-02 (MINOR) — p95 advertised but not retained.** `engineering/run_xcom_benchmarks.py` now
  retains the already-computed `p95_latency_ns` in each `uncertainty` block; the report was regenerated and
  the `detailed-design.md` uncertainty schema updated. Every statistic named in `method.statistics` is now
  present in each uncertainty block.
- **T036-IR-03 (MINOR) — outlier misidentified.** `implementation.md` §4 now names the true largest
  disabled regression (sample index 5, `0.352%`), states that no disabled sample exceeds the 2% threshold
  in this executed run, and discloses that the median (`-5.575%`) reflects the disabled case measuring
  slightly faster than the baseline on this shared host.
- **T036-IR-04 (MINOR) — verification intent disagreement.** `T036-SR-006`'s verification intent is now
  identical (`T033ProviderContractSuite.AcceptedLoopbackProviderConforms`) across `requirements.md`,
  `engineering/requirements/T036-SR-006.json`, `unit-specifications.md`, and `implementation.md`; the case
  is listed in `engineering/validation/scenarios/T036-VS-ACCUMULATED.json`.

### Re-run evidence (same baseline)

- `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` → exit `0`;
  `--verify` → exit `0`. Gated `SC-008`: latency `-5.575%`, throughput `-5.904%` (`pass`); enabled-tap
  observation `53.469%` latency / `34.840%` throughput (`gated: false`). Material digest
  `f4c217e0e36ff00383a587fa8dc13e564410313dcad158211511657fae94ff50`; report SHA-256
  `3b1c2f7a54fe074e918e15355c982227bc5e947a982ffa26d57414cf8440e5bf`.
- The 21 `implemented_by` endpoint digests (14 work-product links plus the 7 harness links in
  `engineering/trace/links.json`) were refreshed to the corrected artifacts; the trusted
  `validate_trace` passes with 750 artifacts and 2716 links, and the four T007–T010 register validators
  (`validate_xcom_task_ownership`, `validate_xcom_requirements_traceability`,
  `validate_xcom_architecture_contracts`, `validate_xcom_unit_design`) pass.
- The predecessor indexes (T020, T030–T035) and the T030–T034 behavior are unchanged; the plan-stage
  T036 section above is retained as historical evidence and is not rewritten.

## T036 second repair stage — residual gated-comparison defect and schema/label alignment

A second separate read-only internal DeepSeek review of the first-repair candidate recorded
`verdict: fail` with three findings (`T036-IR-05`…`-07`) on the same accepted baseline
`8ec69ddd34ed8c7a07adbcb631dcfb2da3faf15f`; the `review` gate failed deterministically because a
reviewing record may not retain findings. This repair pass corrects the residual defects and re-runs the
affected measures. No required check was weakened, and no benchmark or verification result was invented;
the evidence report was re-executed from the accepted owned-loopback workload rather than edited.

### Findings and corrections

- **T036-IR-05 (MAJOR) — residual gated-comparison defect in `engineering/project.json`.** The
  `scope.success_criteria[1]` text still described the gated 2% comparison as the enabled regression,
  contradicting accepted `SC-008`/`XCOM-SW-INTG-003` and the corrected T036 work products. It now states
  that the harness gates the `tap_disabled` regression against the same owned-loopback baseline at the
  accepted 2% median threshold and records the enabled-tap regression only as an ungated observation.
  Because `engineering/project.json` is a material input to `reports/xcom-queue/t036-benchmark.json`, B-1
  was re-executed and B-2 re-verified on the corrected tree.
- **T036-IR-06 (MINOR) — detailed-design evidence-report schema drift.** `detailed-design.md` §4 now
  describes `environment.admitted_inputs` (the map keyed by `XVERSE_XCOM_TOOLCHAIN`,
  `XVERSE_XCOM_PACKAGE_MANIFEST`, `XVERSE_XCOM_T025_TEST_TOOLCHAIN`), drops the unrealizable
  `hashes.report_self` key, and records `baseline.case = "tap_disabled_same_baseline"`, matching the
  realized report.
- **T036-IR-07 (MINOR) — architecture quality-attribute label.** The `architecture.md` §8
  “Same-baseline honesty” row now names the gated `tap_disabled`-versus-same-baseline comparison and labels
  the retained enabled-versus-disabled regression as an ungated observation; the matching negative case
  (`architecture.md` §11 `T36-XB-2` and `verification-plan.md` `NEG-02`) was aligned to the gated case.

### Re-executed evidence (same baseline)

- `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` → exit `0`;
  `--verify` → exit `0`. Gated `SC-008` (`tap_disabled` versus same `baseline`): median latency `0.115%`,
  median throughput `0.114%` (`pass`); enabled-tap observation `53.178%` latency / `34.716%` throughput
  (`gated: false`). Candidate material digest
  `5fe4b7665ff12d4af042b76a3a20a64ba819db33061b06bad33ea108a9251302`; report SHA-256
  `876df54cb34bdaed99b3dad4a63a06ae6d30e5dbd82a9755dd7dda1723dee30c`. The raw samples are retained in
  full; the largest disabled sample regression is `12.666%` (index 3) while the gated median is within 2%,
  and `implementation.md` §4 records this honestly.
- The `implemented_by` endpoint digests for the corrected work products (`engineering/project.json`,
  `architecture.md`, `detailed-design.md`, `verification-plan.md`) were refreshed in
  `engineering/trace/links.json` (23 links); the trace still validates with 750 artifacts and 2716 links,
  and the four T007–T010 register validators pass.
- The confirmed four findings `T036-IR-01`…`-04` from the first repair remain closed. The earlier T036
  sections above are retained as historical evidence for their own candidate revisions and are not
  rewritten; the earlier report SHA-256 and material digest they cite refer to the superseded first-repair
  report, not to the current candidate.

## T036 third repair stage — committed-candidate revision binding

Trusted validation ran the Phase 8 `validation` measure on the prepared candidate and passed the 496 CTest
cases and the 150 pytest cases, then failed at
`engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json` with
`the report is stale or foreign to the exact candidate revision`. Root cause: the report had been measured
on the uncommitted working-tree successor while `HEAD` still equalled the accepted baseline, so it recorded
`baseline_revision == candidate_revision == HEAD == 8ec69ddd…`; candidate preparation then committed exactly
those reviewed files as the direct child commit `18e7cee…`, at which point the former `report == git HEAD`
check rejected the committed candidate. A committed report cannot contain the hash of the commit that
contains it, so the previous contract was unrealizable and the check was wrong, not the evidence.

### Correction

- `engineering/run_xcom_benchmarks.py` no longer equates the candidate with `HEAD`. The report records the
  accepted `baseline_revision` (the measured `HEAD`), `candidate_revision = null`, and the exact-candidate
  binding in `candidate_identity` (the sorted `material_inputs`, `material_digest`, and per-file `hashes`,
  with a `revision_binding` rule). `--verify` now accepts exactly two revisions: `HEAD == baseline_revision`
  (the measured working-tree successor) and `HEAD` as the direct child of `baseline_revision` at a distance
  of one commit (the committed candidate). A foreign or unrelated commit, a merge, and any extra successor
  are rejected. The material-input inventory, the material digest, the per-file SHA-256 hashes, the raw
  sample recomputation, the 2% SC-008 threshold, and the non-production limitations are unchanged and were
  not weakened.
- The report was re-executed with the real harness (not edited), and the affected work products and trace
  were aligned: `architecture.md` (§6.2 report fields, §6.1 `--verify`, §8 exact-candidate binding),
  `detailed-design.md` (§4 schema and the revision-binding bullet, §6 failure semantics),
  `requirements.md` (`T036-STK-002`, `T036-SR-008`), `engineering/requirements/T036-STK-002.json`,
  `engineering/requirements/T036-SR-008.json`, `verification-plan.md` (`CHK-09`, §7),
  `unit-specifications.md` and `engineering/unit-specifications/T036-SR-008-U.json`. The 7
  `implemented_by` harness pins in `engineering/trace/links.json` were refreshed from
  `684f3813…` to `a442fc45f9d7c1b5f348398cc8adf4d57afc82bbf83b1c2053298c8aa227be57`, and the 14
  `implemented_by` endpoint pins for the edited work products (`architecture.md`, `detailed-design.md`,
  `requirements.md`, `verification-plan.md`) now match their current SHA-256 digests; no stale
  hash-pinned link remains.

### Re-executed evidence (same baseline)

- `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` → exit `0`;
  `--verify` → exit `0` from the working-tree successor and, in an isolated committed clone whose parent is
  the baseline, exit `0` in the committed-candidate state. Gated `SC-008` (`tap_disabled` versus same
  `baseline`): median latency `0.815%`, median throughput `0.809%` (`pass`); enabled-tap observation
  `53.316%` latency / `34.775%` throughput (`gated: false`). Candidate material digest
  `247f3afdabde77afbf712399aa28b825279d1c5ec4390847374d1ce2861bc239`; harness SHA-256
  `a442fc45f9d7c1b5f348398cc8adf4d57afc82bbf83b1c2053298c8aa227be57`; report SHA-256
  `95c78ad3988e6e9f501cbfbd0d343f760c7d8a9e374b7c26441e9d88d441bd7c`. The 21 raw samples are retained in
  full; no disabled sample exceeds the 2% threshold on this run (largest per-sample disabled regression is
  sample index 12 at `1.000%`), and `implementation.md` §4 records this honestly.
- Negative probes each exit nonzero: a foreign/orphan commit, a merge whose first parent is the baseline, an
  extra successor commit, changed candidate material, a changed artifact hash, a mismatched material digest,
  a wrong recorded `candidate_revision`, an empty limitations list, and a recorded `pass` whose recomputed
  regression does not hold.
- The trusted `validate_trace` still reports 750 artifacts and 2716 links; the four T007–T010 register
  validators pass. T030–T035 work products and behavior are unchanged. The earlier T036 sections above are
  retained as historical evidence for their own candidate revisions and are not rewritten; the report
  SHA-256 and material digest they cite refer to superseded candidates, not to the current one.

# T037 review index — complete Doxygen comments and warning-free generated reference documentation

Candidate: T037 on baseline `8757a79d4e6b2630124d774fcba2a55d6342a879` (accepted T036 controlled
disabled/enabled-tap benchmark), queue `xcom-t030-t034-20260928`. The T020 and T030–T036 indexes above are
retained as historical predecessor evidence and are not rewritten.

This section records the T037 **plan-stage** work products. The implementation, its local verification, and
the separate internal DeepSeek review are produced by their own stages. External Codex acceptance, the
trusted target-repository integration measure, and the delivery package are separate gates; none is claimed
complete by this index, and external review and acceptance are deferred until the ordered backlog
`xcom-t030-t034-20260928` completes.

## Declared T037 plan-stage work products

- `docs/engineering/xcom/t037/requirements.md` — 5 stakeholder and 10 software requirements
  (`T037-STK-001`…`-005`, `T037-SR-001`…`-010`) with accepted system anchors, the measured plan-stage Doxygen
  gap inventory, the exact evidence report and verification route, and the REF-002 disposition (`unchanged`,
  empty `promoted`; T038–T041 allocated).
- `docs/engineering/xcom/t037/architecture.md` — trust boundaries `T37-XB-1`…`-007`, components
  `T37-CMP-{SOURCE,CONFIG,CHECKER,REPORT,TRACE,WP}`, and the negative-case map.
- `docs/engineering/xcom/t037/detailed-design.md` — the comment obligations for the owned C++ public surface,
  the `Doxyfile` alias requirement (the missing `bounds` command), the strict C++-scoped configuration, the
  fail-closed checker, the `reports/xcom-queue/t037-doxygen.json` schema, and the trace digest-refresh
  obligation.
- `docs/engineering/xcom/t037/unit-specifications.md` — 10 unit specifications and the ten-case index drawn
  from the accepted discovered inventory.
- `docs/engineering/xcom/t037/verification-plan.md` — `CHK-01`…`CHK-13`, `NEG-01`…`NEG-10`, the exact
  evidence report, the task-owned documentation route (`B-1`…`B-5`), and the accepted-anchor traceability.

## Declared T037 engineering records (plan stage)

- `engineering/project.json` — project `xverse-platform`, task `T037`, capability `007`, accepted baseline
  `8757a79d4e6b2630124d774fcba2a55d6342a879`.
- `engineering/requirements/T037-STK-00{1..5}.json` and `engineering/requirements/T037-SR-0{01..10}.json`.
- `engineering/architecture/components/T037-SR-0{01..10}-CMP.json`.
- `engineering/unit-specifications/T037-SR-0{01..10}-U.json`.
- `engineering/validation/scenarios/T037-VS-ACCUMULATED.json` — the inherited discovered case set validating
  `T037-SR-001`…`-010`.
- `engineering/trace/links.json` — 139 additive `T037-L-*` links and refreshed `implemented_by` pins for the
  current-task pointer and the T037-edited configuration/source artifacts. The trusted `validate_trace`
  reports 786 artifacts and 2855 links; the T007–T010 register validators pass.

## Declared T037 implementation change set (expected at the implementation stage)

- Doxygen comments (comments only) across the owned `src/xverse/xcom/include/xverse/xcom/*.hpp`,
  `src/xverse/xcom/src/*.cpp`, and `src/xverse/xcom/fixtures/*`, completing the public-surface and file-block
  obligations; no compiled token, signature, type, default, or expected value changes.
- `Doxyfile` — add the missing alias definition(s) (notably `bounds`) so the repository-wide route the
  trusted Phase 8 validation measure runs is warning-free under `WARN_AS_ERROR = YES`.
- `scripts/check_doxygen.py` — a strict C++-scoped mode that fails closed on an undocumented declaration, a
  missing mandatory tag, or any warning.
- `reports/xcom-queue/t037-doxygen.json` — the exact-candidate report with `command`, `warnings`, `output`,
  the environment identity, hashes, and the candidate identity.
- `engineering/trace/links.json` and inherited `engineering/stage-results/*.json` digest refresh (every
  edited-artifact `implemented_by` pin); `engineering/project.json` current-task pointer; the T037 checkbox
  line in `specs/007-xcom-core/tasks.md` (implementation stage only); `reports/xcom-queue/t037-package.json`;
  `docs/engineering/xcom/t037/{implementation.md,internal-review.json}`.

## Verification state and open limitations

- Trusted measures and the delivery matrix are executed by the workflow gates after implementation; this
  index does not claim they passed.
- **L-T037-1 (measured baseline gap).** The plan stage measured, read-only, that the accepted repository-wide
  `doxygen Doxyfile` route **fails closed** under `WARN_AS_ERROR = YES` (dominated by 104
  `Found unknown command '@bounds'` diagnostics across 49 admitted inputs) and that the strict C++-scoped
  probe over `src/xverse/xcom` reports 111 warning lines concentrated in `activation_plan.hpp` (86) and
  `tool_gateway.hpp` (20). These are the obligations T037 must close; they are plan-stage measurements, not
  implementation results.
- **L-T037-2 (strict C++ scope).** The accepted repository-wide route also covers out-of-scope Python and test
  inputs that cannot be forced to declaration-level strictness without out-of-scope edits; the strict
  declaration-level coverage is therefore scoped to the owned C++ inputs (`DOX-GAP-01`, `DOX-GAP-03`).
- **L-T037-3 (inherited Python findings).** `scripts/check_doxygen.py --coverage-only` fails
  **pre-existing** on Python docstrings in unchanged `scripts/**` and `src/xverse_xdl/**` files
  (`T013-LIM-02`, `T022-LIM-08`, `T023-LIM-08`). T037 preserves that finding as an inherited limitation and
  does not claim the Python coverage check passes.
- **L-T037-4 (trace digest refresh).** T037 edits C++ headers and the Doxygen configuration/checker, so the
  implementation stage must refresh every edited-artifact `implemented_by` pin in `engineering/trace/links.json`
  (and the inherited `engineering/project.json` pins); the plan-stage pins are plan-time only (`T037-OPEN-03`).
- **L-T037-5 (no T010 path reconciliation).** Unlike `docs/engineering/xcom/t036/`,
  `docs/engineering/xcom/t037/` was not declared as a planned artifact path in the T010 unit design, so no
  planned→established path-status reconciliation is performed (`T037-OPEN-07`).
- **L-T037-6 (deferred external review).** External Codex review and explicit user acceptance remain pending;
  the reported DeepSeek stage model is `deepseek-v4-flash` as pinned by the workflow.

## T037 implementation stage — completed comments, strict route, and evidence report

`verdict: awaiting_external_review` — the candidate realizes the plan-stage design. Local results recorded
here are implementation-stage measurements, not acceptance, and no T038/T039/T040/T041 result is claimed.

- **Owned C++ documentation (comments only).** 27 of the 35 owned `src/xverse/xcom` C++ headers, sources, and
  fixtures changed for Doxygen comments only: the 86 undocumented `activation_plan.hpp` plan members, the
  `tool_gateway.hpp` session/endpoint parameter and return gaps, the `stimulation_actions.hpp`
  `reserve_emission`/`journal_and_emit` gaps, the `validation_session.hpp` `Permit` assignment returns, the
  `loopback_provider.hpp`/`synthetic_provider.hpp` private override documentation, the `synthetic_tool.cpp`
  move-constructor parameter, and the mandatory `@file`/`@brief`/`@ingroup` file block on every owned C++
  file. No compiled token, signature, type, default, control-flow decision, contract, or expected value
  changed.
- **`Doxyfile`.** Added the missing `bounds` contract alias (`ALIASES += bounds="\par Bounds:"`); the
  repository-wide `doxygen Doxyfile` route the trusted Phase 8 validation measure runs is now warning-free
  under `WARN_AS_ERROR = YES`.
- **`scripts/check_doxygen.py`.** Added `--strict-cpp` (strict C++-scoped zero-warning generation plus the
  mandatory-file-block coverage gate, fail-closed) and `--report reports/xcom-queue/t037-doxygen.json`
  (executes both routes and writes the exact-candidate evidence report). The preserved default,
  `--coverage-only`, and `--self-test` behavior is unchanged; `--self-test` additionally proves the
  file-block gate rejects a synthetic undocumented header.
- **`reports/xcom-queue/t037-doxygen.json`.** The task-owned evidence report records `command`, `warnings`
  (`count: 0`), `output`, the resolved environment identity, the `strict_cpp` result, artifact `hashes`, and the
  exact-candidate material identity.
- **Trace and governance.** `engineering/trace/links.json` refreshed 57 stale `implemented_by` digest pins for
  the edited artifacts (the plan-stage T037 links remain); `engineering/project.json` carries the current-task
  pointer; the one-line T037 checkbox in `specs/007-xcom-core/tasks.md` is marked complete at implementation
  only.

Measured results (exact candidate, local/offline):

| Route | Result |
| --- | --- |
| `doxygen Doxyfile` with `WARN_AS_ERROR = YES` (repository-wide) | exit `0`; `0` warnings; HTML and XML indexes generated |
| `python3 scripts/check_doxygen.py --strict-cpp` (`INPUT = src/xverse/xcom`) | exit `0`; `33` indexed files; `0` warnings; `0` coverage gaps |
| `python3 scripts/check_doxygen.py --report reports/xcom-queue/t037-doxygen.json` | exit `0`; report written with `warnings.count = 0` |

Open limitations are unchanged: the repository-wide route keeps `WARN_IF_UNDOCUMENTED = NO` and
`WARN_NO_PARAMDOC = NO` because it also covers out-of-scope Python and test inputs (L-T037-2); the inherited
Python docstring findings remain (L-T037-3); and external review/acceptance remain deferred (L-T037-6).

# T038 review index — Spec Kit and REF-002 requirements/design/code/test traceability and public-safe evidence

Candidate: T038 on baseline `d5b9c6399da67a0a028fae21c2f0dcc8da3619bc` (accepted T037 complete Doxygen comments
and warning-free generated reference), queue `xcom-t030-t034-20260928`. The T020 and T030–T037 indexes above
are retained as historical predecessor evidence and are not rewritten.

This section records the T038 **plan-stage** work products. The implementation, its local verification, and the
separate internal DeepSeek review are produced by their own stages. External Codex acceptance, the trusted
target-repository integration measure, and the delivery package are separate gates; none is claimed complete by
this index, and external review and acceptance are deferred until the ordered backlog `xcom-t030-t034-20260928`
completes.

## Declared T038 plan-stage work products

- `docs/engineering/xcom/t038/requirements.md` — 5 stakeholder and 10 software requirements
  (`T038-STK-001`…`-005`, `T038-SR-001`…`-010`) with accepted system/software anchors, the measured
  plan-stage traceability and REF-002 disposition inventory, the exact evidence report and verification route,
  and the REF-002 disposition (`unchanged`, empty `promoted`; T039–T041 allocated).
- `docs/engineering/xcom/t038/architecture.md` — trust boundaries `T38-XB-1`…`-7`, components
  `T38-CMP-{VERIFIER,REPORT,REGISTER,TRACE,SPEC,WP}`, and the negative-case map.
- `docs/engineering/xcom/t038/detailed-design.md` — the chain-validation obligations, the REF-002
  accounting and no-promotion rules, the fail-closed verifier, the
  `reports/xcom-queue/t038-traceability.json` schema, and the trace digest-refresh obligation.
- `docs/engineering/xcom/t038/unit-specifications.md` — 10 unit specifications and the ten-case index drawn
  from the accepted discovered inventory.
- `docs/engineering/xcom/t038/verification-plan.md` — `CHK-01`…`CHK-13`, `NEG-01`…`NEG-11`, the exact evidence
  report, the task-owned traceability route (`B-1`…`B-5`), and the accepted-anchor traceability.

## Declared T038 engineering records (plan stage)

- `engineering/project.json` — project `xverse-platform`, task `T038`, capability `007`, accepted baseline
  `d5b9c6399da67a0a028fae21c2f0dcc8da3619bc`; T037 added to the protected predecessor paths.
- `engineering/requirements/T038-STK-00{1..5}.json` and `engineering/requirements/T038-SR-0{01..10}.json`.
- `engineering/architecture/components/T038-SR-0{01..10}-CMP.json`.
- `engineering/unit-specifications/T038-SR-0{01..10}-U.json`.
- `engineering/validation/scenarios/T038-VS-ACCUMULATED.json` — the inherited discovered case set validating
  `T038-SR-001`…`-010` and `T038-STK-001`…`-005`.
- `engineering/trace/links.json` — 142 additive `T038-L-*` links and refreshed `implemented_by` pins for the
  fifteen links targeting `engineering/project.json`. The trusted `validate_trace` reports 822 artifacts and
  2997 links; the accepted `scripts/validate_xcom_requirements_traceability.py --verify` passes.

## Declared T038 implementation change set (expected at the implementation stage)

- `engineering/check_xcom_traceability.py` — the task-owned, deterministic, offline verifier (`--verify`,
  `--self-test`) that validates the requirement/design/code/test/evidence chain, the twenty REF-002
  dispositions with no promotion, and public safety, and fails closed.
- `reports/xcom-queue/t038-traceability.json` — the exact-candidate report with `requirements`, `design`,
  `code`, `tests`, `evidence`, `ref002`, the environment identity, hashes, and the candidate identity.
- `engineering/trace/links.json` — refreshed `implemented_by` pins for every edited artifact; the plan-stage
  T038 links remain; `engineering/project.json` current-task pointer; the T038 checkbox line in
  `specs/007-xcom-core/tasks.md` (implementation stage only); `reports/xcom-queue/t038-package.json`;
  `docs/engineering/xcom/t038/{implementation.md,internal-review.json}`.

## Verification state and open limitations

- Trusted measures and the delivery matrix are executed by the workflow gates after implementation; this
  index does not claim they passed.
- **L-T038-1 (measured baseline inventory).** The plan stage measured, read-only, the accepted baseline at 786
  inventoried artifacts and 2855 trace links, of which 139 are the accepted `T037-L-*` links; fifteen
  `implemented_by` links pin `engineering/project.json`, and the current-task pointer change refreshes those
  fifteen pins. These are plan-stage measurements, not implementation results.
- **L-T038-2 (all twenty REF-002 IDs remain architectural-target).** The accepted register records ten
  **allocated** and ten **deferred** dispositions; **none** is `implemented`. T038 records and validates the
  `unchanged` capability disposition with an empty `promoted` list and promotes nothing.
- **L-T038-3 (mechanical vs judged public safety).** The task-owned verifier enforces the five mechanically
  decidable excluded-content classes; the classes that are not mechanically decidable remain a review-stage
  judgement (T038-GAP-03).
- **L-T038-4 (trace digest refresh).** T038 edits `engineering/project.json`, so the implementation stage must
  refresh every edited-artifact `implemented_by` pin in `engineering/trace/links.json`; the plan-stage pins are
  plan-time only (`T038-OPEN-02`).
- **L-T038-5 (verifier does not replace the accepted validator).** T038 adds an additive task-owned verifier
  and reuses the accepted `scripts/validate_xcom_requirements_traceability.py` semantics without modifying or
  weakening it (`T038-OPEN-05`).
- **L-T038-6 (deferred external review).** External Codex review and explicit user acceptance remain pending;
  the reported DeepSeek stage model is `deepseek-v4-flash` as pinned by the workflow.

## T038 implementation state (exact candidate)

The T038 implementation produced the task-owned verifier `engineering/check_xcom_traceability.py`, the
exact-candidate evidence report `reports/xcom-queue/t038-traceability.json`, the implementation record, the one-line
T038 checkbox in `specs/007-xcom-core/tasks.md`, and the refreshed `implemented_by` digest pins in
`engineering/trace/links.json`. The report is bound to baseline `d5b9c6399da67a0a028fae21c2f0dcc8da3619bc` and the
54-input material digest `32960ea32ba27231b7ab96d214902ad83f183f7930b711898224ee45b5991d21`.

Measured implementation results (exact candidate, local/offline):

- B-1 `engineering/check_xcom_traceability.py --verify reports/xcom-queue/t038-traceability.json`: exit `0`; the
  T038 chain is complete (`127` resolved edges, `0` unresolved), all twenty REF-002 dispositions are explicit and
  unchanged, and `ref002.promoted` is empty.
- B-2 `engineering/check_xcom_traceability.py --self-test`: exit `0`; `NEG-01` missing edge → `CHAIN_INVALID`,
  `NEG-02` stale hash pin → `STALE_LINK`, `NEG-03` promoted disposition → `REF002_INVALID`, `NEG-04`
  excluded content → `PUBLIC_SAFETY_INVALID`.
- B-3/B-4 `scripts/validate_xcom_requirements_traceability.py --verify` / `--check-human`: exit `0`; the accepted
  register and matrix validate unchanged and the human projections are byte-stable.
- B-5 `run_xcom_phase8_tests.py unit`: `100% tests passed`.

**Pre-repair finding (recorded before repair, per the repository review rule).** The first `--self-test` run
failed the positive fixture with `REF002_INVALID` for `XVE-SYS-0145`…`-0147`, because the accepted
`specs/007-xcom-core/reference-traceability.md` names those IDs as a range. The verifier was corrected to parse the
allocation/deferment bullet table and expand en-dash ranges; the self-test then passed. The repair changed only the
task-owned verifier (additive), not any accepted artifact.

Open limitations are unchanged: mechanical public-safety classes only (L-T038-2); the T035/T036/T037 deliverables
are consumed read-only (L-T038-3); the accepted register maturities are recorded honestly and not rewritten
(L-T038-4); and external review/acceptance remain deferred (L-T038-5/L-T038-6).

# X-COM baseline delivery projection — accepted gateway baseline (2026-09-30)

This section is appended as current index context for the accepted gateway delivery. Every T020 and
T030–T038 section above is retained as historical predecessor evidence for its own candidate revision
and is not rewritten or replaced by a fresh execution claim.

The reviewed candidate `48e85051a419fe1c193afaa47cef40b1e7457fdf` was independently reviewed (T039,
`docs/reviews/t039-r6-independent-review-2026-09-30.md`), its evidence bundle was terminally inspected
(T040, `docs/reviews/t040-r6-terminal-inspection-2026-09-30.md`), the user explicitly approved it (T041,
`automation/reviews/t041-gateway-repair-acceptance-20260930/approval.json`), and it was delivered to
`xverse-platform/main` at that same commit
(`automation/reviews/t041-gateway-repair-acceptance-20260930/delivery/delivery.json` and
`docs/reviews/t041-gateway-repair-delivery-2026-09-30.md`). External tasks T039 and T040 are `completed`
and T041 is `accepted_and_delivered` for that baseline.

A portable, explicitly **DERIVED** projection of those sealed originals is maintained at
`docs/engineering/xcom/accepted-delivery-20260930/projection.json` (with `README.md`); the bounded
reconciliation record is `docs/engineering/xcom/t038/delivery-reconciliation.md`. The projection's
`acceptance_attestation_scope` is `accepted_gateway_baseline_only`: it attests the accepted gateway
baseline only and does not accept or merge any later documentation successor. The capability 007 task
projection in `specs/007-xcom-core/tasks.md` now shows T039–T041 complete for this baseline, with the
pre-acceptance R2–R6 statements retained under an explicit historical label.

The current T036 benchmark, T037 Doxygen, and T038 traceability reports are regenerated to bind the
current documentation successor material identity; the accepted gateway runtime, tests, proto, build
inputs, and all historical baseline evidence remain bound to their original identities. The retained
limitations (logical watch association rather than OS peer authentication; callback-dependent
post-100 ms-grace shutdown; volatile lease identity versus durable recorded stimulation outcomes;
unknown absent outcome with no implicit retry; full owned compiler sanitizer coverage with the admitted
prebuilt gRPC ABI qualification; the `T037-OPEN-06` global Python docstring limitation; the qualified
predecessor conformance replay; and the measured disabled/enabled-tap benchmark scope) remain
accurately recorded. No production-readiness, deployed-service, legacy-compatibility, parity, or
certification claim is made. This documentation/evidence reconciliation is itself a separate successor
candidate and still requires its own review and explicit acceptance before it is accepted or merged.

# XDL Lite Phase 1 review index — offline declared experiment intent compilation (feature `XDL1`)

Candidate: `XDL1` (XDL Lite Phase 1) on accepted baseline
`0c5e249621727b2d0041707de2661f0ed1e1ef23`, admitted thesis revision
`fe58918f9eaf2a6f39cdc9c93cfd4ce615ec84bf`.

This section is appended to the mutable, append-only review index. All pre-existing T020 and
T030–T038 sections above are preserved byte-for-byte. This is a candidate review index only: the
trusted unit/static/integration/validation measures, the assembled pinned `xverse-platform` target
run, the separate read-only `internal_review`, and terminal user acceptance are separate gates, and
none is claimed complete here.

## Declared XDL1 work products

Documentation and work products (`docs/engineering/xdl-lite/`):

- `requirements.md`, `architecture.md`, `detailed-design.md`, `unit-specifications.md`,
  `verification-plan.md`, `integration.md`, `validation.md`, `implementation.md`, `maintenance.md`
- `planned-trace.json`
- `internal-review.json` (to be authored by the separate read-only reviewer; **not** authored here,
  and no verdict is claimed by this index)

Engineering records (this successor candidate):

- `engineering/project.json` — project `xverse-platform`, engineered assurance profile, accepted
  baseline `0c5e249621727b2d0041707de2661f0ed1e1ef23`, current feature pointer `XDL1`, recorded
  predecessor `rework` finding summary.
- `engineering/requirements/` — 19 XDL1 software requirements (`XDL1-SR-001..019`, one bounded
  software allocation per selected REF-002 parent, in the admitted order) plus the 19 original
  `XVE-SYS-*` parent anchors, whose original IDs (including `XVE-SYS-00014`), source text,
  provenance, and `disposition = allocated` are preserved; no new system requirement ID and no
  parent closed or promoted.
- `engineering/architecture/components/` — 19 components (`XDL1-SR-001-CMP..019-CMP`).
- `engineering/unit-specifications/` — 19 unit specifications (`XDL1-SR-001-U..019-U`) with 121
  frozen unit cases and 19 declaration-bound static checks.
- `engineering/verification/measures/` — `XDL1-UNIT` (121 ids), `XDL1-INTEGRATION` (8 ids),
  `XDL1-VALIDATION` (18 ids), `XDL1-STATIC` (19 static-check ids).
- `engineering/validation/scenarios/` — seven intended-use scenarios (`XDL1-VS-01..07`).
- `engineering/trace/links.json` — additive XDL1 links plus refreshed mutable current code-endpoint
  hashes only (3 334 links, 909 artifacts).
- `engineering/stage-results/` — `xdl1-requirements.json`, `xdl1-architecture.json`,
  `xdl1-unit_specification.json`, `xdl1-verification_design.json`, `xdl1-implementation.json`,
  `xdl1-integration.json`, `xdl1-validation.json`, `xdl1-documentation.json`. The separate reviewer
  adds the `internal_review` stage record and `docs/engineering/xdl-lite/internal-review.json`.

Implementation change set (additive only):

- `src/xverse_xdl/experiment_plan.py` (**new** pure offline compiler)
- `src/xverse_xdl/cli.py` (additive `experiment compile` subcommand only)
- `src/xverse_xdl/__init__.py` (additive exports only; `__all__` only grows)
- `xdl/profiles/experiment-lite-v0.1.schema.json` (**new** admitted neutral Profile payload schema)
- `tests/thesis_lite/xdl/**` (owned neutral fixtures and 147 pytest-discoverable cases: 121 unit +
  8 integration + 18 validation)

## Predecessor review finding closure

The predecessor XDL1 attempt-1 candidate was frozen, hash-inventoried, and independently reviewed
read-only (`verdict: rework`, three open major findings, no repair). That review evidence is consumed
read-only and referenced by content hash: predecessor frozen-candidate manifest
`820f3c47d264a6e75a75e3fb58f9465d9bb1ba3495b6c263797d145230c59093`; predecessor
`review/internal-review.json` `b5ed14f18ae1e50d246deb2765215b11bdfd41c54dca0f7699325a1c9d12c2e4`;
predecessor `review/stage.json` `9b09049a68c45160a9ee0e57b918c04dcad6ec7cdc732c94b0953009221e0e23`.

The successor requirement baseline resolves the findings in the affected acceptance criteria; the
successor design freezes the concrete behaviour (`XDL1-DD-13`, `XDL1-DD-14`, detailed-design §10.3 and
§16.2); the successor implementation realizes it, and the integration and validation stages
re-executed each finding's exact reproduction. No assertion was weakened, renamed, skipped, xfailed,
or deleted.

- `XDL1-RVW-001` (major, contract fidelity / units-and-bounds): `ExperimentLimits.max_parameters` is
  now enforced over three explicit scopes — per declared extension payload, **total compiled
  parameters** over the finished plan, and declared core parameters — with any violation emitting
  `XDL1-PLAN-BOUND-EXCEEDED` and `plan = None`. The predecessor emitted a resolved plan carrying more
  compiled parameters than the declared bound; the successor rejects it.
- `XDL1-RVW-002` (major, contract fidelity / declared-intent projection): `components[]` now always
  carries exactly one leading `scope = "system"` entry projecting every declared
  `System.spec.parameters[]` entry (fixture id `loop-count`); component-instance entries project only
  their referenced Component's parameters. The predecessor silently dropped declared System core
  parameters.
- `XDL1-RVW-003` (major, verification coverage / missing negative evidence): per-scope negative cases
  were added for every declared count-based bound — including the total compiled-parameter scope whose
  per-payload lists are each individually within the bound — and `XDL1-PLAN-BOUND-EXCEEDED` is no
  longer the only frozen diagnostic code with zero test occurrences (17 occurrences across
  `test_xdl1_quantity_unit.py` and `test_xdl1_validation.py`).

Closure here rests on executed candidate-local evidence. Its terminal confirmation belongs to the
separate read-only `internal_review` stage and the trusted host measures.

## Verification state and open limitations

- Candidate-local preliminary worker checks (not trusted evidence): `python3 -m pytest -q
  tests/thesis_lite/xdl` reports `147 passed`; `python3 -m pytest -q` over the whole repository reports
  `297 passed`; the CLI over the five neutral fixtures exits `0` with
  `resolved plan ccf08204181f47ae7868ed7b6795c1fb2ae2d6e0aeb04437000a1b4ab3988f7d (23 sections)`,
  and the JSON-envelope plan digest is identical; the rejection fixture exits `1` with structured
  diagnostics and writes no file.
- `fabro_engineering.core.validate_trace(checkout, "xverse-platform")` returns
  `{"artifacts": 909, "links": 3334}`, and every artifact hash recorded by the earlier XDL1 stage
  records re-hashes unchanged.
- The trusted host must bind `unit → XDL1-UNIT`, `static_analysis → XDL1-STATIC`,
  `integration → XDL1-INTEGRATION`, and `validation → XDL1-VALIDATION`, then assemble the exact
  candidate into the pinned `xverse-platform` target (whole-system integration is defined only by the
  trusted `mode = target_repository` contract) and execute the trusted measures. Without those
  bindings the gates fail closed rather than being papered over.
- The separate read-only `internal_review` must independently confirm the predecessor finding
  closures and the absence of new findings; terminal user acceptance follows. Neither is claimed here.
- No runtime, availability, readiness, compatibility, parity, certification, or delivery claim is
  made. A resolved plan proves declared-intent validation only. No scientific protocol value,
  threshold, tolerance, deadline, seed, margin, or campaign parameter is defaulted, invented, or
  narrowed; those remain caller inputs, bounded only by the finite platform library limits. No
  legacy, compatibility, blueprint, or oracle/assurance path is executed and no REF-002 parent is
  closed or promoted.
- Public-safe: this section uses repository-relative locators only and contains no secret, credential,
  host address, private source excerpt, or sensitive deployment detail.

The index points at `docs/engineering/xdl-lite/internal-review.json`, which the later read-only
`internal_review` stage authors after host candidate sealing; this section records the pointer and
claims no verdict.
