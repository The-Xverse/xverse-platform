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
