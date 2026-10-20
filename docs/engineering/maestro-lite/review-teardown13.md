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

7. MAJOR bounded emergency convergence (v2 actual control): owner cancellation
   can reap a frozen staged child while C1 samples membership, yielding the correct
   transient ML-TEARDOWN-MEMBERSHIP-UNKNOWN. One attempt leaves the boundary retained
   despite remaining reserve. Permit at most three retries only for this transient
   diagnostic, using the same original C1 and original unit end; retain unresolved
   after exhaustion. Do not relax identity/capability checks or extend deadlines.
8. ADVISORY verify the new normal phase payloads/source hashes through the unchanged
   schema and public M3/Argus reader, and actual teardown-phase flush failure/hang
   with original-child fault fixtures. Inherited probe-only fault tests do not by
   themselves exercise the new phase record path.
9. MAJOR read-only final inspection: emergency fallback calls blocking record()
   before and after its nonblocking C1 operation. A concurrent manager mutation can
   therefore strand cleanup outside its original deadline. Add optional nonblocking
   record entry for explicit deadlines, remove the eager status read, and report
   unknown boundary facts if both mutation and observation conflict. Exercise a
   manager lock acquired after the original job snapshot; no renewed deadline or
   optimistic release/reap may be inferred.
