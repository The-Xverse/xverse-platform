# Reverse unit teardown unit contract

Before product code; cases in teardown-expected.json.
C1 terminate(descriptor, deadline=...) freezes/kills as permitted, observes exact
empty membership and retains original controls. release_empty requires that state,
rechecks identity/frozen emptiness and confirms original unlink/removal before
closing the FD. Neither accepts a name/PID substitute or claims child reaping.
Explicit deadline session/original generation and <=5 s operation bounds apply;
nonblocking lock conflict rejects. Legacy force_cleanup default remains compatible.

ReverseTeardown(facade, per_unit_seconds=...) captures only original live objects
and owns no new start permit. run(deadline, reason=...) freezes the original target
registry, uses the same normal mutation locks, closes starts and walks the original
combined dependency graph in reverse. Exact catalog handles remain necessary for
ordinary mutation even when a leader has already exited. Observe the issuer's
actual direct-child reap and separate empty C1 before stop outcome, then durable
cleanup intent before removal and actual release before cleanup outcome.

The original storage child owns all normal M3 records and Argus append+flush calls.
Closed phase/stage requests bind unit, generation, original start claim, full handle,
original boundary hash, active step, operation, sequence, host session/time and
observed flags. Forged/copied result objects cannot become record authority. Worker
validates phase/handle/claim/reverse order and public source/mirror continuity.
M3 stop/cleanup intents retain original permit ID but mint no consumption or nonce.
Normal intent payload uses intent/pending with its exact M3 catalog action source;
outcome payload uses stop/cleanup succeeded only after actual observation.

Per-unit caps are finite (0<cap<=5 s), total <=16*cap and original generation end.
Normal work gets 60 percent; reserved remainder supports original C1 cleanup on
normal failure. A missed/failed normal record stays missing; actual emergency tree
release is separate from unresolved native child-reap. Continue other owned units.
Return immutable per-unit facts and a partial result, never full run/evidence success.
Repeated matching reason returns the cached exact result without new I/O; altered
reason/session/identity rejects. Cancellation bypasses the normal locks.

Verify real two-unit reverse stop/reap/release and actual M3/Argus ordering; staged
and already-exited/descendant cases; premature release; forged handles/results;
issuer/C1 loss; storage append/flush/hang; normal lock conflicts; independent cancel;
original deadline and repeat behavior. Retain exact hashes, public records, owned
cleanup/reaping evidence, findings before repairs, full source and installed wheel.
