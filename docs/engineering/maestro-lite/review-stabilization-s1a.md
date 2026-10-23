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
