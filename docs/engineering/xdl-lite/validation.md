# XDL Lite Phase 1 — validation record (feature `XDL1`)

| Field | Value |
| --- | --- |
| Feature | `XDL1` — XDL Lite Phase 1, offline declared experiment intent compilation |
| Stage | `validation` |
| Attempt | `1` |
| Successor | resolves the three open findings of the independent predecessor review (`XDL1-RVW-001/002/003`) |
| Model | DeepSeek V4 Flash (`provider=deepseek`, `backend=api`, `requested_model=deepseek-v4-flash`) |
| Admitted thesis revision | `fe58918f9eaf2a6f39cdc9c93cfd4ce615ec84bf` |
| Accepted platform baseline | `0c5e249621727b2d0041707de2661f0ed1e1ef23` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 (`XDL1-SR-001` … `XDL1-SR-019`) |
| Design authorities | [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md) rev 1 |
| Owned immutable output | `docs/engineering/xdl-lite/validation.md` (this file) |
| Maturity | **Implemented, candidate-locally validated only.** The trusted validation measure over the assembled pinned target, the separate read-only `internal_review`, and terminal user acceptance remain pending host gates. |

This record is produced by the `validation` stage of the externally admitted feature delivery. It
exercises the independent expected-outcome, hostile-input, no-side-effect, and metamorphic cases in
`tests/thesis_lite/xdl` through the real additive compiler, loader, schema registry, catalog and X-COM
activation-plan consumers, confirms that the collected identifiers match the frozen measure and
scenario records, independently re-executes the three predecessor review findings, and completes the
current software-to-parent/design/code/test/validation trace. It makes no runtime, availability,
readiness, compatibility, parity, certification, delivery, or external-acceptance claim.
`status: accepted` on a requirement, component, unit, or measure record is internal engineering intent
only; it is never evidence of implementation satisfaction or external delivery acceptance.

## 1. Scope and boundary

XDL Lite Phase 1 is additive and offline: it compiles declared experiment intent into one canonical
resolved plan over the existing five XDL v1alpha1 resource kinds and the accepted loader, schema
registry, semantics, normalizer, derived catalog, lifecycle-plan and C++ X-COM activation-plan
contracts. Validation covers Phase 1 only. Runtime or legacy execution, artifact retrieval or
availability, oracle access, online learning, fallback routes, Argus/Maestro implementations,
compatibility/parity claims, production change and every Phase 2+ capability are out of scope and are
not validated here.

All cases run offline in this checkout with Python 3.11.16 and pytest 8.4.2. They start no process or
service, open no socket, read no ambient clock/locale/environment, retrieve no artifact, and write
nothing except an explicitly requested CLI output path and the pytest cache. Whole-system validation
over the assembled pinned `xverse-platform` target is a separate trusted host obligation (§9).

## 2. Validation measure and scenarios

| Field | Value |
| --- | --- |
| Measure record | `engineering/verification/measures/XDL1-VALIDATION.json` (`kind = validation`, rev 1, SHA-256 `be287f53b98ef3ce0a128dafbf40fa3003523f96981c30f0b58477a4be3ad0f3`) |
| Declared command | `python3 -m pytest -vv tests/thesis_lite/xdl/test_xdl1_validation.py` |
| Discovery rule | `[1-9][0-9]* passed` |
| Test module | `tests/thesis_lite/xdl/test_xdl1_validation.py` (SHA-256 `5a0358e6a13a2df86863a234c892d27a756a812ab0e0f2fe3fc9825ae3e4e8bd`) |
| Bound identifiers | exactly the 18 cases below |
| Scenario records | `engineering/validation/scenarios/XDL1-VS-01.json` … `XDL1-VS-07.json` (rev 1) |

The union of the seven scenario `test_ids` is **exactly** the eighteen `XDL1-VALIDATION` `test_ids`
(verified in §5): no scenario case is unbound and no measure case is absent from a scenario. Every
accepted software requirement `XDL1-SR-001` … `XDL1-SR-019` is covered by at least one scenario
`validates` link. The record `command` is a candidate-local descriptor only; the executable validation
command and its discovery check are bound by the trusted external host policy.

## 3. Exercised validation cases

Each identifier below is verbatim from the measure record and the scenario records.

