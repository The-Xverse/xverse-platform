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
counters make loss visible. Coalescing replaces only a queued record with the same
logical contract, interface, endpoint, interaction, origin, route, and provider
identity; a full queue without that match drops the new record. `lossless_validation`
uses an exact hub-owned reservation before provider dispatch. If capacity is not
available, submission returns the stable observation-backpressure outcome before the
provider is mutated, and experiment validity is degraded until acknowledgement.

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

The focused unit fixture covers values, versions, all declared filter constraints
including origin, payload dispositions, counters, exact and recreated handles, tap
capacity, bounded queues, and competing reservation/pull publication. The integration
fixture covers logical interaction families, provider outcomes, best-effort isolation,
lossless pre-dispatch rejection before provider mutation, acknowledgement, and shared-
hub concurrency.
The disabled-tap benchmark uses repeated paired samples on the owned loopback
fixture, reports its environment and uncertainty limitations, and enforces the
accepted two-percent median throughput and latency threshold. Its test-only
baseline seam must have a byte-identical function body to `ProviderComposition::submit`
at pinned revision `39977ba9e724524dfc42a51e53fa3d61a8964a85`; validation rejects drift before
running the benchmark. It is local prototype evidence and is not a production
performance claim.

Every `scripts/validate_xcom_observation.py` measure binds host execution to the
exact `SESN_CANDIDATE_REVISION`, rejects a dirty or mismatched candidate before any
measure work, and revalidates that identity after the measure completes. The
validator checks fixed-storage and forbidden-boundary policy, generates strict
Doxygen evidence, and runs the observation measures. It records verbose benchmark
output—including candidate revision, build profile, environment, paired samples,
medians, threshold results, and uncertainty—in host-captured evidence. It also runs
the complete accepted core-types, endpoint/route lifecycle, and provider/loopback
validators in a disposable clean worktree at that exact revision. This preserves
their native ownership and static gates without altering a predecessor validator.
Each predecessor validator applies its explicit finite allowlists for accepted later-
capability paths while retaining its original behavioral, static-analysis, Doxygen,
traceability, ownership, and isolation gates. No historical baseline checkout or
patched projection substitutes for the exact candidate during predecessor execution.
The approved pre-observation revision remains pinned only for the disabled-tap
benchmark comparison seam; it is not predecessor regression evidence.
The companion traceability JSON records reverse artifact roles, requirement
allocations, and design allocations; validation compares those sets exactly with
every forward requirement/design edge and with the authoritative host-measure
allocations.

## REF-002 SADS disposition

The following dispositions are scoped to this prototype observation slice and do
not upgrade the architectural-target maturity recorded by REF-002. `partial` means
the bounded local implementation contributes only the stated behavior; it is not a
claim to implement the full system requirement.

| REF-002 ID | Disposition | Observation-slice contribution or boundary |
| --- | --- | --- |
| XVE-SYS-0139 | partial | Bounded local observation augments the core bus prototype; no runtime bus claim. |
| XVE-SYS-0140 | partial | Records retain all four generic interaction families. |
| XVE-SYS-0141 | deferred | Protocol adapters remain outside this capability. |
| XVE-SYS-0142 | partial | Filtering and records are provider-neutral; no provider adapter is implemented. |
| XVE-SYS-0143 | deferred | Registry and discovery are not implemented. |
| XVE-SYS-0144 | deferred | Sessions, permits, and security/IAM are not implemented. |
| XVE-SYS-0145 | allocated | QoS and capability negotiation remain allocated to the broader X-COM capability. |
| XVE-SYS-0146 | partial | The observation contract is versioned and exposes undecoded schema status only. |
| XVE-SYS-0147 | partial | Records retain source and observation clock-domain metadata; no time authority is implemented. |
| XVE-SYS-0148 | deferred | Persistent record/replay is not implemented. |
| XVE-SYS-0149 | partial | Fixed observation records, counters, and pull access are implemented; no external tool stream exists. |
| XVE-SYS-0150 | deferred | Edge or cloud routing is not implemented. |
| XVE-SYS-0151 | deferred | Argus analytics, storage, and presentation are not implemented. |
| XVE-SYS-0152 | deferred | Stimulation and workflow triggering are not implemented. |
| XVE-SYS-0153 | deferred | Network, encryption, and mutual authentication are not implemented. |
| XVE-SYS-0154 | partial | Provider outcomes and provenance metadata are retained; safe intent execution is not implemented. |
| XVE-SYS-0155 | deferred | Multi-tenant security and deployment isolation are not implemented. |
| XVE-SYS-0156 | deferred | Gateway behavior is not implemented. |
| XVE-SYS-0157 | deferred | Live protocol reconfiguration is not implemented. |
| XVE-SYS-0158 | deferred | Automatic failover and recovery are not implemented. |

Capability 007 also identifies the following shared REF-002 requirements. Their
disposition remains `allocated` to the named owning capability; the observation
slice neither implements nor discharges them. The bounded record contract may be
consumed by those future capabilities through the public X-COM boundary.

| REF-002 IDs | Disposition | Preserved owner/boundary |
| --- | --- | --- |
| XVE-SYS-0048–0049 | allocated | Simulation/model runtime, FMI, and Maestro remain future capabilities. |
| XVE-SYS-0065, XVE-SYS-0089, XVE-SYS-0109–0111 | allocated | Maestro, Runtime, Time, and Security retain ownership. |
| XVE-SYS-0123, XVE-SYS-0126–0127 | allocated | Runtime, Argus, Time, and Security retain ownership. |
| XVE-SYS-0179, XVE-SYS-0183, XVE-SYS-0193–0194 | allocated | Argus owns monitoring, logging, analytics, storage, and presentation. |
| XVE-SYS-0237–0250 | allocated | SDK, plugins, and subsystem adapters remain future extension capabilities. |
| XVE-SYS-0251–0264 | allocated | Time and Maestro retain time-authority and determinism ownership; X-COM only retains supplied clock metadata. |
| XVE-SYS-0265–0279 | allocated | Faults, Runtime, Maestro, and Argus retain fault and recovery ownership. |
