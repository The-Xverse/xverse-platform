# Feature Specification: Component catalog and compatibility runtime

**Feature Branch**: `main` (existing branch; no branch creation required)

**Created**: 2026-09-20

**Status**: Prototype platform catalog/planner and isolated fixture implemented; one exact legacy
candidate graph is validated and deliberately blocked; completed selection, provider implementation,
execution, compatibility, and parity remain unapproved.

**Input**: Define the first M3 capability that describes legacy production components externally,
resolves them through a local catalog, and can later start, observe, and stop one selected component
without modifying its repository. The design must preserve XDL centrality, production immutability,
explicit lifecycle ownership, public-safe evidence, and the unresolved M0 runtime constraints.

## User Scenarios & Testing

### User Story 1 - Register an external component boundary (Priority: P1)

As a platform integrator, I can describe a revision-pinned legacy boundary through existing XDL
Component, System, Deployment, and Profile resources and obtain a derived catalog entry without
copying its source, changing its repository, or claiming that it has run.

**Why this priority**: A catalog must make the compatibility boundary explicit before a runtime can
act on it safely.

**Independent Test**: A valid local XDL graph resolves one compatibility-enabled Deployment binding
to its System component instance, Component identity, Profile payload, and pinned artifact revision;
malformed, duplicate, incomplete, unpinned, or unsupported graphs produce deterministic diagnostics
and no executable plan.

**Acceptance Scenarios**:

1. **Given** a complete local XDL resource graph, **When** the catalog is derived, **Then** each entry
   records the Deployment/binding identity, Component identity, provenance, declared interfaces,
   lifecycle contract, maturity, and compatibility limits without accessing a legacy checkout.
2. **Given** a duplicate Deployment/binding identity, mutable revision, missing artifact provenance,
   or compatibility payload outside the approved runtime Profile, **When** the graph is validated,
   **Then** it fails closed with a stable diagnostic and no selected component.
3. **Given** a legacy boundary with restricted detail, **When** it is documented, **Then** its public
   catalog projection exposes only public-safe identifiers and marks withheld contract data explicitly.

---

### User Story 2 - Produce a safe lifecycle plan (Priority: P1)

As a compatibility operator, I can resolve a selected derived catalog entry and deployment overlay into a
deterministic lifecycle plan that states preparation, start, observation, stop, ownership, timeout,
and failure behavior before anything is launched.

**Why this priority**: M0 found that legacy launch scripts use broad cleanup and fixed sleeps, which
cannot become implicit vNext behavior.

**Independent Test**: A complete catalog entry produces an ordered plan; missing readiness, unowned
cleanup, ambiguous dependency order, live-secret requirement, or unsupported operating mode blocks
planning. Absence of an execution permit does not block planning but marks the plan ineligible to run.

**Acceptance Scenarios**:

1. **Given** a selected component with explicit prerequisites and lifecycle conditions, **When** a
   plan is resolved, **Then** it contains only actions owned by the compatibility runtime and declares
   every external prerequisite as evidence or an unmet condition.
2. **Given** a catalog entry that requires broad process cleanup, ambient discovery, or an unspecified
   readiness signal, **When** planning runs, **Then** it rejects the request instead of inheriting the
   legacy behavior.
3. **Given** a physical, virtual, simulated, or hybrid realization, **When** it is planned, **Then**
   its realization class and associated fidelity limits remain explicit and are not inferred.

---

### User Story 3 - Execute one authorized compatibility boundary (Priority: P2)

As an authorized operator, I can later start, observe, and stop one explicitly selected legacy
component in an isolated environment while preserving its repository and collecting bounded evidence.

**Why this priority**: This is M3's compatibility proof, but it must wait for a selected component,
artifact, environment, and separate execution authorization.

**Independent Test**: In a controlled non-legacy fixture and, only after separate authorization, a
selected legacy component, the runtime proves it starts only declared children, observes declared
signals, applies its own stop policy, and emits an evidence record for each state transition.

**Acceptance Scenarios**:

1. **Given** a validated plan and matching unexpired single-use execution permit, **When** the runtime starts a
   component, **Then** it launches only the declared command or provider action and records the exact
   catalog/XDL-graph/artifact/environment revision used.
2. **Given** a readiness failure, process exit, timeout, or stop failure, **When** it is observed,
   **Then** the runtime emits a classified result, stops only resources it owns, and does not execute
   legacy cleanup commands by inference.
