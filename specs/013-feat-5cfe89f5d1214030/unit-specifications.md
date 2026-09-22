# SWE.3 Unit specifications (EARS)

## XCOM-LIFE-UNIT-001 — EndpointSpec [ubiquitous]

The EndpointSpec shall create an immutable bounded declaration only when endpoint identity, exact plan digest, communication contract identity and version, direction, and explicit provider identity are complete and mutually compatible.

Source: XCOM-LIFE-001, XCOM-LIFE-002, XCOM-LIFE-009.

Verification intent: Run positive and table-driven missing, malformed, over-bound, direction, digest, and contract rejection tests.

## XCOM-LIFE-UNIT-002 — RouteSpec [event_driven]

When endpoint declarations are supplied, the RouteSpec shall accept only compatible source and destination directions, identical contract identities and versions, a shared exact plan digest, distinct endpoint identities, and an explicit matching provider identity.

Source: XCOM-LIFE-002, XCOM-LIFE-008.

Verification intent: Exercise declaration-only valid routes for all interaction kinds and independently reject every contract, direction, plan, provider, and identity mismatch.

## XCOM-LIFE-UNIT-003 — OwnershipHandle [event_driven]

When a resource declaration succeeds, the OwnershipHandle shall identify the issuing controller, resource kind, logical identity, exact plan digest, and monotonically advancing nonzero generation through immutable accessors and private construction.

Source: XCOM-LIFE-003, XCOM-LIFE-006.

Verification intent: Test copied handle validity and cross-controller, wrong-kind, wrong-resource, wrong-digest, closed-generation, and recreated-generation rejection.

## XCOM-LIFE-UNIT-004 — LifecycleController [state_driven]

While an exact current handle is supplied, the LifecycleController shall serialize and enforce declared, validated, active, draining, failed, and closed transitions and return idempotent state for completed safe repeats.

Source: XCOM-LIFE-004, XCOM-LIFE-005, XCOM-LIFE-006, XCOM-LIFE-011.

Verification intent: Run transition-table, safe-repeat, failure-cleanup, immutable-snapshot, exact-diagnostic, and concurrent-contention tests.

## XCOM-LIFE-UNIT-005 — BoundedLifecycleStorage [ubiquitous]

The BoundedLifecycleStorage shall enforce configured endpoint and route limits at or below compile-time maxima, retain no CommunicationItem, and reuse only closed slots with a higher generation and no unrelated record mutation.

Source: XCOM-LIFE-007, XCOM-LIFE-009.

Verification intent: Fill capacities, reject overflow and duplicate live identities, reuse closed slots, inspect object layout/source dependencies, and compare unrelated snapshots.

## XCOM-LIFE-UNIT-006 — LifecycleEvidence [ubiquitous]

The lifecycle slice shall expose complete strict Doxygen and reciprocal requirements, design, code, test, and verification-measure traceability for the exact candidate revision.

Source: XCOM-LIFE-010.

Verification intent: Run strict Doxygen, traceability schema and reciprocal-edge validation, all declared measures, and the independent review.

## XCOM-LIFE-UNIT-007 — RouteLifecycleOperations [event_driven]

When route validation or activation is requested, the RouteLifecycleOperations shall authenticate the exact current route and endpoint handles and shall reject ownership, generation, digest, direction, contract, or lifecycle-state mismatches without mutation.

Source: XCOM-LIFE-006, XCOM-LIFE-008, XCOM-LIFE-011.

Verification intent: Run independent route validation and activation cases for inactive, stale, foreign, wrong-generation, wrong-digest, incompatible, retained-endpoint, and fresh before/after no-mutation boundaries.
