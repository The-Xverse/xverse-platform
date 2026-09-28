# T009 Requirements — Architecture, Boundaries, Component/Sequence Diagrams, and Cross-Language Contracts

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T009 (capability 007, phase 2 repository-owned engineering baseline) |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `209084b11a211273f815980f753ba728e1251a09` |
| Predecessor task | T008 (requirement register + bidirectional traceability; reviewed terminal package `209084b`) |
| Successor tasks | T010 (unit design/ownership/lifetime/thread-safety/bounds/Doxygen plan), T011 (dependency admission), then implementation slices T012–T034, integration/evidence T035–T040, and review/acceptance T039/T041 |
| Requirement ID families | `T009-STK-###` (stakeholder), `T009-SR-###` (software) |
| Authority | the T009 entry in `specs/007-xcom-core/tasks.md`; `specs/007-xcom-core/plan.md` "Architecture", "Project Structure", and "Delivery phases" 1; `specs/007-xcom-core/spec.md` FR-001–FR-005, FR-009–FR-011, FR-022–FR-024, FR-026–FR-032 and SC-002/SC-009/SC-011; `specs/007-xcom-core/data-model.md`; `specs/007-xcom-core/contracts/*.md`; Constitution 2.1.0 articles II, III, V, VI, VII, VIII, IX, X and the capability acceptance gates; ADR-0016, ADR-0018, ADR-0019, ADR-0020; ACC001–ACC015; the T007 ownership register `docs/engineering/xcom/task-ownership.{md,json}`; the T008 register/matrix `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` |
| Classification | Public-safe engineering work product |

### 1.1 Authority statement

This document specifies only the bounded T009 slice. T009 **maintains the capability-007 architecture,
its internal and external boundaries, its component and sequence diagrams, and its cross-language
contracts** as one canonical, machine-checkable model. It elaborates the already-accepted architecture in
`specs/007-xcom-core/plan.md`, `specs/007-xcom-core/data-model.md`, and the accepted contracts under
`specs/007-xcom-core/contracts/`. It does **not** redesign the accepted architecture, invent a new
component, change an accepted functional requirement, success criterion, ADR, or ownership boundary,
weaken an existing requirement or test, or approve any other task.

T009 is a repository-owned work-product task. Its candidate may change documentation/governance artifacts
and add one offline validator script under `scripts/`, but the deterministic gate rejects any T009 change
under `src/`, `tests/`, or `xdl/` (T009-SR-011). The architecture model T009 produces is the
architecture/boundary/contract authority that T010 (unit design), the implementation slices, T030–T034
(external-tool gateway), T035–T038 (integration/evidence, dependency admission), and T039/T041
(review/acceptance) consume.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, the accepted plan and
contracts, the constitution, an accepted ADR, the T007 ownership register, or the T008 register/matrix is
resolved in favour of the accepted source. A material gap is reported rather than guessed. Unresolved gaps
are recorded in §9.

## 2. Scope

### 2.1 In scope (bounded T009)

Keep T009 strictly inside the T009 task entry, which places it in the engineering-baseline enabler group.

1. **Maintain the capability-007 architecture** as a canonical, schema-versioned model with an explicit
   closed layer/language vocabulary and one uniquely identified, uniquely owned record per architectural
   component, each anchored to the accepted plan/contracts and to its real or planned product paths.
2. **Maintain every boundary** between components — in-process C++ interfaces, the Python→C++ build-time
   boundary, the local out-of-process tool boundary, the observation/downstream boundary, and the
   provider realization boundary — with direction, boundary kind, governing contract, authorization
   requirement, safety constraints, and failure semantics.
3. **Maintain the cross-language and external contracts** that cross those boundaries: versioned,
   producer/consumer-identified, artifact-anchored, with encoding, unknown-field policy, and an explicit
   additive evolution rule.
4. **Maintain the component and sequence diagrams** for the four accepted user stories and the structural
   component view, expressed as deterministic diagram definitions that resolve only to declared
   components, boundaries, and contracts, and that cover every component, boundary, contract, and user
   story.
5. **Preserve the accepted architecture, ADRs, dependency direction, domain neutrality, safety
   boundaries, REF-002 dispositions, ownership, and dependency order.** The model records governing ADR
   references and the required one-way dependency direction; a domain primitive in the core, a reverse
   dependency, or a promoted SADS target is a validation failure.
6. **Provide a deterministic, public-safe, offline validator** with a controlled self-test over the
   declared negative cases, and re-run it plus the T007 ownership validator before the candidate is
   presented.
7. **Maintain consistency with the T007 ownership register** by declaring T009's new artifacts to the
   owning `T-ENABLER` slice and re-validating, without weakening the accepted register.

### 2.2 Explicit exclusions (must remain absent from the T009 candidate)

No production or test source is created or modified; no `src/`, `tests/`, or `xdl/` path is changed; no
`proto/` definition is authored (T030 owns the gateway `.proto`); no compilation, linking, runtime
execution, benchmark, or dependency retrieval occurs; no legacy repository is read or written; no external
network peer, package manager, or TCP listener is used; no accepted ADR, accepted requirement, accepted
contract, or existing test is rewritten or weakened; no architecture component, boundary, or contract that
the accepted plan does not sanction is invented; no other task is marked complete; no software candidate
is accepted or integrated; no SESN artifact is created, rewritten, or extended; no target REF-002 SADS
requirement is promoted to implemented.

