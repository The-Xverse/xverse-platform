# Lifecycle and evidence contract

## Execution operations

The lifecycle plan describes these phases without performing them. The permit and durable intent are
checked only when a future runtime attempts the corresponding mutating operation.

| Phase | Required declaration | Failure result |
|---|---|---|
| Prepare | Preconditions, non-secret environment data, exclusive mutation lease, permit, and durable intent. | `Blocked`; no start action. |
| Start | Exact M3 process action; return one ownership handle. | `Failed`; do not infer retry or cleanup. |
| Observe | Declared readiness/health/interface evidence and timeout. | `Blocked` or `Failed`; a delay alone is insufficient. |
| Stop | Explicit idempotent action using a revalidated ownership handle and timeout. | `Failed`; report remaining state without broad remediation. |
| Cleanup | Handle-authorized owned-resource-only cleanup boundary. | `Failed`; preserve evidence and escalate to the operator. |

## Process/provider boundary

A process action declares an absolute executable, ordered argument vector, explicit working directory,
allowlisted environment names, and closed inherited handles. It does not use an implicit shell or
ambient environment. The prototype process provider also requires an explicit executable allowlist,
execution root, and caller-supplied isolation attestation. The attestation is a fail-closed trust input;
it does not create an operating-system sandbox, so the public M3 proof uses only the in-memory fixture.
The current M3 provider boundary accepts only the explicit `ProcessAction` model. A non-process typed
action requires a separately specified platform capability; `None` cannot carry or imply hidden
provider configuration. Every provider exposes its exact ID and kind and returns an opaque ownership
handle bound to execution ID, plan action, provider ID/kind pair, and concrete resource.

Only a validated ownership handle authorizes observe, stop, or cleanup. Names, ports, paths, and
discovery results never confer ownership. Start/stop are idempotent by execution ID. Mutating actions
for one catalog/environment identity are exclusive. After controller interruption, reconciliation is
observation-only until the provider revalidates the persisted handle.

## Evidence record

Every phase emits deterministic data containing selected catalog/Component identity, XDL graph and
artifact revision, plan revision, realization class, declared versus observed status, timestamp,
diagnostics, and evidence limitations. Durable intent precedes every mutation. A record never equates lifecycle completion with component
behavior, protocol compatibility, application correctness, or parity.

## Authorization boundary

Planning produces no side effect and requires no permit. Activating a future execution requires a
matching unexpired single-use permit described in [execution-permit.md](execution-permit.md). Its
persisted activation covers only the bound execution and action set; expiry never prevents
handle-authorized containment of a resource that execution already owns. The permit is an operational
approval record, not an authentication system; host permissions remain the access-control boundary.
The public validation creates a local single-use permit for the isolated in-memory fixture only. It
supplies no permit for a process, legacy component, or production operation.

## Evidence failure and secrets

If intent cannot be persisted, the mutation does not run. If an outcome cannot be persisted, the run
becomes `evidence-incomplete`: no new start action is allowed, while observe and handle-authorized
stop/cleanup remain available. M3 does not resolve or inject secrets; any secret-dependent entry is
catalog-visible but blocked before planning.
