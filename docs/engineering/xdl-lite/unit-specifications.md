# XDL Lite Phase 1 — unit specifications and planned unit cases (successor)

| Field | Value |
| --- | --- |
| Feature | XDL1 (XDL Lite Phase 1 — offline declared experiment intent compilation) |
| Stage / role | unit_specification (pre-code; repository-owned Spec Kit work-product workflow, ADR-0020) |
| Revision | 1 |
| Date | 2026-10-01 |
| Admitted platform baseline revision | `0c5e249621727b2d0041707de2661f0ed1e1ef23` |
| Admitted thesis revision | `fe58918f9eaf2a6f39cdc9c93cfd4ce615ec84bf` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 (`XDL1-SR-001` … `XDL1-SR-019`) |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Component records | `engineering/architecture/components/XDL1-SR-001-CMP.json` … `XDL1-SR-019-CMP.json` |
| Unit records | `engineering/unit-specifications/XDL1-SR-001-U.json` … `XDL1-SR-019-U.json` |
| Planned unit cases | 121 exact pytest-discoverable test identifiers |
| Classification | Public-safe engineering work product |
| Maturity | **Planned / target.** Specification only; no source, schema, fixture or test code exists in this stage. Nothing here is implementation, verification, runtime, readiness, compatibility or delivery evidence. |
| Revision status | **Successor revision.** Supersedes the rejected XDL1 attempt-1 unit specification (frozen predecessor candidate; independent read-only review `verdict: rework`, predecessor `review/internal-review.json` SHA-256 `b5ed14f18ae1e50d246deb2765215b11bdfd41c54dca0f7699325a1c9d12c2e4`). It closes the negative-evidence finding `XDL1-RVW-003` in this work product and binds the contract-level resolutions of `XDL1-RVW-001` and `XDL1-RVW-002` to named, independent unit cases. |

## 1. Purpose and method

This work product specifies the smallest verifiable units of the XDL1 compiler and their planned tests. It is a transcription of the frozen contracts in `requirements.md`, `architecture.md` and `detailed-design.md`; it adds no new behaviour, no scientific value and no implementation. One unit record per allocation component is used for the same reason as `architecture.md` §5: exactly one owning component per accepted software requirement keeps the later `decomposes_to`, `implemented_by`, `verified_by` and `analyzed_by` links unambiguous.

Method: for each of the 19 components the unit interface, state/concurrency, inputs, outputs, errors and invariants are fixed; every planned case is an independent, table-driven expected outcome (precondition, stimulus, expected) whose `id` is the exact pytest node identifier the implementation must create; adversarial cases and metamorphic equivalences are included explicitly; one static check per unit is planned. Test identifiers are frozen here so the verification-design, implementation and validation stages cannot drift.

Successor deltas against the predecessor unit specification:

* `XDL1-SR-002-U` gains three declared core-parameter projection cases that distinguish the System scope from the component scope and prove neither is dropped nor duplicated (resolves `XDL1-RVW-002`).
* `XDL1-SR-012-U` gains the merged-limitation-count negative case (resolves the limitation scope of `XDL1-RVW-003`).
* `XDL1-SR-019-U` gains the complete count-based `ExperimentLimits` negative surface, including the total compiled-parameter scope whose per-payload lists are each individually within the bound (resolves `XDL1-RVW-001` and `XDL1-RVW-003`). `XDL1-PLAN-BOUND-EXCEEDED` is no longer the only frozen diagnostic without negative coverage.
* All other predecessor cases are retained verbatim: no planned identifier was renamed, dropped or weakened.

## 2. Interface contract (frozen)

The units are realized inside one additive module plus its additive exposure. The public surface is exactly the `detailed-design.md` §13 surface; no unit introduces a signature, default, return shape or diagnostic code that differs from it.

| Interface | Kind | Frozen behaviour |
| --- | --- | --- |
| `compile_experiment_plan(resources, *, static_readiness=None, run_id=None, generated_at=None, expected_input_semantic_digests=None, limits=None)` | API | Pure compile of an immutable normalized resource set; returns `ExperimentPlanResult` and never raises for a declared defect |
| `compile_experiment_sources(sources, *, profile_schema_paths=(), …)` | API | Runs the accepted `validate_sources` then the pure core; no discovery |
| `compile_experiment_files(paths, *, profile_schema_paths=(), …)` | API | Runs the accepted `validate_files` then the pure core; reads only the supplied paths |
| `ExperimentLimits` | frozen dataclass | Library bounds of `detailed-design.md` §10.2; a non-positive field raises `ValueError` at construction |
| `ExperimentPlanResult` | frozen dataclass | `diagnostics: tuple[Diagnostic, ...]`, `plan: dict \| None`, `run: FrozenMap`, `is_valid` property |
| `resource_semantic_digest`, `canonical_plan_bytes`, `compute_plan_digest`, `plan_matches_digest`, `experiment_plan_status`, `plan_public_data` | helper API | Domain-separated canonical identity helpers; no I/O |
| `xdl experiment compile [--profile-schema PATH]… [--run-id ID] [--generated-at RFC3339] [--expect-input-digest NAME=SHA256]… [--format text\|json] [-o PLAN.json] RESOURCE…` | CLI | exit 0 resolved, exit 1 rejected, exit 2 invocation/internal; legacy `validate`/`normalize`/`version` behaviour byte-preserved |

The declared limit scopes are exactly `detailed-design.md` §10.2/§10.3: `max_parameters` is enforced over the per-payload scope, the total compiled-parameter scope `C_total` and the declared core-parameter scope, and every violation reuses the single frozen code `XDL1-PLAN-BOUND-EXCEEDED`.

## 3. State, concurrency and determinism

Single-threaded pure compilation; one bounded compile per call over immutable normalized resources; no shared mutable state, no worker, thread, coroutine, timer, or background work. Compiler-emitted structures are fresh and owned by the caller; the volatile run envelope is the only per-call value and never enters the plan body.

* The unit under test is a function call, never a process, service or daemon. There is no lifecycle, no background task, no retry loop and no shared cache.
* Inputs are immutable frozen values; outputs are fresh caller-owned structures. A rejected compile returns no plan object at all (`XDL1-INV-01`), including every bound rejection in §8.
* Determinism is invariantly cross-checked by the metamorphic cases in §9 and by `XDL1-INV-04`/`XDL1-INV-10`.

## 4. Unit inventory

| Unit | Owning component | Requirement | Cases | Planned test files |
| --- | --- | --- | --- | --- |
| `XDL1-SR-001-U` | `XDL1-SR-001-CMP` | `XDL1-SR-001` | 10 | `test_xdl1_intent_unit.py`, `test_xdl1_selection_unit.py` |
| `XDL1-SR-002-U` | `XDL1-SR-002-CMP` | `XDL1-SR-002` | 5 | `test_xdl1_intent_unit.py` |
| `XDL1-SR-003-U` | `XDL1-SR-003-CMP` | `XDL1-SR-003` | 3 | `test_xdl1_intent_unit.py`, `test_xdl1_order_unit.py`, `test_xdl1_side_effect_unit.py` |
| `XDL1-SR-004-U` | `XDL1-SR-004-CMP` | `XDL1-SR-004` | 2 | `test_xdl1_intent_unit.py` |
| `XDL1-SR-005-U` | `XDL1-SR-005-CMP` | `XDL1-SR-005` | 6 | `test_xdl1_quantity_unit.py` |
| `XDL1-SR-006-U` | `XDL1-SR-006-CMP` | `XDL1-SR-006` | 4 | `test_xdl1_time_unit.py` |
| `XDL1-SR-007-U` | `XDL1-SR-007-CMP` | `XDL1-SR-007` | 5 | `test_xdl1_intent_unit.py`, `test_xdl1_order_unit.py` |
| `XDL1-SR-008-U` | `XDL1-SR-008-CMP` | `XDL1-SR-008` | 2 | `test_xdl1_intent_unit.py` |
| `XDL1-SR-009-U` | `XDL1-SR-009-CMP` | `XDL1-SR-009` | 2 | `test_xdl1_intent_unit.py` |
| `XDL1-SR-010-U` | `XDL1-SR-010-CMP` | `XDL1-SR-010` | 2 | `test_xdl1_intent_unit.py` |
| `XDL1-SR-011-U` | `XDL1-SR-011-CMP` | `XDL1-SR-011` | 5 | `test_xdl1_identity_unit.py` |
| `XDL1-SR-012-U` | `XDL1-SR-012-CMP` | `XDL1-SR-012` | 3 | `test_xdl1_intent_unit.py`, `test_xdl1_quantity_unit.py` |
| `XDL1-SR-013-U` | `XDL1-SR-013-CMP` | `XDL1-SR-013` | 4 | `test_xdl1_order_unit.py` |
| `XDL1-SR-014-U` | `XDL1-SR-014-CMP` | `XDL1-SR-014` | 14 | `test_xdl1_diagnostics_unit.py`, `test_xdl1_identity_unit.py`, `test_xdl1_side_effect_unit.py` |
| `XDL1-SR-015-U` | `XDL1-SR-015-CMP` | `XDL1-SR-015` | 3 | `test_xdl1_intent_unit.py` |
| `XDL1-SR-016-U` | `XDL1-SR-016-CMP` | `XDL1-SR-016` | 9 | `test_xdl1_exposure_unit.py` |
| `XDL1-SR-017-U` | `XDL1-SR-017-CMP` | `XDL1-SR-017` | 10 | `test_xdl1_profile_unit.py` |
| `XDL1-SR-018-U` | `XDL1-SR-018-CMP` | `XDL1-SR-018` | 10 | `test_xdl1_diagnostics_unit.py`, `test_xdl1_identity_unit.py`, `test_xdl1_metamorphic_unit.py`, `test_xdl1_order_unit.py` |
| `XDL1-SR-019-U` | `XDL1-SR-019-CMP` | `XDL1-SR-019` | 22 | `test_xdl1_quantity_unit.py` |
| **Total** | | | **121** | |

