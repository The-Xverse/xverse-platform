# Feature Specification: XDL loader, validator, and normalizer

**Feature Branch**: `main` (existing branch; no branch creation required)

**Created**: 2026-09-20

**Status**: Implemented and approved on 2026-09-20

**Input**: Implement the approved XDL v1alpha1 document contract as a safe, deterministic loader,
validation pipeline, normalized semantic representation, and local command-line interface. Do not
implement runtime planning, orchestration, adapters, catalogs, registries, or legacy execution.

## User Scenarios & Testing

### User Story 1 - Load and validate an XDL resource set (Priority: P1)

As an XDL author, I can submit YAML and JSON resources together and receive a definitive validation
result without the tool contacting a registry or silently changing my data.

**Why this priority**: Every later X-Verse capability depends on trustworthy XDL input.

**Independent Test**: Load the five approved examples as one resource set and confirm that parsing,
schema, reference, and semantic gates succeed; mutate each gate independently and confirm failure.

**Acceptance Scenarios**:

1. **Given** valid YAML and JSON resources, **When** they are loaded together, **Then** each resource
   is validated against the exact v1alpha1 kind schema and all supplied references resolve.
2. **Given** duplicate keys, non-JSON values, unknown fields, or an unsupported API version, **When**
   the set is loaded, **Then** validation fails at the earliest applicable gate without normalization.
3. **Given** a reference not present in the supplied set, **When** validation runs, **Then** it reports
   an unresolved-reference diagnostic and performs no network lookup.

---

### User Story 2 - Diagnose semantic and readiness problems (Priority: P1)

As an integrator, I receive stable, machine-readable diagnostics for resource identity, relationships,
extensions, logical/realization separation, and statically assessable readiness obligations.

**Why this priority**: A schema-valid document may still be ambiguous, unsafe, or impossible to bind.

**Independent Test**: Exercise duplicate identity, ambiguous element identity, incompatible flow,
undeclared Profile, unresolved binding, and physical-asset cases and assert stable codes and pointers.

**Acceptance Scenarios**:

1. **Given** duplicate resource or resource-wide element identity, **When** validation runs, **Then**
   every collision is reported and the affected resource cannot normalize.
2. **Given** a namespaced extension, **When** its compatible Profile and explicitly supplied schema
   are available, **Then** the payload is validated; otherwise validation fails closed.
3. **Given** a Deployment with unresolved artifacts, resources, targets, clocks, or a physical asset,
   **When** readiness validation runs, **Then** it reports NotReady reasons without contacting a target.

---

### User Story 3 - Obtain deterministic normalized XDL (Priority: P1)

As a future compiler author, I can consume an immutable normalized semantic representation whose
identity, indexed elements, resolved references, extensions, content, and source map are independent
of YAML presentation.

**Why this priority**: The normalized representation is the handoff from authored data to future
planning capabilities.

**Independent Test**: Normalize semantically equivalent YAML and JSON resources and compare their
canonical JSON output while confirming that comments, key order, aliases, and quote style do not
change semantic content.

**Acceptance Scenarios**:

1. **Given** a resource set that passes gates 1–4, **When** normalization is requested, **Then** each
   resource has derived identity, collection indexes, resolved references, paired Profiles, content,
   provenance, and diagnostic source locations.
2. **Given** any gate 1–4 error, **When** normalization is requested, **Then** no partial normalized
   model is returned.
3. **Given** equivalent YAML and JSON, **When** canonical JSON is produced, **Then** ordering and
   presentation differences do not affect the output.

---

### User Story 4 - Use validation in local automation (Priority: P2)

As a developer or CI job, I can run validation and normalization locally, select text or JSON
diagnostics, and rely on deterministic output and exit status.

**Why this priority**: A stable local interface makes the implementation reviewable and reusable
without creating a network service or production API.

**Independent Test**: Invoke validation and normalization from the command line for valid and invalid
sets, compare repeat output byte-for-byte, and assert the documented status codes.

**Acceptance Scenarios**:

