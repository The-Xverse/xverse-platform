# T018 Verification Plan — Named Checks, Commands, Negative Cases, and Expected Results (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T018 |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `56506d2c9cb71791cba06a1cc418fcadee72e0fa` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | repository-owned Python `pytest` module `tests/test_xcom_plan.py`, the T017 reference validator `scripts/validate_xcom_plan.py`, and the deterministic Fabro gate; no C++/GTest case is added by T018 |

This plan is written **before** implementation. The implementation must realise every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T018 56506d2c9cb71791cba06a1cc418fcadee72e0fa
```

For T018 this gate requires:

- `docs/engineering/xcom/t018/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present;
- the T018 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the plan
  stage leaves it unchecked, per the stage instruction);
- `src/xverse_xdl/xcom_plan.py` in the changed-path set;
- at least one changed path under `tests/`;
- `git diff --check <baseline> --` clean;
- the full `pytest` suite passing (`python3 -m pytest -q`).

Supporting commands (same tools, no network):

```sh
python3 -m py_compile src/xverse_xdl/xcom_plan.py
python3 -m pytest -q tests/test_xcom_plan.py
python3 -m pytest -q
python3 scripts/validate_xcom_plan.py --verify
python3 scripts/validate_xcom_task_ownership.py --verify
git rev-parse 56506d2c9cb71791cba06a1cc418fcadee72e0fa
git diff --name-only 56506d2c9cb71791cba06a1cc418fcadee72e0fa --
git diff --check 56506d2c9cb71791cba06a1cc418fcadee72e0fa --
```

`git rev-parse` for the baseline must print the baseline SHA, proving the binding resolves.

The documented gate invocation path above is workflow infrastructure (an agent instruction), not T018
artifact content, and is out of scope of the public-safety content rule; see `requirements.md` §2.4.

### 2.1 T018 authorized-path set (external boundary check)

`git diff --name-only 56506d2… --` must be a subset of:

```text
src/xverse_xdl/xcom_plan.py
tests/test_xcom_plan.py
docs/engineering/xcom/t018/
reports/xcom-queue/t018-package.json
specs/007-xcom-core/tasks.md            # shared path, T018 checkbox line only
```

No path under `src/xverse/xcom/include/`, `src/xverse/xcom/src/`, `src/xverse_xdl/` other than
`src/xverse_xdl/xcom_plan.py`, `proto/`, `cmake/`, `Doxyfile`, `xdl/`, `scripts/`, `tests/xcom/activation_plan/`,
`docs/engineering/xcom/t017/`, or `specs/007-xcom-core/contracts/` may appear. This set is declared in the
T007 `T-XDL` exclusive/shared lists (`docs/engineering/xcom/task-ownership.json`); the check is performed
externally by the deterministic gate and the review stage because the offline test suite starts no child
process and therefore cannot run `git`.

### 2.2 Environment prerequisite (must hold before the implementation gate can pass)

The repository declares Python dependencies (`jsonschema[format]>=4.26,<5`, `referencing`, `ruamel.yaml`) and a
`src/` package layout in `pyproject.toml`, and the existing suite imports `xverse_xdl`. The implementation
stage must run the checks under a Python 3.11+ environment where the declared dependencies are importable and
this repository's `src/` is on `sys.path`. The baseline environment currently satisfies this (`python3 -V` =
3.13.13; `jsonschema` 4.26.0, `referencing`, `ruamel.yaml` importable; `python3 -m pytest -q` = 113 passed).
Provisioning changes no repository file. If it cannot be provided, the implementation stage must return a
**failed** outcome and must **not** weaken, skip, or edit an existing test to force the gate to pass.

