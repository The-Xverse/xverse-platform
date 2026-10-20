# Increment18 review log

Successor of review-affa17.md (findings 1–392, increment17 accepted in finding 392). Numbering
continues so that no finding ID is reused with a new meaning. Branch
candidate/maestro-lite-affa18-20261020, worktree
/home/jefferson/xverse-platform-worktrees/maestro-lite-affa18-20261020, parent bdf7b29cc.

393. Observation on the accepted increment17 evidence (recorded here, the
    increment17 records are not rewritten). The installed-wheel phase of the
    lane admission drivers b and c (findings 384 and 389) and of every earlier
    two-phase driver ran the candidate wheel e1a5119a…, built on 2026-10-19 in
    integrated-maestro-20261019b and installed into environment d; it predates
    the dispatcher changes of findings 379 and 389 (installed dispatcher.py
    ae9c5c35… versus candidate ebfd6a84…). The full platform runs i, j, l and m
    set PYTHONPATH to the candidate src and recorded the candidate dispatcher
    hash in their frozen manifests, so the source-level claims stand; the lane
    admission, F-01 and F-02 modules do not reach the changed terminal-section
    statements. Consequence: "installed wheel N passed" in those findings means
    the 2026-10-19 wheel, not a wheel of the accepted checkpoints. Increment18
    builds a fresh wheel from its own tree (environment e) before any
    installed-wheel claim. Not detected by the independent review of finding 386.