| Exact identifier (module `tests/thesis_lite/xdl/test_xdl1_validation.py`) | Scenario | Intended use proven |
| --- | --- | --- |
| `test_author_declared_experiment_yields_one_canonical_resolved_plan` | VS-01 | An author's closed resource set plus the admitted neutral experiment Profile resolves to exactly one versioned canonical plan with the frozen body shape and a self-consistent digest. |
| `test_resolved_plan_records_seed_parameters_faults_observers_and_metrics` | VS-01 | The declared seed, parameters, time domains/mappings, intended fault schedule, observers and metric references appear verbatim with no evaluation. |
| `test_integrator_receives_stable_structured_diagnostics_for_declared_defects` | VS-02 | An integrator receives stable, structured diagnostics (pointer, code, severity, remediation) for the declared defect classes. |
| `test_rejected_compile_has_no_side_effect_and_no_partial_plan` | VS-02 | A rejected compile returns `plan = None`, exposes no partial/executable plan, and leaves supplied files and consumers unchanged. |
| `test_downstream_consumer_verifies_versions_and_hashes_without_reparsing_yaml` | VS-03 | A downstream consumer can verify plan/Profile/API versions and normalized source hashes without reparsing YAML. |
| `test_equivalent_encodings_and_permutations_share_one_semantic_identity` | VS-03 | Equivalent YAML/JSON encodings and resource/payload permutations produce equal semantic plan bytes/digest. |
| `test_existing_loader_normalizer_catalog_and_xcom_consumers_remain_compatible` | VS-04 | Accepted loader/normalizer/catalog/X-COM activation-plan consumers keep their accepted behaviour and outputs. |
| `test_existing_cli_commands_remain_byte_compatible` | VS-04 | Accepted `xdl validate`, `xdl normalize`, `xdl version` output and exit codes are preserved for existing inputs. |
| `test_plan_limitations_and_non_readiness_forbid_availability_claims` | VS-05 | The plan carries declared fidelity limitations and the compiler non-readiness statement; no availability claim is emitted. |
| `test_unsupported_physical_realization_rejected_without_default` | VS-05 | An unsupported physical realization is rejected with a stable diagnostic and no default substitution. |
| `test_declared_time_domain_and_mapping_recorded_without_inference` | VS-06 | Declared time domains and mappings are recorded verbatim; nothing is inferred or defaulted. |
| `test_nonfinite_negative_overflow_and_unknown_units_rejected` | VS-06 | Non-finite, negative, overflowing or unknown-unit quantities are rejected without a silent default. |
| `test_per_payload_parameter_bound_exceeded_rejected_without_plan` | VS-07 | A per-payload declared parameter list above `max_parameters` is rejected with `XDL1-PLAN-BOUND-EXCEEDED` and no plan. |
| `test_total_compiled_parameter_bound_exceeded_rejected_without_plan` | VS-07 | Per-payload lists each within the bound while their compiled total exceeds it is rejected with `XDL1-PLAN-BOUND-EXCEEDED` and no plan (XDL1-RVW-001). |
| `test_declared_core_parameter_bound_exceeded_rejected_without_plan` | VS-07 | A declared core System parameter list above the bound is rejected with `XDL1-PLAN-BOUND-EXCEEDED` and no plan. |
| `test_declared_limitation_bound_exceeded_rejected_without_plan` | VS-07 | A declared limitation count above `max_limitations` is rejected with `XDL1-PLAN-BOUND-EXCEEDED` and no plan. |
| `test_parameter_counts_at_declared_bounds_compile_resolved_plan` | VS-07 | Parameter counts exactly at every declared bound compile exactly one resolved, digest-consistent plan. |
| `test_system_core_parameters_projected_without_drop_or_duplication` | VS-07 | Every declared `System.spec.parameters[]` entry appears once in the `scope="system"` `components[]` entry and is not duplicated into a component-instance entry (XDL1-RVW-002). |

## 4. Predecessor finding resolution (XDL1-RVW-001 / -002 / -003)

The independent predecessor review (`/opt/input/predecessor-review/review/internal-review.json`,
SHA-256 `b5ed14f18ae1e50d246deb2765215b11bdfd41c54dca0f7699325a1c9d12c2e4`, read-only) raised three
open findings. This stage exercised each finding's exact reproduction independently against the
successor revision and recorded the concrete observed outputs. The findings are recorded here as
closed by executed evidence; terminal closure remains with the separate read-only `internal_review`
stage and the trusted host measures.

### 4.1 XDL1-RVW-001 — total compiled-parameter bound

* **Contract:** `detailed-design.md` §10.2/§10.3 and decision `XDL1-DD-13` freeze `max_parameters = 256`
  applying to parameters per payload **and total compiled parameters** (`C_total`), enforced with
  `XDL1-PLAN-BOUND-EXCEEDED`.
* **Exact predecessor reproduction re-run:** `compile_experiment_plan(support.default_set(scenario=…),
  limits=ExperimentLimits(max_parameters=2))` where the scenario carries 2 scenario-intent parameters
  (2, within the bound) plus 1 parameter on each of 2 step-intents (1 and 1, each within the bound).
