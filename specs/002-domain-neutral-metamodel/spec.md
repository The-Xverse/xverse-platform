# Feature Specification: M1 domain-neutral metamodel

**Feature Branch**: \`main\` (existing branch; no branch creation required)
**Created**: 2026-09-20
**Status**: Approved M1 architecture — user approval recorded on 2026-09-20; M2 entry gate satisfied
**Input**: Continue after approved M0 with the Spec Kit M1 domain-neutral metamodel capability.

## User Scenarios & Testing

### User Story 1 — Define a domain-neutral system (Priority: P1)

As a platform architect, I can describe a cyber-physical system without embedding an industry,
provider, protocol, simulator, or deployment-specific identity in the platform core.

**Why this priority**: A stable, neutral semantic core is the prerequisite for all future XDL and
runtime work.

**Independent Test**: A reviewer can trace every mandatory core concept to a purpose, identity,
lifecycle, required/optional attributes, relationships, validation rules, and extension strategy.

**Acceptance Scenarios**:

1. **Given** a system with logical components and devices, **When** it is modeled, **Then** its
   identity remains independent of any process, container, physical address, or provider name.
2. **Given** a domain-specific concept, **When** it is needed, **Then** it is represented through a
   declared profile/extension rather than a new core dependency.

---

### User Story 2 — Bind a system without changing its identity (Priority: P1)

As a platform architect, I can map the same logical system to simulated, virtual, physical, or hybrid
realizations while retaining provenance, lifecycle intent, and resource constraints.

**Why this priority**: This fulfills the cyber-physical portability requirement and prevents
environment details from leaking into architecture models.

**Independent Test**: A reviewer can follow the logical-to-realization path only through Deployment
and determine required bindings, readiness conditions, evidence, and failure semantics.

**Acceptance Scenarios**:

1. **Given** one logical Device, **When** it is bound to two different declared realization classes,
   **Then** the Device identifier remains unchanged and each Deployment has distinct provenance.
2. **Given** a Deployment with unresolved artifacts, resources, time mappings, or targets, **When**
   its state is assessed, **Then** it cannot be declared Ready.

---

### User Story 3 — Define observable, repeatable experiments (Priority: P2)

As a systems researcher, I can declare scenarios, time semantics, faults, observers, metrics, and
evidence limitations without claiming that an executor already exists.

**Why this priority**: Repeatability and honest maturity claims are necessary before later runtime
and blueprint work can produce defensible results.

**Independent Test**: A reviewer can determine a scenario’s system, time domain, intended
perturbations, observed evidence, metric interpretation, and explicit unknowns from the model.

**Acceptance Scenarios**:

1. **Given** a Scenario that crosses time domains, **When** it is validated, **Then** it requires an
   explicit mapping or tolerance before deterministic behavior can be claimed.
2. **Given** a Fault or Observer, **When** it is declared, **Then** its target, activation or
   collection condition, and evidence limitation are explicit.

---

### User Story 4 — Govern extension and later implementation (Priority: P2)

As a reviewer, I can assess the proposed vocabulary and ADRs before M2 creates XDL schemas or any
runtime capability.

**Why this priority**: A reviewed model prevents later implementations from silently changing core
semantics.

**Independent Test**: The architecture package contains a diagram, ADRs, traceability, review
findings, acceptance checklist, and explicit exclusions.

**Acceptance Scenarios**:

1. **Given** a proposed extension, **When** it adds specialized behavior, **Then** it uses its own
   namespace and cannot redefine a core identity or validation rule.
2. **Given** M1 documentation, **When** a reviewer checks scope, **Then** no schema, parser, loader,
   adapter, executable blueprint, or legacy modification is presented as implemented.

### Edge Cases

- A logical element has no available realization: retain Unbound/unknown state instead of inventing
  a target.
- An external artifact is private, unavailable, mutable, or lacks a digest: retain the provenance
  gap; do not claim reproducibility.
- An interface transformation, protocol binding, resource allocation, or time mapping is missing:
  reject semantic readiness or record the required exception explicitly.
- A profile attempts to redefine a core term, inject a secret/address, or turn a maturity target into
  an implementation claim: reject it at semantic review.
- A legacy repository has contradictory documented and source-observed behavior: preserve M0 evidence
  and defer the compatibility choice to its own reviewed capability.

## Requirements

- **FR-001**: Define every M1-required core concept with purpose, identity, lifecycle, required and
  optional attributes, relationships, validation rules, and extension strategy.
- **FR-002**: Keep platform semantics domain-neutral; specialized terminology, protocols, providers,
  and equipment types must be profile, adapter, or blueprint concerns.
- **FR-003**: Separate logical System/Component/Node/Device/Interface/Flow identity from realization;
  Deployment is the explicit environment binding.
- **FR-004**: Define semantic lifecycle, readiness, failure, provenance, maturity, and evidence
  concepts without implying an implementation of orchestration or runtime behavior.
- **FR-005**: Define Interfaces, Endpoints, Flows, Networks, Links, and Protocol bindings so that
  direction, payload compatibility, timing, and transformation requirements can later be validated.
- **FR-006**: Define Scenario, Fault, Observer, Metric, TimeDomain, Clock, Resource, and
  ComputeResource semantics for reproducible future experiments.
- **FR-007**: Define profile/namespace extension rules that preserve core meaning and reference
  external standards rather than replacing them.
- **FR-008**: Create and link ADRs for the core vocabulary, logical/realization binding,
  lifecycle/time/evidence semantics, and extension boundaries.
- **FR-009**: Preserve legacy immutability; incorporate M0 findings only as constraints and make no
  runtime compatibility, parity, or execution claim.
- **FR-010**: Produce a public-safe architecture package, validate cross-document coverage, and
  conduct a separate architecture review before declaring M1 ready for human review.
- **FR-011**: Do not create XDL schemas, serialization, a custom grammar, loaders, validators,
  runtime plans, adapters, catalogs, or executable blueprints in this capability.

### Key Entities

System; Scenario; Component; Node; Device; Sensor; Actuator; ComputeResource; Interface; Endpoint;
Flow; Network; Link; Protocol; Model; Artifact; ExecutionTarget; Simulator; TimeDomain; Clock; Fault;
Observer; Metric; Parameter; Resource; Deployment; Profile Extension; Evidence Reference.

## Success Criteria

- **SC-001**: All 26 required core concepts have complete definition fields and no unresolved template
  placeholders.
- **SC-002**: The logical-to-realization relationship is represented exclusively through Deployment
  in the conceptual model and diagram.
- **SC-003**: Each of the four proposed M1 ADRs states its decision, alternatives/consequences,
  evidence, scope, and review status.
- **SC-004**: All requirement and diagram references resolve, and documentary validation reports no
  errors.
- **SC-005**: The separate review contains no BLOCKER or MAJOR constitutional conflict; any remaining
  MINOR/ADVISORY finding is explicit.
- **SC-006**: The M1 package makes no unsupported implementation, runtime, compatibility, fidelity,
  or production-change claim.

## Assumptions and clarification decisions

- M1 creates semantic architecture documentation only. M2 will decide XDL resource packaging,
  serialization grammar, schema syntax, loader behavior, and versioning.
- Namespace-qualified semantic identity is required, but exact identifier syntax and registry
  governance are deferred to M2.
- Deployment is the only logical-to-realization binding; a System definition may declare supported
  realization classes but cannot include provider-local values.
- Lifecycle profiles are semantic validation contracts, not a commitment to a particular scheduler,
  protocol, provider, or error-recovery implementation.
- The SADS and technical description are supplemental reference inputs under
  [REFERENCE_REGISTER.md](../../docs/architecture/REFERENCE_REGISTER.md), not instructions that
  override the user-approved guidance or M0 evidence.

## X-Verse capability obligations

**Compatibility impact**: None on production. M0 findings R01–R05 constrain future descriptor and
runtime work but are not repaired or executed here.

**Failure semantics**: Unresolved references, incompatible contracts, absent artifacts, unavailable
evidence, invalid profile redefinition, and missing time mapping prevent semantic readiness. Failures
are recorded as evidence gaps or lifecycle state, not hidden with defaults.

**Observable outcomes**: Reviewers can inspect the metamodel, diagram, ADRs, traceability, checklists,
and validation report. No runtime signals exist for this documentation-only capability.

**Maturity**: Proposed architectural target. No execution success, interface compatibility, model
fidelity, or deterministic operation is demonstrated.

**Runtime tests**: Not applicable; no executable runtime, adapter, or production workload is created.
