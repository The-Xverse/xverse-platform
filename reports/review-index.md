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
