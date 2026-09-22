# SWE.3 Unit specifications (EARS)

## XCOM-OBS-UNIT-001 — ObservationValues [ubiquitous]

The ObservationValues unit shall validate and own versioned filters, payload policies, overflow policies, records, counters, and diagnostic outcomes using bounded storage.

Source: XCOM-OBS-001 through XCOM-OBS-004, XCOM-OBS-008.

Verification intent: Run value, bound, copy, payload-disposition, and stable-diagnostic unit tests.

## XCOM-OBS-UNIT-002 — ObservationHub [event_driven]

When a tap operation is requested, the ObservationHub unit shall authenticate the exact hub, tap, and generation and apply the declared bounded queue policy without unrelated mutation.

Source: XCOM-OBS-004 through XCOM-OBS-008.

Verification intent: Run handle, queue, saturation, concurrency, counter, validity, and detach tests.

## XCOM-OBS-UNIT-003 — ProviderObservationBridge [event_driven]

When ProviderComposition processes a valid submission, the ProviderObservationBridge unit shall preserve provider authority and publish a normalized outcome without holding provider and observation locks together.

Source: XCOM-OBS-001, XCOM-OBS-002, XCOM-OBS-004, XCOM-OBS-005, XCOM-OBS-007.

Verification intent: Run integrated loopback delivery, outcome, lossless reservation, isolation, and concurrency tests.

## XCOM-OBS-UNIT-004 — SyntheticObservationSink [ubiquitous]

The SyntheticObservationSink unit shall consume owned records only through exact pull-based tap operations and shall expose disconnect and failure behavior without callbacks or external I/O.

Source: XCOM-OBS-006 through XCOM-OBS-009.

Verification intent: Run slow, failed, disconnected, reattached, and foreign-handle sink tests.

## XCOM-OBS-UNIT-005 — ObservationEvidence [ubiquitous]

The ObservationEvidence unit shall enforce strict Doxygen, public-safety, fixed-storage, performance, regression, and reciprocal traceability gates for the exact candidate.

Source: XCOM-OBS-009, XCOM-OBS-010.

Verification intent: Run all declared host measures and independent exact-candidate review.