## 3. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Compiler loads and exposes the public API | `python3 -m py_compile` + import in tests | module imports with stdlib + sibling `xverse_xdl` only; `load_normalized_graph`, `compile_plan`, `compile_plan_text`, `canonical_plan_bytes`, `compute_digest`, `plan_matches_digest`, `plan_status`, `CompileLimits`, `GraphView`, `XcomPlanError` exist |
| CHK-02 | Closed Profile grammar | `test_payload_grammar_matches_t017_profile_schema` | the compiler's five-form table equals `xdl/profiles/xcom-v0.1.schema.json` (`kind` enum, each form's required and permitted members, the `target` members) |
| CHK-03 | Positive plan schema/digest validity | `test_positive_graph_compiles_to_activatable_plan`, `test_compiled_plan_passes_t017_schema_ordering_and_digest` | a positive graph compiles; `validate_plan_structure` and `check_digest` from `scripts/validate_xcom_plan.py` return no findings |
| CHK-04 | Derivation content | `test_positive_graph_derivation`, `test_policies_observation_stimulation_clocks` | contracts/endpoints/routes/providers/policies/observationPoints/stimulation/clockDomains/activationOrder equal the declared mapping of `detailed-design.md` §6–§7 and are ordered/uniquely keyed |
| CHK-05 | Inspectable-versus-activatable | `test_inspectable_and_activatable_status_rule`, `test_unresolved_family_matrix` | fully resolved → `activatable` with six `resolved`; each single unresolved family → `inspectable` with exactly that member `unresolved` and the declared diagnostic |
| CHK-06 | Constant/enum drift guard | `test_compiler_constants_match_t017_schema` | compiler enum/pattern constants equal the T017 schema enums; diagnostic/error codes match `^XCOM-[A-Z0-9-]{3,64}$` |
| CHK-07 | Bounds enforced | `test_declared_bounds_enforced` | over-byte/over-depth/over-node/over-resource input and over-cap compilation yield `XCOM-PLAN-BOUND`; an in-bound graph compiles |
| CHK-08 | Byte-stable determinism | `test_reordered_equivalent_graph_is_byte_identical`, `test_canonical_bytes_stability_and_integral_numbers` | the same graph twice and a reordered-but-equivalent graph yield byte-identical `canonical_plan_bytes` and the same digest; integral-number normalization is reproduced |
| CHK-09 | Governance and offline purity | external `git diff --name-only`; source inspection in `test_compiler_is_offline_and_pure` | changed set ⊆ §2.1; baseline binds; the compiler source imports no `socket`/`subprocess`/`requests`/`urllib`/`os.system`, opens no file, and writes nothing; `XCOM-SW-XDL-002` links resolve in the T008 matrix; REF-002 promoted set empty |

## 4. Negative cases

Each `NEG-*` injects one controlled defect into a bounded, repository-owned, public-safe synthetic graph and
asserts the declared outcome with **no** partial plan and no success claim.

### 4.1 Graph/input defects (`XCOM-PLAN-INPUT`/`XCOM-PLAN-DUPLICATE`, rejected)

| ID | Injected defect |
| --- | --- |
| `NEG-C01` | Root is not `{"resources": [...]}` (or `resources` is missing/not a list) |
| `NEG-C02` | A resource entry omits an `identity` member (`apiVersion`/`kind`/`namespace`/`name`) |
| `NEG-C03` | A graph value is a non-finite number (`NaN`/`Infinity`) |
| `NEG-C04` | Two resource entries share one identity tuple |
| `NEG-C23` | A graph text repeats an object member name (duplicate-member rejection) |
| `NEG-C25` | A `resources` entry is not an object |

### 4.2 Profile payload defects (`XCOM-PLAN-PROFILE`, rejected, except `NEG-C27`)

| ID | Injected defect |
| --- | --- |
| `NEG-C09` | A payload carries an unknown member |
| `NEG-C10` | A payload's `policy` does not match its `kind` (form/kind mismatch) |
| `NEG-C11` | Two payloads decorate the same identity with the same `kind` |
| `NEG-C12` | A payload carries a provider address, credential, permit, live handle, or tool session |
| `NEG-C13` | A payload is attached at an illegal collection, or a resource-level `interface-policy` decorates a multi-interface resource |
| `NEG-C27` | A payload's `target` names an identity other than its attachment (identity `unresolved`, plan `inspectable`) |

### 4.3 Derivation defects (`XCOM-PLAN-IDENTITY`/`XCOM-PLAN-POLICY`/`XCOM-PLAN-CONTRACT`, rejected)