All planned test files live under `tests/thesis_lite/xdl/`; `tests/thesis_lite/__init__.py` and `tests/thesis_lite/xdl/__init__.py` are planned package markers, and neutral fixtures live under `tests/thesis_lite/xdl/fixtures/`. No accepted test file is modified.

## 5. Errors and fail-closed semantics

Every unit returns `plan = None` whenever an error-severity diagnostic exists. The codes each unit can emit are copied from its owning component record and are the frozen `detailed-design.md` §9 catalogue; accepted `XDL-*` codes are produced by the reused gates before the XDL1 stages run. The successor adds `XDL1-PLAN-BOUND-EXCEEDED` to `XDL1-SR-012-U` (limitation count) and `XDL1-SR-019-U` (every count-based and quantity bound) exactly as `detailed-design.md` §10.2/§10.3 declares.

| Unit | Rejection codes |
| --- | --- |
| `XDL1-SR-001-U` | `XDL1-PLAN-SYSTEM-MISSING`; `XDL1-PLAN-SYSTEM-AMBIGUOUS`; `XDL1-PLAN-SCENARIO-MISSING`; `XDL1-PLAN-SCENARIO-AMBIGUOUS`; `XDL1-PLAN-DEPLOYMENT-AMBIGUOUS`; `XDL1-PLAN-DEPLOYMENT-UNBOUND` |
| `XDL1-SR-002-U` | `XDL-SCHEMA-UNSUPPORTED-KIND (accepted, reused)`; `XDL-SEMANTIC-COMPONENT-REFERENCE (accepted, reused)`; `XDL-SEMANTIC-FLOW-DIRECTION (accepted, reused)`; `XDL1-PLAN-PROFILE-PAYLOAD-KIND` |
| `XDL1-SR-003-U` | `XDL1-PLAN-DEPENDENCY-MISSING`; `XDL1-PLAN-DEPENDENCY-CYCLE`; `XDL1-PLAN-TIME-UNIT-UNKNOWN`; `XDL1-PLAN-TIME-PRECISION` |
| `XDL1-SR-004-U` | `XDL1-PLAN-REALIZATION-UNSUPPORTED`; `XDL1-PLAN-DEPLOYMENT-UNBOUND`; `XDL-SEMANTIC-BINDING-SYSTEM (accepted, reused)` |
| `XDL1-SR-005-U` | `XDL-SEMANTIC-EXTENSION-SCHEMA (accepted, reused) for a schema-invalid payload`; `XDL1-PLAN-PROFILE-PAYLOAD-ABSENT`; `XDL1-PLAN-SEED-MISSING`; `XDL1-PLAN-SEED-RANGE`; `XDL1-PLAN-PARAMETER-DUPLICATE`; `XDL1-PLAN-PARAMETER-VALUE-TYPE`; `XDL1-PLAN-PARAMETER-BOUND` |
| `XDL1-SR-006-U` | `XDL-SEMANTIC-TIME-MAPPING (accepted, reused)`; `XDL-SEMANTIC-TIME-DOMAIN-REFERENCE (accepted, reused)`; `XDL1-PLAN-TIME-DOMAIN-UNRESOLVED`; `XDL1-PLAN-TIME-MAPPING-MISSING` |
| `XDL1-SR-007-U` | `XDL1-PLAN-FAULT-TRIGGER-MISSING`; `XDL1-PLAN-FAULT-DURATION-INVALID`; `XDL1-PLAN-SCHEDULE-AMBIGUOUS`; `XDL1-PLAN-TIME-UNIT-UNKNOWN`; `XDL1-PLAN-TIME-DOMAIN-UNRESOLVED` |
| `XDL1-SR-008-U` | `XDL1-PLAN-OBSERVER-UNRESOLVED`; `XDL-SEMANTIC-SCENARIO-TARGET (accepted, reused)` |
| `XDL1-SR-009-U` | `XDL1-PLAN-METRIC-LINK-INCOMPLETE`; `XDL-SEMANTIC-OBSERVER (accepted, reused)` |
| `XDL1-SR-010-U` | `XDL1-PLAN-ARTIFACT-PIN-MISSING`; `XDL1-PLAN-ARTIFACT-REFERENCE-UNRESOLVED`; `XDL-BINDING-ARTIFACT-INTEGRITY (accepted, reused)` |
| `XDL1-SR-011-U` | `XDL1-PLAN-INPUT-MUTATED`; `XDL1-PLAN-DIGEST-SELFCHECK` |
| `XDL1-SR-012-U` | `XDL1-PLAN-BOUND-EXCEEDED (limitation count)` |
| `XDL1-SR-013-U` | `XDL1-PLAN-DEPENDENCY-CYCLE`; `XDL1-PLAN-DEPENDENCY-MISSING` |
| `XDL1-SR-014-U` | `XDL1-PLAN-INPUT-MUTATED`; `XDL1-PLAN-SECRET-IN-PUBLIC-ARTIFACT` |
| `XDL1-SR-015-U` | `XDL1-PLAN-REALIZATION-UNSUPPORTED`; `XDL1-PLAN-DELIVERY-UNSUPPORTED`; `XDL1-PLAN-RETRY-UNSUPPORTED`; `XDL-SEMANTIC-EXTENSION-SCHEMA (accepted, reused)` |
| `XDL1-SR-016-U` | `XDL1-PLAN-PROFILE-SCHEMAREF-UNSUPPORTED` |
| `XDL1-SR-017-U` | `XDL-SEMANTIC-PROFILE-MISSING (accepted, reused)`; `XDL-SEMANTIC-PROFILE-INCOMPATIBLE (accepted, reused)`; `XDL-SEMANTIC-PROFILE-SCHEMA-MISSING (accepted, reused)`; `XDL-SEMANTIC-EXTENSION-SCHEMA (accepted, reused)`; `XDL1-PLAN-PROFILE-ABSENT`; `XDL1-PLAN-PROFILE-DUPLICATE`; `XDL1-PLAN-PROFILE-VERSION-UNSUPPORTED`; `XDL1-PLAN-PROFILE-SCHEMAREF-UNSUPPORTED`; `XDL1-PLAN-PROFILE-PAYLOAD-DUPLICATE`; `XDL1-PLAN-PROFILE-TARGET-MISMATCH` |
| `XDL1-SR-018-U` | `XDL1-PLAN-SCHEDULE-AMBIGUOUS`; `XDL1-PLAN-DIGEST-SELFCHECK`; `XDL1-PLAN-QUANTITY-NONFINITE` |
| `XDL1-SR-019-U` | `XDL1-PLAN-TIME-UNIT-UNKNOWN`; `XDL1-PLAN-TIME-PRECISION`; `XDL1-PLAN-QUANTITY-NONFINITE`; `XDL1-PLAN-QUANTITY-NEGATIVE`; `XDL1-PLAN-QUANTITY-OVERFLOW`; `XDL1-PLAN-BOUND-EXCEEDED`; `XDL1-PLAN-PARAMETER-BOUND` |

## 6. Invariants

