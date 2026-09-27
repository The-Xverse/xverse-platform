# T009 Detailed Design — Architecture Model Schema, Catalogues, and Validator

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T009 |
| Stage / role | plan → detailed design |
| Revision | 1 |
| Baseline revision | `209084b11a211273f815980f753ba728e1251a09` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 1 |
| Maturity | Governance/planning target; documentation-and-script candidate |

## 2. Implementation artifacts (what the T009 candidate adds)

T009 is a work-product task, so its "implementation" is the architecture model, its projection, and their
validator, all outside `src/`, `tests/`, `xdl/`, and `proto/`:

| Artifact | Path | Owner | Purpose |
| --- | --- | --- | --- |
| Architecture model (machine) | `docs/engineering/xcom/t009/architecture-model.json` | T009 | Canonical component/boundary/contract/diagram/invariant model |
| Architecture model (human) | `docs/engineering/xcom/t009/architecture-model.md` | T009 | Deterministic projection including Mermaid diagrams |
| Model validator | `scripts/validate_xcom_architecture_contracts.py` | T009 | Offline, deterministic, bounded checks with a self-test |
| Implementation record | `docs/engineering/xcom/t009/implementation.md` | T009 | Candidate revision, commands, outcomes, limitations |
| Capability task state | `specs/007-xcom-core/tasks.md` | shared | Mark T009 complete only in the implementation stage |
| Ownership consistency | `docs/engineering/xcom/task-ownership.{json,md}` | shared | Record the new validator path in `T-ENABLER`, then re-run `scripts/validate_xcom_task_ownership.py` |

The five plan-stage work products (`requirements.md`, `architecture.md`, `detailed-design.md`,
`unit-specifications.md`, `verification-plan.md`) are documentation; they are produced before this
implementation. No `src/`, `tests/`, `xdl/`, or `proto/` path is created or changed.

## 3. Architecture model schema (version 1)

Top-level object (`schema_version = 1`):

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | integer | `= 1` |
| `task_id` | string | `= "T009"` |
| `capability` | string | `= "007-xcom-core"` |
| `baseline_revision` | string | 40-hex; must equal the run baseline |
| `candidate_revision_rule` | string | States successor candidates bind their own and predecessor revisions |
| `layer_vocabulary` | array of string | Exactly the nine layers (sorted) |
| `language_vocabulary` | array of string | Exactly `["cpp","external","json","protobuf","python"]` (sorted) |
| `boundary_kind_vocabulary` | array of string | Exactly `["artifact","data","in-process","ipc","language","realization","trust"]` (sorted) |
| `contract_kind_vocabulary` | array of string | Exactly `["cross-language-schema","external-rpc","in-process-cpp","schema"]` (sorted) |
| `diagram_kind_vocabulary` | array of string | Exactly `["component","sequence"]` |
| `maturity_vocabulary` | array of string | Exactly the seven accepted maturity tokens |
| `invariant_kind_vocabulary` | array of string | Exactly `["architecture","data-model","dependency","neutrality","safety"]` (sorted) |
| `direction_vocabulary` | array of string | Exactly `["bidirectional","one-way","request-response","stream"]` (sorted) |
| `authorization_vocabulary` | array of string | Exactly `["exact-handle-required","none","plan-digest-bound","tap-policy-required","validation-permit-required"]` (sorted) |
| `adr_vocabulary` | array of string | Exactly `["ADR-0016","ADR-0018","ADR-0019","ADR-0020"]` |
| `authorization_records` | array of string | Exactly the T007 closed set: ACC001–ACC015, ADR-0018, ADR-0019, ADR-0020 (sorted) |
| `ref002` | object | `{disposition: "unchanged", promoted: [], source: "specs/007-xcom-core/reference-traceability.md"}` |
| `counts` | object | Declared expected counts per family, validated against the entries |
| `components` | array of object | Sorted by `id`, ids unique |
| `boundaries` | array of object | Sorted by `id`, ids unique |
| `contracts` | array of object | Sorted by `id`, ids unique |
| `diagrams` | array of object | Sorted by `id`, ids unique |
| `invariants` | array of object | Sorted by `id`, ids unique |

Component object:

| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | `XCOM-CMP-###`; unique |
| `name` | string | Non-empty |
| `layer` | string | One of `layer_vocabulary` |
| `language` | string | One of `language_vocabulary` |
| `scope` | string | `first-proof` \| `later` |
| `responsibility` | string | Non-empty, one bounded sentence |
| `owning_slice` | string | A T007 slice id, or `external`/`downstream`; layer `external` ⇒ `external`, layer `downstream` ⇒ `downstream` |
| `owning_tasks` | array of string | Sorted `T0xx`; empty iff `owning_slice` is `external`/`downstream` |
| `maturity` | string | One of `maturity_vocabulary` |
| `accepted_revision` | string or null | 40-hex iff `maturity == implemented`; else null |
| `reconciliation` | string or null | Required non-empty for `partial` components whose baseline source is unreconciled; else null |
| `artifact_paths` | array of object | `{path, status}`, `status ∈ {established, planned}`, sorted by `path`; non-empty |
| `requirement_links` | array of string | Non-empty; each resolves to a T008 register requirement id or an accepted `FR-###`/`SC-###`/`US#` anchor (`FR-001`–`FR-035`, `SC-001`–`SC-011`, `US1`–`US4`); a pattern-matching but unaccepted anchor such as `FR-999` is rejected |
| `governing_adrs` | array of string | Non-empty; subset of `adr_vocabulary` |
| `constraints` | array of string | Non-empty |
| `intra_layer` | boolean | `true` only for an internal core component that owns no boundary of its own |

Boundary object:

| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | `XCOM-XB-###`; unique |
| `name` | string | Non-empty |
| `kind` | string | One of `boundary_kind_vocabulary` |
| `from_component`, `to_component` | string | Resolve to declared component ids |
| `from_language`, `to_language` | string | One of `language_vocabulary`; both ⊆ resolved contract `endpoint_languages`; for `kind == language` they differ |
| `direction` | string | One of `direction_vocabulary` |
| `scope` | string | `first-proof` \| `later` |
| `contract` | string | Resolves to a declared contract id |
| `authorization` | string | One of `authorization_vocabulary` |
| `safety` | array of string | Non-empty |
| `failure_semantics` | string | Non-empty |
| `maturity` | string | One of `maturity_vocabulary` |
| `accepted_revision` | string or null | 40-hex iff `implemented`; else null |

Contract object:

| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | `XCOM-XLC-###`; unique |
| `name` | string | Non-empty |
| `kind` | string | One of `contract_kind_vocabulary` |
| `producer_components`, `consumer_components` | array of string | Non-empty; resolve to declared component ids |
| `endpoint_languages` | array of string | Non-empty subset of `language_vocabulary`, sorted |
| `version` | string | Non-empty |
| `canonical_artifact` | string | Repository-relative path, or `n/a` only for an in-process C++ contract with no file |
| `encoding` | string | Non-empty |
| `unknown_field_policy` | string | `fail-closed` \| `n/a` (the latter only for in-process C++ contracts) |
| `evolution_rule` | string | Non-empty, additively stated |
| `governing_adrs` | array of string | Non-empty; subset of `adr_vocabulary` |
| `maturity` | string | One of `maturity_vocabulary` |
| `accepted_revision` | string or null | 40-hex iff `implemented`; else null |

Diagram object:

| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | `XCOM-DGM-###`; unique |
| `kind` | string | `component` \| `sequence` |
| `title` | string | Non-empty |
| `user_story` | string | `US1`..`US4` for `sequence`; `-` for `component` |
| `participants` | array of string | Non-empty; resolve to declared component ids, sorted |
| `steps` | array of object | `{from, to, boundary, note}`; empty for `component`, non-empty for `sequence`; `from`/`to` resolve to participants; `boundary` resolves to a declared boundary; `note` non-empty |

Invariant object:

| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | `XCOM-INV-##`; unique |
| `kind` | string | One of `invariant_kind_vocabulary` |
| `statement` | string | Non-empty; for the required safety-boundary invariants it must equal the pinned accepted text |
| `applies_to` | array of string | Non-empty; resolves to declared component or boundary ids |
| `source` | string | Non-empty accepted anchor (`data-model.md invariant n`, `spec FR-###`, `ADR-####`, `contracts/*.md`) |
| `enforcement` | string | Non-empty; names the enforcing `CHK-`/`ORD-`/`DET-` id |

Every family entry's `id` is a non-empty string; a non-string id is a `SCHEMA_INVALID` (2) failure rather
than an uncaught type error in the ordering or uniqueness checks.

