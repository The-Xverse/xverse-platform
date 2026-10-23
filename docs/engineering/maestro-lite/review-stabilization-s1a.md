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
    - **Repair (test only, in the next commit).** In `heartbeat-race` mode, once three starts are complete
      and no ticket exists, each statement is followed by a bounded 0.25 s pause. The run then reaches the
      first lease renewal, and the heartbeat triggers the replacement exactly as the test intends. The
      pause stops as soon as the ticket exists. Its total is bounded by the 20 s active window that the
      test asserts. Product code is unchanged.