### 2.3 Delegated to later tasks (not implemented or decided here)

| Area | Owner | Disposition in T009 |
| --- | --- | --- |
| Unit design, ownership, lifetime, thread-safety, failure semantics, bounds, Doxygen plan | T010 | allocated; T009 declares the component/boundary/contract units only and defers C++ type/unit internals to T010 |
| Compiler/build/`nlohmann/json`/gRPC/Protocol Buffers/static-analysis/sanitizer/Doxygen admission | T011 | allocated; T009 names the contract boundaries and their artifacts but does not pin versions, hashes, or licenses |
| `io.xverse.xcom` Profile, activation-plan schema, and Python plan compiler | T017–T018 | allocated; T009 models the boundary and contract, and does not author the profile or schema |
| C++ activation-plan decoding and capabilities | T019–T020 | allocated; T009 records the consumer side of the cross-language contract only |
| Core, observation, stimulation, and gateway implementation | T012–T034 | allocated; T009 records `partial`/`unreconciled` where baseline source exists and `allocated`/`planned` otherwise |
| Full verification, benchmarks, Doxygen, traceability validation, evidence bundle | T035–T040 | allocated; T009 supplies the architecture model they validate and extend |
| Independent read-only review and explicit user acceptance | T039, T041 | allocated; T009 does not accept, complete, or integrate any candidate |

### 2.4 Affected paths, negative cases, and bounds

**Affected source paths.** T009 changes documentation/governance and adds one offline validator. The plan
stage adds exactly the five work products
`docs/engineering/xcom/t009/{requirements,architecture,detailed-design,unit-specifications,verification-plan}.md`.
The implementation stage adds `docs/engineering/xcom/t009/architecture-model.{json,md}`,
`scripts/validate_xcom_architecture_contracts.py`, and `docs/engineering/xcom/t009/implementation.md`, and
updates the T009 checkbox in `specs/007-xcom-core/tasks.md` and T009's new script path in
`docs/engineering/xcom/task-ownership.{json,md}`. The **affected product source paths are none**: no
`src/`, `tests/`, `xdl/`, or `proto/` path is created or changed (T009-SR-011). The product paths T009
*anchors* are enumerated in `architecture.md` §5 and realised as `artifact_paths` in the model.

**Negative cases.** T009-SR-001..013 each name the negative case(s) that must fail. The declared set is
`NEG-01`..`NEG-39` in `verification-plan.md` §4: malformed/reordered top-level schema (NEG-01),
duplicated component id (NEG-02), unknown layer/language token (NEG-03), component missing a mandatory
field (NEG-04), boundary referencing an undeclared component (NEG-05), unknown boundary kind (NEG-06),
missing required boundary (NEG-07), dangling boundary→contract reference (NEG-08), contract
producer/consumer language mismatch on a cross-language boundary (NEG-09), contract missing version or
evolution rule (NEG-10), diagram participant referencing an undeclared component (NEG-11), diagram step
referencing an undeclared contract (NEG-12), an uncovered user story/boundary/contract (NEG-13), unknown
governing ADR (NEG-14), promoted REF-002 target (NEG-15), dependency-direction violation (NEG-16), domain
primitive in the core (NEG-17), weakened/absent safety invariant (NEG-18), malformed baseline (NEG-19),
unknown authorization reference (NEG-20), unavailable reconciliation dependency (NEG-21), tampered Markdown
projection (NEG-22), prohibited public content (NEG-23), component with no artifact path (NEG-24), an
`established` path absent from the tree (NEG-25), a `planned` path already present in the tree (NEG-26),
duplicated boundary id (NEG-27), duplicated contract id (NEG-28), out-of-order component array (NEG-29),
unreconciled source treated as `implemented` without an accepted revision (NEG-30), a
`requirement_links` id absent from the T008 requirement register (NEG-31), a non-string family id that must
be classified rather than raising (NEG-32), a required safety invariant weakened while still present
(NEG-33), and an `FR-###`/`SC-###`/`US#` anchor that matches the pattern but is outside the accepted spec
anchor set (NEG-34). NEG-35..NEG-39 extend the non-string-id case to an unhashable container id (a list or
dict) on components, boundaries, contracts, and invariants, which must be classified as `SCHEMA_INVALID` (2)
rather than raising. Each fixture isolates one check or one declared ordering/uniqueness rule.

**Concurrency and resource bounds.** T009 has no runtime concurrency: the architecture model is a static
document and the validator is offline and single-threaded. No concurrency case is defined. Applicable
resource bounds are input ≤ 1 MiB per file and ≤ 4 MiB total, no network/subprocess, wall clock ≤ 60 s, and
byte-stable deterministic output. Runtime concurrency/resource bounds for the production data plane are
owned by the implementation slices' own verification plans and by T010. See `verification-plan.md` §6.

## 3. Terminology and measurement

