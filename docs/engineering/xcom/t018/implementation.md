# T018 Implementation Record — Deterministic Profile-Aware Plan Compiler

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T018 (capability 007, phase 4 XDL-derived activation plan) |
| Stage / role | implementation → implementation record |
| Revision | 1 |
| Authorized baseline | `56506d2c9cb71791cba06a1cc418fcadee72e0fa` |
| Candidate state | working tree over the authorized baseline (candidate revision assigned when the workflow checkpoints) |
| Predecessor | T017 reviewed terminal package (`56506d2`); plan-stage work products `docs/engineering/xcom/t018/` rev 1 |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Authorization | ACC002, ACC003, ACC013, ACC014, ACC015; ADR-0016, ADR-0018, ADR-0020; `specs/007-xcom-core/tasks.md` T018; `docs/engineering/xcom/task-ownership.json` `T-XDL` |
| Maturity | Compiler implemented and locally verified; not user-accepted, not externally reviewed, not integrated |
| Classification | Public-safe engineering work product |

T018 implements the bounded task entry *"Implement deterministic Profile-aware plan compilation in
`src/xverse_xdl/xcom_plan.py`."* It realises `T018-U-01`..`T018-U-10` and the accepted `XCOM-DU-009`. It
accepts, completes, and integrates no other task, implements neither the T019 decoder nor the T020
regression suite, and claims no external acceptance.

## 2. Candidate summary

The candidate adds **one new Python module** (`src/xverse_xdl/xcom_plan.py`), **one new pytest module**
(`tests/test_xcom_plan.py`), this record, and the T018 checkbox line in the shared
`specs/007-xcom-core/tasks.md`. It changes **no** path under `src/xverse/xcom/include/`,
`src/xverse/xcom/src/`, any other `src/xverse_xdl/` file, `proto/`, `cmake/`, `Doxyfile`, `xdl/`,
`scripts/`, `tests/xcom/activation_plan/`, `docs/engineering/xcom/t017/`, or
`specs/007-xcom-core/contracts/`; adds no CMake target; executes no production workload; re-parses no
authored YAML/JSON; and defines no second configuration language.

`compile_plan` is a pure, offline, bounded function from the admitted normalized-graph document plus the
`io.xverse.xcom` Profile v0.1 payloads to the canonical activation-plan v1 value. It reproduces the T017
canonical serialization, the `xverse.xcom.activation-plan.v1\x00` domain-separated digest, the
generator/provenance contract, the fail-closed inspectable-versus-activatable rule, and the declared
offline/entity bounds. `tests/test_xcom_plan.py` proves the positive derivation, the byte-stable
determinism, the digest agreement with the T017 reference validator, the schema/ordering validity, the
grammar/enum drift guards, the bound behaviour, and the declared negative set.

## 3. Design-detail resolutions

The plan-stage design is candidate-owned. Four internal inconsistencies in it were resolved in favour of
the accepted T017 schema/contract (`requirements.md` §1.2 decision rule); each resolution is recorded here
rather than left implicit, and none weakens an accepted requirement, check, schema, or test.

1. **Profile `target.kind` excludes `System`.** The accepted `xdl/profiles/xcom-v0.1.schema.json`
   enumerates `target.kind` as `Component`/`Deployment`/`Scenario`, and the design's own §5.1 step 5
   requires the payload target to equal its attachment resource. A payload attached to a `System` resource
   or a `System` interface/flow therefore cannot be grammar-valid. The compiler enforces the accepted
   grammar: contracts are derived from `interface-policy` payloads attached to a reachable `Component`
   interface (or the single-interface resource level), and `flow-policy` payloads are accepted at a
   legal-target resource level (`Component`/`Deployment`/`Scenario`). The design's "System resource level"
   allowance is realised as "legal-target resource level"; no accepted sentence is rewritten.
2. **Per-form completeness is enforced semantically, not at index time.** The closed per-form member
   *sets* (`PROFILE_FORM_PERMITTED`) are enforced at index time (an unknown member or a form/kind mismatch
   is `XCOM-PLAN-PROFILE`), as are the discriminator, version, target structure, and placement rules. The
   accepted design assigns the conditional `serviceEmulation ⇒ permitPolicyRef` case to
   `XCOM-PLAN-POLICY` (`detailed-design.md` §7.3) and an incomplete `flow-policy` to an unresolved policy
   input (§7.1), so a missing policy member is not pre-empted as a profile rejection. `PROFILE_FORM_REQUIRED`
   is still declared and drift-checked against the schema (`CHK-02`, `CHK-06`).