| ID | Injected defect |
| --- | --- |
| `NEG-C05` | The graph contains more than one `System` (ambiguous scope) |
| `NEG-C06` | A flow declares more than one destination endpoint |
| `NEG-C07` | An endpoint has conflicting derived roles |
| `NEG-C08` | A route id equals an endpoint id (activation order collision) |
| `NEG-C14` | A Scenario observer's target is not a declared route |
| `NEG-C15` | A `validation-policy` declares `serviceEmulation: true` without `permitPolicyRef` |
| `NEG-C24` | The graph declares no endpoint and no route (empty activation order) |

### 4.4 Unresolved-input controls (accepted as `inspectable`)

| ID | Injected defect | Expected member |
| --- | --- | --- |
| `NEG-C16` | A required capability is not declared by the selected provider | `capability: unresolved` |
| `NEG-C17` | A routed interface has no `interface-policy` | `schema: unresolved` |
| `NEG-C18` | A referenced clock domain has no mapping | `time: unresolved` |
| `NEG-C19` | An endpoint owner cannot be resolved in the System | `ownership: unresolved` |
| `NEG-C20` | No `flow-policy` is declared for the routes | `policy: unresolved` |

### 4.5 Status, provenance, and bound defects

| ID | Injected defect | Expected |
| --- | --- | --- |
| `NEG-C21` | The derived endpoint count exceeds `max_endpoints` | `failed`, `XCOM-PLAN-BOUND`, no plan |
| `NEG-C22` | The graph document exceeds the depth or node bound | `failed`, `XCOM-PLAN-BOUND`, no plan |
| `NEG-C26` | No `Component`/`Deployment`/`Scenario` contributes (empty `provenance.resources`) | `rejected`, `XCOM-PLAN-INPUT` |

### 4.6 Boundary and governance defects (`failed`)

| ID | Injected defect |
| --- | --- |
| `NEG-G01` | Candidate changed a path outside the §2.1 authorized set (e.g. `src/xverse_xdl/__init__.py`) |
| `NEG-G02` | Candidate changed `src/xverse/xcom/include/**` or `src/xverse/xcom/src/**` (T019 territory) |
| `NEG-G03` | A REF-002 target is recorded as promoted/implemented |
| `NEG-G04` | A source/test/evidence file contains a credential, private address, or absolute host path |
| `NEG-G05` | The T018 checkbox is marked complete in the plan stage, or an existing test/schema/contract is weakened |

## 5. Determinism checks

| ID | Check | Expected |
| --- | --- | --- |
| `DET-01` | `compile_plan` run twice on the same graph | byte-identical canonical bytes and identical digest |
| `DET-02` | Reordered-but-equivalent graph (resource order, member order, payload order) | identical canonical bytes and digest |
| `DET-03` | `canonical_plan_bytes` on integral-number variants (`100` vs `100.0`) and reordered members | identical canonical bytes |

## 6. Bound checks

| ID | Bound | Expected |
| --- | --- | --- |
| `BND-01` | Graph bytes (`compile_plan_text`) | over `max_bytes` → `XCOM-PLAN-BOUND` |
| `BND-02` | Graph depth / nodes / resources | over bound → `XCOM-PLAN-BOUND` |
| `BND-03` | Compiled entity caps (endpoints, routes, providers, observation points, clock domains, diagnostics) | over any cap → `XCOM-PLAN-BOUND` before a plan is returned |
| `BND-04` | No network / no subprocess / no filesystem write | source inspection finds no such call; the compiler remains a pure function |

## 7. Exact planned tests (implementation stage)