| Term | Meaning in T009 |
| --- | --- |
| Component | One architectural node (build-time tool, derived artifact, data-plane unit, boundary, edge, test fixture, external peer, or downstream consumer) with an explicit layer, language, responsibilities, product paths, ownership, and maturity. |
| Layer | Closed architectural stratum: `xdl-input`, `build-time`, `derived-artifact`, `data-plane`, `boundary`, `edge`, `test-fixture`, `external`, `downstream`. |
| Boundary | One directed interface or seam between two components, with a kind, a governing contract, an authorization requirement, safety constraints, and failure semantics. |
| Cross-language contract | A boundary contract whose producer and consumer are implemented in different languages and/or processes (Python↔C++, C++↔external process). |
| Contract | A versioned interface declaration (schema, in-process C/C++ interface, or external RPC) with producer/consumer components, canonical artifact, encoding, unknown-field policy, and evolution rule. |
| Diagram | A deterministic structured definition of a component view or a user-story sequence, resolving only to declared components, boundaries, and contracts. |
| Invariant | A named architectural, data-model, dependency, or safety property the model must assert and that validation enforces. |
| Maturity | Closed vocabulary `implemented`/`partial`/`allocated`/`deferred`/`superseded`/`conflicting`/`needs_clarification`. |
| First proof | The bounded capability-007 prototype scope: owned loopback providers, synthetic sink/tools, no legacy asset, no external peer, no TCP listener beyond the local-only tool gateway. |
| Deterministic serialization | A byte-stable canonical ordering that yields identical output across runs and hosts. |

Measurements are discrete and observable: component/boundary/contract/diagram/invariant counts per layer
and kind, boundary and contract reference-resolution results, diagram coverage results, reference
identity/uniqueness counts, validator exit status, and byte-level model/projection contents. No
availability, throughput, timing, or probability figure is asserted; none is derivable from the accepted
capability and none is invented.

## 4. Admitted inputs

| Input | Reference | Use |
| --- | --- | --- |
| Capability specification | `specs/007-xcom-core/spec.md` FR-001–FR-035, SC-001–SC-011, user stories, edge cases, key entities | the architectural responsibilities, boundaries, and safety properties the model elaborates |
| Task entry | `specs/007-xcom-core/tasks.md` T009 and the dependency-order section | authorized bounded scope and successor ordering |
| Accepted plan | `specs/007-xcom-core/plan.md` "Summary", "Architecture", "Project Structure", "Delivery phases", "Complexity Tracking" | the accepted component decomposition, mixed-language boundary, and dependency order |
| Data model | `specs/007-xcom-core/data-model.md` entities, state models, invariants 1–10 | component responsibilities and the data-model invariants the model asserts |
| Contracts | `specs/007-xcom-core/contracts/{communication-plan,xdl-profile,provider,observation,tool-gateway,validation-tool}.md` | the accepted cross-boundary contracts and their required behavior |
| Research | `specs/007-xcom-core/research.md` | rejected alternatives and standards-interoperability boundaries |
| Analysis | `specs/007-xcom-core/analysis.md` A09/A12 and the consistency checks | open reconciliation state and the accepted consistency statements |
| REF-002 traceability | `specs/007-xcom-core/reference-traceability.md`, `docs/architecture/sads-requirements-traceability.json` | the accepted dispositions T009 records without promotion |
| Constitution | `.specify/memory/constitution.md` 2.1.0, articles II, III, V, VI, VII, VIII, IX, X and the capability acceptance gates | domain neutrality, XDL centrality, dependency direction, maturity, traceability, and evidence obligations |
| ADRs | ADR-0016 (subsystem naming/ownership), ADR-0018 (platform-first), ADR-0019 (X-COM observation/stimulation ownership), ADR-0020 (repository-owned workflow and evidence) | governing decisions the model cites |
| Acceptance records | `specs/007-xcom-core/checklists/acceptance.md` ACC001–ACC015 | exact authorization references |
| Ownership register | `docs/engineering/xcom/task-ownership.{md,json}`, `scripts/validate_xcom_task_ownership.py` | slice/path ownership, baseline/authorization binding, reconciliation vocabulary |
| Requirement register/matrix | `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` | stable requirement links (`XCOM-SYS-*`, `XCOM-SW-*`) the architecture units refine |
| Baseline provenance | `git log` for `src/xverse/xcom/**`, `tests/xcom/**`, `src/xverse_xdl/**`, `scripts/validate_xcom_*.py` | existing-artifact anchoring only; never acceptance proof |

## 5. Stakeholder requirements

### T009-STK-001 — One authoritative architecture, boundary, and contract model

**Statement.** Capability 007 must have a single authoritative model of its architectural components,
their boundaries, and their contracts in which every component, boundary, contract, diagram, and invariant
is uniquely identified, elaborated from — never substituted for — the accepted plan, data model, and
contracts, and anchored to real or explicitly planned product paths.

**Acceptance criteria (observable).**

- AC-1: The model declares exactly one record per component, boundary, contract, diagram, and invariant,
  each with a unique id in a declared family.
- AC-2: Every record has non-empty mandatory fields and at least one acceptance-relevant property.
- AC-3: Every component anchors to the accepted plan/contracts and to at least one repository-relative
  product path marked `established` or `planned`.
- AC-4: No accepted component, boundary, or contract is dropped, merged, or renamed by T009.

**Source anchors.** `tasks.md` T009; `plan.md` "Architecture"/"Project Structure"; `data-model.md`;
Constitution art. X; ACC012/ACC014.

### T009-STK-002 — Accepted architecture, ADRs, and dependency direction preserved