394. Change specification for increment18 step 1 (native helper strengthening,
    plan agreed by the author with the acceptance of finding 392), recorded
    before any edit. Scope decided from the source: (a) F-01, implemented:
    run_authority.c freeze_all issues the cgroup.freeze write for every live
    generation regardless of the remaining budget and bounds only the wait for
    frozen==1; close_authority on the rejection path and on CANCEL uses an
    independent close budget min(generation, now + 2 s) instead of the
    request's own deadline. Wire format unchanged: REJECTED keeps state 0 and a
    reason in 1..7, which affa_protocol.py:108 enforces. (b) F-05, deferred: a
    distinct RELEASE_TIMEOUT reason and a freeze mask on REJECTED change the
    AF17 wire contract (affa_protocol.py:87 bounds the reason to 0..7 and
    rejects a nonzero state on REJECTED), so they need a protocol revision with
    its own change-spec. (c) F-07, no change, rationale recorded: the authority
    stays alive after CANCEL to serve cleanup-only STOP/RETIRE/QUERY, and a
    closed authority cannot thaw (RELEASE is the only '0' writer and requires
    enabled(), which requires !closed); killing it inside terminal_fence would
    remove the waits the original-pidfd-waits property relies on. The
    supervisor cannot observe the authority's closed state natively, so the
    precondition stays the Python check bootstrap.py:_service_terminal (a
    CANCELLED receipt or observed authority death). (d) F-02, deferred with
    design options: a native watch proof needs the authority to verify a fact
    only the supervisor holds; options are (i) a supervisor-issued WATCH token
    under a secret shared at birth between supervisor and authority (the
    supervisor births the authority, so the secret can travel in the sealed
    authority input without Python seeing it only if the supervisor generates
    it, which changes bootstrap.c's birth path and the AC17 config), or (ii)
    routing ADVANCE boundary descriptors through the supervisor, which then
    forwards them to the authority on a new supervisor–authority channel. Both
    change two helpers and the Python client; an author choice between them is
    requested. (e) Verification plan: compile with the harness flags; native and
    client modules plus the F-01 control in the source phase; the F-01 control
    additionally asserts that the authority itself left cgroup.freeze at "1"
    after the REJECTED reply (the pre-change helper leaves "0"); a fresh
    independent review of the changed bytes; environment e with a wheel built
    from this tree; runtime lane re-run (new authority binary digest), new lane
    admission proposal and lane driver; full platform run n.

395. F-01 implemented as specified in finding 394, with one addition stated
    here: on the rejection path the REJECTED reply now carries reason
    FREEZE_FAILED (6) instead of PROTOCOL (4) when the refreeze could not be
    confirmed within the close budget; 6 is inside the 1..7 range that
    affa_protocol.py accepts, so the wire contract is unchanged. Helper source
    run_authority.c 2a2ee8306a7f… → 7fde44db52c661d7c27b21986ca63e7185cab40d824c74869dd0c0a1c2acece0
    (6 insertions, 3 deletions); compiled with the harness flags (cc 11.4.0,
    -std=c11 -O2 -Wall -Wextra -Werror -lcrypto) to 40fa39ee34d9…dcbf. Source
    phase, candidate src: test_affa_release_timeout_fence, test_affa_native,
    test_affa_client, test_affa_epoch, test_affa_protocol — 73 passed. The F-01
    control now also asserts that the authority itself left the unit's
    cgroup.freeze at "1" after the REJECTED reply (observed "1", reason 4,
    pre-fence member present, no marker). Negative check: the same control
    against the increment17 helper (PYTHONPATH = the increment17 src, helper
    source 2a2ee830…) fails exactly that assertion ("authority left the unit
    thawed after a rejected release"), so the control discriminates the change.
    Remaining before the increment18 step-1 evidence is complete: the fresh
    independent review of the changed bytes, environment e with a wheel of this
    tree, the runtime lane re-run, a lane admission proposal for the new
    authority digest, and full run n.

396. Independent review of the F-01 change received (separate agent session,
    read-only; record `evidence/affa18/helper-change-f01-independent-review-20261020.{json,md}`):
    verdict "F-01 addressed", 0 HIGH, 0 MEDIUM, 3 LOW, 5 NOTE; both helper
    hashes verified; the binary 40fa39ee… reproduced from the source. Wording
    correction accepted: the 1..7 reason bound is affa_protocol.py:87; line 108
    requires a nonzero reason and state 0 on REJECTED. Dispositions:
    F01R-01 (a slow freeze can now delay the CANCEL or REJECTED reply past the
    caller's receive deadline; run_broker.py:884 gives CANCEL at most 1 s while
    the helper may wait up to 2 s) — recorded as a deliberate, conservative
    behaviour change: the client then treats the exchange as uncertain and
    kills the authority instead of recording CANCELLED; the reply budget is not
    shortened, because shortening it would reintroduce the skipped-wait
    defect. F01R-02 (freeze_all writes and waits unit by unit, so one slow
    unit delays later units' writes and units reached after the budget are
    reported unfrozen without being checked) — FIXED next under finding 397 by
    a two-pass freeze: every live generation's write first, then one bounded
    wait over all pending units in which each unit is checked at least once.
    F01R-03 (the earlier review's suggestion to retry pending freezes while the
    authority is closed) — recorded as DEFERRED to the protocol revision of
    finding 394(b): a retry loop changes the closed loop's poll timing and the
    supervisor already freezes watched leaves on authority loss. The five
    NOTEs are recorded in the review files and carry no change. Run n
    (driver verify-platform-regression-20261020n.py) was started on the
    pre-397 bytes and stopped deliberately after 251 passed when this review
    arrived; its directory is retained as aborted evidence and is not cited as
    a result.

397. F01R-02 fixed (finding 396): freeze_all is two-pass — every live
    generation's cgroup.freeze write is issued first (never skipped for an
    elapsed budget), then one bounded wait over all pending units in which each
    unit is checked at least once even when the budget has already elapsed;
    any unit still pending sets freeze_failed. run_authority.c 7fde44db… →
    b29a5239345354c4758f22203c7d38d557596bb2d743e826fa89825bdd60a09f (net
    against increment17: 18 insertions, 10 deletions); harness-flag build
    17f2476a2d41…c4af5, warning-free. The F-01 control's docstring now states
    the increment17 and increment18 behaviour and that the reason-6 and
    bounded-wait branches are not reached (review NOTE). Source phase,
    candidate src: AFFA native/client/epoch/protocol modules, the F-01 control,
    the composed authority interruptions and the runtime lane module — 90
    passed; the control again observes REJECTED, the unit's cgroup.freeze at
    "1" and no marker. Next: an independent review of the two-pass bytes,
    environment f (wheel of this tree), runtime lane and crash-point re-runs,
    the lane admission proposal and driver, full run o. Evidence produced
    against 7fde44db (environment e, runtime-lane-20261020b,
    crash-matrix-20261020c) is retained and superseded, not cited for the
    final bytes.

398. Independent review of the two-pass bytes received (separate agent session,
    read-only; record `evidence/affa18/helper-change-twopass-independent-review-20261020.{json,md}`,
    reviewing the full diff against HEAD): verdict "F-01 and F01R-02 addressed";
    23 checks, 19 PASS, 0 FAIL, 4 NOTE; 0 HIGH, 0 MEDIUM, 1 LOW, 5 NOTE; both
    hashes verified; build reproduces 17f2476a…. Disposition of TPR-01 (LOW):
    freeze_failed is never cleared, so reason FREEZE_FAILED (6) on a REJECTED
    or CANCELLED reply means that a freeze failed at some point in the
    authority's life, including the current close, not only in the current
    close as finding 395 says; the precise meaning is recorded here and the
    code is unchanged because the effect is conservative (run_broker.py:902
    maps it to ML-RUN-FREEZE-UNRESOLVED). NOTEs TPR-02..06 (a generation
    removed after its write stays pending until the budget ends; a unit whose
    write fails is not retried; clock failure leaves the wait unbounded and
    busy-spins after parent death, as in HEAD; the rejection-path confirmation
    window can be shorter than in HEAD; the close-budget formula appears three
    times) are recorded without change and join F01R-03 as inputs to the
    protocol revision of finding 394(b). Findings 394, 396 and 397 and the
    deferrals were found accurate. Run o, started on these bytes, stays valid.

399. Lane admission proposal b (`evidence/affa18/lane-admission-proposal-20261020b.json`,
    sha256 85fa8d65…852c) is SUPERSEDED before use: its implementation pin is
    `git archive HEAD src/xverse/maestro`, and HEAD is still the increment17
    checkpoint bdf7b29cc, so the pin does not cover the uncommitted
    run_authority.c change that its helper digests (17f2476a…) describe. The
    builder's method is correct only for a committed tree. Order adopted: after
    a clean run o, commit the increment18 change as checkpoint 18-1, then build
    proposal c from that HEAD and run lane admission driver e against it. No
    lane driver was run against proposal b. Proposal b is retained, not cited.

400. Terminal read-only review of run o (pytest 2167596, environment f = wheel
    d10f8619… of this tree, TMPDIR on tmpfs, 2098 collected; snapshot = the
    accepted increment17 checkpoint bdf7b29cc plus run_authority.c b29a5239…
    and the strengthened F-01 control): returncode 0, 2735.16 s, **2097
    passed, 1 skipped, 0 failed**, 24 subtests passed, frozen inputs
    unchanged. Receipt 2d7b2360…25a9; log c819fb75…8ecb; triage 79cab5b5…e0a5
    (0 failures). The F-01 control and every AFFA, composed-authority and
    runtime lane case pass inside the whole suite; nested child passed
    completely; probe 10934 samples, 0 spikes; GC 60, max 0.059 s; 21
    durable-write stalls, none with a spike. Elapsed time is about 5 minutes
    longer than runs l and m on the same harness; no failure or expiry is
    associated with it and no cause is claimed. Next: checkpoint 18-1 commit,
    proposal c from that commit, lane admission driver e, CAPA successor.

401. Lane admission proposal c and lane driver e (finding 399 order). Proposal
    `evidence/affa18/lane-admission-proposal-20261020c.json` (sha256
    a8eefbb6…1482) is built from checkpoint 18-1 7abdb9dc0 with a clean src
    (guard added to the builder): helper digests from runtime lane c
    (authority 17f2476a…), composed-case indexes from crash-point d,
    environment f, implementation pin = git archive of src/xverse/maestro at
    7abdb9dc0, verification review = the two-pass review; facility digest
    097dd735…, readiness digest 11641661…, execution_approved false, six
    blocking findings (ten unknown causes in two entries, lane activation not
    approved, M1 not admitted, increment18 acceptance open, F-02 native
    deferred). Lane driver e (`lane-admission-20261020e/`, receipt
    68b9ad66…6fb5): source 23 passed, installed wheel 23 passed, the wheel
    phase on environment f's wheel of this tree (closing the finding-393 gap
    for these modules); preflight accepts the real pins read-only, the service
    refuses with READINESS-BLOCKED, and the compiled helpers equal the lane
    run's binaries. Not M1, not lane activation, not acceptance.

402. Terminal read-only review of run p, the persistent-media reference run of
    disposition d on checkpoint 18-2 (pytest 2714672, environment f, session
    TMPDIR, private basetemp and probe on the ext4 root, which stood at 94
    percent at launch; 2098 collected): returncode 0, 3067.62 s, **2097
    passed, 1 skipped, 0 failed**, 24 subtests passed, frozen inputs unchanged.
    Receipt b10eb61a…bbc3; log 865a7bff…f05b; triage da6d75b0…352c (0
    failures). First clean full run on persistent media in increments 17–18.
    Bounded reading: the host condition that run k exposed did not occur —
    probe 11659 samples, 0 spikes over 150 ms, worst 0.0533 s (run k: 9 spikes,
    worst 1.18 s); 33 durable-write stalls over the correlator threshold, none
    coincident with a spike; GC 59, max 0.055 s. The run therefore shows that
    the increment18 bytes pass on persistent media under a quiet host; it does
    not exercise the stall class that ML-CAPA-389 and ML-CAPA-379 target, whose
    effectiveness stays NOT_DEMONSTRATED. Elapsed time is about 5.5 minutes
    longer than run o on tmpfs, consistent with persistent-media writes.
