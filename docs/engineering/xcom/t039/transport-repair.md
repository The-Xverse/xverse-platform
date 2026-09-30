# T039 successor transport repair

Baseline: `a9c6e5d41e65625ed2b8c6f5a4457e10c6fcb090`. This is a successor candidate for the
five findings in the independent T039 review. It is not an accepted delivery until the exact
candidate receives repeated target-repository verification, a separate review, and user acceptance.

## Wire and lifecycle behavior

The published `ToolGateway` service still has ten methods. Protocol v1.1 adds optional
`stimulation_request_id` to `QuerySessionRequest` and a bounded durable outcome to its response.
The separate `GatewayLiveness` service has one local Unix-socket stream, `WatchSession`. A client
opens the watch before stateful calls and holds it for the session lifetime. The server grants one
watch per session, checks cancellation every 10 ms, and closes observation handles and releases or
quarantines the lease when the watch ends. Calls that allocate or mutate resources require the
watch. `QueryVersion` and read-only `QuerySession` remain available without it. The latter reports
terminal state, bounded counters, current lease ownership, and active observation-stream count.

The final gateway-owned cancellation and deadline check for stimulation runs immediately before
the accepted action path. Once that path starts, the RPC can be cancelled or expire while the
action commits. Such a transport result is **uncertain**, not a rejected or failed stimulation
outcome. The caller must query `QuerySession` with the same session and decimal request ID. A
durable intent plus `EMITTED`, `REJECTED`, or `EVIDENCE_INCOMPLETE` resolves the outcome without
replaying the action. An absent durable intent does not by itself prove a scheduled request was
never queued; callers must not retry a queued request solely on that absence. The accepted journal
rejects duplicate retained request IDs, so an immediate retry cannot emit the same retained
request twice.

The adapter validates the request and reserves bounded response room before side effects, and
does not run a second cancellation, deadline, or response-size check after a mutation. The local
gRPC listener requires at least 1024 response bytes. Rejected observation reads now return an
explicit transport error; a valid empty stream still returns success. Declared-clock deadline and
lease-expiry addition saturates across the signed range.

## Verification and maintenance

The pinned gRPC 1.30.2 client inline call operations fail when instrumented with the admitted
ASan/UBSan runtime. In the sanitizer configuration, only the generated gRPC service glue and the
generated-client harness compile without instrumentation. The gateway session, adapter, and all
other production sources stay instrumented, and every generated-client case remains in the full
CTest suite. A future runtime upgrade should remove this narrow exclusion and rerun the complete
suite before changing the verification claim.

The new generated-client cases cover watch denial, explicit cancellation and abrupt process-exit
cleanup with a live lease and observation stream, explicit
read errors, cancellation and deadline after a controlled slow emission, durable outcome lookup,
and duplicate emission prevention. The bounded session cases cover negative clock arithmetic and
pre-dispatch transport abort. The exact commands, environment identities, results, logs, and hashes
belong in the successor evidence manifest after the candidate revision is pinned. Cleanup may wait
for a currently executing action to release the session lock; transport failure after commit must
always be reconciled from the durable journal.