| Invariant | Statement (from `detailed-design.md` §14) | Units |
| --- | --- | --- |
| `XDL1-INV-01` | Any error diagnostic implies `plan is None` | `XDL1-SR-001-U`, `XDL1-SR-002-U`, `XDL1-SR-003-U`, `XDL1-SR-004-U`, `XDL1-SR-005-U`, `XDL1-SR-006-U`, `XDL1-SR-007-U`, `XDL1-SR-008-U`, `XDL1-SR-009-U`, `XDL1-SR-010-U`, `XDL1-SR-012-U`, `XDL1-SR-013-U`, `XDL1-SR-014-U`, `XDL1-SR-015-U`, `XDL1-SR-016-U`, `XDL1-SR-017-U` |
| `XDL1-INV-02` | No filesystem, network, registry, process, clock, locale or environment access | `XDL1-SR-001-U`, `XDL1-SR-002-U`, `XDL1-SR-003-U`, `XDL1-SR-004-U`, `XDL1-SR-005-U`, `XDL1-SR-006-U`, `XDL1-SR-007-U`, `XDL1-SR-008-U`, `XDL1-SR-009-U`, `XDL1-SR-010-U`, `XDL1-SR-012-U`, `XDL1-SR-013-U`, `XDL1-SR-014-U`, `XDL1-SR-015-U`, `XDL1-SR-016-U`, `XDL1-SR-017-U` |
| `XDL1-INV-03` | An emitted plan satisfies `plan_matches_digest(plan)` and `status == 'resolved'` | `XDL1-SR-003-U`, `XDL1-SR-007-U`, `XDL1-SR-008-U`, `XDL1-SR-009-U`, `XDL1-SR-011-U`, `XDL1-SR-012-U`, `XDL1-SR-014-U`, `XDL1-SR-015-U`, `XDL1-SR-018-U` |
| `XDL1-INV-04` | Equal declared content yields equal canonical plan bytes and plan digest | `XDL1-SR-011-U`, `XDL1-SR-013-U`, `XDL1-SR-018-U` |
| `XDL1-INV-05` | No scientific value is defaulted, invented or narrowed | `XDL1-SR-001-U`, `XDL1-SR-004-U`, `XDL1-SR-005-U`, `XDL1-SR-006-U`, `XDL1-SR-008-U`, `XDL1-SR-009-U`, `XDL1-SR-010-U`, `XDL1-SR-019-U` |
| `XDL1-INV-06` | `runId`/`generatedAt`/`sourceByteDigests` never appear in the plan body | `XDL1-SR-011-U`, `XDL1-SR-013-U`, `XDL1-SR-018-U`, `XDL1-SR-019-U` |
| `XDL1-INV-07` | Existing public APIs, schemas, diagnostics and CLI behaviour are unchanged | `XDL1-SR-016-U` |
| `XDL1-INV-08` | `nonReadiness` and declared `limitations` are present and truthful | `XDL1-SR-010-U`, `XDL1-SR-012-U` |
| `XDL1-INV-09` | Only generic platform vocabulary appears | `XDL1-SR-002-U`, `XDL1-SR-017-U` |
| `XDL1-INV-10` | Every emitted array is in the frozen order and every quantity is within `ExperimentLimits` | `XDL1-SR-001-U`, `XDL1-SR-002-U`, `XDL1-SR-003-U`, `XDL1-SR-004-U`, `XDL1-SR-005-U`, `XDL1-SR-006-U`, `XDL1-SR-007-U`, `XDL1-SR-008-U`, `XDL1-SR-009-U`, `XDL1-SR-010-U`, `XDL1-SR-012-U`, `XDL1-SR-013-U`, `XDL1-SR-014-U`, `XDL1-SR-015-U`, `XDL1-SR-016-U`, `XDL1-SR-017-U`, `XDL1-SR-019-U` |
| `XDL1-INV-11` | A plan is emitted only when all three `max_parameters` scopes hold; a violation yields `plan is None` and `XDL1-PLAN-BOUND-EXCEEDED` | `XDL1-SR-019-U` |
| `XDL1-INV-12` | An emitted plan carries exactly one `components[scope="system"]` entry projecting every declared `System.spec.parameters[]` entry, with no System parameter in a component entry | `XDL1-SR-002-U` |

`XDL1-INV-11` is exercised by the `XDL1-SR-019-U` at-bound positive case and the three scope negatives; `XDL1-INV-12` is exercised by the three `XDL1-SR-002-U` projection cases.

## 7. Table-driven expected outcomes and planned test identifiers

Each row is one independent unit case: a fresh precondition, one stimulus and one exact expected outcome. The `id` column is the exact pytest node identifier. No expectation contains a thesis protocol number; all numeric values are platform library bounds, frozen constants or declared caller values.

### 7.1 `XDL1-SR-001-U` — Declared Scenario selection and binding

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_system_missing_rejected` | normalized set with zero System resources | compile_experiment_plan(resources) | rejected; XDL1-PLAN-SYSTEM-MISSING; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_system_ambiguous_rejected` | normalized set with two System resources | compile_experiment_plan(resources) | rejected; XDL1-PLAN-SYSTEM-AMBIGUOUS; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_scenario_missing_rejected` | one System and no Scenario referencing it | compile_experiment_plan(resources) | rejected; XDL1-PLAN-SCENARIO-MISSING; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_scenario_ambiguous_rejected` | two Scenarios that both reference the selected System | compile_experiment_plan(resources) | rejected; XDL1-PLAN-SCENARIO-AMBIGUOUS; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_deployment_ambiguous_rejected` | two Deployments referencing the selected System | compile_experiment_plan(resources) | rejected; XDL1-PLAN-DEPLOYMENT-AMBIGUOUS; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_deployment_unbound_rejected` | exactly one Deployment present but the selected Scenario declares no deploymentRef to it | compile_experiment_plan(resources) | rejected; XDL1-PLAN-DEPLOYMENT-UNBOUND; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_deployment_absent_compiles_with_null_deployment` | no Deployment in the closed set | compile_experiment_plan(resources) | resolved plan; selection.deployment is null, bindings == [] and no error diagnostic |
| `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_scenario_identity_parameters_and_seed_emitted` | admitted valid set with declared seed and two ordered parameters | compile_experiment_plan(resources) | plan.selection.scenario identity equals the declared Scenario; seed.value/unitSemantics and parameters list equal the declared payload in order |
| `tests/thesis_lite/xdl/test_xdl1_selection_unit.py::test_static_readiness_recorded_as_declaration_only` | valid set with a Deployment carrying declared artifacts | compile_experiment_plan(resources, static_readiness=ValidationResult.readiness) | plan.selection.staticReadiness equals the accepted declaration-only readiness map with values in {Ready,NotReady,NotEvaluated}; plan.nonReadiness is present |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_initial_conditions_and_acceptance_intent_recorded_verbatim` | Scenario declaring initialConditions and acceptanceIntent | compile_experiment_plan(resources) | plan.initialConditions equals the declared object verbatim and plan.acceptanceIntent equals the declared value or null when absent |

### 7.2 `XDL1-SR-002-U` — Logical system/component/flow intent mapped to existing kinds

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_components_and_flows_map_to_existing_kinds` | System with componentInstances, interfaces, endpoints and flows | compile_experiment_plan(resources) | components[] and flows[] reference existing System/Component entity identities and declared field values only; no new kind string is emitted |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_no_new_top_level_resource_kind_emitted` | any valid closed resource set | compile_experiment_plan(resources) | the plan contains no kind outside the five accepted v1alpha1 kinds; ProtocolBinding/Realization appear only inside bindings and add no top-level kind |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_system_core_parameters_projected_to_system_scope` | valid set whose System declares spec.parameters[] holding the single id 'loop-count' and whose referenced Component declares spec.parameters[] holding the single id 'nominal-rate' | compile_experiment_plan(resources) | components[0].scope == 'system' with instanceId, componentRef and nodeId all null and declaredParameters listing exactly [loop-count]; the components[scope='component-instance'] entry for that Component lists exactly [nominal-rate]; 'loop-count' does not occur in any component-instance declaredParameters and 'nominal-rate' does not occur in the System entry |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_system_core_parameters_not_dropped_when_component_parameters_present` | System declaring two core parameters and one referenced Component declaring one core parameter | compile_experiment_plan(resources) | the multiset of ids across components[].declaredParameters equals exactly the declared System core parameter ids plus the declared Component core parameter ids (3 ids), each occurring once; no declared core parameter is silently omitted and none is duplicated across scopes |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_system_scope_entry_always_present_with_empty_declared_parameters` | System that declares no spec.parameters[] and no spec.models[] but references one Component that declares a core parameter | compile_experiment_plan(resources) | components[0] is always the scope='system' entry emitted first with declaredParameters == [] and modelRefs == [], followed by the component-instance entry; the plan shape is stable and the empty System projection invents no parameter |

### 7.3 `XDL1-SR-003-U` — Declared lifecycle intent without lifecycle execution

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_lifecycle_intent_fields_emitted` | valid step-intent payloads with phase, dependsOn, duration and typed parameters | compile_experiment_plan(resources) | each lifecycleIntent element carries stepId, actionKind, targetRef, timeDomainId, phase, schedule{declaredAt,declaredUnit,atTicks,tolerance}, dependsOn, duration and parameters |
| `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_lifecycle_order_key_phase_rank` | steps in one domain and equal ticks with phases prepare/start/observe/stop/cleanup declared out of order | compile_experiment_plan(resources) | lifecycleIntent ordered by (timeDomainId, atTicks, phaseRank, stepId) with the frozen phase rank |
| `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_compiler_creates_no_process` | subprocess.Popen, subprocess.run and os.system monkeypatched to raise | compile_experiment_plan(resources) | a resolved plan is returned and no process is created |