3. **A provider with no declared capability is unrepresentable.** The accepted plan schema requires
   `provider.capabilities` `minItems: 1`, while the design says an absent Deployment declaration yields
   `[]` with an unresolved capability state. The compiler records the unresolved capability input and
   omits that provider, so a schema-valid inspectable plan is produced rather than a schema-invalid plan.
   A valid Deployment declares at least one target capability, so this branch is unreachable for admitted
   input.
4. **Provenance digests are payload-order-stable.** The T017 contract preserves array order while `DET-02`
   requires a reordered-but-equivalent graph (including payload order) to share one digest. The compiler
   imposes one canonical payload order (by attachment pointer) when it computes `provenance.graphDigest`
   and each `provenance.resources[].sourceDigest`; payload values are untouched.

## 4. Changed artifacts and symbols

| Artifact | Change | Symbols / structure |
| --- | --- | --- |
| `src/xverse_xdl/xcom_plan.py` | new | Constants `TASK_ID`, `GENERATOR_VERSION`, `PLAN_VERSION`, `PROFILE_NAMESPACE`, `PLAN_TARGET`, `DEFAULT_GENERATED_AT`, `PLAN_DOMAIN_SEPARATOR`, `GRAPH_DOMAIN_SEPARATOR`, the closed vocabularies (`SCOPE_KINDS`, `PROVENANCE_KINDS`, `INTERFACE_KINDS`, `ENDPOINT_ROLES`, `CLOCK_SOURCES`, `ORDERING_VALUES`, `RELIABILITY_VALUES`, `OVERFLOW_POLICIES`, `BACKPRESSURE_POLICIES`, `RESOLUTION_STATES`, `PLAN_STATUS`, `PLACEHOLDER_POLICY`), the code vocabularies (`ERROR_CODES`, `DIAGNOSTIC_CODES`), the drift-guarded closed grammar (`PROFILE_FORM_REQUIRED`/`OPTIONAL`/`PERMITTED`/`COLLECTIONS`, `PAYLOAD_MEMBERS`, `TARGET_REQUIRED`/`MEMBERS`/`KINDS`); types `XcomPlanError`, `CompileLimits`, `GraphView`, `_ProfileRecord`, `_State`; public API `load_normalized_graph`, `compile_plan`, `compile_plan_text`, `canonical_plan_bytes`, `compute_digest`, `plan_matches_digest`, `plan_status`; internal units `_validate_payload`, `_parse_pointer`, `_resource_level_legal`, `_target_matches`, `_index_profiles` (U-01/U-02), `_select_system`/`_select_related`/`_reachable_components`/`_derive_contracts`/`_derive_endpoints`/`_derive_routes`/`_derive_providers` (U-03), `_derive_policies`/`_derive_observation_points`/`_derive_stimulation`/`_derive_clock_domains`/`_derive_activation_order` (U-04), `_normalize_numbers`/`_canonical_resource`/`_graph_digest`/`_provenance_resources` (U-05), `_resolve`/`_build_diagnostics` (U-06), `_check_entity_caps`/`compile_plan` (U-07/U-08). |
| `tests/test_xcom_plan.py` | new | 16 test functions plus inline bounded synthetic normalized-graph fixtures and helpers; imports the T017 validator's `validate_plan_structure`, `check_digest`, `compute_digest`, `canonical_bytes` for independent cross-checking. |
| `docs/engineering/xcom/t018/implementation.md` | new | This record. |
| `specs/007-xcom-core/tasks.md` | modified | T018 checkbox marked complete; no other task line changed (marked after this record exists). |

The compiler imports only `hashlib`, `json`, `math`, `re`, `collections.abc`, `dataclasses`, `typing`, and
`__future__`; it imports no X-COM runtime type, no legacy artifact, and no third-party module at import
time. `jsonschema`/`referencing` are used only by the T017 validator the tests load for cross-checking.

## 5. Requirement-to-evidence trace

