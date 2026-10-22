# Increment 19: decisions requested from the author (2026-10-21)

Candidate branch `candidate/maestro-lite-affa19-20261021`, based on main `557619e0c`; review log
`review-affa19.md`, findings 414–467. Nothing below is decided or
applied. Each item names its evidence and states what remains open, so that a "yes" or "no" is
traceable.

## A. Product fix candidates

| # | Decision | Evidence | Open risk |
| --- | --- | --- | --- |
| A1 | Accept **F-10** (`17da15b50`, `9f31771dd`, `e9b346a05`): a lost observation (`health-loss`/`unknown`) is a valid recorded failure. The assessor accepts the exact pair with `dependencies []`, and both sides take `handleRef` from the issuance of the current generation. | Findings 439–449, 463–466. Two independent reviews (FAIL, then PASS). 35-module regression 362 passed. DV09 tests: strict, (a)/(b) with offline verification, three mutation limits rejected. Run u clean; run v's one failure is the load-dependent nested suite of 467, none in F-10 tests. | Legacy CatalogLauncher path unchanged (448 item 4). F-11 and F-12 are pre-existing and only recorded. |
| A2 | Accept **F-08/F-09 v2** (`f4262c285`): refuse a send whose remaining time is below the longest round trip already observed for its kind. | Findings 438, 447, 452–455, 463–467. Review PASS. Quiet host: A/B b had no persist timeout in arm B (arm A 3 of 10); A/B c put all 8 refusals at the T3 active end; strict T3 discriminates (3/6 fail without the guard, 6/6 pass with it). **Natural load (467):** run v's nested suite failed 12 tests while another project loaded the host; the rerun under load failed 7: 3 v2 refusals outside T3 (7.9, 53 and 103 ms left against 136, 123 and 116 ms) and 4 persist timeouts v2 did not prevent; on the quiet host all 12 passed. | **High, now partly measured:** v2 narrows F-08/F-09 but does not remove them under rising load, and whether the 3 refused sends would have completed is unmeasured (the loaded A/B d stopped at pair 0 when the external load ended). Options: accept as a partial mitigation and keep F-08/F-09 open; ask for a revision (e.g. an estimate that tracks load within the run); or withdraw. |

## B. Acceptance-gate inputs (DV12 gate, findings 456–457, 463)

| # | Decision | Context |
| --- | --- | --- |
| B1 | Allowlist the lane-admission skip (`test_runtime_lane_admission.py:55`, runs under its own driver). | Blocks runs u and v at B3 until allowlisted with a reason and an approval reference. |
| B2 | Allowlist the D-09 xfail until D-09 is ruled. | Same. |
| B3 | Record the G4 disposition (waived or satisfied) and its scope. | Required by B5. The current record is "waived for FR-001–FR-012 draft preparation" (author-decisions.md), and its scope for acceptance is not stated. |
| B4 | Choose the authoritative staleness scope: whole tree, or code paths only (`src`, `tests`, `scripts`, `xdl`, `pyproject.toml`). | The code scope lets documentation-only commits after a run keep that run valid. |

## C. Design rulings (T01, step 5)

| # | Item | Summary |
| --- | --- | --- |
| C1 | **D-09** (finding 444) | After a failed execution the writer is aborted, so offline overall status never reaches complete. The design branch `normal-documented-failure` expects complete. Either finalize factually complete failed runs, or amend the branch. |
| C2 | **CP-10**, **W-01** | DIVERGENT expected-table rows (findings 420, 421): authority-crash marker count, and writer closure under a persistent fsync fault. |
| C3 | **CP-02**, **AF17** | Borderline expected-table rows. |
| C4 | Non-constructible and deferred items (findings 431, 432, 437, 450) | DV03 n2–n4 sealed at admission; DV04 n0 has no application probe; DV05 n4 has an in-process C1 stall; DV06 n5 has no SIGTERM to workloads; DV06 n8 is settled statically; DV03 p1 durable bootstrap-approval consumption is deferred to the U2 gate (ADR-ML3-BOOTSTRAP-0001 line 68). Accept as stated limits, or require design changes. |

## D. Task boxes and records

| # | Decision | Context |
| --- | --- | --- |
| D1 | Confirm the closure of **P3-T02** and **P3-T04**. They were ticked on the instruction "review the open tasks and check if you can close some". | The increment review (462) notes that finding 414 had excluded box changes. Closure evidence is in `specs/024-maestro-lite-lifecycle/review/task-closure-assessment-20261021.md`. |
| D2 | Accept increment 19 as an engineering increment, merge it to main and push. | Separate decisions, as for increments 17 and 18. The ten unknown-cause records stay UNKNOWN: the campaign showed no recurrence on a quiet host (464). |
| D3 | Approve a canonical-note paragraph (Note 23) for increment 19 and the task closures. | Proposed only. |
| D4 | Approve a CAPA successor (step 3) that moves **ML-CAPA-359** from UNKNOWN to HYPOTHESIS (F-08/F-09 load class). | Finding 467 item 3: two of its tests recurred for the first time, under natural load only, and passed on the quiet rerun. Supports but does not confirm the cause; proposed, not built. |
