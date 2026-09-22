# ADR-0015: Owned compatibility lifecycle actions

**Status**: Accepted — M3 fixture implementation authorized 2026-09-20.
**Date**: 2026-09-20

## Context

M0 observed fixed delays, broad cleanup patterns, continued startup after exceptions, and incomplete
container-stop evidence in the legacy launcher. Replaying those behaviors through vNext would create
unsafe authority over resources the runtime did not create and would misrepresent delays as readiness.

## Decision

Future M3 lifecycle plans must explicitly declare prepare, start, observe, stop, cleanup, timeout,
failure, and ownership. The compatibility runtime may act only on resources it directly owns or an
explicitly approved provider action. A readiness condition requires declared observable evidence; a
sleep can constrain timing but cannot establish readiness. On failure it records evidence and leaves
unowned resources untouched.

Ownership is established only by an opaque provider-issued handle bound to the execution ID, plan
action, exact provider ID/kind pair, and concrete created resource. Resource names, ports, paths, or process discovery do
not establish ownership. Starts and stops are idempotent per execution ID, concurrent mutation is
serialized or rejected, and controller restart enters observation-only reconciliation until a handle
is revalidated.

Process providers use an absolute executable, ordered arguments, explicit working directory,
allowlisted environment names, and closed inherited handles. Implicit shell expansion and ambient
environment inheritance are outside the boundary.

The current M3 provider action is `ProcessAction`; non-process typed actions require a separate
platform specification and API change. A missing action cannot be interpreted as hidden provider
configuration. The controller validates the provider ID/kind pair against the plan and the returned
ownership handle before accepting activation.

Every actual execution additionally requires a target-specific, unexpired, single-use execution
permit binding the plan digest, catalog/environment identity, permitted actions, approval evidence,
and validity interval. This is an operational approval gate, not an authentication system; host
permissions remain the access-control boundary.

A durable intent record precedes every mutating action. If intent cannot be stored, the action does
not run. If an outcome cannot be stored, the run becomes `evidence-incomplete`: no further start is
allowed, while observe and handle-authorized stop/cleanup remain available for safety.

## Consequences

The initial fixture can prove lifecycle mechanics without proving compatibility. A selected legacy
component may remain blocked until its artifact, lifecycle contract, environment, owner, and exact
actions are reviewed. Broad process cleanup, port cleanup, ambient discovery, inferred retries, and
legacy repository mutation are prohibited.

M3 does not resolve or inject secrets. A secret-dependent binding may appear in the catalog but is
blocked from planning and execution pending another capability.

## Scope

This ADR defines a proposed safety boundary only. It does not authorize execution, alter legacy
launchers, select an AutoVerse baseline, establish parity, or make a production-readiness claim.
