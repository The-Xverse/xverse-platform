# T018 Requirements — Deterministic Profile-Aware Plan Compilation

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T018 (capability 007, phase 4 XDL-derived activation plan) |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `56506d2c9cb71791cba06a1cc418fcadee72e0fa` |
| Predecessor tasks | T007–T010 (engineering-baseline enablers) and T017 (Profile v0.1 schema, activation-plan v1 schema, digest/provenance contract, validator; reviewed terminal package `56506d2`) |
| Successor tasks | T019 (bounded C++ decoder in `src/xverse/xcom/{include/xverse/xcom/activation_plan.hpp,src/activation_plan.cpp}`), T020 (ordering-equivalence, malformed-plan, drift, bound, regression suites), then T035–T041 |
| Requirement ID families | `T018-STK-###` (stakeholder), `T018-SR-###` (software) |
| Authority | the T018 entry in `specs/007-xcom-core/tasks.md` ("Implement deterministic Profile-aware plan compilation in `src/xverse_xdl/xcom_plan.py`"); `specs/007-xcom-core/plan.md` "Technical Context", "Project Structure", "Delivery phases" 4, "Complexity Tracking"; `specs/007-xcom-core/spec.md` FR-002, FR-031, SC-002 and the failure semantics; `specs/007-xcom-core/contracts/{xdl-profile,communication-plan}.md`; `specs/007-xcom-core/data-model.md` invariants 1, 2, 7; `docs/engineering/xcom/t010/{requirements,design-units}.md` (`XCOM-DU-009`); `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-001`, `XCOM-CMP-002`, `XCOM-CMP-003`, `XCOM-XLC-001`, `XCOM-XLC-005`, `XCOM-XB-001`–`003`); `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` (`XCOM-SW-XDL-002`, `XCOM-DU-XDL-BASELINE`, `XCOM-T-XDL`, `XCOM-L-0138`–`0140`); `docs/engineering/xcom/task-ownership.{md,json}` (T007 `T-XDL` slice); Constitution 2.1.0 articles II, III, VII, VIII, IX, X and the capability acceptance gates; ADR-0016, ADR-0018, ADR-0020; ACC002, ACC003, ACC013, ACC014, ACC015 |
| Classification | Public-safe engineering work product |

### 1.1 Authority statement

This document specifies only the bounded T018 slice: a deterministic, offline, bounded Python compiler that
reads the already normalized and validated XDL graph together with the `io.xverse.xcom` Profile v0.1 payloads
and emits the canonical, digest-bound activation plan v1 defined by T017. It elaborates the accepted
architecture (`XCOM-CMP-001`–`003`, `XCOM-XLC-005`, `XCOM-XB-001`/`XCOM-XB-002`) and the accepted software
requirement `XCOM-SW-XDL-002`.

It does **not** implement the bounded C++ decoder (T019), author the ordering-equivalence, malformed-plan,
drift, bound, or regression suites (T020), redesign the accepted architecture, change an accepted functional
requirement, success criterion, ADR, schema, or contract statement, fix a production numeric bound value,
create a competing configuration language, accept or integrate any candidate, or approve any other task.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, the accepted plan and
contracts, the T017 schemas and digest/provenance contract, the constitution, an accepted ADR, the T007
ownership register, the T008 register/matrix, the T009 architecture model, or the T010 unit design is
resolved in favour of the accepted source. A material gap is reported rather than guessed. Unresolved gaps are
recorded in §9.

## 2. Scope

### 2.1 In scope (bounded T018)

Keep T018 strictly inside the T018 task entry: *"Implement deterministic Profile-aware plan compilation in
`src/xverse_xdl/xcom_plan.py`."*

1. **Implement `src/xverse_xdl/xcom_plan.py`** as a Python 3.11+ module that exposes a pure, deterministic,
   offline, bounded compiler entry point `compile_plan(...)`, plus its input-normalization and
   canonicalization helpers, and that returns the canonical activation-plan v1 value defined by the T017
   schema.
2. **Consume the exact normalized XDL graph and the `io.xverse.xcom` Profile payloads.** The compiler input is
   the JSON-compatible normalized graph document produced by the accepted XDL loader/normalizer
   (`xverse_xdl.canonical_json(validation_result.resources)` is one admitted producer). The compiler must not
   re-read authored YAML/JSON, must not re-implement XDL normalization or reference resolution, and must not
   define a second configuration language.
3. **Derive the plan deterministically** from the graph: contracts and schema/version references from
   `interface-policy` payloads; endpoints and routes from the System interfaces/endpoints/flows; providers and
   capability requirements from `network-provider` payloads and the deployment target capabilities; the
   ordering/reliability/deadline/retry/overflow/backpressure policy set and the observation points, stimulation
   actions, clock domains, activation order, diagnostics, status, and input-resolution state from the
   `flow-policy`, `observation-policy`, and `validation-policy` payloads and the System time domains.
4. **Reproduce the T017 digest/provenance contract exactly**: the canonical serialization rule, the
   `xverse.xcom.activation-plan.v1\x00` domain separator, the digested region (the plan with the top-level
   `digest` member removed), the `{algorithm, value}` digest form, the generator version, and the
   `provenance.generatedAt`/`graphDigest`/`resources` fields.
