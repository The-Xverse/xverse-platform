# SWE.1 Software requirements (EARS)

## XCOM-PROV-001 [ubiquitous]

The X-COM provider composition shall remain domain-neutral and shall register only explicitly supplied source-linked providers without discovery, dynamic loading, protocol addresses, or domain-specific semantics.

Source: specs/007-xcom-core/spec.md FR-001, FR-003, FR-009, and FR-026; provenance: accepted; status: accepted.

Verification intent: Inspect dependencies and exercise explicit registration while scanning for discovery, dynamic loading, protocol, address, and domain-specific behavior.

## XCOM-PROV-002 [event_driven]

When a provider is registered, the X-COM provider composition shall validate and retain its stable identity, contract version, supported interaction kinds, delivery and ordering capabilities, payload and route limits, and finite queue limits within a fixed provider-registry capacity.

Source: specs/007-xcom-core/spec.md FR-006 through FR-009 and contracts/provider.md; provenance: accepted; status: accepted.

Verification intent: Register valid descriptors and reject malformed, duplicate, unsupported-version, zero-bound, and capacity-exhaustion cases without unrelated mutation.

## XCOM-PROV-003 [event_driven]

When route preparation is requested, the X-COM provider composition shall reject provider, contract, interaction, delivery, ordering, payload, queue, endpoint, plan-digest, or lifecycle incompatibility before activating provider resources or emitting traffic.

Source: specs/007-xcom-core/spec.md FR-002, FR-006 through FR-010; provenance: accepted; status: accepted.

Verification intent: Exercise every compatibility boundary with exact current lifecycle handles and prove rejected preparation changes no provider, route, endpoint, or queue state.

## XCOM-PROV-004 [event_driven]

When an explicitly composed provider route is activated, the X-COM provider composition shall bind the provider resource to the exact provider instance, route generation, source and destination endpoint generations, plan digest, and validated provider capabilities.

Source: specs/007-xcom-core/spec.md FR-006, FR-009, and FR-010; data-model.md invariants 1 and 2; provenance: accepted; status: accepted.

Verification intent: Activate only exact current lifecycle resources and reject stale, foreign, closed, failed, mismatched, or recreated handles without partial activation.

## XCOM-PROV-005 [event_driven]

When a communication item is submitted, the X-COM provider composition shall accept it only through an exact active provider-route handle when its contract, interaction kind, logical source endpoint, route, provider, payload size, and lifecycle state match the prepared route.

Source: specs/007-xcom-core/spec.md FR-004 through FR-007 and FR-009; provenance: accepted; status: accepted.

Verification intent: Submit valid items for all four interaction families and reject each identity, contract, kind, payload, handle, and state mismatch with zero delivery.

## XCOM-PROV-006 [state_driven]

While the loopback destination queue is full, the X-COM loopback provider shall reject the submitted item with a stable saturation outcome, preserve every previously accepted item, and allocate no additional queue capacity.

Source: specs/007-xcom-core/spec.md FR-007, FR-008, and SC-001; provenance: accepted; status: accepted.

Verification intent: Fill configured queues, reject overflow, compare retained FIFO contents and capacities, then prove recovery after one receive.

## XCOM-PROV-007 [ubiquitous]

The owned loopback provider shall deliver accepted items deterministically in FIFO submission order per route without strengthening declared delivery, ordering, timing, reliability, or network-fidelity claims.

Source: specs/007-xcom-core/spec.md FR-004, FR-007, FR-008, FR-028, and SC-001; provenance: accepted; status: accepted.

Verification intent: Exchange signal, message, request, and response items across multiple bounded routes and compare item bytes, provenance, order, outcomes, and declared capabilities.

## XCOM-PROV-008 [event_driven]

When a provider route is drained or closed, the X-COM provider composition shall stop accepting new items, expose the exact queued-item disposition, release only resources owned by the exact provider-route handle, and make unsafe repeats or stale handles fail without unrelated mutation.

Source: specs/007-xcom-core/spec.md FR-009 and FR-010; contracts/provider.md; provenance: accepted; status: accepted.

Verification intent: Exercise drain, empty, close, recreation, stale-handle, cross-provider, and interrupted-resource reconciliation scenarios with exact outcomes.

## XCOM-PROV-009 [ubiquitous]

The provider and loopback operations shall use finite preallocated storage, serialize shared mutation, return owned results, invoke no callback while locked, and document caller and provider ownership, lifetime, and thread-safety behavior.

Source: specs/007-xcom-core/spec.md FR-007, FR-009, FR-029; contracts/provider.md; provenance: accepted; status: accepted.

Verification intent: Run concurrent submission and receive tests, storage and allocation checks, public API inspection, strict Doxygen, and ownership/lifetime tests.

## XCOM-PROV-010 [ubiquitous]

The provider-composition slice shall perform no filesystem, environment, process, socket, network, secret, legacy-repository, XDL-compilation, observation, stimulation, gateway, dashboard, Maestro, Argus, or Faults access and shall add no external dependency.

Source: specs/007-xcom-core/spec.md FR-023, FR-024, FR-026 through FR-028; provenance: accepted; status: accepted.

Verification intent: Run source, symbol, dependency, and runtime isolation scans and preserve all accepted earlier X-COM validation suites.

## XCOM-PROV-011 [ubiquitous]

The provider-composition slice shall provide useful Doxygen documentation and reciprocal requirements-to-design-to-code-to-test traceability with revision-bound unit, static-analysis, integration, validation, and independent-review evidence.

Source: specs/007-xcom-core/spec.md FR-029 and FR-030; provenance: accepted; status: accepted.

Verification intent: Generate warning-free strict Doxygen output, validate every traceability edge reciprocally, execute all five measures, and inspect an independent Astra review of the exact revision.