### 7.4 `XDL1-SR-004-U` — Deployment realization binding resolution

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_protocol_binding_recorded_as_declaration` | realization-intent protocolBinding with standardRef, bindingKind, compatibility and limitations | compile_experiment_plan(resources) | bindings[].protocolBinding records the declared values verbatim; no standard, converter or endpoint is resolved |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_binding_keeps_logical_identity_distinct_from_realization` | Deployment binding with logicalRef, realizationClass, targetId and artifacts | compile_experiment_plan(resources) | bindings[] records logicalRef identity and collection separately from realizationClass/targetId/artifactRefs; no physical resolution or handle is produced |

### 7.5 `XDL1-SR-005-U` — Explicit declared parameters and seed

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_seed_missing_rejected` | normalized scenario-intent payload that omits seed | compile_experiment_plan(resources) | rejected; XDL1-PLAN-SEED-MISSING; plan is None; no seed default is invented |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_seed_above_maximum_rejected` | seed value max_seed + 1 (9007199254740992) | compile_experiment_plan(resources) on the normalized path | rejected; XDL1-PLAN-SEED-RANGE; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_seed_negative_rejected` | seed value -1 | compile_experiment_plan(resources) on the normalized path | rejected; XDL1-PLAN-SEED-RANGE; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_parameter_duplicate_rejected` | scenario-intent.parameters containing id 'gain' twice | compile_experiment_plan(resources) | rejected; XDL1-PLAN-PARAMETER-DUPLICATE; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_parameter_value_type_mismatch_rejected` | parameter with valueType 'integer' and a JSON string value | compile_experiment_plan(resources) on the normalized path | rejected; XDL1-PLAN-PARAMETER-VALUE-TYPE; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_parameter_bound_exceeded_rejected` | number parameter with magnitude 1e16 (> max_number_magnitude 1e15) | compile_experiment_plan(resources) | rejected; XDL1-PLAN-PARAMETER-BOUND; plan is None |

### 7.6 `XDL1-SR-006-U` — Explicit time-domain reference

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_time_unit.py::test_time_domain_reference_unresolved_rejected` | fault-intent timeDomainId naming a domain not declared by the System | compile_experiment_plan(resources) | rejected; XDL1-PLAN-TIME-DOMAIN-UNRESOLVED; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_time_unit.py::test_time_mapping_missing_rejected` | deployment/observation using a second time domain with no declared Scenario timeMapping | compile_experiment_plan(resources) and the loader entry point | rejected with no plan; the loader path surfaces the accepted XDL-SEMANTIC-TIME-MAPPING first and the normalized path surfaces XDL1-PLAN-TIME-MAPPING-MISSING |
| `tests/thesis_lite/xdl/test_xdl1_time_unit.py::test_time_mapping_tolerance_ticks_recorded` | declared tolerance 1 ms between two domains | compile_experiment_plan(resources) | timeMappings entry records value 1, unit 'ms' and ticks 1000000 with declaredIndex preserved |
| `tests/thesis_lite/xdl/test_xdl1_time_unit.py::test_time_domain_used_by_entries_recorded` | steps, observers, flows and faults declared against two domains | compile_experiment_plan(resources) | each timeDomains[].usedBy contains exactly the declared using entries in order (step/observer/flow/fault prefixes) with no inference |

### 7.7 `XDL1-SR-007-U` — Deterministic intended fault schedule

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_fault_schedule_fields_emitted` | valid fault-intent payload with time trigger, domain, duration and parameters | compile_experiment_plan(resources) | each faultSchedule element carries entryId fault:<id>, faultKind verbatim, targetRef, collection, activation, recovery, maturity, timeDomainId, trigger, duration and parameters |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_fault_trigger_missing_rejected` | fault-intent payload with no trigger field | compile_experiment_plan(resources) | rejected; XDL1-PLAN-FAULT-TRIGGER-MISSING; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_fault_duration_invalid_rejected` | fault-intent payload that omits duration | compile_experiment_plan(resources) | rejected; XDL1-PLAN-FAULT-DURATION-INVALID; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_schedule_declared_order_ambiguity_rejected` | two faults declaring the same declared-order trigger value | compile_experiment_plan(resources) | rejected; XDL1-PLAN-SCHEDULE-AMBIGUOUS; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_schedule_equal_ticks_tie_break_by_fault_id` | two time-triggered faults with equal canonical ticks in one domain | compile_experiment_plan(resources) | accepted; faultSchedule ordered by faultId ascending with no diagnostic (equal ticks are not ambiguous) |

### 7.8 `XDL1-SR-008-U` — Observer intent references without observation execution

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_observer_references_emitted` | declared Scenario observers with targetRef, samplingIntent, payloadSchema, unitSemantics and evidenceSinkRef | compile_experiment_plan(resources) | each observers element carries observerId, targetRef, collection, timeDomainId, samplingIntent, payloadPolicy{payloadSchema,unitSemantics} and evidenceSinkRef; nothing is invoked |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_observer_unresolved_rejected` | observer targetRef naming an element that does not exist | compile_experiment_plan(resources) | rejected; XDL1-PLAN-OBSERVER-UNRESOLVED; plan is None |

### 7.9 `XDL1-SR-009-U` — Metric intent references without evaluation

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_metric_link_incomplete_rejected` | metric with an empty observerIds list / no resolving time or unit link | compile_experiment_plan(resources) | rejected; XDL1-PLAN-METRIC-LINK-INCOMPLETE; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_metric_status_reference_only` | valid metric linked to a declared observer and time domain | compile_experiment_plan(resources) | metrics[].status is exactly 'reference-only'; no metric value or oracle result appears anywhere in the plan |

### 7.10 `XDL1-SR-010-U` — Model and artifact binding references recorded as references only

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_artifact_pin_missing_rejected` | in-scope Deployment binding referencing a declared artifact without an immutable digest | compile_experiment_plan(resources) | rejected; XDL1-PLAN-ARTIFACT-PIN-MISSING; plan is None; nothing is retrieved |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_artifact_reference_unresolved_rejected` | binding artifactIds naming an artifact that is not declared by the Deployment | compile_experiment_plan(resources) | rejected; XDL1-PLAN-ARTIFACT-REFERENCE-UNRESOLVED; plan is None |

### 7.11 `XDL1-SR-011-U` — Declared input provenance and independent versions

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_resource_semantic_digest_stable` | one normalized resource hashed twice and once after canonical key permutation | resource_semantic_digest(resource) | all three digests are equal 64-hex sha256 values |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_resource_semantic_digest_excludes_source_map` | the same declared content loaded from two file names with differing sourceMap locations | resource_semantic_digest(resource) | both digests are equal, proving sourceMap, file name and source format are excluded |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_input_semantic_digest_uses_contributing_set_only` | contributing resources plus one unrelated valid resource | compile_experiment_plan(resources) | provenance.inputSemanticDigest equals the digest over the ordered contributing set only; the unrelated resource is absent |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_unrelated_extra_resource_does_not_change_plan` | the same valid set with and without an unrelated valid Component | compile_experiment_plan(resources) twice | canonical_plan_bytes and plan.digest are byte-equal across both runs |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_provenance_resources_sorted_and_complete` | valid set with System, Deployment, Scenario, Profile and referenced Components | compile_experiment_plan(resources) | provenance.resources contains exactly the contributing set sorted by (apiVersion, kind, namespace, name, version) with a sha256 semanticDigest each |

