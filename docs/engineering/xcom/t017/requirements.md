# T017 Requirements — `io.xverse.xcom` Profile v0.1 and Activation-Plan v1 Schema and Digest/Provenance Contract

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T017 (capability 007, phase 4 XDL-derived activation plan) |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `a78d6d55dd5a68b1572cf5a594100dfba3be523e` |
| Predecessor tasks | T007–T011 (engineering-baseline enablers, reviewed terminal packages `957a607`/`209084b`/`abb8168`/`a78d6d5`) and the accepted `T-CORE` source present in the baseline |
| Successor tasks | T018 (Python plan compiler in `src/xverse_xdl/xcom_plan.py`), T019 (bounded C++ decoder in `src/xverse/xcom/{include/xverse/xcom/activation_plan.hpp,src/activation_plan.cpp}`), T020 (ordering/malformed/drift/bound/regression tests), then T035–T041 |
| Requirement ID families | `T017-STK-###` (stakeholder), `T017-SR-###` (software) |
| Authority | the T017 entry in `specs/007-xcom-core/tasks.md` ("Define and validate `io.xverse.xcom` Profile v0.1 and the canonical activation-plan v1 schema and digest/provenance contract"); `specs/007-xcom-core/plan.md` "Technical Context", "Project Structure", "Delivery phases" 4, "Complexity Tracking"; `specs/007-xcom-core/spec.md` FR-002, FR-031, SC-002 and the failure semantics; `specs/007-xcom-core/contracts/{xdl-profile,communication-plan}.md`; `specs/007-xcom-core/data-model.md` invariants 1, 2, 7; `docs/engineering/xcom/t010/{requirements,design-units}.md` (`XCOM-DU-009`, `XCOM-DU-010`, `XCOM-DU-011`); `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-001`–`003`, `XCOM-XLC-001`, `XCOM-XLC-005`, `XCOM-XB-001`–`003`); `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` (`XCOM-SW-XDL-001`, `XCOM-DU-XDL-BASELINE`, `XCOM-T-XDL`, `XCOM-L-0134`–`0143`); `docs/engineering/xcom/task-ownership.{md,json}` (T007 `T-XDL` slice); Constitution 2.1.0 articles II, III, IV, VIII, IX, X and the capability acceptance gates; ADR-0016, ADR-0018, ADR-0020; ACC002, ACC003, ACC013, ACC014, ACC015 |
| Classification | Public-safe engineering work product |

### 1.1 Authority statement

This document specifies only the bounded T017 slice. T017 **defines and validates the XDL-facing contracts**:
the versioned `io.xverse.xcom` Profile v0.1 payload schema, the canonical activation-plan v1 schema, the
digest/provenance contract that binds a compiled plan to its normalized XDL input, and an offline,
deterministic validator with controlled negative cases and validation tests. It elaborates the accepted
architecture (`XCOM-CMP-001`–`003`, `XCOM-XLC-001`, `XCOM-XLC-005`, `XCOM-XB-001`–`003`) and the accepted
software requirement `XCOM-SW-XDL-001`.

It does **not** implement the Python plan compiler (T018), implement the C++ decoder (T019), author the
ordering/malformed/drift/bound/regression suite (T020), redesign the accepted architecture, change an
accepted functional requirement, success criterion, ADR, or contract statement, fix production numeric bound
values, create a competing configuration language, accept or integrate any candidate, or approve any other
task.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, the accepted plan and
contracts, the constitution, an accepted ADR, the T007 ownership register, the T008 register/matrix, the T009
architecture model, or the T010 unit design is resolved in favour of the accepted source. A material gap is
reported rather than guessed. Unresolved gaps are recorded in §9.

## 2. Scope

### 2.1 In scope (bounded T017)

Keep T017 strictly inside the T017 task entry: *"Define and validate `io.xverse.xcom` Profile v0.1 and the
canonical activation-plan v1 schema and digest/provenance contract."*

1. **Define the `io.xverse.xcom` Profile v0.1 payload schema** as one closed Draft 2020-12 schema with a
   single closed `kind` discriminator and exactly the five permitted attachment forms from
   `contracts/xdl-profile.md` (`interface-policy`, `flow-policy`, `network-provider`, `observation-policy`,
   `validation-policy`), the recorded `schemaVersion`, `kind`, and decorated identity, and fail-closed unknown
   fields and unsupported versions.
2. **Define the canonical activation-plan v1 schema** as one closed Draft 2020-12 schema covering every
   required-content group of `contracts/communication-plan.md`: plan format version, canonical digest,
   generator version and generation time; exact normalized XDL resource identities, API versions, source
   digests, and graph digest; communication contracts and schema/version references; endpoint roles and route
   graph; selected provider IDs and capability requirements; queue/ordering/reliability/deadline/retry/
   overflow/backpressure policies; allowed observation points and payload policies; allowed stimulation
   actions and permit-policy references; clock domains, activation order, and deterministic diagnostics.
