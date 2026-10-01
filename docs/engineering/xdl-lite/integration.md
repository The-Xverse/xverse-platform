# XDL Lite Phase 1 — integration record (feature `XDL1`)

| Field | Value |
| --- | --- |
| Feature | `XDL1` — XDL Lite Phase 1, offline declared experiment intent compilation |
| Stage | `integration` |
| Attempt | `1` |
| Model | DeepSeek V4 Flash (`provider=deepseek`, `backend=api`, `requested_model=deepseek-v4-flash`) |
| Admitted thesis revision | `fe58918f9eaf2a6f39cdc9c93cfd4ce615ec84bf` |
| Accepted platform baseline | `0c5e249621727b2d0041707de2661f0ed1e1ef23` |
| Maturity | **Implemented, candidate-local integration only.** Whole-system integration over the assembled pinned target is a pending trusted host gate. |
| Owned immutable output | `docs/engineering/xdl-lite/integration.md` (this file) |

This record is produced by the `integration` stage of the externally admitted feature delivery. It is
the successor to the independently reviewed predecessor attempt, whose read-only review returned
`verdict=rework` with findings `XDL1-RVW-001/002/003`. This stage preserves every earlier successor
stage artifact byte-for-byte, exercises the additive compiler/CLI together with the accepted platform
consumers in this one checkout, re-verifies the predecessor finding resolutions, and reports its
pytest runs as **preliminary worker checks**. It makes no trusted-integration, runtime, readiness,
compatibility, parity, certification, or delivery claim.

## 1. Scope and integration boundary

XDL Lite Phase 1 is additive and offline. It compiles declared experiment intent into one canonical
resolved plan over the existing five XDL v1alpha1 resource kinds and the existing loader, schema
registry, normalizer, derived catalog, lifecycle-plan and X-COM activation-plan contracts. It starts
no process, opens no socket, retrieves no artifact, reads no ambient clock/locale/environment and
performs no lifecycle or runtime action.

The admitted workflow separates two integration surfaces:

* **Candidate-local (this stage).** The 8 real-consumer cases in
  `tests/thesis_lite/xdl/test_xdl1_integration.py` run inside this checkout through the real admitted
  code paths, with real repository fixtures. No mock replaces any consumer. These runs are
  preliminary worker checks.
* **Trusted whole-system (pending host).** The trusted host assembles the exact candidate into the
  pinned `xverse-platform` target (`system_integration.mode = target_repository`) and repeats the
  `integration` measure there. Only that run is integration evidence. This candidate cannot inspect
  or edit the trusted policy, so it records the obligation rather than claiming the result.

## 2. The `XDL1-INTEGRATION` measure

| Field | Value |
| --- | --- |
| Measure record | `engineering/verification/measures/XDL1-INTEGRATION.json` (`kind = integration`, rev 1) |
| Record SHA-256 | `2b3c853693be8306c3033148865081ec426d23cd0c68f252488204591d745515` |
| Declared command | `python3 -m pytest -vv tests/thesis_lite/xdl/test_xdl1_integration.py` |
| Discovery rule | `[1-9][0-9]* passed` |
| Test module | `tests/thesis_lite/xdl/test_xdl1_integration.py` (SHA-256 `9594406e719f455b720f39d1a9cd4fb5fc318bb83e03d0f8d129bf572397f231`) |
| Bound identifiers | exactly the 8 cases below |

The record `command` is a candidate-local descriptor only; whole-system integration is defined
solely by the trusted policy `system_integration` contract. The measure is bound to the additive
feature measure ID rather than to a historical protected measure record, so the historical
`integration` record and its evidence are untouched.

The 8 integration identifiers and their module hash are **carried forward unchanged** from the
reviewed predecessor set: no predecessor finding (`XDL1-RVW-001/002/003`) concerned the integration
surface, so the successor changed only the affected unit/validation evidence and the frozen
`detailed-design.md` §10.3/§XDL1-DD-14 compiler behaviour, not the integration contract.

## 3. Real consumers exercised by the 8 integration cases

Verbatim identifiers (each is the exact `test_ids` entry in the measure record):

