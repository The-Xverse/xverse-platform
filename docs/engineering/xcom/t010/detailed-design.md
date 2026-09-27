# T010 Detailed Design — Unit-Design Model Schema, Unit Catalogues, and Validator

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T010 |
| Stage / role | plan → detailed design |
| Revision | 1 |
| Baseline revision | `abb81681e0d844edaecbaf2843f1c2a7deb1e40f` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 1 |
| Maturity | Governance/planning target; documentation-and-script candidate |

## 2. Implementation artifacts (what the T010 candidate adds)

T010 is a work-product task, so its "implementation" is the unit-design model, its projection, and their
validator, all outside `src/`, `tests/`, `xdl/`, and `proto/`:

| Artifact | Path | Owner | Purpose |
| --- | --- | --- | --- |
| Unit-design model (machine) | `docs/engineering/xcom/t010/unit-design.json` | T010 | Canonical unit/ownership/lifetime/thread-safety/failure/bounds/Doxygen model |
| Design-units catalogue (human) | `docs/engineering/xcom/t010/design-units.md` | T010 | Deterministic projection; realises the T008 `design_unit` locator `XCOM-DU-INTG-BASELINE` |
| Model validator | `scripts/validate_xcom_unit_design.py` | T010 | Offline, deterministic, bounded checks with a self-test |
| Implementation record | `docs/engineering/xcom/t010/implementation.md` | T010 | Candidate revision, commands, outcomes, limitations |
| Capability task state | `specs/007-xcom-core/tasks.md` | shared | Mark T010 complete only in the implementation stage |
| Ownership consistency | `docs/engineering/xcom/task-ownership.{json,md}` | shared | Record the new validator path in `T-ENABLER`, then re-run `scripts/validate_xcom_task_ownership.py` |

The five plan-stage work products (`requirements.md`, `architecture.md`, `detailed-design.md`,
`unit-specifications.md`, `verification-plan.md`) are documentation and are produced before this
implementation. No `src/`, `tests/`, `xdl/`, or `proto/` path is created or changed, and no `Doxyfile`/CMake
file is changed.

## 3. Unit-design model schema (version 1)

Top-level object (`schema_version = 1`), fields in this order:

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | integer | `= 1` |
| `task_id` | string | `= "T010"` |
| `capability` | string | `= "007-xcom-core"` |
| `baseline_revision` | string | 40 lowercase hex; equals the run baseline |
| `candidate_revision_rule` | string | States successor candidates bind their own and predecessor revisions |
| `family_vocabulary` | array of string | Exactly `["CORE","ENB","GW","INTG","OBS","STIM","XDL"]` (stored sorted) |
| `kind_vocabulary` | array of string | Exactly `["boundary","build-time","data-plane","derived-artifact","documentation","edge","evidence","test-fixture"]` |
| `language_vocabulary` | array of string | Exactly `["cpp","json","markdown","proto","python"]` |
| `maturity_vocabulary` | array of string | Exactly the seven accepted maturity tokens |
| `ownership_vocabulary` | array of string | Exactly `["caller-owns-value","gateway-issued-handle","platform-owns-shared","provider-issued-handle","session-issued-handle","task-owns-artifact"]` |
| `lifetime_vocabulary` | array of string | Exactly `["document-scoped","endpoint-generation","invocation-scoped","plan-scoped","process-scoped","route-scoped","session-scoped","static-immutable"]` |
| `thread_safety_vocabulary` | array of string | Exactly `["externally-synchronized","immutable-value","internally-synchronized","message-passing","offline-single-threaded","process-isolated","read-only-static","single-thread-owner"]` |
| `bound_kind_vocabulary` | array of string | Exactly `["bytes","capacity","deadline","depth","quota","rate","retry","thread-count","timeout"]` |
| `overflow_policy_vocabulary` | array of string | Exactly `["coalesce","drop-newest","drop-oldest","fail-closed","lossless-backpressure","n/a","reject"]` |
| `outcome_vocabulary` | array of string | Exactly `["accepted","cancelled","delivered","evidence-incomplete","expired","failed","rejected","unknown"]` |
| `doxygen_tag_vocabulary` | array of string | Exactly `["brief","failure","file","ingroup","lifetime","note","ownership","param","post","pre","retval","return","thread_safety"]` |
| `adr_vocabulary` | array of string | Exactly `["ADR-0016","ADR-0018","ADR-0019","ADR-0020"]` |
| `authorization_records` | array of string | Exactly the T007 closed set: ACC001–ACC015, ADR-0018, ADR-0019, ADR-0020 (stored sorted) |
| `ref002` | object | `{disposition: "unchanged", promoted: [], source: "specs/007-xcom-core/reference-traceability.md"}` |
| `dependencies` | object | Required dependency paths: `task_ownership`, `requirement_register`, `architecture_model` |
| `coverage` | object | `component_exemptions` (list of `{id, reason, owning_tasks}`) and `requirement_exemptions` (same shape) |
| `doxygen_plan` | object | §9 schema |
| `counts` | object | Declared expected counts per family and invariant count |
| `units` | array of object | Sorted by `id`, ids unique |
| `invariants` | array of object | Sorted by `id`, ids unique |

Unit object:

| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | `XCOM-DU-###`; unique; required-id set exactly `XCOM-DU-001`–`030` |
| `name` | string | Non-empty |
| `family` | string | One of `family_vocabulary` |
| `kind` | string | One of `kind_vocabulary` |
| `language` | string | One of `language_vocabulary` |
| `scope` | string | `first-proof` \| `later` |
| `owning_slice` | string | A T007 slice id, or `external`/`downstream` |
| `owning_tasks` | array of string | Stored sorted `T0xx`; non-empty and consistent with the T007 register's slice→task mapping |
| `maturity` | string | One of `maturity_vocabulary` |
| `accepted_revision` | string or null | 40-hex iff `maturity == implemented`; else null |
| `reconciliation` | string or null | Required non-empty for a `partial` unit whose baseline coverage is unreconciled or reviewed-but-not-user-accepted; else null |
| `responsibility` | string | Non-empty, one bounded sentence |
| `artifact_paths` | array of object | `{path, status}`, `status ∈ {established, planned}`, stored sorted by `path`; non-empty |
| `component_refs` | array of string | `XCOM-CMP-###` resolving in the T009 model; non-empty for families `CORE`, `XDL`, `OBS`, `STIM`, `GW`; may be empty for `INTG`/`ENB` |
| `contract_refs` | array of string | `XCOM-XLC-###` resolving in the T009 model; may be empty |
| `requirement_links` | array of string | Non-empty; each resolves to a T008 register requirement id; no `FR-###`/`SC-###`/`US#` shorthand is accepted in unit links |
| `governing_adrs` | array of string | Non-empty; subset of `adr_vocabulary` |
| `ownership_model` | string | One of `ownership_vocabulary` |
| `ownership_rationale` | string | Non-empty |
| `lifetime_model` | string | One of `lifetime_vocabulary` |
| `lifetime_rationale` | string | Non-empty |
| `exposes_view` | boolean | `true` iff the unit hands out a borrowed reference/view |
| `view_lifetime` | string or null | Non-empty and non-`n/a` iff `exposes_view`; else null |
| `thread_safety` | object | `{model, rationale, shared_state, synchronization}` (§3.1) |
| `bounds` | array of object | `{resource, kind, configured, value, declared_in}`, non-empty, stored sorted by `(kind, resource)` (§3.2) |
| `overflow_policies` | array of string | Non-empty; `["n/a"]` iff no `capacity`/`quota`/`depth`/`rate` bound exists, otherwise a non-empty subset of the policy vocabulary excluding `n/a` |
| `failure_semantics` | array of object | `{condition, outcome}`, non-empty, stored sorted by `(outcome, condition)`; `outcome ∈ outcome_vocabulary` (§3.3) |
| `doxygen` | object | `{required, group, file_block, public_tags, documented_elements, public_elements, reason}` (§3.4) |
| `planned_evidence` | array of string | Non-empty; names the `CHK-`/`NEG-`/test ids that will evidence the unit |
| `notes` | string | Optional; empty string when absent |

### 3.1 Thread-safety object

| Field | Type | Rule |
| --- | --- | --- |
| `model` | string | One of `thread_safety_vocabulary` |
| `rationale` | string | Non-empty |
| `shared_state` | array of string | Stored sorted; non-empty only for `internally-synchronized`, `message-passing`, and `externally-synchronized` units, and empty for `immutable-value`, `read-only-static`, `single-thread-owner`, `offline-single-threaded`, and `process-isolated` units |
| `synchronization` | string or null | Non-empty iff `model == internally-synchronized`; non-empty description of the caller/message-passing obligation for `externally-synchronized`/`message-passing`; null iff `model ∈ {immutable-value, read-only-static, single-thread-owner, offline-single-threaded, process-isolated}` |

Consistency rules (all enforced): a unit with non-empty `shared_state` must use `internally-synchronized`,
`message-passing`, or `externally-synchronized`; `synchronization` must be non-null for those three synchronizing
models and null for `immutable-value`/`read-only-static`/`single-thread-owner`/`offline-single-threaded`/
`process-isolated`; an `internally-synchronized` unit must name its mechanism in `synchronization`; a
`message-passing` unit must declare a `capacity` bound and an overflow policy set that
does not silently drop below the declared policy; a `process-isolated` unit must not declare `shared_state`.

### 3.2 Bound object

| Field | Type | Rule |
| --- | --- | --- |
| `resource` | string | Non-empty; the bounded resource (for example `per-tap record queue`, `plan bytes`) |
| `kind` | string | One of `bound_kind_vocabulary`; `unbounded` is not a member, so an unbounded declaration is unrepresentable |
| `configured` | boolean | `true` for every bound: T010 fixes no numeric value |
| `value` | integer or null | Non-negative integer when fixed by configuration; null when configured at runtime |
| `declared_in` | string | Non-empty; the configuring source (for example `activation plan`, `tap policy`, `unit configuration`, `Doxyfile`) |

Rules: at least one bound per unit; at most one bound per `(kind, resource)` pair; a `retry` bound must be `0`
(no hidden retry) unless the plan explicitly permits one; a `thread-count` bound must be ≥ 1.

### 3.3 Failure semantics

`failure_semantics` maps a condition to exactly one outcome. Rules: at least one entry per unit; every entry's
`outcome` is from the closed vocabulary; a unit whose scope includes an asynchronous, journaled, externally
observable, or tool-driven path must (a) map `unknown` to a non-success outcome (`failed`, `rejected`,
`expired`, `cancelled`, or `evidence-incomplete`) and (b) declare an `evidence-incomplete` mapping when it
journals or durably writes before an outcome is known. A mapping of `unknown → accepted` or
`unknown → delivered` is rejected.

### 3.4 Doxygen object

| Field | Type | Rule |
| --- | --- | --- |
| `required` | boolean | `true` iff `language == "cpp"`; `false` otherwise |
| `group` | string | Required iff `required`; must equal `doxygen_plan.groups[family]` |
| `file_block` | array of string | Required iff `required`; must include every `doxygen_plan.mandatory_file_block` tag |
| `public_tags` | array of string | Required iff `required`; must include every `doxygen_plan.mandatory_public_tags` tag |
| `documented_elements` | integer | Required iff `required`; equal to `public_elements` |
| `public_elements` | integer | Required iff `required`; ≥ 1 |
| `reason` | string | Required non-empty iff `required == false` |

The declared element counts are a **structural consistency claim**, not proof of documentation: the model
asserts that the unit's public declarations are enumerated and documented, and T037's Doxygen gate produces
the warning-free generation evidence. T010 claims no generated documentation exists.

### 3.5 Array ordering (normative)

The validator enforces ascending `id` order and id uniqueness for exactly the two top-level arrays `units` and
`invariants`. No other array carries a lexical sort guarantee: the fixed vocabularies are compared by exact
equality (authored order significant); `authorization_records`, `owning_tasks`, `shared_state`,
`artifact_paths`, `bounds`, `failure_semantics`, `component_refs`, `contract_refs`, and `governing_adrs` are
stored sorted (by `path`, by `(kind, resource)`, and by `(outcome, condition)` respectively for the object
arrays); and `requirement_links`, `file_block`, `public_tags`, `overflow_policies`, and `planned_evidence`
preserve their authored order.

### 3.6 Expected counts