3. **Define the digest/provenance contract**: the canonical serialization rule, the domain-separated SHA-256
   digest, the digest field form, the digested region, the reproducibility rule, and the provenance fields
   that bind the plan to the exact normalized XDL graph, generator, and generation time.
4. **Define the fail-closed activation rule**: a plan with unresolved identity, schema, capability, time,
   ownership, or policy input is inspectable but not activatable; unknown fields and unsupported plan versions
   are rejected; the schema must not permit a plan that claims activation while declaring an unresolved input.
5. **Provide the offline, deterministic, bounded validator** `scripts/validate_xcom_plan.py` that checks both
   schemas, the digest/provenance contract, and a bounded fixture set, and exposes a self-test over the
   declared negative cases with one distinct nonzero exit class per failure family.
6. **Provide validation tests** under `tests/xcom/activation_plan/` that exercise the Profile payload
   positive/negative cases, the activation-plan positive/negative cases, and the digest/provenance vectors
   through the schema and validator, without network, subprocess, or filesystem writes.
7. **Preserve the accepted architecture, ADRs, dependency direction, domain neutrality, safety boundaries,
   REF-002 dispositions, ownership, and dependency order**, and record the contract extension additively in
   the T-XDL-owned `specs/007-xcom-core/contracts/xdl-profile.md`.
8. **Re-validate the T007 ownership register and the T008/T010 consistency** without weakening any accepted
   register or model.

### 2.2 Explicit exclusions (must remain absent from the T017 candidate)

No Python plan compiler is authored (`src/xverse_xdl/xcom_plan.py` is T018); no C++ source is authored or
changed (`src/xverse/xcom/include/**`, `src/xverse/xcom/src/**` are T019, except the JSON schema under
`src/xverse/xcom/contracts/`); no ordering-equivalence, malformed-plan, drift, bound, or regression test suite
is authored (`tests/test_xcom_plan.py` and the C++ `tests/xcom/activation_plan/` suite are T018/T020); no
`proto/`, CMake, `Doxyfile`, or build file is changed; no compilation or runtime execution occurs; no legacy
repository is read or written; no external network peer, package manager, or TCP listener is used; no accepted
ADR, accepted contract statement, accepted requirement, other task's work product, or existing test is
rewritten or weakened; no production numeric bound value is fixed; no competing configuration language,
domain primitive, or unaccepted unit is invented; no other task is marked complete; no software candidate is
accepted or integrated; no REF-002 target is promoted to implemented.

### 2.3 Delegated to later tasks (not implemented or decided here)

| Area | Owner | Disposition in T017 |
| --- | --- | --- |
| Deterministic Profile-aware plan compilation | T018 | allocated; T017 defines the input Profile and output plan contracts and the digest rule the compiler must satisfy |
| Bounded C++ plan decode with independent version/digest/capability checks | T019 | allocated; T017 defines the schema, digest, and fail-closed rule the decoder independently verifies |
| Ordering-equivalence, malformed-plan, drift, bound, regression tests | T020 | allocated; T017 supplies schema/digest validation tests; T020 extends ordering/malformed/drift/bound coverage |
| Configured production bound values | implementation slices | allocated; T017 requires every bound to be finite and declared, and fixes no production numeric value |
| Compiler/build/dependency admission | T011 | allocated; the Python test environment and locked versions remain a T011-adjacent prerequisite (see §9 A-3) |
| Full verification, benchmarks, traceability validation, evidence bundle | T035–T038, T040 | allocated; T017 supplies schema/contract artifacts they verify |
| Independent read-only review and explicit user acceptance | T039, T041 | allocated; T017 does not accept, complete, or integrate any candidate |

### 2.4 Affected paths, negative cases, and bounds

**Affected source paths (T017-owned, from the `T-XDL` slice exclusive list).** The plan stage adds exactly
`docs/engineering/xcom/t017/{requirements,architecture,detailed-design,unit-specifications,verification-plan}.md`.
The implementation stage adds `xdl/profiles/xcom-v0.1.schema.json`,
`src/xverse/xcom/contracts/v1/activation-plan.schema.json`, `scripts/validate_xcom_plan.py`,
`tests/xcom/activation_plan/` (Python validation modules and bounded JSON fixtures), and
`docs/engineering/xcom/t017/implementation.md`, additively extends
`specs/007-xcom-core/contracts/xdl-profile.md`, and marks the T017 checkbox in
`specs/007-xcom-core/tasks.md`. The review and package stages add
`docs/engineering/xcom/t017/internal-review.json` and `reports/xcom-queue/t017-package.json`. No file under
`src/xverse/xcom/include/`, `src/xverse/xcom/src/`, `src/xverse_xdl/`, `proto/`, `cmake/`, or `Doxyfile` is
changed.

