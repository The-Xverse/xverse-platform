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