**Statement.** T009 must preserve the accepted architecture, the accepted ADRs, the one-way dependency
direction blueprints → domain profiles → XDL/platform APIs → runtime abstractions, and domain neutrality
of the core, changing no accepted decision and introducing no reverse dependency or domain primitive.

**Acceptance criteria (observable).**

- AC-1: Every core/boundary contract record cites a governing ADR from the accepted set.
- AC-2: The model asserts the declared dependency-direction rule; a reverse dependency is rejected.
- AC-3: No core-layer component references a domain-specific primitive (for example ECU, CAN, SOME/IP,
  Zenoh, or a product name as a core primitive).
- AC-4: No accepted ADR, accepted contract, or accepted requirement is rewritten or weakened.

**Source anchors.** ADR-0016/ADR-0018/ADR-0019/ADR-0020; Constitution arts. II, III, IV, VII, VIII;
`plan.md` "Constitution Check"; ACC011/ACC014.

### T009-STK-003 — Exact baseline and authorization binding

**Statement.** The architecture model and every claimed component, boundary, contract, and diagram must be
bound to the exact baseline revision and to the exact accepted authorization that permits the work, so no
architectural claim rests on an unspecified revision or an inferred authorization.

**Acceptance criteria (observable).**

- AC-1: The model records `baseline_revision = 209084b11a211273f815980f753ba728e1251a09` and a
  candidate-revision rule.
- AC-2: Every component boundary/cross-language claim resolves to a declared contract with an explicit
  version.
- AC-3: The model cites only authorization records from the accepted set (ACC001–ACC015, ADR-0016,
  ADR-0018, ADR-0019, ADR-0020).
- AC-4: A malformed baseline or unknown authorization reference is rejected by the validator.

**Source anchors.** ADR-0020 §Decision; ACC012/ACC014/ACC015; Constitution art. X; T007-STK-002.

### T009-STK-004 — Explicit cross-language and external contracts

**Statement.** Every boundary that crosses a language, process, trust, or realization seam must be
declared with a versioned contract that identifies its producer and consumer, its canonical artifact, its
encoding, its unknown-field policy, and its evolution rule, so no cross-language or external interface is
implicit.

**Acceptance criteria (observable).**

- AC-1: Every `cross-language`/`external-rpc` boundary resolves to exactly one declared contract whose
  producer/consumer languages or processes match the boundary endpoints.
- AC-2: Every contract declares a version, an encoding, an unknown-field policy, and a non-empty
  evolution rule.
- AC-3: The Python→C++ activation-plan boundary, the local tool-gateway boundary, the observation-record
  boundary, and the provider boundary are all declared.
- AC-4: A cross-language boundary without a contract, or with a mismatched language, fails validation.

**Source anchors.** `plan.md` "Complexity Tracking"; `contracts/{communication-plan,tool-gateway,observation,provider}.md`; spec FR-022/FR-031/FR-032; ACC002/ACC013.

### T009-STK-005 — Complete component and sequence diagrams

**Statement.** The model must carry a structural component diagram plus a sequence diagram for each
accepted user story, in which every participant, boundary, and contract resolves to a declared record and
which together cover every declared component, boundary, contract, and user story.

**Acceptance criteria (observable).**

- AC-1: The model contains exactly one `component` diagram and one `sequence` diagram for each of US1–US4.
- AC-2: Every diagram participant and step resolves to a declared component and contract.
- AC-3: Every declared component, boundary, and contract appears in ≥ 1 diagram.
- AC-4: An unresolved participant/step or an uncovered component/boundary/contract/user story fails
  validation.

**Source anchors.** `tasks.md` T009; `spec.md` US1–US4; `plan.md` "Architecture"; ACC002/ACC007.

### T009-STK-006 — Safety boundaries and local-only first proof preserved

**Statement.** The model must preserve the accepted safety boundaries: no legacy adapter or execution, no
external network peer, no TCP listener other than the host-protected local tool gateway, stimulation
disabled by default and gated by an exact validation permit, metadata-only observation by default, and the
gateway transport never substituting for the permit.

**Acceptance criteria (observable).**

- AC-1: The model asserts every accepted safety invariant with a stable id.
- AC-2: The tool-gateway contract and boundary record the local-IPC-only and permit-required rules.
- AC-3: The observation contract records metadata-only as the default and payload exposure as
  policy-gated.
- AC-4: A safety invariant that is absent or weakened (for example a permitted TCP listener, an optional
  permit, or a payload-default observation) fails validation.

**Source anchors.** `specs/007-xcom-core/spec.md` FR-012/FR-014/FR-016/FR-026/FR-027/FR-028/FR-032;
`contracts/{tool-gateway,observation,validation-tool}.md`; ADR-0019; ACC011/ACC014.

### T009-STK-007 — Public-safe, deterministic, reproducible model and validator

**Statement.** The architecture model, its Markdown projection, and their validation must be deterministic
and public-safe: byte-stable across runs, free of credentials, private addresses, proprietary source
excerpts, sensitive deployment values, and absolute host paths, and reproducible offline with no network
access.

**Acceptance criteria (observable).**

- AC-1: Serializing the same model twice yields byte-identical output; the Markdown projection matches.
- AC-2: The validator performs no network access and reads only repository-relative files.
- AC-3: A public-safety scan finds no credential, private address, private-key marker, or absolute host
  path in the model, projection, or validator output.
