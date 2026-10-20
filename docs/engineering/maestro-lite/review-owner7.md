# Separate read-only original-owner integration review

Same-agent component review, 2026-10-18. Exact first source/tests are archived in
pre-review-v1.tar.gz. The first real chain reached native unfreeze and C1 cleanup;
its final readback assertion failed because the accepted reader uses records().
No independent/full-candidate review or full lifecycle acceptance is claimed.

Findings recorded before successor repair:

1. MINOR test: call the actual accepted reader records() method, not a property.
2. MAJOR: GateConnection must pin original process/socket/latch object identity and
   scope/epoch/lease/artifact fields; a duplicate FD or changed public attribute is
   not original authority. StageSupervisor must likewise pin its original backend.
3. MAJOR: revalidating a durable intent must reject a later outcome for that same
   execution/action, as well as replaced generation/run/context. A retained old
   intent alone cannot revive a terminal action.
4. MAJOR: bind the actual Argus writer's plan/run/domain identity to the permit's
   accepted plan and recheck at use. An exact writer class/run ID alone is insufficient.
   Read-only identity inspection is allowed; no private Argus storage mutation/call.
5. MAJOR: original gate retention failure during pidfd registration must request
   revocation and dispose only acquired local pidfd state. Bootstrap caller retains
   ownership of the actual child; a failed constructor cannot silently strand it.

Keep synchronous kernel/storage bounds, bounded bootstrap/launcher, full helper/
owner-loss, ordinary handle/readiness/restart, U5–U8 and nine-runtime-case gates open.
Native lease expiry is independent of persistence, but no abandoned Python thread
or after-return timeout is a whole caller bound. Public payload excludes private
permit nonce, raw capability/FD/PID and helper credential data. All 24 ML-SR and 18
unvalidated source parents remain in scope.

6. MINOR: require canonical lowercase 32-byte artifact digests; fromhex alone can
   accept whitespace while producing fewer bytes. Artifact provenance remains a
   trusted bootstrap fact, not authenticated operator approval.

Second read-only pass, exact repaired source archived in pre-review-v2:

7. MAJOR: retain the commit's original host operation deadline in its private claim;
   Stage/Arm/Release cannot acquire a later fresh start window from a new deadline.
8. MAJOR: mirror sourceRefs must hash M3's actual public-redacted record projection,
   not an ad hoc subset. Bind original journal/readback identity and use the public
   projection API; never hash or publish its private nonce as public evidence.

Third read-only pass after expanded tests (21 cases):

9. MINOR test findings: the public reader exposes sealed segments, so seal the
   test evidence before readback; use a valid bounded cancellation reason; an empty
   boundary removal proves release/empty, not termination of a nonexistent process.
   These three assertion/input errors explain expanded-first-tests.log (18 pass,
   three fail). Preserve actual cleanup semantics rather than weaken production.
10. MAJOR: cancellation must target the retained original latch even if its public
   alias was replaced. Preserve original host-session identity in GateConnection's
   configuration pin. A public alias substitution must not redirect revocation.

Fourth read-only pass, after the repaired 85-case run and reply-denial expansion:

11. MINOR tests: a 50 ms whole intent window can expire during the genuine M3
    claim before the instrumented flush is reached, and a 150 ms window can expire
    before a claim is registered. Use a generous initial engineering test window,
    then explicitly hold the real flush or wait past the actual retained deadline.
    Assert that flush was entered; distinguish late persistence from earlier expiry.
    No timing threshold is a dissertation protocol value or hard caller bound.

Findings 1–10 repaired; exact pre-repair variants and failed logs retained.

Final separate read-only component pass after finding 11 repair: 28 owner plus
64 legacy admission cases pass. Original source/receipt/channel identity, actual
M3 public projection, original host deadline, public append and flush ordering,
current Stage membership, credential-checked one-use Release and cancellation
were reviewed. No additional component finding was identified. This is same-agent
review, not an independent full-candidate review or acceptance. All full gates
remain open; no ordinary readiness or bounded synchronous I/O claim is made.
