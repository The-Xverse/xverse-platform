# Author decisions proposed and acted on; no run live

2026-10-20 (UTC). Goal ACTIVE. Supersedes continuation-harness-repairs-20261020.md (its run
history and baseline description remain valid). Author instruction 2026-10-20: "for the author
decisions, propose something and proceed". Work by Claude in the isolated candidate. Stable parent
46e0ebfd332dd833322d764191a7cfe1e008bec1; increment17 remains dirty; no commit; no run live.

## Dispositions (finding 369; record `author-decisions-proposed-20261020.json`, sha256 9920f79c…)

Each is an agent proposal acted on under the author's proceed instruction. None is an explicit
author approval; each derived artefact carries a provisional status that only an explicit author
confirmation can advance.

| Decision | Proposal | Acted on |
| --- | --- | --- |
| (a) source-parent projection v2 | ACCEPT PROVISIONALLY | thesis successor `engineering/successors/ML-SOURCE-PARENT-2026-10-20-v3/source-parent-register.json` (sha256 e37b4ee8…; 18 identities, 76 proposed links; semantics `proposed_public_safe_summary_provisional`); canonical v2 register bd97f975…, proposal 0183f57a… and the five immutable inputs verified unchanged (finding 370) |
| (b) endpoint reconciliation | AUTHORIZE agent-drafted proposal | `endpoint-reconciliation-proposal-20261020.json` (sha256 80ad3bea…): 7 present, 16 mapped, 38 mapped_candidate, 1 superseded; all targets resolve against the AST; 0 of 90 obligations closed (finding 371) |
| (c) transitive cadence redesign | DEFER with trigger | trigger: a transitive-cohort expiry in two of the next three baseline runs, or two in one run; shape cadence 8 s / 0.5 s budgets (period 3.5 s > scan 2.0 s, 15 slots) recorded on ML-CAPA-366 |
| (d) tmpfs | KEEP, with a persistent-media reference run | declared per run; fsync probe retained; one ext4 reference run per increment before acceptance evidence; recorded on ML-CAPA-364 |

CAPA successor `capa-20261020-author-decisions/register.json` sha256
9b9cba0ea0eea76fe0e22d80dd84a18965fc5b4ab8a9fb1eafc2a6b2c642cddb, **45 records/307 bindings**,
parent capa-20261020-run-h (45/302, f563f188…) fully preserved; both validators pass. No state
advanced; no effectiveness claimed; ten unknown causes remain (135, 286, 287, 318, 324, 330,
331, 332, 337, 359). Findings 369–371 in review-affa17.md.

## Remaining author gates (explicit confirmation requested)

1. Confirm or amend AD-2026-10-20-a (public-safe classification and semantic fidelity of the 18
   summaries); on confirmation, re-point the candidate traceability records from the immutable
   v2 register to the v3 successor under a new finding.
2. Commission the independent review of the endpoint mapping (AD-2026-10-20-b); only that review
   closes obligations and re-binds the 24/18/30/90 trace.
3. Confirm the deferral trigger (c) and the tmpfs terms (d).
4. Unchanged: acceptance, M1, main merge, factory runs (only via
   /home/jefferson/x-verse_fabric/automation/factory_start.py), scientific claims, canonical-note
   edits (a DRAFT paragraph is proposed in ../../canonical-note-update-proposal-affa17.md).

## Baseline and next work

Baseline remains run h (1 failed/2093 passed; environment d, drivers f–h pattern, TMPDIR on
tmpfs, probe outside the basetemp, fixture repairs 362/364 narrowed, transitive budget 0.3 s).
Next, in order: the remaining crash-point item (authority/storage loss injected exactly before
the Release send) with hand-authored expectations; IR-ML3-04 lane admission prerequisites; the
persistent-media reference run under disposition (d); full 024 scope (seven P3 tasks, independent
complete review, stable increment17 commit, acceptance, merge), all author-gated.

Thesis: /home/jefferson/distributed_safety_critical_thesis, branch
agent/synchronize-thesis-obsidian-notes, HEAD d97fdd1 (local ahead of origin by 17; fetch
succeeded; no incoming note commits; no pull), note SHA
01fcce48696c30d8e8cf46fa60fcf28eae9f45c19a8885df86528832e18b4abb unchanged.

## Update: author sign-off, redesign results, run i LIVE (finding 373–375)

Author sign-off 2026-10-20 ("I sign-off all of those five", record `author-signoff-20261020.json`
sha256 956cbc43…): dispositions a–d confirmed; a separate review agent counts as independent;
increment17 may be committed after a clean full run; Note 23 applied to the canonical note (new
note SHA a1bbca901651a20dd6d2aacdce9ed760bae80bd1c6f5a8a83211586a5a7437e8); thesis branch pushed
(fe58918..d97fdd1). Fixture redesign for the residual child failure separately authorized.