| Requirement | Evidence |
| --- | --- |
| T018-SR-001 | `load_normalized_graph`, `compile_plan_text`, `_measure_shape`; CHK-01/CHK-07; `test_compiler_module_public_api`, `test_declared_bounds_enforced`; NEG-C01..NEG-C04, NEG-C21..NEG-C23, NEG-C25 |
| T018-SR-002 | `_validate_payload`, `_parse_pointer`, `_resource_level_legal`, `_index_profiles`; CHK-02/CHK-06; `test_payload_grammar_matches_t017_profile_schema`, `test_compiler_constants_match_t017_schema`; NEG-C09..NEG-C13, NEG-C27 |
| T018-SR-003 | `_derive_contracts`, `_derive_endpoints`, `_derive_routes`, `_derive_providers`; CHK-03/CHK-04; `test_positive_graph_derivation`, `test_compiled_plan_passes_t017_schema_ordering_and_digest`; NEG-C05..NEG-C08, NEG-C16, NEG-C17 |
| T018-SR-004 | `_derive_policies`, `_derive_observation_points`, `_derive_stimulation`, `_derive_clock_domains`, `_derive_activation_order`; CHK-04; `test_policies_observation_stimulation_clocks`; NEG-C14, NEG-C15, NEG-C18, NEG-C20, NEG-C24 |
| T018-SR-005 | `canonical_plan_bytes`, `compute_digest`, `plan_matches_digest`; CHK-03/CHK-08; `test_compiler_digest_agrees_with_t017_reference`, `test_reordered_equivalent_graph_is_byte_identical`, `test_canonical_bytes_stability_and_integral_numbers`; NEG-C23 |
| T018-SR-006 | `_canonical_resource`, `_graph_digest`, `_provenance_resources`; CHK-03; `test_positive_graph_compiles_to_activatable_plan`, `test_positive_graph_derivation`; NEG-C01, NEG-C26 |
| T018-SR-007 | `_resolve`, `_build_diagnostics`, `plan_status`; CHK-05; `test_inspectable_and_activatable_status_rule`, `test_unresolved_family_matrix`; NEG-C16..NEG-C20, NEG-C27 |
| T018-SR-008 | `CompileLimits`, `_check_entity_caps`, `error_outcome`; CHK-07; `test_declared_bounds_enforced`; NEG-C21, NEG-C22 |
| T018-SR-009 | `tests/test_xcom_plan.py` (16 tests); CHK-01..CHK-08; `test_verification_plan_lists_every_implemented_test`; full `pytest` gate |
| T018-SR-010 | Candidate path set §2/§4; `test_compiler_is_offline_and_pure`; CHK-09; NEG-G01..NEG-G05 (external gate/review) |

Capability anchors: FR-002/FR-031/SC-002 are implemented **for this compilation slice** by the derived,
digest-bound plan and the byte-stable determinism; FR-007 is **partial** (the declared policy set is
recorded; runtime enforcement is T019/T020); FR-027/FR-030 remain **partial** (governance constraints) with
review and acceptance still separate. REF-002: no direct communication requirement `XVE-SYS-0139`–`0158`
and no shared requirement is implemented or promoted; `ref002_disposition = "unchanged"` with an empty
promoted set. No accepted disposition record is rewritten.

## 6. Commands, results, and evidence