| Exact identifier | Real code path(s) exercised | What it proves |
| --- | --- | --- |
| `test_real_loader_schema_registry_and_compiler_resolve_neutral_experiment` | `validate_files` (loader, core schema registry, Profile schema catalog, semantics, normalizer) → `compile_experiment_plan` | The accepted validation pipeline feeds the additive pure compiler and yields one `resolved` plan over real neutral fixtures; no mocked gate. |
| `test_real_cli_experiment_compile_end_to_end_over_fixture_files` | `python3 -m xverse_xdl experiment compile` (real subprocess) | The additive subcommand resolves real fixture files, exits `0`, and emits the frozen JSON envelope and text summary with the same plan digest. |
| `test_existing_loader_and_normalizer_compatible_on_accepted_examples` | accepted `xdl/examples/v1alpha1/**` through `validate_files`, `canonical_json` | Accepted examples still validate with unchanged resources and no `XDL1-PLAN-*` diagnostic; canonical normalization is stable. |
| `test_existing_catalog_consumer_compatible_on_normalized_resources` | `derive_catalog` over normalized accepted SD-0001 resources | The accepted M3 derived catalog keeps its entries and determinism; it is consumed read-only. |
| `test_existing_xcom_activation_plan_consumer_compatible` | accepted C++ X-COM activation-plan contract entry point `xcom_plan.compile_plan` / `compute_digest` / `plan_matches_digest` | The activation-plan contract still compiles an accepted graph to a stable, self-consistent canonical digest; nothing is started. |
| `test_existing_lifecycle_plan_api_compatible_without_execution` | `derive_catalog` + `build_lifecycle_plan` | The accepted lifecycle-plan API still returns its pure plan shape (`requires_execution_permit`, actions, blockers) and performs no action. |
| `test_legacy_cli_validate_normalize_and_version_behaviour_preserved` | `xdl validate`, `xdl normalize`, `xdl version` (real subprocess) | Accepted CLI commands keep their output, exit codes and permutation-independent normalize output for existing inputs. |
| `test_rejected_compile_leaves_consumers_and_files_unchanged` | additive compiler + accepted consumers over a rejected input set | A rejected compile returns `plan = None` with diagnostics, leaves every supplied file byte-identical, and leaves accepted consumers functional — no partial plan and no side effect. |

Backward compatibility is therefore **asserted by execution**, not assumed: the accepted loader,
normalizer, catalog, lifecycle-plan and C++ X-COM activation-plan contracts are exercised through
their existing public entry points and are only ever consumed read-only. The additive compiler never
imports, invokes or modifies the C++ X-COM boundary, the lifecycle controller, or any accepted XDL
schema under `xdl/schemas/v1alpha1/**`.

## 4. Predecessor review finding closure (read-only, hash-verified evidence)

The predecessor successor-chain review is admitted read-only and hash-verified in this stage:

| Evidence | SHA-256 |
| --- | --- |
| `/opt/input/predecessor-review/manifest.json` (frozen-candidate map) | `820f3c47d264a6e75a75e3fb58f9465d9bb1ba3495b6c263797d145230c59093` |
| `predecessor-review/review/internal-review.json` (`verdict=rework`) | `b5ed14f18ae1e50d246deb2765215b11bdfd41c54dca0f7699325a1c9d12c2e4` |
| `predecessor-review/review/stage.json` (reviewer stage record) | `9b09049a68c45160a9ee0e57b918c04dcad6ec7cdc732c94b0953009221e0e23` |

The three open findings were resolved by the successor `implementation` stage in the frozen
contract, not by weakening any assertion. This stage independently re-executed the affected
behaviour:

| Finding | Resolution in the successor candidate | Independent re-execution in this stage |
| --- | --- | --- |
| `XDL1-RVW-001` — total `max_parameters` bound unenforced | `compile_experiment_plan` now counts the finished compiled-parameter sections (`len(parameters) + Σ lifecycleIntent[].parameters + Σ faultSchedule[].parameters`) once before identity finalization and rejects above the bound with `XDL1-PLAN-BOUND-EXCEEDED` and `plan = None`. | `pytest tests/thesis_lite/xdl -k unit` runs `test_max_parameters_total_compiled_scope_exceeded_rejected` and the at-bound positive `test_max_parameters_all_scopes_at_bound_accepted`; `test_total_compiled_parameter_bound_exceeded_rejected_without_plan` covers the validation level. All pass. |
| `XDL1-RVW-002` — declared `System.spec.parameters` dropped | `components[]` always carries exactly one leading `scope="system"` entry whose `declaredParameters` project every declared `System.spec.parameters[]` entry; component-instance entries project only their referenced Component parameters. | Direct execution over the neutral fixture yields `system declaredParameters: ['loop-count']` with `loop-count` present (previously absent) and `nominal-rate` retained in the component-instance scopes — no drop, no cross-scope duplication. |
| `XDL1-RVW-003` — no negative case for `XDL1-PLAN-BOUND-EXCEEDED` | Per-scope negative cases added across `XDL1-UNIT` (per-payload, total compiled, declared-core, and the count bounds `max_steps`, `max_faults`, `max_observers`, `max_metrics`, `max_dependencies_per_step`, `max_flows`, `max_bindings`, `max_resources`, `max_text_length`, `max_diagnostics`) and `XDL1-VS-07` (`XDL1-PLAN-BOUND-EXCEEDED` occurs 17 times across the unit and validation modules). | The measured `XDL1-UNIT` (121 ids) and `XDL1-VALIDATION` (18 ids) sets are collected and pass; `XDL1-PLAN-BOUND-EXCEEDED` is exercised in `test_xdl1_quantity_unit.py` and `test_xdl1_validation.py`. |

