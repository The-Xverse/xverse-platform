# Preserve terminal results when optional RPC diagnostic identity is lost

Status: DRAFT before fault controls/repair, finding300. Extends RUNTIME-0006.
The optional diagnostic must not discard an already-observed original cleanup
result. A failed original-owner check, changed observation reference or changed
frozen fields makes this observation unavailable. Return the original RuntimeResult
with persistence_failure=None and ML-RUNTIME-RPC-CONTEXT-UNRESOLVED; retain actual
execution/cleanup/evidence outcomes without promoting lifecycle completion.

Pin the first observation reference and its original field values when captured;
validate them on the original getter. Later failed calls must not replace that
first pin. Missing/corrupt metadata is not reconstructed and grants no rights.
The runtime catches the bounded observation validation failures after cleanup,
never weakening ordinary ownership checks or original cleanup/wait requirements.

Unit specification: stop an original owned storage worker before dispatch to
produce an actual bounded RPC timeout. After actual root/helper waits and C1
release, separately lose the storage-owner tag, replace its observation attribute,
or alter a frozen record field reflectively. Each must return the factual incomplete
result with unavailable diagnostic and exact unresolved code. Matching repeat
retains that result after original metadata restoration following actual cleanup;
restore only for original local descriptor disposal, never to manufacture cleanup.
Preserve first raw failure observations in test evidence. A valid getter must still
return the exact original record, and repeated failure/conflict cannot replace it.

No deadline, native protocol, permit, top-level export, service admission or normal
record change. This fixes the selected diagnostic/result contract, not historical
timeout causes or CAPA effectiveness. All original full024 gates remain open.
