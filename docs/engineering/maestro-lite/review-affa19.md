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

421. Step-2 plan, recorded before any step-2 test is written (checkpoint 19-1 cc8818460). Gap
    list from the coverage detail (0ff30783…): DV03 6 PARTIAL, DV04 5 PARTIAL, DV05 4 PARTIAL,
    DV06 3 PARTIAL, DV09 6 (5 PARTIAL, 1 NOT_FOUND), DV10 5 (3 PARTIAL, 2 NOT_FOUND), 29 in all.
    Order: (1) DV09 coverage-assessor controls (drop only ready, drop only intent, duplicate
    generation record, generic Argus complete with missing lifecycle ready, explicit row-by-row
    provisional/offline agreement); (2) DV10 writer/journal faults (Argus open failure, disk-full
    by an injected ENOSPC at the write call, M3 outcome and stop write errors injected into the
    write itself, every report write failing); (3) DV04 start-step dispositions after readiness
    loss, asserted together with block and teardown; (4) DV03 permit/approval controls observed
    on the Release path; (5) DV05/DV06 real-process gaps (elapsed bound on a never-returning
    probe, a catalog workload that ignores TERM, a single dropped Cancel, a hanging C1 cleanup,
    cancel during restart quiescence). Each stimulus gets its expected outcome recorded in a
    finding before its first run; a failing new control is a finding, and a product change
    follows only from such a failure, with its own scope finding and review. Adjustment to the
    proposed order of work: the F-08 repair (ML-CAPA-418) and any step-2 product change come
    before the full installed-wheel platform run (step 3), so that one run exercises every
    product change of the increment; the root-cause campaign (step 4) proceeds after that run.
    Items that need a facility the owned fixtures do not have are recorded as not constructible
    rather than approximated.

422. DV09 expectations, recorded before test_coverage_dv09.py first ran. Fixture: the existing
    test_coverage.Fixture (synthetic observations written through the accepted M3 journal and
    Argus writer APIs), design rows from coverage-expected-tables.json. E1 drop only the ready
    annotation of unit a: universe of obligation ids unchanged; row ready (a, g1) status
    missing; normalRecordStatus incomplete; overallStatus incomplete. E2 drop only the intent
    annotation of unit a: universe unchanged; row intent (a, g1) not satisfied (missing, or
    conflicting/unverifiable because the issued record's cause dangles, recorded as observed);
    normalRecordStatus not complete; overallStatus incomplete or unverifiable. E3 duplicate the
    broker generation record of (a, g1) in the retained broker export: never a complete result;
    either a CoverageError at assessment or a report whose normalRecordStatus is not complete,
    recorded as observed. E4 design row generic-complete-missing-ready: a run whose ready
    annotation for unit a is never written, closed normally through the accepted writer; the
    accepted Argus reader reports assessed evidence status complete with no diagnostics, while
    verify_closed reports row ready (a, g1) missing, normalRecordStatus incomplete and
    overallStatus incomplete (a complete generic assessment never promotes lifecycle coverage).
    E5 explicit provisional/offline agreement: for the nominal fixture closed normally, the
    (obligationId, unitId, generation, status) tuples of the pre-closure provisional report equal
    those of the closed recomputation row by row, normalRecordStatus is complete in both, and
    only the closed assessment reports overallStatus complete.

423. DV09 first run: 4 passed, 1 failed. E1 as expected (ready missing, incomplete). E2 observed
    intent (a, g1) missing, normalRecordStatus and overallStatus incomplete. E3 observed a report,
    not a CoverageError: normalRecordStatus and overallStatus incomplete. E4 as expected: the
    accepted Argus reader reports assessed evidence status complete with no diagnostics while the
    closed lifecycle recomputation reports ready (a, g1) missing and overall incomplete, matching
    the design row generic-complete-missing-ready (the DV09 NOT_FOUND item). E5 failed on an
    expectation error, not a product defect: the closed recomputation has exactly one row more
    than the provisional report, ob.artifact.<sha256("lifecycle-coverage.json")>, the coverage
    report's own artifact, which exists only after the report is published and indexed (the
    provisional report excludes its own artifact by design, as test_coverage already asserts).
    E5 is corrected to: the closed rows equal the provisional rows plus exactly that one report
    artifact row, satisfied.

424. DV10 native storage-fault expectations, recorded before test_native_storage_faults.py first
    ran. Mechanism: the existing owned facility of ADR-ML3-WRITER-FAULT-0001 (a copy of the
    original bootstrap source whose role3 child alone receives a sealed LD_PRELOAD image; all
    other roles keep the empty environment; the production bootstrap.c is not changed), with a
    new owned interposer owned_storage_fault.c. It returns -1 with errno ENOSPC (28) from write()
    on one exact public path once armed, persistently, without calling the kernel; every other
    descriptor passes through. This simulates a full file system at the write call, it is not a
    full file system. The existing owned_writer_stream_fault.c is not changed. Cases on the
    scheduled two-unit lazy stack of test_terminal_runtime (collection and terminal report
    admitted): C0 injection never armed: as in the existing loader-only control, the run
    succeeds, the terminal record is written and the closed recomputation is complete (harness
    control). C1 Argus disk full during the run: target argus/events.jsonl, armed immediately
    before the first annotation whose action is ready. C2 M3 outcome write failure: target the M3
    journal file, armed immediately before the first M3 append of kind outcome. C3 M3 stop write
    failure: target the M3 journal file, armed immediately before the first M3 append with status
    stopped. Expected for C1–C3: the run does not succeed; the failing worker request is reported
    (persistence client failed or an explicit storage diagnostic); no workload marker for any unit
    whose Release would follow the failure (C1, C2: the dependent sink is never released; C3: both
    units had started, so markers may exist); the M3 journal never contains a record for the
    failed append (C2: no outcome record for the first unit; C3: no stopped record), and the Argus
    reader does not report the run complete; the durable manifest is not closed by inference
    (writerState open or failed, never closed after a failed append); RunClosure.close with the
    original authority completes cleanup (cleanup_complete, root reaped, every helper reaped,
    every boundary empty and released) without a writer replay; the closed recomputation is not
    complete. C4 Argus open failure: target argus/events.jsonl armed at library load, so the
    first write of open_run fails: building the scheduled stack raises before any Release, no
    workload marker exists, recorded as observed (exception type, whether helpers are reaped).
    Any deviation is recorded as a finding before a change.

425. DV10 first run (C0 separately: passed, the harness completes a normal run with complete
    closed recomputation and no injected write). C4 passed: building the stack raises
    PersistenceError ML-PERSIST-ACK after 1.0 s, three ENOSPC writes were injected into
    argus/events.jsonl during open_run, and no workload marker exists. C1–C3 matched every
    expectation of finding 424 up to the closure step: not succeeded, client failed, three
    injected ENOSPC writes without a kernel call; C1 (Argus full at the source's ready
    annotation) ML-PERSIST-ACK, source marker only, the dependent sink never released; C2 (M3
    outcome write) ML-PERSIST-ACK, source marker only, the M3 journal holds only the source's
    intent and staged records and no outcome record; C3 (M3 stop write) diagnostic
    ML-SCHEDULE-TEARDOWN-INCOMPLETE, both markers (both units had started), no stopped record;
    the durable manifest in each case is open or failed, never closed. They then failed on the
    test's own guard: the guard copied from the post-terminal writer test forbids every
    persistence RPC during RunClosure.close, but without a terminal outcome RunClosure makes its
    designed single close_incomplete attempt (one closure request: public state, flush, abort,
    reader; never finalize; run_closure.py near line 416, persistence.py close_incomplete). That
    is not a replay of the failed append. Expectation corrected: during RunClosure.close at most
    one persistence request, of kind closure, and no other kind. No product change.

426. DV10 second run (guard corrected per finding 425): C0 and C4 pass; C1–C3 make exactly one
    closure request (stage rpc-unresolved, last acknowledged state open, abort not attempted) and
    then fail on the expectation "cleanup_complete". Full closure facts for C1 and C3: root
    reaped, inventory complete, zero unacknowledged births, authority fenced, final freeze
    acknowledged, every boundary empty and released, every helper reaped (storage -15, authority
    -9, controller -9); the role4 authority's direct-child wait is not reaped (False) and the
    issued source unit's direct_child_reaped and native_retired are unknown (None), so
    cleanup_complete is False with ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN (C3 also
    ML-CLOSURE-UNIT-UNRESOLVED, because the teardown could not record its stop). This is the
    established honest outcome after storage loss, not a new defect: the existing control
    test_composed_persistence_termination.py:258-259 accepts an incomplete cleanup only together
    with that diagnostic, and physical cleanup is shown by the empty, released boundaries. The
    expectation of finding 424 was too strong. Corrected: every physical closure fact above holds,
    normal_unit_records_complete is False, and cleanup_complete is either True or False with
    ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN among the diagnostics. Open observation, not repaired here:
    after a storage fault the authority is killed before it reaps the released workload's leader,
    so the native wait fact is lost although the original authority was alive; this joins the
    known missing-wait-receipt class and is a candidate for the root-cause campaign.

427. The DV10 harness control C0 (interposer loaded, never armed) failed in 1 of 2 module runs and
    then in 6 of 8 repeats at host load 11.9–12.7 (the shared host now runs a llama-server of
    another project at about 4.8 cores, plus fabro collectors; 32 cores). Every failure is a
    persistence RPC that times out after being sent with a small budget, failing the client:
    ML-PERSIST-TIMEOUT on schedule requests sent with 98.6, 23.8 and 70.8 ms and on teardown
    requests sent with 68.2 and 77.4 ms (deadline_ns − started_ns of client.rpc_failure), and
    once ML-OWNER-DEADLINE at teardown validation (deadline already passed). The unmodified
    original bootstrap shows the same failure class: the existing control
    test_terminal_runtime.py::test_actual_native_report_close_and_external_closed_recomputation[False],
    unchanged and passing in run s, failed 6 of 16 repeats in the same window with
    ML-SCHEDULE-TEARDOWN-INCOMPLETE. So the interposer's per-write path checks (readlink, fstat,
    fstatat in role3) raise the rate but do not create the failure. This widens F-08 (finding
    418): the small budgets occur during ordinary teardown and scheduling, not only at the active
    end, and an existing accepted control is load-sensitive on this host. Consequences: (a) the
    C0 control cannot be required to pass under this load; the DV10 fault cases C1–C4 are
    unaffected in their claims (each failed closed at its injected write, verified by the
    injection trace before any timeout); (b) a full platform run under this load would likely fail
    for this reason, so step 3 waits for the F-08 repair or a quieter host; (c) the limiting term of
    each small budget is measured next, before any repair is scoped.

428. Limiting term of the small budgets (finding 427), measured with a temporary probe on the
    unmodified original stack (evidence/affa19/budget-probe: probe_test.py, runs.txt; the probe was
    removed from tests/ after use). It wraps FiniteDispatcher._end and _send, recomputes each term of
    _end (window limit, admitted operation budget 0.5 s, root lease, next health deadline minus
    scan time, per-unit gate leases) and logs the send budget and service time. 6 + 8 repeats at
    load 11.5–13.4: 9 failed. (a) Schedule requests: the limiting term is always the window limit
    (active end), with 0.019–0.35 s left; no health or lease term ever limited a budget below 0.15 s.
    Under this load ordinary requests take 0.08–0.25 s each (step-dispatch 0.11–0.13 s,
    step-complete 0.21–0.25 s, tick-complete 0.04–0.10 s, unit-disposition about 0.16 s), so the run
    consumes its admitted active window before its last steps; _end then hands the remaining sliver
    to the next request, which times out (ML-PERSIST-TIMEOUT) and fails the channel. (b) Teardown
    requests (0.037–0.12 s budgets): TeardownController._stop and _cleanup pass one phase deadline
    through a sequence (intent record, stop/retire, terminate/release, observation loop, outcome
    record); the closing record receives what the earlier operations left. Classification: two
    causes combine. Window exhaustion under load is an environmental sensitivity of the owned
    fixtures (the product correctly refuses to exceed the admitted window). Sending a request whose
    remaining budget is below its normal service time, which converts a clean incomplete end into
    a failed channel without terminal record, is the product defect F-08 (window end, schedule
    path) and its teardown variant, recorded here as F-09. Same-session observation only; the link
    to the ten unknown-cause records remains a hypothesis. Repair scope follows in its own finding.

429. Repair scope for F-08 and F-09 (ML-CAPA-418), recorded before any product edit. Authority:
    the strict form of the new T3 control fails (a run ended by its host deadline loses its
    terminal record), which meets the finding-421 rule for a product change; the choice below is
    an engineering parameter, not a protocol or scientific setting, and widens no deadline.
    F-08 (dispatcher.py, FiniteDispatcher._end): keep every existing term; additionally, when the
    window term (active end, or work end for terminal calls) leaves less than the call's own
    admitted budget (operation, restart, recovery or action-timeout seconds), raise
    ML-SCHEDULE-SERVICE-DEADLINE instead of returning the shorter end. Rationale: the schedule
    admission sizes every operation at its admitted budget, so an operation that cannot be given
    that budget inside the window is outside the admission; refusing it ends the run by the
    existing clean path (terminal phase within the work end) instead of failing the channel.
    Health, lease and gate terms keep their present behaviour (they were never the limiting term
    in finding 428). The lazy terminal-service branch is unchanged. F-09 (teardown.py,
    ReverseTeardown._stop and _cleanup): measure the duration of the phase's opening intent
    record; before the closing outcome record, if the remaining phase deadline is less than twice
    that duration, raise TeardownError ML-TEARDOWN-RECORD-BUDGET without sending, so phase() takes
    its existing emergency path with a healthy channel. Rationale: the two records are the same
    request type, so the measured opening record is the local estimate of the closing record's
    service time; no constant is introduced. Expected effects, to be verified: (i) T3 shows only
    the clean branch (ML-SCHEDULE-SERVICE-DEADLINE, terminal recorded, client not failed) in 10
    repeats under recorded load, after which T3 is tightened; (ii) in repeats of the budget probe
    and of the existing native report control, no ML-PERSIST-TIMEOUT on a schedule or teardown
    request (window exhaustion may still end runs incomplete; pass rates under load are not a
    claim); (iii) the existing dispatcher, scheduler, teardown, terminal and restart modules show no
    new failure class in an interleaved A/B against checkpoint 19-2 (arm A) under the same load;
    (iv) independent review of the diff before acceptance. Not changed: admission formulas,
    windows, budgets, the persistence protocol, the 60/40 normal/emergency split.

430. Candidate checkpoint 19-3 8184a2b15 (finding 429 repair, before review). Smoke: test_dispatcher,
    test_time_context_controls and test_teardown 49 passed, 1 failed
    (test_duration_defers_step_completion_until_actual_tick, ML-SCHEDULE-TEARDOWN-INCOMPLETE) at
    load 11.2; whether the new F-09 guard or load causes it is not known yet. T3 alone showed the
    clean branch in 10 of 10 repeats, but at load 6.9–8.0 versus 10–13 before the change, so that
    comparison is confounded. Verification plan, recorded before it runs: interleaved A/B
    (evidence/affa19/ab-f08-repair-20261021a.py), A = 19-2 c3a9213a1, B = 8184a2b15, 10 iterations
    alternating order, five nodes per run: T3, the native report control [False], the duration
    test above, the paused-ticks dispatcher control and the DV10 harness control C0. Expected, if
    the repair works and introduces no regression: B has no run containing ML-PERSIST-TIMEOUT and
    only the clean T3 variant; B's failures per node are not higher than A's beyond noise (a
    difference of at most 2 of 10 is treated as noise at this sample size); A reproduces the
    timeout class. A B failure that A does not show is a regression finding.

431. DV04 dispatcher-level expectations, recorded before test_readiness_dispositions.py first ran
    (to run after the A/B of finding 430 finishes, so as not to load the host during it). Fixture:
    the real owned two-unit stack of test_dispatcher.full_stack (native helpers, catalog
    launchers, gates). Stimuli applied to the prerequisite (source) after it was ready and before
    the dependent (sink) is released: D1 dead: SIGKILL of the source leader (launcher childfd)
    immediately before the start-sink step effect; D2 unknown health: SIGSTOP of the source's
    launcher (issuer) immediately before the start-sink effect, SIGCONT as soon as that effect returns or raises;
    D3 final guard: SIGKILL of the source leader right after the sink gate's ARM exchange (packet
    kind 3), the window the provider control final-guard uses. Expected in each: the run does not
    succeed; the start-sink step disposition is not completed; no step after start-sink is
    completed; the sink marker never exists (the dependent never executes); unit cleanup is
    complete (teardown triggered and bounded); the run returns within its terminal deadline. These
    are the "dependent blocked, start step disposition non-successful, teardown triggered"
    observations of DV04-N asserted together, which the coverage map found only separately. The
    running-but-application-not-ready stimulus is not constructible: the catalog admits only the
    running existence probe, and an application-level probe is rejected at construction, as the
    coverage map records.

432. DV03 Release-path expectations, recorded before test_permit_release_path.py first ran (to run
    after the A/B). Fixture: test_persistence.storage (real persistence worker, native gate,
    owned boundary and child), with a custom sealed configuration passed through start(override=).
    P1 expiry between intent and Release: permit and approval valid from now-30 s until now+E with
    E = 2.5 s; commit_intent and stage succeed inside validity; the test waits until 0.3 s after
    expiry; owner.release must raise, the gate must receive no Release (gate sequence 0), the
    workload marker must not appear, the latch is cancelled, C1 force cleanup observes
    termination and the worker is reaped. P2 not yet valid: not_before now+30 s; commit_intent
    must raise (claim time check), owner.release must then raise without a claim, gate sequence
    0, no marker. P3 intent-only restart composed with real processes: after a successful intent
    commit the first storage worker is killed (SIGKILL through its pidfd) before any Release; a
    second original worker started on a configuration identical except for a fresh Argus root
    (so the Argus open of finding 425 C4 is not what rejects) and the same M3 journal must refuse
    the same unit's new claim (durable intent without outcome), and no Release or marker occurs.
    Not constructible on the Release path, with reason: superset scope, exclusions and changed
    environment identity are fixed in the sealed configuration and the immutable prepared
    lifecycle at admission; the Release path revalidates the same stored binding and approval, so
    no run-time stimulus can change them after admission, and the admission-level rejections
    (test_admission) are the complete controls for those stimuli.

