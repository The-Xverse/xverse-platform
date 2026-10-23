# Review log: Thesis Lite stabilization S1a (persistence scaling and cancel closure)

Candidate: `candidate/lite-stabilization-s1a-20261023`, base main `8b3d8c8e8`. Authoritative specification:
thesis repository `specs/029-lite-stabilization` (rev 4a). Gate ES-0 met by the author's decisions of
2026-10-23 (`review/author-decisions-20261023.md` there). Findings are recorded before repairs. The
maturity is an engineering stabilization candidate: not M1, not AEB evidence, not a scientific result.

Bench tooling lives in `tools/bench/persistence_scaling/`, outside the pytest collection of the platform
suite (FR-002). The bench virtual environments and run data are on the loop10 image:
- `.x-verse-build/cache/lite-stabilization-s1a/` (wheels, `venv-main`, `venv-main-trace`);
- `.x-verse-build/runs/lite-stabilization-s1a/`.

## Findings

1. **Run length is bounded by the 90 s run-closure cap, not by the 300 s active window (2026-10-23 10:07,
   bench smoke-1).**
   - **What happened.** The first benchmark harness set the run's closure deadline about 150 s ahead.
     `_OriginalRuntimeRun._validate_scope` refused it with `ML-RUNTIME-ENTRY-END`
     (`src/xverse/maestro/runtime_entry.py:105-113`: `scope.closure.monotonic_seconds - now > 90`).
     `run_closure.py:224` applies the same bound.
   - **Origin.** The bound comes from the frozen unit contract
     `docs/engineering/maestro-lite/unit-specification-closure15.md:3-4`: the "total caller end within
     original generation and at most 90 seconds away".
   - **Consequence.** The whole run, from entry through active time, terminal reserve and closure, must fit
     in 90 s. With the Phase 7 terminal reserve of about 21 s plus collection and terminal budgets, the
     active window is at most about 60 s. The spec's S-D1 target (1 200 Maestro ticks in a 300 s active
     window) is therefore infeasible without amending the closure15 contract, and FR-002's 8 192-event
     capacity cannot be reached by an admitted run.
   - **Not a defect of S1.** The cap is a deliberate bound of the accepted closure design.
   - **Proposed S-D1 revision**, recorded before use under the author's delegation (thesis
     `specs/029-lite-stabilization/review/author-decisions-20261023.md`):
     - Keep the 90 s cap. Amending closure15 is not part of S1.
     - The long-run is the largest horizon that the cap admits with 4 units: an active window of about
       55–60 s and a target of 500 Maestro ticks. This needs a mean dispatcher cycle of at most about
       0.11 s.
     - FR-002 is measured up to the event count of that longest admissible run (and of the 8-unit
       benchmark run). The 8 192 admission capacity is reported, not driven.
     - A Phase 8 horizon beyond about 60 s of wall time needs a separate author decision to amend
       closure15. It is carried to AD-25.
2. **S1-T01 profile on main `8b3d8c8e8` (2026-10-23 10:09, run `t01-main-4u-h300`).**
   - **Run.** 4 dummy units, horizon 300, active window 55 s, operation budget 0.38 s, sampled load
     4.28–4.58. The worker trace comes from `xverse_bench_trace` in the bench-only venv; the shares are
     of the worker's per-request handling time, and nested parts overlap.
   - **Outcome.** The run failed with `ML-SCHEDULE-SERVICE-DEADLINE` after 421 Argus events and 683
     persistence round trips. That is the dispatcher's guard against the longest observed round trip
     (research R-1, review 1 finding 5), reached before `ML-PERSIST-TIMEOUT`. The client round trip was
     p50 64 ms, p99 321 ms, max 471 ms; the decile means rose from 30 ms to 148 ms.
   - **Shares per decile:**

     | Part | Share of handling time | Research row |
     | --- | --- | --- |
     | `argus.read_run` (full verified re-read) | 0.52–0.61 | A |
     | `outcomes.same_json` (comparison against earlier events) | 0.26–0.30 | B |
     | `outcomes.history` | 0.06–0.10 | — |
     | `m3.reload` | 0.07–0.14, rising | C |
     | `argus.append_event` and `flush_buffer` | ≤ 0.005 | — |

   - **Growth.** The mean handling time rose from 23 ms to 178 ms per request. The cost of one `read_run`
     grows by 0.156 ms for each event already recorded (linear fit).
   - **Expensive request kinds.** probe (130 requests, mean 172 ms), teardown (280 ms), tick-complete (225,
     103 ms), step-complete (136 ms) and audit (84 ms).
   - **Verdict.** Hypotheses A and B are confirmed as dominant (together about 85% of handling time) and C
     as secondary. fsync and append are ruled out. The prefix hash that FR-003 keeps is not measured
     here: the stream is about 1.3 KB per event, so about 0.55 MB at 421 events. It is expected to be
     well under 1 ms per check and is measured after the repair (FR-002).
3. **A run admits at most 5 units, bounded by the 64 KiB persistence configuration (2026-10-23 10:11, runs
   `size-probe-*`).**
   - **What happened.** `bootstrap.py:1109-1118` refuses a `PersistenceInput` whose private bytes exceed
     65 536 (`ML-BOOT-PERSISTENCE`). The encoded configuration grows by about 10 KiB per unit and hardly
     with the horizon:
     - 4 units: 49 805 bytes at h300 and 48 996 at h100;
     - 5 units: 59 075;
     - 6 units: 69 250 (refused);
     - 8 units: 90 617 (refused).
   - **Consequence.** The spec's 8-unit benchmark configuration (FR-002, review 2 N7) cannot be admitted.
     The FR-002 multi-unit benchmark uses 5 units, the admitted maximum, recorded under the author's
     delegation.
   - **Phase 8.** The AEB blueprint needs more than 5 Maestro units, so this is a new Phase 8 gap. It is not
     repaired in S1a.
   - **Proposal.** Raise the bound in S1b, which already changes the sealed configuration (stderr
     registration, probe declarations), or in a separate successor. Any stderr or probe field added in
     S1b adds bytes per unit, and the S1b design must state the resulting unit maximum.
4. **S1-T02 baseline curves on main (2026-10-23 10:09–10:13).**

   | Run | Units | Operation budget | Outcome | Events | Round trip p99 / max | Decile means |
   | --- | --- | --- | --- | --- | --- | --- |
   | `t01-main-4u-h300` | 4 | 0.38 s | `ML-SCHEDULE-SERVICE-DEADLINE` | 421 | 321 / 471 ms | 30 → 148 ms |
   | `t02-main-5u-h300` | 5 | 0.2 s | `ML-PERSIST-LATE`, cleanup incomplete | 293 | 311 / 579 ms | 39 → 73 ms (decile 9: 151 ms) |

   - **Load.** At most 4.6.
   - **Earlier attempts (harness errors).** `t02-main-8u-h300-bootfail` and `-bootfail2` show finding 3;
     `smoke-1` shows finding 1.
   - **Run data.** On loop10 at `.x-verse-build/runs/lite-stabilization-s1a/`, each with `summary.json`
     from `tools/bench/persistence_scaling/analyze.py`.