5. **Implement the fail-closed inspectable-versus-activatable rule**: a plan whose identity, schema,
   capability, time, ownership, or policy input does not resolve is emitted as `inspectable` with the exact
   unresolved member recorded and a deterministic diagnostic; only a fully resolved plan is `activatable`.
   Contradictory or ambiguous graph input is `rejected`; a bound breach or an unknown outcome is `failed`.
6. **Enforce explicit resource bounds** on the graph input (bytes, depth, nodes, resources) and on the
   compiled entity counts (endpoints, routes, providers, observation points, clock domains, diagnostics), with
   `fail-closed` overflow.
7. **Provide compiler unit/contract tests** in `tests/test_xcom_plan.py` that prove the derivation, the
   byte-stable determinism against reordered-but-equivalent input, the digest agreement with the T017
   reference, the fail-closed status rule, the bound behaviour, and the declared negative cases, and that
   perform no network, subprocess, or filesystem write. The tests import the T017 validator's pure functions
   and verify the compiled plan against the T017 schema/ordering/digest checks.
8. **Preserve the accepted architecture, ADRs, dependency direction, domain neutrality, safety boundaries,
   REF-002 dispositions, ownership, and dependency order**, and record the T018 candidate's changed paths,
   baseline, and evidence in its work products.

### 2.2 Explicit exclusions (must remain absent from the T018 candidate)

No C++ source or header is authored or changed (`src/xverse/xcom/include/**`, `src/xverse/xcom/src/**` are
T019); no ordering-equivalence/malformed-plan/drift/bound/regression suite or C++ test target is authored
(T020); no `proto/`, CMake, `Doxyfile`, or build file is changed; no schema or digest/provenance contract is
rewritten or weakened; no authored YAML/JSON is re-parsed and no second configuration language, grammar, or
competing topology is invented; no XDL normalization or reference-resolution logic is duplicated; no legacy
repository is read or written; no external network peer, package manager, or TCP listener is used; no
production workload or legacy binary is executed; no accepted ADR, accepted contract statement, accepted
requirement, other task's work product, or existing test is rewritten or weakened; no production numeric
bound value is fixed; no other task is marked complete; no software candidate is accepted or integrated; no
REF-002 target is promoted to implemented.

### 2.3 Delegated to later tasks (not implemented or decided here)

| Area | Owner | Disposition in T018 |
| --- | --- | --- |
| Bounded C++ plan decode with independent version/digest/capability checks | T019 | allocated; T018 produces the plan and its digest that T019 independently re-checks |
| Ordering-equivalence, malformed-plan, drift, bound, and regression suites | T020 | allocated; T018 supplies compiler unit/contract tests only |
| Configured production bound values | implementation slices | allocated; T018 enforces finite declared offline-input bounds and fixes no production numeric value |
| Compiler/build/dependency admission with hashes and licenses | T011 | allocated; T018 runs in the same provisioned Python environment as T017 (see §9 A-3) |
| Full verification, benchmarks, traceability validation, evidence bundle | T035–T038, T040 | allocated; T018 supplies the compiler and its unit evidence |
| Independent read-only review and explicit user acceptance | T039, T041 | allocated; T018 does not accept, complete, or integrate any candidate |

### 2.4 Affected paths, negative cases, and bounds

**Affected source paths (T018-owned, from the `T-XDL` slice exclusive list).** The plan stage adds exactly
`docs/engineering/xcom/t018/{requirements,architecture,detailed-design,unit-specifications,verification-plan}.md`.
The implementation stage adds `src/xverse_xdl/xcom_plan.py`, `tests/test_xcom_plan.py`, and
`docs/engineering/xcom/t018/implementation.md`, and marks the T018 checkbox in `specs/007-xcom-core/tasks.md`
(shared path). The review and package stages add `docs/engineering/xcom/t018/internal-review.json` and
`reports/xcom-queue/t018-package.json`.

No file under `src/xverse/xcom/include/`, `src/xverse/xcom/src/`, `proto/`, `cmake/`, or `Doxyfile` is changed.
No other file under `src/xverse_xdl/` is changed: the slice's exclusive list names the exact file
`src/xverse_xdl/xcom_plan.py`, so `src/xverse_xdl/__init__.py` is **not** edited; the compiler is imported as
`xverse_xdl.xcom_plan`. No T017 artifact (`xdl/profiles/xcom-v0.1.schema.json`,
`src/xverse/xcom/contracts/v1/activation-plan.schema.json`, `scripts/validate_xcom_plan.py`,
`tests/xcom/activation_plan/**`, `specs/007-xcom-core/contracts/xdl-profile.md`, `docs/engineering/xcom/t017/**`)
is changed. In particular, no fixture is added under `tests/xcom/activation_plan/fixtures/{profile,plan}/valid/`
because the T017 `--check-human` expectation and the T017 `run_checks` fixture set are bound to those
directories; T018 fixtures, where used, are inline in `tests/test_xcom_plan.py`.