Environment (provisioned, changes no repository file): Python 3.13.13; `jsonschema` 4.26.0, `referencing`,
`ruamel.yaml` importable; this checkout's `src/` is importable so the suite resolves `xverse_xdl`. All
commands run from the repository root at baseline `56506d2c9cb71791cba06a1cc418fcadee72e0fa`.

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| 1 | `python3 -m py_compile src/xverse_xdl/xcom_plan.py` | 0 | Compiler compiles. |
| 2 | `python3 -m pytest -q tests/test_xcom_plan.py` | 0 | `16 passed`. |
| 3 | `python3 -m pytest -q` | 0 | `129 passed, 24 subtests passed` (baseline was `113 passed, 24 subtests`; T018 adds 16 tests, none removed or weakened). |
| 4 | `python3 scripts/validate_xcom_plan.py --verify` | 0 | `X-COM activation-plan validation passed: profileKinds=5 planMembers=16 collections=6 digestVectors=2 exitClasses=6` — T018 changed no T017 artifact, so the T017 suite and fixtures are unchanged. |
| 5 | `python3 scripts/validate_xcom_task_ownership.py --verify` | 0 | `X-COM task-ownership validation passed` (T007). |
| 6 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` | 0 | `X-COM requirements/traceability validation passed` (T008). |
| 7 | `python3 scripts/validate_xcom_architecture_contracts.py --verify` | 12 | `PATH_INVALID` for `XCOM-CMP-002`/`XCOM-CMP-003` planned paths already present. **Pre-existing at the authorized baseline** (`xdl/profiles/xcom-v0.1.schema.json`, `src/xverse/xcom/contracts/v1/activation-plan.schema.json` were delivered by T017); T018 adds `src/xverse_xdl/xcom_plan.py` and `tests/test_xcom_plan.py` as the same class of finding because it legitimately implements its planned paths. No T009 artifact is edited. |
| 8 | `python3 scripts/validate_xcom_unit_design.py --verify` | 13 | `PATH_INVALID` for `XCOM-DU-009`/`XCOM-DU-010`/`XCOM-DU-011` planned paths already present; **pre-existing at the authorized baseline** (the T017 paths) plus the two T018 paths. No T010 artifact is edited. |
| 9 | `git rev-parse 56506d2c9cb71791cba06a1cc418fcadee72e0fa` | 0 | Prints the baseline SHA (binding resolves). |
| 10 | `git diff --check 56506d2c9cb71791cba06a1cc418fcadee72e0fa --` | 0 | Clean. |
| 11 | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T018 56506d2c9cb71791cba06a1cc418fcadee72e0fa` | 0 | `{"ok": true, "task_id": "T018", "changed_paths": 9, "checks": ["pytest"]}` (recorded after the checkbox and this record existed; the invocation path is workflow infrastructure, not artifact content). |

Artifact identity at this candidate state (sha256):

| Artifact | sha256 |
| --- | --- |
| `src/xverse_xdl/xcom_plan.py` | `a0e1365014a0d7ced7dcef05b536e0ccaeff31c13d7cce75e8092d85e534c05a` |
| `tests/test_xcom_plan.py` | `f94c8a1f570e7ad626d38f9a55944567f6f8321fd045e1c70054dd6a93942132` |

`implementation.md` and the post-record `tasks.md` checkbox line are not self-hashed. Hashes are bound to
this candidate state; a successor candidate (for example a repair after review) must record its own exact
revision and repeat the affected checks.

## 7. Bounds and negative-case coverage

- **Graph/input defects (`rejected`, `XCOM-PLAN-INPUT`/`XCOM-PLAN-DUPLICATE`):** NEG-C01, NEG-C02, NEG-C03,
  NEG-C04, NEG-C23, NEG-C25.
- **Profile defects (`rejected`, `XCOM-PLAN-PROFILE`):** NEG-C09..NEG-C13; NEG-C27 is the accepted
  `identity: unresolved` control (`inspectable`).
- **Derivation defects (`rejected`, `XCOM-PLAN-IDENTITY`/`XCOM-PLAN-DUPLICATE`/`XCOM-PLAN-CONTRACT`/
  `XCOM-PLAN-POLICY`):** NEG-C05..NEG-C08, NEG-C14, NEG-C15, NEG-C24.
- **Unresolved-input controls (`inspectable`):** NEG-C16 (capability), NEG-C17 (schema), NEG-C18 (time),
  NEG-C19 (ownership), NEG-C20 (policy), NEG-C27 (identity).
- **Bound defects (`failed`, `XCOM-PLAN-BOUND`, no plan):** NEG-C21 (endpoint cap), NEG-C22 (depth/node),
  BND-01 (bytes), BND-02 (depth/nodes/resources), BND-03 (entity caps).
- **Provenance defect (`rejected`, `XCOM-PLAN-INPUT`):** NEG-C26 (no contributing
  Component/Deployment/Scenario).
- **Boundary/governance defects (`failed`):** NEG-G01..NEG-G05 are performed by the deterministic gate and
  the review stage, not by the offline compiler (which starts no child process and cannot run `git`); the
  offline test asserts the compiler imports no network/subprocess filesystem module, calls no `open`, and
  contains no absolute host path or private-key marker.

