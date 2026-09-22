# Feature Specification: X-COM core communication and validation

**Feature Branch**: `main`

**Created**: 2026-09-21

**Status**: Design accepted and bounded prototype implementation authorized on 2026-09-21

**Input**: Implement the main X-Verse platform before legacy integration. Define X-COM as a
domain-neutral, performance-oriented communication core with common external-tool stimulation and
observation interfaces for node and system validation, plus pluggable monitoring for later dashboards.
Account explicitly for the applicable requirements in the supplied REF-002 X-Verse SADS v0.1.

## User Scenarios & Testing

### User Story 1 - Communicate through stable logical interfaces (Priority: P1)

As a component developer, I bind a declared logical interface to an X-COM provider and exchange
signals, messages, events, and service requests/responses without embedding a protocol in my component.

**Why this priority**: Normal communication is the foundation for every validation and adapter flow.

**Independent Test**: Two owned loopback nodes exchange each interaction kind through a declared
interface; identities, ordering, outcomes, and failure codes are deterministic.

**Acceptance Scenarios**:

1. **Given** a valid XDL deployment and compatible provider, **When** endpoints bind and communicate,
   **Then** X-COM preserves logical interface, schema, origin, correlation, and delivery outcome.
2. **Given** an undeclared or incompatible binding, **When** activation is requested, **Then** X-COM
   rejects it before traffic flows and reports stable diagnostics.
3. **Given** capacity or provider failure, **When** traffic cannot be accepted or delivered, **Then**
   X-COM applies the declared policy and exposes the result without unbounded blocking or retry.

---

### User Story 2 - Observe communication with external tools (Priority: P1)

As a validation or operations engineer, I attach an approved observer to selected X-COM flows so a
sniffer, recorder, Argus, dashboard adapter, or analysis tool can monitor system behavior.

**Why this priority**: Validation requires evidence of what crossed the communication boundary and
whether observation affected the test.

**Independent Test**: A synthetic observer filters loopback traffic, receives normalized metadata and
permitted payload views, and can be slowed or disconnected without silently changing normal delivery.

**Acceptance Scenarios**:

1. **Given** a metadata-only observation policy, **When** matching traffic flows, **Then** the observer
   receives identity, timing, origin, correlation, route, size, and outcome without payload content.
2. **Given** an explicitly permitted payload policy, **When** matching traffic flows, **Then** only the
   allowed payload view is exposed and its redaction/truncation state is recorded.
3. **Given** a slow or failed observer, **When** its bounded capacity is exhausted, **Then** the declared
   drop, coalesce, or lossless-test behavior occurs and counters make the effect visible.

---

### User Story 3 - Stimulate nodes and services safely (Priority: P1)

As a test engineer, I open a bounded validation session through an external tool and inject a declared
signal/message, invoke a service, or emulate an allowed service endpoint to validate node and system
behavior.

**Why this priority**: Controlled stimulation is required for diagnostic, negative, SIL/HIL, and
system-validation scenarios and must not become an ungoverned alternate data path.

**Independent Test**: A synthetic tool uses an exact validation permit against loopback nodes; allowed
actions succeed with synthetic provenance, while undeclared, expired, excessive, or looping actions
fail before entering the normal data path.

**Acceptance Scenarios**:

1. **Given** an armed session bound to exact XDL identities and actions, **When** the tool stimulates an
   allowed interface, **Then** X-COM validates the item, labels its origin, routes it, and journals the
   request and outcome.
2. **Given** no permit or a mismatched schema, target, action, environment, or time window, **When** a
   tool requests stimulation, **Then** X-COM rejects it with no emitted traffic.
3. **Given** a request that would create a prohibited feedback loop or ambiguous service provider,
   **When** it is evaluated, **Then** X-COM fails closed and reports the causal chain.

---

### User Story 4 - Connect future providers and analysis tools (Priority: P2)

As a platform integrator, I add a transport provider or observation/stimulation tool adapter against a
versioned conformance boundary without changing X-COM core semantics.