**Negative cases.** The declared negative set is `NEG-C01`..`NEG-C27` (graph, payload, derivation, status, and
bound defects) and `NEG-G01`..`NEG-G05` (boundary/governance defects) in `verification-plan.md` §4. Each case
injects one controlled defect and asserts the declared outcome (`rejected`/`failed` code, or an
`inspectable`/`activatable` status) with no partial success.

**Public safety.** The compiler source, tests, and retained evidence must contain no credentials, secrets,
private addresses, proprietary excerpts, unrestricted payloads, or absolute host paths. Any graph input is
repository-owned, public-safe, and synthetic. The documented deterministic-gate invocation path in
`verification-plan.md` §2 is workflow infrastructure (an agent instruction), not artifact content, and is out
of scope of this content rule.

**Concurrency and resource bounds.** T018 has no runtime concurrency: the compiler is
`offline-single-threaded`, `caller-owns-value`, and `process-scoped` (T010 `XCOM-DU-009`). Applicable bounds
are graph input ≤ 5 MiB (aligned with the accepted `LoadLimits.max_bytes_per_file`), depth ≤ 100, node count
≤ 100 000, resource count ≤ 1 000, and compiled entity caps for endpoints, routes, providers, observation
points, clock domains, and diagnostics (finite and declared); overflow policy `fail-closed`. The compiler
performs no network, subprocess, or filesystem write. T018 fixes **no** production numeric bound value; the
plan's runtime bounds come from the activation plan or unit configuration (FR-007).

## 3. Terminology and measurement

| Term | Meaning in T018 |
| --- | --- |
| Normalized graph document | The JSON-compatible mapping `{"resources": [resource, ...]}` produced from `xverse_xdl.NormalizedResource` values (`xverse_xdl.canonical_json`), carrying each resource's `identity`, `revision`, `extensions`, `content`, and `references`. It is an admitted input, not an authored configuration language. |
| Profile payload | An `io.xverse.xcom` Profile v0.1 value attached at a resource or element `extensions` location; the grammar is fixed by the T017 `xdl/profiles/xcom-v0.1.schema.json`. |
| Compiled plan | The canonical activation-plan v1 value returned by `compile_plan`, validating against the T017 `activation-plan.schema.json` and satisfying the T017 digest/provenance contract. |
| Observed-at derivation | A mapping rule that reads only members already present in the normalized graph; it never synthesizes an identity, schema id, provider, address, permit, handle, or session. |
| Fail-closed input | An input that does not resolve is recorded as `unresolved` (making the plan `inspectable`) or, when contradictory/ambiguous, causes `rejected`; it is never defaulted, guessed, or silently dropped. |
| Status | Closed vocabulary `inspectable`, `activatable`. |
| Outcome | Closed vocabulary `accepted`, `rejected`, `failed`, `inspectable`, `activatable`. |
| Maturity | Closed vocabulary `implemented`/`partial`/`allocated`/`deferred`/`superseded`/`conflicting`/`needs_clarification`. |
| First proof | The bounded capability-007 prototype scope: owned loopback/synthetic inputs, no legacy asset, no external peer, no TCP listener. |

Measurements are discrete and observable: compiled plan schema-validity and digest-equality results; byte
equality of the canonical plan under reordered-but-equivalent input; per-family input-resolution states;
diagnostic counts and ordering; bound-rejection results; and byte-level source/fixture contents. No
availability, throughput, timing, or probability figure is asserted.

## 4. Admitted inputs

