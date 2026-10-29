# Public released-registration recovery (prototype)

Implementation scope was authorized on2026-10-29 under Studio ADR-0035. This candidate
is not admitted until explicit platform acceptance and assembled main verification.

A host constructs `PublicExecutionService` with optional `recovery_bindings`, a tuple
of `RecoveryProviderBinding(provider_id, installation_digest)` for its registered
providers. These are trusted-host declared pins; the recovery reader does not probe
providers or independently attest an installation. Leave the tuple empty to retain
legacy predecessor fences without recovery.

`inspect_recovery(run_id)` returns an immutable `RecoveryInspection`. Its data shows
eligibility/reasons, original claim identities, exact source witness, declared
host/provider binding, original writer/evidence statuses and original terminal/cleanup
references. It performs no provider callback or resource operation. Ineligible source
is never repaired from a nominal released value or missing records.

A trusted host supplies `HostRecoveryPermit` bound to that exact inspection and current
host/runtime/recovery binding, with at most300seconds validity. Browser/project data
must never construct this permit. `retire_released(inspection, permit)` recaptures the
original source and writes a separate immutable receipt, retaining the structured
original grant and its digest. An exact retry returns the original receipt after
repeating root synchronization. If a post-link synchronization failed, a complete
receipt may remain visible with uncertain durability; retry verifies/synchronizes it
without replacement. Partial or corrupt files confer no activation permission.

`recovery_status(run_id)` reports retirement separately; `read(run_id)` remains
unknown for a lost original owner. Every distinct new Start revalidates predecessor
receipts/sources and current pins and then performs ordinary XDL/provider/lifecycle/
execution-permit admission. Old Start retry never dispatches again. Retirement does
not delete old claims, reopen failed writers, upgrade evidence or reset128-run capacity.

Supported source is the frozen public lifecycle writer format with one regular event
stream, no external artifacts, verified envelope/extension/claim shapes and explicit
reverse cleanup for all attempted acquisitions. A failed abort writer may remain
incomplete with structurally accounted compensation. Only the last interrupted phase
may lack its success outcome, with original terminal failure and all acquiring intents
explicitly released. Unknown/corrupt/open/changed/live source remains fenced. Native
observer loss is separate from lifecycle integrity; original verdicts are preserved.

This is native Linux, trusted-host owned-simulation scope. It has no process signalling,
container/device mutation, private-handle recovery, hostile-host authenticity, real-time
I/O guarantee or physical/remote recovery claim. Original rooted file/byte and finite
record/permit bounds are in capability023. Complete Studio/Autoverse acceptance remains
required after admission; source inspection and owned fixtures do not substitute for it.