1. **Given** valid resources, **When** validation is invoked, **Then** it exits successfully and can
   emit a deterministic JSON report.
2. **Given** invalid resources, **When** validation is invoked, **Then** it exits unsuccessfully and
   reports every deterministic diagnostic available at the reached gates.
3. **Given** valid resources, **When** normalization is invoked, **Then** canonical JSON is written to
   standard output or an explicitly selected file without changing the inputs.

### Edge Cases

- Empty files, multiple YAML documents, byte-order marks, invalid UTF-8, JSON duplicate keys, and
  YAML tags or cyclic aliases.
- Inputs that exceed configured byte, nesting, node, or resource-count limits.
- The same resource identity supplied twice from different files.
- The same element ID used in different collections of one resource.
- Reference chains that are cyclic, missing, or point to the wrong resource kind.
- A Profile namespace claimed by multiple resources or a Profile schema with a mismatched `$id`.
- Schema-valid values such as non-finite numbers or timestamp objects that are not JSON-compatible.
- A diagnostic location that is available for YAML but only a JSON Pointer is derivable for JSON.
- A valid resource set whose Deployment cannot be declared statically ready without live evidence.

## Requirements

### Functional Requirements

- **FR-001**: The loader MUST accept UTF-8 YAML 1.2 and JSON files containing exactly one XDL resource.
- **FR-002**: Parsing MUST reject empty input, multiple documents, duplicate mapping keys, non-string
  keys, custom values outside the JSON data model, non-finite numbers, and cyclic structures.
- **FR-003**: Loading MUST enforce configurable upper bounds for bytes, nesting depth, traversed
  nodes, and resources before unbounded work occurs.
- **FR-004**: The implementation MUST validate the exact `xverse.io/xdl/v1alpha1` kind schema using a
  standards-conforming Draft 2020-12 implementation and format checking.
- **FR-005**: Schema loading MUST use packaged local schemas and MUST NOT retrieve schema references
  over a network.
- **FR-006**: A validation run MUST treat the explicitly supplied resources as its complete resource
  catalog; current-directory, namespace, registry, and network fallback are prohibited.
- **FR-007**: Resource identity MUST be unique across the supplied set.
- **FR-008**: Element IDs MUST be unique across their complete owning resource because ElementRef
  identifies an element without naming its collection.
- **FR-009**: ResourceRef and ElementRef targets MUST resolve exactly by API version, kind, namespace,
  name, and element ID where present.
- **FR-010**: The semantic gate MUST enforce kind-specific ownership, interface/endpoint/flow,
  logical/realization, unit, time-domain, Scenario, Deployment, and Profile invariants from M2.
- **FR-011**: Extension payloads MUST resolve to exactly one compatible Profile and validate against
  an explicitly supplied local Profile schema whose `$id` matches the Profile `schemaRef`.
- **FR-012**: Missing, incompatible, duplicate, or invalid Profile/schema bindings MUST fail closed.
- **FR-013**: Binding/readiness validation MUST evaluate static completeness only and MUST NOT contact
  execution targets, retrieve artifacts, allocate resources, or claim live readiness.
- **FR-014**: Diagnostics MUST contain a stable code, validation gate, severity, resource identity
  when derivable, RFC 6901 pointer, source file/line/column when derivable, message, and correction.
- **FR-015**: Diagnostics MUST have deterministic ordering independent of input argument ordering.
- **FR-016**: Normalization MUST occur only when parse, schema, reference, and semantic gates all pass.
- **FR-017**: A normalized resource MUST expose canonical identity, resource revision, provenance,
  labels, resource-wide element indexes grouped by collection, resolved references, validated
  extensions paired with Profile identity, kind content, and source map.
- **FR-018**: Normalized semantic equality and canonical JSON MUST ignore YAML comments, mapping order,
  anchors, aliases, quote style, and whitespace.