* **Observed successor output (independent re-execution):**
  `plan is None: True`, `is_valid: False`, `diagnostics codes: ['XDL1-PLAN-BOUND-EXCEEDED']`,
  `run.status: 'rejected'`. The predecessor observed the opposite (`is_valid is True`,
  `diagnostics == []`, 4 compiled parameters emitted).
* **Enforcement location:** `src/xverse_xdl/experiment_plan.py` computes `C_total` over the finished
  sections before identity finalization and emits `XDL1-PLAN-BOUND-EXCEEDED` when it exceeds the bound.
* **Bound pytest-discoverable evidence:**
  * `test_xdl1_quantity_unit.py::test_max_parameters_total_compiled_scope_exceeded_rejected` — PASSED
  * `test_xdl1_quantity_unit.py::test_max_parameters_per_payload_scope_exceeded_rejected` — PASSED
  * `test_xdl1_quantity_unit.py::test_max_parameters_declared_core_scope_exceeded_rejected` — PASSED
  * `test_xdl1_quantity_unit.py::test_max_parameters_all_scopes_at_bound_accepted` — PASSED
  * `test_xdl1_validation.py::test_total_compiled_parameter_bound_exceeded_rejected_without_plan` — PASSED
  * `test_xdl1_validation.py::test_parameter_counts_at_declared_bounds_compile_resolved_plan` — PASSED

### 4.2 XDL1-RVW-002 — declared System core-parameter projection

* **Contract:** `detailed-design.md` §5/§7 and decision `XDL1-DD-14` map both `Component.spec.parameters[]`
  and `System.spec.parameters[]` into the plan; the deterministic destination for System-level core
  parameters is an always-present `scope="system"` entry in `components[]`. XDL1-SR-002 requires
  compiling declared System and Component intent into the resolved plan.
* **Exact predecessor reproduction re-run:** compile the neutral fixture, which declares the System
  core parameter id `loop-count`; the predecessor observed `loop-count` absent from the whole plan.
* **Observed successor output (independent re-execution):**
  `plan valid: True`, `components[0].scope: 'system'`,
  `components[0].declaredParameters ids: ['loop-count']`,
  `'loop-count' anywhere in plan: True`.
* **Bound pytest-discoverable evidence:**
  * `test_xdl1_validation.py::test_system_core_parameters_projected_without_drop_or_duplication` — PASSED
  * `test_xdl1_intent_unit.py::test_system_core_parameters_projected_to_system_scope` — PASSED
  * `test_xdl1_intent_unit.py::test_system_core_parameters_not_dropped_when_component_parameters_present` — PASSED
  * `test_xdl1_intent_unit.py::test_system_scope_entry_always_present_with_empty_declared_parameters` — PASSED

### 4.3 XDL1-RVW-003 — missing count-based bound negative evidence

* **Contract:** `detailed-design.md` §9/§10.2 lists `XDL1-PLAN-BOUND-EXCEEDED`; XDL1-SR-019 acceptance
  requires the declared library bounds to have negative tests. The predecessor observed
  `XDL1-PLAN-BOUND-EXCEEDED` as the only one of the 42 frozen diagnostic codes with zero occurrences
  in `tests/thesis_lite/xdl` and no count-based bound negative.
* **Observed successor measurement:** `XDL1-PLAN-BOUND-EXCEEDED` now occurs **17 times** in
  `tests/thesis_lite/xdl` (13 in `test_xdl1_quantity_unit.py`, 4 in `test_xdl1_validation.py`).
