# Public execution contract, proposed version 1.0

This document specifies behavior, not approval of an implementation. Public names
will be owned by xverse.maestro.execution and deliberately exported. No client
argument or annotation may require a private platform class.

## Inspection

Accept canonical authored documents/selection and caller expected compiler
identities, using host-installed profile schemas and provider bindings. Return
actual effective document/source, input-semantic and plan digests, resolved logical
bindings, host/provider pins, bounds, diagnostics and inspection identity. No
process, communication, stimulation or evidence writer starts during inspection.
Unknown semantics or mismatching effective inputs reject instead of being ignored.

## Start

Require exact current inspection and idempotency identity. Recheck installation,
provider capability, permissions, resource availability and expiry before dispatch.
Same identity/body returns the same run; another body conflicts. Maestro schedules
per-element lifecycle in dependency order and records readiness separately from
launch. Providers receive fixed host-bound installation context and semantic
parameters, never executable strings from the imported project.

## Read and stop

Read observes original state/resource/evidence witnesses and never starts work.
Stop requires current state version and actual owned scope, is idempotent, uses a
bounded reverse cleanup policy and distinguishes stopped from failed/unknown
release. PID alone, a process name, an address or a port never establishes ownership.
Reconnect/recovery reconciles existing handles and does not replay dispatch.

## Evidence and identities

The run, plan, semantic and logical-element identities come from authoritative
input inspection and actual runtime receipts. Lifecycle operations create explicit
operation/correlation IDs. Preserve originating event IDs, source clocks, causation,
X-COM sequences, provider outcomes, payload visibility and gaps into actual Argus.
Argus verification exposes recorded versus assessed status; ingestion order is
presentation order, not proof of causality. No source clock mapping is inferred.
Bound queues, event sizes, provider output, diagnostics, writer limits and result
pages. Slow consumers cannot silently change data-plane delivery or erase loss.

## Admission and compatibility

The new capability is limited to the host/provider/environment permissions it
actually verifies. It grants no old private-runtime lane approval, physical-device
permit or automatic native containment authority. Existing closed services remain
closed. Public inspection success does not imply execution permission or readiness.