433. Independent read-only review of candidate 19-3 8184a2b15 (subagent, 2026-10-21, no tests
    run): verdict FAIL. Accepted findings: (1, high) the F-08 threshold is the full admitted
    budget, but the schedule admission does not reserve that budget inside the active window
    (admit_schedule caps active_seconds and sizes only the terminal reserve per operation;
    schedule_plan.py:100,160-164), so the guard removes about one budget (0.5 s) of usable
    active window; finding 362 recorded about zero margin on the 4.8 s fixture (clean spans p90
    4.23 s, p95 4.31 s, p99 4.55 s) and successful sends with 0.481 s and 0.188 s left in run a,
    which the guard would refuse, so quiet-host runs that used to succeed can end
    ML-SCHEDULE-SERVICE-DEADLINE. (2, medium) The rationale of finding 429, "the schedule
    admission sizes every operation at its admitted budget", is wrong; refused operations lie
    inside the admitted window. That statement is withdrawn. (3, medium) the restart pre-check at
    dispatcher.py:877 uses the operation budget while _restart_unit (:825) applies the restart
    budget after quiesce, so a late restart can now fail after the unit has been torn down
    (mutated, run cancelled) instead of being rejected before mutation. (4, medium) step-dispatch
    (:1095) and the effect (:1105) each pass _end, so a step can be durably dispatched and then
    refused. (5, medium, needs measurement) F-09's factor 2 can fire where the old send would have
    succeeded, inside a normal-path window of about 0.27 s, and then cancels the whole run through
    the emergency path; the factor is a constant, contrary to finding 429's wording. (6, low)
    recovery is refused earlier, with a different diagnostic. (7, low) health scans, renewals and
    teardown opening records can still receive slivers. (8, low) action timeouts set the
    threshold for plain statements. (9, nit) the lazy terminal-service branch is unreachable from
    the current terminal=True callers. Consequence: the candidate is not accepted. The threshold
    must be a service-time estimate calibrated on quiet-host timelines, not the full budget, and
    the restart pre-check and the statement/effect pair must be consistent. That calibration needs
    the retained clean timelines and a quieter host. The A/B of finding 430 is completed and
    recorded regardless, as evidence about the defect, not as acceptance of this candidate.

434. A/B of finding 430 completed (2026-10-21, script ab-f08-repair-20261021a.py sha cadb2274…,
    receipt evidence/affa19/ab-f08-repair-20261021a/receipt.json sha 45dea170…, 10 interleaved
    iterations x 5 nodes per arm, 1-minute load before each run 7.3 to 12.0). Arm A (c3a9213a1):
    ML-PERSIST-TIMEOUT in 8 of 10 runs, at least one failed node in 2 of 10 runs, 4 failed
    nodes in total (iteration 6: ML-SCHEDULE-TEARDOWN-INCOMPLETE; iteration 9, load 12.0:
    ML-OWNER-DEADLINE). Arm B (8184a2b15): ML-PERSIST-TIMEOUT in 0 of 10 runs, but at least one
    failed node in 6 of 10 runs, 16 failed nodes in total (terminal_runtime[False] 5, C0 5,
    paused_ticks 4, duration 2). Every B failure ends ML-SCHEDULE-SERVICE-DEADLINE or
    ML-SCHEDULE-TEARDOWN-INCOMPLETE on a fixture with no stimulus. Reading: the guard does remove
    the late-RPC timeout mechanism, but at the price predicted by finding 433 (1). It refuses
    sends that would have succeeded, and the fixtures then fail more often than without the
    guard. This is evidence about the defect and a negative result for the candidate, not
    acceptance. Consequence: 8184a2b15 is rejected. It is reverted on the branch (history kept)
    so that the branch tip carries no unaccepted product change. The redesign (a service-time
    threshold calibrated on quiet-host timelines, consistent restart pre-check and
    statement/effect pair) is a successor candidate with its own review and A/B. The wait helper
    used during the run matched its own command line in pgrep -f and was stopped by hand. It
    did not affect the driver.

435. First run of the DV04 and DV03 files of findings 431 and 432 (2026-10-21, load 4.4 to 5.0,
    log evidence/affa19/dv03-dv04-20261021/run1.log sha a5d93968…). DV04: 3 of 3 modes pass as
    expected. dead and final-guard end ML-LAUNCH-CHILD-EXIT; unknown-health ends
    ML-LAUNCH-TIMEOUT. In every mode start-sink is failed, observe/stop/cleanup are blocked, the
    sink marker is absent, cleanup is complete and the run returns before the terminal deadline.
    DV03: 3 of 3 fail, each against an expectation of finding 432, not against the product.
    (P1) The intent deadline of 8 s lies past the fixture's teardown deadline. commit_intent
    refuses it with ML-OWNER-DEADLINE (owner.py:722) before any stimulus, so the test never
    reached the expiry. (P2) A permit that is not yet valid is already rejected when the
    configuration is sealed (encode_configuration -> validate_permits, ML-PERMIT-M3
    XVERSE-PERMIT-NOT-YET-VALID), before any worker exists. With validity checked at sealing and
    a monotonic clock, "not yet valid at claim" cannot be constructed on the Release path. That
    item of 432 is reclassified to a seal-level rejection with zero effect, and the Release-path
    variant is recorded as not constructible. (P3) The killed worker makes client.abort raise
    ConnectionResetError, not ValueError. _rpc records the RPC failure, calls _fail() and
    re-raises (persistence.py:814-834). The product callers catch (ValueError, OSError)
    (teardown.py:378-508), so this matches the contract and the expectation was too narrow.
    Repairs, tests only: P1 uses the 4 s intent deadline that P3 already uses successfully; P2
    asserts the seal-time rejection and that no worker or journal is created; P3 accepts
    ValueError or OSError and also asserts that the client is failed.

436. DV03 repairs of finding 435 and one further deviation (2026-10-21, load 2.9 to 5.0, logs in
    evidence/affa19/dv03-dv04-20261021/ with SHA256SUMS). After the P1 and P2 repairs, run2 has
    P1 and P2 passing. P3 failed at the second start(): ML-PERSIST-CLOSED
    (persistence.py:724), because the first worker's failure had cancelled the run's latch.
    That is correct product behaviour (inside one run a cancelled latch refuses any new
    original worker), but it shows that the test of 432 never reached a restart. The fixture's
    start() is bound to one run boundary. P3 now asserts the same-run refusal and then performs
    the restart proper: a fresh run boundary (environment factory, new manager and latch, same
    run id) opens a new original worker on the same M3 journal through a local helper that
    mirrors start() without fault modes. Observed in run3 and five repeats (rep1-rep5, 6 of 6
    nodes passing each time): the new worker refuses at init, and the client sees
    ML-PERSIST-ACK. The journal record count is unchanged, so no claim exists and Release cannot
    be reached. The refusal comes from the worker's PermitSession construction (consumed permit
    or unresolved intent, admission.py:562,567). The client-side code is the generic
    ML-PERSIST-ACK, so the evidence cannot say which of the two fired. That diagnostic
    granularity is recorded as an observation, not a defect: the behaviour fails closed as
    DV03-N requires. Files: test_permit_release_path.py sha 3d75f3ae…, test_readiness_dispositions.py
    sha 454031a7…. No product source changed (src/ is identical to c3a9213a1 after revert 1dac853ff).

437. Expectations for the remaining step-2 rows, recorded before any of the new tests first runs
    (2026-10-21). Rows from the coverage detail (0ff30783…): DV05 n1/n4/n5/n9, DV06 n1/n5/n8,
    DV09 p1, DV10 n10. Design row DV05-N: independent deadline, fail-closed fence, no detached
    worker, unresolved if containment cannot release. SLACK 0.5 s is a harness allowance.
    test_dv05_dv06_bounds.py:
    (n1, never-returning probe) Provider stack. The issuer of a released unit is SIGSTOPped, then
    the dependent's start is attempted. Expected: it raises within min(probe policy timeout,
    observe action timeout) + SLACK and before the original deadline; the thread set is
    unchanged (no detached worker); the latch is cancelled; no dependent marker.
    (n9, one dropped Cancel delivery) Gates join owner._gates only when Release is attempted, so
    the window is after the gate's ARM exchange. owner.cancel runs there with the first
    GateConnection.cancel delivery dropped (never reaches the native guard). Expected: Release
    raises; no workload byte; the guard still exits 0 with the boundary frozen, either through a
    later redundant delivery or at its own lease end plus the freeze reserve (which one is
    recorded); force cleanup observes termination.
    (n5, never-returning collect) Collection runtime after a normal teardown. The persistence
    worker is SIGSTOPped as the first collect RPC is sent. Expected: collect_outputs raises
    within its deadline + SLACK; the client is failed with no collection outcome; a second
    collect makes no new RPC; the stopped worker is reaped by drain.
    (n4, never-returning cleanup) The C1 operations (ProcessBoundaryOps release_empty and
    force_cleanup) are in-process cgroupfs syscalls with no stall point an owned fixture can
    construct (cgroup.kill also kills stopped tasks; no uninterruptible-sleep facility), so the
    stalled operation is the native authority's RETIRE inside the cleanup phase (authority
    SIGSTOPped on the first retire_owned). Expected: ReverseTeardown returns or raises within
    its deadline + SLACK and normal records are not complete. RunClosure then reaps every helper
    including the stopped authority, and every boundary is empty and released (containment can
    release, so not unresolved); the lifecycle is not complete.
    (DV06 n1, Cancel during restart quiescence) Active-restart fixture with a leaf restart
    ticket. driver.cancel runs either before the quiesce stop phase or between its stop and
    cleanup phases. Expected: restart disposition not completed; run not successful; latch
    cancelled; M3 records only generation 1; the generation-2 permit is not consumed; no new
    teardown generation; closure complete with helpers reaped and boundaries empty and released.
    (DV06 n8, PID reuse) Read-only finding: no product source signals by PID number (pidfd and
    cgroup.kill only); the only native waitpid calls (run_authority.c:135, catalog_launcher.c:94)
    target the caller's own clone3 child before it is reaped, and the kernel keeps that number
    reserved until then. A recycled number therefore has no target. A static guard test pins
    this. A forced recycle is not constructed (it would need a privileged pid-namespace facility
    and could show nothing beyond the static fact).
    (DV06 n5, TERM ignored then admitted force) Not applicable to catalog workloads: workload
    teardown sends no SIGTERM and goes straight to cgroup.kill (prbc.py force_cleanup,
    run_authority.c). The TERM-then-KILL escalation exists only for helper and worker processes
    and is already controlled (test_persistence unresponsive_to_term, test_supervisor). Recorded
    for the T01 reconciliation, not approximated.
    test_dv09_native_failed_lifecycle.py (DV09 p1): scheduled native stack. The sink workload's
    own cgroup.kill is written by the test right after start-sink completes (an external crash).
    Expected: the run does not succeed; the terminal is recorded; unit cleanup is complete; the
    independent offline verification is complete (every lifecycle obligation of a failed run is
    recorded) while the execution outcome stays failed. If verification is incomplete, the
    missing obligations are recorded as a finding (failure path not complete, or the row not
    constructible this way); the assertion is not weakened.
    test_native_storage_faults.py C5 (DV10 n10, every report write failing): the test-only
    interposer gains a compile-time OWNED_PREFIX mode (directory target, every regular file
    below it; C0-C4 compile with OWNED_PREFIX 0 and are unchanged; passed writes are traced
    only after arming in prefix mode), armed in role 3 when WorkerTerminal.publish begins.
    Expected: injected ENOSPC with the native call never made; no report file (or an empty
    one); the report is not eligible if any terminal facts exist; offline verification not
    complete; closure as in closed_cleanly; lifecycle not complete.
    Quiet-host service-time capture (for the F-08/F-09 redesign): rpc_timeline_plugin.py and
    calibrate.sh in evidence/affa19/service-time-calibration. An observation-only autouse
    wrapper of PersistenceClient._rpc records kind, action, sent budget, service time and
    diagnostic for six modules (dispatcher, terminal_runtime, teardown, time_context_controls,
    active_restart, shared_dispatcher) on the unmodified stack (src == c3a9213a1). The new tests
    are not run while the capture is running.

438. Quiet-host service times and the F-08/F-09 v2 repair scope (2026-10-21), recorded before
    any product edit. Capture (finding 437 method, src == c3a9213a1): 9 repeats of the six
    modules at 1-minute load 3.7 to 5.3, 603 test runs, every test passing, 20 286 persistence
    requests (evidence/affa19/service-time-calibration/quiet-20261021: timelines.tar.gz, logs,
    summary.json sha b00a8065…, replay.json sha 87d5e797…, SHA256SUMS). Service time depends strongly on the
    request type. p50/p99/max in ms: schedule step-complete 40/145/190, step-dispatch 23/88/135,
    tick-complete 24/53/78, run-terminal 53/126/181, unit-disposition 54/110/128; teardown
    record 31/76/118; probe 18/56/80; commit 28/63/84; init 298/457/612. Finding 428 measured
    two to five times these values at load 11-13 (step-complete 210-250, tick-complete 40-100).
    A single constant cutoff therefore either refuses quiet-host sends or misses loaded ones;
    the full 0.5 s budget of 8184a2b15 is far above every quiet p99 except init, which matches
    its A/B result (finding 434). Late requests (ML-PERSIST-TIMEOUT/SENDER/LATE): 48. Of these,
    45 are designed stalls in five negative tests (9 each: restart controller-loss, two stalled
    tick workers, the teardown flush hang, the missing record/ack case), and 3 are the T3
    active-end tick-complete, sent with 41.6, 2.5 and 42.7 ms left after earlier tick-completes
    in the same run had taken 52.9 to 58.9 ms. Offline replay (replay.py; estimates only,
    downstream effects ignored) of rules that use only information available before the send:
    "refuse when the remaining budget is below the longest round trip this run has already
    observed for the same request type" prevents those 3 and refuses 1 request that in fact
    succeeded (also a T3 active-end tick-complete, 45.7 ms left, 58.5 ms seen; refusing it gives
    the designed clean end). Factors 1.5 and 2 refuse 5 and 10 successful requests (the second
    also in the paused-shared teardown), and "2 x last" refuses 6. The budget-probe tails under
    load (finding 428) show the same pattern: run 2 sent step-complete with 0.120 s left after
    step-completes of about 0.19 s, and it timed out.
    Scope of candidate v2 (ML-CAPA-418), in place of the withdrawn 429 rule: (F-08)
    FiniteDispatcher._send refuses a schedule or tick statement with ML-SCHEDULE-SERVICE-DEADLINE,
    before sending, when deadline minus now is below the longest round trip this dispatcher has
    already observed for that statement kind; after each successful call it updates that
    maximum. _end is not changed, so the restart pre-check (433 item 3), the double statement/
    effect evaluation (item 4), the recovery path (item 6) and the effect deadlines are exactly
    as at c3a9213a1. The first statement of a kind has no estimate and is sent as before. (F-09)
    ReverseTeardown._record applies the same rule to teardown records with
    TeardownError ML-TEARDOWN-RECORD-BUDGET and a per-teardown maximum, in place of the
    factor-2 closing-record check. The refusal raises at the same call sites as the existing
    _end refusal and the existing record errors, so no new handling path is added. No
    constant, admission formula, window, budget, lease or protocol changes. Expected effects,
    to be verified: (i) the focused smoke and the six calibration modules pass on a quiet host;
    (ii) in an interleaved A/B against the branch without a repair (src == c3a9213a1), arm B
    has no ML-PERSIST-TIMEOUT on schedule or teardown requests outside designed stalls and no
    failure class absent from arm A; pass rates under load are recorded, not claimed; (iii) an
    independent read-only review of the diff before any acceptance proposal. Acceptance stays
    with the author.

