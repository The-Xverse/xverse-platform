# XDL Lite Phase 1 — verification and validation plan (successor)

| Field | Value |
| --- | --- |
| Feature | XDL1 (XDL Lite Phase 1 — offline declared experiment intent compilation) |
| Stage / role | verification_design (pre-code; repository-owned Spec Kit work-product workflow, ADR-0020) |
| Attempt | XDL1 attempt 1 successor; supersedes the rejected predecessor XDL1 verification draft, which is retained only as external failing review evidence |
| Revision | 1 |
| Date | 2026-10-01 |
| Admitted platform baseline revision | `0c5e249621727b2d0041707de2661f0ed1e1ef23` |
| Admitted thesis revision | `fe58918f9eaf2a6f39cdc9c93cfd4ce615ec84bf` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 (`XDL1-SR-001` … `XDL1-SR-019`) |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Component records | `engineering/architecture/components/XDL1-SR-001-CMP.json` … `XDL1-SR-019-CMP.json` |
| Unit records | `engineering/unit-specifications/XDL1-SR-001-U.json` … `XDL1-SR-019-U.json` |
| New measure records | `engineering/verification/measures/XDL1-{UNIT,INTEGRATION,VALIDATION,STATIC}.json` |
| New validation scenarios | `engineering/validation/scenarios/XDL1-VS-01.json` … `XDL1-VS-07.json` |
| Planned code trace (precode) | [`planned-trace.json`](planned-trace.json) |
| Classification | Public-safe engineering work product |
| Maturity | **Planned / target.** Design only. No source, schema, fixture, or test code exists, and no measure has executed. Nothing in this document is verification, integration, validation, runtime, readiness, compatibility, or delivery evidence. |

## 1. Purpose and scope

This plan freezes how Phase 1 XDL Lite will be verified, integrated, and validated, and it binds every
measure to exact pytest-discoverable test identifiers before any code is written. It covers **Phase 1
only**: an additive, versioned, neutral experiment Profile and a pure, side-effect-free resolved
experiment plan compiler over the accepted XDL loader, schema registry, semantic graph, normalizer,
derived catalog, lifecycle-plan, and C++ X-COM activation-plan contracts.

Out of scope and not verified here: runtime or legacy execution, artifact retrieval or availability,
oracle access, online learning, fallback routes, Argus/Maestro implementations, compatibility or parity
claims, production change, and any Phase 2+ capability.

Authority and admitted inputs are the exact read-only identities recorded in
[`requirements.md`](requirements.md) §1 (re-verified against the admitted manifest in this stage) plus
the local platform anchors consumed read-only. Authoritative thesis planning remains external; nothing
is duplicated into this repository.

### 1.1 Predecessor review evidence and successor obligation

The predecessor XDL1 attempt-1 candidate was hash-inventoried (2852 files) and independently reviewed
read-only; the reviewer returned `verdict: rework` with findings `XDL1-RVW-001` (total
`max_parameters` scope not enforced), `XDL1-RVW-002` (declared `System.spec.parameters` dropped) and
`XDL1-RVW-003` (no negative case for any count-based bound; `XDL1-PLAN-BOUND-EXCEEDED` untested).
Those exact rejected revisions are consumed read-only by content hash, never repaired in place.

This successor requirement/architecture/unit baseline already amends the affected acceptance criteria
and freezes the behaviour; this plan is the stage that must close `XDL1-RVW-003`'s evidence obligation
by binding the required negatives into the `XDL1-UNIT` and `XDL1-VALIDATION` measures (§3, §5.1, §7).

## 2. Verification strategy

XDL1 has an `engineered` assurance profile and a `generic-explicit-command` verification profile. Four
scoped measures are defined, all owned by this feature and bound by the trusted host policy to trusted
executions:

| Measure kind | Feature record | Exact test identifiers | Executed where |
| --- | --- | --- | --- |
| `unit` | `XDL1-UNIT` | 121 unit node identifiers (frozen by `unit-specifications.md` §7/§10) | candidate checkout |
| `static_analysis` | `XDL1-STATIC` | 19 declared static checks (`XDL1-SR-0nn-U-STATIC`) | candidate checkout |
| `integration` | `XDL1-INTEGRATION` | 8 real-consumer integration node identifiers | assembled pinned `xverse-platform` target |
| `validation` | `XDL1-VALIDATION` | 18 scenario node identifiers (the exact union of `XDL1-VS-01` … `XDL1-VS-07`) | candidate checkout and assembled target |

Rules that hold for every measure:

* A measure record's `id` is the feature-scoped identity (`XDL1-*`); its `kind` is the measure kind, so
  the trusted `bound_test_ids` binding resolves the record for the measure without rewriting the
  historical `unit`, `integration`, `validation`, and `static_analysis` records, which remain
  byte-unchanged under the protected `engineering/verification/measures/**` boundary.
* The record `test_ids` are the **exact** identifier set. The trusted execution must discover every one
  of them (`expected_test_ids` equality plus verbose discovery); a missing, renamed, or weakened
  identifier fails the measure rather than degrading it.
* Identifiers were frozen with no hyphen in the module path or function name, so the trusted
  normalization `test_id.replace("-", "_")` is a no-op and each identifier appears verbatim in verbose
  pytest output.
* No measure is satisfied by mocks, fixtures outside the target, source inspection alone, or a
  candidate-local self-report. Whole-system integration is defined only by the trusted policy
  `system_integration` contract (`mode = target_repository`).