* **Per-scope negative coverage — all PASSED, all pytest-discoverable:**

  | Declared bound | Exact negative (and boundary) case | Result |
  | --- | --- | --- |
  | `max_parameters` per payload | `test_xdl1_quantity_unit.py::test_max_parameters_per_payload_scope_exceeded_rejected` | PASSED |
  | `max_parameters` total compiled | `test_xdl1_quantity_unit.py::test_max_parameters_total_compiled_scope_exceeded_rejected` | PASSED |
  | `max_parameters` declared core | `test_xdl1_quantity_unit.py::test_max_parameters_declared_core_scope_exceeded_rejected` | PASSED |
  | `max_parameters` at-bound boundary | `test_xdl1_quantity_unit.py::test_max_parameters_all_scopes_at_bound_accepted` | PASSED |
  | `max_steps` | `test_xdl1_quantity_unit.py::test_max_steps_exceeded_rejected` | PASSED |
  | `max_faults` | `test_xdl1_quantity_unit.py::test_max_faults_exceeded_rejected` | PASSED |
  | `max_observers` | `test_xdl1_quantity_unit.py::test_max_observers_exceeded_rejected` | PASSED |
  | `max_metrics` | `test_xdl1_quantity_unit.py::test_max_metrics_exceeded_rejected` | PASSED |
  | `max_dependencies_per_step` | `test_xdl1_quantity_unit.py::test_max_dependencies_per_step_exceeded_rejected` | PASSED |
  | `max_flows` | `test_xdl1_quantity_unit.py::test_max_flows_exceeded_rejected` | PASSED |
  | `max_bindings` | `test_xdl1_quantity_unit.py::test_max_bindings_exceeded_rejected` | PASSED |
  | `max_resources` | `test_xdl1_quantity_unit.py::test_max_resources_exceeded_rejected` | PASSED |
  | `max_text_length` | `test_xdl1_quantity_unit.py::test_max_text_length_exceeded_rejected` | PASSED |
  | `max_limitations` | `test_xdl1_quantity_unit.py::test_max_limitations_exceeded_rejected` | PASSED |
  | `max_diagnostics` (fail-closed) | `test_xdl1_quantity_unit.py::test_max_diagnostics_exceeded_fails_closed` | PASSED |
  | `max_bytes_per_file` | `test_xdl1_quantity_unit.py::test_max_bytes_per_file_exceeded_rejected` | PASSED |
  | per-value parameter bound | `test_xdl1_quantity_unit.py::test_parameter_bound_exceeded_rejected` | PASSED |
  | non-positive limit constructor | `test_xdl1_quantity_unit.py::test_experiment_limits_nonpositive_raises_value_error` | PASSED |

  The validation-level duplicate negatives `test_per_payload_parameter_bound_exceeded_rejected_without_plan`,
  `test_total_compiled_parameter_bound_exceeded_rejected_without_plan`,
  `test_declared_core_parameter_bound_exceeded_rejected_without_plan` and
  `test_declared_limitation_bound_exceeded_rejected_without_plan` also PASSED.

No assertion was weakened, renamed, skipped, xfailed or deleted to obtain these passes. No assertion
failed during this stage.

## 5. Required hostile-input, no-side-effect and metamorphic coverage

The independent adversarial classes required by the admitted instructions are exercised at unit level
by the frozen 121 `XDL1-UNIT` cases and at validation level by the cases in §3. Representative exact
identifiers (module `tests/thesis_lite/xdl/…`):

