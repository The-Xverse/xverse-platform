# Increment19 review log

Successor of review-affa18.md (findings 393–413; increments 17 and 18 accepted in findings 392
and 411, merged into main in 412 and published in 413). Numbering continues so that no finding ID
is reused with a new meaning. Branch candidate/maestro-lite-affa19-20261021, worktree
/home/jefferson/xverse-platform-worktrees/maestro-lite-affa19-20261021, parent main
557619e0c5a43886e40b16706b329c9aaa5189ed (equal to origin/main after a fresh fetch).

414. Authorization and change specification for increment19 step 1, 2026-10-21, recorded before
    any edit. (a) Author text "go for your propose order of work" in reply to the P3 task
    reconciliation (thesis repository specs/024-maestro-lite-lifecycle/review/
    task-reconciliation-20261020.md, sha256 950cae55…4627, coverage detail 0ff30783…0aa9cf).
    Read as sign-off of the reconciliation and authorization of steps 1–4 of its proposed order:
    (1) T02/T04 test gaps and the expected-table check, (2) DV03–DV06, DV09 and DV10 gaps,
    (3) one full installed-wheel platform run and the DV12 blocking rules, (4) the root-cause
    campaign on the ten unknown causes. Step 5 (design freeze T01, complete review, T07 package)
    still needs the author's decision. Not authorized by that text: task checkbox changes, lane
    activation, M1, factory runs, merges or pushes of main, canonical-note edits, scientific
    claims. (b) Checkout: sparse (non-cone patterns `/*` and
    `!/docs/engineering/maestro-lite/evidence/affa17/`) because the root file system has 11 GB
    free and the excluded directory holds 2.26 GB of retained increment17 evidence. No test reads
    it: the only reference, test_runtime_lane_admission.py, is skipped unless
    MAESTRO_LANE_PROPOSAL is set and is not used in this increment. src/ and tests/ are complete.
    (c) Oracles, read from the design successor ML-DESIGN-2026-10-03-v2 (still DRAFT):
    verification-plan.md (9aca1652…), projection-fixtures.json (a4991bda…), and for the later
    check authority-crash-tables.json (bac7af20…), writer-closure-tables.json (2c985f91…) and
    coverage-expected-tables.json (f914a315…). (d) Step 1 scope. New module
    tests/thesis_lite/maestro/test_preparation_rejections.py; the existing test modules are not
    edited. Expected outcomes authored here before the module is first run (design table code in
    brackets where it differs, because the design names the ML-PROJECTION family and the
    implementation refines it):
    R1 binding realizationClass hybrid -> PreparationError ML-REALIZATION [ML-PROJECTION];
    R2 non-empty faultSchedule -> ML-UNSUPPORTED;
    R3 unbound sink (sink binding removed, design control "unbound-sink") -> a code of the
       ML-PROJECTION family, or an XDL validation/compile rejection before Maestro, recorded as
       observed;
    R4 non-empty action parameters -> ML-UNSUPPORTED;
    R5 actionKind set-parameter (design control "unsupported-action") -> ML-UNSUPPORTED
       [ML-PROJECTION];
    R6 deployment with zero bindings -> ML-PROJECTION family;
    Z  every rejection above and every existing DV01/DV02 rejection (changed digest, rehashed
       forgery, missing prerequisite binding, ambiguous catalog entry, duplicate realization,
       combined cycle, node target, impossible window, missing start step, unexpected command,
       empty provider set) repeated under an effect recorder: zero attempts to open a file,
       start a process, create a socket, lock or thread, or read the ambient clock, and no
       prepared value returned. Pass/fail of Z is per case.
    T04: T1 two simulation time domains -> ML-TIME ("exactly one simulation domain"), or an XDL
    rejection recorded as observed; T2 the stalled-tick-worker control asserts that the run
    returns within its admitted host bound plus a stated margin; T3 a host timeout fires while
    the simulation tick is paused. T2/T3 use the existing owned fixtures; any bound is read from
    the admitted fixture, not widened.
    (e) Expected-table check: a read-only mapping of the nine platform tables
    (affa-, bootstrap-, closure-, outcomes-, provider-, recovery-, scheduler-, teardown-expected.json
    and affa-fresh-context-expectations.json) and the four design tables above onto the tests
    that exercise each case, with a per-case verdict (MATCH, PARTIAL, DIVERGENT, NO_TEST),
    followed by a test that loads every table, pins its digest and checks that each mapped test
    exists. A DIVERGENT case is recorded as a finding; neither table nor test is edited to agree.
    (f) No product change is expected. If a new negative control fails, the failure is
    recorded as a finding before any repair. No full-run driver is live (checked); host load at
    the start was 12.4 (1-minute) with the shared CARLA jobs present.

