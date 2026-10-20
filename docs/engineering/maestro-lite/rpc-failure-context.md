# Original in-memory persistence failure context

Status: partial candidate, source/wheel verified; no stable17 or causal closure.
[ADR-RUNTIME-0006](ADR-ML3-RUNTIME-0006.md) precedes implementation.

`PersistenceClient.rpc_failure` retains the first RPC failure as a frozen
`PersistenceRPCFailure`: closed protocol kind/stage, original host session,
allocated sequence/generated operation ID when available, actual monotonic start
and failure times, original transmitted deadline, and sanitized ML diagnostic.
No body, permit, path, raw exception text or unbounded history is retained. Stage
identifies local validation/send/receive/acknowledgement/post-ack handling, not a
worker or storage root cause. None means no available RPC failure observation;
it does not establish success or absence of another failure.

The existing nonblocking lock serializes capture; a conflicting call cannot replace
the active request's observation. Later calls and original cleanup preserve the
first record. Reading uses original local identity without depending on ordinary
live aliases. An original PersistenceError carries available context when client
construction fails; the private RuntimeResult retains context from the original
storage owner after cleanup. Matching completed start returns the original result.
No deadline, retry, wire, normal evidence, ownership, approval or readiness change.

Retained287 evidence narrows the old timeout to observe-sink dispatch publication/
ACK before local pending registration or effect. Its exact RPC end and underlying
cause remain unavailable;286 cannot be assigned the same cause. The new feature
cannot reconstruct missing historical facts or close135/222/286/287.

A fresh source/wheel candidate passes57 checks per phase:6 new actual fault controls,
29 persistence,14 startup and8 entry. Tests exercise actual blocked worker flush/init,
worker error ACK and a stopped original storage child, then verify original bounded
cleanup/context retention; successful/conflicting calls fabricate no failure. Audit
retains114 absent owned reservations,10 actual failure contexts,12 primary startup
cleanup results,254 M3 links and4 closed original-input recomputations. Old negative
wait-ownership controls preserve their client-level unknowns alongside the test
bootstrap's actual direct-child reap. These are owned components, not admitted M1
or actual RuntimeService execution and not universal host timing bounds.

See [audit](evidence/affa17/rpc-failure-20261019a/verification.json),
[partial bidirectional trace](evidence/affa17/rpc-failure-partial-traceability.json),
[retained failure analysis](evidence/affa17/rpc-failure-retained-localization-20261019.json)
and [continuation](evidence/affa17/continuation-rpc-failure-20261019.md).
Future consumers must treat context as an observation, never a durable outcome,
ACK, ownership or execution grant. Missing context stays unknown. All full024
requirements/matrices,source-parent semantics,M1/regression/independent full review,
stable17 and user acceptance remain open. CAPA remains manual observation-only;
all effectiveness NOT_DEMONSTRATED, with no automatic025 integration or gate effect.


The [metadata-loss repair](rpc-context-loss.md) subsequently validates the original
first record's identity/content and prevents optional observation failures from
blocking actual cleanup results or original RPC cancellation. Source/wheel61 each
pass. The57-check scope above describes the prior frozen candidate; historical
135/222/286/287 and full-scope gates remain open.