| Required class | Representative exact cases | Observed outcome |
| --- | --- | --- |
| Unknown Profile / version / `schemaRef` / namespace / field | `test_xdl1_profile_unit.py::test_profile_absent_rejected`, `::test_profile_version_unsupported_rejected`, `::test_profile_schemaref_unsupported_rejected`, `::test_profile_unknown_namespace_rejected`, `::test_profile_unknown_field_rejected` | rejected, stable code, `plan is None` |
| Payload kind/duplication/target/absent | `test_xdl1_profile_unit.py::test_profile_payload_kind_mismatch_rejected`, `::test_profile_payload_duplicate_rejected`, `::test_profile_payload_target_mismatch_rejected`, `::test_profile_scenario_intent_absent_rejected` | rejected, `XDL1-PLAN-PROFILE-*` |
| Absent/ambiguous selection | `test_xdl1_selection_unit.py::test_system_missing_rejected`, `::test_system_ambiguous_rejected`, `::test_scenario_missing_rejected`, `::test_scenario_ambiguous_rejected`, `::test_deployment_ambiguous_rejected`, `::test_deployment_unbound_rejected` | rejected, `XDL1-PLAN-*-MISSING`/`-AMBIGUOUS`/`-UNBOUND` |
| Missing seed / parameter defects | `test_xdl1_quantity_unit.py::test_seed_missing_rejected`, `::test_seed_above_maximum_rejected`, `::test_parameter_duplicate_rejected`, `::test_parameter_value_type_mismatch_rejected`, `::test_parameter_bound_exceeded_rejected` | rejected, `XDL1-PLAN-SEED-*`/`-PARAMETER-*` |
| Non-finite / negative / overflow / unknown unit / imprecise tick | `test_xdl1_quantity_unit.py::test_quantity_nonfinite_rejected`, `::test_quantity_negative_rejected`, `::test_quantity_overflow_ticks_rejected`, `::test_time_unit_unknown_rejected`, `::test_time_precision_noninteger_tick_rejected` | rejected, `XDL1-PLAN-QUANTITY-*`/`-TIME-*` |
| Missing reference / pin / time mapping | `test_xdl1_time_unit.py::test_time_domain_reference_unresolved_rejected`, `::test_time_mapping_missing_rejected`, `test_xdl1_intent_unit.py::test_artifact_pin_missing_rejected`, `::test_artifact_reference_unresolved_rejected`, `::test_observer_unresolved_rejected` | rejected, no partial plan |
| Unknown fault/action, schedule ambiguity | `test_xdl1_intent_unit.py::test_fault_trigger_missing_rejected`, `::test_fault_duration_invalid_rejected`, `test_xdl1_order_unit.py::test_schedule_declared_order_ambiguity_rejected` | rejected, `XDL1-PLAN-FAULT-*`/`-SCHEDULE-AMBIGUOUS` |
| Dependency cycle / unresolved / self dependency | `test_xdl1_order_unit.py::test_dependency_cycle_rejected`, `::test_dependency_missing_rejected`, `::test_step_depends_on_self_rejected` | rejected, `XDL1-PLAN-DEPENDENCY-*` |
| Unsupported realization / delivery / retry | `test_xdl1_intent_unit.py::test_realization_physical_unsupported_rejected`, `::test_delivery_without_pinned_artifact_rejected`, `::test_retry_with_delivery_none_rejected` | rejected, no default applied |
| Incomplete metric linkage / unresolved observer | `test_xdl1_intent_unit.py::test_metric_link_incomplete_rejected`, `::test_observer_unresolved_rejected` | rejected, `XDL1-PLAN-METRIC-LINK-INCOMPLETE`/`-OBSERVER-UNRESOLVED` |
| Secret-bearing leaf, value not echoed | `test_xdl1_diagnostics_unit.py::test_secret_bearing_leaf_rejected_without_echo` | rejected, `XDL1-PLAN-SECRET-IN-PUBLIC-ARTIFACT`, value absent from output |
| Post-hash mutation and digest self-check | `test_xdl1_identity_unit.py::test_expected_input_digest_mismatch_rejected`, `::test_post_hash_mutation_detected`, `::test_digest_selfcheck_failure_rejected` | rejected, `XDL1-PLAN-INPUT-MUTATED`/`-DIGEST-SELFCHECK` |
| No side effect (file, network, thread, process, clock, locale, inputs) | `test_xdl1_side_effect_unit.py::test_compiler_opens_no_file_after_admission`, `::test_compiler_performs_no_network_access`, `::test_compiler_creates_no_process`, `::test_compiler_spawns_no_thread`, `::test_compiler_reads_no_ambient_clock`, `::test_compilation_independent_of_locale_and_timezone`, `::test_successful_compile_leaves_supplied_files_unchanged` | resolved plan, no side effect |
| Metamorphic: equal YAML/JSON semantic digest, input permutations, volatile-only difference | `test_xdl1_metamorphic_unit.py::test_yaml_and_json_equal_plan_bytes_and_digest`, `::test_resource_order_permutation_equal_plan_bytes`, `::test_payload_order_permutation_equal_plan_bytes`, `::test_volatile_run_envelope_does_not_change_plan_digest`, `::test_resource_revision_change_keeps_unrelated_identity` | equal canonical plan bytes/digest |
| Rejection returns no plan | `test_xdl1_diagnostics_unit.py::test_rejection_returns_no_plan`, `::test_result_is_valid_false_without_plan`, `::test_rejected_run_envelope_has_null_plan_digest` | `plan is None` |

Every listed case executes the real compiler path; no assertion was weakened, renamed, skipped, xfailed
or deleted to obtain a pass. No assertion failed during this stage.

## 6. Identifier-binding verification

Collected pytest node identifiers were compared with the frozen records in this stage:

| Check | Expected | Observed | Result |
| --- | --- | --- | --- |
| `XDL1-UNIT.test_ids` ⊆ collected, no missing | 121 | 121 collected, 0 missing | PASS |
| Unit record `unit_cases` union = `XDL1-UNIT.test_ids` | 121 | 121, set-equal | PASS |
| `XDL1-INTEGRATION.test_ids` ⊆ collected, no missing | 8 | 8 collected, 0 missing | PASS |
| `XDL1-VALIDATION.test_ids` ⊆ collected, no missing | 18 | 18 collected, 0 missing | PASS |
| Union of `XDL1-VS-01..07` `test_ids` = `XDL1-VALIDATION.test_ids` | 18 | set-equal | PASS |
| Every `XDL1-SR-001..019` covered by a scenario `validates` link | 19 | 19, 0 unvalidated | PASS |
| Total collected under `tests/thesis_lite/xdl` | 147 | 147 | PASS |

## 7. Determinism and semantic-identity evidence