These re-executions are **preliminary worker checks only**. The terminal independent read-only review
and the trusted host measures remain the acceptance gates; this record does not close the findings
by itself and does not promote the feature.

## 5. Preserved boundaries

* Accepted XDL schemas `xdl/schemas/v1alpha1/**` unchanged; the new
  `xdl/profiles/experiment-lite-v0.1.schema.json` (SHA-256
  `a2123b3349ab016fda829d57084d9142565bf76fdafd474fe19fe222562dfc30`) is a separate Profile
  artifact referenced through `spec.schemaRef`.
* Accepted public APIs unchanged; the additive module adds nine exports to
  `src/xverse_xdl/__init__.py` (`0e0ca25bf3afab9276a4a18900ed2fc3d82e4c3bf23854c4c9c69b3791cec8ce`)
  and one `experiment compile` subcommand in `src/xverse_xdl/cli.py`
  (`15502fdf6deef6a6f6730d37cd4b755c9a125c223a9e919611536ebaceed2d6a`), and removes nothing.
* C++ X-COM (`proto/xverse/xcom/v1/**`, `src/xverse/xcom/**`, `src/xverse/xcom/contracts/**`,
  `xdl/profiles/xcom-v0.1.schema.json`) not touched, imported or invoked.
* Legacy, compatibility, blueprint and oracle/assurance logic untouched; no runtime or legacy
  execution, no fallback or alternative model route, no online learning, no invented thesis value,
  and no next-phase work.

## 6. Preliminary worker checks (local, not trusted evidence)

Environment: Python 3.11.16, pytest 8.4.2, `/usr/local/bin/python3`, working directory the candidate
checkout. All commands were run read-only apart from pytest cache writes.

| Command | Result |
| --- | --- |
| `python3 -m pytest -vv tests/thesis_lite/xdl/test_xdl1_integration.py` | `8 passed`; the verbose output prints all 8 bound identifiers, matching `XDL1-INTEGRATION.test_ids` exactly (8 collected, no missing, no extra). |
| `python3 -m pytest -q tests/thesis_lite` | `147 passed` (121 unit + 8 integration + 18 validation case identifiers). |
| `python3 -m pytest -q` (whole repository) | `297 passed`, no failure or error in the accepted loaders, catalog, lifecycle, CLI and X-COM suites. |
| `python3 -m xverse_xdl experiment compile --profile-schema xdl/profiles/experiment-lite-v0.1.schema.json <5 neutral fixtures>` | exit `0`, one line `resolved plan ccf08204181f47ae7868ed7b6795c1fb2ae2d6e0aeb04437000a1b4ab3988f7d (23 sections)`. |
| `python3 -m xverse_xdl experiment compile --format json ... <5 neutral fixtures>` | `valid=True`, `status=resolved`, plan digest `ccf08204181f47ae7868ed7b6795c1fb2ae2d6e0aeb04437000a1b4ab3988f7d` — byte-identical to the text-summary digest. |

The resolved-plan digest changed from the predecessor `8c82b2f1…` to
`ccf08204181f47ae7868ed7b6795c1fb2ae2d6e0aeb04437000a1b4ab3988f7d` because the successor plan now
carries the additional always-present `scope="system"` `components[]` entry required by
`XDL1-DD-14`; this is the intended contract change and the digest is stable run-to-run.