**Negative cases.** The declared negative set is `NEG-P01`..`NEG-P14` (Profile payload defects), `NEG-A01`..
`NEG-A22` (activation-plan schema and ordering defects), `NEG-D01`..`NEG-D04` (canonical serialization and
digest defects), `NEG-V01`..`NEG-V08` (validator, canonicalization, and bound defects), and `NEG-G01`..
`NEG-G05` (boundary/governance defects) in `verification-plan.md` §4. Each fixture injects one controlled
defect and asserts one declared nonzero exit class with no partial success.

**Public safety.** The schemas, fixtures, validator output, and the recovered evidence must contain no
credentials, secrets, private addresses, proprietary excerpts, unrestricted payloads, or absolute host paths.
The documented deterministic-gate invocation path in `verification-plan.md` §2 is workflow infrastructure
(an agent instruction), not artifact content, and is out of scope of this content rule.

**Concurrency and resource bounds.** T017 has no runtime concurrency of its own: the two schemas are
`static-immutable` artifacts and the validator is offline, single-threaded, and read-only. Applicable
candidate bounds are per-file input ≤ 1 MiB (fixtures) and ≤ 5 MiB (a supplied plan/Profile document),
aggregate input ≤ 16 MiB, nesting depth ≤ 100, JSON node count ≤ 100 000, wall clock ≤ 60 s, no network, no
subprocess, no filesystem write, and byte-stable deterministic output. The validator applies the 1 MiB bound
to every fixture and the 5 MiB bound to a supplied document, and enforces the depth, node, and wall bounds
fail-closed. The **designed** artifacts' bounds are the `bytes` bound on each schema artifact and the
bounded-size/bounded-depth/bounded-node rules the decoder (T019) must enforce; T017 fixes no production
numeric bound value.

## 3. Terminology and measurement

| Term | Meaning in T017 |
| --- | --- |
| `io.xverse.xcom` Profile v0.1 | The versioned, namespaced policy payload attached at existing XDL `extensions` points and declared by a Profile resource `schemaRef`; validated by `xdl/profiles/xcom-v0.1.schema.json`. |
| Discriminator | The single closed `kind` member that selects exactly one of the five permitted payload forms. |
| Decorated identity | The logical XDL identity (`apiVersion`, `kind`, `namespace`, `name`, optional `version`) whose extension location carries the payload. |
| Activation plan v1 | The canonical, immutable, derived runtime artifact defined by `contracts/communication-plan.md`, validated by `src/xverse/xcom/contracts/v1/activation-plan.schema.json`. |
| Canonical serialization | The byte-stable JSON encoding used as digest input: UTF-8, object members ordered by member name, no insignificant whitespace, every mathematically integral number emitted in its single integer form (so `100` and `100.0` are identical), no non-finite numbers, and no duplicate object members. |
| Digest | Lowercase SHA-256 over the domain-separated canonical serialization of the plan with the `digest` member removed. |
| Provenance | The generator version, normalized XDL resource identities and source digests, graph digest, and generation-time fields that bind the plan to its exact input. |
| Inspectable vs activatable | A plan is `inspectable` when it is well formed but declares an unresolved input; `activatable` only when every identity/schema/capability/time/ownership/policy input resolves. |
| Fail closed | An unknown field, unsupported version, undeclared discriminator, or unresolved input is rejected (or excluded from activation) rather than defaulted. |
| Outcome | Classified validation/validation-result vocabulary: `accepted`, `rejected`, `failed`, `inspectable`, `activatable`. |
| Maturity | Closed vocabulary `implemented`/`partial`/`allocated`/`deferred`/`superseded`/`conflicting`/`needs_clarification`. |
| First proof | The bounded capability-007 prototype scope: owned loopback providers, synthetic sink/tools, no legacy asset, no external peer, no TCP listener. |

Measurements are discrete and observable: schema count and byte size; required-content-group coverage count;
closed-discriminator member count; digest-vector count and byte-equality results; validator exit classes;
negative-case counts per family; requirement/design-unit coverage results; and byte-level schema/fixture
contents. No availability, throughput, timing, or probability figure is asserted.

## 4. Admitted inputs

