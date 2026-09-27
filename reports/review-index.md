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