439. First run of the finding-437 controls (2026-10-21, load 4.2 to 4.4, src == c3a9213a1,
    evidence/affa19/dv05-dv10-20261021 run1.log, dv09-rows*.log, SHA256SUMS): 8 of 9 pass.
    (n1 probe) Raised ML-LAUNCH-TIMEOUT after 1.0006 s against a probe bound of 1.0 s, with 3.89 s
    of the original deadline left; thread set unchanged. (n9 dropped Cancel) The first delivery
    (owner.cancel) was dropped. A second, redundant delivery came at once from the owner's own
    release-uncertain path, so the guard exited 0 with the boundary frozen before its lease end.
    Release raised ML-PERSIST-NOT-OPEN with no workload byte. The lease fallback was not needed
    and is therefore not shown by this case (test_lease_loss shows it alone). (n5 collect)
    ML-PERSIST-TIMEOUT 1.49 s before the collect deadline (the per-request collection operation
    bound); client failed, no outcome, no second RPC, worker reaped. (n4 cleanup) Authority
    stopped at the sink's RETIRE: teardown returned 2.5 s before its deadline. Sink: emergency,
    cleanup complete. Source: emergency, ML-TEARDOWN-NORMAL-INCOMPLETE. Closure reaped every
    helper and left every boundary empty and released, with cleanup_complete False and
    ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN, the same as the storage-loss contract of finding 426.
    (DV06 quiescence) before-stop: restart failed ML-TEARDOWN-CLOSED; between: failed
    ML-SCHEDULE-CANCELLED. Both: generation 1 only, generation-2 permit not consumed, closure
    complete. (PID static guard) passes. (C5 all report writes) 2 injected ENOSPC, no report, no
    retained entry, blocker "publication". Writer: abort attempted, not completed, usability
    after the fault unknown; reader diagnostics name the corrupt and missing artifacts. The
    execution itself succeeded and is reported separately (diagnostic
    ML-SCHEDULE-EVIDENCE-INCOMPLETE). Closure made no request.
    (DV09 p1) FAILED, product defect F-10, recorded before any repair. The sink was killed after
    start-sink completed. The run failed (ML-RUN-CHILD-EXIT), the terminal was recorded, unit
    cleanup was complete, collection was complete, and M3 holds stop/cleanup intents and the
    stopped/cleaned outcomes for both units. Every lifecycle row is satisfied except one:
    ob.input-integrity is conflicting with "invalid/missing source or annotation", so
    normalRecordStatus and overallStatus are incomplete. Cause: the schedule failure path for a
    missing observation (schedule_evidence.py:641-668) emits health-loss with outcome "unknown"
    backed by a logical M3 observation with status "unknown". The design allows exactly that
    (payload-options.md:95, payload-samples.json: health-loss outcomes failed, unknown), and
    coverage.py:359 already accepts it as a terminal annotation. The source check
    (coverage.py:531), however, maps every non-succeeded probe/ready/health/health-loss
    outcome to the M3 status set {"not-ready"}, so this event is marked conflicting and turns
    the integrity row conflicting. The design branch "normal-documented-failure"
    (coverage-expected-tables.json) expects a failed run with exact teardown and collection to
    be normal-complete and overall-complete with execution failed ("a failed run can be
    factually complete"). Native failed runs that lose an observation therefore can never be
    assessed complete. Repair scope (product, ML-CAPA-418 successor): at coverage.py:531 the
    M3 status set for a health-loss event with outcome "unknown" becomes {"unknown"}. Every
    other pair is unchanged: succeeded->running, other non-succeeded->not-ready, and every other
    source_ok condition (action id, execution id, digests, generation). Expected: DV09 p1 passes
    with overall complete and execution failed; the existing coverage, collection, terminal and
    DV09 controls are unchanged. Until the repair, the DV09 p1 test is marked xfail(strict) with
    this finding as its reason.

440. Correction of the F-10 cause in finding 439, recorded before a second product edit
    (2026-10-21). With the status-set repair of 439 applied on the working tree (not committed),
    DV09 p1 still failed with the same single conflicting event. Instrumentation of the
    assessor on the retained run (observational prints in the DV09 test) shows two independent
    rejections of the sink's health-loss/unknown event. (a) The status set: now passes
    (source_ok with {"unknown"} is True). (b) The dependency proof: coverage.py:549-550 requires
    every started/probe/ready/health/health-loss event of a unit with parents to carry fresh
    parent-probe proofs equal to its parent set. The schedule failure path emits dependencies []
    for the sink, whose parent set is {source}. The design fixes only the shape of dependencies
    (payload-options.md:40, array 0..16) and states no rule for which actions need proofs. The
    readiness producer copies the probe's dependencies onto health-loss/failed
    (lifecycle_evidence.py:385). The failure path documents a lost observation and has no fresh
    parent probe to cite, and coverage.py:359 already treats health-loss with outcome failed or
    unknown, like validate failures, as a failure annotation. 439's statement that the status set
    alone is the cause is withdrawn. Revised F-10 scope (product, coverage.py only): a
    health-loss event with outcome "unknown" is (1) matched against the M3 observation status
    {"unknown"} and (2) not subject to the parent-probe dependency proof. health-loss/failed and
    every other action keep both checks, and source_ok keeps every other condition. Expected:
    DV09 p1 passes (overall complete, execution failed). The coverage, coverage_dv09,
    collection_runtime, terminal_runtime, lazy_dispatcher and readiness modules are unchanged in
    outcome. The candidate is a separate commit with an independent review; acceptance stays with
    the author. The instrumentation prints stay in the DV09 test as observations.

441. Third F-10 rejection, found by tracing rather than inferred (2026-10-21), recorded before
    the producer edit. With both assessor edits of finding 440 on the working tree, DV09 p1
    still failed. A write trace of the assessor's validity map (a test-only dict subclass
    recording the source line of every non-satisfied write) shows exactly one write:
    coverage.py:547, the handleRef check, for the same health-loss/unknown event. The failure
    path omits handleRef, while the broker row of the issued sink carries it. That check binds
    an observation event to the exact issued handle. It is an integrity property and is not
    relaxed. The schedule evidence already keeps the unit's handle (self.handles) and derives
    handleRef from it for start/observe/stop/cleanup statements (schedule_evidence.py:556).
    Final F-10 scope, replacing 439 and 440: (1) coverage.py: a health-loss event with outcome
    "unknown" matches the M3 observation status {"unknown"}; (2) coverage.py: such an event is
    not subject to the parent-probe dependency proof; (3) schedule_evidence.py failure branch:
    when the observation is missing and the unit has a recorded handle, the health-loss
    annotation carries handleRef derived exactly as at line 556. Every other check stays as it
    is. Lesson recorded for the CAPA: the cause in 439 was stated from one reading of the code
    before verification; from here a cause is stated only after the trace shows no remaining
    rejection.

442. Harness boundary found while testing F-10 (2026-10-21). The native bootstrap starts the
    persistence worker as python -I -m xverse.maestro.persistence_worker with an empty
    environment, so the worker ignores PYTHONPATH and imports xverse from the interpreter's
    site-packages (/tmp/maestro-lite-platform-regression-target-20261020h, verified with
    env -i python -I). In the focused runner (PYTHONPATH=src), parent-process code (dispatcher,
    teardown, owner, the offline verify path) therefore comes from the worktree, while
    worker-side code (persistence_worker, schedule_evidence, lifecycle_evidence, the worker's
    terminal/preclosure assessment) comes from the installed copy. The installed copy is
    identical to main 557619e0c and to src at c3a9213a1 (diff -r; only xcom absent and the XDL
    data directories present). So no earlier result mixed versions. The 8184a2b15 A/B is also
    unaffected: that candidate changed only dispatcher.py and teardown.py, both parent-side, so
    both arms shared one worker. The F-10 producer edit (schedule_evidence.py) cannot be observed
    with this runner, which explains its "no effect" in finding 441. Consequence: worker-side
    candidates are tested with a separate interpreter. A --system-site-packages venv on /dev/shm
    gets the wheel built from the candidate tree (no-deps), and the runner sets no PYTHONPATH, so
    parent and worker load one version. Every candidate A/B from here installs each arm in its
    own venv. The F-08/F-09 v2 change is parent-side only, but its A/B follows the same rule.

443. Fourth step of the F-10 trace (2026-10-21). Built as a candidate venv (finding 442), the
    producer part of 441 made DV09 p1 lose every record after the unknown observation:
    rpc_failure kind schedule, stage validation, ML-PERSIST-CHILD; no coverage report. A
    debug-only venv (same wheel; its installed persistence_worker logs main() entry and any
    exception to /dev/shm; never in product sources) showed that the worker started and did not
    end through an exception. The cause is on the parent side: dispatcher.py:150-293 rebuilds
    every expected schedule event payload and requires its exact key set. The added handleRef
    made the failure reply mismatch (ML-SCHEDULE-ACK), the client failed and aborted, and the
    worker ended normally on abort, so the next request found the child gone. The F-10 producer
    part therefore needs its exact mirror in that expected payload: for kind failure with
    observation_missing and a bound unit, handleRef is derived from facade._bindings[unit].handle,
    as the same builder does for step-complete phase actions (dispatcher.py:266-268). The F-10
    scope becomes 441 (1)-(3) plus (4) this mirror. A mismatch between the two sides still fails
    closed (ML-SCHEDULE-ACK).

444. F-10 candidate result and a design divergence D-09 (2026-10-21). With the four F-10
    parts (441 (1)-(3), 443 (4)) in a candidate venv: no event is invalid, no row is open,
    normalRecordStatus is complete, required rows are satisfied, and the report's only blocker
    is terminal-outcome. The offline overall status is still incomplete. That is not F-10: the
    offline verifier sets overall to incomplete whenever the Argus writer state is not closed
    (coverage.py:937). The terminal path finalizes the writer only for an eligible report, and
    a failed execution (blocker terminal-outcome) is never eligible, so the writer is aborted.
    By product policy no failed execution can reach overall complete, while the design branch
    normal-documented-failure (coverage-expected-tables.json) expects overall complete with
    execution failed ("a failed run can be factually complete"). Recorded as DIVERGENT D-09 for
    the author's ruling at T01, next to CP-10 and W-01 and related to W-01 (writer closure
    policy). Not repaired: the choice between finalizing the writer for factually complete
    failed runs and amending the design branch is a design decision. The DV09 test is split:
    the F-10 part (normal complete, no open rows, only terminal-outcome blocking) is asserted
    strictly; the overall-complete expectation is xfail(strict) naming D-09. The tracing
    instrumentation of 441-443 is removed from the test; the invalid-event list and open rows
    stay as observations.

445. Independent read-only review of F-10 candidate 17da15b50 (subagent, 2026-10-21, code
    reading only): verdict FAIL. Accepted findings. (1, high) In lazy native mode the start
    step-dispatch is logical (handle None), so the worker never records self.handles[unit]
    (schedule_evidence.py:331 is its only writer; :510-516). If the unit's own start probe
    raises inside facade.start (providers.py:403-405), the failure statement has
    observation_missing; the parent mirror sees a binding and adds handleRef while the worker
    omits it, so the reply fails with ML-SCHEDULE-ACK where 17da15b50's parent acknowledged it.
    (2, high) After a generation advance, commit_generation deletes self.handles[unit]
    (schedule_evidence.py:51-61) while _restart_unit rebinds the facade (dispatcher.py:844), so
    a lost observation of the new generation gives the same mismatch. (3, low) The worker
    accepts observation_missing with any phase; the dispatcher only sends "observe", so
    source_ok's observe phase is right for every reachable case. Left as is. (4, low,
    pre-existing) a stale _probe_failure, left by a check_health that _drain_controller_recovery
    swallowed (dispatcher.py:754, 774-783), can be reported for an unrelated later failure.
    Before F-10 the assessor happened to reject such an event; now it is accepted as a recorded
    loss. Recorded for the root-cause campaign as ML-CAPA-418 input F-11 (misattribution
    candidate), not changed here. (5, nit) cancel with observation_missing is unreachable. The
    coverage relaxations were found not to weaken any obligation: health-loss events satisfy no
    ready, health, outcome or dependency row, and generation and identity checks remain.
    Revised F-10 producer and mirror rule (replacing 441 (3) and 443 (4); 441 (1)-(2)
    unchanged): both sides take handleRef from the issuance of the unit's current generation.
    The worker uses evidence.issued_handles[(unit, generation)] (issuance_evidence.py:120). The
    parent uses the handleRef of the validated issuance receipt client._issued_receipts[(unit,
    generation)] (persistence.py:1010), which the client stores only after validating the
    worker's issued event. Both exist exactly when the issued RPC succeeded, so they agree while
    the channel is alive; if not, the ACK fails closed as before. Expectations for two new
    regression tests in test_dv09_native_failed_lifecycle.py, written before they run: (a)
    lazy start-probe loss (the sink's own first query in facade.start raises): no
    ML-SCHEDULE-ACK, client not failed, failure annotation health-loss/unknown recorded with
    the issued handleRef, terminal recorded, run not successful; (b) lost observation of a
    restarted generation (the leaf's first query of generation 2 raises): the same, with the
    generation-2 handleRef. On 17da15b50 both are expected to fail (ML-SCHEDULE-ACK path); on the
    revision both pass.

446. F-10 revision results (2026-10-21, load 3.5 to 4.4, evidence/affa19/f10-20261021). DV09
    file in three venvs. 17da15b50 (f10): the strict F-10 test passes; (a) and (b) fail with a
    validation-stage RPC failure, the ML-SCHEDULE-ACK path the review traced, confirming
    review items 1 and 2 by execution. Revision (f10r): all four pass, apart from the strict
    xfail for D-09; (a) and (b) record health-loss/unknown with the handleRef of the issued
    generation (1 and 2) and the client stays usable. Baseline (dd00c1db5): the strict test fails
    (conflicting event); (a) and (b) are acknowledged but carry no handleRef. The 35-module set
    (coverage, collection runtime, terminal runtime, dispatchers, restart, runtime and the new
    controls) passed in the f10 venv: 360 passed, 1 skipped, 1 xfailed. The baseline venv failed
    only the DV09 strict test and the two new tests. The revision gets the same regression run
    and a second independent review before any acceptance proposal.

447. F-08/F-09 v2 candidate preparation and expectations, recorded before it runs (2026-10-21).
    The finding-438 patch is applied to an export of 9f31771dd (/dev/shm/affa19-tree-v2) and
    installed as its own venv. The diff is exactly the 438 scope: dispatcher.py __init__ and
    _send, teardown.py __init__ and _record; _end is untouched. It is committed on the branch
    only after its first results are recorded. A/B script ab-f08v2-20261021b.py (finding 442
    rule: arm A = venv of 9f31771dd, arm B = venv of the v2 tree; same test tree, no PYTHONPATH;
    installed file hashes in the receipt; same five nodes as finding 434). Expectations: (i) the
    six calibration modules and the 35-module set pass in the v2 venv on a quiet host, with no
    new ML-SCHEDULE-SERVICE-DEADLINE or ML-TEARDOWN-RECORD-BUDGET in any normal-path test;
    (ii) in the A/B, arm B has no ML-PERSIST-TIMEOUT in these nodes; T3 shows only the clean
    variant (ML-SCHEDULE-SERVICE-DEADLINE); arm B has no failure class that arm A lacks; under
    a quiet host both arms are expected to pass most runs, so the A/B mainly checks for new
    refusals; (iii) an independent review of the v2 diff. Pass rates under load are recorded,
    not claimed.

448. Second independent read-only review (subagent, 2026-10-21, code reading only) of the whole F-10
    change dd00c1db5..9f31771dd: verdict PASS, no high or medium finding. Worker and parent now
    agree in every reachable case traced (lazy start-probe loss, restart after advance, failed
    stage, never-issued units, recovery views, cancellation). Both issuance maps have one writer
    and are never deleted, and they can only diverge once the client has already failed. The
    handleRef values are identical by construction. The coverage relaxations satisfy no
    obligation. Low items: (1) the dependency exemption skipped the dependencies array entirely,
    so arbitrary entries would pass; adopted as a tightening here: a health-loss/unknown event
    must carry dependencies [] (its only producer emits []). (2) F-11 (stale _probe_failure):
    every _query failure cancels the owner, so the reported unit is the one whose observation
    failed; only the diagnostic code can be misattributed; stays an input to the root-cause
    campaign. (3) Pre-existing: between the worker's prepare_generation and the parent's
    _claims update, or after a failed advance, the two generation counters differ, so a failure
    statement naming that unit fails ML-SCHEDULE-ACK on the generation field (already true at
    dd00c1db5); recorded as ML-CAPA-418 input F-12, not changed. (4) The legacy CatalogLauncher
    path carries no handleRef on a lost observation; unchanged from baseline. (5) The revision's
    own regression log was pending at review time; it follows with this tightening. Not
    determined by the review: whether the generation-2 broker row's handleRef equals the
    issuance value at coverage.py:547. Test (b) asserts the recorded value only.

449. F-10 regression evidence (2026-10-21, evidence/affa19/f10-20261021). The revision
    9f31771dd in its own venv passed the 35-module set at load 5.5: 362 passed, 1 skipped, 1
    xfailed (D-09), including the two finding-445 tests and the T04 time-context controls. With
    the finding-448 tightening (health-loss/unknown requires dependencies []), the coverage,
    DV09, collection-runtime, terminal-runtime and runtime-verification subset passed: 135
    passed, 1 xfailed. The T02 modules (preparation, preparation rejections, discriminating
    projection, expected-table trace) passed on 9f31771dd: 74 passed. F-10 is a FIX_CANDIDATE
    for ML-CAPA-418. Acceptance stays with the author.

450. Remaining P3-T03 partials, recorded before the new tests run (2026-10-21; task review on
    the author's instruction "review the open tasks and check if you can close some"; the
    thesis-side assessment is specs/024-maestro-lite-lifecycle/review/task-closure-assessment-
    20261021.md). (DV03 p1, durable one-use bootstrap approval) Not a test gap. The product does
    not implement durable bootstrap-approval consumption: ADR-ML3-BOOTSTRAP-0001.md:68 states
    that durable bootstrap-permit consumption and authentication "remains a full U2 admission
    gate", and the approval reference supplies continuity only. Recorded as deferred design
    scope for the T01 reconciliation and the U2/M1 admission, not approximated. (DV04 n1, stale
    or expired reply) test_readiness_dispositions.py gains mode "stale-reply": during the
    start-sink effect, the source launcher's observations come back with observed_at older than
    the source's freshness. Expected, as in the other modes: start-sink not completed and every
    later step not completed; no sink marker; unit cleanup complete; return before the terminal
    deadline; run not successful; diagnostic recorded as observed. (DV04 n2, restarted
    prerequisite) The release guard queries every prerequisite fresh through its current
    binding (providers.py:362-371), so a cached ready observation is never used; stale
    readiness cannot be inherited by construction. The control in
    test_dv04_restarted_prerequisite.py checks that property on the native stack: source and
    leaf quiesced, source advanced to generation 2 (fresh ready), then the source's
    generation-2 observations report not running while its ready observation stays cached, and
    the leaf's generation-2 start is attempted. Expected: the start raises (ML-PROBE-DEPENDENCY
    or another ML- probe code, recorded); the latch is cancelled; no started/ready event and no
    running M3 outcome exist for the leaf at generation 2; RunClosure reaps every helper and
    leaves every boundary empty and released.

451. Results of the finding-450 controls (2026-10-21, load 4.6 to 4.8, venv of e9b346a05,
    evidence/affa19/dv04-t03-20261021). (DV04 n1 stale-reply) As expected: ML-PROBE-OBSERVATION,
    start-sink failed, every later step blocked, no sink marker, cleanup complete, return before
    the terminal deadline. (DV04 n2) The first run failed on a test-construction error
    (ProcessObservation has no running field; running is a property of exec_pipe_closed,
    leader_alive and exec_error, launcher.py:308-310). The stimulus is corrected to
    leader_alive=False, with no other change. Then, as expected: the leaf's generation-2 start
    raised ML-PROBE-DEPENDENCY although a generation-2 ready observation of the source was
    cached; the latch was cancelled; the leaf's generation 2 reached only intent and issued (M3
    intent pending, observation staged), with no started or ready event and no running outcome.
    Closure reaped every helper and left every boundary empty and released, with
    cleanup_complete False and ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN for the staged leader (the same
    pattern as the stage-ack-pending authority case). Three repeats: 5 of 5 pass each. With
    450's DV03 p1 design finding, every DV03-DV06 partial of the reconciliation is now either
    covered or recorded as not constructible or deferred by design. The remaining P3-T03 blocker
    is defect F-08/F-09.

