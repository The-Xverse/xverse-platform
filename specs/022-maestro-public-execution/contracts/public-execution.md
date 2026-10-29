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

## Current public Python prototype

Imports come from xverse.maestro.execution. CanonicalSubmission,
ExperimentSelection, InspectionHost and prepare_execution produce an immutable
PreparedExecution. Pure provider lifecycle expansion is validated by plan_lifecycle
into LifecycleGraph. HostExecutionPermit binds the exact preparation/graph plus
PublicExecutionService.runtime_binding_digest, environment and external approval
reference. Provider installation_digest must match the separately frozen effective
configuration. A static receipt or a permit without runtime binding cannot run.

PublicExecutionService.start(prepared, graph, permit, idempotency_key=...) rechecks
all inputs before the durable claim. read(run_id) is inert; observe(run_id,
expected_version=...) performs bounded resource observation. stop(run_id,
expected_version=...) cancels and cleans up; close refuses active experiments.
Original snapshots retain stateVersion, run/plan/input/preparation/lifecycle IDs,
operation/correlation IDs, bounded original event references and host clocks,
cleanup state, writer state and a bounded failure code. Original Argus reader
recorded/assessed verdicts remain a separate contract, not inferred from writer state.

Native Linux prototype only; one unresolved active experiment per service. Whole-run
and aggregate cleanup bounds are host inputs. Restarted claims without original
handles are unknown and cannot dispatch again or signal. FixedProcessInstallation
passes at most4096 bytes of frozen data via stdin after the provider retains its
OwnedChild; ProcessOwnershipError also retains a partially acquired child. No
process groups, descendant inference or reconstructed PID signals are supported.
Provider interpretation of scenario/profile semantics and installation reservation
is required and verified for each admitted provider, not granted by a generic enum.