Bounds (offline-input/entity caps, not production values): `max_bytes` 5 242 880, `max_depth` 100,
`max_nodes` 100 000, `max_resources` 1 000, `max_endpoints` 4 096, `max_routes` 4 096, `max_providers`
256, `max_observation_points` 1 024, `max_clock_domains` 256, `max_diagnostics` 4 096; overflow policy
`fail-closed`. A `CompileLimits` value `< 1` is rejected at construction with `XCOM-PLAN-INPUT`.

## 8. Limitations and honesty notes

1. **No acceptance or integration claim.** T018 implements and locally verifies only its own bounded
   artifacts. It accepts or integrates no candidate, including itself, and claims no external review or
   user acceptance. The DeepSeek internal review is a separate stage; external Codex review is deferred
   until the `xcom-t007-t010-t017-t020` backlog completes.
2. **Compiler, not a decoder or runtime.** The tests prove the compiler emits T017-conformant plans for
   bounded synthetic fixtures. They do **not** prove that the C++ decoder (T019) implements the contract,
   that equivalent inputs are byte-identical end to end through the decoder, or that any runtime bound
   holds; that evidence belongs to T019/T020. No availability, throughput, timing, compatibility, or
   production claim is made.
3. **No production numeric bound is fixed.** Every `CompileLimits` value is an offline-input or
   compiled-entity cap; runtime bounds come from the activation plan or unit configuration (FR-007).
4. **Bounded synthetic fixtures, not authored XDL.** The test graphs are inline normalized-graph documents
   in the admitted `{"resources":[...]}` shape (equivalent to `xverse_xdl.canonical_json` output); the
   compiler re-parses no authored YAML/JSON and duplicates no XDL normalization or reference resolution.
5. **Schema-validity is checked by the T017 validator, not at import time.** The compiler does not embed a
   JSON Schema validator; `tests/test_xcom_plan.py` independently runs `validate_plan_structure` and
   `check_digest` against the compiled plans.
6. **T009/T010 validators fail at the baseline.** `validate_xcom_architecture_contracts.py` and
   `validate_xcom_unit_design.py` report `PATH_INVALID` because a delivered planned path is treated as
   present; this already occurred at the authorized baseline for the T017 paths. T018 neither introduces
   nor repairs that pre-existing validator defect, and edits no T009/T010 artifact (commands 7–8).
7. **Not-yet-present successor artifacts.** `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp` and
   `src/xverse/xcom/src/activation_plan.cpp` (T019) and the ordering/malformed/drift/bound/regression
   suites (T020) are absent; T018 produces the plan and its digest they will independently consume and
   check, and does not create, read, or reconcile them.
8. **Environment identity is recorded, not pinned.** The gate's Python environment was provisioned outside
   the repository (declared dependencies plus importable `src/`); that provisioning changes no repository
   file. Compiler/dependency admission with hashes and licenses remains T011.

## 9. Trace links

| Link | Locator |
| --- | --- |
| Software requirement | `XCOM-SW-XDL-002` (`docs/engineering/xcom/t008/requirements-register.json`) |
| Design unit (baseline) | `XCOM-DU-XDL-BASELINE` (`docs/engineering/xcom/t008/traceability-matrix.json`, `XCOM-L-0138`–`0140`) |
| Design unit (T010) | `XCOM-DU-009` (`docs/engineering/xcom/t010/design-units.md`) |
| Test unit | `XCOM-T-XDL` (`docs/engineering/xcom/t008/traceability-matrix.json`) |
| Components | `XCOM-CMP-001`, `XCOM-CMP-002`, `XCOM-CMP-003` (`docs/engineering/xcom/t009/architecture-model.json`) |
| Contracts | `XCOM-XLC-001`, `XCOM-XLC-005`; `XCOM-XB-001`–`003` (`docs/engineering/xcom/t009/architecture-model.json`) |
| Accepted T017 artifacts (anchored, unchanged) | `xdl/profiles/xcom-v0.1.schema.json`, `src/xverse/xcom/contracts/v1/activation-plan.schema.json`, `scripts/validate_xcom_plan.py`, `specs/007-xcom-core/contracts/xdl-profile.md` |
| Capability | `specs/007-xcom-core/spec.md` FR-002/FR-031/SC-002; `specs/007-xcom-core/tasks.md` T018 |
| REF-002 | `specs/007-xcom-core/reference-traceability.md` — `unchanged`, promoted set empty |
