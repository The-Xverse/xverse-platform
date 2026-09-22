# X-COM observation boundary

## Scope and maturity

This document describes the capability-007 Phase 6 observation boundary. It is a
domain-neutral, provider-neutral C++20 prototype: implemented behavior is bounded
observation on owned loopback fixtures, not a production telemetry service. The
boundary does not implement stimulation, time authority, sessions, permits,
gateways, dashboards, adapters, Argus storage, Maestro, Faults, XDL compilation,
or legacy execution.

The public contract is versioned as `1.0.0`. A tap is attached to a caller-owned
`ObservationHub` with a logical filter, payload policy, finite record capacity,
and overflow policy. A tap handle is exact authority for one hub, tap slot, and
generation; names, routes, providers, and addresses are only filter data and do
not confer mutation authority.

## Observable behavior

Metadata-only is the default and returns zero payload bytes while retaining the
logical contract, interface, endpoint, interaction, origin, source and observation
timestamps, clock domains, correlation, causation, route, provider, source size,
and normalized provider outcome. An explicit bounded-prefix policy copies at most
the configured maximum and reports `complete` or `truncated`; redaction returns no
bytes and reports `redacted`. Schema status remains `undecoded` because this slice
does not perform schema decoding.

Every tap owns a fixed record ring. Best-effort `drop_newest` and `coalesce_latest`
never block or mutate provider delivery; accepted, dropped, coalesced, and queued
counters make loss visible. `lossless_validation` is explicit: if capacity is not
available, pre-dispatch submission returns the stable observation-backpressure
outcome, the provider is not mutated, and experiment validity is degraded until an
acknowledgement recovers it.

Records and snapshots are returned by value. Pull operations are serialized with
hub mutation, and there is no consumer callback path, including under an X-COM
lock. Storage is preallocated with eight tap slots and sixteen record slots per
tap; payload prefixes are bounded to 1024 bytes. No filesystem, environment,
process, socket, network, secret, external dependency, or ambient runtime access
is part of the implementation.

## Failure semantics and compatibility

Malformed policies, invalid identities, capacity exhaustion, stale/foreign/closed
handles, empty pulls, disconnected sinks, and lossless backpressure have stable
`ObservationOutcome` values and do not cause unrelated mutation. Provider
composition retains source-compatible no-tap behavior through an optional,
non-owning hub reference. Observation is not a provider-specific sniffer and does
not establish protocol, product, domain, parity, or production-readiness claims.

## Evidence and benchmark boundary

The focused unit fixture covers values, filters, payload dispositions, counters,
exact handles, bounded queues, and concurrent pull/publication. The integration
fixture covers logical interaction families, provider outcomes, best-effort
isolation, lossless pre-dispatch rejection, acknowledgement, and concurrency.
The disabled-tap benchmark uses repeated paired samples on the owned loopback
fixture, reports its environment and uncertainty limitations, and enforces the
accepted two-percent median throughput and latency threshold. It is local
prototype evidence and is not a production performance claim.

`scripts/validate_xcom_observation.py` binds host execution to the exact
`SESN_CANDIDATE_REVISION`, checks fixed-storage and forbidden-boundary policy,
generates strict Doxygen evidence, runs the observation measures, and preserves
the accepted core-types, endpoint/route lifecycle, and provider/loopback
regressions. Those predecessor measures are invoked explicitly as unit, lint,
static, and integration modes; core-types uses the accepted unchanged-core
guard plus current-candidate unit, static, and integration measures because its
legacy lint ownership assertion rejects later admitted units. Nested legacy
`--all` modes are not used. The companion traceability JSON is reciprocal across
requirements, design units, implementation, fixtures, and verification measures.

## SADS disposition

No REF-002 SADS requirement is allocated to this Phase 6 evidence slice. Any
future allocation for telemetry presentation, security, simulation/FMI, results,
or UI must be accepted as a separate capability; this boundary records those
areas as deferred rather than treating target architecture as implementation
evidence.