| Input | Reference | Use |
| --- | --- | --- |
| Capability specification | `specs/007-xcom-core/spec.md` FR-002, FR-031, SC-002, failure semantics, key entities | the XDL-derived, digest-bound plan obligation and the fail-before-activation rule |
| Task entry | `specs/007-xcom-core/tasks.md` T017 and the dependency-order section | authorized bounded scope and successor ordering |
| Accepted plan | `specs/007-xcom-core/plan.md` "Technical Context", "Project Structure", "Delivery phases" 4 | the `io.xverse.xcom` Profile, activation-plan schema, and bounded-decode placement |
| Profile contract | `specs/007-xcom-core/contracts/xdl-profile.md` | the five permitted payload forms, the closed discriminator, and the no-address/no-credential rule |
| Plan contract | `specs/007-xcom-core/contracts/communication-plan.md` | the required activation-plan content, unknown-fields-fail-closed rule, inspectable-vs-activatable rule, and canonical byte-identity requirement |
| Data model | `specs/007-xcom-core/data-model.md` invariants 1, 2, 7 | logical/physical separation, exact-handle ownership, plan-digest binding |
| Unit design | `docs/engineering/xcom/t010/{requirements,design-units}.md` | `XCOM-DU-009` (Profile schema/compiler), `XCOM-DU-010` (activation-plan schema and digest contract), `XCOM-DU-011` (bounded decode) contracts |
| Architecture model | `docs/engineering/xcom/t009/architecture-model.{json,md}` | `XCOM-CMP-001`–`003`, `XCOM-XLC-001`, `XCOM-XLC-005`, `XCOM-XB-001`–`003` identities |
| Requirement register/matrix | `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` | `XCOM-SW-XDL-001` and the `XCOM-DU-XDL-BASELINE`/`XCOM-T-XDL` locators and links `XCOM-L-0134`–`0143` |
| Ownership register | `docs/engineering/xcom/task-ownership.{md,json}`, `scripts/validate_xcom_task_ownership.py` | slice/path ownership, baseline/authorization binding |
| REF-002 traceability | `specs/007-xcom-core/reference-traceability.md`, `docs/architecture/sads-requirements-traceability.json` | the accepted dispositions T017 records without promotion |
| Constitution | `.specify/memory/constitution.md` 2.1.0, articles II, III, IV, VIII, IX, X and the capability acceptance gates | domain neutrality, XDL centrality, standards interoperability, direction, maturity, traceability |
| ADRs | ADR-0016, ADR-0018, ADR-0020 | governing decisions the design cites |
| Acceptance records | `specs/007-xcom-core/checklists/acceptance.md` ACC002/ACC003/ACC013/ACC014/ACC015 | exact authorization references |
| XDL schema baseline | `xdl/schemas/v1alpha1/{common,profile,component,deployment,scenario}.schema.json`, `src/xverse_xdl/schema.py` | the extension-point and `schemaRef` conventions and the established Draft 2020-12 validation approach |
| Baseline provenance | `git rev-parse a78d6d55dd5a68b1572cf5a594100dfba3be523e`, `git log` for `src/xverse/xcom/**`, `tests/xcom/**`, `src/xverse_xdl/**`, `xdl/**` | existing-artifact anchoring only; never acceptance proof |

## 5. Stakeholder requirements

### T017-STK-001 — Versioned, closed `io.xverse.xcom` Profile v0.1

**Statement.** Capability 007 must define one versioned `io.xverse.xcom` Profile v0.1 payload schema on the
existing XDL extension points, with a single closed `kind` discriminator covering exactly the five permitted
attachment forms, a recorded `schemaVersion` and decorated identity, and fail-closed rejection of unknown
fields, unknown kinds, and unsupported versions — without introducing a competing configuration language or
storing provider addresses, credentials, permits, handles, or sessions in logical resources.

**Acceptance criteria (observable).**

- AC-1: Exactly one `xdl/profiles/xcom-v0.1.schema.json` exists, is a valid Draft 2020-12 schema, and is
  closed (`additionalProperties: false` at every object).
- AC-2: The `kind` enum contains exactly the five permitted forms, and each form's payload shape is declared
  with a closed member set.
- AC-3: An unknown field, unknown `kind`, missing `schemaVersion`/`kind`/identity, or unsupported version is
  rejected.
- AC-4: A payload carrying a provider address, credential, permit, live handle, or tool session in a logical
  resource location is rejected.

**Source anchors.** `contracts/xdl-profile.md`; spec FR-031/FR-002; Constitution arts. III, V; T010
`XCOM-DU-009`; `XCOM-XLC-005`.

### T017-STK-002 — Canonical, fail-closed activation-plan v1 schema

**Statement.** Capability 007 must define one canonical activation-plan v1 schema that covers every
required-content group of the accepted plan contract, records the plan format version and digest, is closed to
unknown fields, and distinguishes an inspectable plan from an activatable plan so a plan with any unresolved
identity/schema/capability/time/ownership/policy input cannot activate.

**Acceptance criteria (observable).**

- AC-1: Exactly one `src/xverse/xcom/contracts/v1/activation-plan.schema.json` exists, is a valid Draft
  2020-12 schema, and is closed.
- AC-2: Every required-content group of `contracts/communication-plan.md` is represented by a required member
  (or a required member of a required member).
- AC-3: `planVersion` is fixed; an unknown top-level field or a missing required group is rejected.
- AC-4: The schema cannot represent an `activatable` plan whose declared input status is unresolved; the
  decoder (T019) and validator enforce the same rule.

**Source anchors.** `contracts/communication-plan.md`; spec FR-002/SC-002; T010 `XCOM-DU-010`; `XCOM-XLC-001`.

