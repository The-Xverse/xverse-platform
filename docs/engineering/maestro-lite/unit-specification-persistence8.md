# Persistence isolation unit contract

ML3-PERSISTENCE8-2026-10-18-v1, partial candidate, ready false.

Input cap: sealed regular memfd <= 1 MiB; strict private JSON, original XDL resources,
plan/preparation/provider/permit pins, fixed host session and <=394 s generation.
IPC: <=64 KiB SEQPACKET; exact closed version/kind/sequence/operation/deadline/scope/
body envelopes; 128 requests/session, operation <=5 s, drain <=2 s. Reject unknown,
duplicate, nonfinite, malformed, transferred-FD, foreign/forked/replayed/late data.

The worker creates the original PermitSession and accepted Argus run after Init.
No second writer or provider/cgroup/gate authority. RegisterIntent performs genuine
M3 claim -> actual public projection -> Argus append -> public flush -> current
M3/UTC and deadline checks. Revalidate uses that exact original stored receipt and
never consumes a new permit. Abort is failure closure only and never readiness.
The parent authenticates actual original-child replies and retains private receipt
identity. ReleaseOwner must consume that exact client/claim and use a bounded RPC
for fresh journal/permit validation before native Release. No supervisor-side
journal, manifest or Argus read/write may occur in that path.

Verify actual compiler/M3/Argus -> isolated ACK -> C1 frozen Stage -> native Release
and independent evidence readback after abort. Exercise initialization/claim/append/
flush/revalidation/abort failure and interruptible hang, cancellation while storage
is blocked, late/forged/copied replies, altered config/plan, original deadline,
replay, no workload instructions on failure, original C1 cleanup, child reaping and
unresolved identity retention. Preserve all existing admission/owner/API behavior;
run exact source and copied installed-wheel regressions with byte comparisons.
Record separate read-only findings before repair. Keep full requirement gates open.