**Array ordering (normative).** The validator enforces ascending `id` order and id uniqueness for exactly
the five top-level arrays `components`, `boundaries`, `contracts`, `diagrams`, and `invariants`. No other
array carries a lexical sort guarantee: the fixed vocabularies are compared by exact equality (authored
order significant); `authorization_records`, `adr_vocabulary`, `owning_tasks`, `participants`,
`endpoint_languages`, and each `artifact_paths` list are stored sorted and duplicate-free; and
`requirement_links`, `governing_adrs`, `safety`, `constraints`, `applies_to`, and diagram `steps`
preserve their authored order.

**Derivation rule.** Each record is elaborated from the accepted plan/data-model/contracts. `counts`
records the realized count per family; the validator checks each declared count equals the number of
entries in that family and that no family is empty. T009 never invents a component, boundary, or contract
that the accepted plan does not sanction; where the accepted source is silent, the record is marked
`needs_clarification` and reported.

### 3.1 Expected counts

| Family | Count | Notes |
| --- | ---: | --- |
| `XCOM-CMP-###` | 13 | `XCOM-CMP-001`–`013` (§5) |
| `XCOM-XB-###` | 11 | `XCOM-XB-001`–`011` (§6) |
| `XCOM-XLC-###` | 6 | `XCOM-XLC-001`–`006` (§7) |
| `XCOM-DGM-###` | 5 | `XCOM-DGM-001`–`005` (§8) |
| `XCOM-INV-##` | 15 | `XCOM-INV-01`–`15` (§9) |

## 4. Determinism, bounds, and safety rules

- **Determinism (T009-SR-001, T009-SR-013).** Stable key/element ordering; no timestamps, hostnames,
  absolute paths, or unordered iteration in the model, projection, or validator output.
- **Bounds (T009-STK-007).** The validator reads only repository-relative files, each ≤ 1 MiB; total input
  ≤ 4 MiB; no recursion outside the repository; wall-clock timeout ≤ 60 s; single-threaded.
- **Offline (T009-SR-013).** No network client, resolver, package manager, or subprocess shell; only file
  reads and pure computation. `git`-based path checks are performed by the deterministic gate and the
  implementation record, not inside the validator.
- **Public safety (T009-SR-012).** No credential, secret, private address, private-key marker,
  proprietary source excerpt, unrestricted payload, or absolute host path in the model, projection, or
  validator output.
- **Docs-only boundary (T009-SR-011).** The candidate diff contains no `src/`, `tests/`, `xdl/`, or
  `proto/` path, no accepted-ADR rewrite, and no weakened requirement or test. The single added script
  lives under `scripts/`.
- **Ownership consistency (T009-SR-013).** The new script path is recorded under `T-ENABLER`
  `paths_exclusive` in `docs/engineering/xcom/task-ownership.json` and its projection; the change is
  regenerated deterministically and `scripts/validate_xcom_task_ownership.py --verify` and `--check-human`
  must both exit 0 afterwards. No other slice's ownership is changed.
- **Fail-closed dependencies (T009-SR-009, T009-SR-010).** The validator requires
  `docs/engineering/xcom/task-ownership.json` (reconciliation state) and
  `docs/engineering/xcom/t008/requirements-register.json` (requirement-link resolution) to be present,
  readable, and well-formed; an unavailable or malformed dependency is a hard `BINDING_INVALID` (9), never
  a skipped check.

## 5. Component catalogue

Identifiers fix the candidate-chosen names. Layer abbreviations: `xdl-input`, `build-time`,
`derived-artifact`, `data-plane`, `boundary`, `edge`, `test-fixture`, `external`, `downstream`.