### T017-STK-003 — Digest/provenance contract for the derived plan

**Statement.** Capability 007 must define the digest/provenance contract that binds an activation plan to its
exact normalized XDL input: a byte-stable canonical serialization, a domain-separated SHA-256 digest over the
plan body, a digest field form, provenance fields naming the generator and the source resource/graph digests,
and a reproducibility rule that makes equivalent normalized inputs produce byte-identical plans.

**Acceptance criteria (observable).**

- AC-1: The canonical serialization rule is stated precisely enough to reimplement independently and is
  byte-stable under member reordering and whitespace changes.
- AC-2: The digest algorithm, domain separator, digested region, and field form are fixed, and a digest is
  never computed over itself.
- AC-3: Provenance names the generator version, the normalized XDL graph digest, and the source resource
  digests; a plan missing provenance or whose recorded digest does not match the recomputed digest is rejected.
- AC-4: Equivalent normalized inputs at a fixed generation time produce byte-identical canonical bytes and
  the same digest.

**Source anchors.** `contracts/communication-plan.md`; spec SC-002; `data-model.md` invariant 7; T010
`XCOM-DU-010`; `XCOM-XLC-001`.

### T017-STK-004 — Deterministic, offline, public-safe validation

**Statement.** T017 must provide a repository-owned, deterministic, offline, bounded validator with a
self-test over the declared negative cases and validation tests under `tests/`, so the schemas and the
digest/provenance contract are machine-checked without network, subprocess, or filesystem writes, and so the
retained evidence is public-safe.

**Acceptance criteria (observable).**

- AC-1: `scripts/validate_xcom_plan.py` parses both schemas, checks the closed/discriminator/coverage/digest
  rules, and validates the bounded fixtures, with one distinct nonzero exit class per failure family.
- AC-2: `--self-test` injects every declared negative case and asserts the declared exit with no partial
  success.
- AC-3: The validator is offline, single-threaded, bounded, and byte-stable; the validation tests exercise the
  positive and negative cases through the schema/validator and pass under the repository test command.
- AC-4: No schema, fixture, validator output, or evidence contains a credential, private address, proprietary
  excerpt, unrestricted payload, or absolute host path.

**Source anchors.** spec FR-027/FR-030; Constitution art. X; `contracts/xdl-profile.md`; T010 `XCOM-DU-009`/
`XCOM-DU-010`.

### T017-STK-005 — Accepted intent, governance, and dependency order preserved

**Statement.** T017 must preserve the accepted architecture, accepted ADRs, REF-002 dispositions, safety
boundaries, failure semantics, one-way dependency direction, domain neutrality, ownership, and dependency
order, must not implement T018/T019/T020, must not weaken an existing requirement or test, and must not mark
the task complete in the plan stage or claim acceptance/review.

**Acceptance criteria (observable).**

- AC-1: No `src/xverse/xcom/src/**`, `src/xverse/xcom/include/**`, `src/xverse_xdl/**`, `proto/**`, CMake,
  `Doxyfile`, or build file is changed; no accepted ADR or contract statement is rewritten (the
  `xdl-profile.md` change is additive and T-XDL-owned).
- AC-2: `ref002.disposition = "unchanged"` with an empty promoted set; no deferred/allocated target is
  reported as implemented.
- AC-3: The T017 checkbox is left unchecked in the plan stage and marked only in the implementation stage; no
  acceptance or integration claim is recorded; review remains a separate pass.
- AC-4: The T007 ownership validator and the T008/T010 consistency still pass; the T017 plan work products
  exist with the required structure.

**Source anchors.** ADR-0018/ADR-0020; ACC014/ACC015; Constitution arts. II, VIII, IX, X; T007 register;
`tasks.md` T039/T041.

## 6. Software requirements

Each software requirement refines one or more stakeholder requirements. Identifier names of the design
artifacts are fixed by `detailed-design.md`.

### 6.1 Profile v0.1 schema

#### T017-SR-001 — Profile payload structure, discriminator, and version (refines T017-STK-001)

**Statement.** The Profile v0.1 schema must require `schemaVersion`, a closed `kind`, and the decorated
identity, must fix `schemaVersion` to exactly `"0.1"`, must constrain `kind` to the five permitted forms, and
must reject a missing/extra member, an unknown `kind`, or an unsupported version.

**Acceptance criteria.** Schema valid and closed; `schemaVersion` const `"0.1"`; `kind` enum exactly the five
forms; `required` includes `schemaVersion`, `kind`, and the identity member; unknown-version and
unknown-kind fixtures rejected with the declared class.

**Verification intent.** CHK-01, CHK-02; NEG-P01..NEG-P05.

#### T017-SR-002 — Per-form payload grammar (refines T017-STK-001)