* The compiler derives plan identity from the declared content only; run identifiers, wall-clock
  observations and source-byte provenance are excluded from the semantic digest. Equivalent YAML and
  JSON encodings, and resource/payload permutations, yield equal canonical plan bytes and digest
  (`test_yaml_and_json_equal_plan_bytes_and_digest`, `::test_resource_order_permutation_equal_plan_bytes`,
  `::test_payload_order_permutation_equal_plan_bytes`, `::test_volatile_run_envelope_does_not_change_plan_digest`).
* Source bytes remain separately reconstructible: each input resource carries a semantic digest and
  the supplied-file bytes are never mutated by a successful or rejected compile.
* Repeated end-to-end CLI runs over the five neutral fixtures produce the same plan digest
  `ccf08204181f47ae7868ed7b6795c1fb2ae2d6e0aeb04437000a1b4ab3988f7d` (23 sections); the text summary
  digest equals the JSON envelope plan digest. This digest differs from the rejected predecessor value
  `8c82b2f1627113c1ea84916242668d692610407ba7d41bbd96c2353fe44e06db` because the successor plan now
  carries the additional always-present `scope="system"` `components[]` entry required by
  `XDL1-DD-14`; it is stable run-to-run.

## 8. Completed trace

`engineering/trace/links.json` is the mutable current trace file (schema_version 1, project_id
`xverse-platform`, 3334 links). This stage:

* refreshed **only** the mutable code-endpoint `target_revision` hashes;
* preserved every link identity, relation, source, source revision and target byte-for-byte;
* added **no** new link and removed none.

Specifically, the 21 `implemented_by` `target_revision` values whose code endpoint is the mutable
current pointer `engineering/project.json` were refreshed to the current endpoint SHA-256
`3ad8a8b541431040082b64a0ed2756e3c374ea0ee7a2dc82212e6d0c3fbdfe84`:
`T034-L-0168`, `T035-L-0182`, `T035-L-0188`, `T036-L-0046`, `T036-L-0051`, `T036-L-0088`,
`T036-L-0093`, `T036-L-0110`, `T036-L-0115`, `T036-L-0121`, `T036-L-0127`, `T037-L-0074`,
`T037-L-0079`, `T037-L-0105`, `T037-L-0111`, `T038-L-0049`, `T038-L-0055`, `T038-L-0074`,
`T038-L-0104`, `T038-L-0109`, `T038-L-0125`. These links carry the previous revision
`b29433c2f8d3c2310a8cdcaf538548ff18a09aac1b0ed87c8c801682eb6824d0`, which predates the
requirements-stage current-pointer update; the scheduled refresh was explicitly assigned to this
stage. The reserialization was verified byte-identical apart from those 21 `target_revision` values.

Result: `core.validate_trace(root, "xverse-platform")` now returns `{"artifacts": 909, "links": 3334}`
(previously it aborted on the first stale `engineering/project.json` endpoint). All `XDL1` accepted
software requirements now carry `allocated_to`/`implemented_by`/`verified_by`; every `XDL1` unit
record carries its owning component, `decomposes_to`, `implemented_by`, `verified_by` and
`analyzed_by`; every scenario carries at least one `validates` link. No closed or promoted REF-002
parent is recorded.

### 8.1 Software → parent → design → code → test → validation trace

Each `XDL1-SR` is a bounded software allocation of exactly one original REF-002 parent anchor
(`disposition = allocated`); the parent text, provenance and disposition are preserved and no parent
is closed. Code endpoints are the accepted candidate sources; test endpoints are the unit and
validation case identifiers marshalled through the `XDL1-UNIT`/`XDL1-VALIDATION` measures.

