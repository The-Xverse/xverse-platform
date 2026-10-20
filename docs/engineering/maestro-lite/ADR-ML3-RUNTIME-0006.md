# Retain original in-memory persistence RPC failure context

Status: DRAFT before source implementation, finding297. Refines partial ML-SR-018,
020/024 observability without changing the external024 design or normal evidence.

The original worker can publish a record without the caller observing its ACK.
A bare ML-PERSIST-TIMEOUT does not identify the operation or prove its cause. Keep
one frozen first-failure record per original PersistenceClient: protocol kind,
request sequence/generated operation ID when allocated, a closed local stage,
host session, actual monotonic start/failure and original deadline nanoseconds,
and a bounded sanitized ML diagnostic. None means unavailable, not success.
No body, unit/permit/FD/path/private exception text or unbounded history is retained.
This record is an observation, not a durable outcome, ownership or ACK receipt.

Capture under the existing nonblocking RPC lock before original fail-closed cleanup;
conflict rejection must not overwrite the first in-flight operation. Retain the
first record through later failed calls and expose it only on the original local
owner, even when ordinary aliases no longer validate. Attach it to original
PersistenceError exceptions for constructor/startup loss, and include it in the
private RuntimeResult after original cleanup. Keep accepted top-level exports,
wire format, original deadlines, cancellation and unknown outcomes unchanged.

Unit specification: actual owned worker flush blocked past its original end must
retain receive-stage context and generated identity without retry; actual worker
error ACK must retain acknowledgement-stage context and sanitized code. Original
cleanup must reap both and preserve the identical frozen record. A successful
owned call leaves no failure. A conflicting call must leave the record unchanged.
A separately owned runtime with its original storage child stopped before a
schedule request must return incomplete execution plus the original context after
actual helper/root cleanup; do not infer historical287 cause from this control.

Python allocation: bounded host diagnostics, no native data-plane or new worker.
Existing unknown135/222/286/287 and all effectiveness/release gates remain open.
No new factory/M1 admission, author approval, scientific result or acceptance.