- **FR-019**: Public library results MUST be immutable from the consumer's perspective.
- **FR-020**: The local command interface MUST provide `validate` and `normalize`, deterministic text
  and JSON reporting, documented status codes, explicit Profile-schema inputs, and no telemetry.
- **FR-021**: Inputs MUST never be modified, and all output files MUST be written only when explicitly
  requested.
- **FR-022**: The package MUST expose its version and supported XDL API versions.
- **FR-023**: Tests MUST cover every validation gate, all five resource kinds, YAML/JSON equivalence,
  deterministic diagnostics, limits, CLI behavior, and the approved example graph.
- **FR-024**: The implementation MUST remain domain-neutral and MUST NOT contain automotive concepts,
  provider assumptions, runtime planning, orchestration, adapters, catalogs, or legacy execution.
- **FR-025**: The capability MUST include user documentation, compatibility/failure semantics,
  validation evidence, dependency provenance, and a separate architecture review.

### Key Entities

- **Source Document**: Immutable bytes, source name, format, parsed value, and pointer locations.
- **Resource Identity**: API version, kind, namespace, and name; renders a canonical XDL URI.
- **Element Identity**: Resource identity plus a resource-wide element ID.
- **Resource Catalog**: Explicit closed set used for duplicate and reference resolution.
- **Profile Schema Catalog**: Explicit local schemas keyed by canonical `$id`.
- **Diagnostic**: Stable validation result with gate, severity, identity, location, explanation, and correction.
- **Resolved Reference**: Authored ResourceRef/ElementRef plus exact target identity.
- **Normalized Resource**: Immutable, presentation-independent semantic handoff.
- **Validation Result**: Ordered diagnostics, normalized resources when eligible, and static readiness.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All five approved example resources load, fully validate with the supplied example
  Profile schema, and normalize in one command.
- **SC-002**: At least 25 negative tests cover all six gates plus parser limits and every test reports
  the expected stable diagnostic code and non-success status.
- **SC-003**: Equivalent YAML and JSON fixtures produce byte-identical canonical semantic JSON after
  source-map exclusion.
- **SC-004**: Repeating validation with reversed input order produces byte-identical JSON diagnostics.
- **SC-005**: A local set of 100 small resources validates and normalizes within two seconds and
  128 MiB peak resident memory in the reference environment; results record the environment.
- **SC-006**: Public interfaces, CLI help, examples, and diagnostics contain no unresolved template
  markers, secret values, private infrastructure, or unsupported runtime claims.
- **SC-007**: The separate architecture review reports no unresolved BLOCKER or MAJOR constitutional
  conflict before human acceptance.
- **SC-008**: No legacy or companion repository, production process, network service, or runtime
  interface is changed or executed.

## Assumptions

- One file contains one XDL resource; Bundle/import and multi-document streams remain deferred.
- Callers supply the complete resource set and any Profile schemas explicitly.
- YAML presentation locations may be more precise than JSON locations; JSON Pointer remains mandatory.
- Static Deployment readiness means declared prerequisites are complete, not that a live target is ready.
- The package initially targets supported CPython versions on Linux, macOS, and Windows without a daemon.

## X-Verse capability obligations

**Compatibility impact**: New local library/CLI for XDL v1alpha1 only. It changes no legacy contract
and does not assert compatibility with a legacy component. Resource-wide element uniqueness tightens
an ambiguous M2 prose rule while preserving the approved reference shape and current examples.

**Failure semantics**: Fail closed at the earliest gate that makes later interpretation unsafe;
collect independent diagnostics within a reached gate; never repair input, fetch missing data, infer
defaults, or return partial normalization.

**Observable outcomes**: Deterministic diagnostics, exit status, normalized canonical JSON, package
version, supported API version, test evidence, and architecture findings.

**Maturity**: Prototype implementation of the approved alpha language contract. Passing validation
demonstrates document conformance and selected static readiness only, not runtime interoperability.

**Exclusions**: Runtime plans, execution, orchestration, live readiness probes, artifact retrieval,
registry discovery, schema networking, adapters, catalogs, blueprints, and production interfaces.