- AC-4: Validation is bounded in file size and runtime.

**Source anchors.** `spec.md` FR-027; Constitution art. X; ADR-0020 §Decision; T007-STK-006.

### T009-STK-008 — Independent review and explicit acceptance remain separate

**Statement.** T009 must preserve the separate read-only review and explicit user acceptance gates and
must not accept, complete, or integrate any candidate, including its own.

**Acceptance criteria (observable).**

- AC-1: T009 leaves the T009 and all other task checkboxes unchanged in the plan stage and marks only its
  own checkbox in the implementation stage.
- AC-2: T009 records no acceptance or integration claim for any candidate.
- AC-3: The review of T009's architecture work is a separate pass recorded in `internal-review.json`;
  external Codex review remains deferred until the `xcom-t007-t010-t017-t020` backlog completes.

**Source anchors.** ADR-0020 §Decision; ACC012/ACC015; `tasks.md` T039/T041.

## 6. Software requirements

Each software requirement refines one or more stakeholder requirements. Identifier names below are fixed
by `detailed-design.md`; the requirements state their observable contract.

### 6.1 Architecture model and structure

#### T009-SR-001 — Canonical architecture model with deterministic serialization (refines T009-STK-007)

**Statement.** The architecture model must exist as one canonical, schema-versioned JSON model with a fixed
top-level and per-record field set, stable ordering (the `components`, `boundaries`, `contracts`,
`diagrams`, and `invariants` arrays sorted by `id`, ids unique), a recorded `schema_version`, a byte-stable
JSON serialization, and a deterministic Markdown projection.

**Acceptance criteria.** Declared top-level and per-record schemas are implemented; every family entry's
`id` is a non-empty string; two serializations are byte-identical; `schema_version` is present and stable;
the Markdown projection equals the model; each of the five declared top-level arrays is sorted by `id` and
carries unique ids; nested arrays preserve their authored order and carry no sort requirement.

**Verification intent.** Structural check CHK-01; determinism check CHK-12; negative cases NEG-01
(missing/reordered top-level field), NEG-27 (duplicated boundary id), NEG-28 (duplicated contract id),
NEG-29 (out-of-order component array), NEG-32 (a non-string family id), and NEG-35..NEG-39 (an unhashable
container family id on components, boundaries, contracts, and invariants), each of which must be classified
as a schema failure rather than raising an uncaught error.

#### T009-SR-002 — Component identity, layer/language vocabulary, and product-path anchoring (refines T009-STK-001)

**Statement.** Every component must carry a unique id in a declared family, a `layer` from the closed
layer vocabulary, a `language` from the closed language vocabulary, a non-empty responsibility, a
`first_proof`/`later` scope, an owning slice and task set from the accepted ownership register, a maturity
from the closed vocabulary, and at least one repository-relative `artifact_path` tagged `established` or
`planned`, plus a non-empty `requirement_links` list whose every entry resolves either to a T008 register
requirement id or to an accepted `FR-###`/`SC-###`/`US#` anchor from `specs/007-xcom-core/spec.md`; the
model must reject a duplicate id, an unknown layer/language/maturity token, a missing mandatory field, a
component with no artifact path, or a requirement link that resolves to neither.

**Acceptance criteria.** All component ids unique; all layers/languages/maturities from their closed sets;
all mandatory fields non-empty; every component has ≥ 1 artifact path; every `requirement_links` entry
resolves in the T008 register or the accepted anchor set; a duplicate id, unknown token, missing field,
empty path set, or unresolvable requirement link fails validation.

**Verification intent.** Identity check CHK-02; path-mapping check CHK-06; negative cases NEG-02
(duplicate id), NEG-03 (unknown token), NEG-04 (missing field), NEG-24 (no artifact path), NEG-31
(dangling requirement link), and NEG-34 (an `FR-###` anchor outside the accepted spec anchor set).

#### T009-SR-003 — Boundary model completeness and reference resolution (refines T009-STK-001, T009-STK-005)

**Statement.** Every boundary must declare a unique id, a name, a `kind` from the closed boundary-kind
vocabulary, a `from_component` and `to_component` that resolve to declared components, a direction, a
governing `contract` that resolves to a declared contract, an authorization requirement, at least one
safety constraint, non-empty failure semantics, and a maturity; the requirement set
(`XCOM-XB-001`..`XCOM-XB-011` per `detailed-design.md` §6) must all be present, and the model must reject
an undeclared component reference, an unknown kind, a missing required boundary, or a duplicated boundary
id.

**Acceptance criteria.** Only declared boundary kinds used; every boundary endpoint and contract resolves;
the required boundary set is exactly present; a dangling, unknown, missing, or duplicated boundary fails
validation.

**Verification intent.** Boundary check CHK-03; negative cases NEG-05 (undeclared component), NEG-06
(unknown kind), NEG-07 (missing required boundary), and NEG-27 (duplicated boundary id).

### 6.2 Cross-language and external contracts

#### T009-SR-004 — Cross-language and external contract catalogue and resolution (refines T009-STK-004)

