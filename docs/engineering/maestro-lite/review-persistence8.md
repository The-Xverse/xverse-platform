# Separate read-only persistence isolation review

Same-agent component review, 18 October 2026. First source/test candidate archived
in pre-review-v1. Actual isolated M3/Argus-to-native Release, original C1 cleanup,
Abort and worker reap succeeded; final public-reader assertion addressed wrong root.
Legacy owner tests pass (28). No independent full-candidate review is claimed.

Findings recorded before successor repair:

1. MINOR test: EvidenceStore uses the exact supplied root, not root/run_id. Use its
   accepted root and dictionary manifest contracts for offline readback; never infer successful evidence from
   an empty read of a nonexistent directory.
2. MAJOR: initialization must recheck the original request deadline before/after
   validation and every journal/writer creation step. A late returned storage call
   may leave partial evidence, but must not start a subsequent storage operation.
3. MAJOR: client commit must mark an attempt only after acquiring its nonblocking
   RPC mutation lock. A conflicting request must not burn an unrelated unit's attempt
   before any dispatch. Preserve one attempt once an actual dispatch is admitted.
4. MAJOR: lost original wait ownership during drain must yield an explicit unresolved
   retained-identity observation, never a fabricated reap or an unclassified exception.

Review boundaries: private sealed input is not author approval; actual helper pins,
creation/thread lifetime and inherited-FD admission remain trusted bootstrap facts.
PDEATHSIG is a best-effort parent-thread guard, not full owner-loss/kernel-stall proof.
Complete lifecycle, nine runtime cases, all source/acceptance gates remain open.

Second read-only pass after the 27-case persistence expansion:

5. MAJOR evidence precision: distinguish client-confirmed reaping, test-bootstrap
   reaping after constructor rejection and the deliberately violated exclusive-wait
   case. A true overall child-reaped flag must not silently imply that every client
   proved its own wait ownership. Record exact drain diagnostics and external local
   pidfd disposal separately in the final harness receipts.

The private input scope does not authenticate an executable/environment. Actual
helper artifact/FD admission and creation remain external trusted bootstrap facts;
no full M1 or process-run readiness follows from this component.

Final separate read-only component pass: 119 focused persistence/local-owner/legacy
admission tests pass. Findings 1–4 are repaired in the product/test successor;
finding 5 is repaired in the receipt schema and audited by the final verifier.
Reviewed original-child credential/pidfd/channel authority, sealed input/XDL/permit
validation before effects, one-writer ownership, every initialization checkpoint,
shared actual M3/Argus intent/flush sequence, fresh bounded revalidation, original
deadline and receipt identity, no supervisor-side storage I/O, cancellation and
exact-child TERM/KILL/reap/unresolved paths. No additional component finding was
identified. Full source/wheel regressions remain required for this exact candidate.
This is same-agent review; independent full review/acceptance remain open.

Third read-only pass after v1 full regression (966 plus 24 subtests, 387 wheel):

6. MAJOR: successful Abort must close the shared start latch. Worker loss discovered
   by a pre-dispatch availability check must likewise fail closed, rather than only
   rejecting the current method while leaving that latch open. Original-holder/fork
   rejection must occur before any signal/cancel effect, and ordinary cancellation
   must still leave a healthy idle owner available for Abort. Preserve the entire
   exact v1 source/evidence in pre-repair-v2 before changing code. Rebuild the wheel
   and repeat full/installed regression for the successor.

Successor v2: finding 6 is repaired. Successful Abort cancels the original shared
latch; genuine child-loss at availability closes it, while holder/fork rejection
occurs before revocation effects and healthy idle cancellation still allows Abort.
All 29 isolated persistence cases pass, including new actual Abort/child-loss cases.
Separate read-only successor review found no additional component issue. Full
source/wheel regression is repeated for this product change; no v1 green result
is promoted as v2 verification. Independent full review/whole runtime gates stay open.
