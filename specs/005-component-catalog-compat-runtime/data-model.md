# Data model: M3 component catalog and compatibility runtime

## Relationship model

```text
Component ← System componentInstance ← Deployment binding + compatibility Profile payload
                                      │ deterministic derivation
                                      ▼
                               Catalog Entry
                                      │ selected without side effect
                                      ▼
Lifecycle Plan ─── matching Execution Permit ─── Provider action → Owned Resource Handle
        │
        ▼
Durable intent/outcome Evidence Journal
```

## Entities

### Catalog Entry

Immutable derived record indexed by exact Deployment identity plus binding ID. It resolves the
binding's System component instance to an exact Component and joins the binding/target/artifact data
with `io.xverse.runtime.compatibility`. It is not independently authored. Multiple entries may share
one digest-identical artifact.

### Compatibility Boundary

One-way vNext responsibility around an unchanged external component. It declares what the future
adapter/provider may invoke and observe, rather than importing legacy implementation semantics.

### Realization Overlay

Selected environment binding for a logical component. It may identify a process, container, emulator,
model unit, remote provider, or physical asset by pinned/indirect reference. It never changes the
logical Component identity.

### Lifecycle Contract

Required prerequisites, owned actions, readiness observations, stop conditions, timeouts, failure
classification, and cleanup scope. Each field is explicit; sleeps and ambient discovery cannot fill a
missing readiness or ownership rule.

### Lifecycle Plan

Side-effect-free resolved sequence for exactly one selected entry/overlay. It records blocked
conditions as diagnostics and is absent when validation is incomplete. Its digest includes the exact
Deployment/binding, System instance, Component, Profile, target, realization, interfaces, time
domains, applicable Scenarios, environment, actions, and artifacts.

### Execution Permit

Explicit local, single-use operational approval that binds a canonical plan digest, catalog and
environment identity, permitted lifecycle action set, approval evidence reference, validity interval,
nonce, and exclusions. Planning does not need a permit. M3 does not claim authentication or identity
verification; host permissions remain the access-control boundary.

### Owned Resource Handle

Opaque provider-issued identity bound to execution ID, plan action, exact provider ID/kind pair, and concrete created
resource. It is the only basis for observe/stop/cleanup authority. Names, ports, paths, and ambient
discovery cannot create or reconstruct ownership.

### Evidence Journal

Append-only durable intent/outcome journal per planned transition. Intent persistence precedes every
mutating action. It separates declared state, observed state, unavailable observation, withheld detail,
timestamps, outcome, diagnostic references, and evidence limits.

## State model

```text
Unselected → Validated → Planned → Permitted → Preparing → Starting → Observing → Stopping → Stopped
                    │        │             │             │            │             │
                    └────────┴─────────────┴─────────────┴────────────┴─────────────→ Blocked/Failed
                                                          │
                                                          └──────────→ EvidenceIncomplete
```

Catalog validation and planning terminate at `Validated`, `Planned`, or `Blocked` without side effects.
Only a valid permit may enter `Preparing`. Start/stop are idempotent by execution ID and mutation is
exclusive per catalog/environment identity. After interruption, reconciliation is observation-only
until the provider validates the persisted handle. `EvidenceIncomplete` prohibits new start actions
but permits observation and handle-authorized stop/cleanup of already-owned resources.