**Statement.** The model must declare the contract catalogue (`XCOM-XLC-001`..`XCOM-XLC-006` per
`detailed-design.md` §7) with, for each contract, a unique id, a `kind`, producer and consumer component
lists that resolve to declared components, producer/consumer languages from the closed vocabulary, a
version, a canonical artifact path, an encoding, an unknown-field policy, a non-empty additive evolution
rule, at least one governing ADR, and a maturity; every `cross-language`/`external-rpc`/`artifact`
boundary must resolve to a contract whose producer/consumer languages or processes match the boundary
endpoints, and the model must reject a dangling boundary→contract reference, a language mismatch, a
contract missing its version or evolution rule, or a duplicated contract id.

**Acceptance criteria.** Every cross-boundary resolves to a matching contract; every contract carries
version, encoding, unknown-field policy, and evolution rule; a dangling reference, language mismatch,
missing version/evolution rule, or duplicate contract id fails validation.

**Verification intent.** Contract check CHK-04; negative cases NEG-08 (dangling contract reference),
NEG-09 (language mismatch), NEG-10 (missing version/evolution rule), and NEG-28 (duplicated contract id).

#### T009-SR-005 — Diagram coverage and resolution (refines T009-STK-005)

**Statement.** The model must declare exactly one `component` diagram and one `sequence` diagram for each
of US1–US4, where every diagram participant resolves to a declared component, every sequence step resolves
to declared components and a declared contract, and every declared component, boundary, contract, and user
story appears in ≥ 1 diagram; the model must reject an unresolved participant or step, or an uncovered
component/boundary/contract/user story.

**Acceptance criteria.** Diagram set is exactly the component view plus US1–US4 sequences; participants and
steps resolve; coverage holds in both directions; an unresolved participant/step or an uncovered element
fails validation.

**Verification intent.** Diagram check CHK-05; negative cases NEG-11 (undeclared participant), NEG-12
(undeclared step contract), and NEG-13 (missing coverage).

### 6.3 Governance, neutrality, and safety

#### T009-SR-006 — Governing ADR and REF-002 non-promotion consistency (refines T009-STK-002)

**Statement.** Every component, contract, and boundary must cite a governing ADR from the accepted set;
the model must record `ref002_disposition = "unchanged"` with an empty promoted set, must not mark a
component or contract `implemented` for a deferred/allocated SADS target, and must reject an unknown
governing ADR or a promoted REF-002 target.

**Acceptance criteria.** All governing ADR references resolve to the accepted set; the REF-002 promoted
set is empty; no deferred/allocated target is reported as implemented; an unknown ADR or a promoted target
fails validation.

**Verification intent.** Governance check CHK-07; negative cases NEG-14 (unknown ADR) and NEG-15 (promoted
target).

#### T009-SR-007 — Domain neutrality and dependency-direction rule (refines T009-STK-002)

**Statement.** The model must assert the one-way dependency-direction rule (blueprints → domain profiles →
XDL/platform APIs → runtime abstractions) and the core domain-neutrality rule, must record the layer of
every component, must confine Python to the `xdl-input`/`build-time` layers and the data plane to C++, and
must reject a reverse dependency or a domain-specific primitive in a core-layer component.

**Acceptance criteria.** Dependency-direction invariant present and enforced; core components contain no
domain primitive; Python confined to build-time and data plane to C++; a reverse dependency or core-layer
domain primitive fails validation.

**Verification intent.** Neutrality/direction check CHK-08; negative cases NEG-16 (reverse dependency) and
NEG-17 (core domain primitive).

#### T009-SR-008 — Safety boundary invariants (refines T009-STK-006)

**Statement.** The model must assert the accepted safety invariants with stable ids: no legacy adapter or
execution; no external network peer; no TCP listener other than the host-protected local tool gateway;
stimulation disabled by default and gated by an exact validation permit; local transport access never
substitutes for the permit; metadata-only observation is the default; disabled/absent observation does not
change normal delivery; and the model must reject a missing or weakened safety invariant.

**Acceptance criteria.** All declared safety invariants present with stable ids and non-empty statements;
each is referenced by at least one component or boundary; each required safety-boundary invariant
(`XCOM-INV-03/06/08/11/12/13/15`) carries its accepted `kind` and statement text; a removed or weakened
invariant (permitted TCP listener, optional permit, payload-default observation) fails validation.

**Verification intent.** Safety check CHK-09; negative cases NEG-18 (removed safety invariant) and NEG-33
(required invariant present but weakened).

#### T009-SR-009 — Maturity and reconciliation honesty (refines T009-STK-001, T009-STK-003)

**Statement.** Every component, boundary, and contract must use the closed maturity vocabulary;
`implemented` must require an accepted exact-revision binding; components whose baseline source is present
but unreconciled (`XCOM-SW-CORE`, `XCOM-SW-OBS` coverage, including T012–T016 and T021–T024) must be
`partial` with an `unreconciled` reason; and the model must be consistent with the T007 reconciliation
state, failing closed when the T007 ownership dependency is unavailable.

**Acceptance criteria.** Closed vocabulary only; `implemented` fully evidenced and revision-bound;
unreconciled coverage `partial` with reason; a violation fails validation; an unavailable
`docs/engineering/xcom/task-ownership.json` or `docs/engineering/xcom/t008/requirements-register.json`
yields a distinct nonzero failure and never a passing result.

**Verification intent.** Maturity check CHK-11; negative cases NEG-21 (dependency unavailable) and NEG-30
(unreconciled source treated as implemented without an accepted revision).