5. **S1-T03: a cancel during an ordinary persistence call poisons storage. Reproduced on main (2026-10-23
   10:16).**
   - **The test.** `tests/thesis_lite/maestro/test_stabilization_cancel.py` (FR-004) uses the owned
     2-unit runtime fixture. It cancels the run at the second ordinary `tick-complete` statement, in two
     variants:
     - `pre-send`: the cancel happens before `_rpc` sends;
     - `in-flight`: the request is sent and its reply is pending (the cancel is placed inside the
       client's `_receive`).
   - **Expected after the repair.**
     - The client is not failed (FR-005).
     - `last_writer_state` is `failed`, the manifest has `writerState: failed`, and there is no CORRUPT or
       MUTATED reason (FR-006).
     - Every issued unit is reaped and retired, and `cleanup_complete` holds (FR-007).
   - **Result on the bench venv of main `8b3d8c8e8`.** Both variants fail at the first assertion:
     `storage._failed` is True. This confirms research R-2: both the pre-send refusal and the in-flight
     `check()` refusal go through `_fail()`. The log is `t03-main-repro.log` in the run directory. The
     test is committed failing, as the reproduction. The repair follows in a later commit.
6. **Repair of finding 5 (FR-005 to FR-007), with ADR amendment S1a-1 (commit `3f032783e`, recorded before
   this implementation).**
   - **Change in `persistence.py`.**
     - A new `PersistenceCancelled` (code `ML-PERSIST-CLOSED`) is raised before send when the latch is
       cancelled and the client is not failed. It is checked ahead of `check_child`, because the
       bootstrap root's `_live` also refuses a cancelled latch, with `ML-BOOT-CLOSED`. That was the first
       repair attempt's miss: storage was still failed by the `ML-BOOT-CLOSED` path.
     - `_rpc` re-raises it without `_fail()`, and `_available` does the same.
     - A request in flight checks the child as the terminal kinds do, and may receive its reply within
       `CANCEL_REPLY_GRACE_NS` (0.5 s). After that it fails closed.
   - **Rejected intermediate design (recorded).** Letting the in-flight request run to its own deadline
     broke `test_persistence.py::test_cancel_while_flush_is_blocked_returns_without_storage_lock`, which
     requires a cancel to release the caller within 2 s even when the worker's flush hangs. That accepted
     property is the reason for the bounded grace.
   - **FR-006 refinement.** After the repair, a cancelled run goes through Maestro's normal terminal path:
     dispositions, run-terminal, collection, the terminal report and finalize. The writer ends `closed`,
     with `complete` evidence of a run that did not succeed (`terminalSucceeded: false`,
     `eligible: false`, blocker `terminal-outcome`). That is an honest closure, and stronger than the
     spec's abort expectation. The test therefore accepts `closed` or `failed`, requires the manifest
     state to match, forbids CORRUPT, MUTATED and WRITER-STATE reasons, and requires the success flags to
     be false.
   - **FR-007.** Every issued unit was reaped and retired through the normal reverse teardown, and
     `cleanup_complete` holds, so no RunClosure STOP/RETIRE change was needed for this path. The live
     cancel-paused confirmation (VS-09) checks the native-frozen live case.
   - **Verification on venv `venv-cand`** (candidate wheel, no PYTHONPATH):
     - `test_stabilization_cancel.py`: 2/2 passed, three times in a row.
     - The previously failing pair (blocked flush; `cancel-queued-recovery`) plus the new test: 13
       passed.
     - The focused group (`test_persistence`, `test_runtime_entry`, `test_active_control_deadlines`,
       `test_lazy_dispatcher`, `test_retained_inputs`, `test_terminal_runtime`, `test_outcomes`) at load
       4.6–4.8 with the intermediate design gave 111 passed, 2 failed and 1 error. The failures were the
       blocked-flush regression and a setup `ML-PERSIST-TIMEOUT` in `cancel-queued-recovery`. The latter
       passes on main and on the final repair; it is classified as load-sensitive setup, and the full
       run decides.
7. **Repair of findings 2 and 4: resumable byte-verified reads (S1-T04; FR-002, FR-003; S-D7).**
   - **Argus** (amendment S1a-2, `detailed-design.md` section 8.6). `recover_stream` is refactored into
     one scan with an optional resume state; the acceptance code is the same. `resume_stream` continues a
     *clean* scan only when the device and inode match and the SHA-256 of the whole verified prefix,
     re-read on every call, is unchanged. `read_records(root, checkpoint)` resumes only when the manifest
     bytes are unchanged; otherwise it is a complete `read_run`. Damaged evidence never yields a
     checkpoint. `read_run`, `verify`, the exports and the CLI are unchanged.
   - **Maestro** (`OutcomeJournal._mirrors`). It uses `read_records`, indexes only new records, and
     compares expected event fields again only when the expected object or the accepted record object
     changed. A complete read produces new objects, so everything is compared again.
   - **XDL** (`FileEvidenceJournal._reload`). It re-reads the whole file, re-hashes the verified prefix
     (which must end at a line boundary, with the same device and inode), and parses only new lines. A
     claim-wire reload stays complete. The sequence check is unchanged.
   - **New tests.**
     - `tests/thesis_lite/argus/test_stabilization_read_records.py`: equality with `read_run` after every
       one of 40 appends, with only one complete read; a same-size prefix rewrite; truncation; a replaced
       inode; foreign appends (non-canonical, non-JSON, duplicate); a changed manifest; another root.
     - `tests/thesis_lite/maestro/test_stabilization_journal_reload.py`: two writers on one journal, at
       most two lines parsed per reload; a changed prefix byte; a broken sequence; a replaced file.
     - Result: 13 passed.
   - **Benchmark on the candidate venv** (load 3.8–5.1; runs in `.x-verse-build/runs/lite-stabilization-s1a/`):

     | Run | Outcome | Events | Per-event p99 / max | Last − first decile | Duration |
     | --- | --- | --- | --- | --- | --- |
     | `t04-cand-4u-h300` | succeeded, evidence complete | 450 | 40.5 / 98.3 ms | +6.8 ms | 20.4 s |
     | `t04-cand-4u-h600` | executed, evidence incomplete (finding 8) | 791 | 31.6 / 79.2 ms | +2.8 ms | 36.1 s |
     | `t04-cand-5u-h600` | as above | 796 | 40.7 / 106 ms | +3.8 ms | 37.3 s |
     | `t04-cand-4u-h800` | as above | 1016 | 35.9 / 77.8 ms | +6.8 ms | 46.9 s |
     | `t04-cand-5u-h800` | as above | 1009 | 35.5 / 97.1 ms | +5.5 ms | 47.4 s |
     | `t04-cand-4u-h800-r4m` (retained cap 4 MiB) | **succeeded, evidence complete** | — | — | — | 50.5 s |
     | `t04-cand-4u-h1000` | `ML-SCHEDULE-SERVICE-DEADLINE` (finding 9) | 1218 | 39.7 / 96.9 ms | +5.1 ms | 57.7 s |

     Per-request worker handling is flat at 2.4–3.5 ms; on main it rose from 23 ms to 178 ms. FR-002 passes
     for every candidate run with 4 and 5 units: p99 ≤ 0.1 s, maximum ≤ 0.25 s, last-decile increase ≤
     0.05 s.
   - **Calls outside the per-event metric.** These are start-up and terminal calls, separated in
     `analyze.py`. `init` takes 0.5–0.68 s (0.47–0.58 s on main), inside the 4 s start-up window. Each
     `terminal-report` call takes 0.36–0.63 s, inside the ≤ 2 s terminal budget.
8. **Run length is also bounded by the 1 MiB default cap of `retained-inputs.json` (2026-10-23 10:38).**
   - **What happened.** At 600 and 800 ticks the terminal report stopped at stage `retained-inputs`, with
     blocker `publication`. The writer was aborted (`failed`, incomplete), and the dispatcher reported
     `ML-SCHEDULE-EVIDENCE-INCOMPLETE`.
   - **Cause.** The retained public inputs grow by about 1.7 KB per event (760 077 bytes at 450 events).
     When the caller does not declare the artifact, `coverage.py:203` caps it at 1 MiB, which allows about
     600 events.
   - **Within the accepted contract.** Coverage admission allows a declared `maximumBytes` up to the
     16 MiB total (`coverage.py:330-336`). With `ArtifactExpectation("retained-inputs.json", maximum_bytes=4 MiB)`,
     the 800-tick run succeeded with complete evidence (1 549 471 bytes retained).
   - **Disposition.** This is not a code defect. It is an admission parameter that long runs must declare.
     Carried to S1c FR-018: the blueprint declares a retained-inputs cap sized for its horizon. Recorded for
     Phase 8.
9. **Admission accepts a horizon that cannot fit its active window (2026-10-23 10:35, runs `h1000`).**
   - **What happened.** With 1 000 ticks and a 55 s active window, the 4-unit run ended with
     `ML-SCHEDULE-SERVICE-DEADLINE`. The 5-unit run ended with `ML-SCHEDULE-TEARDOWN-INCOMPLETE` and
     `cleanupComplete: false`: teardown began too late.
   - **Cause.** The ticks advance at about 0.05 s (the poll floor) plus the round trips, so 1 000 ticks
     need more than 55 s. `admit_schedule` checks the event and request capacity, but not that
     `ticks × poll + calls` fits the window.
   - **Pre-existing.** Unrelated to the repair.
   - **Disposition (proposed, LOW).** The blueprint chooses a horizon with margin. The measured capacity
     is at least 800 ticks with 4 units at load ≤ 5. A feasibility check in admission is a candidate for a
     later successor and is not implemented in S1a.
   - **S-D1 consequence**, recorded under the author's delegation and replacing the target in finding 1:
     the long-run uses **600 Maestro ticks** with 4 units, an active window of 55 s, and a retained-inputs
     cap of 4 MiB. That is about 0.75 of the measured 800-tick capacity, leaving margin for a slower cycle
     under load.
10. **A race test depended on slow persistence (2026-10-23 11:05, found by the nested platform regression in
    `focused-perf-1.log`).**
    - **Test.** `test_active_controller_recovery.py::test_original_active_replacement_retains_owner_writer_and_productive_access[heartbeat-race]`.
    - **Results.** It fails 3/3 on the candidate (`assert len(tickets)==1`: 0 tickets). It passes 3/3 on main,
      and 2/2 on a cancel-repair-only build (`55838b5f8`, venv `venv-cancel`), so the cause is the
      finding 7 change.
    - **Cause, from a debug trace of controller requests** (not committed). The mode enqueues the controller
      replacement when the old controller sends its first `heartbeat` after three starts. That heartbeat is
      the lease renewal of `_renew_service`, `dispatcher.py:1207-1229`, first due about 2.4 s into the run.
      - On the cancel-only build, the run lasts 11.7 s and the old controller sends 2 heartbeats.
      - On the candidate, the whole schedule (prepare, start, observe, stop and cleanup of 4 units)
        finishes in about 1.5 s, before any renewal. No heartbeat is sent, and the race is never set up.
    - **Assessment.** The behaviour is correct: no renewal is needed in a short run. The test's trigger
      depended on persistence being slow.
    - **Repair (test only, committed with this finding in `a803b4087`; review 1 R1-5).** In `heartbeat-race` mode, once three starts are complete
      and no ticket exists, each statement is followed by a bounded 0.25 s pause. The run then reaches the
      first lease renewal, and the heartbeat triggers the replacement exactly as the test intends. The
      pause stops as soon as the ticket exists. Its total is bounded by the 20 s active window that the
      test asserts. Product code is unchanged.
11. **Independent implementation review 1 on `a803b4087` (2026-10-23 about 11:40): FAIL. Recorded before any
    repair.**
    - **HIGH R1-1.** `resume_stream` can return more than `max_read_records`. A clean scan that ended
      exactly at the cap still produced a checkpoint (`recovery.py:669-681, 702-705`), so a resumed read
      accepts the next record. The reviewer reproduced it with `max_read_records=3`: the resumed read gave
      4 records, while `read_run` gave 3 plus `ARGUS2-BOUND-EXCEEDED`. Maestro probably cannot reach it,
      because `coverage.py:884` sets `max_events == max_read_records`, but the equality claim of section
      8.6 is false.
    - **MEDIUM R1-2.** `reconcile_snapshot` (`persistence.py` about 1310-1317) wraps the `recovery` RPC in
      `except Exception: self._fail()`, so a cancel before that send still fails storage (FR-005).
    - **MEDIUM R1-3.** The 0.5 s in-flight grace departs from the spec text of FR-005 ("completes within
      its own deadline"). Its expiry shares the `ML-PERSIST-CLOSED` code.
    - **MEDIUM R1-4.** The claims overstate the evidence:
      - FR-006 says `failed`, but the candidate accepts `closed`;
      - FR-007 (STOP/RETIRE for unacknowledged generations) is not implemented or tested;
      - FR-003 has no differential or tamper check at Maestro level;
      - FR-002's full re-read costs at capacity are not reported;
      - FR-008 is not addressed.
    - **LOW R1-5.** Ordering and wording:
      - the S1a-2 amendment shares its commit with the implementation;
      - the "next commit" wording of finding 10 is wrong;
      - "damaged evidence never yields a checkpoint" holds only for damage found by the stream scan.
    - **LOW R1-6.** Weak or missing tests:
      - a redundant assertion;
      - no positive check of the terminal events after a cancel;
      - no test for the grace expiry, a symlink-replaced stream, or a Maestro-level same-size tamper.
    - **LOW R1-7.** The finding-10 test pause is bounded but timing-based.
    - **Verified equivalent by the reviewer:** the restored scan state, the prefix read, manifest-only
      dependence, `EvidenceLimits` equality, the shared-record consumers, `_index` reset paths, no start
      authority after a late reply, the `_failed` consumers, `_reload` equivalence, and bench files outside
      the DV12 collection (`pytest tests`).
12. **Repairs and dispositions for review 1 (finding 11).** The thesis delegated revisions DR-1 to DR-5 were
    recorded first, in `specs/029-lite-stabilization/review/author-decisions-20261023.md` (spec rev 4b).
    - **R1-1 (repaired).** No checkpoint is created when `len(records) >= max_read_records`
      (`recovery.py`). Regression test `test_scan_stopped_at_the_record_cap_is_not_resumable`.
    - **R1-2 (repaired).** `reconcile_snapshot` re-raises `PersistenceCancelled` before its fail-closed
      handler.
    - **R1-3 (repaired, DR-1).** The grace expiry has its own code, `ML-PERSIST-CANCEL-GRACE`. Test
      `test_in_flight_reply_grace_expiry_fails_closed_with_its_own_code`: a blocked flush, then a cancel;
      the caller is released after at least 0.5 s and in less than 2 s, and storage is failed and drained.
    - **R1-4 (dispositioned).**
      - FR-006 is revised by DR-2: `closed` or `failed`. The cancel test now also asserts exactly one
        run-terminal event with outcome `cancelled`.
      - FR-007 is narrowed by DR-3: RunClosure STOP/RETIRE only if VS-09, or a cancel before
        acknowledgement, shows unattested facts.
      - FR-003 is scoped by DR-4: new Maestro-level same-size, same-inode tamper variants
        `argus-same-size` (ordinal byte in the first line) and `journal-same-size` (sequence byte in the
        first M3 record) of `test_original_durable_history_loss_blocks_new_ready`. They fail closed after
        earlier successful checks: 5/5 variants pass.
      - FR-002 full re-read costs, from the worker traces at 450–1 009 events: revalidate ≤ 20.7 ms, audit
        ≤ 37.8 ms, terminal-report handling 0.42–0.49 s (client round trip ≤ 0.63 s) against the ≤ 2 s
        terminal budget, init 0.50–0.68 s within the start-up window. The trace writes a request's line
        only when the next request arrives, so the worker's last request (closure or abort) is not in the
        trace. Its client-side round trip is in `rpc.jsonl`: closure ≤ 0.4 ms in all runs.
      - FR-008, derived for 5 units (DR-5):
        - the terminal reserve admitted by `admit_schedule` is 21.4 s for 4 units at operation 0.38 s and
          19.4 s for 5 units at 0.2 s;
        - S1a adds no teardown work: FR-007 is not implemented, and the grace stays inside the existing
          drain;
        - the measured terminal calls (≤ 0.63 s each) fit the ≤ 2 s terminal budget;
        - S1b's graceful stop must re-derive this.
    - **R1-5 (corrected).** The finding-10 wording now names the commit. Section 8.6 states precisely which
      damage prevents a checkpoint. In future, amendments get their own commit before the code: S1a-1 did,
      S1a-2 did not. That is recorded here.
    - **R1-6 (repaired).** The redundant assertion is removed. Added: the symlink-replaced stream test, the
      grace-expiry test, the Maestro-level same-size tamper variants and the positive run-terminal check.
    - **R1-7 (accepted, LOW).** The bounded 0.25 s pause keeps the test's intent without a product hook. A
      deterministic heartbeat trigger would need a test-only hook in the dispatcher and is not added.
13. **Independent implementation review 2 on `3a321a13e` (2026-10-23 about 12:00): PASS for the code and for
    the DV12 full run.**
    - **Verified by the reviewer:**
      - R1-1 by probe: 0 mismatches on HEAD over 6 limit combinations, against 31 on the old `recovery.py`.
      - R1-2 is the only `_fail()` gap of its kind.
      - R1-3 is routed through the generic failure path.
      - No closed code table needs the new code.
      - The same-size variants run after two `_revalidate` calls, so the cached-prefix path is exercised.
      - The worktree is clean, and nothing in `tools/bench` is collected.
    - **Two MEDIUM record corrections (M1, M2) and LOW wording items, corrected here.**
    - **M1: corrected figures** (`summary.json` regenerated with the current `analyze.py`, which separates
      start-up and terminal calls):

      | Run | Per-event p99 / max | Decile means | Terminal calls |
      | --- | --- | --- | --- |
      | `t01-main-4u-h300` | 315 / 370 ms | 23 → 149 ms | init 471 ms |
      | `t02-main-5u-h300` | 294 / 478 ms | — | init 579 ms |
      | `t04-cand-4u-h800-r4m` | 49.8 / 99.9 ms | +7.9 ms | **terminal-report 991 and 711 ms**, init 576 ms |
      | `t04-cand-4u-h600-b` | 38.7 / 88.6 ms | +7.6 ms | terminal-report 507 and 445 ms |

      - `t04-cand-4u-h800-r4m` (succeeded, evidence complete) is the case closest to the S-D1 long-run, and
        it passes FR-002.
      - The values in findings 2 and 4 were computed before start-up calls were separated, so their maxima
        were the `init` calls.
      - In finding 7, the middle deciles were 2.2–6.8 ms and the edge deciles 7–22 ms (start-up and
        teardown).
      - Across every candidate run, revalidate ≤ 27.0 ms and audit ≤ 39.6 ms.
      - The terminal report grows with the run: 0.36–0.51 s at 450–800 events when it stopped early at the
        retained-inputs stage, and **0.71–0.99 s for a complete 800-tick report**. Both fit the ≤ 2 s
        terminal budget, with about 1 s of margin at 800 ticks.
      - No candidate run issued a `closure` or `abort` RPC, so their re-read cost is **not measured**. The
        "closure ≤ 0.4 ms" of finding 12 came from main runs that failed before any re-read; that claim is
        withdrawn.
      - FR-008 still holds against the 2 s budget. The S-D1 long-run of 600 ticks has more margin than the
        800-tick run.
    - **M2.** `ADR-ML3-PERSISTENCE-0001` amendment S1a-1 now states the `ML-PERSIST-CANCEL-GRACE` code and
      the `reconcile_snapshot` path.
    - **LOW items:**
      - The docstrings of `StreamCheckpoint` and `read_records` state the record-cap case.
      - A run that reaches `max_read_records` falls back to a complete read on every check. Below the
        admitted capacity this does not arise; it is recorded here.
      - The benchmarks ran on `venv-cand-trace`, which is equivalent to `a803b4087`. Later changes do not
        touch the measured path: the checkpoint-cap condition is not reached below capacity, and the cancel
        paths are not exercised by the benchmark.
      - `focused-r1-repair.log` lists the test files used: `test_persistence`, `test_runtime_entry`,
        `test_active_control_deadlines`, `test_active_controller_recovery`, `test_terminal_runtime`,
        `test_outcomes`, `test_stabilization_cancel`, `test_stabilization_journal_reload`,
        `argus/test_stabilization_read_records`, `argus/test_argus2_recovery_unit` and
        `argus/test_argus2_reader_unit`. They ran on `venv-cand` built from the working tree at `3a321a13e`
        (runner `runv.sh`, `-p no:randomly`). Result: 136 passed.
      - R1-2 has no test. It is the same pattern as the other ordinary paths, which are covered.
14. **Decisive full installed-wheel run, and the DV12 gate (2026-10-23).**
    - **Run.** `evidence/affa19/stabilization-s1a/platform-regression-20261023a-1`, head `d04bc7937`,
      driven by `run-z-quiet-loop.sh` with `verify-platform-regression-20261021t.py`. It was triggered at
      10:48Z at load 5.36, on the first attempt.
    - **Result: clean.** 2417 passed, 1 skipped, 24 subtests, 0 failed, in 2590 s. It collected 2418
      tests (2397 for Phase 6, plus the S1a tests). The loop reported `decisive: clean`.
    - **Load.** Sampled every 30 s, maximum 7.94, ≤ 10.
    - **The race test.** It passed in the nested platform regression and in the direct run (finding 10).
    - **DV12 gate.** `scripts/validate_maestro_acceptance_evidence.py --candidate d04bc7937… --g4
      acceptance-inputs/g4.json --allowlist acceptance-inputs/allowlist.json --scope code`:
      `accepted_as_evidence: true`, no blockers. The run code SHA-256 equals the candidate code SHA-256,
      `2a3374670ddd17e7…`.
    - **Evidence.** `dv12-gate-verdict.json` and `SHA256SUMS` (13 files) in the run directory, receipts
      in `receipts.tar.gz`. The loop removed its tmpfs work directory.
    - **Next.** CAPA successor step 9 (`build-capa-20261023-stabilization-s1a-step9.py`) is built after
      this log is committed.
15. **The CAPA register verifier cannot verify step 8 or step 9 on the merged main history. A pre-existing
    tooling defect (2026-10-23 12:40). Recorded before the successor.**
    - **What happened.** CAPA step 9 (`capa-20261023-stabilization-s1a-step9`, register `34c742da…`, 56
      records and 681 bindings) passes parent preservation: 665 parent bindings, none changed or lost.
      `affa17/verify-capa-register-20261020.py` then fails with `AssertionError: E-FAULTS-REVIEW-LOG`.
      Re-running that verifier on step 8 (`49f25e74…`) in this worktree fails the same way, so the defect
      predates S1a.
    - **Cause, verified.** The binding is to `review-faults-lite.md`, with bound SHA-256 `6558cc6f…`
      (CAPA step 7). Flows-lite finding 13 placed that blob into history through a restore/re-restore commit
      pair on the flows branch, whose net change to the path is zero. After the `--no-ff` merge into main,
      default history simplification of `git rev-list HEAD -- <path>` (`verify-capa-register-20261020.py:36`)
      drops that side branch:
      - with the default, 5 commits are listed and none carries the blob;
      - with `--full-history`, 8 commits are listed and one carries it.
    - **Disposition.** The frozen `affa17` verifier is not edited. A successor,
      `affa19/verify-capa-register-20261023.py`, differs only by `--full-history` in the committed-blob
      search; its docstring records why. Step 8 and step 9 are verified with it. The original verifier's
      result is recorded as above.
16. **CAPA successor step 9, built after finding 14 was committed.**
    - **Location.** `evidence/affa19/capa-20261023-stabilization-s1a-step9/`, built by
      `build-capa-20261023-stabilization-s1a-step9.py` over `platform-regression-20261023a-1`.
    - **Additive over step 8 (`49f25e74…`).** No record was opened, changed or closed. Every S1a defect
      was a defect of this unaccepted candidate, or a pre-existing limit recorded as a finding (findings
      1–15), repaired or dispositioned before acceptance.
    - **Register `34c742da8952960150018f02a4bed8083d3dca0306eef41ac4531a40f767dcf3`:** 56 records and 681
      bindings. The 16 new bindings cover:
      - the review log, as committed in `8a3272633`;
      - the two ADRs and the Argus design;
      - the run's `SHA256SUMS` and DV12 verdict;
      - five test modules and the bench tooling.
    - **Successor verifier** `verify-capa-register-20261023.py` (finding 15): rc 0, 56 records and 681
      bindings verified (`verification-recheck.json`). With the same verifier, step 8 also verifies (rc
      0, 665 bindings; `step8-verification-with-successor.json`).
    - **Parent preservation** (`affa17/check-capa-parent-preservation-20261019.py`): `parent_preserved:
      true`; 665 parent bindings checked, none changed or lost; policy and schema unchanged
      (`parent-preservation.json`).
    - No cause is verified and no effectiveness is claimed.
    - **Worktree.** The sparse checkout was disabled to run the `affa17` tooling, which leaves the
      worktree without exclusions.
17. **Author acceptance (2026-10-23 about 16:15 WEST).** The author wrote "i accept" in reply to the S1a
    and S1c-1 acceptance request. This is gate ES-2 of the thesis S1 plan
    (`specs/029-lite-stabilization`): S1a is accepted as presented in
    `review/acceptance-package-s1a-20261023.md`, including the delegated revisions DR-1 to DR-5.
    - **Accepted content.** The code is this candidate at `d04bc7937`; the commits after it add evidence and
      this log only. The evidence is the clean run `platform-regression-20261023a-1` (2417 passed, 1 skipped),
      the DV12 verdict and CAPA step 9 `34c742da…` (finding 16).
    - **Merge.** `--no-ff` into main from base `8b3d8c8e8`, which equals main, so the merged tree equals this
      candidate's tree. The tree identity is checked before the push.
    - **Carried, not repaired.** The S1b scope (graceful stop, stderr capture, the challenge-marker probe), the
      64 KiB persistence configuration bound that limits a run to 5 units, admission not checking horizon
      feasibility, and the VS-09 live cancel confirmation (S1-T06a), which runs on the merged revision.
    - **Unchanged.** Not M1, not AEB evidence, not a scientific result. Lane activation, M1 admission and
      factory runs stay closed.
18. **Post-merge live finding: an intermittent persistence child exit right after a cancel (2026-10-23 17:22;
    S1a successor; recorded before any analysis or repair).**
    - **Context.** These are the S1 VS-09 development runs on main `b28a2aacf`, with the blueprint S1c-2a
      candidate (`xverse-blueprints` `f19ae58`). The runs are on loop10 under
      `.x-verse-build/runs/lite-stabilization-s1/vs09-20261023/`, and the compat log has them as findings
      15–20. The non-M1 owned harness (`_OriginalRuntimeRun`) calls `entry.stop` about 6 s into a
      simulation pause.
    - **Observed: 1 of 7 cancel runs** (`dev-s1c2a-20261023T172145-cancel-paused`, load 7.3).
      - `entry.stop` returned at 13.7132 s.
      - A `schedule` request (sequence 452) started at 13.7136 s, which is 0.4 ms later. It failed in stage
        `receive` at 13.7162 s with `ML-PERSIST-CHILD`: the worker child had exited. Its deadline was 15.71 s.
      - The outcome is `ML-SCHEDULE-CANCELLED`, with `cleanupComplete` false and closure
        `ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN`.
      - The closure writer is `rpc-unresolved`, with `abort_attempted` false. `dispatchTerminal` is null, and
        the native units have no retired or reaped facts.
      - The Argus root keeps its initial open manifest (0 events), while the stream has 269 lines.
      - The host was left clean: no residue processes or sockets, and the restore guard succeeded.
    - **The other 6 cancel runs closed as DR-2 requires**: `170215`, `164544`, and `172613`, `172841`,
      `173109` and `173336`.
      - The writer ended `failed` by abort, and `xverse-argus verify` gives only WRITER-STATE.
      - The 4 native units are retired and reaped.
    - **What is known.**
      - The request passed the client's `_live` check after the latch was cancelled. So its kind allows a
        cancel (`schedule` with a failure, disposition or run-terminal body).
      - It was then refused because the child had exited (`allow_exit` is false for `schedule`).
      - The worker's own exit reason is not recorded. Unit and worker stderr are not captured; that is GA-30,
        the S1b FR-010 stderr capture.
    - **Not known.**
      - Whether the worker exited on its own: for example, on a request it refuses after the bootstrap
        root's cancel.
      - Whether another path signalled it: `_fail()` on a concurrent request, or the native cancel.
      - Whether the rate depends on load.
    - **Effect.** GA-11 is not closed. VS-09 and the S1d P3 criterion will fail intermittently until this is
      understood. The S1a acceptance evidence is unaffected: that suite has no live cancel race at this timing.
    - **Plan.**
      - Diagnose before any repair: reproduce on the owned harness with the worker's stderr captured, which
        is an S1b prerequisite. Alternatively, use a bench reproduction that sends disposition statements
        immediately after `entry.stop`.
      - Record the cause as the next finding, then write the ADR amendment, then the repair. This branch
        (`candidate/lite-stabilization-s1a2-20261023`) holds the record only, until the author decides how it
        is sequenced with S1b.
19. **Code analysis of finding 18 by independent review 7 of S1c-2a (2026-10-23 about 18:00). The mechanism is a
    hypothesis, not proven; corrections to finding 18 are included.**
    - **Shown by the code.**
      - After a cancel, a `schedule` request passes the client check only for the body kinds `failure`,
        `step-disposition`, `unit-disposition` and `run-terminal` (`persistence.py` `_rpc`). Its `allow_exit`
        is false.
      - At stage `receive`, `ML-PERSIST-CHILD` comes only from `_live`: the child exited, or its pidfd or socket
        identity changed.
      - `_failed` was false before the send, and `_rpc` holds a non-blocking lock. So no concurrent `_rpc` and
        no client `_fail()` preceded this request.
      - The `stop` path (`runtime_entry.stop` → the dispatcher driver's `cancel` → `owner.cancel`) does not call
        the persistence client.
      - The first post-cancel statement is `failure`, and its exception is swallowed.
      - **A kill chain exists.**
        - `RunBroker.cancel` turns a `ValueError` from the K.CANCEL exchange into `connection.revoke()`
          (`run_broker.py` about 905–911).
        - That includes `ML-AFFA-CONFLICT`, raised when another thread holds the authority connection's
          non-blocking lock (`affa_client.py` about 340).
        - `revoke` SIGKILLs the authority (about 425–441).
        - Before its terminal fence, the bootstrap root reacts to the authority's death by calling `cleanup()`.
          That kills every child, including the persistence worker (`native/bootstrap.c` about 287 and 316).
      - Health probes use that same lock: `check_health` → `RunUnitIssuer.observe` → `_native(K.QUERY)` →
        `connection._exchange`.
    - **Consistent with the hypothesis.**
      - Only `172145`'s cancel (13.708 s) fell inside a health scan: lite-driver's health was at 13.686 s, and
        the carla-adapter record never reached the journal.
      - The 6 good runs cancelled 1.2–1.6 s after a completed scan.
      - `stop` took 4.81 ms here, against 2.7–3.4 ms elsewhere.
    - **Not established.**
      - That the lock was actually held at that instant.
      - A worker self-exit is not excluded: the root also kills everything if the worker dies first.
    - **Corrections to finding 18.**
      - The rate is 1 of 5 on blueprint `f19ae58`, and 1 of 7 pooled over 3 blueprint revisions and 2 observe
        paths.
      - For `164544` and `170215` only the manifests' recorded reasons exist (WRITER-STATE only), not
        `verify` output.
      - "Host left clean" covers the 4 unit command lines only.
      - "The S1a acceptance evidence is unaffected" is withdrawn as unsupported.
      - Finding 18 was written at about 17:35, with runs up to 17:33, not at 17:22.
    - **Discriminating diagnosis (proposed; no repair before it).**
      - A bench or unit reproduction that calls `entry.stop` while the authority connection lock is held by a
        health QUERY.
      - Record `RunBroker._cancel_result`, confirmed or revoked, in the owned harness's `maestro-run.json`.
      - Then the ADR amendment and the repair, for example a cancel that waits a bounded time for the lock
        instead of revoking.
20. **VS-09 attempt 2 on the merged mains reproduces the cancel race (run 18:46; written at 18:48:08 2026-10-23).**
    - **Revisions.** Platform main `b28a2aacf`, compat main `bb07492` and blueprints main `6ac7703`, from clean
      detached worktrees. CARLA instance 14, load 5.1.
    - **Run.** `runs/lite-stabilization-s1/vs09-merged-20261023/lite-…-cancel-paused`. The S1c-2a harness failed
      visibly (exit 1).
      - `ML-SCHEDULE-CANCELLED`, but `persistenceFailure` is `ML-PERSIST-CHILD` (kind `schedule`, stage
        `receive`).
      - `cleanupComplete` false. The native units are not attested.
      - The Maestro root is `open`, with CORRUPT, MUTATED and WRITER-STATE.
      - The guard destroyed the 3 owned actors, and there is no unit residue.
      - nominal passed on the same revisions.
    - **Timing.**
      - `entry.stop` took 5.36 ms. Clean cancel runs took 2.7–3.4 ms; `172145` took 4.81 ms.
      - The failing request started 0.93 ms *before* `stop` returned, and failed 6.86 ms after it started.
      - The cancel came at 13.730 s. The last recorded health events were a complete scan at 12.804–12.855 s; at
        about 1.6 s spacing the next scan was due at about 14.4 s. No health event follows the cancel.
    - **Effect on the finding-19 hypothesis.** The cancel did not visibly fall inside a health scan. The
      health-QUERY form of the hypothesis is weakened. The general form remains open: `RunBroker.cancel` meets a
      busy authority connection (`ML-AFFA-CONFLICT`), revokes it, and the root then kills the worker. A lease
      renewal, a tick or a scheduled-step exchange could hold that lock, as well as a health QUERY.
      - The slow `stop` in both failing runs is consistent with the extra revoke-and-reap work.
    - **Rate.** 2 of 10 post-S1a cancel runs with the cancel path exercised (blueprint heads `f19ae58`,
      `588f84a`, `8aa57ca` and `6ac7703`).
    - **S1a-2 diagnosis (author-sequenced before S1b).**
      - **(1)** Instrument the owned harness to record `RunBroker._cancel_result`, confirmed or revoked, and the
        identity of the lock holder at cancel time. This is evidence only, with no behaviour change.
      - **(2)** Build a deterministic bench or unit reproduction: `entry.stop` while the authority connection
        lock is held by each candidate operation.
      - **(3)** Only then the ADR amendment and the repair.
21. **S1a-2 diagnosis: the mechanism is reproduced deterministically (written at 18:50:49 2026-10-23; before any repair).**
    - **Test.** `tests/thesis_lite/maestro/test_stabilization_cancel_conflict.py`, on the real `broker_stack`
      composition: storage, the native AFFA authority and the run bootstrap. It ran with the installed candidate
      wheel (`.x-verse-build/cache/lite-stabilization-s1a/venv-cand`, whose code equals main `b28a2aacf`), at
      load 4.1, in 5.6 s.
    - **Idle connection.** `RunBroker.cancel` gives
      `RunCancellation(native_epoch_confirmed=True, epoch=1, frozen_units=3, issuer_dead=False, …)`, and the
      storage worker stays alive. PASS.
    - **Busy connection.** The test holds `connection._lock` in place of a concurrent dispatcher exchange.
      `RunBroker.cancel` gives `RunCancellation(native_epoch_confirmed=False, epoch=None, frozen_units=0,
      issuer_dead=True, issuer_reaped=True, …)`, and the storage worker exits within 2 s. FAIL, as expected.
    - **Cause, now established.**
      1. `connection._exchange` refuses with `ML-AFFA-CONFLICT` when its non-blocking lock is held.
      2. `RunBroker.cancel` treats that `ValueError` as an unconfirmable cancel and calls `revoke()`, which
         SIGKILLs the authority.
      3. The bootstrap root then kills every child, including the persistence worker. The run's closure then
         fails with `ML-PERSIST-CHILD` (findings 18 and 20).
    - **In the live harness.** The operator's `entry.stop` runs on its own thread, while the dispatcher thread
      exchanges on the same connection for health queries, renewals and step effects. The race window is the
      fraction of time the dispatcher holds that lock, about 2 in 10 cancel runs.
    - **Not a defect of the revoke itself.** Revoking an authority that cannot confirm a cancel is the designed
      fail-safe. The defect is that a merely *busy* connection is treated as unconfirmable.
    - **Next.** An ADR amendment (S1a-3) before the repair: a bounded wait for the exchange lock on K.CANCEL only,
      falling back to the unchanged revoke when the bound expires.
22. **S1a-2 repair implemented per amendment S1a-3 (written at 18:54:23 2026-10-23).**
    - **Code.** `run_broker.py`:
      - `RunBroker._cancel_exchange(end)` retries a K.CANCEL refused with `ML-AFFA-CONFLICT`, which happens
        before any send. It polls every `CANCEL_LOCK_POLL_SECONDS` = 1 ms, until `CANCEL_LOCK_WAIT_SECONDS` =
        0.5 s or the cancel's end.
      - Each attempt builds its frame with the then-current sequence.
      - Any other error, or the expiry of the bound, reaches the unchanged revoke. `connection._exchange` is
        unchanged.
    - **Tests.** `test_stabilization_cancel_conflict.py`:

      | Case | Result | Outcome |
      | --- | --- | --- |
      | idle | 0.4 ms | confirmed |
      | lock held 0.1 s | 0.101 s | confirmed epoch 1, 3 frozen units, storage worker alive |
      | lock held 0.9 s | 0.501 s | unchanged revoke: `issuer_dead` |

    - **Against the unrepaired main wheel** (`venv-cand`), the 0.1 s case fails: it is revoked at once
      (0.0005 s). The past-bound case fails only in its timing assertion.
    - **Wider run** with the S1a-2 wheel (`.x-verse-build/cache/lite-stabilization-s1a2/venv-s1a2`, wheel
      `6b4f63a7…`; load 3.8): `test_stabilization_cancel_conflict.py`, `test_run_broker.py`,
      `test_stabilization_cancel.py` and `test_affa_client.py` gave 38 passed in 32 s.
    - **Next.**
      1. An independent review.
      2. The full installed-wheel run, the DV12 gate and CAPA step 10, committing the log before the CAPA build.
      3. The acceptance package.
      4. VS-09 on the merged revision.
23. **Independent review of S1a-2 at `20dc3dcde` (written at 19:06:24 2026-10-23): FAIL, narrow, with no safety
    violation (every traced path still ends in the unchanged revoke). Recorded before any repair.**
    - **MEDIUM-1.** The K.CANCEL frame is built before `_exchange` takes the lock (`run_broker.py`
      `_cancel_exchange`). ADR S1a-3's Decision says "after".
      - With two concurrent `RunBroker.cancel` calls — the operator's stop, and the dispatcher's own
        `owner.cancel("dispatcher-failed")`, which every live cancel takes — the winner's CANCELLED reply raises
        `connection.epoch` just before it releases the lock.
      - The loser's frame is then stale, and `_validate` raises `ML-AFFA-REQUEST-SCOPE` before any send. That
        is not retried, so it reaches revoke and the same kill chain.
      - The window is a few µs under the GIL, but it is on the live path. Finding 20's timing — the dispatcher's
        request began 0.93 ms before `stop` returned — fits it.
    - **MEDIUM-2.**
      - No test exercises two concurrent cancels on `broker_stack`, a stale frame, or a second K.CANCEL after
        CANCELLED.
      - The lock-holding tests never change the sequence or epoch.
      - Finding 20's step (1), recording the live lock holder, was not done.
    - **LOW-3.** A cancel with a caller deadline (`teardown._emergency`) can wait until that deadline. Revoke is
      then left with no time to reap: `issuer_reaped` is false, and `ML-TEARDOWN-ISSUER-UNFENCED` follows.
      SIGKILL is still sent.
    - **LOW-4.** The ADR:
      - (a) The superseded Decision bullets are not withdrawn.
      - (b) The Cost omits that `owner.cancel`'s gate and launcher cancels, and `runtime_entry.stop`'s
        `_stop_lock` hold, are delayed by up to 0.5 s; a concurrent stop then gets `ML-RUNTIME-ENTRY-CONFLICT`.
      - (c) The `_fence` rationale ignores the operator thread. That is pre-existing; `_fence` has its own
        CANCELLED shortcut.
    - **Confirmed.**
      - `ML-AFFA-CONFLICT` is raised only before any send, with no state change.
      - The double-revoke paths are safe.
      - A repeated K.CANCEL is idempotent natively.
      - No deadlock is possible, and the worst-case cancel time is unchanged.
      - The ADR commits preceded the code.
      - 127 tests passed across 4 runs at load 3.3–4.4.
    - **Repair plan.** An ADR note comes first. Then `_cancel_exchange`:
      - returns the retained CANCELLED reply when the connection is already cancelled, as `_fence` does;
      - retries a pre-send `ML-AFFA-REQUEST-SCOPE` when the frame's sequence or epoch has gone stale;
      - keeps a 0.25 s reap reserve before a caller's limit.

      The tests add:
      - a deterministic stale-frame case: another cancel wins between the frame build and the lock;
      - a real two-thread concurrent cancel;
      - a second cancel after CANCELLED.

      Recording the live lock holder is carried to the harness, as a `RunBroker._cancel_result` record in
      S1c-2. Then a fresh wheel and a re-review.
24. **Finding-23 repairs (written at 19:08:45 2026-10-23), per the ADR revision committed first (`cac6e6135`).**
    - **Code.** `RunBroker._cancel_exchange(end, limit)`:
      - returns the retained CANCELLED reply when the connection's epoch history already ends in CANCELLED;
      - retries a pre-send `ML-AFFA-REQUEST-SCOPE` when the frame's sequence or epoch is stale;
      - ends its wait `CANCEL_REAP_RESERVE_SECONDS` = 0.25 s before a caller's deadline.
    - **New tests.**

      | Test | Result |
      | --- | --- |
      | stale frame (a winner cancels between the build and the lock) | the refusal is `ML-AFFA-REQUEST-SCOPE`, then a confirmed epoch 1 with 3 frozen units and storage alive |
      | two concurrent cancels through a barrier | both confirmed, storage alive |
      | cancel after CANCELLED | the retained reply, with no further exchange |

    - **Run.** Wheel `b253356a…`, installed sources equal to the worktree, load 3.7. The conflict tests (6),
      `test_run_broker`, `test_affa_client`, `test_stabilization_cancel`, `test_composed_issuer_loss`,
      `test_runtime_pending_stop`, `test_shared_closure`, `test_runtime_entry` and `test_run_teardown` gave
      77 passed in 82 s.
    - **Carried.** Recording the live lock holder and `RunBroker._cancel_result` in the live harness is S1c-2
      scope.
25. **Independent re-review of S1a-2 at `fb364bfac` (written at 19:17:25 2026-10-23): PASS, with 1 LOW.**
    - **Confirmed.**
      - The CANCELLED shortcut cannot return a reply from an earlier epoch or another run. Only CANCELLED and
        ADVANCED replies, checked by `_match`, enter the history, and nothing follows a CANCELLED. A new
        RunBroker refuses a closed connection.
      - The stale-frame retry is bounded, and never retries a refusal caused by the deadline.
      - The reserve probe: with a 0.4 s deadline the wait ended at 0.151 s, and the revoke reaped.
      - The fail-safe is preserved. There is no deadlock or livelock.
      - The ADR text matches the code, and the commit order is correct.
    - **Runs.** `test_stabilization_cancel_conflict.py` ran three times, 6 passed each time. The related test
      files gave 35, 36 and 42 passed, at load 3.0–4.7.
    - **The two discriminating tests.** These fail on the pre-repair `_cancel_exchange` (probe):
      - the stale-frame test;
      - the after-CANCELLED test.
    - **LOW-1.** `test_two_concurrent_cancels_are_both_confirmed` passes on the pre-repair code too. In 1 of 4
      traced runs it did not overlap. It is therefore a smoke test of the conflict wait, not a test of the
      stale-frame interleaving.
    - **Disposition.** The test's docstring and finding 24 now describe it as a smoke test. This changes the
      docstring only. The change is made before the full run, so the full run covers it.
26. **S1a-2: the decisive full installed-wheel run and the DV12 gate (written at 20:16:35 2026-10-23).**
    - **Run.** `evidence/affa19/stabilization-s1a2/platform-regression-20261023b-1`, head `d8b44719c`, driven by
      `run-z-quiet-loop.sh`.
      - Triggered at 18:21:30Z at load 3.52, on the first attempt.
      - **Clean:** 2423 passed, 1 skipped (`test_runtime_lane_admission`: `MAESTRO_LANE_PROPOSAL` is not set; as in
        S1a), 24 subtests, in 2511 s.
      - The maximum sampled load was 8.07.
    - **DV12 gate.** `scripts/validate_maestro_acceptance_evidence.py --scope code`: `accepted_as_evidence: true`,
      with no blockers. The run and candidate code are both `33b2d1fd…`; the evidence and the review logs are
      excluded from the comparison.
      - The verdict is `dv12-gate-verdict.json`, and `SHA256SUMS` covers the run directory.
    - **Next.** CAPA step 10 (parent step 9, `34c742da…`) is built after this log is committed.
27. **CAPA successor step 10 for S1a-2 (written at 20:17:26 2026-10-23), built after finding 26 was committed.**
    - **Location.** `evidence/affa19/capa-20261023-stabilization-s1a2-step10/`, built by
      `build-capa-20261023-stabilization-s1a2-step10.py` over `platform-regression-20261023b-1`.
    - **Additive over step 9 (`34c742da…`).** No record was opened, changed or closed.
    - **Register `4b04cb4aee387323fc123395e7ecf58e491f7384b4fbebce8ed668ab747569d0`:** 56 records and 687 bindings.
      The 6 new bindings cover:
      - this review log, as committed in `3d66178c4`;
      - the ADR-ML3-AFFA-0001 S1a-3 amendment;
      - `run_broker.py`;
      - `test_stabilization_cancel_conflict.py`;
      - the run's `SHA256SUMS` and its DV12 verdict.
    - **Successor verifier** `verify-capa-register-20261023.py`: rc 0, with 56 records and 687 bindings verified
      (`verification-recheck.json`).
    - **Parent preservation** (`affa17/check-capa-parent-preservation-20261019.py`): `parent_preserved: true`. All
      681 parent bindings were checked, none changed or lost, and the policy and schema are unchanged
      (`parent-preservation.json`).
    - No cause is verified beyond the deterministic reproduction, and no effectiveness is claimed.
    - **S1a-2 is ready for the author's acceptance.** VS-09 follows on the merged revision.
28. **S1a-3 (thesis S-D9, path (a) of FR-002): the long-run terminal report is dominated by the retained-inputs encoder
    (written at 22:08:50 2026-10-23; before any repair).**
    - **Branch.** `candidate/lite-stabilization-s1a3-20261023`, stacked on the S1b candidate `0929bd2d5`, because
      both touch the evidence path.
    - **Trigger.** S1c finding 32: a live long-run (600 ticks, 4 units, load 8.4) hit the 2 s `terminal-report`
      deadline (`ML-PERSIST-TIMEOUT`). It took 0.80 s at load 6.3.
    - **Profile.** The bench is `tools/bench/persistence_scaling` at 600 ticks with 4 units and a 4 MiB retained cap,
      on the S1b wheel at load 3.7, with a bench-only, measurement-only timer hook in a separate venv
      (`.x-verse-build/cache/lite-stabilization-s1b/venv-prof`). Run
      `runs/lite-stabilization-s1/s1a3-profile-20261023/h600-e`:
      - `WorkerTerminal.publish`: 1303 ms (`terminal-report` client round trip 1313 ms).
      - `retained_snapshot`: 1090 ms.
      - `WorkerTerminal.checkpoint`: **166,561 calls**, about 386 ms including the timer overhead.
      - `assess_preclosure`: 165 ms.
      - `_json` (11 calls): 36 ms.
      - `close`: 470 ms, a separate call.
    - **A cProfile attempt** (`h600-c`) pushed the call to its 1.988 s deadline and was killed. That is a measurement
      artefact, recorded and not used.
    - **Cause.** `evidence._bounded` streams the retained-inputs document (about 1.3 MB, about 800 annotations) with
      `JSONEncoder.iterencode`. That is CPython's pure-Python encoder, which yields very small chunks, and it calls
      the terminal checkpoint (the worker liveness check plus the deadline) once per chunk. The per-event
      validation loop in `retained_snapshot` adds one checkpoint per event.
    - **Repair plan (ADR-ML3-EVIDENCE-0001 amendment S1a-4, before the code).**
      - Encode the top-level object field by field, and list values element by element, with the same encoder
        settings. The C encoder is used per element. The size cap is checked after every element; the checkpoint
        runs once per element and at least every 64 KiB.
      - The output must be **byte-identical** to today's `_bounded` for every input. A differential test runs over
        generated and recorded bodies.
      - Memory stays bounded by one element plus the cap. The 8192-event and cap checks are unchanged.
      - No incremental cache is introduced unless the re-measurement shows it is still needed.
29. **The S1a-3 repair, per amendment S1a-4 (written at 22:14:53 2026-10-23).**
    - **Code.** `evidence._bounded` now emits a top-level object key by key, sorted, and a list value element by
      element, each through the same `JSONEncoder` (the C path). The size cap is checked after every element and
      the checkpoint runs once per element. Any other shape keeps the original chunked encoding.
    - **Differential test** `tests/thesis_lite/maestro/test_stabilization_bounded_encoding.py`: 362 passed. It covers:
      - byte identity against a verbatim copy of the old implementation, over 300 generated bodies and values
        (unicode, escapes, `-0.0`, `1e-310`, large integers, nesting);
      - identical refusal at every cap (60 bodies, four caps each);
      - NaN and infinity refused as before;
      - the checkpoint running per element, under a tenth of the previous count, and still able to stop the
        encoding.
    - **Re-measurement** on the same bench (600 ticks, 4 units, 4 MiB cap), at load 3.3–3.5:

      | Measure | Before | After (runs `fixed-h600-a/b/c`) |
      | --- | --- | --- |
      | `retained_snapshot` | 1090 ms | 46–50 ms |
      | `publish` | 1303 ms | 269–289 ms |
      | checkpoint calls | 166,561 | 1810 |

      - `close` takes 491–530 ms: `verify_runtime_closed` (the independent re-read of the closed evidence) 393 ms
        and `argus.finalize` 90 ms. That is unchanged by design.
      - Both terminal calls are now about 0.27 s and 0.5 s against their 2 s budget at low load.
      - The live terminal cost was 1.5–2.5 times the bench cost under load 6–8.4, so the expected live figures are
        at most about 0.7 s and 1.3 s.
      - The run succeeded, with cleanup complete.
30. **Independent review of S1a-3 (`2497b5a4d`; written at 22:22:19 2026-10-23): PASS, LOW only.**
    - **Confirmed.**
      - The reviewer's 48-case standalone probe on the venv's Python 3.13.13, with the C encoder active, gave
        identical bytes or the identical exception type. It covered:
        - tuples, `OrderedDict`, dict and list subclasses;
        - int, float and str subclasses, and `IntEnum`;
        - big ints and the 4300-digit limit;
        - `-0.0`, `5e-324` and other awkward floats;
        - nested and top-level non-str keys (the fallback path);
        - surrogates, NaN, cycles and shared references.
      - A cap sweep over 300 bodies gave 0 mismatches. Memory is about one element plus the cap.
      - A 64 KiB element encodes in about 2 ms.
      - The figures in finding 29 are consistent with finding 28.
      - The commit order is correct.
      - 362 differential cases passed.
    - **LOW findings, dispositioned.** The full run had already started on `2497b5a4d`, so no code or test is changed
      after it.
      - **(1)** An element that both crosses the cap and fails to encode raises `ValueError` instead of
        `ML-EVIDENCE-EXPORT-SIZE`. Callers cannot reach this: every element was already serialized with
        `allow_nan=False`. Accepted.
      - **(2)** Nesting deeper than about 1200 levels now encodes where the original raised `RecursionError`. The
        writer bounds nesting at 128. Accepted.
      - **(3) Wording correction to amendment S1a-4 and finding 28.** The 64 KiB element bound holds for retained
        claims (`retained_intent`). Internal events and `publicM3` records are small by construction, and only the
        writer's `max_event_bytes` bounds them. Even a 1 MiB element encodes in tens of ms.
      - **(4)** The differential test does not generate tuples, subclasses or top-level non-str keys. A mutant that
        dropped the non-str-key fallback would pass it.
        - The disposition rests on the reviewer's probe, which covers those cases and is kept as evidence in the
          thesis scratch record.
        - The test generator is to be widened with the next code change in this area.
        - This is recorded for the author.
31. **S1a-3: the decisive full installed-wheel run and the DV12 gate (written at 23:03:56 2026-10-23).**
    - **Run.** `evidence/affa19/stabilization-s1a3/platform-regression-20261023d-1`, head `2497b5a4d`.
      - Triggered at 21:21:34Z at load 3.22, on the first attempt.
      - **Clean:** 2886 passed (including the 362 differential cases), 1 skipped (lane admission), 39 subtests, in
        2438 s.
      - The maximum sampled load was 5.11.
    - **DV12 gate** (`--scope code`, candidate `5e81c7b05`): `accepted_as_evidence: true`, with no blockers. The run
      and candidate code are both `868a21b6…`; the review-log commit after the run is outside the code scope.