* Static analysis is a repository static inspection over the additive scope (Python `ast` parse,
  JSON Schema 2020-12 meta-schema validation, additive-diff scope check). The 19
  `XDL1-STATIC` identifiers are declaration-bound static rules, not collected pytest tests; the
  `static_analysis` measure carries no pytest discovery.

### 2.1 Gate record bindings

The trusted, externally owned policy maps each measure kind to this feature's measure record and
executes the approved executable command; the worker cannot and does not inspect or edit that policy.
The binding contract this stage provides is:

| Trusted measure | Bound feature record | Bound record kind | Trusted evidence produced |
| --- | --- | --- | --- |
| `unit` | `XDL1-UNIT` | `unit` | unit measure record + bounded log in the trusted evidence root |
| `static_analysis` | `XDL1-STATIC` | `static_analysis` | static-analysis measure record + bounded log |
| `integration` | `XDL1-INTEGRATION` | `integration` | whole-system integration record carrying the `system_integration` identity |
| `validation` | `XDL1-VALIDATION` | `validation` | validation measure record + bounded log |

This is a documented external dependency, not an independent engineering decision: the identifiers and
kinds required by the binding are fixed by the admitted instructions and are realized in the four new
records. If the trusted policy does not bind these identities, the host gates fail closed; no
candidate-local artifact is presented as trusted evidence.

### 2.2 Evidence status of this stage

This stage **authors no verification evidence**. It records planned identifiers, scenarios, and trace
endpoints only. Trusted unit/static/integration/validation evidence, the assembled-target run, the
read-only internal review, and terminal acceptance are all pending host gates; the plan never reports
them as complete.

## 3. Unit verification (`XDL1-UNIT`)

The unit measure verifies the 121 frozen unit cases of `unit-specifications.md` §7, §8 and
§10 through the real compiler API. Exact identifiers are listed in Appendix A.2 and stored in
`engineering/verification/measures/XDL1-UNIT.json`.

