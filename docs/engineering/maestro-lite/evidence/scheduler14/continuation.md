# Scheduler 14 working continuation — not a stable increment

Parent/source HEAD 4b1c42753fa8bf874720cf181740db0729d5039c. Worktree:
/home/jefferson/xverse-platform-worktrees/maestro-lite-scheduler-20261018
Branch candidate/maestro-lite-scheduler14-20261018. Uncommitted authorized work.
Latest stable thesis checkpoint remains 539a1d18f0d66ac3b76dc7ca3c37228167802c12.
Previous turn is progress: real source changes, recorded findings/repairs and 124
passing current composition cases. Goal remains active across the entire Lite scope.

Read working-state.json, working-traceability.json, ../../review-scheduler14.md,
../../ADR-ML3-SCHEDULER-0001.md and ../../unit-specification-scheduler14.md.
The historical teardown13 verification proves its exact parent, not this working tree.
No full source regression or copied isolated wheel consumer run has been performed
for scheduler14. No new source/thesis checkpoint was committed; the full increment
is unfinished. Commit each verified stable increment when its defined work is done.

## Current code and actual checks

- schedule_plan.py: pure finite admission and independent canonical decode. Exact
  original policy/unit set, finite active/operation/cadence/pacing/teardown bounds,
  zero/paused/monotonic finite tick sequence, event/call caps. Legacy default 128;
  explicitly bound scheduled cap 128..8192. Subnormal derived-slot overflow rejects.
- persistence.py/worker: optional hashed schedule input and independent validation
  before storage opens, exact init ACK and pinned per-session cap. Private framing
  remains version 1/64 KiB and original credentials. Legacy shape/cap unchanged.
- schedule_evidence.py: actual original-worker finite tick pull/completion cursor,
  schema-v2 run-scoped clock-validation annotations, actual public append/flush and
  retained-reader comparison. These alone do not prove declared step completion.
- lifecycle_evidence.py: separate outcomes-producer counter from shared event mirror
  register; event-cap accounting shared with teardown/schedule/claim annotations.
- owner.py: original native RENEW/RENEWED wrapper, exact ACK before updating the
  retained lease pin. No native source/wire change. Root renewal is still separate.
- teardown.py: separate scoped stop/cleanup with original handles/C1, original
  controller caches, retiring stopped units from active readiness, final reverse
  cleanup retaining already-cleaned facts. Skip only that controller's confirmed
  cleaned units in live snapshots. providers.py avoids invented first-sample health
  deadlines and excludes retired units from cadence scheduling.
- 25 admission tests + 14 owned worker/scoped tests + 27 teardown + 35 provider +
  23 outcomes = 124 passed in composition-v3.log. Installed 22 module identities
  match current source in installed-module-identity-v3.json. Current 87 roots and
  92 roots from historical retained runs are absent. Native strict/full regression
  verification remains pending for the final increment. Findings are separate
  same-agent inspections, not independent full-candidate review.

Python: /tmp/maestro-lite-scheduler-verify-20261018/bin/python
This venv was copied from the stable parent's environment and receives real wheels.
After ANY product edit rebuild/reinstall the real wheel before original -I workers
or wheel tests, then recheck installed source identity. Direct Python path only;
never resolve the venv interpreter to the shared system executable.

Retain all raw failed logs and archives. composition-v1 had six expected Init
mismatches from a stale installed wheel plus one real cleaned-registry bug; it is
not current-candidate verification. health-deadline-red reproduces min(empty) before
its repair. Current v3 source was unchanged during its actual check.

## Concrete next implementation

1. Finish ScheduleJournal normal step dispatch/phase outcomes, exactly one step
   terminal disposition, bounded factual missing-Query diagnostics (at most one per
   unit), unit/run dispositions and typed original-client receipts. Use accepted M3
   append and Argus APIs, exact phase action IDs/public source hashes, shared mirror
   history, independent producer counters, clocks and original claim/handle scope.
   Do not fabricate normal ready/stopped/cleaned results from missing observations.
2. Before admitting the dispatcher, revise the event calculation: two RPCs per
   step are planned, but a successful completion needs both its phase annotation
   and its terminal-disposition annotation, in addition to dispatch. Current draft
   counts only two annotations per step. Preserve the separate n diagnostic reserve
   already added; enforce one-use in the journal. Recompute exact independent test
   expectations and worker round trip. Do not silently enlarge limits.
3. Implement the original-holder FiniteDispatcher over already-issued bound original
   resources and BootstrapSession. Reject prior releases/attempts/tick consumption
   when beginning a full dispatch. Full-mode worker step/tick state must validate
   identities, combined eligibility, dispatch/completion windows, durations and
   actual durable readiness/stop/cleanup sources. Raw tick validation is not proof
   that a step executed. Cover prepare/start/observe/stop/cleanup, honest blocked/
   failed/cancelled dispositions and mandatory final-horizon reverse cleanup.
4. Service host health and root/individual gate leases independently of paused ticks.
   Reserve a whole admitted scan/renewal margin; cap every intervening operation by
   the next due deadline and original active end. A late/missing observation closes
   starts and initiates original reverse cleanup within the original reserve.
   Pacing is explicitly host pacing, never inferred simulation rate. Root renewal
   does not renew gates; cancellation cannot be reversed by a lease ACK.
5. Where normal failure/disposition records remain possible after cancellation,
   any client RPC exception must stay closed; never reopen a failed worker. Any
   allow-cancel path must be limited to exact factual failure/terminal kinds, with
   an irreversible worker closing state. It must not permit tick progression,
   dispatch, probes, new permits, start, restart or ownership adoption.
6. Add real full-phase XDL/owned integration cases, paused/duration/tick faults,
   health/issuer/storage hangs, malformed receipts, mutation conflicts and repeats.
   Record separate read-only findings BEFORE fixes, preserve failed-source archives,
   then verify source + copied isolated installed wheel, exact hashes, ownership/
   reaping (including explicit forced-loss unknowns), full platform regression and
   component trace before stable source and thesis commits.

All seven full P3 tasks remain open. Retain all 24 ML-SR, 18 unvalidated/null-mapped
REF-002 parents, 30 scenario pairs, 90 declared endpoints and nine full runtime
cases. Original bootstrap/environment admission, full helper closure/global M1,
restart/recovery, U7 dual assessment, U8 collection/results, G1/G3/G4/G5, independent
full review and explicit acceptance remain open. Phases 4–9 remain downstream.
No canonical-note, scientific protocol/result, main or legacy change. No factory
run. Any new run must use /home/jefferson/x-verse_fabric/automation/factory_start.py.
Follow both AGENTS.md, perform the thesis Git freshness check and read the complete
canonical dynamic note before significant work. Do not infer author approval from
DRAFT records. Sol/high recommended for the dispatcher/authority integration.