### 6.4 Binding, boundary, and public safety

#### T009-SR-010 — Exact baseline and authorization binding (refines T009-STK-003)

**Statement.** The model must record the exact 40-hex baseline and a candidate-revision rule, cite only
accepted authorization records, tag every artifact path `established` or `planned`, and reject a non-40-hex
baseline, an unknown authorization reference, an `established` path that is absent from the tree, or a
`planned` path that already exists.

**Acceptance criteria.** The model binds the run baseline; authorization references are a non-empty subset
of the accepted set; established/planned path status is consistent with the tree; a malformed baseline,
unknown authorization, absent `established` path, or present `planned` path fails validation.

**Verification intent.** Binding check CHK-10; path-consistency check CHK-06; negative cases NEG-19
(malformed baseline), NEG-20 (unknown authorization), NEG-25 (absent established path), and NEG-26
(present planned path).

#### T009-SR-011 — Docs-only boundary for the T009 candidate (refines T009-STK-002)

**Statement.** The T009 candidate must change only work-product/governance documentation and add one
validator script under `scripts/`; it must not change, create, or delete any path under `src/`, `tests/`,
`xdl/`, or `proto/`, and must not modify an accepted ADR, accepted contract, or weaken an existing
requirement or test.

**Acceptance criteria.** `git diff --name-only <baseline>` contains no `src/`, `tests/`, `xdl/`, or
`proto/` path; no accepted ADR or contract text is edited; `git diff --check` is clean; the T007 ownership
validator still passes.

**Verification intent.** Boundary check CHK-14; deterministic gate in `verification-plan.md` §2.

#### T009-SR-012 — Public-safe architecture model, projection, and validator output (refines T009-STK-007)

**Statement.** The architecture model, its projection, and the validator output and retained evidence must
contain no credentials, secrets, private addresses, proprietary source excerpts, unrestricted payloads,
private-key markers, or absolute host paths. The documented external deterministic-gate invocation path in
`verification-plan.md` §2 is workflow infrastructure, not model content, and is out of scope of this content
rule.

**Acceptance criteria.** A public-safety scan of the model, projection, and validator output finds none of
the prohibited classes; the scan is reproducible.

**Verification intent.** Public-safety check CHK-13; negative case NEG-23.

#### T009-SR-013 — Deterministic validator with self-test and ownership consistency (refines T009-STK-007, T009-STK-003)

**Statement.** A repository-owned validator must check the architecture model against T009-SR-001..012,
provide a self-test over controlled positive and negative fixtures, be deterministic, offline, and bounded,
expose a distinct nonzero exit per failure class, and the T009 candidate must record its new artifacts in
the T007 ownership register and re-run that register's validator without weakening it.

**Acceptance criteria.** The validator passes the real model; its self-test exercises every negative case;
it performs no network access or subprocess; file and runtime bounds hold; `--check-human` confirms the
projection; the T007 ownership validator still exits 0 after the consistency update.

**Verification intent.** CHK-15 (self-test), CHK-16 (offline/bounded), DET-01..DET-04, BND-01..BND-06 in
`verification-plan.md`; ownership re-check CHK-14.

## 7. Capability 007 requirement links

| Capability anchor | T009 disposition and link | Remaining work |
| --- | --- | --- |
| FR-001–FR-003 domain neutrality, XDL centrality, logical/physical identity separation | **Implemented for this slice (architecture)**: T009-STK-002, T009-SR-006, T009-SR-007 assert domain neutrality, XDL centrality, and the dependency-direction rule; `XCOM-CMP-001`–`003` and `XCOM-XLC-001`/`005` model the XDL-derived boundary. | T017–T020 implement the Profile/plan; T038 validates the traceability. |
| FR-009–FR-010 explicit provider/endpoint ownership and lifecycle | **Implemented for this slice (architecture)**: `XCOM-CMP-005`/`006`/`007` and `XCOM-XB-004`/`009` with `XCOM-XLC-004`. | T014–T015 implement; T033–T034 prove replaceability. |
| FR-011/FR-014 versioned observation boundary without perturbing delivery | **Implemented for this slice (architecture)**: `XCOM-CMP-008`, `XCOM-XB-005`/`006`, `XCOM-XLC-003`, and safety invariant `XCOM-INV-06`. | T021–T024 implement; T032/T036 verify. |
| FR-015–FR-021 stimulation boundary and evidence | **Implemented for this slice (architecture)**: `XCOM-CMP-009`, `XCOM-XB-007`, `XCOM-XLC-006`, and safety invariants `XCOM-INV-03`/`08`/`09`/`10`. | T025 (accepted) plus T026–T029 implement; T029 verifies. |
| FR-022–FR-023 provider-neutral tool contracts, normalized records for Argus | **Implemented for this slice (architecture)**: `XCOM-CMP-010`–`013`, `XCOM-XB-006`/`008`, `XCOM-XLC-002`/`003`. | T030–T034 implement; Argus consumption is a later capability. |
| FR-026/FR-027/FR-028 no ambient network/legacy, public-safe evidence, loopback-only proof | **Partial (constraint)**: T009-SR-008, T009-SR-010, T009-SR-011, T009-SR-012 declare the safety, binding, boundary, and public-safety rules. | Enforced at runtime by the implementation slices and verified by T035/T038. |
| FR-029/FR-031/FR-032 Doxygen, XDL Profile, local out-of-process tool | **Partial (architecture)**: `XCOM-XLC-001` (Python→C++ plan), `XCOM-XLC-002` (local gateway), and the Doxygen obligation delegated to T010/T037. | T010 owns the Doxygen plan; T017–T020 and T030–T034 implement. |
| SC-002 deterministic ordering-equivalent plans | **Implemented for this slice (architecture)**: `XCOM-XLC-001` declares the canonical digest-bound plan; T009-SR-001 declares deterministic serialization. | T018–T020 verify. |
| SC-009/SC-010 traceability and separate review | **Partial (governance)**: T009-STK-008 keeps review and acceptance separate; the model links to the T008 register. | T038 validates traceability; T039/T041 review and accept. |
| Constitution arts. II, V, VII, VIII, IX, X | **Implemented for this slice**: T009-SR-002, SR-006, SR-007, SR-008, SR-009, SR-010, SR-012. | Bound to exact candidates by later tasks. |

