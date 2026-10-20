# W-02/W-03 owned syscall fault facility — proposed engineering decision

Current continuation (2026-10-19): the historical proposal below was implemented
as an owned fixture. Its original successful-append W02 preparation is rejected:
append_event flushes immediately, so it produced no target write. The selected
successor explicitly records a failed extra fixture annotation before its target
internal-flush failure. Loader/role isolation, that conditional W02 mechanism and
actual-close-then-EIO W03 pass4/4 per source/wheel phase. See
ADR-ML3-WRITER-FAULT-0001.md, findings244/246–248 and
evidence/affa17/native-writer-stream-20261019c/verification.json.
An isolated healthy-prefix W02 fault, complete W rows and full17 remain open.
Production bootstrap, Argus writer and private stream are unchanged.

Historical proposal status: DRAFT / NOT IMPLEMENTED / NOT ADMITTED / NO STAGE COVERAGE CLAIM.
Scope: existing full increment17 W-02/W-03 verification. This does not modify the
production bootstrap, Argus writer, private stream, original deadline or main branch.

## Observed constraint

Original Argus finalize calls public flush_buffer, then the internal stream flush
and close, before the try/except that assigns failed state. Public method-entry
exceptions do not demonstrate either internal flush/close stage. Replacing or
inspecting the private Python stream is prohibited. Native bootstrap also executes
workers with an empty environment; an ambient LD_PRELOAD is neither effective nor
an admitted facility. Prior W-01/W-04/W-05/W-06 controls remain bounded mechanism
evidence; W-02/W-03 stay unverified.

## Candidate mechanism for separate review before implementation

Use a fixed, hash-admitted OWNED TEST bootstrap derived from the frozen original.
Embed an identified C shared-library image in the helper binary itself. Only role3
creates an immutable sealed memfd containing those bytes and supplies a fixed
LD_PRELOAD=/proc/self/fd/... entry to its own Python worker. Other helper roles keep
the original empty environment. The derivative helper digest binds library bytes,
fixed code, mode and exact owned public events.jsonl target before any birth. Keep
the original parent/child, credentials, no-new-privileges, dumpability, containment,
watchdog and lease mechanisms. Record every deviation from the production facility;
this is a fault-injection environment, not full M1 admission.

The library may intercept write/close syscalls only for a writable descriptor whose
OS target is the exactly admitted OWNED PUBLIC event-stream pathname. Matching that
public syscall target must not inspect, replace or obtain the writer's private
Python stream object/state. Reject this candidate if that boundary cannot be
established in separate source review. No descriptor/permit/control material is
exported as runtime authority. No process discovery or foreign-target injection.

- W-03 candidate: after the actual original close syscall on the selected public
  stream succeeds, return a fixed EIO. Preserve the actual C syscall observation
  and public writer state/usability/manifest separately; an open state flag cannot
  justify abort. Do not infer close from merely entering public finalize.
- W-02 candidate: a fixed wrapper around public flush_buffer calls the original
  method during finalize, then appends one small explicitly labelled non-Maestro
  test annotation through public append_event. The next internal flush must issue
  an actual write; inject its failure only after the first public flush wrapper
  has returned. Record exact operation ordering. If the append flushes early or
  the expected syscall never occurs, record mechanism NOT_DEMONSTRATED, not W-02.
  Use a persistent write fault to verify unknown usability/no abort; an optional
  one-shot fault may exercise positive fresh flush before bounded abort.

The extra test annotation receives no normal Maestro coverage or scientific credit.
Never inspect/replace the private stream, reopen a writer, fake an ACK, change a
deadline or manufacture a durable manifest. At most one bounded abort follows a
fresh successful public flush. Preserve actual original writer/process/manifest
observations and original helper/C1/root waits even when injection fails.

## Proof required before counting any stage

Freeze bootstrap/library source and compiler commands, hashes, actual embedded
library bytes, package identity, original external inputs and expected outcomes.
First prove the admission-only loader on an owned component, including isolation
from other roles; no new factory run is implied. Then execute the actual original
native report/close path, retain both Python public-method and C syscall traces,
and independently read the durable original manifest/bytes. Run exact source and
installed-wheel controls once; retain every failed mechanism. A loader failure,
unsupported interposition or missing trace keeps the W row unverified.

This work can proceed independently of the pending restart API clarification.
Record a separate read-only facility review before implementation and an ADR update
if this candidate is selected. Do not silently reinterpret the prohibition on
private stream state or promote this proposal into validated stage evidence.