| Input | Reference | Use |
| --- | --- | --- |
| Capability specification | `specs/007-xcom-core/spec.md` FR-002, FR-031, SC-002, failure semantics, key entities | the XDL-derived, digest-bound plan obligation and the fail-before-activation rule |
| Task entry | `specs/007-xcom-core/tasks.md` T018 and the dependency-order section | authorized bounded scope and successor ordering |
| Accepted plan | `specs/007-xcom-core/plan.md` "Technical Context", "Project Structure", "Delivery phases" 4 | the compiler placement and bounded-decode boundary |
| Profile contract | `specs/007-xcom-core/contracts/xdl-profile.md` (including the T017-appended normative grammar) | the five permitted payload forms, the closed discriminator, and the placement/safety rule |
| Plan contract | `specs/007-xcom-core/contracts/communication-plan.md` | the required plan content, unknown-fields-fail-closed rule, inspectable-vs-activatable rule, and canonical byte-identity requirement |
| Data model | `specs/007-xcom-core/data-model.md` invariants 1, 2, 7 | logical/physical separation, exact-handle ownership, plan-digest binding |
| T017 schemas and digest contract | `xdl/profiles/xcom-v0.1.schema.json`, `src/xverse/xcom/contracts/v1/activation-plan.schema.json`, `docs/engineering/xcom/t017/{detailed-design,unit-specifications,verification-plan}.md` | the fixed input grammar, output grammar, and canonical/digest rules the compiler must reproduce |
| T017 reference validator | `scripts/validate_xcom_plan.py` (`canonical_bytes`, `compute_digest`, `validate_plan_structure`, `check_digest`) | the executable reference the tests compare against |
| Unit design | `docs/engineering/xcom/t010/{requirements,design-units}.md` (`XCOM-DU-009`) | compiler ownership, lifetime, thread-safety, bounds, and failure semantics |
| Architecture model | `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-001`–`003`, `XCOM-XLC-005`, `XCOM-XB-001`/`002`) | component/boundary identities and the one-way dependency rule |
| Requirement register/matrix | `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` | `XCOM-SW-XDL-002` and the `XCOM-DU-XDL-BASELINE`/`XCOM-T-XDL` locators and links `XCOM-L-0138`–`0140` |
| Ownership register | `docs/engineering/xcom/task-ownership.{md,json}`, `scripts/validate_xcom_task_ownership.py` | slice/path ownership, baseline/authorization binding |
| XDL normalized input | `src/xverse_xdl/{models,normalize,validate}.py`, `xdl/schemas/v1alpha1/*.schema.json`, `xdl/examples/v1alpha1/*` | the normalized graph document shape and the admitted producer |
| REF-002 traceability | `specs/007-xcom-core/reference-traceability.md`, `docs/architecture/sads-requirements-traceability.json` | the accepted dispositions T018 records without promotion |
| Constitution | `.specify/memory/constitution.md` 2.1.0, articles II, III, VII, VIII, IX, X and the capability acceptance gates | domain neutrality, XDL centrality, platform-first, direction, maturity, traceability |
| ADRs | ADR-0016, ADR-0018, ADR-0020 | governing decisions the design cites |
| Acceptance records | `specs/007-xcom-core/checklists/acceptance.md` ACC002/ACC003/ACC013/ACC014/ACC015 | exact authorization references |
| Baseline provenance | `git rev-parse 56506d2c9cb71791cba06a1cc418fcadee72e0fa`, `git log` for `src/xverse/xcom/**`, `tests/xcom/**`, `src/xverse_xdl/**`, `xdl/**` | existing-artifact anchoring only; never acceptance proof |

## 5. Stakeholder requirements

### T018-STK-001 — Deterministic, Profile-aware compilation from the exact normalized XDL graph

**Statement.** Capability 007 must compile the already normalized and validated XDL graph together with the
`io.xverse.xcom` Profile v0.1 payloads into the canonical activation-plan v1 value, deriving every plan
member from declared graph data only, and producing byte-identical canonical output for semantically
equivalent normalized inputs at a fixed generation time — without introducing a competing topology or
configuration language.

**Acceptance criteria (observable).**

- AC-1: `src/xverse_xdl/xcom_plan.py` exposes `compile_plan(...)`; a positive normalized graph compiles
  without file reads, network, subprocess, or writes and returns a schema-valid plan v1.
- AC-2: Every plan member is derived from a declared graph member or a declared Profile payload; no identity,
  schema id, provider, capability, address, permit, handle, or session is synthesized.
- AC-3: Compiling the same graph twice, or compiling a reordered-but-equivalent graph (resource order,
  member order, payload order), yields byte-identical canonical plan bytes and the same digest.

**Source anchors.** `contracts/communication-plan.md`; spec FR-002/SC-002; `data-model.md` invariant 7; T010
`XCOM-DU-009`; `XCOM-XLC-005`, `XCOM-XB-002`.

### T018-STK-002 — Faithful, fail-closed plan content coverage

**Statement.** The compiled plan must cover every required-content group of the accepted plan contract and the
T017 schema, must record the exact normalized resource identities and source digests that contributed, and
must fail closed — an unknown or contradictory field, an undeclared discriminator, a duplicate identifier, or
a missing required group is rejected rather than defaulted.

**Acceptance criteria (observable).**

- AC-1: The compiled plan validates against `activation-plan.schema.json` with `additionalProperties: false`
  respected at every object and every required member present.
- AC-2: `planVersion` is `"1"`, `generator.task` is `"T018"`, and `provenance.resources` records the exact
  contributing normalized identities with their source digests.
- AC-3: An unknown payload member, an unknown discriminator, a duplicate identifier, or a missing required
  group yields `rejected` with a stable code and no partial plan.

**Source anchors.** `contracts/communication-plan.md`; `contracts/xdl-profile.md`; spec FR-031/FR-002; T017
`detailed-design.md`; T010 `XCOM-DU-009`; `XCOM-XLC-001`.

### T018-STK-003 — Digest/provenance contract reproduced exactly

**Statement.** The compiler must reproduce the T017 digest/provenance contract exactly: the canonical
serialization rule (member-name order, no insignificant whitespace, single integer form for mathematically
integral numbers, no duplicate members), the `xverse.xcom.activation-plan.v1\x00` domain separator, the
digested region (the plan with the `digest` member removed), the `{algorithm:"sha256", value:"<64 lowercase
hex>"}` form, the explicit-or-sentinel generation time, and the provenance that binds the plan to its exact
input.

**Acceptance criteria (observable).**

- AC-1: `compute_digest` agrees byte-for-byte with the T017 reference `scripts/validate_xcom_plan.py`
  `compute_digest` for every compiled positive plan; the T017 `check_digest` accepts the compiled plan.