452. F-08/F-09 v2 first results and commit (2026-10-21). The v2 venv (finding-438 patch on
    e9b346a05; applied with evidence/affa19/f08v2-apply.py) passed the 35-module set plus
    test_teardown.py at load 3.9: 389 passed, 1 skipped, 1 xfailed (D-09), with no failure of any
    kind, so no normal-path test was refused by the new guards (expectation 447 (i);
    evidence/affa19/f08v2-20261021). The same patch is now committed on the branch head; the
    worktree src equals the tested venv. Next: the interleaved A/B (447 (ii)) against the venv of
    e9b346a05 and an independent review (447 (iii)). Not accepted.

453. Independent read-only review of F-08/F-09 v2 f4262c285 (subagent, 2026-10-21, code reading
    only): verdict PASS, no high finding. Every _send and _record caller already handles the
    raised codes. The refusal happens before _active is set or any pending/outcome state
    changes, so it adds no half-done state. A refusal can only be worse than the old timeout
    through a false refusal of a repeated kind. failure, begin and run-terminal are
    first-of-kind and never guarded. All callers run on the dispatch thread, so the estimate
    state is single-threaded. _end is byte-identical to c3a9213a1, so 433 items 3, 4, 6 and 8 are
    moot. Medium items. (1) The A/B cannot attribute failures to the guard: the F-08 code is
    shared with _end and _service, and ML-TEARDOWN-RECORD-BUDGET is replaced by
    ML-TEARDOWN-NORMAL-INCOMPLETE in phase() and run(). Expectation 447 (i) ("no new
    RECORD-BUDGET") is therefore not checkable from output codes. Handled without a product
    change: guard_trace_plugin.py (evidence/affa19/guard-trace, observation only) logs each
    refusal at its source, using the guard's own condition (code raised, v2 estimate present,
    remaining below it), and ab-f08v2-20261021c.py carries it in both arms. (2) The estimator is
    a lifetime maximum with no decay. One slow call (a load spike, or a step-complete under a
    long action timeout, schedule_plan.py:107-111) sets the threshold for the rest of the run.
    Under load, the shared teardown phase window (0.6 x min(deadline, 1 s)) could then refuse
    closing records that would have fit. The quiet replay of 438 does not cover this. Recorded
    as an open measurement: the attribution A/B is owed under host load comparable to findings
    427-428, and the estimator stays a candidate until then. No load is generated on the shared
    host for this purpose. Low items, recorded: run-terminal is never protected (first of its
    kind); the teardown estimate resets with each new ReverseTeardown (fails open); the measured
    span includes local reply validation and, in the cancelled terminal scope, a bootstrap
    terminal-service RPC, so the implemented estimator is not exactly the replayed one; a
    refusal is reported with cause "external", like an _end refusal.

454. v2 A/B b completed (2026-10-21, ab-f08v2-20261021b.py, receipt evidence/affa19/
    ab-f08v2-20261021b/receipt.json sha c3a7f2e9…, 10 interleaved iterations x 5 nodes, load 3.8
    to 4.4; installed hashes in the receipt: arm A = e9b346a05 dispatcher e59f6499…, arm B = v2
    dispatcher 9a4b3a0a…, identical coverage.py). Arm A: no failed node; ML-PERSIST-TIMEOUT in
    3 of 10 runs, all the T3 active-end tick-complete (T3 variants: 7 clean, 3 timeout). Arm B:
    no failed node; no ML-PERSIST-TIMEOUT; T3 clean in 10 of 10. This meets expectation 447 (ii)
    on a quiet host: the late-RPC mechanism is gone from these nodes, and no failure class
    appears that arm A lacks. It shows nothing yet about false refusals under load (453 item
    2). The attribution A/B (ab-f08v2-20261021c.py, guard_trace_plugin) follows, to count and
    place every refusal.

455. v2 attribution A/B c and the run-t plan (2026-10-21). A/B c (ab-f08v2-20261021c.py with
    guard_trace_plugin, receipt evidence/affa19/ab-f08v2-20261021c/receipt.json sha 6d29e8a1…,
    10 interleaved iterations, load 3.6 to 6.2). Arm A: no failed node; ML-PERSIST-TIMEOUT in 3
    of 10 runs, all at T3; 0 guard refusals (no v2 estimate). Arm B: no failed node; no
    ML-PERSIST-TIMEOUT; T3 clean in 10 of 10. 8 guard refusals, every one F-08 on the T3
    active-end tick-complete, sent with 5.9 to 51.2 ms left against an observed round trip of
    49.1 to 64.6 ms. No F-09 refusal, and no refusal in any normal-path node (terminal runtime,
    two dispatcher controls, C0). This answers 453 item 1 for these nodes and a quiet host: every
    refusal is placed, each sits exactly where finding 418 located the defect, and none
    coincides with a failure. 453 item 2 (lifetime maximum under load) stays open. Run t (step
    3, authorized in finding 414): verify-platform-regression-20261021t.py, the first full
    platform Python run with one installed version (finding 442). It freezes the clean HEAD as a
    git archive on tmpfs, builds and installs that tree's wheel in a new venv, checks that the
    installed package equals the frozen src, and runs `pytest tests` from the frozen tree with no
    PYTHONPATH (tmpdir, basetemp and receipts on tmpfs, fsync probe, outer deadline 7200 s). It
    exercises every product change of the increment (F-10, F-08/F-09 v2) together; neither is
    accepted. Expected: collection succeeds (count recorded, not presumed). A clean run is
    hoped for but not presumed: any failure is recorded with its traceback before any
    interpretation, and no retry follows without a finding. The host is quiet (load about 4) and
    its condition is recorded at launch and end.

456. DV12 blocking rules (P3-T06; step 3, authorized in finding 414), recorded before the code
    and its tests run (2026-10-21). Gap rows (coverage detail 0ff30783…): n2 missing G4
    disposition (no G4 token anywhere), n6 skipped tests do not block (run s had one skip and
    passed_exit_status true), n7 zero tests caught only by a driver assertion, n8 staleness
    against the successor revision untested; p1 (installed-wheel full run) is run t. Design
    (verification-plan.md DV12-N): missing G4 disposition, skipped or zero tests, or stale
    successor evidence block admission or acceptance. These rules belong to verification
    tooling, not to the runtime product: new scripts/validate_maestro_acceptance_evidence.py
    (repository pattern scripts/validate_*.py) reads a run directory (configuration.json,
    wheel-receipt.json, wheel.log), the expected candidate commit, a G4 disposition file and an
    optional allowlist. It prints a JSON verdict with every blocker and exits 1 when any blocker
    exists. Rules: B1 collected > 0 and the final pytest summary accounts for exactly the
    collected count; B2 returncode 0, no failed or error count, no outer timeout; B3 every
    skipped or xfailed test must be named in the allowlist with a reason and an approval
    reference, or acceptance is blocked, and any xpassed blocks; B4 staleness: receipt head ==
    expected candidate, archive sha == sha of git archive of that commit,
    installed_equals_frozen_src true, wheel_verification true; B5 a G4 disposition record must
    exist with gate "G4", disposition "waived" or "satisfied", a scope, and an approval
    reference. tests/thesis_lite/maestro/test_acceptance_evidence_gate.py: one clean synthetic
    run passes, and each of nine mutations is blocked with its own named blocker (zero tests,
    count mismatch, failure, timeout, unlisted skip, xpass, stale head, reused archive, missing
    G4). No allowlist or G4 record is approved by this finding. The gate's verdict on run t is
    reported as observed, including any blocker that needs an author decision (expected: the
    lane-admission skip and the D-09 xfail need allowlist approval, and G4 needs the author's
    recorded waiver scope).

457. DV12 gate results (2026-10-21). scripts/validate_maestro_acceptance_evidence.py and
    tests/thesis_lite/maestro/test_acceptance_evidence_gate.py: 11 passed. The clean synthetic
    run (listed skip, G4 record) has no blocker. Each of the nine mutations is blocked by its
    own named rule (B1 zero tests, B1 count mismatch, B2 failures, B2 outer timeout, B3 unlisted
    skip, B3 xpassed, B4 stale head, B4 archive mismatch, B5 missing G4). A G4 record without an
    approval, or with a disposition other than waived or satisfied, counts as missing. The gate
    and its tests are not part of run t's frozen tree (added after the freeze); they are applied
    to run t's directory when it ends. DV12 n2, n6, n7 and n8 are now covered by tooling plus
    tests. Which skips and xfails may be allowlisted, and the G4 waiver scope record, are author
    decisions; none is approved here.