| Test | Family | Asserts |
| --- | --- | --- |
| `tests/test_xcom_plan.py::test_compiler_module_public_api` | positive | CHK-01 |
| `tests/test_xcom_plan.py::test_compiler_constants_match_t017_schema` | drift guard | CHK-06 |
| `tests/test_xcom_plan.py::test_payload_grammar_matches_t017_profile_schema` | drift guard | CHK-02, CHK-06 |
| `tests/test_xcom_plan.py::test_positive_graph_compiles_to_activatable_plan` | positive | CHK-03, CHK-05 |
| `tests/test_xcom_plan.py::test_compiled_plan_passes_t017_schema_ordering_and_digest` | positive | CHK-03 |
| `tests/test_xcom_plan.py::test_compiler_digest_agrees_with_t017_reference` | positive | CHK-03, DET-01 |
| `tests/test_xcom_plan.py::test_positive_graph_derivation` | positive | CHK-04 |
| `tests/test_xcom_plan.py::test_policies_observation_stimulation_clocks` | positive | CHK-04 |
| `tests/test_xcom_plan.py::test_inspectable_and_activatable_status_rule` | positive/negative | CHK-05 |
| `tests/test_xcom_plan.py::test_unresolved_family_matrix` | negative controls | CHK-05; NEG-C16..NEG-C20, NEG-C27 |
| `tests/test_xcom_plan.py::test_reordered_equivalent_graph_is_byte_identical` | determinism | CHK-08, DET-01, DET-02 |
| `tests/test_xcom_plan.py::test_canonical_bytes_stability_and_integral_numbers` | determinism | CHK-08, DET-03 |
| `tests/test_xcom_plan.py::test_declared_bounds_enforced` | bound | CHK-07; BND-01..BND-03, NEG-C21, NEG-C22 |
| `tests/test_xcom_plan.py::test_graph_view_revalidates_limits_and_does_not_alias_input` | bound | T018-SR-001/008; R-02 |
| `tests/test_xcom_plan.py::test_profile_policy_values_are_checked_before_plan_emission` | negative | T018-SR-002; R-03 |
| `tests/test_xcom_plan.py::test_generated_at_rejects_impossible_calendar_and_clock_values` | negative | T018-SR-006; R-04 |
| `tests/test_xcom_plan.py::test_text_parser_failures_use_declared_error_codes` | bound | T018-SR-001/008; R-05 |
| `tests/test_xcom_plan.py::test_compiler_negatives` | negative | NEG-C01..NEG-C15, NEG-C23..NEG-C26 |
| `tests/test_xcom_plan.py::test_compiler_is_offline_and_pure` | governance/offline | CHK-09, BND-04 |
| `tests/test_xcom_plan.py::test_verification_plan_lists_every_implemented_test` | traceability | plan/test identifier agreement |
| `python3 -m pytest -q tests/test_xcom_plan.py` | suite | the compiler tests pass |
| `python3 -m pytest -q` | gate | the full suite passes; the T017 suite is unchanged |
| `python3 scripts/validate_xcom_plan.py --verify` | cross-check | the T017 artifacts still validate (T018 changed no T017 artifact) |

## 8. Expected results and limitations

- All checks and negative cases are deterministic and offline; the compiler is a pure function that returns a
  plan value or raises a classified `XcomPlanError`, and it never reports a partial result.
- The tests prove that the **compiler** produces plans satisfying the T017 contract for the bounded synthetic
  fixtures. They do **not** prove that the C++ decoder implements the contract, that equivalent normalized
  inputs are byte-identical end to end through the decoder, or that any runtime bound holds; that evidence
  belongs to T019/T020.
- No runtime, throughput, timing, availability, compatibility, or production claim is made.
- The plan-stage candidate changes only documentation; the deterministic gate cannot pass until the
  implementation stage supplies `src/xverse_xdl/xcom_plan.py`, `tests/test_xcom_plan.py`, and
  `implementation.md` and marks the T018 checkbox.

## 9. Traceability of checks

| Requirement | Checks | Negative cases |
| --- | --- | --- |
| T018-SR-001 | CHK-01, CHK-07 | NEG-C01..NEG-C04, NEG-C21..NEG-C23, NEG-C25 |
| T018-SR-002 | CHK-02, CHK-06 | NEG-C09..NEG-C13, NEG-C27 |
| T018-SR-003 | CHK-03, CHK-04 | NEG-C05..NEG-C08, NEG-C16, NEG-C17 |
| T018-SR-004 | CHK-04 | NEG-C14, NEG-C15, NEG-C18, NEG-C20, NEG-C24 |
| T018-SR-005 | CHK-03, DET-01, DET-02, DET-03 | NEG-C23 |
| T018-SR-006 | CHK-03 | NEG-C01, NEG-C26 |
| T018-SR-007 | CHK-05 | NEG-C16..NEG-C20, NEG-C27 |
| T018-SR-008 | CHK-07, BND-01..BND-04 | NEG-C21, NEG-C22 |
| T018-SR-009 | CHK-01..CHK-08 | (positive and negative via tests) |
| T018-SR-010 | CHK-09 | NEG-G01..NEG-G05 |