Done since: source-parent register v4 (author-confirmed,
`engineering/successors/ML-SOURCE-PARENT-2026-10-20-v4/`, sha256 41e28ad0…); crash-matrix b
(release-before-send controls, 17/17 per phase, receipt f260e97d…; finding 372, storage-fault
expectation corrected after observation and declared); schedule-worker lease comparison fixed at
nanosecond resolution (finding 374, test redesign, 15 passed locally); transitive redesign found
infeasible within the fixture (finding 375: probe cap 5 s, restart budget 2 s, period invariant;
product proposal: terminal statement at dispatcher.py:1465 to use per_unit_seconds, author
decision required). Independent review of the endpoint mapping by a separate agent in progress
(outputs `endpoint-reconciliation-independent-review-20261020.{json,md}` when present).

**Run i LIVE**: driver `verify-platform-regression-20261020i.py` (REPAIRED adds
test_schedule_worker.py), driver PID 2896923, pytest PID 2897880, 2096 collected, environment d,
TMPDIR on tmpfs, probe outside the basetemp. Expected ~41 min. Terminal receipt:
`platform-regression-20261020i/source-receipt.json`. Then: triage, correlate, finding 376, CAPA
successor from capa-20261020-author-decisions (never overwrite), docs; if the run is clean
(0 failed) commit increment17 on the candidate branch as authorized; otherwise record and do
not commit. Do not restart a live run because a log is stale.

## Run i terminal and author rulings (findings 376–378); checkpoint commit

Run i: **2096 passed, 0 failed**, 2470 s, inputs unchanged (receipt dcd5ebc2…, log 99a12f0c…,
triage 1f5e745d…; probe 9875 samples/0 spikes; GC max 0.054 s). First clean full run; nested
child passed completely. Author rulings ("1 accepted. 2 i authorize"): endpoint proposal v2
accepted and the 90 obligations re-bound (`endpoint-rebound-traceability-20261020.json`
0ab343d7…); the run-terminal budget product change is authorized (dispatcher.py:1465 →
per_unit_seconds), to be applied after the checkpoint commit and verified by run j. CAPA
successor `capa-20261020-run-i/register.json` 49bd43abf862574ac46888cb249fd9944e873ab634b1d9ee1c7d244ea94600d2
(46 records/332 bindings, parent 45/307 preserved; adds ML-CAPA-374).

Checkpoint commit: the run-i snapshot (sources, tests, docs, evidence, CAPA chain) is committed
on candidate/maestro-lite-affa17-20261018 as authorized (finding 373). The candidate has no
upstream; nothing is pushed or merged. Next: apply the product change (own finding), verify the
transitive and crash-point modules, launch run j with REPAIRED extended to dispatcher.py, then
the ext4 reference run (disposition d), IR-ML3-04 prerequisites, full 024 scope. No run is live
at this point.

