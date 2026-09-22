# SWE.1 Software requirements (EARS)

## XCOM-LIFE-001 [ubiquitous]

The X-COM endpoint and route lifecycle shall remain domain-neutral and shall keep logical endpoint and route identity independent from provider addresses, protocols, physical devices, and domain-specific semantics.

Source: specs/007-xcom-core/spec.md FR-001 and FR-003; provenance: accepted; status: accepted.

Verification intent: Compile and exercise endpoint and route lifecycles using only logical identities, contracts, plan digests, and explicit provider identities, with forbidden-field and dependency scans.

## XCOM-LIFE-002 [ubiquitous]

The X-COM lifecycle shall validate bounded endpoint declarations and route declarations against exact communication contracts and plan digests before either resource can become active.

Source: specs/007-xcom-core/spec.md FR-002 and FR-006; data-model.md EndpointSpec and RoutePlan; provenance: accepted; status: accepted.

Verification intent: Run positive and table-driven negative declaration, contract, direction, identity, digest, and bound tests and prove rejected declarations create no active resource.

## XCOM-LIFE-003 [event_driven]

When a lifecycle resource is declared, the X-COM lifecycle controller shall issue an opaque handle bound to the exact controller instance, logical resource identity, plan digest, resource kind, and monotonically advancing nonzero generation.

Source: specs/007-xcom-core/spec.md FR-009 and data-model.md EndpointSpec and EndpointHandle; provenance: accepted; status: accepted.

Verification intent: Inspect handles only through public accessors and test cross-controller, wrong-kind, wrong-digest, old-generation, copied-valid, and recreated-resource cases.

## XCOM-LIFE-004 [state_driven]

While an exact current handle is supplied, the X-COM lifecycle controller shall enforce the deterministic declared-to-validated-to-active-to-draining-to-closed state sequence, permit failure from each nonterminal operational state, and permit explicit closure from failed state.

Source: specs/007-xcom-core/spec.md FR-010 and data-model.md State models; provenance: accepted; status: accepted.

Verification intent: Exercise every permitted transition, every skipped or terminal transition, explicit failure and cleanup, and byte-stable resulting diagnostics.

## XCOM-LIFE-005 [ubiquitous]

The X-COM lifecycle controller shall treat an exact repeat of an already completed transition as idempotent by returning the current state without duplicating resources or advancing generation.

Source: specs/007-xcom-core/spec.md FR-010; provenance: accepted; status: accepted.

Verification intent: Repeat each completed transition and compare current state, resource counts, and generations before and after.

## XCOM-LIFE-006 [event_driven]

When a stale, foreign, mismatched, absent, or otherwise invalid handle is supplied, the X-COM lifecycle controller shall reject the operation with deterministic stable diagnostics and shall mutate no endpoint or route.

Source: specs/007-xcom-core/spec.md FR-009, FR-010, and FR-025; provenance: accepted; status: accepted.

Verification intent: Run forged-context, cross-controller, closed-generation, wrong-resource, and unknown-handle tests and compare exact codes, phases, identities, reasons, corrections, ordering, and unchanged snapshots.

## XCOM-LIFE-007 [ubiquitous]

The X-COM lifecycle controller shall enforce configured finite endpoint and route capacities at or below compile-time maxima and shall reject exhaustion or duplicate live identities without allocation growth, replacement, or unrelated-resource mutation.

Source: specs/007-xcom-core/spec.md FR-007 and data-model.md invariant 5; provenance: accepted; status: accepted.

Verification intent: Fill each configured capacity, reject the next declaration, close and recreate deterministically, and verify stable storage size, generation behavior, and isolation.

## XCOM-LIFE-008 [event_driven]

When route validation or activation is requested, the X-COM lifecycle controller shall require exact current endpoint handles, compatible source and destination directions and contract identities, a shared exact plan digest, and the required endpoint states before changing route state.

Source: specs/007-xcom-core/spec.md FR-006, FR-009, and data-model.md RoutePlan; provenance: accepted; status: accepted.

Verification intent: Test compatible signal, message, request, and response routes plus every endpoint-handle, direction, contract, plan, lifecycle-state, and endpoint-in-use rejection boundary.

## XCOM-LIFE-009 [ubiquitous]

The endpoint and route lifecycle slice shall store, copy, queue, emit, or transport no CommunicationItem, shall perform no filesystem, environment, process, socket, discovery, secret, or legacy access, and shall add no external dependency.

Source: specs/007-xcom-core/spec.md FR-026 and FR-028; bounded slice decision; provenance: accepted; status: accepted.

Verification intent: Run source/dependency scans, object-layout assertions, offline builds, and regression checks proving the slice contains only control-plane state and preserves the accepted core-types behavior.

## XCOM-LIFE-010 [ubiquitous]

The endpoint and route lifecycle slice shall provide useful Doxygen documentation and bidirectional requirements-to-design-to-code-to-test traceability with revision-bound unit, static-analysis, integration, validation, and independent-review evidence.

Source: specs/007-xcom-core/spec.md FR-029 and FR-030; provenance: accepted; status: accepted.

Verification intent: Generate warning-free strict Doxygen output, validate every traceability edge reciprocally, execute all five measures, and inspect the independent exact-revision review.

## XCOM-LIFE-011 [event_driven]

When a repeated transition is unsafe or a requested transition is invalid, the X-COM lifecycle controller shall reject it without changing any endpoint or route state.

Source: specs/007-xcom-core/spec.md FR-010; provenance: accepted; status: accepted.

Verification intent: Exercise skipped, reversed, terminal, and unsafe repeat transitions and compare fresh before and after snapshots of every affected resource.
