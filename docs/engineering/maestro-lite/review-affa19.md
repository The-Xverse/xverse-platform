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