3. **Given** a completed run, **When** evidence is inspected, **Then** it distinguishes declared,
   observed, unavailable, and withheld information without asserting application-level parity.

### Edge Cases

- Multiple derived catalog entries claim the same Deployment/binding identity; multiple entries may
  intentionally share one digest-identical artifact.
- An XDL binding uses a mutable tag, branch, unqualified command, ambient working directory, raw secret,
  or secret dependency that M3 cannot resolve.
- The requested component is documented but lacks a verified startup, readiness, stop, or interface
  contract.
- A plan would target a physical asset, shared host resource, or existing process not owned by the
  runtime.
- A component exits before readiness, remains running after stop timeout, or emits no observation.
- Start or stop is repeated, two controllers act concurrently, or the controller restarts with an
  unreconciled ownership handle.
- Durable evidence accepts an intent record but rejects the corresponding outcome record.
- An execution permit is missing, expired, already consumed, or bound to a different plan/environment.
- A derived catalog entry conflicts with the selected System, Deployment, Profile, time domain, interface, or
  realization class.
- Revision-pinned launcher evidence and a supplemental architecture reference prescribe different
  dependency/startup order for the same candidate boundary.
- Public evidence would expose private infrastructure, credentials, sensitive paths, or proprietary
  payload detail.
- A selected artifact embeds an environment-specific endpoint, native-memory payload encoding,
  payload-bearing logs, detached work, or test assumptions that are absent from its external
  configuration and lifecycle declaration.

## Requirements

### Functional Requirements

- **FR-001**: The capability MUST treat XDL as the canonical identity and relationship language;
  catalog data MUST reference an exact XDL Component and MUST NOT define a parallel system language.
- **FR-002**: A catalog entry MUST be derived, never independently authored, from a normalized XDL
  graph containing an exact Component, its System component instance, a Deployment binding, artifacts,
  and the `io.xverse.runtime.compatibility` Profile payload on that binding.
- **FR-003**: Catalog loading MUST use an explicit local input set and MUST NOT scan repositories,
  current directories, registries, or networks for a component.
- **FR-004**: Each derived catalog identity, formed from exact Deployment identity plus binding ID,
  MUST be unique. Multiple entries MAY reference the same digest-identical artifact.
- **FR-005**: Mutable branches, tags, image labels, path-only artifacts, and unqualified commands MUST
  be rejected where they would prevent reproducible selection.
- **FR-006**: A derived catalog entry and its public projection MUST distinguish observed facts, operator declarations, architectural
  targets, unknowns, withheld details, and evidence references.
- **FR-007**: The capability MUST model prepare, start, observe, stop, cleanup, timeout, failure, and
  ownership semantics explicitly; fixed sleeps alone cannot satisfy readiness.
- **FR-008**: A compatibility runtime MUST create actions only for resources it directly owns and MUST
  NOT infer broad cleanup, process-name killing, port cleanup, repository mutation, or deployment
  repair from a legacy script.
- **FR-009**: Planning MUST fail closed when startup prerequisites, readiness evidence, stop behavior,
  interface contract, artifact provenance, execution environment, or ownership are unresolved.
- **FR-010**: A plan MUST preserve the selected System, Deployment, Scenario, Profile, time-domain,
  and realization references when they apply; it MUST NOT infer missing bindings.
- **FR-011**: The capability MUST keep logical component identity separate from process, container,
  emulator, model-unit, remote, and physical realization overlays.
- **FR-012**: Physical and hybrid components MUST require an explicit external asset reference and a
  declared ownership/failure boundary before planning or execution.
- **FR-013**: Catalog derivation and planning MUST require no execution permit and MUST have no side
  effect. A plan without a permit MUST remain inspectable but explicitly ineligible for execution.
- **FR-014**: Execution MUST require an explicit operator request and a matching, unexpired,
  single-use execution permit bound to the exact plan digest, catalog identity, environment identity,
  permitted actions, approval evidence reference, and validity interval. Permit consumption MUST
  activate exactly one execution ID; expiry or consumption MUST prevent a new execution but MUST NOT
  prevent handle-authorized stop/cleanup of a resource already owned by that execution.
- **FR-015**: Observation MUST be limited to declared health, lifecycle, interface, and evidence
  signals; missing observations MUST be reported as unavailable rather than synthesized as success.