415. Additions to the step-1 expectations, recorded before test_preparation_rejections.py first
    ran. (a) Design control "original-argus-fixture" (projection-fixtures.json): the accepted
    Argus fixture set, validated and compiled unchanged, must be rejected whole by prepare with
    an ML- code and zero effects; the specific first code is recorded as observed. (b) The
    ambiguous-catalog case runs as its own test because it patches projection.derive_catalog;
    expected ML-CATALOG with zero effects. (c) The effect recorder denies builtins.open,
    Path.open, os.open, os.fork, os.posix_spawn, subprocess.Popen/run, socket.socket,
    threading.Lock/RLock/Thread and time.time/monotonic/time_ns/monotonic_ns during the single
    prepare() call; compilation of the fixture happens before the recorder is armed.

416. First run of test_preparation_rejections.py (focused, environment h interpreter with src on
    PYTHONPATH, TMPDIR on tmpfs): 17 passed, 3 failed. Observed against the finding-414/415
    expectations: R2, R4, R5 and all fourteen Z cases rejected with the expected codes and zero
    recorded effects; the ambiguous-catalog case ML-CATALOG with zero effects; the original
    Argus fixture is rejected whole with ML-UNSUPPORTED ("fault execution belongs to Phase 5")
    and zero effects. Three mismatches, none a product defect: (a) R1 hybrid realization is
    rejected whole with zero effects but one stage earlier than expected, by the accepted
    catalog derivation (ML-CATALOG) rather than by the projection's realization check
    (ML-REALIZATION). The projection branch for hybrid (projection.py, realizationClass not in
    simulated/virtual) is therefore defensive and unreachable through validated XDL; this is
    recorded, not changed. The expected code is corrected to ML-CATALOG citing this finding.
    (b) R3 and R6 failed in the harness, not in Maestro: removing a binding from an already
    normalized resource leaves its profile payload orphaned and the XDL compiler rejects the
    plan (XDL1-PLAN-PROFILE-TARGET-MISMATCH), so the case never reached prepare. Through the
    source-document route (validate_sources, then compile), R3 (sink binding removed) reaches
    Maestro and is rejected with ML-PROJECTION ("step target must resolve one executable
    instance"), matching the design control "unbound-sink". (c) R6, a deployment with zero
    bindings, is rejected by the XDL schema (XDL-SCHEMA-INVALID, "[] should be non-empty"),
    so no plan exists and nothing reaches Maestro. The case becomes its own test asserting the
    XDL rejection; the "zero executable units" stimulus at the Maestro layer remains covered by
    the node-target and duplicate-realization cases. The test edits are confined to the new
    module.

417. T04 expectations, recorded before test_time_context_controls.py first ran. T1 (two
    simulation tick domains): ML-TIME with zero effects, for a second simulation domain that is
    declared but unused, one that is used by a step through a declared time mapping, and a
    single domain whose clock class is logical. A read-only probe of the three variants
    (scratchpad probe_t1.py, before the test was written) already showed ML-TIME for each;
    the expectation of finding 414 is unchanged. T2 (stalled tick worker): the existing
    owned dispatcher fixture of test_actual_tick_worker_stall_returns_incomplete_with_owned_cleanup
    (SIGSTOP of the real tick worker after begin), unchanged admitted schedule (active 4.8 s,
    operation 0.5 s, poll 0.05 s); additionally asserted: driver.run returns no later than its
    own terminal deadline (the second value of ends(driver)) plus a 1.0 s return margin, measured
    on time.monotonic; not execution_succeeded; unit cleanup complete; worker reaped; zero
    workload markers. The 1.0 s margin is a test-side tolerance for the return path under the
    shared host, not a product deadline, and is not added to any admitted bound. T3 (paused
    simulation): the same fixture with the tick sequence held at 0 for 400 admitted pauses
    (poll 0.05 s, so the simulation does not advance before the active end) and active 8 s as in
    the existing paused control; request_limit raised to 2048 only so that the schedule admits the
    longer tick sequence. Expected: the host deadline ends the run while the tick is still 0: not
    execution_succeeded, every step scheduled at tick >= 1 has a non-completed disposition, unit
    cleanup complete, worker reaped, return no later than the terminal deadline plus 1.0 s. If
    the fixture advances ticks faster than the poll interval (so the run completes), T3 is
    recorded as not established by this fixture rather than adjusted to pass.

418. T04 results and a new defect F-08, 2026-10-21 (host load 10–13 with the shared CARLA jobs).
    T1: three parametrized cases pass (ML-TIME, zero effects). T2: the stalled-tick-worker
    control passes and returns 16.24 s before its terminal deadline in each of 7 repeats; the
    terminal deadline of the fixture is generous, so this bound shows only that the run is not
    held open, not how promptly the stall is detected. T3: the paused simulation never advances
    past tick 0 before the active end (65–77 tick pulls of the 400 admitted pauses), every step
    after tick 0 ends blocked, cleanup completes and the run returns 10–12 s before its terminal
    deadline in every repeat, so the DV08 observation "host timeout still fires" holds. One
    expectation of finding 417 was wrong: "worker reaped" after run() applies only when the
    persistence client has failed, because the client belongs to the owner and outlives the run
    (drain() of an open client raises ML-PERSIST-STILL-OPEN by design).
    F-08 (defect, recorded before any repair): the outcome at the active end is nondeterministic.
    Ten instrumented repeats (evidence/affa19/t3-active-end-probe: probe_test.py, run19.sh,
    runs.txt, sha256 64c74a5c…, 539939b9…, c949717e…; the probe module was removed from tests/
    after use): 4 clean ends
    (ML-SCHEDULE-SERVICE-DEADLINE raised by FiniteDispatcher._end before a send, terminal record
    written, client open); 5 ML-PERSIST-TIMEOUT on a tick-complete schedule RPC sent with
    23–85 ms of remaining budget while the same RPC took 42–88 ms in the preceding cycle; 1
    ML-PERSIST-SENDER on a tick RPC sent with 1.9 ms remaining. After the timeout the persistence
    channel is failed (by design: an unanswered request leaves the channel state unknown), every
    later disposition write fails with ML-PERSIST-CHILD and the run has no terminal record. Cause
    as observed: FiniteDispatcher._end returns min(active end, now + operation budget, …) and
    raises only when that end is already in the past, so near the active end it hands out a
    deadline shorter than the worker's normal service time. The run stays fail-closed and
    fabricates nothing, but whether a run ended by its host deadline keeps its terminal record
    depends on where the last tick cycle falls. Relevance beyond T3, a hypothesis only: the same
    code ML-PERSIST-TIMEOUT is the failure of the paused-shared and nonopen-writer cases in run r
    and of the A/B (finding 409), which grew under host load; a longer service time under load
    would widen the window. Not established as their cause. test_time_context_controls.py asserts
    each observed variant exactly (clean branch, or timeout/sender branch with failed client, no
    terminal record and reaped worker), to be tightened to the clean branch when F-08 is
    repaired. The repair is scoped in a later finding with its own expectations; it is a product
    change and goes through review.

419. Two DV02 positives listed NO_TEST by the expected-table mapping (projection-fixtures.json
    discriminating_cases), expectations copied from the design table before the tests first ran.
    D1 flow-only-reversed-steps: step dependsOn removed and step declaration order reversed, the
    source->sink flow kept. Expected: accepted; a flow edge from the source ready node to the
    sink dispatch node; no step edge between start-sink and start-source; static eligibility
    gives start-source first and start-sink only after start-source completes, although
    start-sink is declared first; no cycle. D2 step-only-reversed-instances: the flow made
    self-unit (a second endpoint source-in on source-instance, flow source-out -> source-in) and
    the instance declaration order reversed, the step dependsOn start-source -> start-sink kept.
    Expected: accepted; the dependsOn step edge present; no inter-unit flow edge from the
    self-unit flow; start-source eligible first, start-sink after it; no cycle. If XDL rejects
    the self-unit flow, D2 is recorded as not constructible with the accepted compiler, not
    adjusted. The third NO_TEST projection row (no-payload-mapping) is not attempted: every
    supported phase/action pair of the implementation has a payload mapping, so the stimulus
    cannot be constructed without a product change; it stays NO_TEST.

420. Expected-table check (reconciliation observation 2), 2026-10-21. Method: a read-only
    subagent mapped every row of the 13 tables of finding 414(e) onto the tests that inject its
    condition and read the test bodies; the main session read both DIVERGENT rows and their test
    lines in full, read a random sample of four MATCH rows against the cited lines (all four
    hold), and updated the projection rows for the tests of findings 416 and 419. Result,
    recorded in docs/engineering/maestro-lite/expected-table-trace-20261021.json: 208 rows,
    85 MATCH, 117 PARTIAL, 2 DIVERGENT, 4 NO_TEST. The four design tables are now held as
    byte-identical copies under docs/engineering/maestro-lite/design-oracle/ML-DESIGN-2026-10-03-v2
    (sha256 equal to the thesis-repository originals named in finding 414). New test module
    test_expected_table_trace.py loads all 13 tables, pins each digest, requires every row of
    each declared section to be mapped exactly once by JSON-pointer locator, and checks that every
    cited test function exists; 28 passed, and five injected corruptions (changed digest, dropped
    row, duplicated row, missing test function, stale summary) are each detected. It does not
    re-judge verdicts. DIVERGENT, both between the DRAFT design and the implementation, neither
    hidden: (a) authority-crash-tables CP-10 says zero workload instructions after the epoch bump;
    test_composed_post_release_loss.py:146,222 allows one marker for a storage loss exactly
    before the Release send, a correction declared in the test and in finding 372 that reclassifies
    that window to CP-11 (no storage-liveness check exists between the last revalidation and the
    send). The design table has no row for that window. (b) writer-closure-tables W-01 says an
    early flush/fsync error leaves the writer usable with a bounded abort permitted; the
    implementation, for a persistent fault, never attempts abort and reports usability unknown
    (test_terminal_native_writer_failures.py:26, test_terminal_writer.py:73,77), consistent with
    the stricter reading "abort only after a positive flush"; the one-off fault matches W-01.
    Neither table nor test was edited; both are inputs to the T01 design-freeze reconciliation and
    need an author ruling (amend the design row, or change the implementation). Borderline rows
    for the same ruling: CP-02 (the [False] parameter runs without the harness reservation
    approval, a precondition the row does not state) and AF17 (restart of a prerequisite with
    active dependents is rejected, ML-GENERATION-DEPENDENTS, rather than stopping the dependents).
    NO_TEST: affa INV07 (a labelling invariant, not testable behaviour), projection
    no-payload-mapping (finding 419), coverage missing-normal-outcome-without-disposition and
    generic-complete-missing-ready (the latter is also the DV09 gap scheduled for step 2). The
    PARTIAL majority is mostly unasserted secondary observations (timing words such as "promptly",
    coverage emergency/overall statuses); they are inputs to step 2, not failures.