## 8. REF-002 dispositions

T009 is an architecture/traceability task and implements **no** direct REF-002 communication requirement
XVE-SYS-0139–0158. It **records** `ref002_disposition = "unchanged"` and promotes none. Every
capability-007 disposition in `specs/007-xcom-core/reference-traceability.md` and
`docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` remains exactly as accepted.

| REF-002 group | Disposition in T009 | Basis |
| --- | --- | --- |
| `XVE-SYS-0139`–`0158` (communication/interoperability) | **unchanged** — no target is promoted; the model's promoted set is empty | T009 records architecture/boundary/contract structure only; it implements and demonstrates nothing. |
| Shared extensibility (`XVE-SYS-0237`–`0250`), time (`XVE-SYS-0251`–`0264`), failure recovery (`XVE-SYS-0265`–`0279`) | **allocated to their owning capabilities; unchanged** | `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` §X-COM allocation; capability 007 may establish contracts but claims no full system requirement. |

**Conflicting:** none identified within the admitted inputs.
**Needing clarification:** none; the only open item is the reconciliation of already-present source
(§9 A-1), which the model records rather than resolves.

## 9. Assumptions and open items

1. **A-1 (open reconciliation)** — `src/xverse/xcom/**`, `tests/xcom/**`, and the `scripts/validate_xcom_*.py`
   validators contain SESN-era artifacts for T012–T016 and T021–T024, but those task checkboxes are open
   and no accepted exact-candidate revision is recorded (analysis A12). The model records the
   corresponding components as `partial` with an `unreconciled` reason; it does not relabel, delete, or
   extend them.
2. **A-2** — The accepted T025 successor is merged at `4b01586b438a8587d231ee8828d896c206c06a96`
   (implementation `cc9044ab28d0ae9b4df8447072f68b73b3db184a`); the stimulation-session component is
   bound to that accepted revision.
3. **A-3** — Component, boundary, contract, diagram, and invariant identifiers are candidate-chosen names
   fixed by `detailed-design.md`; no accepted text is contradicted and no accepted component or contract is
   renumbered.
4. **A-4** — "Baseline" means the exact Git commit identified by `git rev-parse`; no floating branch, tag,
   or ambient state is a valid binding.
5. **A-5** — The deterministic gate for T009 is a work-product gate that runs no C++/Python test suite;
   the T009 verification is static validation of the architecture model, its projection, and the docs-only
   boundary (`verification-plan.md` §2).
6. **A-6** — The model is derived from the accepted plan, data model, and contracts; where the accepted
   source is silent, the model records an architecture note or a `needs_clarification` disposition rather
   than inventing a component or contract.
7. **A-7** — A component whose only paths are `planned` is `allocated`; a component whose baseline source
   exists but is unreconciled is `partial`; a component bound to the accepted T025 revision is
   `implemented`. No component is `implemented` on the basis of source presence alone.

## 10. Requirement index

| Requirement | Refines | Primary units |
| --- | --- | --- |
| T009-STK-001 | — | U-MODEL, U-COMP, U-BOUND |
| T009-STK-002 | — | U-ADR, U-NEUTRAL |
| T009-STK-003 | — | U-BIND |
| T009-STK-004 | — | U-XLANG |
| T009-STK-005 | — | U-DIAG |
| T009-STK-006 | — | U-SAFE |
| T009-STK-007 | — | U-MODEL, U-SAFE, U-VALIDATE |
| T009-STK-008 | — | U-SAFE |
| T009-SR-001 | STK-007 | U-MODEL |
| T009-SR-002 | STK-001 | U-COMP |
| T009-SR-003 | STK-001, STK-005 | U-BOUND |
| T009-SR-004 | STK-004 | U-XLANG |
| T009-SR-005 | STK-005 | U-DIAG |
| T009-SR-006 | STK-002 | U-ADR |
| T009-SR-007 | STK-002 | U-NEUTRAL |
| T009-SR-008 | STK-006 | U-SAFE |
| T009-SR-009 | STK-001, STK-003 | U-BIND |
| T009-SR-010 | STK-003 | U-BIND, U-COMP |
| T009-SR-011 | STK-002 | U-SAFE |
| T009-SR-012 | STK-007 | U-SAFE |
| T009-SR-013 | STK-007, STK-003 | U-MODEL, U-VALIDATE |
