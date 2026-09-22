# SWE.3 Unit specifications (EARS)

## XCOM-PROV-UNIT-001 — ProviderDescriptor [ubiquitous]

The ProviderDescriptor shall own a validated stable provider identity and contract version, explicit supported interaction and policy capabilities, and nonzero finite route, queue, and payload limits.

Source: XCOM-PROV-001, XCOM-PROV-002, XCOM-PROV-007.

Verification intent: Run valid construction and table-driven malformed, empty, over-bound, contradictory-capability, and zero-limit cases.

## XCOM-PROV-UNIT-002 — ProviderComposition [event_driven]

When a provider is supplied explicitly, the ProviderComposition shall register it within fixed capacity only when its identity and descriptor are unique, valid, and supported.

Source: XCOM-PROV-001, XCOM-PROV-002, XCOM-PROV-009, XCOM-PROV-010.

Verification intent: Test explicit valid registration, duplicate identities and instances, capacity exhaustion, lifetime contract, source linkage, and absence of discovery or dynamic loading.

## XCOM-PROV-UNIT-003 — ProviderRouteBinding [event_driven]

When route preparation or activation is requested, the ProviderRouteBinding shall validate provider capabilities and exact current lifecycle route and endpoint generations before issuing an immutable opaque provider-route handle.

Source: XCOM-PROV-003, XCOM-PROV-004.

Verification intent: Test every provider, policy, plan, endpoint, route, controller, state, generation, and capacity rejection with fresh no-mutation snapshots.

## XCOM-PROV-UNIT-004 — ProviderSubmission [event_driven]

When an item is submitted with an exact active provider-route handle, the ProviderSubmission shall validate all item and lifecycle bindings and return one stable accepted, saturated, unsupported, inactive, stale, or rejected outcome without partial delivery.

Source: XCOM-PROV-004, XCOM-PROV-005, XCOM-PROV-006.

Verification intent: Exercise valid and invalid items, all outcomes, exact diagnostic bytes, no-delivery rejection, and unchanged unrelated routes.

## XCOM-PROV-UNIT-005 — LoopbackProvider [ubiquitous]

The LoopbackProvider shall use fixed route and FIFO storage to deliver accepted items in deterministic per-route order for every supported interaction kind and shall reject the newest item while a queue is full.

Source: XCOM-PROV-005, XCOM-PROV-006, XCOM-PROV-007, XCOM-PROV-009.

Verification intent: Test all interaction families, multiple routes, order, exact item preservation, saturation, recovery, concurrency, and fixed allocation.

## XCOM-PROV-UNIT-006 — ProviderRouteCleanup [event_driven]

When an exact provider route is drained or closed, the ProviderRouteCleanup shall stop new submissions, expose queued-item disposition, and release only the exact owned generation after its declared close preconditions hold.

Source: XCOM-PROV-004, XCOM-PROV-008, XCOM-PROV-009.

Verification intent: Test drain with pending and empty queues, close preconditions, safe repeats, stale generations, recreation, reconciliation, and cross-route isolation.

## XCOM-PROV-UNIT-007 — ProviderEvidence [ubiquitous]

The provider-composition slice shall expose complete strict Doxygen and reciprocal requirements, design, code, test, and verification-measure traceability for the exact candidate revision.

Source: XCOM-PROV-010, XCOM-PROV-011.

Verification intent: Run strict Doxygen, forbidden-access and dependency scans, reciprocal traceability validation, all declared measures, prior regressions, and independent review.
