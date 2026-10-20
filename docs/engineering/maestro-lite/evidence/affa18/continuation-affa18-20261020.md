# Increment18 continuation

2026-10-20 (UTC). Goal ACTIVE. Successor of evidence/affa17/continuation-author-decisions-20261020.md.
Branch candidate/maestro-lite-affa18-20261020, worktree
/home/jefferson/xverse-platform-worktrees/maestro-lite-affa18-20261020, parent bdf7b29cc
(increment17 accepted, finding 392). Review log: ../../review-affa18.md (findings 393+).

## Step 1 done: native F-01 fix (findings 393-401)

- run_authority.c 2a2ee830… → b29a5239… (checkpoint 18-1 7abdb9dc0): refreeze write never skipped,
  two-pass wait over all units, independent close budget min(generation, now+2 s) on rejection
  and CANCEL; REJECTED wire format unchanged.
- Two independent reviews (F-01 change; full diff after the two-pass fix): 0 HIGH, 0 MEDIUM.
- F-01 control asserts the native refreeze; fails against the increment17 helper.
- Environment f (`/tmp/maestro-lite-platform-regression-target-20261020f`, wheel d10f8619… of this
  tree); runtime lane c, crash-point d 17/17 per phase; lane admission proposal c (built from
  7abdb9dc0) and driver e 23/23 per phase; full run o 2097 passed/1 skipped/0 failed.
- Superseded or aborted evidence retained: environment e, runtime lane b, crash-point c
  (intermediate bytes 7fde44db), proposal b (implementation pin of the parent commit), run n
  (stopped after 251 passed when the review recommended the two-pass change).
- CAPA successor capa-20261020-affa18-run-o/register.json
  2f25a62ace2633e04827df13a7900c08fafde35d5afed39ea72fdd68beb180c4 (50/437; F-01 FIX_CANDIDATE).
- Observation on increment17 (finding 393): its installed-wheel phases used the 2026-10-19 wheel,
  which predates the dispatcher changes; full runs were unaffected.

## Next (author decisions marked)

1. AUTHOR: choose the F-02 design: (i) supervisor-issued WATCH token keyed by a secret the
   supervisor generates and passes to the authority at birth, verified on ADVANCE; or (ii) ADVANCE
   boundary descriptors routed through the supervisor on a new supervisor-authority channel.
2. Persistent-media (ext4) reference run on the increment18 bytes (driver k pattern, environment f).
3. Then re-examine readiness for lane activation (still blocked by the listed findings).
4. AUTHOR: acceptance of increment18; merges of increment17/18 into main remain separate decisions.

Gates unchanged: acceptance, M1, lane activation, merges, factory runs (only via
/home/jefferson/x-verse_fabric/automation/factory_start.py), scientific claims, canonical-note edits.
Thesis: /home/jefferson/distributed_safety_critical_thesis, branch
agent/synchronize-thesis-obsidian-notes, HEAD d97fdd1, note sha256
a1bbca901651a20dd6d2aacdce9ed760bae80bd1c6f5a8a83211586a5a7437e8.

## Step 2 done: ext4 reference run p (finding 402)

Run p (driver verify-platform-regression-20261020p.py): **2097 passed/1 skipped/0 failed** on the
ext4 root, inputs unchanged; probe 0 spikes (worst 0.053 s), so the host was quiet and the
ML-CAPA-379/389 stall class was not exercised. CAPA successor
`capa-20261020-affa18-run-p/register.json` 552f79f8e846ed7adbc29eca57d80e17a6a199240d0260835f5e4502df44693d
(50 records/446 bindings). Host disk: the root filesystem stood at 94 percent at launch.

## Step 3: readiness re-examination (result)

The lane admission readiness statement still lists six blocking entries: ten unknown-cause CAPA
records (in two entries), lane activation not approved, M1 not admitted, increment18 acceptance
open, and F-02 native deferred. None is cleared by steps 1–2: no unknown cause was explained, and
F-02 awaits the author's design choice. Lane activation therefore remains correctly refused by the
product's own readiness check.

## Step 4 done: native F-02 watch proof (findings 403-409; checkpoint 18-4 e290ce78c)

- Author choice: option (i), supervisor-keyed WATCH token. bootstrap.c c1f2885d… (binary
  b47d1a01…), run_authority.c ffdc632e… (binary c0c162ea…), affa_protocol/bootstrap/affa_client/
  run_broker Python changes; new tests/thesis_lite/maestro/test_affa_watch_token.py (6 tests).
- Three independent reviews: 0 HIGH/MEDIUM; F02D-01 LOW recorded as a non-claim (no key
  confidentiality against a hostile same-uid peer); optional hardening: owner-unreadable
  authority image. The comment at run_authority.c:510 will be corrected with the next helper change.
- Environment h (wheel eca0939d…), runtime lane e, crash-point f 17/17 per phase, proposal d
  7b454c1d…, lane admission f 23/23 per phase. Run q aborted at preflight (2104 vs 2102 declared).
- Run r: **3 failed/2100 passed/1 skipped**, all F-02/F-01 controls passed; it ran under an unrelated
  CARLA simulator load (PID 3540156, started 16 min before), 65 operation stalls > 0.5 s against
  7–21 in clean runs, 0 fsync spikes. A/B `ab-load-discrimination-20261020a/` (10 interleaved
  iterations per arm): the paused-shared case failed 5/10 on d52683ad (pre-F-02) and 5/10 on e290ce78c;
  F-02 is not the discriminator; host contention supported, not proven (finding 409).
- CAPA successor capa-20261020-affa18-run-r/register.json
  7f46df79cbcee43791a10b1a924ff5959c0d64e480a27ae8ba3cda02a22935f2 (50/478; F-02 FIX_CANDIDATE).

## Next (superseded by step 5 below)

1. ~~Clean full run on e290ce78c~~ done as run s (finding 410).
2. Re-examine readiness: five blocking entries remain (ten unknown causes in two entries, lane
   activation not approved, M1 not admitted, increment18 acceptance open).
3. AUTHOR: acceptance of increment18; merges of increments 17/18 into main; lane activation; M1;
   optional F02D-01 hardening; F-05 wire revision.

## Step 5 done: clean full run s (finding 410)

Run s (driver verify-platform-regression-20261020s.py, HEAD b1dc99792 with src/tests identical to
e290ce78c): **2103 passed/1 skipped/0 failed**, child clean, F-02/F-01 controls passed, launched on
the author's go with the CARLA load still present (host_condition_at_launch in configuration.json;
61 stalls > 0.5 s, 0 fsync spikes). CAPA successor capa-20261020-affa18-run-s/register.json
4fd92f3fb2b9af81e229f8393193bb1e518c68820c95614c2463f59138014b20 (50/487). Next finding: 411.

## Next (current)

1. Readiness re-examination: five blocking entries remain (ten unknown causes in two entries, lane
   activation not approved, M1 not admitted, increment18 acceptance open).
2. AUTHOR: acceptance of increment18 (an acceptance record on the increment17 pattern, finding 392);
   merges of increments 17/18 into main; lane activation; M1; optional F02D-01 hardening; F-05.