**Statement.** For each permitted form the schema must declare a closed payload object capturing the form's
contract obligations: `interface-policy` (interaction kind, schema/encoding constraints, semantic
compatibility), `flow-policy` (ordering, reliability, deadline, retry, queue, overflow, observation points),
`network-provider` (required provider capabilities, declared fidelity/limitations), `observation-policy`
(filters, metadata/payload access, bounds, validity effect), and `validation-policy` (allowed stimulation
actions, injection points, service-emulation eligibility, time policy, quotas, permit-policy reference); a
form payload missing a required member or carrying an unknown member is rejected.

**Acceptance criteria.** All five forms declared and closed; each required member present; a per-form negative
fixture rejected with the declared class.

**Verification intent.** CHK-03; NEG-P06..NEG-P11.

#### T017-SR-003 — Profile placement and logical-resource safety (refines T017-STK-001, T017-STK-005)

**Statement.** The Profile schema and its supporting contract text must forbid storing provider addresses,
credentials, validation permits, live handles, or tool sessions in a logical resource payload, and must
require that a form is attached only at a legal XDL extension location; a payload containing any such
environment-specific or secret value, a duplicate/conflicting policy, or an illegal attachment is rejected.

**Acceptance criteria.** No schema member accepts an address/credential/permit/handle/session; the contract
text states the placement rule; NEG-P12..NEG-P14 rejected with the declared class.

**Verification intent.** CHK-04; NEG-P12..NEG-P14.

### 6.2 Activation-plan v1 schema and digest contract

#### T017-SR-004 — Activation-plan required-content coverage (refines T017-STK-002)

**Statement.** The activation-plan schema must require, in a closed object, `planVersion`, `digest`,
`generator`, `provenance`, `contracts`, `endpoints`, `routes`, `providers`, `policies`, `observationPoints`,
`stimulation`, `clockDomains`, `activationOrder`, `diagnostics`, and `status`; each member must represent the
corresponding required-content group; a missing required group, an unknown top-level field, or a wrong
`planVersion` is rejected.

**Acceptance criteria.** All required members present and closed; `planVersion` const `"1"`; a
missing-group/unknown-field/wrong-version fixture rejected with the declared class.

**Verification intent.** CHK-05, CHK-06; NEG-A01..NEG-A08.

#### T017-SR-005 — Inspectable-versus-activatable fail-closed rule (refines T017-STK-002, T017-STK-005)

**Statement.** The schema must model a plan `status` from the closed vocabulary `{inspectable, activatable}`
and must not permit a plan to be `activatable` while any declared input-resolution member records an
unresolved identity, schema, capability, time, ownership, or policy input; the validator must reject a plan
that claims `activatable` with an unresolved input and must accept an `inspectable` plan with one.

**Acceptance criteria.** `status` closed; the conditional rule present; NEG-A09 (activatable-with-unresolved)
and NEG-A10 (inspectable-with-unresolved, accepted) behave as declared.

**Verification intent.** CHK-07; NEG-A09, NEG-A10.

#### T017-SR-006 — Deterministic ordering of plan collections (refines T017-STK-002, T017-STK-003)

**Statement.** The schema must require the plan's identity-bearing collections (contracts, endpoints, routes,
providers, observation points, clock domains, activation order, diagnostics) to be in their declared
deterministic order with unique identifiers, so that semantically equivalent normalized inputs serialise
identically; a duplicate identifier or an out-of-order collection is rejected.

**Acceptance criteria.** Each collection has a stable key and uniqueness rule; the validator checks ordering
and uniqueness; NEG-A11..NEG-A13 and NEG-A17..NEG-A22 rejected with the declared class.

**Verification intent.** CHK-08; NEG-A11..NEG-A13, NEG-A17..NEG-A22.

#### T017-SR-007 — Digest and provenance contract and reproducibility (refines T017-STK-003)

**Statement.** The digest/provenance contract must define the canonical serialization, the domain separator,
the digested region (the plan with the `digest` member removed), the digest field form (algorithm `sha256`
and a 64-character lowercase-hex value), the provenance fields (generator version, generation time, normalized
XDL graph digest, and per-resource identity/API-version/source-digest records), and the reproducibility rule
(fixed generation time yields byte-identical canonical bytes); a plan with a missing/malformed digest, a
digest equal to the recomputation of a different body, a self-referential digest region, or missing
provenance is rejected.

**Acceptance criteria.** Contract text and schema agree on all digest/provenance members; the validator
recomputes the digest over the canonical body and compares; NEG-A14..NEG-A16 and NEG-D01..NEG-D04 behave as
declared.

**Verification intent.** CHK-09, CHK-10, DET-01..DET-03; NEG-A14..NEG-A16, NEG-D01..NEG-D04.

### 6.3 Validator, tests, governance, and binding

#### T017-SR-008 — Offline deterministic validator with per-family exit classes (refines T017-STK-004)

