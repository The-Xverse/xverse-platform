# Separate read-only teardown review — before successor repairs

18 October 2026; same-agent component review, not independent full-candidate review.
Read prbc, launcher revalidation, coordinator, storage extension and actual tests.

1. MAJOR framing mismatch: worker dispatch admits teardown but the shared strict
   frame decoder still rejects it. The textual change missed its multiline set.
   Add the closed kind explicitly; verify the actual diff and installed worker.
2. MAJOR emergency reserve order: helper drain currently precedes original C1
   cleanup, so a stalled helper can consume the reserve needed to kill/empty/release
   its exact tree. Attempt original C1 cleanup first, then drain within the same
   original unit end; never renew either deadline.
3. MINOR retained facts: preserve an actual successful issuer Query reap before
   writing its normal outcome. A later helper loss or write failure must not erase
   that already observed fact or infer a new reap from C1 release.
4. MINOR deadline clarity: the job-snapshot lock uses a dummy HostDeadline only to
   select nonblocking mode. Pass the original caller end instead; no invented end
   should appear in the new teardown path.
5. ADVISORY scope: this is reverse unit teardown with a local irreversible start
   barrier, not the full scheduler/global M1 cancellation protocol. Full helper
   closure, missing-observation dispositions/recovery, dual coverage/U8 and full
   admission/runtime remain open. Same-controller repeat facts are retained;
   reconstruction after controller loss remains a separate recovery obligation.
6. ADVISORY evidence: keep forced issuer-loss direct-child reaping explicitly
   unresolved even if original C1 removes its tree. New verifier must count the
   additional deliberate loss control separately from inherited bootstrap controls.
   M3/Argus normal gaps cannot be satisfied by emergency cleanup.

Findings precede repairs. Source/wheel regression, exact hashes and actual owned
cleanup/reaping audit are required before a stable commit. No acceptance or merge.
