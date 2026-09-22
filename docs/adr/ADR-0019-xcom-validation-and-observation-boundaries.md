# ADR-0019: X-COM validation and observation boundaries

**Status**: Accepted for specification — directed by the user on 2026-09-21; implementation remains
subject to the X-COM Spec Kit acceptance gate.

**Date**: 2026-09-21

## Context

X-COM must support node and system validation in addition to normal component communication. External
diagnostic, simulation, test, recording, and analysis tools need a common way to observe communication,
inject signals or messages, and invoke or emulate declared services. Operators also need to connect
dashboards and future tools to the data flowing through X-COM.

Vector describes CANoe use cases spanning communication-flow analysis, simulation, stimulation,
testing, diagnostics, and tool integration. That is useful capability context, but X-Verse remains
vendor-independent and domain-neutral and makes no CANoe compatibility claim.

## Decision

X-COM will define two explicit extension boundaries in addition to its normal provider boundary:

1. **Observation boundary** — passive, filterable taps expose normalized communication metadata and,
   only under an explicit payload policy, payload data. Consumers may include Argus, dashboards,
   recorders, sniffers, test reports, and analysis tools.
2. **Stimulation boundary** — an explicitly armed validation session may inject a declared signal or
   message, invoke a declared service, or emulate a declared service endpoint at an allowed logical
   injection point.

Every observed or stimulated item must carry logical interface identity, schema/version identity,
origin, timestamps and clock domain, sequence information where available, correlation/causation
identity, route/provider identity, and an evidence-safe outcome. Injected data must remain
distinguishable from component-originated data throughout its lifetime.

Stimulation is disabled by default and fails closed. A session must bind to an exact XDL system,
deployment, scenario, allowed interfaces/actions, environment, time window, rate/resource limits, and
operator-controlled authorization. Schema mismatch, undeclared targets, expired authorization,
feedback loops, ambiguous service ownership, and exhausted capacity must not silently enter the normal
data path. Deterministic scheduling and replay require explicit clock and ordering contracts.

Observation must not alter delivery semantics. A slow or failed observer cannot block the normal data
plane unless a separately declared lossless validation mode makes that effect explicit. Bounded queues,
drop/coalesce policy, and counters must make degradation observable. Payload capture is opt-in and must
support redaction or metadata-only operation.

X-COM owns communication events, taps, stimulation, and provider-neutral contracts. Argus owns
collection, storage/export, queries, dashboards, and operator visualization. The Faults subsystem owns
fault policy and campaigns; it may use X-COM's controlled stimulation hooks. Domain-specific diagnostics
and protocol semantics belong in profiles and adapters.

## Consequences

The first X-COM capability must cover normal communication, observation, and controlled stimulation
together so that testing is not retrofitted as an unsafe side channel. It will use owned loopback
fixtures and synthetic tools before any legacy protocol adapter or physical target. One local-only,
out-of-process gateway must prove that an outside tool can use the boundary without opening a remote
network listener; exact wire-contract and dependency details belong to the Spec Kit capability.

Dashboards, long-term telemetry storage, automotive diagnostic databases, packet-capture formats,
remote authorization infrastructure, and legacy gateway adapters are separate capabilities. A stable
boundary may support them later without embedding their product or domain model in X-COM.

The extra provenance and policy checks add design and performance cost. The implementation must prove
bounded overhead, fail-closed stimulation, observer isolation, and auditable validation results before
its maturity can advance beyond prototype.