### 7.12 `XDL1-SR-012-U` — Declared fidelity limitations and non-readiness statement

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_limitations_merged_and_nonreadiness_present` | resources carrying metadata.provenance.limitations plus scenario-intent.fidelityLimitations | compile_experiment_plan(resources) | plan.limitations is the merged declared set within max_limitations; plan.nonReadiness carries the frozen statement, claim 'declared-intent-validation-only' and all four false flags |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_limitations_additive_do_not_widen_claim` | valid set compiled with and without one extra declared fidelity limitation | compile_experiment_plan(resources) twice | the extra limitation is additive; nonReadiness flags stay false and no availability, readiness, compatibility or parity claim is added |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_limitations_exceeded_rejected` | declared metadata.provenance.limitations plus scenario-intent.fidelityLimitations whose merged declared set has 3 distinct entries and limits=ExperimentLimits(max_limitations=2) | compile_experiment_plan(resources, limits=ExperimentLimits(max_limitations=2)) | rejected; XDL1-PLAN-BOUND-EXCEEDED naming the merged limitation-count scope; plan is None; no resolved plan is emitted with limitations silently dropped and no limitation is truncated into a resolved plan |

### 7.13 `XDL1-SR-013-U` — Deterministic dependency order and cycle rejection

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_dependency_order_stable_tie_break` | two independent component instances declared in opposite resource order across two runs | compile_experiment_plan(resources) twice with permuted input order | both runs emit an identical dependencyOrder ordered by ascending key (kindRank, declaredIndex, id) |
| `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_dependency_cycle_rejected` | System flows forming a component-instance cycle | compile_experiment_plan(resources) | rejected; XDL1-PLAN-DEPENDENCY-CYCLE with the offending node ids in related; no partial order and no plan |
| `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_dependency_missing_rejected` | step-intent dependsOn naming a step that is not declared | compile_experiment_plan(resources) | rejected; XDL1-PLAN-DEPENDENCY-MISSING; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_step_depends_on_self_rejected` | step-intent dependsOn naming its own step id | compile_experiment_plan(resources) | rejected; XDL1-PLAN-DEPENDENCY-CYCLE; plan is None |

### 7.14 `XDL1-SR-014-U` — Pure offline no-side-effect contract

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_expected_input_digest_mismatch_rejected` | a caller-supplied expected_input_semantic_digests entry that differs from the computed value | compile_experiment_plan(resources, expected_input_semantic_digests=...) | rejected; XDL1-PLAN-INPUT-MUTATED; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_post_hash_mutation_detected` | a normalized input mutated after its digest was first computed at entry | compile_experiment_plan(resources) with the entry digest captured and the value changed before finalization | rejected; XDL1-PLAN-INPUT-MUTATED; plan is None and no stale digest is emitted |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_digest_selfcheck_failure_rejected` | an assembled plan whose digest does not match the recomputed canonical digest | compile_experiment_plan(resources) with the digest assembly path exercised so the self-check fails | rejected; XDL1-PLAN-DIGEST-SELFCHECK; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py::test_rejection_returns_no_plan` | a set carrying one of each declared rejection defect | compile_experiment_plan(resources) | ExperimentPlanResult.plan is None for every defect and no partial, placeholder or executable handle is returned |
| `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py::test_error_diagnostic_has_stable_code_pointer_and_correction` | a rejected set | compile_experiment_plan(resources) | every diagnostic has a stable XDL1-PLAN-* or accepted XDL-* code, a ValidationGate, severity error, a JSON pointer and a non-empty correction |
| `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py::test_secret_bearing_leaf_rejected_without_echo` | a declared text/parameter value matching the credential pattern | compile_experiment_plan(resources) | rejected; XDL1-PLAN-SECRET-IN-PUBLIC-ARTIFACT; the offending value is not echoed in any diagnostic message |
| `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py::test_result_is_valid_false_without_plan` | a rejected set | compile_experiment_plan(resources) | ExperimentPlanResult.is_valid is False and plan is None |
| `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py::test_rejected_run_envelope_has_null_plan_digest` | a rejected set | compile_experiment_plan(resources) | the volatile run envelope records status 'rejected' and planDigest None while the plan body does not exist |
| `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_compiler_opens_no_file_after_admission` | normalized resources already in memory and builtins.open monkeypatched to raise | compile_experiment_plan(resources) | a resolved plan is returned and no file is opened (no OSError surfaces) |
| `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_compiler_performs_no_network_access` | socket.socket monkeypatched to raise | compile_experiment_plan(resources) | a resolved plan is returned and no socket/registry/network call occurs |
| `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_compiler_spawns_no_thread` | threading.Thread and multiprocessing.Process monkeypatched to raise | compile_experiment_plan(resources) | a resolved plan is returned and no thread or worker is started |
| `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_compiler_reads_no_ambient_clock` | time.time, datetime.now and datetime.utcnow monkeypatched to raise, generated_at omitted | compile_experiment_plan(resources) | compilation succeeds and run.generatedAt is the frozen sentinel 1970-01-01T00:00:00Z |
| `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_compilation_independent_of_locale_and_timezone` | the same set compiled under two TZ and LANG values | compile_experiment_plan(resources) | canonical_plan_bytes and plan.digest are identical under both environments |
| `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py::test_successful_compile_leaves_supplied_files_unchanged` | real fixture files with recorded digests | compile_experiment_files(paths) | the plan resolves and every supplied file keeps its exact bytes and digest |

### 7.15 `XDL1-SR-015-U` — Explicit unsupported realization, delivery and retry behaviour

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_realization_physical_unsupported_rejected` | Deployment binding/or target declared with realizationClass physical | compile_experiment_plan(resources) | rejected; XDL1-PLAN-REALIZATION-UNSUPPORTED; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_delivery_without_pinned_artifact_rejected` | realization-intent delivery 'staged' on a binding with no pinned artifactIds | compile_experiment_plan(resources) | rejected; XDL1-PLAN-DELIVERY-UNSUPPORTED; plan is None; no default delivery is applied |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py::test_retry_with_delivery_none_rejected` | realization-intent with delivery 'none' together with retry {policy: bounded, maxAttempts: 3} | compile_experiment_plan(resources) | rejected; XDL1-PLAN-RETRY-UNSUPPORTED; plan is None |

