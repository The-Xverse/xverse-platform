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

403. Author decision 2026-10-20 ("go with your recommendation") on finding
    394(d): F-02 is implemented natively with option (i). Change specification,
    recorded before any edit:
    (a) Supervisor (bootstrap.c, RUN_BOOTSTRAP build only): at initialisation it
    draws a 32-byte watch key with getrandom; each successful WATCH (kind 4)
    replies (kind 20) with token = HMAC-SHA256(key, "MLWT" || st_dev || st_ino)
    of the retained boundary descriptor in the reply's token field (p+72); at
    the authority's birth (role 4) it passes the key in a sealed memfd as a
    third argument and closes its copy after clone. Python never receives the
    key.
    (b) Authority (run_authority.c): initialize requires the third argument,
    reads exactly 32 bytes from the sealed memfd and closes it; advance_unit
    additionally requires the request's ticket field (p+224) to equal the
    HMAC over the ADVANCE boundary descriptor's st_dev/st_ino, compared with
    CRYPTO_memcmp, and keeps the handle field (p+256) zero. An ADVANCE with no
    or a wrong token is rejected natively, so an unwatched boundary can no
    longer be admitted even if the Python precondition is bypassed.
    (c) Python: affa_protocol.py requires a nonzero ticket on ADVANCE requests
    (ADVANCED replies stay zero); bootstrap.py accepts a nonzero token on v2
    WATCH replies (kind 20, pid 0) and retains it per watched identity;
    affa_client.py checks before sending that an ADVANCE carries the retained
    token of its descriptor (the existing _watched precondition stays);
    run_broker.py puts that token into the ADVANCE frame.
    (d) Tests: the native harness supplies its own sealed key and computes
    tokens as the supervisor would; new native controls show that ADVANCE
    without a token and with the token of a different boundary are REJECTED
    with no generation admitted, and that the correct token is ADVANCED; the
    client test for unwatched boundaries carries a nonzero ticket so it still
    reaches the UNWATCHED check; end-to-end generation tests through the real
    supervisor exercise the whole flow.
    (e) Wire compatibility: AF17 and BS17 packet layouts are unchanged; field
    semantics change for ADVANCE tickets and WATCH reply tokens, and the
    authority's argv gains one argument, so old and new helpers do not
    interoperate (both are built from the same tree in every harness).
    (f) Verification: compile both helpers with the harness flags; source
    phase over the AFFA, bootstrap, generation and composed modules; an
    independent review of the changed bytes; environment g; runtime lane,
    crash-point and lane admission re-runs from a committed tree; full run.

