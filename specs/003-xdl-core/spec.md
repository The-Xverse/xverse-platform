# Feature Specification: M2 XDL Core v0.1

**Feature Branch**: \`main\` (existing branch; no branch creation required)
**Created**: 2026-09-20
**Status**: Approved M2 specification/schema package; user approval recorded on 2026-09-20
**Input**: Define XDL Core v0.1 from the approved M1 metamodel using Spec Kit. Do not implement a
loader, runtime, compatibility adapter, catalog, or production integration.

## User Scenarios & Testing

### User Story 1 — Describe a logical system (Priority: P1)

As a systems architect, I can represent a domain-neutral cyber-physical system using stable identity,
components, nodes, devices, interfaces, endpoints, flows, networks, models, parameters, and time
domains without including environment-specific deployment values.

**Independent Test**: Validate a System example against the System schema and confirm every reference
resolves within the declared namespace or through an explicit resource reference.

**Acceptance Scenarios**:

1. **Given** a logical System document, **When** it contains valid components, endpoints, and flows,
   **Then** its structure passes the v1alpha1 schema and semantic rules.
2. **Given** a System containing a host address, credential value, or concrete runtime target in its
   logical identity, **When** it is reviewed, **Then** the value is rejected as a realization concern.

### User Story 2 — Bind a realization overlay (Priority: P1)

As a deployment architect, I can bind logical elements to simulated, virtual, physical, or hybrid
execution targets without changing their logical identifiers.

**Independent Test**: Validate a Deployment example, resolve its System and element references, and
confirm each binding declares realization class, target, lifecycle/readiness, and artifact/resource
constraints.

**Acceptance Scenarios**:

1. **Given** the same System and two Deployment resources, **When** their bindings differ, **Then**
   the System and element identities remain unchanged.
2. **Given** an unresolved artifact, target, resource claim, or time mapping, **When** readiness is
   evaluated, **Then** the Deployment cannot be considered Ready.

### User Story 3 — Define a reproducible experiment (Priority: P2)

As a researcher, I can define a Scenario with stimuli, faults, observers, metrics, timing, and
traceability while separating declared intent from observed evidence.

**Independent Test**: Validate a Scenario example and confirm that every action, fault, observer, and
metric has a target, time interpretation, and evidence/acceptance semantics where applicable.

**Acceptance Scenarios**:

1. **Given** a Scenario referencing multiple time domains, **When** no mapping or tolerance exists,
   **Then** semantic validation reports the ambiguity.
2. **Given** a metric, **When** its observer inputs or unit semantics are missing, **Then** the
   Scenario is incomplete rather than implicitly accepted.

### User Story 4 — Reuse components and extensions (Priority: P2)

As a platform integrator, I can declare reusable Component resources and namespaced Profile resources
without redefining XDL Core or duplicating external standards.

**Independent Test**: Validate Component and Profile examples and confirm extension payloads use
declared reverse-domain namespaces with compatible XDL API versions.

**Acceptance Scenarios**:

1. **Given** a profile extension, **When** its namespace is not declared or it attempts to overwrite a
   core field, **Then** semantic validation rejects it.
2. **Given** an external model or standard artifact, **When** it is referenced, **Then** XDL stores
   provenance and binding information rather than copying its complete semantic model.

### User Story 5 — Evolve XDL safely (Priority: P2)

As a tool author, I can determine schema/API compatibility, resource revision, and external artifact
version independently, and I can normalize YAML or JSON into the same semantic representation.

**Independent Test**: Compare equivalent YAML and JSON examples after parsing and confirm that
presentation order, comments, and YAML anchors do not affect canonical semantic identity.

**Acceptance Scenarios**:

1. **Given** an unknown core field, **When** a v1alpha1 schema validates the resource, **Then** it is
   rejected unless it appears under a declared extension namespace.
2. **Given** a breaking semantic change, **When** it is introduced, **Then** it uses a new API version
   and an explicit conversion decision rather than silently changing v1alpha1.

### Edge Cases

- Duplicate element identifiers in one resource.
- Cross-resource references with missing namespace, kind, name, or element.
- Cyclic resource references or imports.
- YAML aliases, duplicate keys, implicit scalar types, and non-string mapping keys.
- Mutable artifact tags without digest/revision evidence.
- Unknown core fields, undeclared extensions, or conflicting profile namespaces.
- A physical realization without an external asset binding.
- A flow whose endpoint direction, interface, protocol, or time semantics are incompatible.
- A scenario fault targeting an element outside the selected System/Deployment.
- Secrets or private infrastructure values embedded in shareable resources.

## Requirements

- **FR-001**: XDL Core v0.1 MUST use the API version \`xverse.io/xdl/v1alpha1\` and YAML 1.2.2 or JSON
  serialization mapped to the JSON data model.
- **FR-002**: Every resource MUST contain \`apiVersion\`, \`kind\`, \`metadata\`, and \`spec\`.
- **FR-003**: The initial resource kinds MUST be System, Component, Deployment, Scenario, and Profile.
- **FR-004**: Resource identity MUST be derived from API version, kind, namespace, and name; element
  identity MUST be unique inside its owning resource.
- **FR-005**: References MUST be structured and explicit; string path conventions MUST NOT be used as
  hidden resolution rules.
- **FR-006**: System MUST represent the approved M1 logical concepts without provider or
  industry-specific dependencies.
- **FR-007**: Component MUST describe a reusable logical capability and its contracts without
  prescribing a process/container runtime.
- **FR-008**: Deployment MUST be the sole resource that binds logical identity to artifacts,
  execution targets, simulators, resources, networks, time mappings, and lifecycle readiness.
- **FR-009**: Scenario MUST represent stimuli, faults, observers, metrics, timing, and acceptance
  intent while preserving evidence limitations.
- **FR-010**: Profile MUST declare a reverse-domain namespace, compatible API versions, referenced
  schema/documentation, and conflict policy.
- **FR-011**: Core schemas MUST use JSON Schema Draft 2020-12 and reject unknown core fields.
- **FR-012**: Namespaced extension payloads MUST be isolated under \`extensions\`; extensions MUST NOT
  redefine core identity, relationships, or validation meaning.
- **FR-013**: Schema/API version, resource revision, profile version, and artifact/model version MUST
  remain separate concepts.
- **FR-014**: v1alpha1 compatibility MUST require exact API-version recognition; incompatible changes
  MUST use a new API version and explicit conversion.
- **FR-015**: YAML presentation details, key order, comments, anchors, and aliases MUST NOT affect the
  normalized semantic model or canonical identity.
- **FR-016**: Validation MUST be layered: parse, schema, reference, semantic, binding/readiness, and
  policy checks, with stable diagnostic locations and severity.
- **FR-017**: XDL MUST reference SysML/UML, SSP/FMI/FMUs, and other external standards/artifacts rather
  than duplicating their full semantic universes.
- **FR-018**: Secrets MUST be indirect references to an external secure mechanism; public resources
  MUST NOT contain credential material or sensitive deployment values.
- **FR-019**: The package MUST include specification documents, schema drafts, YAML examples, ADRs,
  validation evidence, and a separate architecture review.
- **FR-020**: This capability MUST NOT implement a loader/parser library, runtime plan compiler,
  orchestrator, adapter, component catalog, executable blueprint, or production interface.

### Key Entities

XDL Resource; Resource Metadata; Resource Reference; Element Reference; System; Component;
Deployment; Scenario; Profile; Extension Payload; Provenance; Traceability Reference; Artifact
Reference; Execution Target; Resource Claim; Lifecycle Contract; Validation Diagnostic; Normalized
Semantic Resource.

## Success Criteria

- **SC-001**: All five resource kinds have Draft 2020-12 schemas, examples, and normative semantic
  definitions.
- **SC-002**: Every schema and JSON fixture parses successfully; every YAML example parses to a mapping
  with the expected API version and kind.
- **SC-003**: Positive examples pass the local structural/semantic validator and negative fixtures
  exercise at least unknown field, duplicate identifier, unresolved reference, undeclared extension,
  realization leakage, and incomplete readiness cases.
- **SC-004**: Requirements FR-001–FR-020 have task and artifact coverage with no unresolved template
  markers.
- **SC-005**: ADR-0009 through ADR-0012 record resource packaging, identity/versioning, serialization/
  schema, and extension/standards decisions.
- **SC-006**: A separate architecture review reports no unresolved BLOCKER or MAJOR constitutional
  conflict before M2 is presented for human approval.
- **SC-007**: No legacy repository, production process, runtime interface, or companion repository is
  modified by M2.

## Assumptions and clarification decisions

- JSON is the schema data model; YAML 1.2.2 is a human-facing serialization that must compose to JSON-
  compatible mappings, sequences, and scalar values. Duplicate keys and non-string mapping keys are
  invalid for XDL.
- \`metadata.namespace\` and \`metadata.name\` form resource scope. A canonical display identity is
  \`xdl://<namespace>/<kind>/<name>\`; element references add \`#<element-id>\`.
- The schemas are normative structural drafts. Cross-resource resolution, graph compatibility,
  readiness, and policy rules are normative prose plus validation fixtures until a later loader/
  validator implementation capability.
- Separate resources are used instead of one monolithic document. A later Bundle/import mechanism is
  deferred until real composition needs are validated.
- Examples are illustrative XDL resources, not executable blueprints or compatibility descriptors.

## X-Verse capability obligations

**Compatibility impact**: None on legacy production. XDL v1alpha1 is new and no existing asset is
declared compatible.

**Failure semantics**: Parsing, structural, reference, semantic, binding, and policy failures produce
diagnostics and prevent normalization/readiness at their respective gate. No automatic coercion,
unknown-field preservation, secret fallback, or implicit provider choice is allowed.

**Observable outcomes**: Versioned documents, schema identifiers, examples, validation output,
negative fixtures, traceability, ADRs, and architecture findings.

**Maturity**: Proposed XDL v1alpha1 specification/schema draft. It is not a loader, runtime,
compatibility guarantee, or demonstrated deployment.

**Runtime tests**: Not applicable. M2 does not execute workloads or provide runtime code.