**Why this priority**: Native transports, Argus, diagnostic tools, and later legacy adapters must
coexist without coupling the core to one protocol or product.

**Independent Test**: A second synthetic provider and tool adapter pass the same contract suite and are
rejected when they misreport capability, violate ownership, or emit an unsupported contract version.

**Acceptance Scenarios**:

1. **Given** a compatible provider, **When** it is registered explicitly, **Then** its capabilities and
   limits are discoverable through the stable boundary.
2. **Given** an incompatible version or capability set, **When** registration is attempted, **Then** it
   is rejected before endpoint activation.
3. **Given** an observer or stimulation adapter failure, **When** X-COM isolates it, **Then** unrelated
   routes remain bounded and their state stays observable.

### Edge Cases

- Clock domains differ, timestamps regress, or no trustworthy source timestamp exists.
- Signal updates race with a service response or multiple observers see different filtered views.
- A schema changes while endpoints, observers, or a validation session are active.
- Backpressure exhausts a route, observer queue, or stimulation quota.
- A tool disconnects after intent is journaled but before the outcome is observed.
- A provider restarts with stale endpoint handles or duplicate sequence identifiers.
- Payload inspection is prohibited even though metadata observation is allowed.
- An injected item returns through a bridge and would be reinjected indefinitely.
- A service emulator conflicts with a real provider or outlives its validation session.

## Requirements

### Functional Requirements

- **FR-001**: X-COM MUST remain domain-neutral; automotive diagnostics and bus semantics MUST be
  supplied through profiles, providers, or tool adapters.
- **FR-002**: X-COM MUST derive logical interfaces, endpoints, schemas, deployments, scenarios, and
  policy references from the exact normalized XDL graph; it MUST NOT introduce a competing topology or
  configuration language.
- **FR-003**: X-COM MUST distinguish logical interface identity from provider, protocol, address, and
  physical realization.
- **FR-004**: X-COM MUST support typed signal/state updates, messages/events, and service
  request/response interactions with explicit semantic differences.
- **FR-005**: Every communication item MUST identify contract version, logical interface and endpoint,
  schema/version, origin, timestamp and clock domain, correlation/causation, and route/provider.
- **FR-006**: Binding and activation MUST fail before traffic flows when identity, direction, schema,
  interaction kind, provider capability, or declared policy is incompatible.
- **FR-007**: Queueing, ordering, reliability, deadline, overflow, retry, and backpressure behavior MUST
  be explicit, bounded, and restricted to supported provider capabilities.
- **FR-008**: X-COM MUST NOT silently upgrade delivery guarantees or claim timing/network fidelity that
  the selected provider and environment have not demonstrated.
- **FR-009**: Provider registration and endpoint ownership MUST be explicit; only exact issued handles
  may mutate, close, or replace active resources.
- **FR-010**: Provider and endpoint lifecycle operations MUST be idempotent or reject unsafe repeats,
  and restart reconciliation MUST not infer ownership from names or addresses.
- **FR-011**: X-COM MUST expose a versioned, filterable observation boundary at declared logical route
  points without requiring a provider-specific sniffer interface.
- **FR-012**: Observation MUST support metadata-only operation by default; payload views require an
  explicit allow policy and MUST report redaction, truncation, decoding, and schema status.
- **FR-013**: Observation queues MUST be bounded. Slow observers MUST use a declared drop, coalesce, or
  lossless-validation policy with counters and an observable effect on test validity.
- **FR-014**: Observer attachment, failure, and detachment MUST NOT silently change normal delivery,
  routing, ordering, or timing semantics.
- **FR-015**: X-COM MUST expose a common stimulation boundary for injecting declared signals/messages,
  invoking services, and emulating explicitly allowed service endpoints.
- **FR-016**: Stimulation MUST be disabled by default and require a single-session permit bound to the
  exact XDL graph, scenario, deployment/environment, interfaces, actions, validity interval, and
  resource/rate limits.
- **FR-017**: Every injected item MUST remain visibly classified as synthetic or tool-originated and
  preserve tool, session, request, correlation, and causal identity through routing and observation.