- **FR-016**: Stop and cleanup MUST use an exact provider-issued ownership handle and MUST apply only
  to runtime-owned resources; name, port, path, or ambient process discovery MUST NOT establish ownership.
- **FR-017**: Each lifecycle transition MUST produce deterministic, machine-readable evidence with
  catalog identity, XDL graph, artifact, environment, plan, time, outcome, and evidence-limit references.
- **FR-018**: Evidence MUST be public-safe by default and exclude credentials, private addresses,
  sensitive deployment paths, payload contents, and proprietary source excerpts.
- **FR-019**: Diagnostics MUST have stable codes, severity, lifecycle phase, selected identity when
  available, explanation, correction, and deterministic ordering.
- **FR-020**: A successful component lifecycle result MUST mean only that declared runtime conditions
  were observed; it MUST NOT claim application behavior, protocol compatibility, cruise-control
  parity, fidelity, or production readiness.
- **FR-021**: The initial implementation MUST support a controlled fixture before any selected legacy
  component is executed, and it MUST retain the fixture/legacy evidence distinction.
- **FR-022**: Legacy component selection for execution MUST be recorded in a reviewable decision that
  pins the artifact, environment, interfaces, lifecycle contract, owner authorization, and exclusions.
- **FR-023**: Existing M0 findings R01–R05 MUST remain explicit constraints; their existence MUST NOT
  be reclassified as resolved by catalog derivation or fixture success.
- **FR-024**: Component-specific protocol terms belong in compatibility adapters or Profiles; the
  catalog/runtime core MUST remain domain-neutral.
- **FR-025**: The capability MUST include design documentation, compatibility impact, failure
  semantics, observability/evidence contracts, acceptance checks, and a separate architecture review.
- **FR-026**: The compatibility Profile payload MUST occur only on a Deployment binding and MUST NOT
  add runtime or realization data to the logical Component resource.
- **FR-027**: An execution permit is an operational approval record, not an authentication or access-
  control system. M3 MUST rely on host permissions for access control and MUST make this limit explicit.
- **FR-028**: A process action MUST identify an absolute executable, ordered argument vector, explicit
  working directory, allowlisted environment names, and closed inherited handles; implicit shell
  expansion and ambient environment inheritance are prohibited.
- **FR-029**: Start and stop MUST be idempotent per execution ID; concurrent mutation of one catalog
  entry/environment MUST be rejected or serialized without launching duplicate resources.
- **FR-030**: After controller interruption, the runtime MUST enter reconciliation mode and MUST NOT
  mutate a resource until its persisted ownership handle is revalidated. An unverifiable handle remains
  observed but unowned.
- **FR-031**: A durable intent evidence record MUST succeed before any mutating action. If outcome
  persistence fails, no new start action may occur; observe and owned stop/cleanup remain permitted and
  the run is classified `evidence-incomplete`.
- **FR-032**: M3 MUST NOT resolve or inject secrets. Any component requiring a secret value or secret
  reference is catalog-visible but blocked from planning/execution pending a separately specified
  secret-resolution capability.
- **FR-033**: Provider actions MUST expose the exact selected provider ID/kind pair and return an opaque
  ownership handle bound to the execution ID, plan action, provider ID/kind pair, and concrete resource
  identity; only that validated handle may authorize mutation.
- **FR-034**: Catalog derivation, planning, execution, observation, stop, cleanup, and evidence
  collection MUST NOT modify a legacy source checkout. A provider MUST use only an explicitly selected
  immutable artifact or isolated fixture and MUST NOT run destructive cleanup inside a legacy repository.
- **FR-035**: A structurally valid compatibility binding MAY declare unique stable `XVERSE-PLAN-*`
  blocker codes for unresolved decision evidence. Catalog derivation MUST preserve and deterministically
  order those codes, planning MUST remain inspectable but unplannable, and declared blockers MUST NOT
  waive XDL/Profile validation or make a plan execution-eligible.

### Key Entities

- **Catalog Entry**: An immutable derived index entry identified by Deployment identity plus binding ID;
  it links the exact System instance and Component to its runtime Profile payload and realization data.
- **Compatibility Boundary**: The declared adapter/provider responsibility between vNext and an
  unchanged external component.
- **Realization Overlay**: Environment-specific binding data that leaves logical XDL identity intact.
- **Lifecycle Contract**: Declared prerequisites, commands/provider actions, readiness, observation,
  stop, timeout, ownership, and failure semantics.