**Statement.** `scripts/validate_xcom_plan.py` must check the Profile schema, the activation-plan schema, the
closed/discriminator/coverage/digest rules, and the bounded fixtures; support `--verify`, `--self-test`, and
`--check-human`; be deterministic, offline, single-threaded, and bounded; read only the repository's declared
artifact set and fixtures; and expose a distinct nonzero exit class per failure family with no partial
success.

**Acceptance criteria.** `--verify` passes on the real artifacts; `--self-test` exercises every declared
negative case; exit classes are distinct and documented; no network/subprocess/write; file/runtime bounds
hold.

**Verification intent.** CHK-11, CHK-12, BND-01..BND-04; NEG-V01..NEG-V08.

#### T017-SR-009 — Validation tests for Profile, activation plan, and digest (refines T017-STK-004)

**Statement.** Validation tests under `tests/xcom/activation_plan/` must exercise the Profile positive and
negative cases, the activation-plan positive and negative cases, and the digest/provenance vectors by
importing the validator's pure functions and/or by invoking its `--verify`/`--self-test` entry points, and
must not perform network, subprocess, or filesystem writes.

**Acceptance criteria.** Tests exist for Profile, plan, and digest families; each negative case is asserted;
the full repository test command passes.

**Verification intent.** CHK-13; `pytest` gate; NEG-Pxx/NEG-Axx/NEG-Dxx asserted in tests.

#### T017-SR-010 — Additive XDL Profile contract recording (refines T017-STK-005)

**Statement.** The T-XDL-owned `specs/007-xcom-core/contracts/xdl-profile.md` must be extended additively to
record the Profile v0.1 payload grammar, the extension-location rule, and the digest/provenance contract, so
the schema and validator have a normative contract; no existing accepted contract statement may be rewritten
or weakened.

**Acceptance criteria.** The file gains new sections; existing sentences are unchanged; a reader can derive
the exact schema rules from it.

**Verification intent.** CHK-14; inspection and `git diff` review.

#### T017-SR-011 — Boundary, binding, and REF-002 non-promotion (refines T017-STK-005)

**Statement.** The T017 candidate must change only the T017-owned work products and `T-XDL` exclusive paths
declared in §2.4, must bind to baseline `a78d6d55dd5a68b1572cf5a594100dfba3be523e`, must cite only accepted
authorizations, must link `XCOM-SW-XDL-001` and the `XCOM-DU-XDL-BASELINE`/`XCOM-T-XDL` locators, must leave
the T017 checkbox unchecked in the plan stage, and must record `ref002.disposition = "unchanged"` with an
empty promoted set; a change outside the authorized paths, an unknown authorization, a dangling link, a
REF-002 promotion, or a public-safety leak fails validation.

**Acceptance criteria.** `git diff --name-only` ⊆ the authorized path set; baseline binds by `git rev-parse`;
links resolve in the T008 matrix; REF-002 promoted set empty; public-safety scan clean.

**Verification intent.** CHK-15, CHK-16; NEG-G01..NEG-G05.

## 7. Capability 007 requirement links

| Capability anchor | T017 disposition and link | Remaining work |
| --- | --- | --- |
| FR-031 versioned `io.xverse.xcom` Profile on existing XDL extension points, compiled into the digest-bound plan | **Implemented for this slice (definition/validation)**: T017-SR-001..003 define Profile v0.1; T017-SR-004..007 define the plan and digest contract; `XCOM-SW-XDL-001`. | T018 compiles; T019 decodes; T020 tests. |
| FR-002 derive from the exact normalized XDL graph; no competing configuration language | **Implemented for this slice (definition/validation)**: the Profile and plan are derived/validated against XDL identities; T017-SR-011 forbids a competing language. | T018 compiles deterministically; T038 validates traceability. |
| SC-002 equivalent normalized inputs produce byte-identical plans and diagnostic ordering | **Implemented for this slice (contract)**: T017-SR-006/007 define deterministic ordering and canonical digest; T017 validation tests check ordering. | T018/T019/T020 prove byte-identical plans and ordering equivalence. |
| FR-027 public-safe evidence/logs | **Partial (constraint)**: T017-SR-011 and the validator's public-safety check keep schemas/fixtures/evidence free of secrets and absolute paths. | Enforced at runtime by the slices; T035/T038 verify. |
| FR-030 traceability, evidence, separate review | **Partial (governance)**: T017 binds `XCOM-SW-XDL-001` and the design-unit/test locators; review/acceptance remain separate. | T038 validates traceability; T039/T041 review and accept. |
| Constitution arts. II, III, IV, VIII, IX, X | **Implemented for this slice (definition/validation)**: T017-SR-003/010/011 preserve neutrality, XDL centrality, standards interoperability, direction, maturity, and traceability. | Bound to exact candidates by later tasks. |

## 8. REF-002 dispositions