- **FR-018**: X-COM MUST validate an injected item against its declared interaction, direction, schema,
  target, session scope, and quota before it can enter a route.
- **FR-019**: X-COM MUST detect or bound prohibited reinjection loops and MUST reject ambiguous or
  conflicting service emulation.
- **FR-020**: Scheduled stimulation MUST declare a clock domain, ordering rule, late-item policy, and
  reproducibility limits; immediate injection MUST be labeled as such.
- **FR-021**: Stimulation intent MUST be durably journaled before emission and followed by an outcome;
  an incomplete outcome MUST remain explicit and MUST NOT be converted into success.
- **FR-022**: External tools MUST use versioned provider-neutral contracts. No dashboard, diagnostic
  product, test language, or transport protocol may become a core primitive.
- **FR-023**: X-COM MUST publish normalized observation records suitable for Argus and third-party
  consumers; X-COM MUST NOT own dashboard rendering, long-term storage, or query presentation.
- **FR-024**: Fault campaigns and mutation policy belong to the Faults subsystem; X-COM MAY expose
  controlled hooks but MUST NOT embed domain-specific fault semantics.
- **FR-025**: Diagnostic codes MUST be stable and include severity, phase, affected identity, reason,
  correction, and deterministic ordering.
- **FR-026**: Normal data-plane use MUST not require network discovery, ambient configuration, secrets,
  or access to a legacy repository.
- **FR-027**: Public evidence and logs MUST exclude credentials, private addresses, unrestricted
  payloads, proprietary source excerpts, and sensitive deployment values.
- **FR-028**: The initial proof MUST use owned loopback providers and synthetic tools only; it MUST NOT
  execute or adapt a legacy component or contact an external network peer.
- **FR-029**: The implementation MUST provide useful Doxygen documentation for every public C/C++
  interface and changed unit, including ownership, thread-safety, failure, and lifetime contracts.
- **FR-030**: The capability MUST include requirements-to-design-to-code-to-test traceability,
  unit/contract/integration/performance evidence, and a separate architecture review before acceptance.
- **FR-031**: X-COM-specific interaction, provider, observation, and stimulation policy MUST use a
  versioned `io.xverse.xcom` Profile payload on existing XDL extension points and MUST be compiled into
  the digest-bound activation plan.
- **FR-032**: The initial proof MUST provide one local-only, out-of-process tool gateway and a synthetic
  client in a separate process. It MUST expose no TCP listener, use host-protected local IPC, enforce
  request/stream deadlines and bounds, and still require the exact validation permit.
- **FR-033**: Scheduled stimulation MUST use an explicit time-authority interface. When source and
  execution clock domains cannot be mapped within a declared tolerance, the request MUST fail or be
  marked invalid before emission according to the declared policy.
- **FR-034**: Service emulation MUST atomically acquire an exclusive lease bound to the exact validation
  session and endpoint generation; conflicts, expiry, revocation, and disconnect MUST release or
  quarantine the lease without leaving ambiguous ownership.
- **FR-035**: Capability 007 MUST account for all REF-002 communication requirements
  XVE-SYS-0139–0158 and every identified shared requirement through an explicit disposition and owning
  capability; a deferred or allocated target MUST NOT be reported as implemented.

### Key Entities

- **Communication Contract**: Versioned logical interaction and schema declaration derived from XDL.
- **Endpoint**: Owned producer, consumer, client, or service endpoint bound to one contract.
- **Route**: Resolved connection between endpoints through one explicitly selected provider.
- **Communication Item**: Signal update, message/event, request, response, or lifecycle diagnostic.
- **Provider**: Transport realization with declared capabilities, limits, and issued resource handles.
- **Observation Tap**: Filtered logical route point with payload policy and bounded delivery behavior.
- **Observation Record**: Normalized metadata and optional controlled payload view for external tools.
- **Validation Session**: Bounded, explicitly armed context authorizing exact stimulation actions.
- **Stimulation Request**: Tool-originated signal/message/service action with schedule and provenance.
- **Validation Permit**: Single-session authority bound to exact declarations, actions, limits, and time.
- **Tool Gateway**: Local-only out-of-process adapter that maps versioned tool RPCs/streams to the same
  validation and observation contracts enforced in process.