| Planned module | Cases |
| --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py` | 6 |
| `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py` | 9 |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py` | 11 |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py` | 23 |
| `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py` | 5 |
| `tests/thesis_lite/xdl/test_xdl1_order_unit.py` | 8 |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py` | 10 |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py` | 29 |
| `tests/thesis_lite/xdl/test_xdl1_selection_unit.py` | 9 |
| `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py` | 7 |
| `tests/thesis_lite/xdl/test_xdl1_time_unit.py` | 4 |
| **Total** | **121** |

The successor set preserves all 102 predecessor identifiers verbatim and adds 19: three
`System.spec.parameters` projection cases (`XDL1-SR-002-U`), one limitation-count negative
(`XDL1-SR-012-U`), and fifteen count-based bound cases (`XDL1-SR-019-U`) including
`test_max_parameters_per_payload_scope_exceeded_rejected`,
`test_max_parameters_total_compiled_scope_exceeded_rejected`,
`test_max_parameters_declared_core_scope_exceeded_rejected` and the boundary case
`test_max_parameters_all_scopes_at_bound_accepted`. This is the unit-level closure of
`XDL1-RVW-001/002/003`.

Each unit record's `unit_cases` are bound by a `verified_by` link to `XDL1-UNIT`, and each unit record
is additionally bound by an `analyzed_by` link to `XDL1-STATIC` (see §6 and §8).

## 4. Integration verification (`XDL1-INTEGRATION`)

The 8 integration cases are authored by the implementation stage and executed by
the trusted integration measure **over the exact candidate assembled into the pinned xverse-platform
target**. They exercise the real admitted consumers without mocks; they perform no execution,
retrieval, or network activity.

| Exact identifier (module `tests/thesis_lite/xdl/test_xdl1_integration.py`) | What it proves |
| --- | --- |
| `test_real_loader_schema_registry_and_compiler_resolve_neutral_experiment` | The accepted loader, core schema registry, Profile schema catalog, semantics and normalizer feed `compile_experiment_plan` and yield one resolved plan over real neutral fixtures — no mocked gate. |
| `test_real_cli_experiment_compile_end_to_end_over_fixture_files` | The additive `xdl experiment compile` subcommand resolves real fixture files, exits `0`, and prints the frozen JSON envelope or the text summary. |
| `test_existing_loader_and_normalizer_compatible_on_accepted_examples` | `validate_files`/`validate_sources` over the accepted `xdl/examples/v1alpha1/**` examples keep their accepted resources and produce no new diagnostics. |
| `test_existing_catalog_consumer_compatible_on_normalized_resources` | The accepted derived catalog (`derive_catalog`) over normalized accepted resources keeps its entries and diagnostics unchanged. |
| `test_existing_xcom_activation_plan_consumer_compatible` | The accepted C++ X-COM activation-plan contract (`xcom_plan` compile over an accepted activation-plan fixture) produces an unchanged canonical plan digest; nothing is started. |
| `test_existing_lifecycle_plan_api_compatible_without_execution` | `build_lifecycle_plan` remains a pure planning API returning the accepted plan shape; no lifecycle action is performed. |
| `test_legacy_cli_validate_normalize_and_version_behaviour_preserved` | `xdl validate`, `xdl normalize`, and `xdl version` keep their accepted output and exit codes for existing inputs. |
| `test_rejected_compile_leaves_consumers_and_files_unchanged` | A rejected compile leaves every supplied file byte-identical and every existing consumer still functional; no partial plan or side effect is produced. |

Backward compatibility is therefore **asserted** rather than assumed, and the accepted C++ X-COM
boundary is only ever consumed read-only by an existing public entry point — it is never modified and
never invoked by the Phase 1 compiler.

## 5. Validation scenarios (`XDL1-VALIDATION`)

Seven intended-use scenarios are recorded under `engineering/validation/scenarios/`. Every scenario is
bound by `validates` links to the accepted software requirements it exercises, and every accepted
software requirement `XDL1-SR-001` … `019` is validated by at least one scenario.

| Scenario | Title | Validates | Test identifiers |
| --- | --- | --- | --- |
| `XDL1-VS-01` | Author compiles declared experiment intent into one canonical resolved plan | SR-001, SR-002, SR-003, SR-004, SR-005, SR-007, SR-008, SR-009, SR-010, SR-011, SR-012 | 2 |
| `XDL1-VS-02` | Integrator receives stable structured diagnostics and no side effect | SR-005, SR-006, SR-013, SR-014, SR-015, SR-017, SR-019 | 2 |
| `XDL1-VS-03` | Downstream consumer verifies versions and hashes without reparsing YAML | SR-011, SR-018 | 2 |
| `XDL1-VS-04` | Existing platform consumers and legacy CLI behaviour remain compatible | SR-016 | 2 |
| `XDL1-VS-05` | Declaration-only honesty: limitations, non-readiness and unsupported realization | SR-004, SR-010, SR-012, SR-015 | 2 |
| `XDL1-VS-06` | Explicit time domain and quantity/unit validation without inference | SR-006, SR-019 | 2 |
| `XDL1-VS-07` | Declared finite library bounds and System core-parameter projection (resolves XDL1-RVW-001/002/003) | SR-002, SR-012, SR-014, SR-019 | 6 |

Each scenario record carries `intended_use`, `expected`, `test_ids`, `validates`, and `environment`.
The union of scenario `test_ids` is exactly the `XDL1-VALIDATION` record `test_ids`
(18), so the trusted validation measure discovers every scenario case and no
scenario case is unbound.

### 5.1 `XDL1-VS-07` — declared bound scopes and System projection (`XDL1-RVW-001/002/003`)

| Exact identifier (module `tests/thesis_lite/xdl/test_xdl1_validation.py`) | Expected |
| --- | --- |
| `test_per_payload_parameter_bound_exceeded_rejected_without_plan` | a declared extension `parameterList` longer than `ExperimentLimits.max_parameters` is rejected with `XDL1-PLAN-BOUND-EXCEEDED`, `plan is None`, no side effect (scope 1) |
| `test_total_compiled_parameter_bound_exceeded_rejected_without_plan` | valid scenario-intent and step-intent declarations whose individual per-payload lists are each within `max_parameters` while the **total compiled** count exceeds it are rejected with `XDL1-PLAN-BOUND-EXCEEDED`, `plan is None`, no side effect (scope 2) |
| `test_declared_core_parameter_bound_exceeded_rejected_without_plan` | a declared `System`/`Component`.`spec.parameters[]` list longer than `max_parameters` is rejected with `XDL1-PLAN-BOUND-EXCEEDED`, `plan is None` (scope 3) |
| `test_declared_limitation_bound_exceeded_rejected_without_plan` | a declared fidelity-limitation count above `max_limitations` is rejected with `XDL1-PLAN-BOUND-EXCEEDED`, `plan is None` (`XDL1-SR-012`) |
| `test_parameter_counts_at_declared_bounds_compile_resolved_plan` | parameter counts exactly at each declared bound compile one resolved plan (boundary evidence) |
| `test_system_core_parameters_projected_without_drop_or_duplication` | the resolved plan carries exactly one `components[scope="system"]` entry whose `declaredParameters` contains every declared `System.spec.parameters[]` entry exactly once and no System parameter in a component-instance entry (`XDL1-RVW-002`) |

Scenario `XDL1-VS-07` therefore supplies the validation-level negative evidence required by
`detailed-design.md` §10.3 for **each** declared `max_parameters` scope, which closes the
`XDL1-RVW-003` review obligation at the validation measure, and the end-to-end positive evidence for
the `XDL1-RVW-002` System projection.

## 6. Static analysis (`XDL1-STATIC`)

The 19 declared static checks `XDL1-SR-001-U-STATIC` … `XDL1-SR-019-U-STATIC` fixed in
`unit-specifications.md` §10 are bound to the `static_analysis` measure by one `analyzed_by` link per
unit record. They establish, by bounded repository static inspection:

* lexical/structural rules — the frozen constants (`TIME_UNIT_TICKS`, `ExperimentLimits` defaults,
  `SUPPORTED_REALIZATION_CLASSES`, domain separators, phase/trigger ranks, `max_ticks`, the
  `nonReadiness` constant, the digest serialization options);
* absence rules — no new top-level XDL kind, no lifecycle/permit/provider import, no process/network/
  clock/locale/environment access, no artifact retrieval, no observer/metric/oracle call, no default
  seed, parameter, time mapping, delivery, or retry value;
* schema rules — the admitted Profile payload schema is valid JSON Schema 2020-12 with
  `additionalProperties: false`, closed kinds/consts, and finite bounds;
* scope rules — no change under `xdl/schemas/v1alpha1/**`, `src/xverse/xcom/**`, `proto/**`, accepted
  tests, or historical records, and `__all__` only grows.

## 7. Required negative, no-side-effect, and metamorphic coverage

Hostile-input, no-side-effect, and metamorphic behaviour is required by the admitted instructions and is
mapped to exact cases here. Mutation of an already-hashed input is covered explicitly.

| Required class | Representative exact cases | Expected |
| --- | --- | --- |
| Unknown Profile / version / `schemaRef` / namespace / field | `test_xdl1_profile_unit.py::test_profile_absent_rejected`, `::test_profile_version_unsupported_rejected`, `::test_profile_schemaref_unsupported_rejected`, `::test_profile_unknown_namespace_rejected`, `::test_profile_unknown_field_rejected` | reject, stable code, `plan is None` |
| Payload kind/duplication/target/absent | `test_xdl1_profile_unit.py::test_profile_payload_kind_mismatch_rejected`, `::test_profile_payload_duplicate_rejected`, `::test_profile_payload_target_mismatch_rejected`, `::test_profile_scenario_intent_absent_rejected` | reject, `XDL1-PLAN-PROFILE-*` |
| Absent/ambiguous selection | `test_xdl1_selection_unit.py::test_system_missing_rejected`, `::test_system_ambiguous_rejected`, `::test_scenario_missing_rejected`, `::test_scenario_ambiguous_rejected`, `::test_deployment_ambiguous_rejected`, `::test_deployment_unbound_rejected` | reject, `XDL1-PLAN-*-MISSING`/`-AMBIGUOUS`/`-UNBOUND` |
| Missing seed / parameter defects | `test_xdl1_quantity_unit.py::test_seed_missing_rejected`, `::test_seed_above_maximum_rejected`, `::test_parameter_duplicate_rejected`, `::test_parameter_value_type_mismatch_rejected`, `::test_parameter_bound_exceeded_rejected` | reject, `XDL1-PLAN-SEED-*`/`-PARAMETER-*` |
| Non-finite / negative / overflow / unknown unit / imprecise tick | `test_xdl1_quantity_unit.py::test_quantity_nonfinite_rejected`, `::test_quantity_negative_rejected`, `::test_quantity_overflow_ticks_rejected`, `::test_time_unit_unknown_rejected`, `::test_time_precision_noninteger_tick_rejected` | reject, `XDL1-PLAN-QUANTITY-*`/`-TIME-*` |
| **Declared count bound exceeded (all scopes)** | `test_xdl1_quantity_unit.py::test_max_parameters_per_payload_scope_exceeded_rejected`, `::test_max_parameters_total_compiled_scope_exceeded_rejected`, `::test_max_parameters_declared_core_scope_exceeded_rejected`, `::test_max_limitations_exceeded_rejected`, `::test_max_steps_exceeded_rejected`, `::test_max_faults_exceeded_rejected`, `::test_max_observers_exceeded_rejected`, `::test_max_metrics_exceeded_rejected`, `::test_max_dependencies_per_step_exceeded_rejected`, `::test_max_flows_exceeded_rejected`, `::test_max_bindings_exceeded_rejected`, `::test_max_resources_exceeded_rejected`, `::test_max_text_length_exceeded_rejected`; `test_xdl1_validation.py::test_per_payload_parameter_bound_exceeded_rejected_without_plan`, `::test_total_compiled_parameter_bound_exceeded_rejected_without_plan`, `::test_declared_core_parameter_bound_exceeded_rejected_without_plan`, `::test_declared_limitation_bound_exceeded_rejected_without_plan` | reject, `XDL1-PLAN-BOUND-EXCEEDED`, `plan is None`, no side effect; `::test_max_bytes_per_file_exceeded_rejected` expects the accepted `XDL-PARSE-TOO-LARGE` gate code |
| Declared bound boundary accepted | `test_xdl1_quantity_unit.py::test_max_parameters_all_scopes_at_bound_accepted`; `test_xdl1_validation.py::test_parameter_counts_at_declared_bounds_compile_resolved_plan` | one resolved plan |
| **Declared core System parameter projected, never dropped or duplicated** | `test_xdl1_intent_unit.py::test_system_core_parameters_projected_to_system_scope`, `::test_system_core_parameters_not_dropped_when_component_parameters_present`, `::test_system_scope_entry_always_present_with_empty_declared_parameters`; `test_xdl1_validation.py::test_system_core_parameters_projected_without_drop_or_duplication` | System parameter at `components[scope="system"].declaredParameters` exactly once |
| Missing reference / pin / time mapping | `test_xdl1_time_unit.py::test_time_domain_reference_unresolved_rejected`, `::test_time_mapping_missing_rejected`, `test_xdl1_intent_unit.py::test_artifact_pin_missing_rejected`, `::test_artifact_reference_unresolved_rejected`, `::test_observer_unresolved_rejected` | reject, no partial plan |
| Unknown fault/action and schedule ambiguity | `test_xdl1_intent_unit.py::test_fault_trigger_missing_rejected`, `::test_fault_duration_invalid_rejected`, `test_xdl1_order_unit.py::test_schedule_declared_order_ambiguity_rejected` | reject, `XDL1-PLAN-FAULT-*`/`-SCHEDULE-AMBIGUOUS` |
| Dependency cycle / unresolved dependency / self-dependency | `test_xdl1_order_unit.py::test_dependency_cycle_rejected`, `::test_dependency_missing_rejected`, `::test_step_depends_on_self_rejected` | reject, `XDL1-PLAN-DEPENDENCY-*` |
| Unsupported realization / delivery / retry | `test_xdl1_intent_unit.py::test_realization_physical_unsupported_rejected`, `::test_delivery_without_pinned_artifact_rejected`, `::test_retry_with_delivery_none_rejected` | reject, no default applied |
| Incomplete metric linkage / unresolved observer | `test_xdl1_intent_unit.py::test_metric_link_incomplete_rejected`, `::test_observer_unresolved_rejected` | reject, `XDL1-PLAN-METRIC-LINK-INCOMPLETE`/`-OBSERVER-UNRESOLVED` |
| Secret-bearing leaf, value not echoed | `test_xdl1_diagnostics_unit.py::test_secret_bearing_leaf_rejected_without_echo` | reject, `XDL1-PLAN-SECRET-IN-PUBLIC-ARTIFACT` |
| Post-hash mutation and digest self-check | `test_xdl1_identity_unit.py::test_expected_input_digest_mismatch_rejected`, `::test_post_hash_mutation_detected`, `::test_digest_selfcheck_failure_rejected` | reject, `XDL1-PLAN-INPUT-MUTATED`/`-DIGEST-SELFCHECK` |
| No side effect (file, network, thread, clock, locale, inputs) | `test_xdl1_side_effect_unit.py::test_compiler_opens_no_file_after_admission`, `::test_compiler_performs_no_network_access`, `::test_compiler_spawns_no_thread`, `::test_compiler_reads_no_ambient_clock`, `::test_compilation_independent_of_locale_and_timezone`, `::test_successful_compile_leaves_supplied_files_unchanged` | resolved plan, no side effect |
| Metamorphic: equal YAML/JSON semantic digest, input permutations, volatile-only difference | `test_xdl1_metamorphic_unit.py::test_yaml_and_json_equal_plan_bytes_and_digest`, `::test_resource_order_permutation_equal_plan_bytes`, `::test_payload_order_permutation_equal_plan_bytes`, `::test_volatile_run_envelope_does_not_change_plan_digest`, `::test_resource_revision_change_keeps_unrelated_identity` | equal canonical plan bytes/digest |
| Rejection returns no plan | `test_xdl1_diagnostics_unit.py::test_rejection_returns_no_plan`, `::test_result_is_valid_false_without_plan`, `::test_rejected_run_envelope_has_null_plan_digest` | `plan is None` |

Validation-level counterparts (real end-to-end, exact identifiers in Appendix A.4) include
`test_rejected_compile_has_no_side_effect_and_no_partial_plan`,
`test_equivalent_encodings_and_permutations_share_one_semantic_identity`,
`test_nonfinite_negative_overflow_and_unknown_units_rejected` and the five `XDL1-VS-07` cases.

## 8. Traceability

Bidirectional traceability is recorded in `engineering/trace/links.json` (additive only; all
3082 pre-existing links and endpoint revisions are preserved
byte-for-byte). This stage adds:

| Relation | Links | Count |
| --- | --- | --- |
| `verified_by` | `XDL1-SR-0nn` → `XDL1-UNIT` / `XDL1-INTEGRATION` / `XDL1-VALIDATION` | 57 |
| `verified_by` | `XDL1-SR-0nn-CMP` → `XDL1-UNIT` / `XDL1-INTEGRATION` / `XDL1-VALIDATION` | 57 |
| `verified_by` | `XDL1-SR-0nn-U` → `XDL1-UNIT` | 19 |
| `analyzed_by` | `XDL1-SR-0nn-U` → `XDL1-STATIC` | 19 |
| `validates` | `XDL1-VS-0n` → validated `XDL1-SR-0nn` | 31 |
| **New links** | | **183** |

Earlier stages own the other relations: `refines` (19, requirements stage), `allocated_to` (19,
architecture stage), `decomposes_to` (19, unit-specification stage), and `implemented_by`
(implementation stage).

| Requirement | Parent (original ID) | Component | Unit | Unit cases | Planned code endpoint(s) | Measures | Validation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `XDL1-SR-001` | `XVE-SYS-0001` | `XDL1-SR-001-CMP` | `XDL1-SR-001-U` | 10 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-01 |
| `XDL1-SR-002` | `XVE-SYS-0003` | `XDL1-SR-002-CMP` | `XDL1-SR-002-U` | 5 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-01, XDL1-VS-07 |
| `XDL1-SR-003` | `XVE-SYS-0005` | `XDL1-SR-003-CMP` | `XDL1-SR-003-U` | 3 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-01 |
| `XDL1-SR-004` | `XVE-SYS-0006` | `XDL1-SR-004-CMP` | `XDL1-SR-004-U` | 2 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-01, XDL1-VS-05 |
| `XDL1-SR-005` | `XVE-SYS-0009` | `XDL1-SR-005-CMP` | `XDL1-SR-005-U` | 6 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-01, XDL1-VS-02 |
| `XDL1-SR-006` | `XVE-SYS-00014` | `XDL1-SR-006-CMP` | `XDL1-SR-006-U` | 4 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-02, XDL1-VS-06 |
| `XDL1-SR-007` | `XVE-SYS-0016` | `XDL1-SR-007-CMP` | `XDL1-SR-007-U` | 5 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-01 |
| `XDL1-SR-008` | `XVE-SYS-0025` | `XDL1-SR-008-CMP` | `XDL1-SR-008-U` | 2 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-01 |
| `XDL1-SR-009` | `XVE-SYS-0027` | `XDL1-SR-009-CMP` | `XDL1-SR-009-U` | 2 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-01 |
| `XDL1-SR-010` | `XVE-SYS-0035` | `XDL1-SR-010-CMP` | `XDL1-SR-010-U` | 2 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-01, XDL1-VS-05 |
| `XDL1-SR-011` | `XVE-SYS-0037` | `XDL1-SR-011-CMP` | `XDL1-SR-011-U` | 5 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-01, XDL1-VS-03 |
| `XDL1-SR-012` | `XVE-SYS-0038` | `XDL1-SR-012-CMP` | `XDL1-SR-012-U` | 3 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-01, XDL1-VS-05, XDL1-VS-07 |
| `XDL1-SR-013` | `XVE-SYS-0078` | `XDL1-SR-013-CMP` | `XDL1-SR-013-U` | 4 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-02 |
| `XDL1-SR-014` | `XVE-SYS-0117` | `XDL1-SR-014-CMP` | `XDL1-SR-014-U` | 14 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-02, XDL1-VS-07 |
| `XDL1-SR-015` | `XVE-SYS-0118` | `XDL1-SR-015-CMP` | `XDL1-SR-015-U` | 3 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-02, XDL1-VS-05 |
| `XDL1-SR-016` | `XVE-SYS-0146` | `XDL1-SR-016-CMP` | `XDL1-SR-016-U` | 9 | `src/xverse_xdl/experiment_plan.py`, `src/xverse_xdl/cli.py`, `src/xverse_xdl/__init__.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-04 |
| `XDL1-SR-017` | `XVE-SYS-0237` | `XDL1-SR-017-CMP` | `XDL1-SR-017-U` | 10 | `src/xverse_xdl/experiment_plan.py`, `xdl/profiles/experiment-lite-v0.1.schema.json` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-02 |
| `XDL1-SR-018` | `XVE-SYS-0251` | `XDL1-SR-018-CMP` | `XDL1-SR-018-U` | 10 | `src/xverse_xdl/experiment_plan.py` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-03 |
| `XDL1-SR-019` | `XVE-SYS-0254` | `XDL1-SR-019-CMP` | `XDL1-SR-019-U` | 22 | `src/xverse_xdl/experiment_plan.py`, `xdl/profiles/experiment-lite-v0.1.schema.json` | UNIT, INTEGRATION, VALIDATION | XDL1-VS-02, XDL1-VS-06, XDL1-VS-07 |

### 8.1 Deferred code endpoints (precode)

`implemented_by` links cannot be added in this stage: the trusted `code_endpoint` contract resolves a
**real** file and binds its SHA-256 as the code-endpoint revision, and no implementation file exists
before the precode gate. The exact planned endpoints are therefore recorded outside the final trace in
[`planned-trace.json`](planned-trace.json) and in the table above. The implementation stage must add one
`implemented_by` link per requirement/component/unit to these endpoints with the exact source hashes,
and the validation stage refreshes only the mutable current code-endpoint hashes.

Consequently `validate_trace` cannot pass at precode (the accepted software requirements also lack
`implemented_by` coverage) and no completeness is claimed here. That is an expected, recorded
condition — not a blocker for this stage and not a substituted pass.

## 9. Environment, determinism, and evidence

* All cases run offline (Python 3.11+, `pytest`); no case starts a process, service, or device, opens a
  socket, or writes outside an explicitly requested CLI output path.
* Integration and the assembled-target parts of validation run only inside the trusted target checkout
  produced by the host assembly command against the pinned revision; candidate-local runs are
  preliminary worker checks, not integration evidence.
* Expected values are platform library bounds, frozen constants, and declared caller values. No
  scientific protocol number, threshold, tolerance, deadline, or campaign parameter appears in any
  expectation, and none is defaulted, invented, or narrowed.
* The trusted measures retain commands, tool versions, exit statuses, bounded logs, and hashes in the
  external evidence root; this candidate records planned identifiers and trace endpoints only.

## 10. Limitations and maturity

* Maturity of every item: **planned / target**. No implementation, verification, integration,
  validation, runtime, availability, readiness, compatibility, parity, or delivery claim is made, and
  none may be inferred from this plan. Source inspection does not demonstrate runtime success.
* `XDL1-SR-*` records remain `status: accepted` as internal engineering intent only; no REF-002 parent
  is closed, promoted, or marked implemented.
* `XDL1-RVW-001/002/003` are closed **at the plan level only** — the successor design freezes the
  behaviour and this stage binds exact identifiers and negatives. Satisfaction still requires the
  successor's own code and executed measures, owned by the implementation, integration and validation
  stages; nothing here is evidence that the behaviour exists.
* Known scheduled refresh (not this stage): 21 pre-existing `implemented_by` links target
  `engineering/project.json` with its previous hash; the validation stage owns exactly that mutable
  refresh.
* The trusted measure bindings and executable commands are external host policy; this stage provides
  the bound identities and cannot inspect or execute them.
* Integration, static, validation, and unit evidence are **pending host execution**; none exists yet.

## 11. Next step and model recommendation

Next stage: **implementation** — realize only the frozen design, create the exact
121 + 8 + 18 test identifiers, the neutral
fixtures, the admitted Profile schema, and the additive API/CLI, then add the `implemented_by` trace
endpoints with exact source hashes. Implementation may not start until the four design stages complete
and the precode gate passes.

Model recommendation: the pinned `deepseek-v4-flash` with **high** reasoning remains the most
cost-effective and only authorized route for that work, because it is deterministic transcription of
the frozen contracts and identifiers into code with precise, already-specified tests; no stronger tier
is justified and there is no new Terra/Luna/Sol/Astra engineering route in this package, no fallback,
and no model switch is claimed or performed.

Blocker: none at this stage. Material dependency for the host: the trusted policy must bind `unit`,
`static_analysis`, `integration`, and `validation` to `XDL1-UNIT`, `XDL1-STATIC`, `XDL1-INTEGRATION`,
and `XDL1-VALIDATION` respectively; without that binding the host gates fail closed.

---

## Appendix A — exact measure-bound test identifiers

Generated from the frozen unit records and the verification-design scenario definitions; the same
identifiers are stored machine-readably in the XDL1-UNIT, XDL1-INTEGRATION, XDL1-VALIDATION and
XDL1-STATIC measure records.

### A.1 XDL1-UNIT — per planned module

| Planned module | Cases |
| --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py` | 6 |
| `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py` | 9 |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py` | 11 |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py` | 23 |
| `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py` | 5 |
| `tests/thesis_lite/xdl/test_xdl1_order_unit.py` | 8 |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py` | 10 |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py` | 29 |
| `tests/thesis_lite/xdl/test_xdl1_selection_unit.py` | 9 |
| `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py` | 7 |
| `tests/thesis_lite/xdl/test_xdl1_time_unit.py` | 4 |
| **Total** | **121** |

### A.2 XDL1-UNIT — full identifier list (121)

* `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py::test_diagnostics_sorted_deterministically`
* `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py::test_error_diagnostic_has_stable_code_pointer_and_correction`
* `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py::test_rejected_run_envelope_has_null_plan_digest`
* `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py::test_rejection_returns_no_plan`
* `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py::test_result_is_valid_false_without_plan`
* `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py::test_secret_bearing_leaf_rejected_without_echo`
* `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_cli_experiment_compile_json_emits_plan`
* `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_cli_experiment_compile_rejection_exits_one`
* `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_cli_experiment_compile_text_emits_summary`
* `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_cli_invocation_error_exits_two`
* `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_cli_output_path_collision_exits_two`
* `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_compile_api_result_shape`
* `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_compile_sources_uses_real_loader`
* `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_init_all_is_additive_superset`
* `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_public_api_exports_present`
* `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_digest_selfcheck_failure_rejected`
* `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_expected_input_digest_mismatch_rejected`
* `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_input_semantic_digest_uses_contributing_set_only`
* `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_plan_body_excludes_volatile_fields`
* `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_plan_digest_self_consistent`
* `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_plan_matches_digest_for_emitted_plan`
* `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_post_hash_mutation_detected`
* `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_provenance_resources_sorted_and_complete`
* `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_resource_semantic_digest_excludes_source_map`
* `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_resource_semantic_digest_stable`
* `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_unrelated_extra_resource_does_not_change_plan`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_artifact_pin_missing_rejected`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_artifact_reference_unresolved_rejected`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_binding_keeps_logical_identity_distinct_from_realization`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_components_and_flows_map_to_existing_kinds`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_delivery_without_pinned_artifact_rejected`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_fault_duration_invalid_rejected`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_fault_schedule_fields_emitted`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_fault_trigger_missing_rejected`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_initial_conditions_and_acceptance_intent_recorded_verbatim`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_lifecycle_intent_fields_emitted`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_limitations_additive_do_not_widen_claim`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_limitations_merged_and_nonreadiness_present`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_metric_link_incomplete_rejected`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_metric_status_reference_only`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_no_new_top_level_resource_kind_emitted`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_observer_references_emitted`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_observer_unresolved_rejected`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_protocol_binding_recorded_as_declaration`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_realization_physical_unsupported_rejected`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_retry_with_delivery_none_rejected`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_system_core_parameters_not_dropped_when_component_parameters_present`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_system_core_parameters_projected_to_system_scope`
* `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_system_scope_entry_always_present_with_empty_declared_parameters`
* `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_payload_order_permutation_equal_plan_bytes`
* `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_resource_order_permutation_equal_plan_bytes`
* `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_resource_revision_change_keeps_unrelated_identity`
* `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_volatile_run_envelope_does_not_change_plan_digest`
* `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_yaml_and_json_equal_plan_bytes_and_digest`
* `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_dependency_cycle_rejected`
* `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_dependency_missing_rejected`
* `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_dependency_order_stable_tie_break`
* `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_lifecycle_order_key_phase_rank`
* `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_observer_and_metric_order_stable`
* `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_schedule_declared_order_ambiguity_rejected`
* `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_schedule_equal_ticks_tie_break_by_fault_id`
* `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_step_depends_on_self_rejected`
* `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_absent_rejected`
* `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_duplicate_rejected`
* `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_payload_duplicate_rejected`
* `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_payload_kind_mismatch_rejected`
* `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_payload_target_mismatch_rejected`
* `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_scenario_intent_absent_rejected`
* `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_schemaref_unsupported_rejected`
* `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_unknown_field_rejected`
* `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_unknown_namespace_rejected`
* `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_version_unsupported_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_experiment_limits_nonpositive_raises_value_error`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_bindings_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_bytes_per_file_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_dependencies_per_step_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_diagnostics_exceeded_fails_closed`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_faults_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_flows_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_limitations_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_metrics_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_observers_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_parameters_all_scopes_at_bound_accepted`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_parameters_declared_core_scope_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_parameters_per_payload_scope_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_parameters_total_compiled_scope_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_resources_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_steps_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_text_length_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_parameter_bound_exceeded_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_parameter_duplicate_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_parameter_value_type_mismatch_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_quantity_negative_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_quantity_nonfinite_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_quantity_overflow_ticks_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_seed_above_maximum_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_seed_missing_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_seed_negative_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_time_precision_noninteger_tick_rejected`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_time_unit_scaling_exact_ticks`
* `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_time_unit_unknown_rejected`
* `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_deployment_absent_compiles_with_null_deployment`
* `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_deployment_ambiguous_rejected`
* `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_deployment_unbound_rejected`
* `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_scenario_ambiguous_rejected`
* `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_scenario_identity_parameters_and_seed_emitted`
* `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_scenario_missing_rejected`
* `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_static_readiness_recorded_as_declaration_only`
* `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_system_ambiguous_rejected`
* `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_system_missing_rejected`
* `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_compilation_independent_of_locale_and_timezone`
* `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_compiler_creates_no_process`
* `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_compiler_opens_no_file_after_admission`
* `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_compiler_performs_no_network_access`
* `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_compiler_reads_no_ambient_clock`
* `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_compiler_spawns_no_thread`
* `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_successful_compile_leaves_supplied_files_unchanged`
* `tests/thesis_lite/xdl/test_xdl1_time_unit.py::test_time_domain_reference_unresolved_rejected`
* `tests/thesis_lite/xdl/test_xdl1_time_unit.py::test_time_domain_used_by_entries_recorded`
* `tests/thesis_lite/xdl/test_xdl1_time_unit.py::test_time_mapping_missing_rejected`
* `tests/thesis_lite/xdl/test_xdl1_time_unit.py::test_time_mapping_tolerance_ticks_recorded`

### A.3 XDL1-INTEGRATION — 8 real-consumer integration cases

* `tests/thesis_lite/xdl/test_xdl1_integration.py::test_existing_catalog_consumer_compatible_on_normalized_resources`
* `tests/thesis_lite/xdl/test_xdl1_integration.py::test_existing_lifecycle_plan_api_compatible_without_execution`
* `tests/thesis_lite/xdl/test_xdl1_integration.py::test_existing_loader_and_normalizer_compatible_on_accepted_examples`
* `tests/thesis_lite/xdl/test_xdl1_integration.py::test_existing_xcom_activation_plan_consumer_compatible`
* `tests/thesis_lite/xdl/test_xdl1_integration.py::test_legacy_cli_validate_normalize_and_version_behaviour_preserved`
* `tests/thesis_lite/xdl/test_xdl1_integration.py::test_real_cli_experiment_compile_end_to_end_over_fixture_files`
* `tests/thesis_lite/xdl/test_xdl1_integration.py::test_real_loader_schema_registry_and_compiler_resolve_neutral_experiment`
* `tests/thesis_lite/xdl/test_xdl1_integration.py::test_rejected_compile_leaves_consumers_and_files_unchanged`

### A.4 XDL1-VALIDATION — 18 scenario validation cases

* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_author_declared_experiment_yields_one_canonical_resolved_plan`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_declared_core_parameter_bound_exceeded_rejected_without_plan`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_declared_limitation_bound_exceeded_rejected_without_plan`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_declared_time_domain_and_mapping_recorded_without_inference`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_downstream_consumer_verifies_versions_and_hashes_without_reparsing_yaml`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_equivalent_encodings_and_permutations_share_one_semantic_identity`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_existing_cli_commands_remain_byte_compatible`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_existing_loader_normalizer_catalog_and_xcom_consumers_remain_compatible`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_integrator_receives_stable_structured_diagnostics_for_declared_defects`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_nonfinite_negative_overflow_and_unknown_units_rejected`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_parameter_counts_at_declared_bounds_compile_resolved_plan`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_per_payload_parameter_bound_exceeded_rejected_without_plan`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_plan_limitations_and_non_readiness_forbid_availability_claims`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_rejected_compile_has_no_side_effect_and_no_partial_plan`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_resolved_plan_records_seed_parameters_faults_observers_and_metrics`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_system_core_parameters_projected_without_drop_or_duplication`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_total_compiled_parameter_bound_exceeded_rejected_without_plan`
* `tests/thesis_lite/xdl/test_xdl1_validation.py::test_unsupported_physical_realization_rejected_without_default`

### A.5 XDL1-STATIC — 19 declared static checks

* `XDL1-SR-001-U-STATIC`
* `XDL1-SR-002-U-STATIC`
* `XDL1-SR-003-U-STATIC`
* `XDL1-SR-004-U-STATIC`
* `XDL1-SR-005-U-STATIC`
* `XDL1-SR-006-U-STATIC`
* `XDL1-SR-007-U-STATIC`
* `XDL1-SR-008-U-STATIC`
* `XDL1-SR-009-U-STATIC`
* `XDL1-SR-010-U-STATIC`
* `XDL1-SR-011-U-STATIC`
* `XDL1-SR-012-U-STATIC`
* `XDL1-SR-013-U-STATIC`
* `XDL1-SR-014-U-STATIC`
* `XDL1-SR-015-U-STATIC`
* `XDL1-SR-016-U-STATIC`
* `XDL1-SR-017-U-STATIC`
* `XDL1-SR-018-U-STATIC`
* `XDL1-SR-019-U-STATIC`