| Component | Layer | Language | Scope | Owns | Maturity | Anchored paths (status) |
| --- | --- | --- | --- | --- | --- | --- |
| `XCOM-CMP-001` Normalized XDL input | xdl-input | python | first-proof | T-XDL (T018) | partial | `xdl/metamodel/NORMALIZED_MODEL.md` (established), `xdl/schemas/v1alpha1/` (established) |
| `XCOM-CMP-002` X-COM Profile/plan compiler | build-time | python | first-proof | T-XDL (T017, T018) | allocated | `xdl/profiles/xcom-v0.1.schema.json` (planned), `src/xverse_xdl/xcom_plan.py` (planned), `tests/test_xcom_plan.py` (planned) |
| `XCOM-CMP-003` Canonical activation plan | derived-artifact | json | first-proof | T-XDL (T017, T019) | allocated | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` (planned) |
| `XCOM-CMP-004` Core value/contract/diagnostic types | data-plane | cpp | first-proof | T-CORE (T013) | partial | `src/xverse/xcom/include/xverse/xcom/contract.hpp` etc. (established) |
| `XCOM-CMP-005` Endpoint/route lifecycle and handles | data-plane | cpp | first-proof | T-CORE (T014) | partial | `src/xverse/xcom/include/xverse/xcom/endpoint_route_lifecycle.hpp`, `src/xverse/xcom/src/endpoint_route_lifecycle.cpp`, `tests/xcom/endpoint_route_lifecycle/` (established) |
| `XCOM-CMP-006` Provider boundary and composition | data-plane | cpp | first-proof | T-CORE (T015) | partial | `src/xverse/xcom/include/xverse/xcom/provider.hpp`, `src/xverse/xcom/src/provider.cpp` (established) |
| `XCOM-CMP-007` Owned loopback provider | test-fixture | cpp | first-proof | T-CORE (T015, T016) | partial | `src/xverse/xcom/include/xverse/xcom/loopback_provider.hpp`, `src/xverse/xcom/src/loopback_provider.cpp`, `tests/xcom/provider_loopback/` (established) |
| `XCOM-CMP-008` Observation boundary | boundary | cpp | first-proof | T-OBS (T021–T023) | partial | `src/xverse/xcom/include/xverse/xcom/observation.hpp`, `src/xverse/xcom/src/observation.cpp`, `tests/xcom/observation/` (established) |
| `XCOM-CMP-009` Validation stimulation session | boundary | cpp | first-proof | T-STIM (T025) | implemented | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp`, `src/xverse/xcom/src/validation_session.cpp`, `tests/xcom/validation_session/` (established) |
| `XCOM-CMP-010` Local tool gateway | edge | cpp | first-proof | T-CORE (T030–T032) | allocated | `proto/xverse/xcom/v1/tool_gateway.proto` (planned), `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` (planned), `src/xverse/xcom/src/tool_gateway.cpp` (planned), `tests/xcom/tool_gateway/` (planned) |
| `XCOM-CMP-011` Synthetic sink and tools | test-fixture | cpp | first-proof | T-OBS/T-CORE (T023, T032, T033) | partial | `tests/xcom/observation/integration/` (established), `src/xverse/xcom/fixtures/synthetic_tool.cpp` (planned), `tests/xcom/tool_gateway/` (planned) |
| `XCOM-CMP-012` External validation tool | external | external | later | external | allocated | `n/a` (out of process, not owned) |
| `XCOM-CMP-013` Argus observation adapter | downstream | external | later | downstream | allocated | `src/xverse/argus/` (planned) |

`XCOM-CMP-005` is the only `intra_layer = true` component: it is an internal core unit with no boundary of
its own and appears in diagrams as a core participant. `XCOM-CMP-009` and its contract `XCOM-XLC-006` carry
`accepted_revision = 4b01586b438a8587d231ee8828d896c206c06a96` (the accepted T025 merge); `XCOM-CMP-001`
carries the capability-004 interface with a recorded reconciliation note (no runtime claim).

## 6. Boundary catalogue

| Boundary | Kind | From → To | Languages | Direction | Contract | Authorization | Scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `XCOM-XB-001` | data | CMP-001 → CMP-002 | python → python | one-way | XLC-005 | none | first-proof |
| `XCOM-XB-002` | artifact | CMP-002 → CMP-003 | python → json | one-way | XLC-001 | none | first-proof |
| `XCOM-XB-003` | language | CMP-003 → CMP-004 | json → cpp | one-way | XLC-001 | plan-digest-bound | first-proof |
| `XCOM-XB-004` | in-process | CMP-004 → CMP-006 | cpp → cpp | bidirectional | XLC-004 | exact-handle-required | first-proof |
| `XCOM-XB-005` | in-process | CMP-004 → CMP-008 | cpp → cpp | one-way | XLC-003 | tap-policy-required | first-proof |
| `XCOM-XB-006` | trust | CMP-008 → CMP-013 | cpp → cpp | one-way | XLC-003 | none | later |
| `XCOM-XB-007` | in-process | CMP-009 → CMP-004 | cpp → cpp | bidirectional | XLC-006 | validation-permit-required | first-proof |
| `XCOM-XB-008` | ipc | CMP-010 → CMP-012 | protobuf → external | bidirectional | XLC-002 | validation-permit-required | later |
| `XCOM-XB-009` | realization | CMP-007 → CMP-004 | cpp → cpp | bidirectional | XLC-004 | exact-handle-required | first-proof |
| `XCOM-XB-010` | ipc | CMP-011 → CMP-010 | protobuf → cpp | bidirectional | XLC-002 | validation-permit-required | first-proof |
| `XCOM-XB-011` | trust | CMP-008 → CMP-011 | cpp → cpp | one-way | XLC-003 | none | first-proof |