T017 is a schema/contract definition task and implements **no** direct REF-002 communication requirement
XVE-SYS-0139–0158 and no shared requirement. It **records** `ref002_disposition = "unchanged"` and promotes
none. Every capability-007 disposition in `specs/007-xcom-core/reference-traceability.md` and
`docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` remains exactly as accepted.

| REF-002 group | Disposition in T017 | Basis |
| --- | --- | --- |
| `XVE-SYS-0139`–`0158` (communication/interoperability) | **unchanged** — no target is promoted; the disposition set is empty | T017 defines schemas and a contract only; it implements and demonstrates nothing. |
| Shared extensibility (`XVE-SYS-0237`–`0250`), time (`XVE-SYS-0251`–`0264`), failure recovery (`XVE-SYS-0265`–`0279`) | **allocated to their owning capabilities; unchanged** | `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` §X-COM allocation; capability 007 may define contracts but claims no full system requirement. |

**Conflicting:** none identified within the admitted inputs.
**Needing clarification:** none; the only open items are the environment prerequisite (§9 A-3) and the
not-yet-present T018/T019/T020 artifacts (§9 A-1), which T017 records rather than resolves.

## 9. Assumptions and open items

1. **A-1 (owned successor artifacts pending)** — `src/xverse_xdl/xcom_plan.py` (T018),
   `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp` and `src/xverse/xcom/src/activation_plan.cpp`
   (T019), and the extended `tests/test_xcom_plan.py`/C++ `tests/xcom/activation_plan/` suite (T020) are not
   present in the baseline. T017 defines the contracts they consume; it does not create them.
2. **A-2 (accepted T-CORE source present but unreconciled)** — `src/xverse/xcom/**` contains SESN-era C++
   artifacts whose task checkboxes are open (analysis A12). T017 does not read, extend, or reconcile them.
3. **A-3 (test-environment prerequisite)** — the repository declares Python dependencies
   (`jsonschema[format]>=4.26,<5`, `referencing`, `ruamel.yaml`) and a `src/` package layout in
   `pyproject.toml`. The gate runs the full `pytest` suite, so the T017 implementation must run under a
   Python 3.11+ environment where those dependencies are importable and the repository `src/` is on
   `sys.path` (the declared baseline shell lacks them). Provisioning that environment with the locked
   versions is a prerequisite recorded here; it is not a T017 product artifact and changes no repository
   file. If it cannot be provided, the implementation stage returns a failed outcome rather than weakening a
   test.
4. **A-4** — "Baseline" means the exact Git commit identified by `git rev-parse`; no floating branch, tag, or
   ambient state is a valid binding.
5. **A-5** — T017 fixes **no** production numeric bound value. The bounds in §2.4 are validator/validator-input
   bounds aligned with the accepted `LoadLimits` defaults; runtime plan bounds come from the activation plan
   or unit configuration (FR-007).
6. **A-6** — Requirement identifiers `T017-STK-###`/`T017-SR-###` and design-unit identifiers `T017-U-###`
   are candidate-chosen names fixed by `detailed-design.md`; no accepted component, contract, requirement, or
   design unit is renumbered. `T017-U-01`/`T017-U-02` realise the accepted `XCOM-DU-009`/`XCOM-DU-010`.
7. **A-7** — The `xdl-profile.md` update is additive: new sections are appended and no existing sentence is
   altered. The file is owned by the `T-XDL` slice, so the change is authorized.
8. **A-8** — Canonical serialization is intentionally a small, explicit rule rather than an invented
   configuration language; it is a digest-input encoding of the already-defined plan, and RFC 8785-style
   interoperability remains a later option if a plan consumer requires it.

## 10. Requirement index

| Requirement | Refines | Primary design units |
| --- | --- | --- |
| T017-STK-001 | — | T017-U-01, T017-U-03, T017-U-04 |
| T017-STK-002 | — | T017-U-02, T017-U-03 |
| T017-STK-003 | — | T017-U-02, T017-U-03, T017-U-05 |
| T017-STK-004 | — | T017-U-05, T017-U-06, T017-U-07 |
| T017-STK-005 | — | T017-U-04, T017-U-08 |
| T017-SR-001 | STK-001 | T017-U-01 |
| T017-SR-002 | STK-001 | T017-U-01 |
| T017-SR-003 | STK-001, STK-005 | T017-U-01, T017-U-04 |
| T017-SR-004 | STK-002 | T017-U-02 |
| T017-SR-005 | STK-002, STK-005 | T017-U-02, T017-U-05 |
| T017-SR-006 | STK-002, STK-003 | T017-U-02, T017-U-05 |
| T017-SR-007 | STK-003 | T017-U-02, T017-U-03, T017-U-05 |
| T017-SR-008 | STK-004 | T017-U-05 |
| T017-SR-009 | STK-004 | T017-U-06, T017-U-07 |
| T017-SR-010 | STK-005 | T017-U-04 |
| T017-SR-011 | STK-005 | T017-U-04, T017-U-08 |