### 7.16 `XDL1-SR-016-U` — Preserved schema, Profile serialization and X-COM boundary

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_public_api_exports_present` | installed candidate package | import the frozen ExperimentLimits, ExperimentPlanResult, compile_* helpers and probe helpers from xverse_xdl | every frozen public name is importable with the frozen signature |
| `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_init_all_is_additive_superset` | installed candidate package | compare xverse_xdl.__all__ before and after the additive change | the previous name set is a subset of the new __all__ and no name was removed |
| `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_compile_api_result_shape` | one valid and one invalid normalized set | compile_experiment_plan(resources) | ExperimentPlanResult exposes diagnostics tuple, plan dict\|None, run FrozenMap and the is_valid property with the frozen semantics |
| `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_compile_sources_uses_real_loader` | real XDL source bytes for the neutral experiment fixture | compile_experiment_sources(sources, profile_schema_paths=(...)) | the accepted validate_sources path is exercised (no mock), resources are the normalized accepted resources and a resolved plan is returned |
| `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_cli_experiment_compile_json_emits_plan` | valid fixture files on disk | xdl experiment compile --format json RESOURCE... | exit 0 and stdout parses to {reportVersion, toolVersion, valid, plan, run, diagnostics} with plan non-null |
| `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_cli_experiment_compile_text_emits_summary` | valid fixture files on disk | xdl experiment compile RESOURCE... | exit 0 and stdout carries 'resolved plan <digest>' with the plan digest |
| `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_cli_experiment_compile_rejection_exits_one` | fixture files carrying one declared defect | xdl experiment compile --format json RESOURCE... | exit 1, plan null and at least one structured diagnostic; no -o file is created |
| `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_cli_invocation_error_exits_two` | a malformed --expect-input-digest argument | xdl experiment compile --expect-input-digest bogus RESOURCE... | exit 2 with an invocation message and no plan |
| `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py::test_cli_output_path_collision_exits_two` | an -o path equal to one of the input resource paths | xdl experiment compile -o <input> RESOURCE... | exit 2 and the input file bytes are unchanged |

### 7.17 `XDL1-SR-017-U` — Additive, explicitly admitted, fail-closed Profile extension

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_absent_rejected` | normalized closed set with one System, one Scenario and no admitted Profile resource | compile_experiment_plan(resources) on the normalized API entry point | rejected; exactly one error XDL1-PLAN-PROFILE-ABSENT (gate policy); plan is None |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_duplicate_rejected` | normalized set with two Profile resources that both claim extensionNamespace io.xverse.experiment | compile_experiment_plan(resources) (normalized path only; the loader path rejects earlier) | rejected; XDL1-PLAN-PROFILE-DUPLICATE; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_version_unsupported_rejected` | admitted Profile resource with metadata.version 0.2.0 | compile_experiment_plan(resources) | rejected; XDL1-PLAN-PROFILE-VERSION-UNSUPPORTED; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_schemaref_unsupported_rejected` | admitted Profile whose spec.schemaRef is another admitted Profile $id (xcom-v0.1) | compile_experiment_plan(resources) | rejected; XDL1-PLAN-PROFILE-SCHEMAREF-UNSUPPORTED; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_unknown_namespace_rejected` | resource carrying an extension under namespace io.xverse.unknown | compile_experiment_sources with the accepted loader, schema registry and semantics | rejected by the accepted gate with XDL-SEMANTIC-PROFILE-MISSING; plan is None and the XDL1 pipeline is skipped |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_payload_kind_mismatch_rejected` | scenario-intent kind value attached at a step extension pointer | compile_experiment_plan(resources) | rejected; XDL1-PLAN-PROFILE-PAYLOAD-KIND; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_payload_duplicate_rejected` | two experiment payloads at one attachment pointer (Scenario.extensions[io.xverse.experiment]) | compile_experiment_plan(resources) | rejected; XDL1-PLAN-PROFILE-PAYLOAD-DUPLICATE; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_payload_target_mismatch_rejected` | scenario-intent payload whose target.name differs from the owning Scenario metadata.name | compile_experiment_plan(resources) | rejected; XDL1-PLAN-PROFILE-TARGET-MISMATCH; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_scenario_intent_absent_rejected` | selected Scenario has no scenario-intent payload though other payloads are present | compile_experiment_plan(resources) | rejected; XDL1-PLAN-PROFILE-PAYLOAD-ABSENT; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py::test_profile_unknown_field_rejected` | scenario-intent payload carrying an undeclared extra field | compile_experiment_sources with the explicit Profile schema path | rejected by the accepted payload schema gate with XDL-SEMANTIC-EXTENSION-SCHEMA; plan is None |

### 7.18 `XDL1-SR-018-U` — Simulation-time ordering and canonical semantic identity

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_plan_digest_self_consistent` | a resolved plan emitted by the compiler | compute_plan_digest(plan) and canonical_plan_bytes(plan) | the recomputed digest equals plan.digest.value and the canonical bytes are stable across repeated calls |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_plan_matches_digest_for_emitted_plan` | a resolved plan emitted by the compiler | plan_matches_digest(plan) and experiment_plan_status(plan) | plan_matches_digest is True and experiment_plan_status is exactly 'resolved' |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py::test_plan_body_excludes_volatile_fields` | a resolved plan compiled with an explicit run_id and generated_at | recursive key scan of the plan body | no runId, generatedAt or sourceByteDigests key appears anywhere in the plan body; they exist only in the run envelope |
| `tests/thesis_lite/xdl/test_xdl1_order_unit.py::test_observer_and_metric_order_stable` | observers and metrics declared in reverse identity order | compile_experiment_plan(resources) twice with permuted input order | observers ordered by (timeDomainId, observerId) and metrics by metricId with observerIds and timeDomainIds sorted; both runs identical |
| `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py::test_diagnostics_sorted_deterministically` | a rejected set supplied twice with permuted resource order | compile_experiment_plan(resources) | both runs return identical diagnostic tuples ordered by Diagnostic.sort_key |
| `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_yaml_and_json_equal_plan_bytes_and_digest` | the same declared intent authored as YAML and as JSON | compile_experiment_sources for both encodings | canonical_plan_bytes, plan.digest and provenance.inputSemanticDigest are equal; only sourceByteDigests differ |
| `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_resource_order_permutation_equal_plan_bytes` | the same resources supplied in two different orders | compile_experiment_plan(resources) | canonical_plan_bytes and plan.digest are byte-equal |
| `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_payload_order_permutation_equal_plan_bytes` | the same payloads declared in two different orders within their extension maps | compile_experiment_plan(resources) | canonical_plan_bytes and plan.digest are byte-equal |
| `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_volatile_run_envelope_does_not_change_plan_digest` | the same set compiled with two different run_id and generated_at values | compile_experiment_plan(resources, run_id=..., generated_at=...) | plan bodies and planDigest are equal; only the volatile run envelope differs |
| `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_resource_revision_change_keeps_unrelated_identity` | the same set with one unrelated resource revision and one artifact digest changed | compile_experiment_plan(resources) | selection/component logical identities are byte-identical; only the affected binding artifact reference and the recomputed digest change |

### 7.19 `XDL1-SR-019-U` — Quantities, units and finite library bounds

| Test identifier | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_quantity_nonfinite_rejected` | declared duration value NaN reached through the normalized API entry point | compile_experiment_plan(resources) | rejected; XDL1-PLAN-QUANTITY-NONFINITE; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_quantity_negative_rejected` | declared duration value -1 with unit ms | compile_experiment_plan(resources) | rejected; XDL1-PLAN-QUANTITY-NEGATIVE; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_quantity_overflow_ticks_rejected` | declared duration that scales to more than max_ticks canonical ticks | compile_experiment_plan(resources) | rejected; XDL1-PLAN-QUANTITY-OVERFLOW; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_time_unit_unknown_rejected` | declared time unit 'min' outside the closed vocabulary | compile_experiment_plan(resources) on the normalized path | rejected; XDL1-PLAN-TIME-UNIT-UNKNOWN; plan is None; no conversion is attempted |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_time_precision_noninteger_tick_rejected` | declared value 0.5 with unit ns, which is not an exact integer tick | compile_experiment_plan(resources) | rejected; XDL1-PLAN-TIME-PRECISION; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_time_unit_scaling_exact_ticks` | table of (tick,1),(ns,1),(us,1000),(ms,1000000),(s,1000000000) declared quantities | compile_experiment_plan(resources) for each table row | each row is accepted with no diagnostic and the recorded atTicks/ticks equals the exact table value |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_experiment_limits_nonpositive_raises_value_error` | ExperimentLimits with one non-positive field | construct ExperimentLimits(max_steps=0) | ValueError is raised and no compile occurs |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_parameters_per_payload_scope_exceeded_rejected` | scenario-intent.parameters declaring 3 distinct entries with limits=ExperimentLimits(max_parameters=2) | compile_experiment_plan(resources, limits=ExperimentLimits(max_parameters=2)) | rejected; XDL1-PLAN-BOUND-EXCEEDED naming the per-payload parameter scope; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_parameters_total_compiled_scope_exceeded_rejected` | valid scenario-intent declaring 2 parameters plus one step-intent declaring 1 parameter (each individual list within the bound) with limits=ExperimentLimits(max_parameters=2), so the total compiled-parameter count C_total == 3 exceeds the bound | compile_experiment_plan(resources, limits=ExperimentLimits(max_parameters=2)) | rejected; XDL1-PLAN-BOUND-EXCEEDED (gate policy) naming the total compiled-parameter scope; plan is None; the per-payload scope alone does not admit the plan |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_parameters_declared_core_scope_exceeded_rejected` | System declaring 3 core parameters in spec.parameters[] with extension parameter lists within the bound and limits=ExperimentLimits(max_parameters=2) | compile_experiment_plan(resources, limits=ExperimentLimits(max_parameters=2)) | rejected; XDL1-PLAN-BOUND-EXCEEDED naming the declared core-parameter scope with the declaring resource pointer; plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_parameters_all_scopes_at_bound_accepted` | scenario-intent declaring 1 parameter, one step-intent declaring 1 parameter, System declaring 2 core parameters and the referenced Component declaring 2 core parameters, each list at exactly the bound with limits=ExperimentLimits(max_parameters=2) | compile_experiment_plan(resources, limits=ExperimentLimits(max_parameters=2)) | resolved plan; no error diagnostic; the emitted plan carries 2 compiled parameters (plan.parameters 1 + lifecycleIntent[].parameters 1) which equals the bound |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_steps_exceeded_rejected` | Scenario declaring 2 steps with limits=ExperimentLimits(max_steps=1) | compile_experiment_plan(resources, limits=ExperimentLimits(max_steps=1)) | rejected; XDL1-PLAN-BOUND-EXCEEDED (declared step count); plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_faults_exceeded_rejected` | Scenario declaring 2 faults with limits=ExperimentLimits(max_faults=1) | compile_experiment_plan(resources, limits=ExperimentLimits(max_faults=1)) | rejected; XDL1-PLAN-BOUND-EXCEEDED (declared fault count); plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_observers_exceeded_rejected` | Scenario declaring 2 observers with limits=ExperimentLimits(max_observers=1) | compile_experiment_plan(resources, limits=ExperimentLimits(max_observers=1)) | rejected; XDL1-PLAN-BOUND-EXCEEDED (declared observer count); plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_metrics_exceeded_rejected` | Scenario declaring 2 metrics with limits=ExperimentLimits(max_metrics=1) | compile_experiment_plan(resources, limits=ExperimentLimits(max_metrics=1)) | rejected; XDL1-PLAN-BOUND-EXCEEDED (declared metric count); plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_dependencies_per_step_exceeded_rejected` | one step-intent declaring 2 dependsOn entries with limits=ExperimentLimits(max_dependencies_per_step=1) | compile_experiment_plan(resources, limits=ExperimentLimits(max_dependencies_per_step=1)) | rejected; XDL1-PLAN-BOUND-EXCEEDED (per-step dependency count); plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_flows_exceeded_rejected` | System declaring 2 flows with limits=ExperimentLimits(max_flows=1) | compile_experiment_plan(resources, limits=ExperimentLimits(max_flows=1)) | rejected; XDL1-PLAN-BOUND-EXCEEDED (declared flow count); plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_bindings_exceeded_rejected` | Deployment declaring 2 bindings with limits=ExperimentLimits(max_bindings=1) | compile_experiment_plan(resources, limits=ExperimentLimits(max_bindings=1)) | rejected; XDL1-PLAN-BOUND-EXCEEDED (declared binding count); plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_resources_exceeded_rejected` | normalized closed set carrying 2 resources with limits=ExperimentLimits(max_resources=1) | compile_experiment_plan(resources, limits=ExperimentLimits(max_resources=1)) | rejected; XDL1-PLAN-BOUND-EXCEEDED (closed input-set resource count); plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_text_length_exceeded_rejected` | declared fidelityLimitations entry of 5 characters with limits=ExperimentLimits(max_text_length=4) | compile_experiment_plan(resources, limits=ExperimentLimits(max_text_length=4)) | rejected; XDL1-PLAN-BOUND-EXCEEDED (declared text length); plan is None |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_bytes_per_file_exceeded_rejected` | one input file whose byte length is 1 byte greater than the ExperimentLimits.max_bytes_per_file bound mirrored from the accepted LoadLimits | compile_experiment_files(paths, limits=ExperimentLimits()) | rejected by the accepted parse gate with XDL-PARSE-TOO-LARGE; plan is None; the supplied file keeps its exact bytes |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_diagnostics_exceeded_fails_closed` | closed set declaring 3 independent defects (3 steps each with a dependsOn naming an undeclared step) with limits=ExperimentLimits(max_diagnostics=2, max_steps=8) so no entity bound fires first | compile_experiment_plan(resources, limits=ExperimentLimits(max_diagnostics=2, max_steps=8)) | rejected; plan is None; ExperimentPlanResult.is_valid is False; the returned diagnostics tuple holds at most max_diagnostics entries (the declared bound is enforced before fail-closed) |

