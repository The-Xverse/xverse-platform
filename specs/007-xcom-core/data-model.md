# Data model: X-COM core communication and validation

The model below is a derived runtime representation. XDL resources remain authoritative and the
activation plan records their identities and digest; none of these entities is a new authored system
description.

## Entities

### CommunicationContract

- stable contract ID and version;
- interaction kind: `signal`, `message`, or `service`;
- direction and endpoint roles;
- schema ID, schema version, and content-type/encoding declaration;
- supported ordering, reliability, deadline, overflow, and backpressure policy;
- XDL provenance.

### EndpointSpec and EndpointHandle

`EndpointSpec` identifies one logical producer/consumer or service client/provider and its contract.
An activated provider returns an opaque `EndpointHandle` bound to provider instance, plan digest,
endpoint identity, and generation. Only a valid handle may publish, invoke, observe state, or close.

### RoutePlan

- route ID and plan digest;
- source and destination endpoint identities;
- selected provider ID/version and declared capabilities;
- queue and delivery policy;
- observation points and allowed validation actions;
- activation order and deterministic diagnostics.

### CommunicationItem

- interaction kind and contract identity;
- schema identity and typed payload view;
- origin: component, validation tool, replay, or provider-generated;
- source and observed timestamps plus clock domains;
- sequence, correlation, causation, route, and provider identities;
- delivery or rejection outcome.

The payload lifetime is explicit. Observers receive immutable views or bounded copies according to the
declared policy; they cannot retain an unsafe reference after callback completion.

### ObservationTap

- tap ID, route point, and filter;
- metadata/payload policy and redaction state;
- bounded capacity and drop/coalesce/lossless-validation policy;
- counters and validity effect;
- owned observer handle and lifecycle state.

### ObservationRecord

A normalized immutable projection of one communication or lifecycle event. It carries the item
identity and outcome plus observation time, tap identity, payload-view status, and queue counters.

### ValidationPermit and ValidationSession

The permit binds one session ID to an exact plan/XDL digest, scenario, deployment/environment,
authorized tool identity, allowed interfaces/actions, service-emulation ownership, time window,
rate/capacity limits, and nonce. A session consumes the permit once and owns all issued stimulation
handles until bounded closure or expiry.

### StimulationRequest and StimulationOutcome

The request identifies a permitted action, target, typed value/payload, schedule/clock domain,
correlation, causal parent, and quota cost. Durable intent precedes emission. The outcome records
accepted, rejected, delivered, expired, cancelled, or unknown status without inferring success.

### TimeAuthority

Identifies the active clock domain, supplies bounded current-time reads, and maps timestamps only when
an explicit mapping and tolerance exist. A missing or out-of-tolerance mapping is a validation result,
not an invitation to compare raw clock values.

### ToolGatewaySession

Represents one local IPC peer using the versioned external-tool contract. It binds transport session,
validation/observation handles, deadlines, flow-control bounds, and disconnect outcome without treating
socket access as stimulation authorization.

### ServiceEmulationLease

An atomically acquired exclusive lease bound to validation-session ID, service endpoint identity and
generation, plan digest, acquisition time, and expiry. Revocation or disconnect drains or quarantines
the lease before another provider may acquire it.

### Diagnostic

Stable code, severity, lifecycle phase, affected identity, explanation, correction, and deterministic
sort key. Diagnostics contain no unrestricted payload or sensitive deployment value.

## State models

Endpoint and route: `declared → validated → active → draining → closed`, with `failed` available from
each operational state. Restarted providers must reconcile exact handles before returning to `active`.

Observation tap: `declared → attached → active → degraded → detached`. `degraded` includes visible
drops, coalescing, truncation, or a lossless-mode backpressure effect.

Validation session: `declared → armed → active → closing → closed`, with `expired`, `revoked`, and
`evidence-incomplete` terminal states. No stimulation is accepted outside `active`.

## Invariants

1. Logical identities never depend on provider addresses or handles.
2. No endpoint, route, tap, or validation session is mutable without its exact issued handle.
3. Synthetic origin survives routing and observation.
4. Service emulation has at most one permitted owner per service endpoint and session.
5. All queues and quotas are finite and their overflow behavior is declared.
6. Metadata-only observation contains no payload bytes.
7. Every activation and stimulation decision is bound to the exact plan digest.
8. Local tool transport access never replaces validation-permit checks.
9. Scheduled requests never compare or order unmapped clock domains.
10. One endpoint generation has at most one active service-emulation lease.