| Family | Units | Notes |
| --- | ---: | --- |
| `CORE` | 8 | `XCOM-DU-001`–`008` |
| `XDL` | 3 | `XCOM-DU-009`–`011` |
| `OBS` | 2 | `XCOM-DU-012`–`013` |
| `STIM` | 5 | `XCOM-DU-014`–`018` |
| `GW` | 3 | `XCOM-DU-019`–`021` |
| `INTG` | 4 | `XCOM-DU-022`–`025` |
| `ENB` | 5 | `XCOM-DU-026`–`030` |
| **Total** | **30** | plus 14 invariants `XCOM-UDI-01`–`14` |

## 4. Determinism, bounds, and safety rules

- **Determinism (T010-SR-001, T010-SR-014).** Stable key/element ordering; no timestamps, hostnames,
  absolute paths, or unordered iteration in the model, projection, or validator output.
- **Bounds (T010-STK-007).** The validator reads only repository-relative files, each ≤ 1 MiB; total input
  ≤ 4 MiB; no recursion outside the repository; wall-clock timeout ≤ 60 s; single-threaded.
- **Offline (T010-SR-014).** No network client, resolver, package manager, or subprocess shell; only file
  reads and pure computation. `git`-based path checks are performed by the deterministic gate and the
  implementation record, not inside the validator.
- **Public safety (T010-SR-013).** No credential, secret, private address, private-key marker, proprietary
  source excerpt, unrestricted payload, or absolute host path in the model, projection, or validator output.
- **Work-product boundary (T010-SR-012).** The candidate diff contains no `src/`, `tests/`, `xdl/`, or
  `proto/` path, no `Doxyfile`/CMake change, no accepted-ADR rewrite, no other task's work product, and no
  weakened requirement or test. The single added script lives under `scripts/`.
- **Ownership consistency (T010-SR-014).** The new script path is recorded under `T-ENABLER`
  `paths_exclusive` in `docs/engineering/xcom/task-ownership.json` and its projection; the change is
  regenerated deterministically and `scripts/validate_xcom_task_ownership.py --verify` and `--check-human`
  must both exit 0 afterwards. No other slice's ownership is changed.
- **Fail-closed dependencies (T010-SR-011).** The validator requires
  `docs/engineering/xcom/task-ownership.json`, `docs/engineering/xcom/t008/requirements-register.json`, and
  `docs/engineering/xcom/t009/architecture-model.json` to be present, readable, and well-formed; an
  unavailable or malformed dependency is a hard `BINDING_INVALID` (10), never a skipped check.
- **No numeric production values (T010-SR-005).** Every bound is `configured = true`; `value` is null unless a
  bounded, non-production value is fixed by the unit's own configuration (for example `retry = 0`). T010
  fixes no production capacity, rate, or deadline.

## 5. Unit catalogue — identity, ownership, and artifacts

Layer/owner abbreviations follow the T007 register. Status `(e)` = `established`, `(p)` = `planned`.