- **Time Authority**: Explicit source of clock-domain identity, current time, mapping, and tolerance.
- **Service-emulation Lease**: Exclusive session-owned right to emulate one endpoint generation.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Owned loopback tests exchange all four interaction families and reject at least twenty
  malformed, incompatible, over-capacity, or unauthorized cases with stable diagnostics.
- **SC-002**: Equivalent normalized XDL inputs produce byte-identical binding plans and diagnostic
  ordering regardless of source document order.
- **SC-003**: Metadata-only observation exposes zero payload bytes and 100% of emitted observation
  records identify origin, logical contract, clock domain, route, and outcome.
- **SC-004**: Under saturation tests, every queue remains within its configured bound and every dropped
  or coalesced item is reflected in counters and validation status.
- **SC-005**: Removing, blocking, or crashing a best-effort observer does not change the normal-route
  item count, order, or delivery outcomes in the owned deterministic fixture.
- **SC-006**: All accepted stimulation items carry synthetic provenance; all missing, expired,
  mismatched, looping, conflicting, or over-quota requests emit zero normal-route items.
- **SC-007**: The initial implementation demonstrates at least one signal injection, message injection,
  service invocation, and bounded service emulation using only owned fixtures.
- **SC-008**: With taps disabled, the benchmark records no more than 2% median throughput regression
  and no more than 2% median latency regression against the same owned loopback baseline; results must
  include uncertainty and environment data and are not production claims.
- **SC-009**: Every requirement traces to design units and automated evidence, and public interfaces
  generate warning-free Doxygen output.
- **SC-010**: A separate review has no unresolved BLOCKER or MAJOR finding before human acceptance.
- **SC-011**: A synthetic client in a separate process observes traffic and completes every allowed
  stimulation action through a host-protected local endpoint, while tests prove no TCP listener exists
  and invalid/expired sessions emit zero items.

## Assumptions

- The first implementation includes a local-only out-of-process gateway for owned synthetic tools.
  Remote tool access, network listeners, and distributed authorization remain later capabilities.
- Existing normalized XDL v1alpha1 identity and profile-extension rules remain authoritative.
- The first validation permit uses an explicit local host-controlled record; remote identity,
  authentication, and policy distribution are separate security capabilities.
- Argus will consume the observation contract later. The initial proof uses a synthetic sink and
  does not implement a dashboard or telemetry database.
- Lossless observation is permitted only as an explicitly declared validation mode whose backpressure
  is part of the experiment semantics.

## X-Verse capability obligations

**Compatibility impact**: Introduces a future platform communication/provider/tool boundary. It changes
no legacy protocol, API, topic, artifact, deployment, or repository and implements no legacy adapter.

**Failure semantics**: Configuration and authorization errors fail before activation/emission. Runtime
capacity, provider, observer, and tool failures follow bounded declared policies and remain observable.
Unknown delivery or stimulation outcome is never reported as success.

**Observable outcomes**: Binding plans, endpoint and route state, normalized tap records, stimulation
intent/outcome records, queue/capacity counters, diagnostics, benchmark evidence, and review reports.

**Maturity**: Specification/design target. An accepted first implementation would remain a prototype
validated only with owned loopback providers and synthetic tools.

**Evidence and documentation**: Spec Kit artifacts, ADR-0018/ADR-0019, public API and Doxygen
documentation, REF-002 requirement traceability, automated checks, bounded benchmark evidence, and
separate review.

**Exclusions**: Legacy adapters or execution, physical buses, production deployment, distributed
discovery, remote authorization or TCP tool access, dashboard UI, telemetry persistence, diagnostic
databases, general record/replay, network-fidelity simulation, fault-campaign authoring, and
OpenTelemetry, ASAM XIL, CANoe, transport-protocol, or legacy compatibility/parity claims.