458. Run t result (2026-10-21; evidence/affa19/platform-regression-20261021t, wheel.log sha
    bce5e7ac…, wheel-receipt.json sha 01fcba3c…; head a343ed387, 2190 collected, 2420 s, load
    3.9 to 4.8, fsync probe 0 spikes on tmpfs). Return code 1: 13 failed, 2175 passed, 1
    skipped, 1 xfailed, 24 subtests passed. All 13 failures are Argus packaging tests
    (test_argus2_consumer_unit 9, test_argus2_integration 2, test_argus2_validation 2), each
    with "<venv>/bin/python: No module named build". The tests build a wheel themselves with
    `python -m build`. The candidate venv from candidate-venv/mkvenv.sh inherits the system
    site-packages but not the build tools, which environment h installs in its own
    site-packages. This is the verification-environment omission of finding 357 recurring in
    the new harness: an error in my mkvenv.sh, not a product failure. Every other module
    passed with one installed version, including every Maestro module, the increment-19 DV
    controls and both product candidates (F-10, F-08/F-09 v2). Skip: the lane-admission
    module, which runs under its own driver (MAESTRO_LANE_PROPOSAL unset). Xfail: D-09. Run t
    is therefore not a clean run and is not presented as one. Repair (harness only, recorded
    before it is made): mkvenv.sh copies the build-tool distributions of environment h (build,
    hatchling and their dependencies, with the versions environment h's preparation records)
    into the candidate venv, file by file from their RECORD entries, and verifies `python -m
    build --version` and the hatchling import. Then the 13 tests are rerun on run t's frozen
    tree and wheel as a focused confirmation, and a complete run u follows on the same head
    for a clean full run. Run t is not retried as is.

459. Run-t harness repair confirmed, and the DV12 gate applied to run t (2026-10-21). mkvenv.sh
    now copies build 1.6.1, hatchling 1.32.4, packaging 26.3, pluggy 1.7.0, pyproject_hooks
    1.3.3, tomlkit 0.15.2 and trove_classifiers 2026.9.21.13 from environment h's site-packages
    (pathspec 1.1.1 comes from the system site-packages, as for environment h) and verifies
    `python -m build --version` and the hatchling import. The 13 failed Argus tests, rerun on run
    t's own frozen tree and wheel in a venv built by the repaired script: 13 passed
    (argus13-fixed-venv.log). Run t's receipts are archived (receipts.tar.gz, 9.9 MB) and its
    tmpfs work directory is removed. The gate (scripts/validate_maestro_acceptance_evidence.py,
    candidate a343ed387) on run t: blocked, with B2 failures 13, B3 unlisted skip
    (lane admission), B3 unlisted xfail (D-09) and B5 missing G4 disposition. B1 (counts
    consistent, 2190) and B4 (head fresh, archive equal to the candidate's git archive,
    installed equals frozen src) pass. This is the gate behaving as designed on real evidence
    (dv12-gate-verdict.json). Run u follows: the same driver on the new head, with the repaired
    venv script.

460. CAPA successor capa-20261021-affa19-step2 (2026-10-21; builder build-capa-20261021-
    affa19-step2.py; register sha 335f93f6…; 56 records / 572 bindings; parent
    capa-20261021-affa19-f08 ebcc01d6… preserved; both validators pass). Additive: review
    spans 420-458; the step-2 tests, the DV12 gate, the candidate-venv tooling; the A/B,
    calibration and run-t receipts; the two candidate patches written into the folder
    (f08-f09-v2.patch = git diff e9b346a05 f4262c285 -- src, f10.patch = git diff dd00c1db5
    e9b346a05 -- src). Record changes: ML-CAPA-418 (F-08/F-09) TRIAGED -> FIX_CANDIDATE on v2,
    with the load limit stated; ML-CAPA-357 gains the run-t recurrence. New records:
    ML-CAPA-439 (F-10, FIX_CANDIDATE), ML-CAPA-442 (installed-package worker boundary and its
    tooling, FIX_CANDIDATE), ML-CAPA-444-D09 (TRIAGED, awaiting the author's ruling),
    ML-CAPA-445-F11 and ML-CAPA-448-F12 (pre-existing review observations, TRIAGED). No cause is
    VERIFIED and every effectiveness stays NOT_DEMONSTRATED. The ten unknown-cause records are
    unchanged.

461. Run u, the first clean full platform run with one installed version, and the step-4
    campaign plan (2026-10-21). Run u (evidence/affa19/platform-regression-20261021u; driver
    as run t; head e2c338033 with the repaired venv script; 2201 collected; 2440 s; load 4.1;
    fsync probe 0 spikes on tmpfs): return code 0, 2199 passed, 1 skipped (lane admission,
    under its own driver), 1 xfailed (D-09), 24 subtests passed. It exercises both product
    candidates (F-10, F-08/F-09 v2), every increment-19 control and the DV12 gate tests together.
    Neither candidate is accepted. DV12 gate on run u (candidate e2c33803…): blocked only by
    B3 unlisted skip (lane admission), B3 unlisted xfail (D-09) and B5 missing G4 disposition.
    B1, B2 and B4 pass. All three remaining blockers are author decisions: whether the lane
    skip and the D-09 xfail may be allowlisted with their reasons, and the G4 waiver scope
    record. Receipts archived (receipts.tar.gz) and the tmpfs work directory removed. Step-4
    campaign (campaign-unknown-causes-20261021.py, authorized in finding 414): the original
    reproducers of the ten unknown-cause records (135, 286, 287, 318, 324, 330, 331, 332, 337,
    and 359 as two nodes), 10 interleaved iterations, arm A = venv of e9b346a05 (no guard),
    arm B = venv of f4262c285 (v2), with the RPC timeline and guard-trace plugins (observation
    only). Expectations: on a quiet host the reproducers may well all pass, and a pass is
    recorded as absence of recurrence, not as a cause. Any failure is recorded with its late or
    under-budget RPCs. A failure in arm A that shows a sub-service-time send while arm B shows a
    guard refusal at the same place would support, not verify, a link to F-08; any other failure
    keeps its record UNKNOWN. No cause status changes from this campaign alone.

462. Independent read-only review of increment 19 as a whole (subagent, 2026-10-21, head
    07a9bb75a, code and evidence reading only). Recommendation: NOT READY to accept the
    increment as a whole. F-10 is close to an author decision; F-08/F-09 v2 is not ready by the
    increment's own record. Passed: the product diff is exactly the two candidate patches; the
    8184a2b15 revert is complete; no accepted pre-existing test or script was modified; the
    numbers in findings match the receipts (runs t and u, the three A/Bs, calibration, CAPA);
    no product edit was made while a full run was live; no acceptance, merge, M1, factory or
    scientific claim. Accepted findings and their dispositions:
    - (FAIL) The product candidates have no targeted tests. No test exercises the F-08 refusal,
      the F-09 refusal or its emergency path (never executed in any evidence), or the limits of
      the F-10 relaxation (non-empty dependencies, a wrong handleRef, health-loss/failed keeping
      both checks; 448's tightening is unasserted). Adopted: targeted tests follow.
    - Vacuity notes, adopted:
      - DV05 n1 has an upper bound only and no code, so an unrelated fast ValueError passes;
      - the DV09 strict test does not assert that a health-loss/unknown event exists;
      - the D-09 xfail has no raises=;
      - DV09 (a)/(b) do not run verify(), leaving the generation-2 coverage row open (448);
      - DV04 n2 asserts neither the code nor the cached generation 2;
      - DV03 P1 records no observed code;
      - T3 still accepts the F-08 timeout branch, so the full run cannot detect an F-08
        regression. With v2 on the branch, T3 is tightened to the clean variant (planned in
        418 and 429 (i)).
    - Gate notes, adopted: no test of an allowlisted xfail, of B4 not-installed or of B0; the
      B4 whole-tree archive comparison would block a candidate whose only later commits are
      docs. B4 gains a path-scoped mode (src, tests, scripts, xdl, pyproject.toml), recorded and
      tested; which scope is authoritative is the author's decision.
    - Record notes:
      - finding 447 named 9f31771dd as the v2 base; the real base was e9b346a05 (findings 452,
        454, and the installed coverage.py hash);
      - run u's tmpfs directory carries the driver's "t" prefix;
      - the CAPA register's inherited top-level accepted/merged flags refer to increments 17 and
        18; increment19.accepted is false;
      - the T04 closure note's "second logical domain" wording is to be checked against the
        test.
    - Expectation ordering is verifiable from Git only where the finding was committed before
      its test or edit (438, 439, 447). Elsewhere findings and their tests share a commit; this
      is stated, not repaired.
    - Risks for the author: v2 is unmeasured under load (high); F-09 is unexercised (high,
      addressed by the targeted test); D-09, CP-10, W-01 and the gate's allowlist and G4
      decisions remain open.
    The test hardening starts after the running step-4 campaign ends, because the campaign uses
    the live worktree's tests.

463. Hardening and targeted controls after review 462, recorded before they run (2026-10-21;
    run on the venv of f4262c285, after the campaign ends). Hardened assertions:
    - T3 accepts only the clean end (ML-SCHEDULE-SERVICE-DEADLINE, terminal recorded, client
      usable);
    - DV05 n1 requires ML-LAUNCH-TIMEOUT and elapsed within [bound - 0.05 s, bound + SLACK];
    - DV04 n2 requires ML-PROBE-DEPENDENCY and a cached generation of 2;
    - the strict DV09 test requires the recorded health-loss/unknown event with handleRef;
    - the D-09 xfail is restricted to raises=AssertionError;
    - DV09 (a) and (b) also run the offline verification and require that the assessor rejects
      no health-loss event of the lost generation (1, and 2 after the restart; 448's open
      point).
    New test_candidate_guards_and_f10_limits.py:
    - F-08: with the per-run estimate for tick-complete seeded above any window, the first
      tick-complete is refused before any send (no tick-complete request bytes reach
      schedule_call). The run ends ML-SCHEDULE-SERVICE-DEADLINE with the terminal recorded, the
      client usable and no RPC failure.
    - F-09: with the teardown estimate seeded the same way, a teardown record is refused
      (ML-TEARDOWN-RECORD-BUDGET observed at its source). The run does not succeed. The client
      stays usable with no RPC failure, unit cleanup is complete, normal records are
      incomplete, and every unit without normal records was handled on the emergency path. This
      is the first execution of the F-09 branch.
    - F-10 limits: the recorded lost observation, as the assessor reads it, is mutated three
      ways (a dependency added, a foreign handleRef, outcome changed to failed). Each mutation
      must make that event non-satisfied.
    Gate:
    - three more tests (an allowlisted xfail passes and an unlisted one blocks; B4
      not-installed; B0 missing run files);
    - --scope code compares content-addressed listings (git ls-tree -r of src, tests, scripts,
      xdl, pyproject.toml), because archive bytes also carry the commit id and time (two
      archives of identical src differed). On run u, code scope against the current head
      leaves only the three author-decision blockers.
    The gate tests (14) already pass. Seeding the estimates is a test stimulus standing for an
    earlier slow round trip; it changes no product code. If any expectation fails, the failure
    is recorded before any change.

464. Campaign and hardening results (2026-10-21). Step-4 campaign (receipt
    evidence/affa19/campaign-unknown-causes-20261021/receipt.json sha 39ad4881…; 10 interleaved
    iterations, load 3.6 to 5.5; installed dispatchers e59f6499… (A) and 9a4b3a0a… (B)): 11
    reproducers x 10 x 2 arms = 220 node runs, no failure, no guard refusal. As stated in 461,
    this is absence of recurrence on a quiet host. No record's cause changes, and the ten
    unknown-cause records stay UNKNOWN; reproduction under load stays owed. Hardened and
    targeted controls of 463 (venv of f4262c285): 37 passed, 1 xfailed (D-09), 1 failed.
    - Passed as expected:
      - T3 strict: clean end, terminal recorded;
      - DV05 n1 with its code and bounds;
      - DV04 n2 with ML-PROBE-DEPENDENCY and generation 2;
      - the strict DV09 test with the recorded loss;
      - DV09 (a) and (b) with no rejected loss in the offline verification, which closes 448's
        open point for generation 2;
      - F-08 targeted: tick-complete refused before any send, ML-SCHEDULE-SERVICE-DEADLINE,
        terminal recorded, client usable, no RPC failure;
      - the three F-10 limit mutations, each rejected (1 of 1);
      - the 14 gate tests.
    - DV03 P1's observed refusal code is ML-PERSIST-ACK, with 1.9 s of the deadline left (not a
      deadline refusal), and is now pinned.
    - Failed: F-09 targeted, on its assertion result.cleanup.unit_cleanup_complete. The guard
      refused the sink's teardown record (ML-TEARDOWN-RECORD-BUDGET observed at its source). The
      run ended ML-SCHEDULE-TEARDOWN-INCOMPLETE with the terminal recorded and the client
      usable. The final TeardownResult (reason dispatcher-terminal) has units=(), and
      unit_cleanup_complete is defined as bool(units) and all(...), so it is False for an
      empty tuple. Recorded before any change. Open question: wrong assertion target (the
      units were handled earlier, on the refused phase's emergency path), or under-reported
      cleanup after an F-09 refusal. Next: a read of the actual boundaries (RunClosure) in the
      same scenario before any conclusion.

465. The F-09 targeted failure of 464 resolved by reading the boundaries (2026-10-21). In the
    same scenario, with a RunClosure read added: after the refusal rpc_failure is None and the
    client is usable, the terminal is recorded, all five boundaries end empty and released, and
    every helper is reaped. The physical cleanup is RunClosure's, with diagnostics
    ML-CLOSURE-REPORT-INCOMPLETE, ML-CLOSURE-UNIT-UNRESOLVED and ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN.
    The dispatcher's final TeardownResult carries no units, and the teardown objects hold no
    normal stop or cleanup result. This is the existing emergency contract (finding 426): units
    that leave the normal path are unresolved, and their containment is released by closure.
    Not a product defect. The 463 expectation "result.cleanup.unit_cleanup_complete" targeted
    the wrong object and is replaced by the closure facts plus the pinned unresolved-unit
    semantics. Consequence for F-09: a refused teardown record trades the old RPC timeout for an
    emergency end with a usable channel and a recorded terminal. Units that would otherwise have
    been cleaned on the normal path end unresolved, which a false refusal under load would make
    costly. That cost is the reason 453 item 2 stays the open risk. DV03 P1 now asserts
    ML-PERSIST-ACK.

466. Hardening confirmed (2026-10-21, evidence/affa19/hardening-20261021). The hardened and
    targeted set (T3 strict, DV05 n1, DV04 n2, DV09 strict, (a) and (b) with verification, D-09
    with raises=, F-08 and F-09 targeted with the closure facts, three F-10 limit mutations,
    DV03 P1 with ML-PERSIST-ACK, 14 gate tests): 38 passed, 1 xfailed in each of three repeats
    at load 4.0 to 6.0. Discrimination of the strict T3: six runs on the venv of e9b346a05 (no
    guard) gave 3 passed and 3 failed (ML-PERSIST-TIMEOUT); six runs on the venv of f4262c285
    gave 6 passed (clean). The full run therefore now detects an F-08 regression (review 462
    item 3). Run v follows on the hardened head: the same driver, a new frozen archive, a clean
    full installed-wheel run expected but not presumed.

467. Run v on the hardened head 8744ed1ca is not clean, and the F-08/F-09 v2 load risk of 453
    item 2 is now partly measured (2026-10-21, evidence/affa19/platform-regression-20261021v).
    Run v: 2209 collected; 1 failed, 2206 passed, 1 skipped (lane admission), 1 xfailed (D-09),
    24 subtests, 3515 s. The single outer failure is the Argus nested full-suite test
    (test_argus2_integration.py::test_existing_platform_pytest_regression_unchanged_in_assembled_target):
    the nested platform run had 12 failed, 1911 passed. Product sources are identical to run u's
    head e2c338033 (clean), so the difference is host condition: another project's llama-server
    started about 2 minutes into run v at 220-240 % CPU and up to 15 GB RSS; load rose from 5.9
    at launch to 15.3 at the end. The fsync probe saw no spike over 150 ms, so storage is not
    implicated. Guard codes in the receipts: ML-SCHEDULE-SERVICE-DEADLINE only at the T3 active
    end (outer and nested), as in A/B c; the nested run keeps only the last 4000 characters of
    output, so the 12 nested failures carry no traceback in the log.
    Classification, recorded before any change (rerun-v-nested-failures-20261021.sh, run v's
    frozen tree and venv, the observation-only guard trace plugin):
    (a) nested-rerun/, still under the external load (load 14.2 to 13.4): 7 failed, 5 passed.
        Three are v2 guard refusals outside T3 that end the test in a non-clean variant:
        launcher_composition [closed], F-08 step-dispatch with 7.9 ms left against an estimate
        of 136 ms -> ML-SCHEDULE-SERVICE-DEADLINE; launcher_composition [lost-close-ack], F-09
        cleanup outcome record with 53 ms left against 123 ms -> ML-SCHEDULE-TEARDOWN-INCOMPLETE;
        native_writer_stream_faults [seeded-flush-persistent], F-09 stop outcome record with
        103 ms left against 116 ms -> ML-SCHEDULE-TEARDOWN-INCOMPLETE. Four are
        ML-PERSIST-TIMEOUT that v2 did not prevent: lazy_dispatcher nominal, stream faults
        [loader-only] and [seeded-flush-once], shared_dispatcher paused ticks.
    (b) nested-rerun-quiet/, after llama-server exited (load 7.3 falling to 6.5): 12 passed, no
        guard refusal. All 12 failures therefore depend on host load.
    (c) A/B d (ab-f08v2-loaded-20261021d.py; A = venv of e9b346a05, verified equal to its src,
        i.e. the head without v2; B = run v's venv) was written to answer whether the three
        refusals were false. It stopped at pair 0 with zero runs because the external load had
        ended; no load was generated to replace it. Whether the refused sends would have
        completed stays unmeasured. Against the quiet calibration of 438 (step-dispatch p50 23
        ms; teardown record p50/p99 31/76 ms, two to five times higher under load per 428), the
        7.9 ms send would almost certainly have timed out, the 53 ms one probably, and the 103
        ms one is undetermined.
    Consequences. (1) Expected effect (ii) of 438, "no ML-PERSIST-TIMEOUT outside designed
    stalls", does not hold under natural load: v2 bounds a send by the longest round trip seen
    so far in the same run, and under a load that rises during the run the next round trip can
    exceed it. v2 narrows F-08/F-09 but does not remove them, and A2 cannot be proposed as a
    complete repair. (2) Under load v2 changes some failures from a persist timeout to an
    explicit refusal with a usable channel (465). For tests that assert the clean variant this
    is still a failure, so the full suite is not load-robust with or without v2. (3) Two of the
    twelve, [seeded-flush-persistent] and transitive [cleaned-leaf], are the tests of
    ML-CAPA-359 (UNKNOWN cause, ML-PERSIST-TIMEOUT / ML-SCHEDULE-TEARDOWN-INCOMPLETE, never
    recurred in the quiet campaign of 464). This is the first recurrence: under natural load,
    and absent on the quiet rerun. It supports, but does not confirm, the hypothesis that 359
    belongs to the F-08/F-09 load class. A CAPA successor that moves 359 to HYPOTHESIS with this
    evidence is proposed, not built. (4) DV12 gate on run v (--scope code; run and candidate code
    sha 0ebb6ecc… equal): blockers B2 (1 failure), B3 skip and xfail unlisted, B5 G4. Run u
    remains the clean full run, on code that differs from the head only in tests and scripts.
    Next: the loaded A/B d when the host is loaded again by its own jobs; author decision on
    A2 with this evidence (accept as partial mitigation, revise, or withdraw).

468. Author decisions on the request of 2026-10-21 (author-decision-request-20261021.md, as
    revised by 467). The author's text, verbatim: "I accept all that depends on my decision, and
    for open questions I let you decide what is the best". Recorded meaning: every recommendation
    of the decision summary given to the author is accepted as stated; items given there without
    a recommendation (C2, C3) are delegated to the agent, which records each ruling and its
    basis as its own finding before acting on it.
    A1 F-10 (e9b346a05) ACCEPTED as an engineering fix candidate on this branch.
    A2 F-08/F-09 v2 (f4262c285) ACCEPTED AS A PARTIAL MITIGATION ONLY: F-08/F-09 stay open
       (ML-CAPA-418 is not closed); the acceptance is withdrawn if the loaded A/B d shows arm B
       failing more than arm A.
    B1 lane-admission skip and B2 D-09 xfail ALLOWLISTED; B2 expires with the C1 product fix.
    B3 G4 WAIVED for engineering-increment evidence only; feature acceptance (P3-T07) needs G4
       satisfied or decided again.
    B4 staleness scope CODE (src, tests, scripts, xdl, pyproject.toml) is authoritative.
    C1 D-09: the design branch normal-documented-failure is KEPT; the product is to be fixed in a
       later candidate so that a factually complete failed run is finalized, not aborted.
    C2 CP-10, W-01 and C3 CP-02, AF17: DELEGATED; one brief and ruling per row follow.
    C4 the non-constructible and deferred items (431, 432, 437, 450) ACCEPTED AS STATED LIMITS,
       to be listed in the T01 as-built reconciliation.
    D1 closure of P3-T02 and P3-T04 CONFIRMED (both reopen if the T01 freeze changes the
       projection or time contracts).
    D2 acceptance, merge and push of increment 19: NOT NOW, by the accepted recommendation; to
       be decided after A2's condition, the loaded A/B and a clean full run on the final head.
    D3 Note 23 paragraph APPROVED, to be applied after D1 with the A2 outcome added.
    D4 a CAPA successor (step 3) moving ML-CAPA-359 to HYPOTHESIS APPROVED.
    Gate inputs written from this record: evidence/affa19/acceptance-inputs/allowlist.json and
    g4.json, approval reference "review-affa19.md finding 468".

469. Loaded A/B d2 (2026-10-21, evidence/affa19/ab-f08v2-loaded-20261021d2, watcher
    ab-f08v2-loaded-20261021d-watch.sh, driver ab-f08v2-loaded-20261021d.py unchanged). Trigger
    at 12:47:27Z: a new llama-server of another project and 1-minute load 10.5. Arms as in 467:
    A = head without v2 (e9b346a05 venv), B = run v venv; the 12 tests of 467; 4 pairs,
    alternating order. Load 13.5 to 14.7 in pairs 0 and 1, then falling, 8.8 to 6.1 in pairs 2
    and 3.
    Failed tests of 12 per run: pair 0 A 9, B 10; pair 1 B 9, A 10; pair 2 A 1, B 0; pair 3 B 0,
    A 0. Totals A 20, B 19. Arm A codes: ML-SCHEDULE-TEARDOWN-INCOMPLETE 7, ML-PERSIST-TIMEOUT 6,
    ML-BOOT-CLOSED 1, ML-OWNER-DEADLINE 1; no guard (no refusal possible). Arm B codes:
    ML-SCHEDULE-TEARDOWN-INCOMPLETE 9, ML-SCHEDULE-SERVICE-DEADLINE 6, no ML-PERSIST-TIMEOUT; 15
    refusals, all in pairs 0 and 1. Remaining time against estimate ranged from 3 ms against
    104 ms to 296 against 299 and 166 against 168; three refusals were within 3 ms of the
    estimate. Their counterfactual outcome is unmeasured, but the same tests failed in arm A
    in the same pairs.
    Reading. (1) At load above about 13 these 12 tests fail in most runs with or without v2;
    at load below about 9 they pass in both arms (one A failure). The dominant cause is the
    fixed RPC and phase budgets against host load, which is the F-08/F-09 class itself and not
    a v2 effect. (2) v2 replaces persist timeouts by explicit refusals (6 timeouts in A, 0 in
    B) with no increase in failures. The A2 condition of 468 (withdraw if B fails more than A)
    is NOT met, so A2 stands as accepted partial mitigation. (3) Full-run evidence of this
    suite is therefore meaningful only with the host condition recorded: run u (load about 5)
    is clean, while run v (load rising to 15) is not, on identical product code. Ruling
    (delegated, 468): a full run whose recorded host load exceeds 10 at any sample is treated
    as an observation, not as a regression signal, and it is repeated on a quieter host. The
    gate is not changed, so a failed run still blocks (B2); the ruling only prevents a load
    failure from being read as a product regression. (4) F-08/F-09 stay open. Removing them
    needs budgets that account for load (design scope, T01), which is not attempted in
    increment 19.
    The run v work directory on /dev/shm (84 MB) is deleted after this record.

470. Delegated rulings C2 and C3 (finding 468), with C4 applied (2026-10-21). Basis: the design
    rows in design-oracle/ML-DESIGN-2026-10-03-v2, the trace of 420
    (expected-table-trace-20261021.json) and the cited test lines. Rule used for all four: where
    the implementation is stricter (fails closed) than a DRAFT row, or classifies a window the
    row does not name, amend the design row to the as-built behaviour; change the
    implementation only where it is weaker than the row in a way that can be closed. None of
    the four is weaker in a closable way, so no product change follows from C2 or C3.
    CP-10 (DIVERGENT -> AMEND DESIGN). The row's guarantee, "zero workload instructions after
    epoch bump", holds in every variant that bumps the epoch (cancel, authority loss, durable
    mirror or journal loss: 0 markers). The storage-worker loss variant has no epoch bump: the
    loss is not observed between the last revalidation and the Release send, so Release
    linearizes and the run is in CP-11 (one released execution, normal outcome possibly a
    mandatory gap), which is what test_composed_post_release_loss.py:146,222 asserts. A
    storage-liveness check before the send would narrow that window but cannot close it (the
    worker can be lost right after the check), and it would add a round trip, which 469 shows
    is load-sensitive. Amendment: CP-10's provable cleanup is conditioned on the epoch bump; a
    storage-worker loss not observed before Release linearization is classified CP-11, with at
    most the instructions issued by the one released execution.
    W-01 (DIVERGENT -> AMEND DESIGN). A one-off flush/fsync error matches the row (usable, one
    bounded abort). For a persistent fault the implementation never aborts and reports
    usability unknown (test_terminal_native_writer_failures.py:26, test_terminal_writer.py:73,77),
    the rule W-02 already states for stream errors ("abort only if usability is positively
    demonstrated"). After a failed fsync the durability of earlier writes cannot be established
    by retrying, so claiming usability would be the weaker reading. Amendment: split W-01 into a
    transient case (a later flush succeeds: usable, bounded abort permitted) and a persistent
    case (usability uncertain, no abort, last durable manifest reported), as implemented.
    CP-02 (BORDERLINE -> AMEND DESIGN). An empty retained boundary identity is released only
    under an admitted reservation approval; without it the identity stays retained and the
    state unresolved (test_boundary.py:150,467-470). Releasing with "surviving authority: none"
    would be an action without authority. Amendment: state the reservation-approval
    precondition in the row; without it the outcome is unresolved, identity retained.
    AF17 (BORDERLINE -> AMEND DESIGN). A request that names the transitive cohort stops and
    releases dependents leaf -> middle -> source before the advance, with fresh execution ids
    and permits (test_generation_dependents.py:99-110, test_active_transitive_restart.py:
    142-153). A lone prerequisite restart while dependents are active is rejected with
    ML-GENERATION-DEPENDENTS and no effect (test_active_restart.py:134,138). Stopping
    dependents that the request did not name would act on units without their own permit.
    Amendment: the request must name the transitive cohort; one that omits active dependents
    is rejected with no effect; "never silently retry with old execution, generation or permit"
    is unchanged and holds.
    C4 applied: DV03 n2-n4 (sealed at admission), DV04 n0 (no application-level probe), DV05 n4
    (in-process C1 stall, replaced by the authority RETIRE stall), DV06 n5 (no SIGTERM to
    workloads), DV06 n8 (PID reuse, settled statically) and DV03 p1 (deferred to the U2 gate by
    ADR-ML3-BOOTSTRAP-0001 line 68) are stated limits of the as-built design.
    Where the amendments go: the DRAFT design tables are not edited, and the design-oracle
    copies stay byte-identical to their originals (test_expected_table_trace.py pins them). The
    amendments, C1 and C4 form the as-built reconciliation for P3-T01, written in the thesis
    repository as specs/024-maestro-lite-lifecycle/review/as-built-reconciliation-20261021.md.
    Freezing ML-DESIGN-v2 with that reconciliation is a design acceptance that 468 did not list,
    so it is prepared and put to the author, not assumed.

471. C1 product fix scope (D-09), recorded before any product edit (2026-10-21). Cause (444):
    TerminalReportWorker.publish sets eligible = no blockers and an entry; close passes that
    flag to close_runtime_writer, which finalizes only when eligible and otherwise aborts after a
    positive flush; the parent's _writer_ack requires finalize_attempted == (eligible and
    before open). A failed execution always carries the blocker terminal-outcome, so its writer
    is aborted and coverage.py:937 keeps offline overall incomplete. Design branch
    normal-documented-failure (kept by C1) expects overall complete with execution failed.
    Change (candidate, terminal_runtime.py and terminal_writer.py; F-05 wire unchanged: no key,
    code or stage is added):
    (1) a report is finalizable when it is eligible, or when its only blocker is terminal-outcome
        and it has an entry and a retained entry, stage published, and normal, required and
        collection all true. Eligibility keeps its meaning (an acceptable successful run).
    (2) the worker passes finalize=<finalizable> to close_runtime_writer, which finalizes when
        finalize is true; finalize defaults to eligible for existing direct callers, must be a
        bool, and eligible without finalize is rejected. The abort path is unchanged for every
        other report, including W-01/W-02 handling.
    (3) the parent's _writer_ack requires finalize_attempted == (finalizable(report) and before
        open), computed from the report ACK fields it has already validated.
    (4) RunClosure's ML-CLOSURE-REPORT-INCOMPLETE uses finalizable instead of eligible, so a
        factually complete failed run is not reported as incomplete evidence; the execution
        failure stays reported by the dispatcher, whose diagnostic is not changed.
    Expected, to be verified: the D-09 test passes and its xfail(strict) is removed together
    with allowlist entry B2 (468); every test that asserts an abort for a failed execution whose
    report is otherwise complete changes from abort-completed to finalize-completed, and each such
    change is listed in the next finding before tests are edited; reports with any other blocker
    still abort. Independent review before the C1 acceptance proposal; full run after.

472. C1 candidate result, review and added controls (2026-10-21, evidence/affa19/c1-20261021).
    Independent read-only review of the 471 diff: PASS, no HIGH item. Items: (1)-(4) no path
    finalizes a report that is not factually complete; worker and parent evaluate finalizable on
    byte-identical, ACK-validated fields; nothing treats a closed writer as execution success;
    the W-01/W-02 abort path is unchanged for every non-finalizable report. (3) leftover:
    dispatcher.py:1510 still used eligible, so a factually complete failed run with no earlier
    diagnostic would carry ML-SCHEDULE-EVIDENCE-INCOMPLETE; aligned to finalizable (finding 471
    (4) is corrected accordingly: the dispatcher's evidence rule now equals RunClosure's; its
    execution diagnostic is unchanged). (5) MEDIUM, three missing controls, added:
    (a) test_dv09_native_failed_lifecycle.py::test_run_closure_reports_no_incomplete_evidence_for_a_documented_failure,
    (b) ::test_failed_run_with_another_gap_still_aborts_and_closure_reports_incomplete (outputs
    removed before collection: a second blocker keeps abort-completed, writer failed, closure
    ML-CLOSURE-REPORT-INCOMPLETE), (c) test_c1_failed_finalize_fault.py (failed run under the W-04
    recovery finalize fault: finalize attempted, the W-04 public states, no evidence
    completeness). (6) allowlist entry B2 removed (acceptance-inputs/allowlist.json), as 468
    required; terminal_writer.py docstring updated.
    Changed tests: the D-09 test loses its xfail(strict) and asserts the design branch (writer
    finalized and never aborted, offline complete, execution failed); no existing test outside
    the C1 modules asserts a report whose only blocker is terminal-outcome (grep), so no
    existing expectation changes.
    Verification with one installed version (venv of the worktree src, verified equal):
    D-09 test fails on the head without C1 at the abort (discrimination) and passes with it.
    C1 unit controls 21 passed. Affected set (18 modules plus the three C1 modules): run 1 at
    load 14 had 6 failures in test_active_controller_recovery, all F-08/F-09 codes; the baseline
    arm did not run (collection error of the new C1 module on the old product, expected). Run 2:
    C1 14 failed / 161 passed at load 5.5 rising to 11, baseline 15 failed / 133 passed at load
    11; every failure in both arms carries ML-SCHEDULE-TEARDOWN-INCOMPLETE,
    ML-SCHEDULE-SERVICE-DEADLINE, ML-PERSIST-TIMEOUT or a missing terminal, the load class of
    467-469; all C1 controls passed. Targeted A/B of the finalize- and closure-related failures
    of run 2 (terminal runtime changed-output, native writer failures, terminal faults, helper
    closure, runtime entry, storage-root loss, stream faults), two alternating pairs at load 7.5
    to 5.3: 26 passed in each of the four runs. Reading: no C1-attributable failure; the run-2
    failures are load. C1 is a fix candidate; acceptance with increment 19 follows the full run.

473. CAPA successor step 3 (2026-10-21, evidence/affa19/capa-20261021-affa19-step3, builder
    build-capa-20261021-affa19-step3.py), parent step 2 (335f93f6…, 56 records / 572 bindings),
    additive: review spans 459-472 and the run u/v, gate-input, loaded A/B and C1 evidence.
    ML-CAPA-418 stays FIX_CANDIDATE (v2 accepted as a partial mitigation only, 468 A2; F-08/F-09
    open); ML-CAPA-439 stays FIX_CANDIDATE (accepted, 468 A1; increment acceptance pending);
    ML-CAPA-444-D09 TRIAGED -> FIX_CANDIDATE on C1 cc3d444c1; ML-CAPA-359 UNRESOLVED/UNKNOWN ->
    TRIAGED/HYPOTHESIS (468 D4). No cause verified, no effectiveness claimed. This finding is
    bound by the next successor. Run w (full installed-wheel run on cc3d444c1) is in progress.

474. Complete independent review of increment 19 for P3-T06 (2026-10-21; read-only, whole diff
    557619e0c..d6a905a8d of src, tests, scripts, pyproject.toml), recorded before any repair.
    Verdict READY for an author acceptance proposal of increment 19 as an engineering
    increment (not feature acceptance); no HIGH item. Verified: a v2 refusal or an F-10
    health-loss failure can never leave a report whose only blocker is terminal-outcome
    (emergency teardown writes no stop/cleanup outcome, so required rows stay missing or
    unverifiable and normal-records blocks; a refused disposition or terminal send blocks
    publication), so C1 cannot finalize an incomplete run; lifecycle_complete and
    ready_for_execution stay False; execution success comes only from the dispatcher;
    eligibility keeps its meaning; no new wait, retry, RPC, action, stage or blocker value;
    every test file in the diff is new, so no assertion was weakened.
    Items. (1) MEDIUM gate: --scope code (src, tests, scripts, xdl, pyproject.toml) omits docs/
    and specs/ paths that the full run's tests read (test_expected_table_trace.py reads the
    design-oracle tables and the trace; xcom tests read docs/engineering/xcom and specs/), so a
    docs-only commit after a run could change a test input without staling the run; decision B4
    assumed docs do not affect tests. (2) MEDIUM gate: wheel.log is not checked against the
    receipt's log_sha256, and in code scope the run's archive_sha256 is not checked against its
    head. (3) LOW: ML-TEARDOWN-RECORD-BUDGET (F-09 refusal) is caught in run() and phase() and
    reported as ML-TEARDOWN-NORMAL-INCOMPLETE, so results cannot separate F-09 refusals from other
    teardown failures (469's arm-B counts rest on the trace plugin, as recorded there). (4) LOW:
    ML-SCHEDULE-SERVICE-DEADLINE already existed on main, so the strict T3 discriminates against
    ML-PERSIST-TIMEOUT only, probabilistically (466 measured 3/6 vs 6/6). (5) LOW: the dispatcher
    switch to finalizable (472) cannot change behaviour: a failed run always has an earlier
    diagnostic, and for a succeeded run finalizable equals eligible; kept for one rule
    everywhere, recorded as unreachable. (6) LOW gate: -ra folds identical skips into one
    "SKIPPED [N]" line, which the gate counts as one, so a valid run with grouped skips is falsely
    blocked (fails safe). (7) LOW: no integrated control drives a v2 refusal through the terminal
    report and asserts its blockers and writer outcome.
    Repairs, scope recorded here: (1) the code scope becomes the whole tree except
    docs/engineering/maestro-lite/evidence/ and docs/engineering/maestro-lite/review-*.md (no
    test reads them; the lane-admission test reads evidence/affa17 only when its own driver sets
    MAESTRO_LANE_PROPOSAL, and it is skipped in full runs); this replaces the B4 path list, as
    the ruling's intent ("documentation-only commits after a run keep it valid") holds only for
    files no test reads. (2) the gate checks sha256(wheel.log) == receipt log_sha256 (B2-log) and,
    in code scope, the receipt archive_sha256 against git archive of the run head (B4-archive).
    (6) skip and xfail counts read the [N] of grouped lines. (7) the targeted F-08 and F-09 tests
    also assert that the report is not finalizable and the writer is not finalized. (3) and (4)
    are recorded, not repaired: (3) changes product observability and belongs with the open
    F-08/F-09 design-scope work; (4) is a limit of the T3 control. Because the gate and tests
    change, run w no longer covers the final head; a further full run follows the repair.

475. Item 7 of 474 resolved by observation, and one verified-OK claim of 474 corrected
    (2026-10-21). The added control first asserted that no v2 refusal leaves a finalizable
    report. On the C1 venv (worktree src, verified equal) the F-09 control holds it (emergency
    path; blockers normal-records, required-coverage, collection, terminal-outcome; writer not
    finalized). The F-08 control refutes it: after a refused tick-complete the dispatcher ends
    on the normal teardown path (unit cleanup complete, terminal recorded, channel usable), and
    the report's only blocker is terminal-outcome, so C1 finalizes the writer. The 474 claim
    "a v2 refusal can never leave only terminal-outcome" therefore holds for F-09 only. This is
    not a defect: v2 coverage obligations are lifecycle facts (intent, ready, health slots,
    stop, cleanup, disposition, terminal), not ticks, and the independent assessor finds every
    one recorded. A run refused at a tick is a documented failure in the sense of design branch
    normal-documented-failure (kept by C1, 468). The F-08 control now asserts that integrated
    outcome: blockers exactly terminal-outcome, writer finalized and never aborted, offline
    verification complete, execution not succeeded. The F-09 control asserts that whatever
    terminal facts exist are neither finalizable nor finalized. Whether a refused tick-complete
    should itself become a lifecycle obligation is a design-scope question; it is recorded for
    T01 as an observation, not ruled here.

476. Author delegation of the remaining decisions (2026-10-21). The author's texts, verbatim, in
    order: "do it" (in reply to the task table row "P3-T03 ... Removing the defect needs
    load-aware budgets, which is a design-scope change"), then "I let you think about the
    decisions that I need to make and do it by yourself in order to progress". Recorded meaning:
    the agent takes the decisions still open for this feature (capability 024, P3-T01 to P3-T07)
    itself, records each with its basis before acting on it, and keeps irreversible steps behind
    evidence gates. Decisions taken under this delegation:
    E1 P3-T03: remove F-08/F-09 by load-aware interior budgets (design principle: outer
       admitted bounds stay hard; only the interior allocation inside them follows service times
       observed in the same run; identical behaviour on a quiet host). Design, ADR, scope
       finding, independent review and a loaded A/B precede any acceptance; v2 stays until the
       design says whether it is subsumed.
    E2 P3-T01: freeze ML-DESIGN-2026-10-03-v2 as amended by the as-built reconciliation
       (thesis specs/024-maestro-lite-lifecycle/review/as-built-reconciliation-20261021.md),
       after E1's design is added to it as an amendment, so the frozen design includes the
       budget model it is implemented against.
    E3 D2: accept increment 19 as an engineering increment, merge it into platform main and
       push, only when all hold: a clean full installed-wheel run on the final head with the
       host condition recorded (469 (3)), the DV12 gate passing with the 468 inputs, independent
       reviews of every product change without an open HIGH or MEDIUM item, and the CAPA register
       successor validated. A run that fails under recorded external load is repeated on a quiet
       host, not waived.
    E4 P3-T07: decided when T01-T06 are closed; the G4 disposition for feature acceptance is
       re-decided then, with source-parent semantic fidelity carried as a stated limit if it is
       still unproven. No scientific claim, lane activation, M1 admission or factory run follows
       from this delegation: they are outside the P3 tasks and stay closed.
    E5 canonical note: engineering-context entries are applied at milestones (increment
       acceptance, design freeze) with DRAFT or AUTHOR-DELEGATED status, never as scientific
       results; the research framing RF-2026-08-30-v6 and AEB-EXPERIMENT-2026-08-30-v2 stay
       unchanged.

477. Load-aware interior budgets (E1, finding 476): design and scope, recorded before any
    product edit (2026-10-21; ADR-ML3-BUDGET-0001.md). Basis: a read-only inventory of every
    site where a budget becomes a deadline or a go/no-go decision at dabf858a5. Observed codes
    traced: ML-SCHEDULE-TEARDOWN-INCOMPLETE from dispatcher _effect stop/cleanup (one
    now+operation_seconds end shared by stop and cleanup, of which phase() gives the normal path
    0.6) and from the finished-restart quiesce; ML-PERSIST-TIMEOUT from active-loop RPCs
    (teardown records without an estimate yet, window-limited statements, or the start effect's
    commit/issued/probe RPCs; which of these hit the four 467 cases is not determined because
    the rerun logs do not print client.rpc_failure); terminal-phase phase()/run() slivers while
    _work_end has slack (427). ML-SCHEDULE-SERVICE-DEADLINE at the active end is the outer bound
    working and is not removed. Scope: new pure module service_time.py (ServiceTimes, lifetime
    max per kind, shared by dispatcher and teardowns, v2's _service_seen and _record_seen become
    views of it); M2 widening-only sizing at effect stop/cleanup, quiesce (both sites), non-lazy
    terminal phases and the terminal run(), never earlier than today's deadline and capped by the
    outer bound minus later reserve, health minus scan+renew margin and leases minus renew margin;
    phase()/run() treat the admitted budget as a floor of the normal share; M1 refusal before a
    stop/cleanup step-dispatch that no longer fits (ML-SCHEDULE-SERVICE-DEADLINE), rejection
    before a restart mutation that does not fit (ML-SCHEDULE-RESTART-DEADLINE), finished-restart
    quiesce deferred to terminal cleanup when it does not fit; no M1 at tick pull (the F-08
    control asserts the tick-complete refusal); ML-TEARDOWN-RECORD-BUDGET kept as the
    UnitTeardown diagnostic; observation-only interior trace. Ruling on the open point: declared
    action timeouts stay hard (no M2 under use_action_timeouts, M1 only), because
    ADR-ML3-RESTART-0003 clips them to the existing ends. Margins: sizing 1.5, decision 1.0,
    module constants. No new code, RPC, wire field, admission field or sealed knob; no change to
    persistence.py, schedule_plan.py or run_closure.py.
    Expectations, to be verified: (i) seeded controls: a seeded phase:stop of 0.45 s with a
    0.15 s per-record delay completes normally where the head goes to emergency, every deadline
    stays at or below its outer bound and the emergency share stays 0.4; a seeded 3600 s
    phase:stop keeps the stop step blocked with ML-SCHEDULE-SERVICE-DEADLINE, normal terminal
    cleanup, a finalizable report and a usable channel; a seeded restart:unit rejects the
    restart unmutated; caps hold for leases and health and no ML-SCHEDULE-LEASE-EXHAUSTED
    appears; the sizing helper returns today's deadline whenever the need fits; the terminal
    reserve keeps dispositions, run-terminal and a full terminal_seconds report; a refused
    record shows ML-TEARDOWN-RECORD-BUDGET in UnitTeardown. (ii) The F-08 and F-09 controls and T3
    pass unchanged. (iii) Quiet host: the affected modules pass, and the interior trace records
    whether any widening or M1 stop occurs (expected none or few; the quiet identity is to be
    measured). (iv) Natural-load A/B against dabf858a5 on the 12 tests of 467, at least 4
    interleaved pairs triggered by external load at or above 10, with an observation plugin
    logging client.rpc_failure: candidate failures at most arm A's, fewer ML-PERSIST-TIMEOUT and
    ML-SCHEDULE-TEARDOWN-INCOMPLETE, no new failure class. (v) Independent review before any
    acceptance proposal.

478. Run w (2026-10-21, evidence/affa19/platform-regression-20261021w; head cc3d444c1, 2232
    collected): 32 failed, 2199 passed, 1 skipped, 4122 s. Host: another project's llama-server
    at about 550 % CPU from about 15 minutes into the run, load 12-15 for most of it (12.9 at the
    end); fsync probe 0 spikes. Repaired gate (474) on run w against its own head: only B2 (log
    bound, archive equal to its head, allowlist and G4 satisfied). By 469 (3) this run is an
    observation, not a regression signal. Classification of the 31 Maestro outer failures, one
    rerun each from run w's frozen tree at load 11-14: on run w's venv (C1) 27 failed, on the
    head-without-C1 venv (8a19e35a4 product) 11 failed, run back to back while other test
    processes also loaded the host. The C1-only failures carry ML-SCHEDULE-TEARDOWN-INCOMPLETE,
    ML-PERSIST-TIMEOUT, ML-RUN-ORIGINAL-END or a fault boundary not reached; each arises in an
    active-phase effect or before collection, before the terminal writer close that is the only
    point where C1 acts, so C1 cannot cause them. Reading: load variation between two single
    runs, consistent with the interleaved pairs of 472 at load 5-7 (26/26 in both arms). Not
    proof: a quiet-host full run (run x) is the confirmation, and the gap is listed as an open
    observation until then.

479. Load-aware budget candidate (E1) implemented as scoped in 477, uncommitted, with two
    departures recorded here (2026-10-21, evidence/affa19/budget-20261021): (1) an outer bound
    the inventory missed: owner._deadline rejects any request deadline beyond now + 5 s
    (ML-OWNER-DEADLINE, channel failed); a first version widened a terminal per-unit window to
    about 10 s and lost the terminal, so every interior cap includes now + 5 (the whole-run
    teardown keeps its 80 s bound). (2) M1 refinement: the stop/cleanup dispatch check also
    requires the phase estimate to fit the normal share of the window the effect can actually
    get, not only the time before the active end, because in the lazy native profile the
    lease-renewal margin (service_calls x op + op, about 2-2.5 s) caps M2 for active effects.
    Files: service_time.py (new, 43 lines), dispatcher.py (+162), teardown.py (+82/-26),
    tests/thesis_lite/maestro/test_load_aware_budgets.py (new, 185 lines). Controls (candidate
    venv verified equal to src, head = dabf858a5 product): (e) sizing identity property, 2000
    random cases; (a) +0.15 s per record with a seeded slow phase completes normally where the
    head ends TEARDOWN-INCOMPLETE; (b) seeded 3600 s phase:stop gives SERVICE-DEADLINE, every
    stop/cleanup step blocked, normal terminal cleanup, finalizable report, offline complete;
    (c) seeded restart:unit is rejected with ML-SCHEDULE-RESTART-DEADLINE unmutated; (d) widening
    stays within every outer bound, no lease exhaustion (bounds check, not discrimination); (g)
    ML-TEARDOWN-RECORD-BUDGET visible. Candidate 6/6 pass, head fails each discriminating
    control. Existing guard controls, T3, DV09 and both C1 modules: 37 passed at load 6.9.
    Affected modules under rising load (6.8 to 16.6): every failure carries a load-class code and
    the head fails the same tests on rerun (5/5 and 9 vs 8). Interior trace: at load about 6 the
    nominal phase spans are about 0.1 s against today's 0.3 s normal share, so no widening and no
    M1 stop (quiet identity shown on the nominal fixture only); at load 12-15 (24 dispatcher
    runs) zero widenings (lease margin caps them) and four M1 stops, all at step-dispatch.
    Reading: in this profile the benefit comes mainly from M1 (emergency ends become documented
    failures), not from widening. Open: first-of-kind phases fail open; lifetime maxima can cause
    false M1 refusals; natural-load A/B (477 (iv)) and independent review owed. A/B e starts now:
    the host is loaded by its own external process.

480. Independent review of the load-aware budget candidate (479): FAIL (2026-10-21), recorded
    before any repair. (1) HIGH: dispatcher _run_end widens with a cap of _work_end minus the
    post-teardown reserve only; teardown._deadline rejects a run deadline more than 80 s away
    (ML-TEARDOWN-DEADLINE). At the head the bound held by construction (n x per_unit_seconds,
    n <= 16, per_unit <= 5); with widening, any need above the normal share gives now + need +
    0.4 w, and when the terminal slack exceeds 80 s (possible after an early failure in a long
    active window, horizon up to 394 s) run() raises, _cleanup raises, and the run ends
    ML-SCHEDULE-CLEANUP-INCOMPLETE with no unit cleaned by Maestro. The 479 sentence "the
    whole-run teardown keeps its 80 s bound" was not enforced in code. (2) MEDIUM: the M1
    step-dispatch check reads health and lease state before _service() refreshes it, so after
    restart or quiesce work it can refuse a step the head would dispatch (safe: no mutation,
    documented failure; but a false refusal, also on a quiet host once a phase estimate exists).
    (3) MEDIUM: the _run_end and run() widening ignore the lease and health caps of ADR item 3.
    (4) LOW: the F-09 record estimate now survives teardown replacement (shared estimator; a
    behaviour change not recorded in 479). (5) LOW: teardown._split widens inside declared
    action-timeout deadlines (never beyond them), contrary to the ADR wording. (6) LOW: NaN or
    negative seeds bypass ServiceTimes.observe and fail open. (7) LOW tests: (e) checks _split
    with approx, (b) restates the reserve formula, (d) prints but does not assert scans and
    renewals, (a) accepts two outcomes. (8) LOW: work after a widened effect is reserved only
    for step-complete. Verified OK: _end M2 never exceeds any bound; quiet identity exact for
    sized() and _split; emergency share kept; M1 refusals before any mutation; estimator max-only;
    observational lists unread by product code; discrimination of (a), (b), (c), (g).
    Repair scope: (1)+(3) cap the terminal _run_end widening by now + 80 s minus 1 s, every live
    lease minus the renewal margin and health minus scan and renewal margin, and add a control
    with more than 80 s of terminal slack and a large seeded estimate that fails on the 479
    candidate; (2) refresh service state (_service()) before the M1 fit check, so the check sees
    the window the dispatch will get; (5) ADR wording: the teardown split may widen up to, never
    beyond, a declared action-timeout deadline; (6) ServiceTimes rejects non-finite or negative
    values on every write path, and _send writes through observe; (7) controls tightened: exact
    equality, outcome pinned, scans and renewals asserted; (4) and (8) recorded as accepted
    behaviour. A/B e runs on the 479 venv; its result is read as evidence for the M1/M2 effect
    under load, and the repaired candidate gets its own targeted reruns and a second review.

481. A/B e (2026-10-21, evidence/affa19/ab-budget-loaded-20261021e; driver
    ab-budget-loaded-20261021e.py; expectations of 477 (iv) recorded before the run). Arms on the
    12 load-sensitive tests of 467: A = head without E1 (dabf858a5 product), B = the 479 candidate
    (before the 480 repairs). External load from another project's llama-server; 4 interleaved
    pairs; load 12.3 (A) and 14.1 (B) in pair 0, then 6.1 to 9.1. Failed tests of 12 per run:
    pair 0 A 8, B 1; pair 1 B 0, A 0; pair 2 A 1, B 1; pair 3 B 0, A 0. Totals A 9, B 2. Codes: A
    ML-SCHEDULE-TEARDOWN-INCOMPLETE 5, ML-PERSIST-TIMEOUT 2, ML-SCHEDULE-SERVICE-DEADLINE 1, 6 v2
    refusals; B ML-SCHEDULE-SERVICE-DEADLINE 1 (paused shared ticks, pair 2) and one transitive
    [cleaned-leaf] failure whose restart result carries ML-PERSIST-TIMEOUT (pair 0, load 14.1;
    _restart_unit is not widened by design, 477). Against the pre-registered expectations: B
    failures at most A's (2 vs 9) holds; fewer ML-PERSIST-TIMEOUT (dispatcher diagnostics 0 vs 2;
    one more inside a restart result) and ML-SCHEDULE-TEARDOWN-INCOMPLETE (0 vs 5) holds; no new
    failure class holds (both B codes occur in A's class). Limits: one pair at load above 10;
    the arm is the 479 candidate, so the 480 repairs (terminal cap, M1 service refresh) are not
    covered by this A/B; persist timeouts inside restart operations remain possible by design.
    Reading: E1 removes the dominant F-08/F-09 failure modes at the load reached here; the
    remaining exposure is the unwidened restart path and active-window exhaustion (outer).

482. Second independent review of the repaired budget candidate (after 480): FAIL (2026-10-21),
    recorded before any change. (1) HIGH, confirmed by the run log (budget-20261021/
    repair-set1.log, load 5.8: 1 failed, 69 passed): control (a) fails on the repaired candidate
    (client._failed, the persistence channel failed), and the dispatcher trace shows no terminal
    widening. Cause: the 480 (3) cap includes min(live leases) minus the renewal margin
    (service_calls x op + op, about 2 s), while the bootstrap lease is renewed to at most now +
    5 s, so the cap sits at or below today's n x per-unit window and _run_end returns today's
    window. The renewal margin protects renewals between active operations, but no renewal
    happens inside teardown.run(): in the lazy profile every terminal record itself renews the
    lease through service_terminal, and in the non-lazy profile nothing renews during run(). The
    480 (3) reading of ADR item 3 for the terminal run was therefore wrong. A/B e (481) ran on
    the 479 arm, so its terminal benefit does not carry over to the 480 state. (2) MEDIUM: the
    480 (2) _service() call runs before every step-dispatch, not only before a stop/cleanup step
    with an estimate; on a quiet host scans/renewals can move before the step-dispatch statement,
    controller-recovery drain can run between admission and dispatch, and an exception there
    leaves the step blocked where the head records it failed. (3) LOW: the v2 guard still reads
    the raw _service_seen dict (alias of ServiceTimes.seen), so 480 (6) "every write path" is not
    closed by construction. (4) LOW: ValueError("ML-SERVICE-TIME-ESTIMATE") is a new code string,
    contrary to ADR item 7 (reachable only through the test-only setter). (5) LOW tests: the
    estimator test's statement_max check is vacuous (":" kinds are excluded); (d) does not assert
    scans; (h) does not exercise the health or teardown_deadline caps. (6) LOW: statement_max
    iterates the shared dict without a snapshot. (7) LOW: the finished-restart deferral appends a
    trace entry on every inner-loop pass.
    Repair scope: (1) the terminal _run_end cap becomes work_end minus post reserve, now + 79 s,
    the boundary teardown deadline and, in the non-lazy profile only, the live leases themselves
    (no renewal margin; nothing renews inside run()); no lease cap in the lazy profile, where the
    terminal records renew it; health is not a cap there (next_health_deadline is None once the
    latch is cancelled) and is dropped; ADR item 3 and 480 (3) corrected accordingly. (2) the
    pre-check _service() runs only for a stop/cleanup step whose phase estimate is non-zero
    (inside the M1 check, after its early returns). (3) the v2 guard reads est(). (4) the guard
    raises a plain ValueError naming the argument, no ML- code; ADR item 7 stands. (5) tests: a
    statement kind in the statement_max check, health scans asserted where the fixture scans,
    (h) cases for the teardown_deadline cap and for the lazy/non-lazy lease rule. (6) snapshot
    iteration. (7) trace a deferral once per ticket. Then rerun (a)-(h), the guard, T3, DV09 and
    C1 sets, and a third review.

483. 482 repairs applied (2026-10-21; budget3 venv verified equal to the worktree src). The
    terminal _run_end cap is work_end minus post reserve, now + 79 s, the boundary teardown
    deadline, and in the non-lazy profile the live leases themselves; the pre-check _service()
    runs only inside the M1 check after its early returns; the v2 guard reads est(); the
    estimator's guard raises a plain ValueError; statement_max iterates a snapshot; a deferred
    finished-restart quiesce is traced once; tests: statement kind in the estimator check, (h)
    cases for the lazy/non-lazy lease rule and the teardown_deadline cap. Controls set (budget
    controls a-h, estimator, guard controls, T3, DV09, both C1 modules, gate tests) on budget3 at
    load 10.1 to 9.5: 70 passed, control (a) included. Recorded before A/B f: the affected-module
    set on the 480 state (budget2) at load 6 rising to 17 had 35 failed / 103 passed, every
    failure with a load-class code (ML-SCHEDULE-SERVICE-DEADLINE 10, ML-PERSIST-TIMEOUT 7,
    ML-SCHEDULE-TEARDOWN-INCOMPLETE 6, ML-RUN-ORIGINAL-END 2, ML-OWNER-DEADLINE 1; the last also
    fires when a deadline has already passed and appears in head-only logs: A/B d2 arm A, the
    433 A/B arm A, DV03/DV04 run 1). A/B f (ab-budget-loaded-20261021f.py): arms A = dabf858a5
    product, B = budget3, on the union of those 35 nodes and the 12 tests of 467
    (budget-20261021/ab-f-nodes.txt), 2 interleaved pairs under whatever external load the host
    carries, recorded per run. Expectation: B failures at most A's per pair at comparable load,
    no failure class in B absent from A, fewer ML-SCHEDULE-TEARDOWN-INCOMPLETE and
    ML-PERSIST-TIMEOUT in B.

484. Third independent review of the budget candidate (483 state): PASS, no HIGH or MEDIUM item
    (2026-10-21). Verified: lazy terminal records renew the lease (persistence.py record_teardown
    -> session._service_terminal, bootstrap.py renews to min(now + 4.9 s, generation - 2 s)) and
    the native STOP/RETIRE after CANCELLED skip the connection-lease check, so the uncapped lazy
    run() deadline cannot cause ML-RUN-ORIGINAL-END; nothing renews inside a non-lazy run(), so
    the live-lease cap there is right; the moved _service() is behaviour-neutral (the head already
    serviced before the step-dispatch send, and an exception there already left the step blocked;
    482 (2)'s premise was mostly wrong); all 482 (3)-(7) repairs complete. LOW items and
    dispositions: (1) a lazy per-unit lease tail of about 0.1 s when per_unit < 5 and widening
    applies (the head had the same window at per_unit = 5): accepted limit. (2) M1 checks stop
    plus cleanup against one normal share, which is stricter than the head in a narrow band
    (example: op 0.5, per_unit 1, stop 0.16 s, cleanup 0.17 s, a lease 2.0-2.6 s away): accepted as
    a known conservative bias; the outcome is a documented failure, never an unsafe state. (3) a
    closure-path run() (run_closure.py, up to now + 80 s) can widen beyond live leases in the
    non-lazy profile, as the head could whenever n x per_unit exceeded about 5 s: accepted, ADR
    wording corrected to state the lease cap as a property of the dispatcher's terminal window,
    not of run(). (4) the _run_end comment on health is inaccurate for the non-lazy success path:
    corrected (no consumer inside run() reads it). (5) tests: (h) does not exercise gate leases,
    the 482 (5) health assertion was dropped because the fixture scans 0 times (BUDGET-D logs
    scans 0), (a) is pinned to a single M1 stop and may flake under load, repair2-set1 ran
    without -s: recorded, not repaired. (6) the 480 repair-scope text and ADR item 3 lead
    sentence are superseded by 482 (1): corrected in the ADR; 480 stays as recorded history.

485. A/B f (2026-10-21, evidence/affa19/ab-budget-loaded-20261021f; expectations of 483 recorded
    before the run). Arms A = dabf858a5 product, B = budget3 (483 state), 39 tests (the 35 set-2
    failures of 483 and the 12 tests of 467), 2 interleaved pairs. Load at start/end: pair 0 A
    10.6/7.8, B 7.8/8.6; pair 1 B 8.6/5.8, A 5.8/12.3. Failed tests: pair 0 A 5, B 1; pair 1 B 0,
    A 20. Totals A 25 (ML-SCHEDULE-SERVICE-DEADLINE 9, ML-SCHEDULE-TEARDOWN-INCOMPLETE 4,
    ML-PERSIST-TIMEOUT 2, ML-BOOT-CLOSED 1, ML-OWNER-DEADLINE 1, the rest without an ML code
    in the assertion line), B 1 (paused shared ticks, ML-SCHEDULE-TEARDOWN-INCOMPLETE, which A
    also failed). No B-only failure. Against the expectations: B at most A per pair holds; no
    class in B absent from A holds; fewer TEARDOWN-INCOMPLETE (1 vs 4) and PERSIST-TIMEOUT (0 vs
    2) holds. Limit: load was not matched within pair 1 (A's run saw it rise to 12.3); two pairs.
    With A/B e (481) this supports E1 as removing the dominant F-08/F-09 failure modes under the
    load seen today; active-window exhaustion (outer bound) and the unwidened restart path remain.
    Next: commit E1 (budget3 state plus the 484 comment and ADR corrections), CAPA step 4, then
    the full installed-wheel run on the final head under the quiet-host watcher (469 (3), E3).

486. CAPA successor step 4 (2026-10-21, evidence/affa19/capa-20261021-affa19-step4, builder
    build-capa-20261021-affa19-step4.py), parent step 3 (dc3a67a8…), additive: review spans
    473-485, the gate repair and refusal controls (dabf858a5), the E1 patch (897d9dc50 against
    its parent), the budget evidence and A/B e/f. ML-CAPA-418 (F-08/F-09) stays FIX_CANDIDATE, now
    on E1 (load-aware interior budgets) with v2 kept as the last pre-send check; three reviews
    (FAIL, FAIL, PASS) and the natural-load A/Bs e and f; effectiveness not claimed beyond the
    observed load. ML-CAPA-359 notes E1 as its tracked correction (cause still HYPOTHESIS). No
    record closed, no cause verified. This finding is bound by the next successor.

487. Run x (2026-10-21, evidence/affa19/platform-regression-20261021x; driver
    verify-platform-regression-20261021t.py started by run-x-quiet-watch.sh; head 98595161d,
    product 897d9dc50, wheel sha 94fe115e…, 2251 collected). Trigger at 16:19:48Z after five
    quiet checks (load 5.76); another project's llama-server started about 2 min after launch
    (elapsed 3204 s of 3341 s at the end sample) and the end load was 10.41. Result: 2249 passed,
    1 skipped, 1 failed: the Argus nested suite (test_argus2_integration.py:173), whose nested
    Maestro run (the first half of the outer run, under the llama-server load) had 9 failures:
    controller recovery [cleaned-then-restart], active restart [leaf, external-thread,
    parent-reject], transitive restart [cohort, cleaned-leaf], shared schedule ticks, and RPC
    context loss [context-reference, context-content]. The same 9 tests passed in the outer run.
    Codes in the nested work directories: ML-SCHEDULE-SERVICE-DEADLINE, ML-SCHEDULE-TEARDOWN-
    INCOMPLETE, ML-SCHEDULE-OPERATION-FAILED, i.e. the budget class of F-08/F-09, concentrated on
    the restart paths that E1 leaves unwidened by design (477, 481, 485). Rerun of the 9 on the
    run's own frozen tree and venv at load 9.5-10.6: rep 1 one failure ([cleaned-then-restart],
    ML-SCHEDULE-SERVICE-DEADLINE), rep 2 none (nested-rerun.log). DV12 gate: not accepted,
    blocker B2-failures 1 (dv12-gate-verdict.json, sha 45cf01c6…). Classification under 469: the
    recorded end load exceeds 10, so the run is an observation, not a regression signal, and E3
    is not met. Limit: run x recorded load only at launch and end, so the load during the nested
    phase is unknown. Repair to the evidence procedure (not to the product): run-y-quiet-watch.sh
    keeps the run-x quiet condition and adds a 30 s load sampler for the whole run
    (load-samples.jsonl), so 469 is applied to in-run samples. Next: run y on the head carrying
    this finding. If the restart class recurs on a run whose samples stay at or below 10, it is
    a regression signal against E1 and the restart path is reopened as a design item; it is not
    waived. Receipts archived (receipts.tar.gz) and the tmpfs work directory removed.

488. Run y (2026-10-21, evidence/affa19/platform-regression-20261021y; run-y-quiet-watch.sh; head
    5eae7d746, product 897d9dc50 unchanged in code scope). Trigger 20:03:38Z (load 6.03); 109
    in-run samples, 1-minute load 5.16-13.01, 25 samples above 10. Result: 2249 passed, 1
    skipped, 1 failed, again only the Argus nested suite, whose nested Maestro run had 6 failures
    (transitive restart requires new generations; launcher startup [lost-close-ack]; lazy nominal
    stages; storage full [C0-never-armed]; native stream fault [seeded-flush-once,
    seeded-flush-persistent]); the outer run of the same tests passed. Codes in the nested work
    directories: ML-SCHEDULE-SERVICE-DEADLINE only. The failing set differs from run x (487)
    except for the restart family, so the failures are timing failures spread over budgeted
    paths, not a fixed defect. DV12 gate: not accepted, B2-failures 1 (sha a4a2f754…).
    Classification under 469: samples above 10, so an observation; E3 not met.
    Nested-versus-outer asymmetry (runs v, x, y: nested failures 12, 9, 6; outer 0, 0, 0). Two
    readings were examined. (a) Leftover processes or threads from the Argus tests that run
    before the nested suite: refuted for this head; an observation-only session-finish probe
    over the Argus tests (nested test deselected) found no live descendant process and only the
    main thread (leak-probe/; its 2 failures are the probe's own PYTHONPATH, which those two
    tests forbid). (b) Load: in run y the nested phase (about 20:04-20:32) had mean load 8.61
    with 16 samples above 10, the outer phase mean 9.16 with 9 samples above 10, so short
    bursts were more frequent during the nested phase; consistent with load, not decisive.
    Status: HYPOTHESIS (load bursts), the asymmetry remains an open observation for T06. Limit:
    nested-failure-dirs.tar.gz lacks the transitive-restart directory (not in the archived
    session directory). Procedure (delegated E3, no waiver): run-z-quiet-loop.sh repeats the
    run-y procedure on one head until a run is decisive: clean, or failed with every sample at
    or below 10 (then the 487 rule applies: regression signal, budgeted paths reopened as a
    design item); runs with samples above 10 are archived as observations and repeated; overall
    bound 10 h. Receipts archived and the tmpfs work directory removed.

489. Loop z (2026-10-21/22, run-z-quiet-loop.sh, head 34e140f57, product 897d9dc50): decisive
    after two attempts. z-1 (trigger 21:31:00Z; 116 samples, load 4.33-14.14, 45 above 10): 6
    outer failures and 7 nested failures: restart family, paused (shared) ticks, native writer
    failures [fsync-persistent, artifact-check], registry whole-run replay, and outer
    test_load_aware_budgets.py::test_widened_deadlines_stay_inside_every_outer_bound; gate
    B2-failures 6 (sha 87b52df1…); observation under 469 except the last test (below). z-2
    (trigger 06:56:56Z; 87 samples, load 3.70-5.09, none above 10): 2248 passed, 1 skipped, 2
    failed, namely the same control (d) test_widened_deadlines_stay_inside_every_outer_bound
    both in the outer run and as the only nested failure (so the Argus test failed too); gate
    B2-failures 2 (sha 4c823b32…). Under the 487 rule z-2 is a regression signal; it is read
    here before any repair. All three failures stop at test_load_aware_budgets.py:171,
    `assert driver.lease_renewals >= 1`, with result.execution_succeeded, diagnostic None,
    widening present, every active deadline at or below the active end, every deadline at or
    below the work end, no stop, scans 0, renewals 0 (BUDGET-D). Cause (verified by reading
    dispatcher.py:1110-1199): _service renews only when a live lease is within the renewal
    margin (service_calls x operation_seconds + operation_seconds) or a health scan is due
    inside that reserve; leases are about 5 s ahead, so a run that completes before any lease
    comes due makes no renewal, and the count depends on run duration and on where the lease
    phase falls, not on E1. The assertion was added by the 480 (7) repair ("scans and renewals
    asserted"); the scan half was already dropped in 483/484 (5) for the same reason ("the
    fixture scans 0 times"). Classification: test-oracle defect in E1's own control (d), not a
    product defect: nothing in the failing runs shows a lapsed lease, a missed due renewal or
    a budget violation, and z-2 is otherwise clean on a quiet host (2248 of 2249 other outer
    tests and 1965 of 1966 nested). Repair scope (test only, no product change): replace the
    count with an invariant oracle over every _service entry during the run, namely (i) no live
    lease has lapsed at entry and (ii) whenever a live lease is within the renewal margin at
    entry and _service returns, the renewal count has increased; keep the run unchanged and
    record how many entries were due, so a run with no due entry is visible as vacuous for (ii)
    (limit, not a failure). The 487 design reopening is not triggered by this signal: its
    premise (a budget-class failure at low load) does not hold. Next: independent review of
    the repair, targeted reruns of the file, then a new full run on the repaired head through
    the loop.

490. 489 repair applied (test only, tests/thesis_lite/maestro/test_load_aware_budgets.py; no
    product change, product still 897d9dc50) and reviewed. Helper spy_service_points records every
    FiniteDispatcher._service entry of the control's driver (lease set and margin as
    dispatcher.py:1116-1121); control (d) asserts (i) no live lease lapsed at any entry and (ii)
    every entry with a lease inside the renewal margin that returns has raised the renewal count;
    the count assertion is removed. The number of due entries is written to
    budget-d-service-points.json under the boundary-receipt namespace, so a full run's archived
    receipts show whether (ii) was exercised. Reruns on the budget4 venv (src equal to the
    worktree) at load 3.4-3.6: 6 file runs, 8 passed each; due points 0, 0, 1, 0, 1, 0, with
    renewals only in the runs that had a due point, which confirms 489's cause. Mutant
    (_renew_service a no-op): fails in 1 of 4 runs (the run with due points), passes otherwise;
    so (ii) discriminates only when a lease comes due. Independent review: PASS, no HIGH.
    Cause analysis confirmed (renewal only inside the 2.5 s native margin; leases about 5 s
    ahead; a lapsed lease would be rejected by bootstrap.renew, so successful runs show none
    missed); (ii) is guaranteed whenever _service returns, including the native early return
    after controller recovery (the drain counts +2), so no false failure. MEDIUM (vacuous case
    visible only under -s): repaired by the receipt above. LOW: docstring overstated the oracle
    in the non-native profile (one bootstrap renewal satisfies (ii) even if a gate is skipped):
    reworded; margin written as n x op + op to mirror dispatcher.py:1117: done; conditional
    discrimination of (d): accepted limit, because test_shared_dispatcher.py:148-160 forces
    native renewals by a time floor (73 ticks x 0.05 s > 2.5 s margin) and asserts that the
    lease values advanced. Observation, not repaired: test_dispatcher.py:307-314 (non-native)
    also uses a renewal count (>= 3) whose floor is only just above its margin; it failed in
    z-1 under load (samples above 10) and is kept under T06 observation. Next: commit, then the
    loop on the repaired head; E3 still requires a clean run, the gate and a CAPA successor.

491. Run 22a-1 (2026-10-22, evidence/affa19/platform-regression-20261022a-1; run-z-quiet-loop.sh,
    decisive at attempt 1; driver verify-platform-regression-20261021t.py; head af9bd3c72,
    product 897d9dc50 plus the 490 test repair; 2251 collected). Trigger 07:53:09Z at load 3.29;
    90 in-run samples, 1-minute load 3.70-8.29, none above 10. Result: 2250 passed, 1 skipped
    (lane admission, its own driver), 0 failed, 24 subtests passed in 2691 s; returncode 0, no
    outer timeout, descendant cleanup known; the Argus nested suite passed (its nested run had
    no failure). Control (d) receipts: outer and nested each recorded 56 service points with 1
    due point, renewed before return (budget-d-service-points.json), so invariant (ii) was
    exercised in both. DV12 gate (candidate af9bd3c72, scope code, G4 and allowlist inputs of
    468): accepted_as_evidence true, no blocker, run and candidate code sha f25a295d…
    (dv12-gate-verdict.json sha fdb188ae…, SHA256SUMS sha f847dec7…). Against 476 E3: (1) a
    clean full installed-wheel run on the final head with host load recorded: met; (2) DV12 gate
    passing: met; (3) no open HIGH or MEDIUM review item: met (474 items repaired in dabf858a5,
    480/482 repaired and 484 PASS, 490 PASS with its MEDIUM repaired); (4) validated CAPA
    successor: step 5 next. Limits carried: effectiveness of E1 is shown only up to the loads
    observed (about 14); the nested-versus-outer asymmetry (488) and the test_dispatcher.py
    renewal-count oracle (490) remain T06 observations; one clean run is not a reliability
    estimate.

492. CAPA successor step 5 (2026-10-22, evidence/affa19/capa-20261022-affa19-step5, builder
    build-capa-20261022-affa19-step5.py), parent step 4 (7b384e75…), additive: review spans
    486-491, the quiet-host procedure (run-x/run-y watchers, run-z loop), the full-run evidence
    of x, y, z-1, z-2 and the decisive run 22a-1 with its gate verdict, and the control (d)
    oracle repair (f1f0b630e..af9bd3c72, tests only). ML-CAPA-418 stays FIX_CANDIDATE on E1; the
    increment19 block records the decisive run and its accepted gate, with the increment not
    yet accepted or merged at build time. No record closed, no cause verified, no effectiveness
    claimed. Register sha a934c2d8…, 56 records / 644 bindings; verify-capa-register-20261020.py
    (verification.json) and check-capa-parent-preservation-20261019.py (627 parent bindings
    checked, none changed, no record lost) both pass. The first build attempt was refused by the
    schema (root_cause_summary above 2000 characters); the run narrative moved to the action
    plan. This finding is bound by the next successor.

493. Increment 19 acceptance (2026-10-22) under the author's delegation (476 E3: "accept increment
    19, merge into platform main and push, only when all hold"). All four conditions hold: clean
    full installed-wheel run on the final head with host load recorded (491, run 22a-1 on
    af9bd3c72, 2250 passed, 0 failed, load at most 8.29); DV12 gate accepted (491); no open
    HIGH or MEDIUM review item (491); validated CAPA successor (492, step 5, a934c2d8…, both
    validators pass). Decision: increment 19 ACCEPTED for engineering integration and merged
    --no-ff into platform main, then pushed to origin. Scope of the acceptance: engineering
    increment only; it does not open lane activation, M1, factory runs or any scientific claim,
    does not change RF-2026-08-30-v6 or AEB-EXPERIMENT-2026-08-30-v2, and does not decide T07
    (E4: T07 after T01-T06 with G4 re-decided and source-parent fidelity carried as a limit).
    Carried limits: 468 C4, 484 LOW items, 488 asymmetry and 490 observations, E1 effectiveness
    only up to the observed load, ML-CAPA-418 FIX_CANDIDATE and ML-CAPA-359 HYPOTHESIS.
    This finding is bound by the next successor.

494. Post-acceptance record and task rulings (2026-10-22, under the author's delegation of 476).
    Merge facts: candidate cdac0eb77 merged --no-ff into /home/jefferson/xverse-platform main as
    63f5cb8c7 (parent 557619e0c); the merged tree equals cdac0eb77 (empty diff); main pushed,
    origin/main = 63f5cb8c7; the author's four untracked files in that checkout untouched.
    Rulings on the open P3 tasks against the signed-off closure criteria
    (specs/024-maestro-lite-lifecycle/review/task-closure-assessment-20261021.md):
    (1) P3-T03 closes. Its last blocker was F-08/F-09. E1 load-aware budgets are accepted with
    the increment; the decisive run 22a-1 is clean; under external load above 10 the budgeted
    operations still end as documented, fail-closed failures (runs x, y, z-1; 469), never as
    an unsafe or unreleased state. Stated operating limit: on this host, timing outcomes are
    claimed only at sampled 1-minute load at most 10; ML-CAPA-418 stays FIX_CANDIDATE.
    (2) ML-CAPA-337 moves from UNRESOLVED/UNKNOWN to TRIAGED/HYPOTHESIS: its first retained bad
    RPC (review-affa17.md finding 337) is a source-generation-1 teardown record that timed out
    with ML-PERSIST-TIMEOUT inside a 0.25 s window, the F-09 signature (a teardown record sent
    with less remaining time than its service time); no recurrence in the quiet step-4 campaign
    (464) or in the clean run 22a-1; E1 is its tracked correction. Supported, not confirmed.
    ML-CAPA-286 (registry recovery / nominal lifecycle) stays UNKNOWN: no signature links it to
    F-08/F-09 and it did not recur (464, 22a-1); it is carried as a stated limit of P3-T05.
    (3) P3-T05 closes: the DV09/DV10 gaps are closed (F-10 and the C1 D-09 fix are accepted with
    the increment), 337 is classified as above and 286 is carried as a limit.
    (4) P3-T06 closes: one clean full installed-wheel run on the final head (491), DV12 blocking
    and accepted (491), the expected-table check (19-1), the complete independent review (474,
    READY) with every later product change reviewed (480/482/484, 490). Observations carried:
    488 nested-versus-outer asymmetry, 490 renewal-count oracle in test_dispatcher.py.
    (5) P3-T07 is not decided here. Its task text requires explicit author acceptance of the
    feature acceptance package; E4 placed it after T01-T06 with G4 re-decided and source-parent
    fidelity carried as a limit. The package is prepared for the author; no feature acceptance
    is claimed. Next: CAPA successor step 6 for (2), then a documentation-only merge to main.

495. CAPA successor step 6 (2026-10-22, evidence/affa19/capa-20261022-affa19-step6, builder
    build-capa-20261022-affa19-step6.py), parent step 5 (a934c2d8…), additive: review spans
    492-494; ML-CAPA-337 UNRESOLVED/UNKNOWN -> TRIAGED/HYPOTHESIS (494 (2)), tracked with
    ML-CAPA-418; ML-CAPA-286 unchanged (UNKNOWN, limit of P3-T05); the increment19 block records
    the acceptance (493) and the merge 63f5cb8c7. No record closed, no cause verified, no
    effectiveness claimed. Register sha fb8d7058…, 56 records / 647 bindings; both validators
    pass (644 parent bindings checked, none changed, no record lost). This finding is bound by
    the next successor.