| Software req | Parent (original ID) | Component | Unit | Code endpoint(s) | Unit cases | Validation scenario |
| --- | --- | --- | --- | --- | --- | --- |
| `XDL1-SR-001` | `XVE-SYS-0001` | `XDL1-SR-001-CMP` | `XDL1-SR-001-U` | `src/xverse_xdl/experiment_plan.py` | 10 | VS-01 |
| `XDL1-SR-002` | `XVE-SYS-0003` | `XDL1-SR-002-CMP` | `XDL1-SR-002-U` | `src/xverse_xdl/experiment_plan.py` | 5 | VS-01, VS-07 |
| `XDL1-SR-003` | `XVE-SYS-0005` | `XDL1-SR-003-CMP` | `XDL1-SR-003-U` | `src/xverse_xdl/experiment_plan.py` | 3 | VS-01 |
| `XDL1-SR-004` | `XVE-SYS-0006` | `XDL1-SR-004-CMP` | `XDL1-SR-004-U` | `src/xverse_xdl/experiment_plan.py` | 2 | VS-01, VS-05 |
| `XDL1-SR-005` | `XVE-SYS-0009` | `XDL1-SR-005-CMP` | `XDL1-SR-005-U` | `src/xverse_xdl/experiment_plan.py` | 6 | VS-01, VS-02 |
| `XDL1-SR-006` | `XVE-SYS-00014` | `XDL1-SR-006-CMP` | `XDL1-SR-006-U` | `src/xverse_xdl/experiment_plan.py` | 4 | VS-02, VS-06 |
| `XDL1-SR-007` | `XVE-SYS-0016` | `XDL1-SR-007-CMP` | `XDL1-SR-007-U` | `src/xverse_xdl/experiment_plan.py` | 5 | VS-01 |
| `XDL1-SR-008` | `XVE-SYS-0025` | `XDL1-SR-008-CMP` | `XDL1-SR-008-U` | `src/xverse_xdl/experiment_plan.py` | 2 | VS-01 |
| `XDL1-SR-009` | `XVE-SYS-0027` | `XDL1-SR-009-CMP` | `XDL1-SR-009-U` | `src/xverse_xdl/experiment_plan.py` | 2 | VS-01 |
| `XDL1-SR-010` | `XVE-SYS-0035` | `XDL1-SR-010-CMP` | `XDL1-SR-010-U` | `src/xverse_xdl/experiment_plan.py` | 2 | VS-01, VS-05 |
| `XDL1-SR-011` | `XVE-SYS-0037` | `XDL1-SR-011-CMP` | `XDL1-SR-011-U` | `src/xverse_xdl/experiment_plan.py` | 5 | VS-01, VS-03 |
| `XDL1-SR-012` | `XVE-SYS-0038` | `XDL1-SR-012-CMP` | `XDL1-SR-012-U` | `src/xverse_xdl/experiment_plan.py` | 3 | VS-01, VS-05, VS-07 |
| `XDL1-SR-013` | `XVE-SYS-0078` | `XDL1-SR-013-CMP` | `XDL1-SR-013-U` | `src/xverse_xdl/experiment_plan.py` | 4 | VS-02 |
| `XDL1-SR-014` | `XVE-SYS-0117` | `XDL1-SR-014-CMP` | `XDL1-SR-014-U` | `src/xverse_xdl/experiment_plan.py` | 14 | VS-02, VS-07 |
| `XDL1-SR-015` | `XVE-SYS-0118` | `XDL1-SR-015-CMP` | `XDL1-SR-015-U` | `src/xverse_xdl/experiment_plan.py` | 3 | VS-02, VS-05 |
| `XDL1-SR-016` | `XVE-SYS-0146` | `XDL1-SR-016-CMP` | `XDL1-SR-016-U` | `src/xverse_xdl/experiment_plan.py`, `src/xverse_xdl/cli.py`, `src/xverse_xdl/__init__.py` | 9 | VS-04 |
| `XDL1-SR-017` | `XVE-SYS-0237` | `XDL1-SR-017-CMP` | `XDL1-SR-017-U` | `src/xverse_xdl/experiment_plan.py`, `xdl/profiles/experiment-lite-v0.1.schema.json` | 10 | VS-02 |
| `XDL1-SR-018` | `XVE-SYS-0251` | `XDL1-SR-018-CMP` | `XDL1-SR-018-U` | `src/xverse_xdl/experiment_plan.py` | 10 | VS-03 |
| `XDL1-SR-019` | `XVE-SYS-0254` | `XDL1-SR-019-CMP` | `XDL1-SR-019-U` | `src/xverse_xdl/experiment_plan.py`, `xdl/profiles/experiment-lite-v0.1.schema.json` | 22 | VS-02, VS-06, VS-07 |

Test endpoints in the trace: `XDL1-UNIT` (121 cases, `tests/thesis_lite/xdl/test_xdl1_*_unit.py`),
`XDL1-VALIDATION` (18 cases, `tests/thesis_lite/xdl/test_xdl1_validation.py`), `XDL1-INTEGRATION`
(8 cases, `tests/thesis_lite/xdl/test_xdl1_integration.py`) and `XDL1-STATIC` (19 declaration-bound
static checks, no pytest discovery).

## 9. Prior-artifact preservation

* Every artifact hash recorded by `xdl1-requirements.json` (39), `xdl1-architecture.json` (21),
  `xdl1-unit_specification.json` (20), `xdl1-verification_design.json` (13),
  `xdl1-implementation.json` (26) and `xdl1-integration.json` (1) was re-hashed against the working
  tree: **120 checked, 0 mismatches**. No earlier stage output, historical record, accepted test or
  accepted schema was modified.
* The only mutable file changed by this stage is `engineering/trace/links.json` (21 code-endpoint hash
  refreshes, no link added/removed/retyped).