Read-only verification additionally confirmed that run-to-run output is deterministic (the text
summary digest equals the JSON envelope plan digest) and that no file was created or mutated by a
successful or rejected compile.

### 6.1 Prior-artifact preservation check

Every artifact hash recorded by the earlier successor stage records was re-hashed against the working
tree in this stage using `fabro_engineering.core.validate_stage` followed by an independent
`sha256` recomputation: **all match, 0 mismatches** (`39 requirements + 21 architecture +
20 unit_specification + 13 verification_design + 26 implementation = 119` artifacts). No earlier
stage output, historical record, accepted test, or accepted schema was modified.

Selected preserved successor artifacts:

| Artifact | SHA-256 |
| --- | --- |
| `docs/engineering/xdl-lite/requirements.md` | `d29a7f2c6314e7fc145fad62ac86357f24c4bfcb6af0487429190ee5bf20d128` |
| `docs/engineering/xdl-lite/architecture.md` | `6fd9cce342822554addaa1be70d547ec3782b0db086fe164f897975d41fb9ae8` |
| `docs/engineering/xdl-lite/detailed-design.md` | `d5635372fb363fcfaa996c0285a999b43b5008e652e0209ed23622e3942e87ea` |
| `docs/engineering/xdl-lite/unit-specifications.md` | `008fcb8d36a355b008234136c8d05b3bfc0e91ebf5a8861bc47da38d39fcefd2` |
| `docs/engineering/xdl-lite/verification-plan.md` | `9772f9adeb81f9fa936d28267ae80eaf2f4a79e58b63c1964a32dcd0ab6bceb7` |
| `docs/engineering/xdl-lite/planned-trace.json` | `7b670c9bd73b6b6aa5e7cfed65024736d2f44e077431a8196b3daf59b8400b00` |
| `src/xverse_xdl/experiment_plan.py` | `4e4affa52fe77cea4f37598cd6bce2309a0a767a7e878372ecee0a5599603393` |
| `engineering/validation/scenarios/XDL1-VS-07.json` | `574a1b205a4b1ebddca0727e1ebfc4883a97430ce3867a741dfb4a8378fc65e9` |

## 7. Trace and current-pointer status

`engineering/trace/links.json` (mutable current trace) holds 3334 links, of which 309 touch `XDL1`.
The additive `implemented_by` links added by the implementation stage bind each `XDL1-SR` requirement
and allocation to the admitted code endpoints with exact source SHA-256 revisions. This stage does
not rewrite the trace file; the scheduled refresh of the 21 pre-existing `engineering/project.json`
`implemented_by` endpoint hashes remains owned by the `validation` stage, and `core.validate_trace`
is expected to abort on those until then.

`engineering/project.json` already carries the current feature pointer `XDL1`, accepted baseline
authority `0c5e249621727b2d0041707de2661f0ed1e1ef23`, the additive change boundary, and the recorded
predecessor `rework` finding summary; it is not modified by this stage.

## 8. Limitations and open host obligations

* These local pytest runs are **preliminary worker checks**. They are not the trusted integration
  measure and are not evidence of whole-system integration, and they do not by themselves close
  `XDL1-RVW-001/002/003`.
* The trusted host must assemble the exact candidate into the pinned `xverse-platform` target at the
  declared revision and run the `integration` measure over the assembled checkout; the candidate
  cannot inspect the external policy or the assembled target.
* The trusted policy must bind the `integration` measure to the new `XDL1-INTEGRATION` record
  (SHA-256 `2b3c853693be8306c3033148865081ec426d23cd0c68f252488204591d745515`); its absence fails the
  gate closed rather than being papered over.
* This record claims no runtime execution, artifact availability, readiness, compatibility, parity,
  certification, or delivery. A resolved plan proves declared-intent validation only.
* No scientific protocol value, threshold, tolerance, deadline, seed, margin or campaign parameter
  is defaulted, invented or narrowed; those remain caller inputs, bounded only by the finite
  platform library limits.
* Public-safe: this record uses repository-relative locators only and contains no secret, credential,
  host address, or private source excerpt.

## 9. Hand-off

The `validation` stage owns `docs/engineering/xdl-lite/validation.md`, the validation tests, the
trace endpoint-hash refresh, and the completed software-to-parent/design/code/test/validation trace.
A separate read-only `internal_review` stage follows candidate sealing and must independently confirm
the predecessor finding closures and the absence of new findings. No pass is claimed until the
trusted host gates and the independent reviewer have completed.
