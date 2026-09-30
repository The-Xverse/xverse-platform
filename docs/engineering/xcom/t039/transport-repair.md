# T039 successor transport repair

Baseline: `a9c6e5d41e65625ed2b8c6f5a4457e10c6fcb090`. This is a successor candidate for the
five findings in the independent T039 review and the later F06 shutdown finding. It is not an accepted delivery until the exact
candidate receives repeated target-repository verification, a separate review, and user acceptance.

## Wire and lifecycle behavior

The published `ToolGateway` service still has ten methods. Protocol v1.1 adds optional
`stimulation_request_id` to `QuerySessionRequest` and a bounded durable outcome to its response.
The separate `GatewayLiveness` service has one local Unix-socket stream, `WatchSession`. A client
opens the watch before stateful calls and holds it for the session lifetime. `WatchSessionReady`
returns a fresh 64-character opaque `watch_id`. Each stateful call carries it in exactly one
`x-xcom-watch-id` metadata entry. An absent, different, or duplicated association is rejected before
core admission. `QueryVersion` advertises `xcom.gateway_liveness.local_ipc` revision 2; clients of
the unaccepted revision 1 watch must adopt the association metadata before stateful calls.
The identifier associates calls with the owner's live watch; callers must keep it
private and must not delegate it to another process. It is a lifecycle association, not stimulation
authorization or an OS process identity. Host permissions and the exact permit remain required.
The server grants one watch per session, checks cancellation every 10 ms, and closes observation
handles and releases or quarantines the lease when the watch ends. Calls that allocate or mutate
resources require this association. `QueryVersion` and read-only `QuerySession` remain available
without it. The latter reports
terminal state, bounded counters, current lease ownership, and active observation-stream count.

Server destruction stops stateful admission and signals the watch to finish, then uses gRPC shutdown
with a 100 ms forced-cancellation deadline before joining its poller and unlinking the socket.
An otherwise idle healthy watch cannot hold shutdown open. In-flight host action callbacks must
still return; the gateway does not preempt a running callback. Stateful handlers serialize admission
and dispatch, and the stimulation pre-commit probe also checks watch loss.

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

The admitted gRPC 1.30.2 binary uses the ordinary POSIX mutex layout. Its
[`sync_posix.h`](https://github.com/grpc/grpc/blob/v1.30.2/include/grpc/impl/codegen/sync_posix.h)
adds a pointer to `gpr_mu` under `GRPC_ASAN_ENABLED`, shifting `ClientContext` fields when an ASan
consumer links this unsanitized binary. The resulting layout is 512 rather than 504 bytes, and
`initial_metadata_corked_` moves from offset 392 to 400. A minimal placement-construction probe
reproduces the resulting invalid free without gateway code.

The gRPC target publicly defines the upstream `GRPC_ASAN_SUPPRESSED=1` layout option from
[`port_platform.h`](https://github.com/grpc/grpc/blob/v1.30.2/include/grpc/impl/codegen/port_platform.h).
It preserves the admitted binary's mutex ABI. It does not disable compiler ASan/UBSan or leak
detection; generated glue, the generated-client harness, the adapter, and the core all compile
with instrumentation. A public static assertion rejects the wrong mutex layout. On a runtime
upgrade or a sanitizer-built gRPC replacement, reassess the layout option against that binary
and rerun dependency admission and the full suite.

The new generated-client cases cover watch denial, explicit cancellation and abrupt process-exit
cleanup with a live lease and observation stream, denial of a separate unassociated process,
wrong and duplicate watch metadata, shutdown while the owner keeps its watch and resources live,
explicit read errors, cancellation and deadline after a controlled slow emission, durable outcome
lookup, and duplicate emission prevention. The bounded session cases cover negative clock arithmetic and
pre-dispatch transport abort. The exact commands, environment identities, results, logs, and hashes
belong in the successor evidence manifest after the candidate revision is pinned. Cleanup may wait
for a currently executing action to release the session lock; transport failure after commit must
always be reconciled from the durable journal.
