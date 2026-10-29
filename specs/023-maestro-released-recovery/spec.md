# Capability 023: released Maestro registration recovery

Status: authorized specification/implementation/review in progress; not accepted.
Baseline: ce2d5558cd36de5b29ab1e3c622303c7a77c61eb.
User approval: “I approve”, 2026-10-29, in response to Studio ADR-0035 scoped proposal.
This adds a public recovery boundary; accepted capability022 and its open Studio
T07 remain unchanged. No legacy source edits, physical/hybrid scope or publication.

## Stakeholder and system needs

MRX-SN-01: An operator can reuse a registration after original ownership is lost
only when original lifecycle provenance establishes fully released acquisition.
MRX-SN-02: Evidence, uncertainty and process-control authority remain distinct.
MRX-SYS-01: Host-owned inspection/permission/retirement must never replay Start.
MRX-SYS-02: A new run needs ordinary exact input/provider/permit admission as well
as verified retirement of every predecessor claim.

## User scenarios

US1: Inspect a predecessor without effects and receive exact original identities,
reader verdicts, a source witness and explicit eligibility/refusal reasons.
US2: A host grants a finite permit for that inspection; retirement writes only a
separate receipt. Retried retirement returns its original receipt.
US3: New Start revalidates the retirement and all ordinary admission. Original
read remains unknown, and unresolved/changed claims still fence the registration.
US4: Original terminal failed-writer evidence can remain incomplete while actual
released compensation is verifiable; aborted execution is not rewritten as success.

## Software requirements

- MRX-FR-001: Expose public bounded read inspection, host permit and retirement interfaces without private resource handles.
- MRX-FR-002: Bind original claim run/plan/input/request/operation/correlation identities, exact source bytes, host/runtime root and declared installed-provider pins.
- MRX-FR-003: Use the real public Argus reader and verify a terminal lifecycle with every acquiring intent explicitly compensated by released cleanup; preserve recorded and assessed verdicts.
- MRX-FR-004: Reject live ownership, open writers, unknown cleanup, missing/duplicate/inconsistent lifecycle facts, corruption, changing sources and unsupported shapes before any retirement.
- MRX-FR-005: Require a finite exact-inspection host-only recovery permit; imported XDL, caller records, paths and PIDs grant no authority.
- MRX-FR-006: Persist a separate immutable durable retirement record atomically and idempotently; preserve original claim and Argus bytes.
- MRX-FR-007: Allow new Start in the same root only after revalidating all predecessor retirements against current source and host/provider pins; original read remains unknown and repeated old Start never dispatches.
- MRX-FR-008: Serialize with original public root owner, reject concurrent/busy/active registrations and bound files, records, bytes, diagnostics and permits.
- MRX-FR-009: Inspection and retirement perform no provider callbacks, process signals, container mutation, message publication or device stimulation.
- MRX-FR-010: Preserve existing constructor/API behavior when recovery is unconfigured, SDK regression and native X-COM evidence boundaries.
- MRX-FR-011: Retain exact candidate/environment/commands/results, explicit REF-002 allocations and separate review findings; user acceptance precedes main/dependency integration.
- MRX-FR-012: Demonstrate actual owned-child normal stop, failed/cancelled startup compensation, owner loss, permitted retirement and a distinct new run in the original registration; complete Studio live acceptance remains downstream.

## Exclusions and fidelity

Trusted host, native Linux prototype, registered simulated/virtual resources only.
No hostile-host authenticity, kernel containment, remote/physical recovery, resource
termination, arbitrary root reset or restoration of old runtime/resource handles.
Native samples/coalescing, workload outcome and lifecycle compensation remain
separate. Missing lifecycle facts cannot be repaired from receipt order or silence.