| Unit | Family | Kind | Language | Scope | Owner (tasks) | Maturity | Artifacts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `XCOM-DU-001` Value and payload view | CORE | data-plane | cpp | first-proof | T-CORE (T013) | partial | `include/xverse/xcom/value.hpp` (e), `src/xverse/xcom/src/value.cpp` (e), `tests/xcom/core_types/` (e) |
| `XCOM-DU-002` Contract and logical identity | CORE | data-plane | cpp | first-proof | T-CORE (T012) | partial | `include/xverse/xcom/contract.hpp` (e), `src/xverse/xcom/src/contract.cpp` (e) |
| `XCOM-DU-003` Item identity, origin, time, correlation | CORE | data-plane | cpp | first-proof | T-CORE (T013) | partial | `include/xverse/xcom/item.hpp` (e), `src/xverse/xcom/src/item.cpp` (e) |
| `XCOM-DU-004` Diagnostics and deterministic ordering | CORE | data-plane | cpp | first-proof | T-CORE (T013) | partial | `include/xverse/xcom/diagnostic.hpp` (e), `src/xverse/xcom/src/diagnostic.cpp` (e) |
| `XCOM-DU-005` Result/outcome and core type aggregate | CORE | data-plane | cpp | first-proof | T-CORE (T013) | partial | `include/xverse/xcom/result.hpp` (e), `include/xverse/xcom/core_types.hpp` (e) |
| `XCOM-DU-006` Endpoint/route lifecycle and generation handles | CORE | data-plane | cpp | first-proof | T-CORE (T014) | partial | `include/xverse/xcom/endpoint_route_lifecycle.hpp` (e), `src/xverse/xcom/src/endpoint_route_lifecycle.cpp` (e), `tests/xcom/endpoint_route_lifecycle/` (e) |
| `XCOM-DU-007` Provider boundary and composition | CORE | data-plane | cpp | first-proof | T-CORE (T015) | partial | `include/xverse/xcom/provider.hpp` (e), `src/xverse/xcom/src/provider.cpp` (e) |
| `XCOM-DU-008` Owned loopback provider | CORE | test-fixture | cpp | first-proof | T-CORE (T015, T016) | partial | `include/xverse/xcom/loopback_provider.hpp` (e), `src/xverse/xcom/src/loopback_provider.cpp` (e), `tests/xcom/provider_loopback/` (e) |
| `XCOM-DU-009` XDL Profile/plan compiler | XDL | build-time | python | first-proof | T-XDL (T017, T018) | allocated | `src/xverse_xdl/xcom_plan.py` (p), `xdl/profiles/xcom-v0.1.schema.json` (p), `tests/test_xcom_plan.py` (p) |
| `XCOM-DU-010` Activation-plan v1 schema | XDL | derived-artifact | json | first-proof | T-XDL (T017) | allocated | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` (p) |
| `XCOM-DU-011` Bounded activation-plan decode | XDL | data-plane | cpp | first-proof | T-XDL (T019, T020) | allocated | `include/xverse/xcom/activation_plan.hpp` (p), `src/xverse/xcom/src/activation_plan.cpp` (p), `tests/xcom/activation_plan/` (p) |
| `XCOM-DU-012` Observation record and payload-view policy | OBS | boundary | cpp | first-proof | T-OBS (T021) | partial | `include/xverse/xcom/observation.hpp` (e), `src/xverse/xcom/src/observation.cpp` (e) |
| `XCOM-DU-013` Bounded observer queue, counters, synthetic sink | OBS | boundary | cpp | first-proof | T-OBS (T022, T023) | partial | `include/xverse/xcom/observation.hpp` (e), `src/xverse/xcom/src/observation.cpp` (e), `tests/xcom/observation/` (e) |
| `XCOM-DU-014` Time authority | STIM | boundary | cpp | first-proof | T-STIM (T025) | implemented | `include/xverse/xcom/validation_session.hpp` (e), `src/xverse/xcom/src/validation_session.cpp` (e), `tests/xcom/validation_session/` (e) |
| `XCOM-DU-015` Validation permit and session lifecycle | STIM | boundary | cpp | first-proof | T-STIM (T025) | implemented | `include/xverse/xcom/validation_session.hpp` (e), `src/xverse/xcom/src/validation_session.cpp` (e), `tests/xcom/validation_session/` (e) |
| `XCOM-DU-016` Stimulation intent/outcome journal | STIM | boundary | cpp | first-proof | T-STIM (T026) | allocated | `include/xverse/xcom/stimulation_journal.hpp` (p), `src/xverse/xcom/src/stimulation_journal.cpp` (p), `tests/xcom/stimulation_journal/` (p) |
| `XCOM-DU-017` Fail-closed pre-emission guard | STIM | boundary | cpp | first-proof | T-STIM (T027) | allocated | `include/xverse/xcom/stimulation_guard.hpp` (p), `src/xverse/xcom/src/stimulation_guard.cpp` (p), `tests/xcom/stimulation_guard/` (p) |
| `XCOM-DU-018` Guarded injection and service-emulation lease | STIM | boundary | cpp | first-proof | T-STIM (T028) | allocated | `include/xverse/xcom/stimulation_actions.hpp` (p), `src/xverse/xcom/src/stimulation_actions.cpp` (p), `tests/xcom/stimulation_actions/` (p) |
| `XCOM-DU-019` Tool gateway Protocol Buffers API | GW | edge | proto | first-proof | T-CORE (T030) | allocated | `proto/xverse/xcom/v1/tool_gateway.proto` (p) |
| `XCOM-DU-020` Local-IPC-only gateway session | GW | edge | cpp | first-proof | T-CORE (T031) | allocated | `include/xverse/xcom/tool_gateway.hpp` (p), `src/xverse/xcom/src/tool_gateway.cpp` (p), `tests/xcom/tool_gateway/` (p) |
| `XCOM-DU-021` Separate-process synthetic tool client | GW | test-fixture | cpp | first-proof | T-CORE (T032, T033) | allocated | `src/xverse/xcom/fixtures/synthetic_tool.cpp` (p), `tests/xcom/tool_gateway/` (p) |
| `XCOM-DU-022` Doxygen documentation and warning gate | INTG | documentation | python | first-proof | T-INTG (T037) | partial | `Doxyfile` (e), `scripts/check_doxygen.py` (e), `docs/xcom/` (e) |
| `XCOM-DU-023` Requirements traceability validation | INTG | documentation | python | first-proof | T-INTG (T038) | partial | `scripts/validate_xcom_requirements_traceability.py` (e), `docs/engineering/xcom/t008/` (e) |
| `XCOM-DU-024` Public-safe evidence bundle | INTG | evidence | markdown | first-proof | T-INTG (T035, T040) | partial | `reports/xcom-queue/` (e), `docs/engineering/xcom/t035/` (p), `docs/engineering/xcom/t036/` (p), `docs/engineering/xcom/t038/` (p), `docs/engineering/xcom/t040/` (p) |
| `XCOM-DU-025` Controlled benchmark evidence | INTG | evidence | cpp | first-proof | T-INTG (T036) | partial | `tests/xcom/observation/integration/disabled_tap_benchmark.cpp` (e), `tests/xcom/performance/` (p) |
| `XCOM-DU-026` Requirement register and REF-002 model | ENB | documentation | json | first-proof | T-ENABLER (T008) | partial | `docs/engineering/xcom/t008/requirements-register.json` (e), `docs/engineering/xcom/t008/traceability-matrix.json` (e) |
| `XCOM-DU-027` Architecture and contract model | ENB | documentation | json | first-proof | T-ENABLER (T009) | partial | `docs/engineering/xcom/t009/architecture-model.json` (e), `docs/engineering/xcom/t009/architecture-model.md` (e), `scripts/validate_xcom_architecture_contracts.py` (e) |
| `XCOM-DU-028` Unit-design model and Doxygen plan | ENB | documentation | json | first-proof | T-ENABLER (T010) | allocated | `docs/engineering/xcom/t010/unit-design.json` (p), `docs/engineering/xcom/t010/design-units.md` (p), `scripts/validate_xcom_unit_design.py` (p) |
| `XCOM-DU-029` Dependency admission and build lock | ENB | documentation | markdown | first-proof | T-ENABLER (T011) | partial | `docs/engineering/xcom/dependency-lock.md` (e), `docs/engineering/xcom/build-environment.md` (e), `cmake/XComOfflineDependencies.cmake` (e), `scripts/xcom_dependency_preflight.py` (e) |
| `XCOM-DU-030` Independent review and acceptance record | ENB | documentation | markdown | first-proof | T-REVIEW (T039, T041) | allocated | `docs/engineering/xcom/t039/` (p), `docs/reviews/` (p) |

Maturity notes: `XCOM-DU-014`/`015` carry
`accepted_revision = 4b01586b438a8587d231ee8828d896c206c06a96` (the accepted T025 merge). The `partial`
units whose baseline source is present but unreconciled or reviewed-but-not-user-accepted carry a
non-empty `reconciliation` reason (analysis A12 and §4 of `requirements.md`); the `allocated` units carry
`accepted_revision = null` and no reconciliation reason.

## 6. Ownership and lifetime catalogue

| Unit | Ownership model | Lifetime model | View lifetime |
| --- | --- | --- | --- |
| `XCOM-DU-001` | caller-owns-value | invocation-scoped | bounded to the owning item or callback scope; not retained after the callback returns |
| `XCOM-DU-002` | platform-owns-shared | plan-scoped | — |
| `XCOM-DU-003` | caller-owns-value | invocation-scoped | bounded to the item's lifetime; payload views are not retained |
| `XCOM-DU-004` | caller-owns-value | invocation-scoped | — |
| `XCOM-DU-005` | caller-owns-value | invocation-scoped | — |
| `XCOM-DU-006` | provider-issued-handle | endpoint-generation | — |
| `XCOM-DU-007` | provider-issued-handle | process-scoped | — |
| `XCOM-DU-008` | provider-issued-handle | process-scoped | — |
| `XCOM-DU-009` | caller-owns-value | process-scoped | — |
| `XCOM-DU-010` | task-owns-artifact | static-immutable | — |
| `XCOM-DU-011` | caller-owns-value | plan-scoped | bounded to the decoded plan; typed views are not retained after use |
| `XCOM-DU-012` | platform-owns-shared | route-scoped | bounded to the observation callback; payload views are truncated to the tap policy and never retained |
| `XCOM-DU-013` | platform-owns-shared | route-scoped | — |
| `XCOM-DU-014` | platform-owns-shared | session-scoped | — |
| `XCOM-DU-015` | session-issued-handle | session-scoped | — |
| `XCOM-DU-016` | platform-owns-shared | session-scoped | — |
| `XCOM-DU-017` | session-issued-handle | session-scoped | — |
| `XCOM-DU-018` | session-issued-handle | endpoint-generation | — |
| `XCOM-DU-019` | task-owns-artifact | static-immutable | — |
| `XCOM-DU-020` | gateway-issued-handle | session-scoped | — |
| `XCOM-DU-021` | gateway-issued-handle | process-scoped | — |
| `XCOM-DU-022`–`030` | task-owns-artifact | document-scoped | — |

Rule: only a valid, exact issued handle may mutate, close, or replace an active resource (`XCOM-DU-006`–
`008`, `015`, `017`, `018`, `020`, `021`); restart reconciliation never infers ownership from a name or
address. This realises FR-009/FR-010 and T009 `XCOM-INV-02`.

## 7. Thread-safety and concurrency catalogue

| Unit | Thread-safety model | Shared mutable state | Synchronization / boundary |
| --- | --- | --- | --- |
| `XCOM-DU-001`, `002`, `003`, `004`, `005` | immutable-value | — (none) | none required; values are immutable after construction |
| `XCOM-DU-006` | internally-synchronized | per-provider endpoint/route handle table; generation counters | per-provider mutex held only for the state transition; no lock held across a provider callback |
| `XCOM-DU-007` | externally-synchronized | registered provider table | composition happens once before activation; the table is read-only afterwards (caller obligation) |
| `XCOM-DU-008` | single-thread-owner | — (none) | the owning test thread drives the loopback route and exclusively owns its per-route in-flight queue; no cross-thread hand-off in the first proof |
| `XCOM-DU-009` | offline-single-threaded | — (none) | build-time compiler; one process, one thread |
| `XCOM-DU-010`, `019` | read-only-static | — (none) | immutable schema/definition artifact |
| `XCOM-DU-011` | immutable-value | — (none) | decoded plan is immutable after bounded decode |
| `XCOM-DU-012` | immutable-value | — (none) | observation records are immutable projections |
| `XCOM-DU-013` | message-passing | per-tap bounded record queue; drop/coalesce counters | producer enqueues under the tap mutex; the observer drains on its own thread; counters are atomic |
| `XCOM-DU-014` | externally-synchronized | — (none) | the host-implemented time authority is called by the session's single active thread (caller obligation) |
| `XCOM-DU-015` | internally-synchronized | session state machine; consumed-permit record; quota counters | per-session mutex guarding transitions and quota consumption |
| `XCOM-DU-016` | internally-synchronized | append-only journal file handle; journal index | per-journal mutex; single writer; intent is persisted before emission |
| `XCOM-DU-017` | internally-synchronized | per-session action tally; loop-detection window | per-session mutex; rejection performs no state mutation |
| `XCOM-DU-018` | internally-synchronized | exclusive lease table keyed by (endpoint, generation); drain state | atomic lease acquisition under a per-session/per-endpoint mutex; release or quarantine on expiry/revocation/disconnect |
| `XCOM-DU-020` | internally-synchronized | accepted local IPC peer sessions; per-session deadlines and flow-control windows | per-session mutex plus bounded request queue; local IPC only, no TCP listener |
| `XCOM-DU-021` | externally-synchronized | in-flight request table | one request/stream at a time per session (caller obligation) |
| `XCOM-DU-022`–`030` | offline-single-threaded | — (none) | offline validation/evidence tooling; one process, one thread |

Rule: a unit whose `shared_state` is non-empty must use an `internally-synchronized`, `externally-synchronized`,
or `message-passing` model, and a unit that owns no shared mutable state must declare `synchronization = null`
(`XCOM-UDI-04`); no unit claims concurrency safety it does not implement.

## 8. Bounds and overflow catalogue

| Unit | Bounds (kind, resource) | Configuring source | Overflow policy set |
| --- | --- | --- | --- |
| `XCOM-DU-001`, `003`, `005`, `012` | bytes (payload/view size), capacity (value elements) | unit configuration / `io.xverse.xcom` Profile | `["fail-closed"]` |
| `XCOM-DU-002`, `004` | bytes (descriptor/diagnostic size) | unit configuration | `["n/a"]` |
| `XCOM-DU-006` | capacity (active endpoints/routes), retry (`0`) | activation plan | `["reject"]` |
| `XCOM-DU-007` | capacity (registered providers), retry (`0`) | explicit composition input | `["reject"]` |
| `XCOM-DU-008` | capacity (per-route in-flight queue depth), retry (`0`) | activation plan | `["reject","fail-closed"]` |
| `XCOM-DU-009` | bytes (graph input), capacity (compiled nodes/edges) | XDL input / unit configuration | `["fail-closed"]` |
| `XCOM-DU-010` | bytes (schema artifact) | static artifact | `["n/a"]` |
| `XCOM-DU-011` | bytes (plan bytes), capacity (decoded entities), depth (nesting) | activation plan | `["fail-closed"]` |
| `XCOM-DU-013` | capacity (per-tap queue depth), quota (coalesce window), retry (`0`) | tap policy | `["drop-newest","coalesce","lossless-backpressure"]` |
| `XCOM-DU-014` | timeout (bounded clock read), deadline (mapping tolerance) | session time-authority policy | `["n/a"]` |
| `XCOM-DU-015` | capacity (armed sessions), rate (requests per interval), quota (actions per session), deadline (validity interval) | validation permit | `["reject","fail-closed"]` |
| `XCOM-DU-016` | bytes (journal record size), capacity (finite retained records / retention) | journal configuration | `["fail-closed"]` |
| `XCOM-DU-017` | quota (actions), depth (loop-detection window), rate | validation permit | `["reject","fail-closed"]` |
| `XCOM-DU-018` | capacity (leases), depth (drain queue), deadline (drain deadline) | activation plan / permit | `["fail-closed","reject"]` |
| `XCOM-DU-019` | bytes (message/stream size), capacity (streams) | tool API schema | `["fail-closed"]` |
| `XCOM-DU-020` | capacity (concurrent sessions/streams), bytes (message size), deadline, timeout, rate | gateway configuration | `["fail-closed","reject"]` |
| `XCOM-DU-021` | deadline, timeout, bytes | tool client configuration | `["n/a"]` |
| `XCOM-DU-022`–`030` | bytes (artifact size), thread-count (`1`), timeout (validation runtime) | offline tooling configuration | `["n/a"]` |

Every bound is finite and `configured = true`; `value` is null unless the unit's own configuration fixes a
bounded value (only `retry = 0` and `thread-count = 1` are fixed by T010). No production capacity, rate, or
deadline value is asserted. This realises FR-007/FR-008/FR-013 and T009 `XCOM-INV-05`.

## 9. Failure-semantics catalogue

| Unit group | Representative condition → outcome |
| --- | --- |
| `XCOM-DU-001`, `003`, `005` | malformed value/payload → `rejected`; declared bound exceeded → `failed`; indeterminate → `failed` |
| `XCOM-DU-002`, `004` | incompatible contract/identity → `rejected`; internal defect → `failed` |
| `XCOM-DU-006`, `007` | stale, foreign, or duplicate handle → `rejected`; provider failure → `failed`; unknown → `failed` |
| `XCOM-DU-008` | policy violation → `rejected`; loopback failure → `failed`; unknown → `failed` |
| `XCOM-DU-009`, `011` | invalid/malformed input → `rejected`; bound exceeded → `failed`; unknown → `failed` |
| `XCOM-DU-012` | payload policy absent → `rejected`; view beyond bound → `rejected` with truncation recorded |
| `XCOM-DU-013` | queue saturated at the declared bound → classified `rejected` under the `drop-newest` tap policy, while `coalesce` merges the offered record into the pending one and `lossless-backpressure` backpressures the producer before any record is lost (neither is a rejection), the selected policy and its counter being surfaced; observer detached → `failed` isolated from the normal route |
| `XCOM-DU-014` | unmapped or out-of-tolerance clock domain → `invalid`/`rejected` before emission; elapsed validity → `expired` |
| `XCOM-DU-015` | missing/consumed/mismatched permit → `rejected`; validity elapsed → `expired`; quota exceeded → `rejected` |
| `XCOM-DU-016` | journal write/fsync failure or disk full → `evidence-incomplete`; intent recorded without outcome → `evidence-incomplete`; unknown → `evidence-incomplete` (never `accepted`) |
| `XCOM-DU-017` | schema/target/direction/action/time/quota/loop/ownership mismatch → `rejected` with zero emission and no state mutation |
| `XCOM-DU-018` | lease conflict → `rejected`; revoke/expiry/disconnect → `cancelled`/`expired`; emission without outcome → `evidence-incomplete` |
| `XCOM-DU-020`, `021` | unauthorized/expired session → `rejected`/`expired`; transport or peer failure → `failed`; disconnected after intent → `evidence-incomplete` |
| `XCOM-DU-022`–`030` | invalid tooling input → `failed`; unavailable dependency → `failed` (fail-closed) |

Rules (`XCOM-UDI-07`): an unknown or incomplete outcome is never reported as `accepted` or `delivered`;
configuration/authorization/validation errors fail before activation or emission; and a rejection never
mutates operational state or emits a normal-route item.

## 10. Doxygen plan (DOX-01)

### 10.1 Admitted configuration and target

| Field | Value |
| --- | --- |
| Configuration | `Doxyfile` (admitted, read-only for T010) |
| Warning gate | `WARN_AS_ERROR = YES` |
| Current strictness | `WARN_IF_UNDOCUMENTED = NO`, `WARN_NO_PARAMDOC = NO` (global) |
| Strict target | `WARN_IF_UNDOCUMENTED = YES`, `WARN_NO_PARAMDOC = YES` for the owned C++ inputs |
| Strict owners | T011 (admission) and T037 (execution) |
| Gate | `scripts/check_doxygen.py` plus the strict C++ configuration |
| Existing aliases | `@ownership`, `@lifetime`, `@thread_safety`, `@failure`, `@unitspec{1}` |
| Mandatory file block | `@file`, `@brief`, `@ingroup` |
| Mandatory public tags | `@brief`, `@ownership`, `@lifetime`, `@thread_safety`, `@failure` |
| Conditional public tags | `@param`, `@return`, `@retval` (outcome-returning units), `@note` (bounds), `@pre`/`@post` (preconditions) |
| Groups | `CORE → xcom_core`, `XDL → xcom_xdl`, `OBS → xcom_obs`, `STIM → xcom_stim`, `GW → xcom_gw`, `INTG → xcom_intg`, `ENB → xcom_enb` |
| Coverage rule | every public declaration in a C++ unit's header is documented; every unit header carries the mandatory file block; the ownership/lifetime/thread-safety/failure aliases are present on every public declaration |

### 10.2 Known gaps (recorded, never reported as closed)

| Gap | Description | Owning tasks | Status |
| --- | --- | --- | --- |
| `DOX-GAP-01` | `Doxyfile` sets `WARN_IF_UNDOCUMENTED = NO` and `WARN_NO_PARAMDOC = NO`; the strict C++ configuration is not yet admitted | T011, T037 | allocated |
| `DOX-GAP-02` | Generated protobuf C++ (`*.pb.h`/`*.pb.cc`) provenance and documentation policy are admitted by T011 | T011 | allocated |
| `DOX-GAP-03` | System and third-party headers are out of documentation scope; the allowed exclusion list is admitted by T011 | T011, T037 | allocated |

### 10.3 Per-unit obligations

All 19 `cpp` units (`XCOM-DU-001`–`008`, `011`, `012`–`018`, `020`, `021`, `025`) declare
`doxygen.required = true` with the family group, the mandatory file block, the mandatory public tags, and
`documented_elements == public_elements`. The 11 non-`cpp` units declare `doxygen.required = false` with a
reason (schema/definition artifact, Python tooling, or evidence document). `XCOM-DU-019` (proto) is not a
hand-written C++ interface; its generated-code documentation policy is `DOX-GAP-02`.

T010 owns the plan only. It generates no Doxygen output, changes no `Doxyfile`, and asserts no warning-free
result; T037 produces that evidence once T011 admits the strict configuration.

## 11. Invariant catalogue

| Invariant | Kind | Statement (abridged) | Enforcing check |
| --- | --- | --- | --- |
| `XCOM-UDI-01` | ownership | Every unit has exactly one owning slice and a task set consistent with the T007 register. | CHK-03, CHK-11 |
| `XCOM-UDI-02` | ownership | Only an exact issued handle mutates, closes, or replaces an active resource. | CHK-04 |
| `XCOM-UDI-03` | lifetime | Immutable values and static artifacts are shared without synchronization. | CHK-05 |
| `XCOM-UDI-04` | thread-safety | Every shared mutable state is protected by a declared synchronization mechanism or boundary. | CHK-05 |
| `XCOM-UDI-05` | bounds | Every queue, quota, depth, rate, byte, and retry bound is finite and declared with its source. | CHK-06 |
| `XCOM-UDI-06` | bounds | No unit silently retries or silently upgrades delivery guarantees. | CHK-06 |
| `XCOM-UDI-07` | failure | An unknown or incomplete outcome is never reported as success. | CHK-07 |
| `XCOM-UDI-08` | doxygen | Every public C/C++ interface documents its ownership, lifetime, thread-safety, and failure contract. | CHK-08 |
| `XCOM-UDI-09` | lifetime | Payload views have an explicit bounded lifetime and metadata-only is the observation default. | CHK-04, CHK-05 |
| `XCOM-UDI-10` | failure | Synthetic provenance survives routing, observation, and restart classification. | CHK-07 |
| `XCOM-UDI-11` | dependency | Dependencies flow one-way blueprints → profiles → XDL/platform → runtime; subsystem naming is preserved. | CHK-11 |
| `XCOM-UDI-12` | neutrality | No core unit embeds a domain-specific primitive (ECU, CAN, SOME/IP, Zenoh, or a product name). | CHK-11 |
| `XCOM-UDI-13` | safety | The first proof executes no legacy workload, contacts no external peer, and exposes no TCP listener except the host-protected local tool gateway. | CHK-11 |
| `XCOM-UDI-14` | documentation | Every unit declares explicit, classified failure semantics and planned evidence. | CHK-07, CHK-10 |

`XCOM-UDI-05`–`08` and `XCOM-UDI-13` are the **pinned safety/contract invariants**: the validator requires
them to be present *and* to carry their accepted `(kind, statement)` text, so removing or weakening one (for
example permitting an unbounded queue, a silent retry, an unknown-as-success outcome, an undocumented public
interface, or a TCP listener) is a `GOVERNANCE_INVALID` failure (9); the pinned-invariant branch of
`_check_governance` reports only that class. Each invariant's `enforcing_check` names the primary catalogue
check that proves its content: `XCOM-UDI-05`/`-06` → CHK-06 (bounds), `-07` → CHK-07 (failure),
`-08` → CHK-08 (doxygen), `-13` → CHK-11 (safety).

## 12. Validator design

### 12.1 Interface

`scripts/validate_xcom_unit_design.py` supports:

| Mode | Behaviour |
| --- | --- |
| `--self-test` | Runs controlled positive and negative fixtures for every NEG case. |
| `--verify` (default) | Validates `unit-design.json` against §3–§11 and §12.2. |
| `--check-human` | Confirms `design-units.md` is the deterministic projection of the JSON model. |

Exit classes (distinct nonzero per class; lowest numeric when several apply):

| Exit | Class | Covers |
| ---: | --- | --- |
| 0 | `OK` | Valid unit-design model |
| 2 | `SCHEMA_INVALID` | Top-level/per-record field, ordering, uniqueness, count, or non-string/unhashable unit id |
| 3 | `IDENTITY_INVALID` | Duplicate id, wrong id pattern, unknown family/kind/language/maturity/outcome token, missing mandatory field, or a unit with no artifact path |
| 4 | `OWNERSHIP_INVALID` | Missing ownership/lifetime model, missing view lifetime, no owning task, mutable unit without an issued-handle rule, or ownership inconsistent with the T007 register |
| 5 | `THREAD_INVALID` | Missing thread-safety model, shared state with an immutable-value model, `internally-synchronized` without a mechanism, or a message-passing/process claim without the required boundary or bound |
| 6 | `BOUNDS_INVALID` | Missing bound, non-integer/negative value, capacity/quota/depth/rate bound without an overflow policy set, `["n/a"]` with such a bound, or a permitted non-zero retry |
| 7 | `FAILURE_INVALID` | Missing failure semantics, unknown outcome token, unknown mapped to success, or a journal/write unit without `evidence-incomplete` |
| 8 | `DOXYGEN_INVALID` | A `cpp` unit missing a mandatory tag or group, a plan without the warning-as-error rule, an element-coverage mismatch, or a non-`cpp` unit claiming an obligation |
| 9 | `GOVERNANCE_INVALID` | Unknown governing ADR, promoted REF-002 target, unproven `implemented`, unreconciled `partial` without a reason, reverse dependency, or core domain primitive |
| 10 | `BINDING_INVALID` | Malformed baseline, unknown authorization reference, dangling requirement/component/contract reference, uncovered required element, invalid exemption, or an unavailable/malformed dependency |
| 11 | `DETERMINISM_INVALID` | Two serializations or the Markdown projection differ |
| 12 | `PUBLIC_SAFETY_INVALID` | Prohibited content class found |
| 13 | `PATH_INVALID` | `established` path absent from the tree or `planned` path present in the tree |
| 14 | `IO_ERROR` | Input unreadable or over bound |

### 12.2 Algorithm

```text
validate(model, task_ownership, requirement_register, architecture_model):
  require the three dependency files present, readable, well-formed; else BINDING_INVALID (10)
  check schema_version, task_id, capability, baseline_revision (40-hex), candidate_revision_rule
  check each fixed vocabulary equals its declared set (authored order significant)
  check authorization_records == the T007 closed set; adr_vocabulary closed
  check counts equal the entry counts per family/invariant and no family is empty
  check every units/invariants entry id is a non-empty string (else SCHEMA_INVALID 2)
  check units/invariants sorted by id and ids unique
  for each unit:
    check id pattern, required-id membership, family/kind/language/scope/maturity in vocabulary
    check owning_slice/tasks consistent with the T007 register
    check accepted_revision 40-hex iff implemented else null
    check reconciliation present iff partial-and-unreconciled else null
    check >= 1 artifact_path with status in {established, planned}
    check ownership_model/lifetime_model in vocabulary with non-empty rationales
    check exposes_view => non-empty, non-"n/a" view_lifetime; else view_lifetime null
    check thread_safety.model in vocabulary; consistency rules of §3.1
    check >= 1 bound; kind in vocabulary; value null or non-negative integer;
          capacity/quota/depth/rate present => non-empty overflow policy set without "n/a"; else ["n/a"]
    check failure_semantics non-empty; outcomes in vocabulary; unknown never success;
          journal/write units declare evidence-incomplete
    check doxygen: cpp => required true with group/file_block/public_tags and equal element counts;
          non-cpp => required false with a reason
    check requirement_links non-empty and each resolves in the T008 register
    check component_refs/contract_refs resolve in the T009 model
    check governing_adrs subset of adr_vocabulary
  check required unit set exactly XCOM-DU-001..030
  check every non-exempt T009 component is covered by >= 1 unit
  check every non-exempt XCOM-SW-* register requirement is covered by >= 1 unit
  check every exemption is real (its target is not covered) and carries a reason and owning tasks
  check the pinned invariants are present AND match their accepted (kind, statement) text
  check no promoted REF-002 id and no implemented record for a deferred/allocated target
  check dependency-direction, core-neutrality, and safety invariants present and enforced
  check established paths exist on disk and planned paths do not (PATH_INVALID 13)
  check determinism: re-serialize; require byte-identical
  check public-safety: scan for absolute paths, credentials, private addresses, key markers
  report highest-precedence failure or OK