Each boundary declares non-empty `safety` and `failure_semantics`. Representative constraints:
`XCOM-XB-003` "unresolved identity/schema/capability/time/ownership fails closed before activation";
`XCOM-XB-008`/`XCOM-XB-010` "local IPC only; no TCP listener; transport access does not authorize
stimulation"; `XCOM-XB-005`/`XCOM-XB-011` "metadata-only by default; observer failure does not change
normal delivery"; `XCOM-XB-007` "fail-closed pre-emission guard; rejection emits zero normal-route items".

Boundary-kind/contract-kind consistency (validator-enforced): `data` ⇒ `schema`; `artifact` ⇒
`schema` or `cross-language-schema`; `language` ⇒ `cross-language-schema`; `in-process`/`realization` ⇒
`in-process-cpp`; `ipc` ⇒ `external-rpc`; `trust` ⇒ `in-process-cpp`, `external-rpc`, or
`cross-language-schema`.

## 7. Contract catalogue

| Contract | Kind | Producer(s) | Consumer(s) | Endpoint languages | Version | Canonical artifact | Maturity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `XCOM-XLC-001` Canonical activation plan | cross-language-schema | CMP-002 | CMP-003, CMP-004 | cpp, json, python | v1 | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` | allocated |
| `XCOM-XLC-002` Local tool gateway | external-rpc | CMP-010 | CMP-011, CMP-012 | cpp, external, protobuf | v1 | `proto/xverse/xcom/v1/tool_gateway.proto` | allocated |
| `XCOM-XLC-003` Observation record | in-process-cpp | CMP-008 | CMP-011, CMP-013 | cpp | v1 | `src/xverse/xcom/include/xverse/xcom/observation.hpp` | partial |
| `XCOM-XLC-004` Provider contract | in-process-cpp | CMP-006 | CMP-004, CMP-007 | cpp | v1 | `src/xverse/xcom/include/xverse/xcom/provider.hpp` | partial |
| `XCOM-XLC-005` XDL resource/Profile input | schema | CMP-001 | CMP-002 | python | v1alpha1 | `xdl/schemas/v1alpha1/xdl.schema.json` | partial |
| `XCOM-XLC-006` Validation stimulation/time | in-process-cpp | CMP-009 | CMP-004, CMP-010 | cpp | v1 | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp` | implemented |

