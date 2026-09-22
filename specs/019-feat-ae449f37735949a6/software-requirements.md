# SWE.1 Software requirements (EARS)

## XCOM-OBS-001 [ubiquitous]

The X-COM observation boundary shall remain domain-neutral, provider-neutral, versioned, and filterable at declared logical route points without requiring a provider-specific sniffer interface.

Source: specs/007-xcom-core/spec.md FR-001, FR-003, FR-011, FR-022 and ADR-0019; provenance: accepted; status: accepted.

Verification intent: Attach synthetic taps to multiple logical routes and providers, validate version and filter behavior, and scan dependencies and public interfaces for provider, protocol, product, or domain coupling.

## XCOM-OBS-002 [state_driven]

While an observation tap uses the default metadata-only policy, the X-COM shall expose zero payload bytes in each matching record and shall retain contract, interface, endpoint, interaction, origin, timestamp, clock-domain, correlation, causation, route, provider, size, and provider-outcome metadata.

Source: specs/007-xcom-core/spec.md FR-005, FR-012 and SC-003; provenance: accepted; status: accepted.

Verification intent: Submit every interaction family with nonempty payloads and prove records preserve required metadata while exposing an empty payload view.

## XCOM-OBS-003 [event_driven]

When an explicit payload observation policy permits content, the X-COM shall expose only the configured bounded payload view and shall report whether content is complete, truncated, omitted, redacted, and schema-decoded or undecoded without inventing decoding success.

Source: specs/007-xcom-core/spec.md FR-012, FR-025 and ADR-0019; provenance: accepted; status: accepted.

Verification intent: Exercise metadata-only, bounded-prefix, complete-within-limit, and explicit redaction cases and compare payload bytes and status fields.

## XCOM-OBS-004 [state_driven]

While a best-effort tap queue is full, the X-COM shall apply its declared bounded drop-newest or coalesce-latest policy, shall never grow storage or block normal provider delivery, and shall expose exact accepted, dropped, coalesced, and queued counters.

Source: specs/007-xcom-core/spec.md FR-007, FR-013, FR-014 and SC-004; provenance: accepted; status: accepted.

Verification intent: Saturate fixed queues for both best-effort policies, compare bounds and counters, and prove normal-route item count, order, and provider outcomes remain unchanged.

## XCOM-OBS-005 [state_driven]

While a tap uses explicitly declared lossless-validation mode, the X-COM shall reject the corresponding normal submission before provider mutation when observation capacity is unavailable, shall return a stable observation-backpressure outcome, and shall mark experiment validity as degraded until acknowledged.

Source: specs/007-xcom-core/spec.md FR-013, FR-014 and ADR-0019; provenance: accepted; status: accepted.

Verification intent: Exhaust lossless capacity, prove zero provider delivery for the rejected item, inspect the stable outcome and degraded-validity counters, then acknowledge and recover.

## XCOM-OBS-006 [event_driven]

When a tap is attached, polled, inspected, acknowledged, or detached, the X-COM shall require an exact current hub identity, tap identity, and generation and shall reject stale, foreign, duplicate, or closed handles without unrelated mutation.

Source: specs/007-xcom-core/spec.md FR-009, FR-010, FR-011 and FR-014; provenance: accepted; status: accepted.

Verification intent: Exercise exact, stale, foreign, recreated, duplicate-detach, and capacity-exhausted handles across independent hubs.

## XCOM-OBS-007 [event_driven]

When a best-effort observer is slow, disconnected, failed, or detached, the X-COM shall isolate that observer so unrelated routes and provider delivery outcomes remain unchanged and any observation loss remains visible.

Source: specs/007-xcom-core/spec.md FR-013, FR-014, SC-004 and SC-005; provenance: accepted; status: accepted.

Verification intent: Compare deterministic loopback traffic with active, saturated, disconnected, failed, and detached synthetic sinks and inspect per-tap loss counters.

## XCOM-OBS-008 [ubiquitous]

The observation implementation shall use finite preallocated storage, serialize shared mutation, return owned records and snapshots, invoke no consumer callback while locked, and document ownership, lifetime, and thread-safety behavior.

Source: specs/007-xcom-core/spec.md FR-007, FR-013 and FR-029; provenance: accepted; status: accepted.

Verification intent: Run concurrent publication and polling tests, allocation and fixed-storage inspection, callback-symbol exclusion, public API inspection, and strict Doxygen.

## XCOM-OBS-009 [ubiquitous]

The observation slice shall perform no filesystem, environment, process, socket, network, secret, legacy-repository, XDL-compilation, stimulation, gateway, dashboard, Argus-storage, Maestro, or Faults operation and shall add no external dependency.

Source: specs/007-xcom-core/spec.md FR-023, FR-024, FR-026 through FR-028; provenance: accepted; status: accepted.

Verification intent: Run forbidden-access, symbol, dependency, and runtime-isolation scans and preserve all accepted X-COM validators.

## XCOM-OBS-010 [ubiquitous]

The observation slice shall provide warning-free Doxygen, reciprocal requirements-to-design-to-code-to-test traceability, host-bound evidence, and a repeatable benchmark showing no more than two percent median throughput and latency regression when taps are disabled on the admitted fixture.

Source: specs/007-xcom-core/spec.md FR-029, FR-030, SC-008 through SC-010; provenance: accepted; status: accepted.

Verification intent: Generate strict Doxygen, validate reciprocal traceability, run unit/static/integration/validation and repeated paired disabled-tap benchmarks with environment disclosure, and complete independent review.