Checkpoint commit created: **1e081a1ba37a8ea9fdf0f5230ffb61a4157652d3** on
candidate/maestro-lite-affa17-20261018 (123,339 files; sources, tests, docs, evidence, CAPA chain of
the run-i snapshot; no upstream, nothing pushed). Product change of finding 379 applied after the
commit (dispatcher.py run-terminal statement budget → per_unit_seconds); driver
`verify-platform-regression-20261020j.py` prepared (REPAIRED adds dispatcher.py).
Targeted verification of the change (source phase, candidate): transitive restart, control
deadlines, controller recovery, shared dispatcher, post-release loss and dispatch diagnostics
modules, **37 passed** in 244 s. **Run j LIVE** (driver verify-platform-regression-20261020j.py,
2096 collected); terminal receipt `platform-regression-20261020j/source-receipt.json`. Then:
triage, finding 380, CAPA successor from capa-20261020-run-i (binds dispatcher.py as the
candidate patch of ML-CAPA-366's authorized correction), docs; commit the product change as a
second checkpoint only if run j is clean.

## Run j terminal (finding 380); run k LIVE

Run j: **2096 passed, 0 failed**, 2477 s, inputs unchanged (receipt c844c684…, log a18e4702…,
triage f32bd56c…; probe 9901 samples/0 spikes; GC max 0.054 s). The product change is full-suite
verified on tmpfs. CAPA successor `capa-20261020-run-j/register.json`
5442b5438788fe280d9a4b73137d56c631ec900f4aa9bc4f5d28c2f97173d976 (47 records/343 bindings,
parent 46/332 preserved; adds ML-CAPA-379).

**Run k LIVE** (persistent-media reference run, disposition d): driver
`verify-platform-regression-20261020k.py`, driver PID 4166655, pytest PID 4170570, 2096
collected, TMPDIR/basetemp/probe on the ext4 root (/tmp, 91 percent full). Terminal receipt:
`platform-regression-20261020k/source-receipt.json`. Its expiries are host-condition
observations (triage, correlate with the ext4 probe, finding 381, CAPA successor from run-j),
not acceptance failures. Second checkpoint commit of the product change (dispatcher.py, docs,
run-j evidence, CAPA j) is made while k runs, excluding k's live directory.
Second checkpoint commit created: **36e6bf132** (product change, run-j evidence, CAPA j, driver k)
on top of 1e081a1b; only run k's live directory and driver log remain untracked until k is terminal.

## IR-ML3-04 prerequisites (finding 381)

Helper-bytes independent review recorded (dddbec1c…; 6 ENFORCED / 1 PARTIAL; 0 HIGH, 2 MEDIUM
verified by this session, 5 LOW, 9 NOTE) and lane admission proposal built from real pins
(325f3286…; facility 419c46e2…, readiness cdeebd4d…; not an admission). Pending author:
disposition of F-01/F-02 and the partial watchdog verdict; activation of a bounded lane
admission test. Run k still live; its CAPA successor will add F-01/F-02 as UNRESOLVED
observations and bind the review and proposal.

## Finding 382 work in progress (author: "propose something and go")

Dispositions acted on: F-01/F-02 = documented Python-side precondition for increment17 with owned
tests; native strengthening queued for the next increment. New untracked controls (not yet
committed): `tests/thesis_lite/maestro/test_affa_release_timeout_fence.py` (F-01: REJECTED after
the ticket under a frozen ancestor, cleanup-only fence before any thaw, no marker; passes locally)
and `tests/thesis_lite/maestro/test_runtime_lane_admission.py` (real pins through
MAESTRO_LANE_PROPOSAL; skipped without it). F-02 is already covered by
test_affa_client.py::test_advance_requires_actual_original_watched_C1_before_send. Driver
`verify-lane-admission-20261020a.py` prepared (OUT lane-admission-20261020a). PENDING until run k
is terminal (frozen-input manifest): a one-line edit of test_runtime_entry.py introducing a
module constant ENVIRONMENT_DIGEST (used at the bootstrap admission) so the lane test can pin the
verification-environment digest; then run the lane driver, record finding 383, and include
test_runtime_entry.py in the next full-run driver's REPAIRED tuple.

## Run k terminal (finding 383), lane admission verified (finding 384), run l LIVE

Run k (ext4 reference): 2 failed/2094 passed; probe 9 spikes (worst 1.18 s); outer expiry a 0.3 s
unit-disposition statement in the terminal section (bounds 379; extension proposed for the
author); child 3 failures of the stall class; host-condition observations per disposition d.
CAPA successor `capa-20261020-run-k/register.json` 7bac7f7c01f6b32c7839d2c595d6b667391662607a7d4cbf8b399fb288290ba5
(49 records/359 bindings; adds ML-CAPA-381-F01/F02). Lane admission driver b: 23 passed per
phase (receipt 622c92db…); driver a retained with its fixture-import harness error.
test_runtime_entry.py now carries ENVIRONMENT_DIGEST. **Run l LIVE**: driver
verify-platform-regression-20261020l.py (REPAIRED adds test_runtime_entry.py; ADDED adds the two
new modules; 2098 collected). Commits: evidence/docs of run k and the IR-ML3-04 records as the
third checkpoint now; tests and lane evidence as the fourth checkpoint after a clean run l.
Pending author: extension of the per-unit budget to the terminal section's unit statements
(finding 383 d); lane activation; M1; acceptance; merge.

## Run l terminal (finding 388); review (386) and confirmation (387); fourth checkpoint

Run l: **2097 passed/1 skipped/0 failed**, 2409 s, inputs unchanged (receipt 286392d3…, log
abaef48b…, triage b343c7dd…; probe 0 spikes). Complete independent review record
increment17-independent-review-20261020.json (e9f4dd64…): B-01/B-02/B-03 and N-01..N-09 recorded
with dispositions in finding 386; author confirmed the finding-382 dispositions ("yes", finding
387, record author-confirmation-382-20261020.json). CAPA successor
`capa-20261020-run-l/register.json` 155f89b5aa9545dff4823301b21998e3dbc01b3ece733a7237058c39d4fd048c
(49 records/385 bindings, parent run-k preserved). Fourth checkpoint commits the three test files
at the run-l-verified bytes plus run-l evidence and docs. Then, under finding 389: apply the
scripted test changes (B-02 F-01 discriminators, N-02 integer-nanosecond comparison, N-03
docstring) and the author-authorized terminal-section extension (dispatcher.py failure/
step-disposition/unit-disposition statements → per_unit_seconds, capped by work_end), targeted
verification, lane driver c, full run m (driver m prepared; REPAIRED already lists dispatcher.py
and test_schedule_worker.py), fifth checkpoint. Then the author's acceptance decision.