## 8. Count-based `ExperimentLimits` bound coverage (resolves `XDL1-RVW-003`)

Every declared finite library bound in `detailed-design.md` §10.2 has a named negative case (or an explicit accepted-gate equivalent) in the frozen identifier set. A bound declared as "per payload and total compiled parameters" is negatively exercised at the total-plan scope as well as the per-payload scope. No bound may remain without negative coverage.

| Declared bound | Scope in §10.2/§10.3 | Negative (or boundary) case | Expected code |
| --- | --- | --- | --- |
| `max_resources` | closed input-set resource count | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_resources_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_bytes_per_file` | each input source (mirrors accepted `LoadLimits`) | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_bytes_per_file_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL-PARSE-TOO-LARGE` (accepted parse gate) |
| `max_parameters` (per payload) | each declared extension `parameterList` | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_parameters_per_payload_scope_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_parameters` (total compiled) | total compiled-parameter count `C_total` over the finished sections | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_parameters_total_compiled_scope_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_parameters` (declared core) | each declared `System`/`Component`.`spec.parameters[]` list | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_parameters_declared_core_scope_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_parameters` (all scopes, boundary) | each scope at exactly the bound | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_parameters_all_scopes_at_bound_accepted` (`XDL1-SR-019-U`) | none — resolved plan |
| `max_steps` | declared Scenario steps | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_steps_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_faults` | declared Scenario faults | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_faults_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_observers` | declared Scenario observers | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_observers_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_metrics` | declared Scenario metrics | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_metrics_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_dependencies_per_step` | `dependsOn` entries per step | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_dependencies_per_step_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_flows` | declared System flows | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_flows_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_bindings` | declared Deployment bindings | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_bindings_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_ticks` | any canonical tick value | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_quantity_overflow_ticks_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-QUANTITY-OVERFLOW` |
| `max_seed` | seed value | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_seed_above_maximum_rejected` (`XDL1-SR-005-U`) | `XDL1-PLAN-SEED-RANGE` |
| `max_number_magnitude` | declared numeric parameter magnitude | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_parameter_bound_exceeded_rejected` (`XDL1-SR-005-U`) | `XDL1-PLAN-PARAMETER-BOUND` |
| `max_text_length` | declared text/limitation strings | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_text_length_exceeded_rejected` (`XDL1-SR-019-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_limitations` | merged plan limitations | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_limitations_exceeded_rejected` (`XDL1-SR-012-U`) | `XDL1-PLAN-BOUND-EXCEEDED` |
| `max_diagnostics` | returned diagnostics before the compile fails closed | `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py::test_max_diagnostics_exceeded_fails_closed` (`XDL1-SR-019-U`) | `plan is None` and the returned diagnostics tuple is bounded to `max_diagnostics` entries |

The `max_diagnostics` row asserts the declared bound is observable (the returned error diagnostics are capped and the compile fails closed with no plan). `detailed-design.md` §9 assigns no separate diagnostic code to the diagnostic-count scope, so no new code is invented; the fail-closed postcondition is already implied by any error diagnostic. This interpretation is recorded in the stage assumptions.

## 9. Adversarial and metamorphic cases

Adversarial (hostile-input) coverage is the negative surface fixed by `detailed-design.md` §17: unknown Profile/version/`schemaRef`/kind/field, absent or ambiguous selection, missing reference/pin/time mapping/seed, non-finite/negative/overflow/imprecise quantity, unknown unit, unknown fault/action, dependency cycle, competing declared order, unsupported realization/delivery/retry, incomplete metric linkage, secret-bearing leaf and post-hash mutation. Each has a named negative case in §7 with the exact rejection code and the `plan is None` postcondition; the bound cases in §8 extend that surface to every declared finite library bound; and the no-side-effect units prove no file, process, socket, thread, clock or environment read occurs during rejection or success.

Metamorphic equivalence:

| Metamorphic relation | Planned case |
| --- | --- |
| compile_experiment_sources for both encodings | `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_yaml_and_json_equal_plan_bytes_and_digest` (`XDL1-SR-018-U`) |
| compile_experiment_plan(resources) | `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_resource_order_permutation_equal_plan_bytes` (`XDL1-SR-018-U`) |
| compile_experiment_plan(resources) | `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_payload_order_permutation_equal_plan_bytes` (`XDL1-SR-018-U`) |
| compile_experiment_plan(resources, run_id=..., generated_at=...) | `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_volatile_run_envelope_does_not_change_plan_digest` (`XDL1-SR-018-U`) |
| compile_experiment_plan(resources) | `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py::test_resource_revision_change_keeps_unrelated_identity` (`XDL1-SR-018-U`) |

## 10. Static checks