404. F-02 implemented as specified in finding 403, with two Python details found
    while testing and recorded here: the client's expected-reply builder no
    longer copies the request ticket into the expected ADVANCED reply (an
    ADVANCED reply carries no ticket), and test harnesses that build ADVANCE
    frames use a nonzero placeholder ticket that the direct-launch harness
    replaces with its own HMAC and the client-routed harness with the
    supervisor's retained token. Changed bytes (sha256): bootstrap.c 83b10177…,
    run_authority.c 5938cd01…, affa_protocol.py 4c0e8eb0…, bootstrap.py
    48e38bec…, affa_client.py f88a4bc9…, run_broker.py 29ebeba8…; tests
    test_affa_native.py, test_affa_client.py, test_affa_protocol.py changed;
    test_affa_watch_token.py new. Both helpers compile warning-free with the
    harness flags (authority 05314aa505b3…, RUN_BOOTSTRAP supervisor
    500b8b6f2160…; the plain supervisor build is clean too). Source
    phase, candidate src, environment f interpreter: the AFFA native, epoch,
    client, protocol, F-01 and F-02 modules with the run-bootstrap and bootstrap
    modules — 115 passed; twenty generation, run-broker, composed, runtime lane,
    runtime entry/service, launcher-composition, bootstrap-launcher, runtime
    admission and recovery modules that exercise WATCH and ADVANCE through the
    real supervisor — 224 passed, 1 skipped (the lane admission control, by
    design). The F-02 controls observe: correct token ADVANCED and the new
    generation released; missing (zeroed below the protocol layer), foreign
    (the other unit's real boundary) and forged tokens REJECTED with reason 4,
    an empty new boundary and a rejected late Stage. Pending: the independent
    review of these bytes, environment g, runtime lane d, crash-point e, a
    committed checkpoint, proposal d, lane driver f, full run q.

405. Independent review of the F-02 bytes received (separate agent session,
    read-only; `evidence/affa18/helper-change-f02-independent-review-20261020.{json,md}`):
    verdict "F-02 addressed"; 22 PASS, 0 FAIL, 3 NOTE checks; 0 HIGH, 0 MEDIUM,
    3 LOW, 4 NOTE; all six frozen hashes verified. Confirmed: Python holds tokens
    but never the key; the authority recomputes the token from the same open
    descriptor it then admits, before any state change; inode reuse cannot occur
    while the supervisor keeps its watched descriptors open. Dispositions:
    F02R-01 (LOW: the authority is dumpable, so its Python parent could ptrace it
    or read the key fd through /proc, until PR_SET_DUMPABLE(0) at the end of
    initialize) — FIXED next under finding 406 by making the authority
    non-dumpable as the first statement of main; the supervisor holds the key
    from initialisation under the same pattern, so it is made non-dumpable
    first as well. F02R-02 (LOW: no packet-level test of the kind-20 token rule)
    and F02R-03 (LOW: the client's ML-AFFA-WATCH-TOKEN check never exercised) —
    tests added under finding 406. NOTEs recorded without change: F02R-04 a
    token proves the boundary was watched, not that the supervisor still lives;
    after abrupt supervisor death the authority accepts tokens until its lease
    ends (the supervisor's death also ends the run's lease renewal); F02R-05 the
    negative controls' late-Stage rejection is not independent proof of
    non-admission and there is no negative control through a supervisor-born
    authority; F02R-06 finding 403 omits the zero-key, seal and size checks, the
    forged control and the F02R-01/04 caveats, which this finding now records;
    F02R-07 a token is bound to a boundary identity, not to a unit, slot or
    generation.

406. F02R-01..03 addressed (finding 405). Both helpers call
    prctl(PR_SET_DUMPABLE, 0) as the first statement of main, before any secret
    exists in the process (authority: before the key memfd is read; supervisor:
    before the watch key is generated); the later calls in initialize stay.
    run_authority.c 5938cd01… → ffdc632ed58b796031d25eac0dfe739cf3ba151344d91dc60ed4be27cc2a5344,
    bootstrap.c 83b10177… → c1f2885db167852b93d207b1051421e44610efa2f88bfe45309f4a944e8dfe05;
    all three builds warning-free (authority c0c162ea…, RUN_BOOTSTRAP
    supervisor b47d1a01…, plain supervisor). Tests added in
    test_affa_watch_token.py (5880f335…): the packet rule (a v2 kind-20 reply
    must carry a token with pid 0; a WATCH request with a token and any other
    child-less reply with a token are rejected — the request by the general
    token-without-child rule, which precedes the WATCH rule; v1 has no WATCH
    reply), and the client's pre-send check (an ADVANCE whose ticket differs
    from the retained supervisor token raises ML-AFFA-WATCH-TOKEN, nothing is
    sent, the connection is not revoked). Source phase: AFFA native, epoch,
    client, protocol, F-01, F-02, run-bootstrap, bootstrap and bootstrap-value
    modules — 127 passed. Evidence produced before this change (environment g,
    runtime lane d, crash-point e) is superseded for the final bytes.

407. Independent review of the finding-406 delta received (separate agent
    session, read-only; `evidence/affa18/helper-change-dumpable-independent-review-20261020.{json,md}`):
    verdict "partially addressed"; 7 PASS, 1 FAIL, 2 NOTE checks; 0 HIGH, 0
    MEDIUM, 1 LOW, 3 NOTE; removing the two added lines reproduces the
    previously reviewed blobs exactly; binary hashes of finding 406 reproduced.
    The supervisor side is closed (non-dumpable before the key is generated).
    F02D-01 (LOW, authority): exec of a readable image makes the authority
    dumpable again from execveat until main, while it already holds the
    inherited key memfd, so a hostile same-uid process (including the Python
    peer, which controls the boundary's thaw timing) could read the key in that
    window. Disposition: RECORDED AS A NON-CLAIM, no helper change. Key
    confidentiality against a hostile same-uid peer is not claimed; the
    containment design never defended against a hostile same-uid owner, which
    already owns every boundary's cgroup.freeze and can signal every child
    directly. F-02 is claimed only against a buggy, regressed or bypassed Python
    precondition, which it closes natively. The reviewer's alternative (an
    owner-unreadable authority image enforced by the supervisor, so exec starts
    non-dumpable) is recorded as an option for a later hardening increment.
    F02D-02 (NOTE): the comment at run_authority.c:510 and finding 406 say
    "before any secret exists in this process"; precisely, the key bytes reach
    memory only after the process is non-dumpable, while the key memfd is
    already open from exec — this finding corrects the record; the comment is
    left unchanged to avoid another helper-byte change for wording alone and
    will be corrected with the next helper change. F02D-03 (NOTE): the packet
    test now pins the v1 rejection to ML-BOOT-WIRE-HEADER and adds a kind-20
    reply naming a child, rejected by the WATCH rule (test module re-run: 6
    passed). F02D-04 confirms the supervisor closure. F-02 stands as addressed
    for its stated scope.

408. Checkpoint 18-4 e290ce78c (the F-02 change, findings 403-407) and its
    lane admission evidence. Proposal `evidence/affa18/lane-admission-proposal-20261020d.json`
    (sha256 7b454c1d…9edf) is built from e290ce78c with a clean src: helper
    digests from runtime lane e (authority c0c162ea…, RUN_BOOTSTRAP supervisor
    b47d1a01…), composed-case indexes from crash-point f, environment h (wheel
    eca0939d… of this tree), verification review = the F-02 review; facility
    digest f19d534a…, readiness digest 4056f582…, execution_approved false,
    five blocking findings (the F-02 deferral entry is removed because F-02 is
    implemented; ten unknown causes in two entries, lane activation not
    approved, M1 not admitted, increment18 acceptance open). Lane admission
    driver f (`lane-admission-20261020f/`, receipt 0551f2c5…f212): source 23
    passed, installed wheel 23 passed. Full-run driver q stopped at its
    collection preflight (2104 collected against a declared 2102, the six new
    F-02 tests); no test ran; its directory is retained as an aborted preflight
    and run r (driver verify-platform-regression-20261020r.py, 2104) is live.

409. Terminal read-only review of run r (driver verify-platform-regression-20261020r.py,
    pytest 3801780, environment h, e290ce78c, 2104 collected, TMPDIR on tmpfs):
    returncode 1, 3489.36 s, **3 failed / 2100 passed / 1 skipped**, no outer timeout,
    frozen inputs unchanged, descendants gone. Receipt 68a937cb…505d, log 381cb93d…0cdc,
    triage `failure-triage.json` 6cf8b857…bd88, correlation
    `stall-fsync-correlation.json` b03e62a6…bdd8. Run r is not a clean run.
    (a) Failures: test_shared_dispatcher::test_paused_shared_ticks_renew_both_original_
    leases_and_observe_health (ML-PERSIST-TIMEOUT, health_scans 4, lease_renewals 8);
    test_terminal_faults::test_actual_nonopen_writer_close_requires_original_report_
    receipt[True-closed] (ML-PERSIST-TIMEOUT, renewals 2); and the nested Argus case, whose
    child reports 2 failed / 1817 passed / 1 skipped (test_dispatcher::test_paused_ticks_
    still_service_host_health_and_original_leases; test_launcher_composition::test_actual_
    original_startup_through_terminal_and_helper_closure[closed]; tail only). All six F-02
    controls (test_affa_watch_token.py) and the F-01 control passed.
    (b) Host condition: a CARLA 0.9.16 simulator of an unrelated project
    (CarlaUE4-Linux-Shipping, PID 3540156, ~116 % CPU, 3 GB RSS) started at 14:22:03 +0100,
    16 min before run r started (14:38:22), and was still running at its end, alongside
    live factory collectors; load average 7.4/9.6/9.9 on 32 CPUs at the receipt. Elapsed
    time of the full run has risen monotonically m 2409 s, o 2735 s, p 3068 s, r 3490 s;
    operation stalls > 0.5 s (same correlation tool) were 7–21 in clean runs i–o, 33 in p and
    65 in r, with 0 fsync spikes in r (13 951 probe samples, worst 0.0001 s), so the storage
    hypothesis does not apply to r. The process is not ours and was not stopped.
    (c) Discrimination (`evidence/affa18/ab-load-discrimination-20261020a.py` dc64d985…77fe,
    receipt 03462b0d…7112): the four failing node IDs, ten interleaved iterations per arm,
    each from a `git archive` snapshot on tmpfs with driver r's selected environment, arm A =
    d52683ad (pre-F-02, environment f, run p's configuration), arm B = e290ce78c (F-02,
    environment h). test_paused_shared_ticks failed **5/10 in A and 5/10 in B**; the other
    three failed 0/10 in each arm. Both diagnostics occur in the pre-F-02 arm (A: 2
    ML-PERSIST-TIMEOUT, 3 ML-SCHEDULE-TEARDOWN-INCOMPLETE; B: 5
    ML-SCHEDULE-TEARDOWN-INCOMPLETE). The same case passed in all nine full runs i–p before
    the load appeared. Conclusion: the F-02 change is not the discriminator (identical
    failure rate on the pre-F-02 bytes under the same load); a host-contention cause is
    supported, not proven (no run after the load ended). The paused-shared fixture fails at
    50 % under moderate load in isolation, which is a thin-margin observation for
    ML-CAPA-364, not a product defect claim; fixture margins remain capped (findings 362/367).
    (d) Disposition: run r is retained as a failed run under a changed host condition and as
    a prevention observation; it does not count as the clean full run owed on the F-02
    bytes. ML-CAPA-381-F02 may still move to FIX_CANDIDATE on its native controls (passed
    inside run r, lane admission f, runtime lane e, crash-point f); effectiveness remains
    NOT_DEMONSTRATED. A clean full run on e290ce78c is owed once the host is quiet; no
    product or fixture edit follows from this finding.

410. Terminal read-only review of run s (driver verify-platform-regression-20261020s.py
    6589301d…a9ba, pytest 2496450, environment h, 2104 collected, TMPDIR on tmpfs; HEAD
    b1dc99792, whose src and tests are identical to e290ce78c): returncode 0, 3198.23 s,
    **2103 passed / 1 skipped / 0 failed**, the nested Argus child clean, no outer timeout,
    frozen inputs unchanged, descendants gone. Receipt bbabbbb3…9b16, log 654f67f0…d80e,
    triage eaa82ab9…db4, correlation edd489d8…1b48. All six F-02 controls and the F-01
    control passed. This is the first clean full run on the F-02 bytes. It was launched on
    the author's go ("safe to go") with the finding-409 host load still present and heavier:
    the driver now records the host at launch (`host_condition_at_launch`: load average
    7.58/7.52/7.56; the CARLA server PID 3540156 at ~111 % CPU plus an unrelated CARLA render
    job PID 1615721 at ~279 %), and both were still running at the receipt. Operation stalls
    > 0.5 s: 61 (r: 65; clean runs i–o: 7–21); 0 fsync spikes (12 787 samples, worst
    0.0001 s). Reading together with 409: at comparable stall levels run r failed 3 and run s
    failed none, which is consistent with the A/B (the paused-shared case fails
    intermittently, about half the time in isolation under this load) and not with a
    deterministic regression. Host contention raises the failure probability of the
    thin-margin fixtures; it is still not proven as a cause, and the margin observation stays
    on ML-CAPA-364. Run s is a prevention observation for 222, 357, 359-CHILD, 364, 374, 379,
    381-F01, 381-F02 and 389; effectiveness remains NOT_DEMONSTRATED everywhere (one clean run
    is not a demonstration), and no state, cause or product change follows. The owed clean
    full run on the F-02 bytes is discharged. Increment18 remains not accepted.

411. Author acceptance of increment18, 2026-10-20 ("go with your proposal", to the three
    recommendations: (1) accept increment18 with an acceptance record on the finding-392
    pattern carrying the open items; (2) hold the merges of increments 17/18 into main as a
    separate decision; (3) defer the optional F02D-01 hardening and the F-05 wire revision to a
    later increment). Recorded terms, which bound every later citation of this acceptance:
    (a) scope: the Maestro Lite increment18 candidate as committed in checkpoints 7abdb9dc0
    (F-01), d52683ad5, 18547fd6c, e290ce78c (F-02), b1dc99792 and 3bee8fb9d on
    candidate/maestro-lite-affa18-20261020 (parent bdf7b29cc, increment17 accepted), accepted
    as an engineering increment; its product changes are the native F-01 refreeze/close-budget
    correction and the native F-02 watch proof. (b) basis: clean full runs o (tmpfs, F-01
    bytes), p (ext4 reference, quiet host, F-01 bytes) and s (tmpfs, F-02 bytes, under an
    unrelated host load); run r (3 failed under that load) retained with the A/B showing F-02
    is not the discriminator (finding 409); independent reviews of every product change
    (F-01, two-pass, F-02, dumpable delta; 0 HIGH, 0 MEDIUM open); runtime lane e, crash-point
    f and lane admission f on the final bytes; CAPA chain through capa-20261020-affa18-run-s.
    No separate whole-increment review was performed beyond the per-change reviews, which
    together cover every product byte changed in increment18. (c) carried open: the ten CAPA
    records with unknown cause (135, 286, 287, 318, 324, 330, 331, 332, 337, 359);
    effectiveness NOT_DEMONSTRATED for every record, including 381-F01/F02 (the F-01 reason-6
    and bounded-wait branches are not exercised); F02D-01 as a non-claim (no key
    confidentiality against a hostile same-uid peer) with the owner-unreadable authority image
    as deferred hardening; the run_authority.c:510 comment correction (F02D-02) deferred to the
    next helper change; F-05 (distinct release-timeout reason, wire revision) deferred; F-07
    unchanged by design; the thin-margin paused-shared fixture under host load (ML-CAPA-364
    observation); the tmpfs harness as a declared fidelity choice. (d) not covered: lane
    activation, M1 admission, the merges of increments 17 and 18 into
    /home/jefferson/xverse-platform main, the remaining 024 scope, factory runs, canonical-note
    edits and any scientific claim. The candidate branch remains pushed to origin as a backup
    branch (no merge, no pull request).