`unknown_field_policy = fail-closed` for `XLC-001`, `XLC-002`, `XLC-005`, `XLC-006`; `n/a` for the
in-process C++ contracts `XLC-003`/`XLC-004`. Evolution rules are additively stated (for example
`XLC-002`: "additive field numbers only; reserved removed numbers/names; explicit protocol version
negotiation"). `XLC-001`, `XLC-002`, `XLC-005`, `XLC-006` cite ADR-0018/ADR-0019/ADR-0020 as applicable;
`XLC-003`/`XLC-004` cite ADR-0019/ADR-0018. `XLC-006` carries
`accepted_revision = 4b01586b438a8587d231ee8828d896c206c06a96`.

## 8. Diagram definitions

| Diagram | Kind | User story | Participants | Steps (from → to via boundary) |
| --- | --- | --- | --- | --- |
| `XCOM-DGM-001` | component | - | all 13 components | none |
| `XCOM-DGM-002` | sequence | US1 | CMP-001, CMP-002, CMP-003, CMP-004, CMP-005, CMP-006, CMP-007 | XB-001, XB-002, XB-003, XB-004, XB-009 |
| `XCOM-DGM-003` | sequence | US2 | CMP-004, CMP-008, CMP-011, CMP-013 | XB-005, XB-011, XB-006 |
| `XCOM-DGM-004` | sequence | US3 | CMP-004, CMP-008, CMP-009 | XB-007, XB-005 |
| `XCOM-DGM-005` | sequence | US4 | CMP-004, CMP-006, CMP-007, CMP-010, CMP-011, CMP-012 | XB-010, XB-008, XB-004, XB-009 |

Coverage is enforced in both directions: every component appears in ≥ 1 diagram `participants`; every
boundary appears in ≥ 1 diagram step; every contract is referenced by ≥ 1 boundary that appears in a step;
and US1–US4 each have exactly one `sequence` diagram. The Markdown projection renders each diagram as a
deterministic Mermaid block derived from its participants and steps, so the JSON remains authoritative.

## 9. Invariant catalogue

| Invariant | Kind | Statement (abridged) | Source |
| --- | --- | --- | --- |
| `XCOM-INV-01` | data-model | Logical identity never depends on provider address or handle. | data-model.md invariant 1 |
| `XCOM-INV-02` | data-model | No endpoint/route/tap/session is mutable without its exact issued handle. | data-model.md invariant 2 |
| `XCOM-INV-03` | data-model | Synthetic origin survives routing and observation. | data-model.md invariant 3 |
| `XCOM-INV-04` | data-model | At most one permitted service-emulation owner per endpoint and session. | data-model.md invariant 4 |
| `XCOM-INV-05` | data-model | All queues and quotas are finite with declared overflow behaviour. | data-model.md invariant 5 |
| `XCOM-INV-06` | data-model | Metadata-only observation contains no payload bytes. | data-model.md invariant 6 |
| `XCOM-INV-07` | data-model | Every activation and stimulation decision is bound to the exact plan digest. | data-model.md invariant 7 |
| `XCOM-INV-08` | safety | Local tool transport access never replaces validation-permit checks. | data-model.md invariant 8; spec FR-032 |
| `XCOM-INV-09` | data-model | Scheduled requests never compare or order unmapped clock domains. | data-model.md invariant 9; spec FR-033 |
| `XCOM-INV-10` | data-model | One endpoint generation has at most one active service-emulation lease. | data-model.md invariant 10 |
| `XCOM-INV-11` | dependency | Dependencies flow one-way blueprints → profiles → XDL/platform → runtime. | Constitution art. VIII; ADR-0018 |
| `XCOM-INV-12` | neutrality | Core components contain no domain-specific primitive. | Constitution art. II; spec FR-001 |
| `XCOM-INV-13` | safety | The first proof exposes no TCP listener except the host-protected local tool gateway. | spec FR-028/FR-032; tool-gateway contract |
| `XCOM-INV-14` | architecture | Python is confined to `xdl-input`/`build-time`; the data plane is C++. | plan "Technical Context"; AGENTS language directive |
| `XCOM-INV-15` | safety | The first proof executes no legacy workload and contacts no external network peer. | spec FR-028; ADR-0018 |

Every invariant resolves its `applies_to` to declared components/boundaries and maps to an enforcing check
id. The `safety`/`neutrality`/`dependency` invariants plus `INV-03`/`06` are the safety-boundary set the
validator requires: each must be present **and** carry its pinned accepted `(kind, statement)` text, so
removing one or weakening its statement (for example to permit a TCP listener, make the permit optional, or
default observation to payload capture) is a `SAFETY_INVALID` failure.

## 10. Validator design

### 10.1 Interface

`scripts/validate_xcom_architecture_contracts.py` supports:

| Mode | Behaviour |
| --- | --- |
| `--self-test` | Runs controlled positive and negative fixtures for every NEG case. |
| `--verify` (default) | Validates `architecture-model.json` against §3–§9 and §10.2. |
| `--check-human` | Confirms `architecture-model.md` is the deterministic projection of the JSON model. |

Exit classes (distinct nonzero per class, lowest numeric when several apply):

| Exit | Class | Covers |
| ---: | --- | --- |
| 0 | `OK` | Valid architecture model |
| 2 | `SCHEMA_INVALID` | Top-level/per-record field, non-string family id, array ordering/uniqueness, or schema version differs |
| 3 | `IDENTITY_INVALID` | Duplicate id, unknown layer/language/kind/maturity token, missing mandatory field, or a component with no artifact path |
| 4 | `BOUNDARY_INVALID` | Unresolved boundary endpoint, unknown kind, missing required boundary, or duplicated boundary id |
| 5 | `CONTRACT_INVALID` | Dangling boundary→contract reference, language mismatch, missing version/evolution rule, or duplicated contract id |
| 6 | `DIAGRAM_INVALID` | Unresolved participant/step, orphan step, or missing component/boundary/contract/user-story coverage |
| 7 | `GOVERNANCE_INVALID` | Unknown governing ADR, promoted REF-002 target, dependency-direction violation, core domain primitive, or unproven `implemented` maturity |
| 8 | `SAFETY_INVALID` | Missing or weakened declared safety/neutrality/dependency invariant |
| 9 | `BINDING_INVALID` | Malformed baseline, unknown authorization reference, unavailable dependency, or dangling requirement link |
| 10 | `DETERMINISM_INVALID` | Two serializations or the Markdown projection differ |
| 11 | `PUBLIC_SAFETY_INVALID` | Prohibited content class found |
| 12 | `PATH_INVALID` | `established` path absent from the tree or `planned` path present in the tree |
| 13 | `IO_ERROR` | Input unreadable or over bound |

### 10.2 Algorithm

```text
validate(model, task_ownership, requirement_register):
  require docs/engineering/xcom/task-ownership.json and
          docs/engineering/xcom/t008/requirements-register.json present and well-formed;
          else fail BINDING_INVALID (9)
  check schema_version, task_id, capability, baseline_revision, candidate_revision_rule
  check each fixed vocabulary equals its declared set (authored order significant)
  check authorization_records == the T007 closed set; adr_vocabulary closed
  check counts equal the entry counts per family and no family is empty
  check every family entry id is a non-empty string (non-string id => SCHEMA_INVALID 2)
  check components/boundaries/contracts/diagrams/invariants sorted by id and ids unique
  for each component:
    check id pattern, layer/language/scope/maturity in vocabulary, mandatory fields non-empty
    check owning_slice/tasks consistency (external/downstream layers)
    check accepted_revision 40-hex iff implemented, else null
    check reconciliation present iff partial-with-unreconciled-source
    check >= 1 artifact_path; status in {established, planned}
    check requirement_links non-empty and each resolves in the T008 requirement register
          or the accepted FR-001..035 / SC-001..011 / US1..US4 anchor set
    check governing_adrs subset of adr_vocabulary
  check established paths exist on disk and planned paths do not (PATH_INVALID 12)
  check required component set exactly XCOM-CMP-001..013
  for each boundary:
    check endpoints resolve to components; kind/direction/authorization in vocabulary
    check contract resolves; boundary kind => contract kind; from/to_language subset of endpoint_languages
    check kind == language => from_language != to_language
    check safety non-empty; failure_semantics non-empty
  check required boundary set exactly XCOM-XB-001..011
  for each contract:
    check producer/consumer components resolve; endpoint_languages subset/sorted
    check version/encoding/evolution_rule non-empty; unknown_field_policy legal for kind
    check governing_adrs subset; accepted_revision rule
  check contract set exactly XCOM-XLC-001..006
  for each diagram:
    check kind/user_story legality; participants resolve; steps empty iff component
    check sequence steps' from/to are participants and boundary resolves
  check diagram set exactly XCOM-DGM-001..005; exactly one US1..US4 sequence each
  check every component in >= 1 participants; every boundary in >= 1 step
  for each invariant:
    check kind in vocabulary; applies_to resolves; source/enforcement non-empty
  check no promoted REF-002 id and no implemented record for a deferred/allocated target
  check dependency-direction and core-neutrality invariants present and enforced
  check the required safety-boundary invariants are present AND match their pinned
        accepted (kind, statement) text (weakening => SAFETY_INVALID 8)
  check safety invariant set present
  check reconciliation consistency with the T007 register
  check determinism: re-serialize; require byte-identical
  check public-safety: scan for absolute paths, credentials, private addresses, key markers
  report highest-precedence failure or OK
```

### 10.3 REF-002 handling

The model records `ref002.disposition = "unchanged"` with an empty `promoted` list. T009 promotes no
`architectural-target` to `implemented`, and the validator rejects a non-empty promoted list or an
`implemented` record asserted for a deferred/allocated target (exit 7). The authoritative disposition table
remains `specs/007-xcom-core/reference-traceability.md` and
`docs/architecture/sads-requirements-traceability.json`.

## 11. Ordering and coverage constraints (validator-enforced)

1. `components`, `boundaries`, `contracts`, `diagrams`, `invariants` are sorted by `id` with unique ids.
2. Every boundary endpoint resolves to a declared component; the required boundary set is exactly present.
3. Every boundary resolves to a declared contract whose kind and endpoint languages fit the boundary.
4. The contract set is exactly `XLC-001`–`006` and every contract has version/encoding/evolution rule.
5. US1–US4 each have exactly one sequence diagram; every component, boundary, and contract is covered.
6. Every component has ≥ 1 artifact path; `established` paths exist and `planned` paths do not.
7. `implemented` requires an exact accepted revision; unreconciled baseline coverage is `partial` with a
   reason and is consistent with the T007 register.
8. Every safety/neutrality/dependency invariant is present, enforced, and (for the seven required
   safety-boundary invariants) carries its pinned accepted `(kind, statement)` text.

Each constraint is enforced by a distinct check; the self-test includes a schema fixture (NEG-01), a
non-string-id schema fixture (NEG-32), unhashable-container-id schema fixtures (NEG-35..NEG-39), a boundary
fixture (NEG-05), a contract fixture (NEG-08), a
diagram-coverage fixture (NEG-13), a governance fixture (NEG-14), a safety-removal fixture (NEG-18), a
safety-weakening fixture (NEG-33), a path-status fixture (NEG-25), a fail-closed dependency fixture
(NEG-21), and an unaccepted-anchor fixture (NEG-34). The implementation neutralises one check function at a
time and confirms the corresponding NEG fixture fails, so all fifteen check functions (`_check_model_schema`,
`_check_ordering`, `_check_identity`, `_check_paths`, `_check_boundaries`, `_check_contracts`,
`_check_diagrams`, `_check_governance`, `_check_neutrality`, `_check_safety`, `_check_binding`,
`_check_maturity`, `_check_dependencies`, `_check_determinism`, `_scan_public_safety`) are load-bearing
(`verification-plan.md` DET-04).

## 12. Alternatives considered

| Alternative | Rejected because |
| --- | --- |
| Keep architecture only as prose in `specs/007-xcom-core/plan.md` | Not machine checkable; component/boundary/contract resolution, coverage, ADR/REF-002 consistency, and public safety cannot be proven absent. |
| Store the model only as a Markdown table set | No canonical JSON to serialize deterministically or to validate; a machine-readable model is required for the T008-style exact-candidate evidence. |
| Model every C++ type and unit here | That is T010's unit-design deliverable (ownership, lifetime, thread-safety, failure semantics, bounds, Doxygen); T009 stays at component/boundary/contract granularity. |
| Author the gateway `.proto` here | T030 owns the versioned `.proto`; T009 models the boundary and its contract, not the wire definition. |
| Depend on a rendered diagram image | Non-deterministic binary output cannot be byte-checked; structured diagram definitions render to deterministic Mermaid instead. |
| Treat existing T012–T024 source as `implemented` | Source presence is not acceptance evidence (Constitution art. IX; analysis A12); those components are `partial` with an `unreconciled` reason. |
| Place the model under `specs/007-xcom-core/` | That path is shared with the accepted specification; the per-task `docs/engineering/xcom/t009/` directory is already exclusively owned by `T-ENABLER`. |

## 13. Requirement-to-design trace

| Requirement | Design section |
| --- | --- |
| T009-SR-001 | §3, §3.1, §10 |
| T009-SR-002 | §3, §5 |
| T009-SR-003 | §3, §6 |
| T009-SR-004 | §3, §7, §10.2 |
| T009-SR-005 | §3, §8 |
| T009-SR-006 | §7, §9, §10.3 |
| T009-SR-007 | §9, §10.2 |
| T009-SR-008 | §6, §9 |
| T009-SR-009 | §3, §5, §10.2 |
| T009-SR-010 | §3, §4, §5, §10.2 |
| T009-SR-011 | §2, §4 |
| T009-SR-012 | §4, §10.2 |
| T009-SR-013 | §4, §10, §11 |