* No file under `src/xverse_xdl/**`, `xdl/**`, `tests/**`, `proto/**` or any protected path was
  modified by this stage.

## 10. Preliminary worker checks (local, not trusted evidence)

Environment: Python 3.11.16, pytest 8.4.2, `/usr/local/bin/python3`, working directory the candidate
checkout. Commands were read-only apart from pytest cache writes.

| Command | Result |
| --- | --- |
| `python3 -m pytest -q tests/thesis_lite/xdl` | `147 passed in 9.20s` (121 unit + 8 integration + 18 validation). |
| `python3 -m pytest -vv tests/thesis_lite/xdl/test_xdl1_validation.py` | `18 passed`; collected identifiers equal `XDL1-VALIDATION.test_ids` exactly. |
| `python3 -m pytest -vv tests/thesis_lite/xdl/test_xdl1_quantity_unit.py -k "bound or max_"` | `17 passed, 12 deselected` — every count-based bound negative including the total-scope case. |
| `python3 -m pytest -vv tests/thesis_lite/xdl/test_xdl1_validation.py -k "bound or system_core"` | `6 passed, 12 deselected` — the XDL1-VS-07 bound and projection cases. |
| `python3 -m pytest -q` (whole repository) | `297 passed in 22.44s`; no failure or error in the accepted loaders, catalog, lifecycle, CLI and C++ X-COM suites. |
| `python3 -m xverse_xdl experiment compile --profile-schema xdl/profiles/experiment-lite-v0.1.schema.json <5 neutral fixtures>` | exit `0`, one line `resolved plan ccf08204181f47ae7868ed7b6795c1fb2ae2d6e0aeb04437000a1b4ab3988f7d (23 sections)`. |
| `core.validate_trace(checkout, "xverse-platform")` | `{"artifacts": 909, "links": 3334}` (completed trace, no stale endpoint). |

These runs are the candidate's own checks. The trusted host owns the executable
`unit`/`static_analysis`/`integration`/`validation` commands, their discovery checks, the exact
candidate revision, and the assembled pinned `xverse-platform` target; this record does not present
its local runs as trusted evidence.

## 11. Limitations and open host obligations

* These local runs are not the trusted validation measure and are not whole-system or external
  evidence. A resolved plan proves declared-intent validation only — never artifact availability,
  executable readiness, runtime success, or delivery.
* The trusted policy must bind the `validation` measure to `XDL1-VALIDATION`, `unit` to `XDL1-UNIT`,
  `static_analysis` to `XDL1-STATIC`, and `integration` to the new `XDL1-INTEGRATION` record; without
  that binding the host gates fail closed rather than being papered over.
* Whole-system integration is defined only by the trusted `system_integration` contract
  (`mode = target_repository`) over `0c5e249621727b2d0041707de2661f0ed1e1ef23`; this candidate cannot
  inspect or edit that external policy. Only that assembled-target run is integration evidence.
* Independent read-only `internal_review` and terminal user acceptance are pending; nothing here
  constitutes acceptance. The predecessor findings are closed by executed candidate-local evidence,
  but their terminal closure belongs to that separate stage.
* `status: accepted` on `XDL1-SR-*`, `XDL1-SR-*`-CMP, `XDL1-SR-*`-U and the measure records is internal
  engineering intent. No REF-002 parent is closed, promoted or marked implemented, and no maturity
  classification beyond implemented/candidate-locally-validated is claimed.
* No scientific protocol value, threshold, tolerance, deadline, seed, margin or campaign parameter is
  defaulted, invented or narrowed; those remain caller inputs, bounded only by the finite platform
  library limits.
* Public-safe: this record uses repository-relative locators only and contains no secret, credential,
  host address, private source excerpt, or sensitive deployment detail.

## 12. Hand-off and model recommendation

Next stage: **documentation** — author `maintenance.md`, `implementation.md` and `reports/review-index.md`,
keeping runtime/readiness/certification claims absent and pointing the index at the later read-only
`internal-review.json`. The separate read-only `internal_review` and terminal acceptance follow.

Model recommendation: the pinned `deepseek-v4-flash` with **high** reasoning remains the most
cost-effective and only authorized route for the documentation stage, because it is deterministic
transcription of the frozen, already-reviewed artifacts into maintenance/usage prose; no stronger tier
is justified, and there is no new Terra/Luna/Sol/Astra engineering route in this package, no fallback,
and no model switch is claimed or performed.

Blocker: none. The trusted measure bindings, the assembled-target integration run, the read-only
internal review, and terminal acceptance remain external host/user obligations and are pending, not
failed.