- AC-2: `generatedAt` comes from an explicit deterministic input, or the fixed sentinel
  `1970-01-01T00:00:00Z`; the digest is never computed over itself.
- AC-3: Canonical bytes are stable under member reordering and whitespace changes and normalize integral
  numbers, so equivalent inputs share one digest.

**Source anchors.** `contracts/communication-plan.md`; `contracts/xdl-profile.md` "Activation-plan v1 digest
and provenance"; spec SC-002; `data-model.md` invariant 7; T017 `detailed-design.md` §5; T010 `XCOM-DU-009`.

### T018-STK-004 — Fail-closed inspectable-versus-activatable status with bounded resources

**Statement.** The compiler must decide the plan `status` from the six declared input-resolution families
(identity, schema, capability, time, ownership, policy): a fully resolved compilation is `activatable`, a plan
with any unresolved input is `inspectable` with the exact member recorded and a deterministic diagnostic, and
contradictory/ambiguous input is `rejected`; every input is bounded and overflow fails closed.

**Acceptance criteria (observable).**

- AC-1: An unresolved family yields `status = "inspectable"` with that member `"unresolved"`, the other five
  `"resolved"` where applicable, and one deterministic diagnostic; a fully resolved input yields
  `"activatable"` with all six `"resolved"`.
- AC-2: A contract rule violation that cannot be represented (schema `status`/`inputResolution` conditional)
  is never emitted: no `activatable` plan carries an unresolved member.
- AC-3: Over-bound or over-depth input yields `failed` with the declared bound code; contradictions yield
  `rejected`; no rejected/failed operation returns a partial plan.

**Source anchors.** `contracts/communication-plan.md`; spec FR-002/failure semantics; T017 `detailed-design.md`
§4.3/§8; T010 `XCOM-DU-009` failure semantics; `data-model.md` invariant 7.

### T018-STK-005 — Accepted intent, governance, and dependency order preserved

**Statement.** T018 must preserve the accepted architecture, accepted ADRs, REF-002 dispositions, safety
boundaries, failure semantics, one-way dependency direction, domain neutrality, ownership, and dependency
order, must not implement T019/T020, must not weaken an existing requirement, schema, contract, or test, and
must not mark the task complete in the plan stage or claim acceptance/review.

**Acceptance criteria (observable).**

- AC-1: The candidate changes only the T018-owned paths of §2.4; no `src/xverse/xcom/{include,src}/**`,
  `proto/**`, CMake, `Doxyfile`, T017 artifact, or other `src/xverse_xdl/**` file is changed.
- AC-2: The compiler depends only on `xverse_xdl`'s server-side normalizer/models and the Python standard
  library at import time; no X-COM runtime type and no legacy artifact is imported.
- AC-3: `ref002.disposition = "unchanged"` with an empty promoted set; no deferred/allocated target is reported
  as implemented.
- AC-4: The T018 checkbox is left unchecked in the plan stage and marked only in the implementation stage; no
  acceptance, review, or integration claim is recorded; the T007 ownership validator still passes.

**Source anchors.** ADR-0018/ADR-0020; ACC014/ACC015; Constitution arts. II, III, VII, VIII, IX, X; T007
register; `tasks.md` T039/T041.

## 6. Software requirements

Each software requirement refines one or more stakeholder requirements. Identifier names of the design
artifacts are fixed by `detailed-design.md`.

### 6.1 Graph input, payload index, and derivation

#### T018-SR-001 — Bounded normalized-graph input (refines T018-STK-001, T018-STK-004)

**Statement.** The compiler must accept a JSON-compatible normalized graph document `{"resources":[...]}`,
reject a non-object root, a missing/non-array `resources`, a non-object resource entry, a missing identity
member, a duplicate resource identity, a non-finite number, an over-depth/over-node/over-resource input, or an
over-byte input, and return an immutable bounded view without reading any file, network, or subprocess.

**Acceptance criteria.** `load_normalized_graph` accepts a valid document; each defect yields the declared
`rejected`/`failed` code; over-depth/over-node/over-resource/over-byte → `failed`; no partial graph is
returned on error.

**Verification intent.** CHK-01, CHK-07; NEG-C01..NEG-C04, NEG-C21..NEG-C23, NEG-C25.

#### T018-SR-002 — Profile payload index and closed-grammar validation (refines T018-STK-002)

**Statement.** The compiler must index every `io.xverse.xcom` Profile payload by its attachment pointer and
decorated identity, validate it against the closed Profile v0.1 grammar (the single closed `kind`
discriminator, the exact five forms, the closed per-form member sets, and the placement/safety rule that
forbids addresses, credentials, permits, handles, and sessions), and reject an unknown member, an unknown
`kind`, an unsupported `schemaVersion`, a form/`kind` mismatch, a payload whose `target` does not match its
attachment, a payload attached at an illegal location, and a duplicate/conflicting payload for the same
decorated identity and form; a resource-level `interface-policy` on a resource that declares more than one
interface is ambiguous and rejected.

**Acceptance criteria.** All five forms indexed; every defect yields the declared `rejected`/`unresolved`
outcome; the compiler's declared closed member sets agree exactly with
`xdl/profiles/xcom-v0.1.schema.json` (drift guard).