- **Lifecycle Plan**: Deterministic, side-effect-free resolution output for one selected component.
- **Execution Permit**: Explicit local, single-use operational approval record bound to one plan and
  environment; it is not an identity or access-control system.
- **Owned Resource Handle**: Provider-issued opaque identity that proves which concrete resource a
  lifecycle execution created and may later observe, stop, or clean up.
- **Evidence Journal**: Append-only sequence of durable pre-action intent and post-action outcome records.
- **Lifecycle Evidence Record**: Immutable account of declared and observed state transitions, limits,
  and withheld information.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A catalog validation run accepts at least three public-safe XDL graphs with distinct
  realization classes and rejects at least twelve malformed or unsafe graph cases.
- **SC-002**: Equivalent catalog inputs yield byte-identical lifecycle plans and diagnostics regardless
  of input ordering.
- **SC-003**: Planning a component with any unresolved prerequisite, ownership, readiness, artifact,
  stop, or secret contract returns a blocked plan or no plan with one or more stable diagnostics;
  missing execution permit alone does not prevent plan inspection.
- **SC-004**: A controlled fixture completes prepare/start/observe/stop within its declared timeout and
  produces one evidence record per lifecycle transition.
- **SC-005**: A selected legacy component is not executed until its decision record and explicit
  operator request with a matching execution permit are present; no legacy checkout file changes
  during catalog, planning, or authorized execution verification.
- **SC-006**: Evidence and public documentation contain no secret values, private infrastructure,
  proprietary source excerpts, or unsupported compatibility/parity claims.
- **SC-007**: A separate architecture review has no unresolved BLOCKER or MAJOR finding before M3
  human acceptance.
- **SC-008**: Negative tests prove expired, replayed, mismatched, or missing permits cannot execute a
  plan, while permit-free planning remains deterministic.
- **SC-009**: Repeated/concurrent lifecycle calls, controller interruption, unverifiable handles, and
  evidence-write failure never create a duplicate resource or trigger mutation of an unowned resource.
- **SC-010**: The SD-0001 Component, System, Deployment, and runtime Profile graph validates as one
  exact catalog entry and yields a byte-stable plan whose unresolved evidence is represented by the
  expected declared blockers; it starts no process and grants no execution eligibility.
- **SC-011**: A standalone public validator verifies the locked SD-0001 resource/schema digests,
  exact catalog/provider/artifact/resource identities, plan digest, and blocker set; digest drift or
  path traversal fails before catalog use and never performs a lifecycle action.

## Assumptions

- This M3 step implements the platform catalog/planner, execution/evidence boundary, process isolation,
  and an in-memory fixture. It also represents one nominated legacy candidate as a valid blocked plan;
  it does not complete target selection, execute a legacy component, or create a legacy adapter.
- A later implementation will derive catalog entries from existing normalized XDL resources. Typed
  operational fields live only in the `io.xverse.runtime.compatibility` Profile payload attached to a
  Deployment binding; no separate descriptor document or new XDL kind is introduced.
- The first actual execution proof will use an isolated fixture before a separately approved legacy
  component and environment.
- The M0 source-observed S-CORE launcher and documented PID/Rust path remain alternative evidence;
  neither is selected as the M3 execution target in this specification.
- Exact public-safe fixture actions may be versioned for testing. Protected endpoint data and
  credentials remain outside M3; a binding that needs secret resolution is blocked.

## X-Verse capability obligations

**Compatibility impact**: This defines an external compatibility boundary and lifecycle contract for
future use. It changes no legacy contract, repository, API, topic, artifact, deployment, or behavior.

**Failure semantics**: Catalog and planning errors fail closed with no execution. Runtime failures,
when separately authorized, stop only owned resources, preserve evidence, and report unresolved state
without remediation by inference.

**Observable outcomes**: Catalog diagnostics, resolved plans, lifecycle state/evidence records,
explicit authorization decisions, and public-safe review reports.

**Maturity**: Prototype for derived catalog, deterministic planning, permit/evidence mechanics,
process isolation, and the in-memory fixture. M3 has no selected legacy component, legacy provider,
compatibility proof, application parity, or production-readiness claim.

**Exclusions**: Legacy execution, adapter implementation, protocol conversion, registry discovery,
runtime orchestration of multi-component systems, cruise-control parity, application behavior
verification, secret resolution/injection, authentication/access-control infrastructure, live
production changes, and M4–M7 capabilities.