```

### 12.3 REF-002 handling

The model records `ref002.disposition = "unchanged"` with an empty `promoted` list. T010 promotes no target,
and the validator rejects a non-empty promoted list or an `implemented` record asserted for a deferred,
allocated, or unreconciled target (exit 9). The authoritative disposition table remains
`specs/007-xcom-core/reference-traceability.md` and `docs/architecture/sads-requirements-traceability.json`.

## 13. Ordering, coverage, and cross-resolution constraints (validator-enforced)

1. `units` and `invariants` are sorted by `id` with unique ids; every id is a non-empty string.
2. The required unit set is exactly `XCOM-DU-001`–`030`; declared counts match the entries.
3. Every unit has ≥ 1 artifact path; `established` paths exist and `planned` paths are absent.
4. Every unit declares ownership, lifetime, thread-safety, bounds, and failure contracts consistent with §6–§9.
5. Every `requirement_links` entry resolves in the T008 register, and every non-exempt `XCOM-SW-*`
   requirement is covered.
6. Every `component_refs`/`contract_refs` entry resolves in the T009 model, and every non-exempt T009
   component is covered by ≥ 1 unit.
7. Every `cpp` unit declares its Doxygen obligation; the plan declares the warning-as-error rule and its gaps.
8. Every exemption (component or requirement) is real, reasoned, and task-owned.
9. The pinned invariants are present with their accepted text; the dependency-direction, neutrality, and
   safety invariants are enforced.

Each constraint is enforced by a distinct check function; the implementation neutralises one check at a time
and confirms the corresponding NEG fixture fails, so all check functions are load-bearing
(`verification-plan.md` DET-04).

## 14. Alternatives considered

| Alternative | Rejected because |
| --- | --- |
| Keep unit design only as prose in this package | Not machine checkable; per-unit ownership/lifetime/thread-safety/failure/bounds/Doxygen consistency, coverage, and cross-resolution to T008/T009 cannot be proven absent. |
| Duplicate the full unit contract in `design-units.md` tables and leave JSON advisory | Two authorities drift; the JSON model is canonical and the Markdown is its deterministic projection. |
| Fix production numeric bounds in T010 | The values come from the activation plan or unit configuration (FR-007); inventing them would be an unsupported production claim. |
| Model only the C++ units | The Python plan compiler, the JSON schema, and the documentation/evidence units carry their own ownership, failure, and Doxygen obligations and would be uncovered. |
| Fold the Doxygen plan into T011/T037 | FR-029 requires every public interface and changed unit to document ownership, thread-safety, failure, and lifetime; the plan is design input those tasks execute, and T010 is the task entry that owns it. |
| Strengthen `Doxyfile` in this candidate | It is an admitted shared configuration owned by the toolchain capability and admitted by T011; changing it here would exceed the work-product boundary and claim unexecuted verification. |
| Mark the reviewed T007–T009 work products `implemented` | Source/review presence is not user acceptance (Constitution art. IX; ADR-0020); they stay `partial` with a reconciliation reason. |
| Reuse the T009 exit-code numbers exactly | T010 has distinct rule families (ownership/lifetime, thread-safety, bounds, failure, Doxygen); a dedicated class per family keeps each failure independently observable. |

## 15. Requirement-to-design trace

| Requirement | Design section |
| --- | --- |
| T010-SR-001 | §3, §3.5, §3.6, §12 |
| T010-SR-002 | §3, §5 |
| T010-SR-003 | §3, §6 |
| T010-SR-004 | §3.1, §7 |
| T010-SR-005 | §3.2, §8 |
| T010-SR-006 | §3.3, §9 |
| T010-SR-007 | §3.4, §10 |
| T010-SR-008 | §3, §13 |
| T010-SR-009 | §3, §13 |
| T010-SR-010 | §11, §12.3 |
| T010-SR-011 | §4, §12.2 |
| T010-SR-012 | §2, §4 |
| T010-SR-013 | §4, §12.2 |
| T010-SR-014 | §4, §12, §13 |