**Verification intent.** CHK-02, CHK-06; NEG-C09..NEG-C13, NEG-C27.

#### T018-SR-003 — Contract, endpoint, route, and provider derivation (refines T018-STK-001, T018-STK-002)

**Statement.** The compiler must derive, from the in-scope System/Component/Deployment/Scenario and their
Profile payloads: one contract per `interface-policy` (contractId = interface id, schemaId/schemaVersion from
the payload); one endpoint per declared interface endpoint with role `initiator`/`responder` from flow
direction (falling back to the endpoint direction; a bidirectional endpoint with no flow role is rejected);
one route per single-destination flow (routeId = flow id, from/to = source/destination endpoint, contractId =
flow interface id), rejecting a multi-destination flow or a route id that collides with an endpoint id; and
one provider per `network-provider` payload (`providerId` = the decorated target/binding id, `capabilities` =
the deployment target's declared capabilities, `requiredCapabilities` = the payload's required capabilities).

**Acceptance criteria.** Positive graph yields the declared contracts/endpoints/routes/providers; a dangling
interface contract leaves `schema` unresolved; an undeclared required capability leaves `capability`
unresolved; each contradiction is rejected; all collections are ordered by their declared key with unique
ids.

**Verification intent.** CHK-03; NEG-C05..NEG-C08, NEG-C16, NEG-C17.

#### T018-SR-004 — Policy, observation, stimulation, clock, and activation-order derivation (refines T018-STK-002)

**Statement.** The compiler must derive the required `policies` object (ordering, reliability, deadlineMs,
retry, queueDepth, overflow, backpressure) from the `flow-policy` payloads with a deterministic backpressure
mapping, the `observationPoints` array from the Scenario observers and `observation-policy` payloads, the
`stimulation` object from the `validation-policy` payloads (disabled by default), the `clockDomains` array
from the System time domains with an explicit `unmapped` fallback, and the `activationOrder` as a
duplicate-free sequence of declared endpoint then route ids; a conflicting `flow-policy` set or an absent
policy leaves `policy` unresolved with a deterministic placeholder policy and a diagnostic; an observer whose
target is not a declared route and a `serviceEmulation: true` payload without a `permitPolicyRef` are
rejected.

**Acceptance criteria.** Positive graph yields the declared policies/observation points/stimulation/clock
domains/activation order; conflict/absence yields `policy: unresolved`; the two contradictions are rejected;
`activationOrder` is never empty and never names an undeclared id.

**Verification intent.** CHK-04; NEG-C14, NEG-C15, NEG-C18, NEG-C20, NEG-C24.

### 6.2 Canonical serialization, digest, provenance, and status

#### T018-SR-005 — Canonical serialization and domain-separated digest (refines T018-STK-003)

**Statement.** `canonical_plan_bytes` must encode the plan as UTF-8 with object members ordered
lexicographically by member name, no insignificant whitespace, every mathematically integral number in its
single integer form, no non-finite numbers, and no duplicate members; `compute_digest` must be SHA-256 over
the `xverse.xcom.activation-plan.v1\x00` domain separator concatenated with the canonical bytes of the plan
with the top-level `digest` member removed; the recorded `digest` must equal the recomputed digest.

**Acceptance criteria.** The compiler's `compute_digest` equals the T017 reference `compute_digest`; a
reordered/whitespace-altered/integral-number body yields the same canonical bytes; the digested region
excludes `digest`; malformed or drifted digest is never emitted.

**Verification intent.** CHK-03; NEG-C23; DET-01, DET-02.

#### T018-SR-006 — Provenance, generator identity, and generation time (refines T018-STK-003)

**Statement.** The compiler must record `generator = {task:"T018", version:<generator version>}`,
`provenance.generatedAt` from an explicit deterministic input or the fixed sentinel `1970-01-01T00:00:00Z`,
`provenance.graphDigest` as the domain-separated SHA-256 (`xverse.xcom.normalized-graph.v1\x00`) of the
canonical normalized graph document, and an ordered `provenance.resources` array of the exact contributing
Component/Deployment/Scenario identities with their `sourceDigest` (`sha256` of the canonical resource
document); a non-plain-semver resource revision omits the optional `version` member rather than inventing one.

**Acceptance criteria.** Generator task/version match the schema patterns; the sentinel is used when no time
is supplied; `provenance.resources` is ordered and unique; a graph with no contributing
Component/Deployment/Scenario is rejected.

**Verification intent.** CHK-03, DET-01; NEG-C01, NEG-C26.

#### T018-SR-007 — Inspectable-versus-activatable status and deterministic diagnostics (refines T018-STK-004)

**Statement.** The compiler must compute the six `inputResolution` states (identity, schema, capability, time,
ownership, policy) from declared data only, set `status = "activatable"` iff all six are `"resolved"` and
`"inspectable"` otherwise, and emit a deterministic diagnostic set ordered by `(code, targetId)` with unique
entries and stable codes, where each diagnostic names the affected entity or the fixed `xcom-plan` target; it
must never emit an `activatable` plan with an unresolved member.