| Check | Unit | Tool | Rule | Expected |
| --- | --- | --- | --- | --- |
| `XDL1-SR-001-U-STATIC` | `XDL1-SR-001-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | selection emits exactly one System/Scenario identity and a null-only Deployment when absent | static inspection of the selection branch shows no default identity, no first-match fallback and no partial selection return |
| `XDL1-SR-002-U-STATIC` | `XDL1-SR-002-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | only the five accepted v1alpha1 kind strings appear in emitted plan sections | grep of experiment_plan.py and the emitted plan shows no new top-level kind literal |
| `XDL1-SR-003-U-STATIC` | `XDL1-SR-003-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | experiment_plan.py imports no lifecycle/permit/provider capability | ast scan shows no import of xverse_xdl.lifecycle or process-starting module |
| `XDL1-SR-004-U-STATIC` | `XDL1-SR-004-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | binding projection keeps logicalRef distinct from realizationClass/targetId and resolves nothing physical | ast/field inspection shows no artifact retrieval, address resolution or handle construction |
| `XDL1-SR-005-U-STATIC` | `XDL1-SR-005-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | no literal seed or protocol default is present in experiment_plan.py | ast scan shows no default seed value and no invented parameter constant |
| `XDL1-SR-006-U-STATIC` | `XDL1-SR-006-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | no implicit time mapping or default time domain is synthesized | ast inspection shows conversion only through TIME_UNIT_TICKS and mapping only from declared entries |
| `XDL1-SR-007-U-STATIC` | `XDL1-SR-007-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | faultKind is copied verbatim and no fault activation/injection call exists | ast scan shows no fault runtime call and no invented fault-class vocabulary |
| `XDL1-SR-008-U-STATIC` | `XDL1-SR-008-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | no Argus writer, observer callable or evidence sink is imported or invoked | ast scan shows no observer/writer/oracle call in experiment_plan.py |
| `XDL1-SR-009-U-STATIC` | `XDL1-SR-009-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | metric status is the constant 'reference-only' and no metric computation exists | ast scan shows no metric arithmetic, oracle access or non-constant status value |
| `XDL1-SR-010-U-STATIC` | `XDL1-SR-010-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | no artifact fetch, unpack, digest-verify or availability probe exists | ast scan shows no file/network/process call reachable from artifact projection |
| `XDL1-SR-011-U-STATIC` | `XDL1-SR-011-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | resource and input digests use the frozen domain separators and canonical_json without source maps | literal inspection shows RESOURCE_DOMAIN_SEPARATOR, INPUT_DOMAIN_SEPARATOR and include_source_map=False |
| `XDL1-SR-012-U-STATIC` | `XDL1-SR-012-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | nonReadiness is a compiler-emitted constant with four false capability flags | literal inspection shows the frozen statement/claim and no caller-supplied readiness value |
| `XDL1-SR-013-U-STATIC` | `XDL1-SR-013-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | ready-set drain uses the frozen (kindRank, declaredIndex, id) key and no recursion without depth bound | ast inspection shows the deterministic sort key and an explicit cycle check with a rejected return |
| `XDL1-SR-014-U-STATIC` | `XDL1-SR-014-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | no forbidden import (subprocess, socket, threading, multiprocessing, http, urllib.request, time, datetime, os.environ access) exists in experiment_plan.py | ast scan reports no forbidden import and no ambient clock/locale/environment read |
| `XDL1-SR-015-U-STATIC` | `XDL1-SR-015-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | SUPPORTED_REALIZATION_CLASSES is the frozen tuple and every unsupported form returns a rejection | literal inspection shows ('simulated','virtual','hybrid') and no default delivery/retry value |
| `XDL1-SR-016-U-STATIC` | `XDL1-SR-016-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | no accepted file outside the additive boundary changes and __all__ only grows | diff shows no change under xdl/schemas/v1alpha1, src/xverse/xcom, proto or accepted tests; __all__ is a superset |
| `XDL1-SR-017-U-STATIC` | `XDL1-SR-017-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | payload schema is valid draft 2020-12 with additionalProperties false, closed kinds/consts and finite bounds | jsonschema meta-schema validation passes and the four payload kinds are the only admitted consts |
| `XDL1-SR-018-U-STATIC` | `XDL1-SR-018-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | canonical serialization uses sort_keys, compact separators, allow_nan False and the plan domain separator | ast inspection shows the frozen json.dumps options and PLAN_DOMAIN_SEPARATOR usage |
| `XDL1-SR-019-U-STATIC` | `XDL1-SR-019-U` | repository static inspection (python ast parse, jsonschema meta-schema validation, additive diff scope check) | TIME_UNIT_TICKS and ExperimentLimits defaults match the frozen design table and are all positive | literal inspection shows the frozen mapping and max_ticks == 9007199254740991 |

These checks are the planned input to the `XDL1-STATIC` (`static_analysis`) measure owned by the verification-design stage. No static check is executed in this stage. Each unit record also carries the declared-core projection rule (`XDL1-SR-002-U-STATIC`) and the frozen bound table (`XDL1-SR-019-U-STATIC`).

## 11. Coverage summary

| File | Cases |
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

Requirement coverage is complete: each `XDL1-SR-001` … `XDL1-SR-019` owns exactly one unit record and every acceptance-criterion class of every requirement has at least one positive and one negative planned case, except where a criterion is inherently positive-only (for example the additive-exports check) or inherently negative-only (for example the unsupported-realization check), which is stated in the case text.

## 12. Predecessor finding resolution

The predecessor XDL1 attempt-1 unit specification was part of a candidate that an independent read-only review returned with `verdict: rework`; it is retained only as failed review evidence. This successor work product binds each finding to named, independent cases. A binding is a planned contract; it is not evidence that the behaviour exists — the successor's own executed measures are owned by later stages.

| Finding | Predecessor gap | Resolution in this successor unit specification |
| --- | --- | --- |
| `XDL1-RVW-001` | `ExperimentLimits.max_parameters` total compiled-parameter scope declared but not enforced; no plan-level parameter count was checked. | `XDL1-SR-019-U::test_max_parameters_total_compiled_scope_exceeded_rejected` uses a valid scenario-intent plus step-intent declaration whose individual lists are each within `max_parameters` while the total compiled count exceeds it, and requires `XDL1-PLAN-BOUND-EXCEEDED` with `plan is None`; `XDL1-SR-019-U::test_max_parameters_all_scopes_at_bound_accepted` fixes the boundary. `XDL1-INV-11` states the invariant. |
| `XDL1-RVW-002` | declared `System.spec.parameters` were mapped but silently dropped; only Component parameters were projected, and no unit case asserted the System projection. | `XDL1-SR-002-U::test_system_core_parameters_projected_to_system_scope` requires a System parameter (`loop-count`) at `components[scope="system"].declaredParameters` and a distinct Component parameter (`nominal-rate`) at its component-instance entry, with neither appearing in the other scope; `XDL1-SR-002-U::test_system_core_parameters_not_dropped_when_component_parameters_present` requires the full declared-id union exactly once; `XDL1-SR-002-U::test_system_scope_entry_always_present_with_empty_declared_parameters` fixes the stable shape. `XDL1-INV-12` states the invariant. |
| `XDL1-RVW-003` | `XDL1-PLAN-BOUND-EXCEEDED` had zero tests and no count-based bound had a negative case. | §8 binds every declared finite bound to a named negative case; `XDL1-PLAN-BOUND-EXCEEDED` now has the per-payload, total compiled, declared core, `max_steps`, `max_faults`, `max_observers`, `max_metrics`, `max_dependencies_per_step`, `max_flows`, `max_bindings`, `max_resources`, `max_text_length` and `max_limitations` negatives; `XDL1-SR-012-U` carries the limitation-count negative. |

## 13. Traceability and hand-off

* This stage adds one additive `decomposes_to` link per unit (`XDL1-L-201` … `XDL1-L-219`) in `engineering/trace/links.json`; all pre-existing links and endpoint revisions are preserved unchanged.
* `implemented_by` (unit → source endpoint), `verified_by` (unit → `XDL1-UNIT` measure) and `analyzed_by` (unit → `XDL1-STATIC` measure) links are owned by the implementation and verification-design stages and are **not** claimed here. Until they exist, the XDL1 unit records are intentionally untraced downstream and no completeness claim is made; `validate_trace` therefore cannot pass yet, exactly as recorded by the requirements and architecture stages.
* The verification-design stage must create the `XDL1-UNIT`, `XDL1-STATIC`, `XDL1-INTEGRATION` and `XDL1-VALIDATION` measure records and bind the `XDL1-UNIT` record's `test_ids` to the exact identifiers in §7 (and §11 totals) without renaming any of them.
* The implementation stage must create exactly these node identifiers under `tests/thesis_lite/xdl/`. Renaming, dropping or weakening one requires a reviewed successor candidate.

## 14. Limitations, model recommendation and next step

* Maturity of every item: **planned / target**. No source, schema, fixture or test code exists; source inspection does not demonstrate runtime success, and no verification, integration, validation, availability, readiness, compatibility or delivery claim is made.
* The `XDL1-SR-*` records remain `status: accepted` as *internal engineering intent* only, and no REF-002 parent is closed or promoted.
* Planned identifiers are frozen contracts for the later stages; the implementation stage must not edit `engineering/unit-specifications/XDL1-*.json`, this document or any earlier artifact.
* Model recommendation for the next stage (**verification_design**): the pinned `deepseek-v4-flash` with **high** reasoning remains the most cost-effective and only authorized route, because that work is deterministic mapping of the frozen identifiers in §7–§8 onto the four scoped measure records with no stronger-reasoning requirement; no Terra/Luna/Sol/Astra route is available in this package and no fallback or model switch is performed.
* Blocker: none at this stage. Implementation remains gated on completion of the four pre-code design stages and the precode gate.