**Acceptance criteria.** A fully resolved graph yields all-resolved/`activatable`; each single unresolved
family yields exactly that member unresolved with `inspectable` and one matching diagnostic; diagnostics are
ordered and unique.

**Verification intent.** CHK-05; NEG-C16..NEG-C20, NEG-C27.

#### T018-SR-008 — Bound enforcement and fail-closed overflow (refines T018-STK-004)

**Statement.** The compiler must apply the declared input bounds (bytes, depth, nodes, resources) to the graph
document and the declared compiled-entity caps (endpoints, routes, providers, observation points, clock
domains, diagnostics) to the derived plan, and must fail closed with a `failed` class code before emitting any
plan when a bound is exceeded or when a compilation step's outcome is unknown.

**Acceptance criteria.** Each over-bound input yields the declared `failed` code and no plan; an in-bound graph
compiles; the caps are finite and declared in `unit-specifications.md`.

**Verification intent.** CHK-07; NEG-C21, NEG-C22.

### 6.3 Tests, governance, and binding

#### T018-SR-009 — Compiler unit and contract tests (refines T018-STK-001, T018-STK-002, T018-STK-003, T018-STK-004)

**Statement.** `tests/test_xcom_plan.py` must exercise the compiler's positive derivation, byte-stable
determinism under reordered-but-equivalent input, digest agreement with the T017 reference, schema-validity
and ordering of the compiled plan, the inspectable/activatable rule, the bound behaviour, the payload/schema
drift guard, and every declared negative case, importing the T017 validator's pure functions and performing no
network, subprocess, or filesystem write.

**Acceptance criteria.** Tests exist for each family; every NEG-C case is asserted; the full repository test
command passes and the T017 suite is not modified or weakened.

**Verification intent.** CHK-01..CHK-08; `pytest` gate.

#### T018-SR-010 — Boundary, binding, and REF-002 non-promotion (refines T018-STK-005)

**Statement.** The T018 candidate must change only the T018-owned work products and `T-XDL` exclusive paths
declared in §2.4, must bind to baseline `56506d2c9cb71791cba06a1cc418fcadee72e0fa`, must cite only accepted
authorizations, must link `XCOM-SW-XDL-002` and the `XCOM-DU-XDL-BASELINE`/`XCOM-T-XDL` locators, must leave
the T018 checkbox unchecked in the plan stage, and must record `ref002.disposition = "unchanged"` with an
empty promoted set; a change outside the authorized paths, an unknown authorization, a dangling link, a
REF-002 promotion, or a public-safety leak fails validation.

**Acceptance criteria.** `git diff --name-only` ⊆ the authorized path set; baseline binds by `git rev-parse`;
links resolve in the T008 matrix; REF-002 promoted set empty; public-safety scan clean.

**Verification intent.** CHK-09; NEG-G01..NEG-G05.

## 7. Capability 007 requirement links

| Capability anchor | T018 disposition and link | Remaining work |
| --- | --- | --- |
| FR-002 derive from the exact normalized XDL graph; no competing configuration language | **Implemented for this slice (compilation)**: `XCOM-SW-XDL-002`; T018-SR-001/003/004 derive every plan member from the normalized graph; T018-SR-002 forbids a second language. | T019/T020 prove decode and byte-identity end to end; T038 validates traceability. |
| FR-031 versioned `io.xverse.xcom` Profile compiled into the digest-bound activation plan | **Implemented for this slice (compilation)**: T018-SR-002/003/004/005 consume the Profile v0.1 payloads and emit the digest-bound plan. | T019 decodes; T020 regresses; T035/T038 verify. |
| SC-002 equivalent normalized inputs produce byte-identical plans and diagnostic ordering | **Implemented for this slice (compilation)**: T018-SR-005/007 and the determinism test prove byte-identical plans and ordered diagnostics. | T020 extends ordering-equivalence coverage; T036 benchmarks. |
| FR-007 explicit bounded queue/ordering/reliability/deadline/retry/overflow/backpressure | **Partial (compilation)**: T018-SR-004 records the declared policy set; runtime enforcement is T-CORE/T019. | T019/T020 prove runtime bounds. |
| FR-027 public-safe evidence/logs | **Partial (constraint)**: T018-SR-010 keeps source/tests/evidence free of secrets and absolute paths. | T035/T038 verify. |
| FR-030 traceability, evidence, separate review | **Partial (governance)**: T018 binds `XCOM-SW-XDL-002` and the T008/T010 locators; review/acceptance remain separate. | T038 validates; T039/T041 review and accept. |
| Constitution arts. II, III, VII, VIII, IX, X | **Implemented for this slice (compilation)**: T018-SR-001/002/010 preserve neutrality, XDL centrality, platform-first, direction, maturity, and traceability. | Bound to exact candidates by later tasks. |

## 8. REF-002 dispositions

T018 compiles plans and implements **no** direct REF-002 communication requirement XVE-SYS-0139–0158 and no
shared requirement. It **records** `ref002_disposition = "unchanged"` and promotes none. Every capability-007
disposition in `specs/007-xcom-core/reference-traceability.md` and
`docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` remains exactly as accepted.

| REF-002 group | Disposition in T018 | Basis |
| --- | --- | --- |
| `XVE-SYS-0139`–`0158` (communication/interoperability) | **unchanged** — no target is promoted; the disposition set is empty | T018 implements an offline build-time compiler and demonstrates no runtime communication. |
| Shared extensibility (`XVE-SYS-0237`–`0250`), time (`XVE-SYS-0251`–`0264`), failure recovery (`XVE-SYS-0265`–`0279`) | **allocated to their owning capabilities; unchanged** | `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` §X-COM allocation; capability 007 may compile contracts but claims no full system requirement. |

**Conflicting:** none identified within the admitted inputs.
**Needing clarification:** none; the only open items are the environment prerequisite (§9 A-3) and the
decoder/suite artifacts pending T019/T020 (§9 A-1), which T018 records rather than resolves.

## 9. Assumptions and open items

1. **A-1 (owned successor artifacts pending)** — `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp`
   and `src/xverse/xcom/src/activation_plan.cpp` (T019) and the ordering/malformed/drift/bound/regression
   suites (T020) are not present in the baseline. T018 produces the plan and its digest; it does not create,
   read, or reconcile them.
2. **A-2 (accepted T-CORE source present but unreconciled)** — `src/xverse/xcom/**` contains SESN-era C++
   artifacts whose task checkboxes are open (analysis A12). T018 does not read, extend, or reconcile them and
   imports no X-COM runtime type.
3. **A-3 (test-environment prerequisite)** — the repository declares Python dependencies
   (`jsonschema[format]>=4.26,<5`, `referencing`, `ruamel.yaml`) and a `src/` package layout in
   `pyproject.toml`. The gate runs the full `pytest` suite, so the T018 implementation must run under a
   Python 3.11+ environment where those dependencies are importable and the repository `src/` is on
   `sys.path`. The baseline environment currently satisfies this (`python3 -V` = 3.13.13, `jsonschema`
   4.26.0/`referencing`/`ruamel.yaml` importable, `python3 -m pytest -q` = 113 passed); provisioning changes
   no repository file. If it cannot be provided at implementation time, the implementation stage returns a
   failed outcome rather than weakening a test.
4. **A-4** — "Baseline" means the exact Git commit identified by `git rev-parse`; no floating branch, tag, or
   ambient state is a valid binding.
5. **A-5** — T018 fixes **no** production numeric bound value. Every bound in §2.4 is an offline-input or
   compiled-entity cap; runtime bounds come from the activation plan or unit configuration (FR-007).
6. **A-6** — Requirement identifiers `T018-STK-###`/`T018-SR-###` and design-unit identifiers `T018-U-###`
   are candidate-chosen names fixed by `detailed-design.md`; no accepted component, contract, requirement, or
   design unit is renumbered. `T018-U-01`..`T018-U-08` realise the accepted `XCOM-DU-009` and `T018-U-09`/
   `T018-U-10` are the work-product and test units; T018 does not renumber `XCOM-DU-009`/`010`/`011`.
7. **A-7** — The compiler's derivation mapping (which graph member feeds which plan member) is implementation
   design owned by `docs/engineering/xcom/t018/`; it introduces no new cross-language contract, so the T017
   `xdl-profile.md` contract is **not** changed and no accepted sentence is rewritten.
8. **A-8** — The normalized graph document `{"resources":[...]}` is an admitted derived input, not an authored
   configuration language: callers obtain it from the accepted `xverse_xdl` normalization path
   (`xverse_xdl.canonical_json`). The compiler re-parses nothing else.
9. **A-9** — The graph digest domain separator `xverse.xcom.normalized-graph.v1\x00` is a T018-design detail
   that the T017 contract leaves open (it requires a `graphDigest` but fixes only its `sha256` form). It is
   provenance metadata, not independently recomputed by the decoder; the T017 plan digest remains the
   activation binding.

## 10. Requirement index

| Requirement | Refines | Primary design units |
| --- | --- | --- |
| T018-STK-001 | — | T018-U-01, T018-U-03, T018-U-04, T018-U-07 |
| T018-STK-002 | — | T018-U-02, T018-U-03, T018-U-04 |
| T018-STK-003 | — | T018-U-05, T018-U-07 |
| T018-STK-004 | — | T018-U-06, T018-U-07, T018-U-08 |
| T018-STK-005 | — | T018-U-09 |
| T018-SR-001 | STK-001, STK-004 | T018-U-01 |
| T018-SR-002 | STK-002 | T018-U-02 |
| T018-SR-003 | STK-001, STK-002 | T018-U-03 |
| T018-SR-004 | STK-002 | T018-U-04 |
| T018-SR-005 | STK-003 | T018-U-05 |
| T018-SR-006 | STK-003 | T018-U-05 |
| T018-SR-007 | STK-004 | T018-U-06, T018-U-07 |
| T018-SR-008 | STK-004 | T018-U-08 |
| T018-SR-009 | STK-001..004 | T018-U-10 |
| T018-SR-010 | STK-005 | T018-U-09 |
