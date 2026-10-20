# Maestro continuation — non-open writer/helper closure and clock-scope gap

2026-10-19. Goal ACTIVE; previous and current turns are PROGRESS (substantive
production fixes, native failure controls, helper composition, stronger failing
verification and an identified clock-scope gap). No impasse/user decision needed.
Entire nine-phase dissertation Lite objective remains intact. Accepted phases2/9
(~22% by accepted milestones, not measured implementation completeness).16 stable
Maestro increments committed. Selected COMPLETE increment17 remains unfinished and
uncommitted; do not substitute a smaller stable component checkpoint. User asks to
commit every completed stable increment. No acceptance/main merge/publication or
scientific campaign/canonical-note mutation is implied. No agents or factory runs.

## Repositories/freshness/authority

Thesis /home/jefferson/distributed_safety_critical_thesis,
branch agent/synchronize-thesis-obsidian-notes, HEAD
28f8f74ff9a49f247f41921ed81863b18cd56626; upstream
origin/agent/synchronize-thesis-obsidian-notes at
fe58918f9eaf2a6f39cdc9c93cfd4ce615ec84bf. Fresh fetch --prune origin succeeded
THIS turn, tool84180 terminal0. No incoming canonical-note commit; no pull.
Canonical note known version SHA256 remains
01fcce48696c30d8e8cf46fa60fcf28eae9f45c19a8885df86528832e18b4abb.
Do not claim fresh complete rereading of this known version. Preserve author's dirty
AGENTS/note and unrelated untracked files. Only existing canonical-note proposal was
appended; actual notes/dynamic_thesis_notes.md was not edited.

Candidate /home/jefferson/xverse-platform-worktrees/maestro-lite-affa-20261018,
branch candidate/maestro-lite-affa17-20261018, stable HEAD16
46e0ebfd332dd833322d764191a7cfe1e008bec1. Owner repository
/home/jefferson/xverse-platform main previously pinned
c2997c0f810d117cf45b2e34a4011b3ba7219494; recheck before integration.
Follow both AGENTS, owning constitution/Spec Kit workflow, external capability024/
ML-DESIGN-2026-10-03-v2 (not main020). coverage-runtime-closure-inputs.json binds
original context/design sources. Separate read-only findings precede repair; this
turn records169–176 and ADR refinements before implementation.

RF-2026-08-30-v6/AEB-EXPERIMENT-2026-08-30-v2 remain: one heterogeneous AEB,frozen
ML,competent paired fixed/MLOC principal comparison,separate targeted authorization/
transition-verification ablations,no oracle leakage,MRC availability credit,invented
thresholds/results. Code/engineering docs only; no academic prose/LaTeX change.
New factory runs must enter /home/jefferson/x-verse_fabric/automation/factory_start.py
with runtime operational state there. These owned component checks are not factory
or scientific runs. Canonical-note changes/acceptance/main integration remain gated.

## Implementation carried forward

Read prior continuation-terminal-runtime-20261019.md for original v6 WorkerTerminal,
finish_run, automatic dispatcher report/close, scheduler handle/dependency/source proof
and older histories. Current changes extend that implementation, do not replace it.

Finding166 repaired: original worker request guard admits non-open writer observation
ONLY for exact terminal close shape with original retained WorkerTerminal receipt.
WorkerTerminal.close still checks actual receipt digest and same original fixed end
BEFORE any observation. Parent _writer_ack accepts before_state=failed/closed only
with unchanged after state, stage not-open and zero writer attempts/completions.
Public writer helper never reopens or aborts/finalizes such a writer. Dispatcher now
separately checks report eligibility; actual independently complete closed evidence
does not mint a missing original report-index ACK.

New test_terminal_faults.py compiles an OWNED test bootstrap from unchanged production
bootstrap.c, changing ONLY role3's fixed -m invocation to fixed -c fault code. Its
exact compiled digest is passed through normal original BootstrapAdmission; unchanged
sealed interpreter image/native clone/C1/lease/parent mechanics remain. No production
fault mode/config field/environment hook was added. Fixed code intercepts report
indexing and calls actual public abort (failed) or record+finalize (closed), then
raises to lose the index ACK. Four controls compare original versus changed report
receipt. Compiled source/binaries/code hashes and archives are retained by audit.

Finding173 repaired in run_closure.py: RunClosureResult.terminal_reports is additive.
A genuine original client's pinned terminal outcome is matched to original broker/
root and retained EXACTLY; no close_incomplete replay or fake legacy abort fields.
Incomplete/missing report/ACK adds ML-CLOSURE-REPORT-INCOMPLETE. All original native
workload/authority/root/helper/C1 waits continue. Legacy clients without a terminal
outcome keep abort-only close_incomplete behavior. lifecycle_complete,ready_for_execution
and local_control_disposed remain false under existing maturity/ownership gates.

New test_terminal_helper_closure.py covers closed,lost-close-ACK and required missing
output. It verifies exact original receipt object, no writer RPC, unchanged manifest,
all original helper/root/C1 waits, separate cleanup/execution/evidence and matching
repeat. Retention converts receipt public_bytes to public_data before JSON writing.
All three pass in current source phase; one passes in wheel, other two fail earlier
on persistence timing and never reach new helper assertion. Legacy shared closure/
paused scheduling pass in both current phases; that does not explain older failures.

Native report/fault/helper tests now import original observe_original_operations
fixture. RPC measurements retain began/ended/fixed end/observed_at/generation and
actual protocol diagnostics. No assertion/deadline/requiredness was weakened.

## Evidence ledger — exact, do not conflate

terminal-fault-red-20261019a:1 pass/3 fail of4 source, tool8695 terminal1,no wheel.
Failed-state case reproduces old close guard. Closed cases also expose test error:
Argus finalize publishes manifest without run-closed event; abort appends run-failed.
Only test expectation corrected; old artifacts retained.

terminal-fault-red-20261019b:2 pass/2 fail source, tool84819 terminal1,no wheel.
Both genuine non-open cases reproduce old guard ML-PERSIST-ACK; changed digests reject.
Audits of both red scopes complete tool54211 terminal0, retaining actual original
pins, helper artifacts/root waits, code snapshots and raw public files.

terminal-nonopen-20261019c:100 source/100 installed wheel pass, tool73984 terminal0.
Audit12953 terminal0:56 original broker wait receipts/56 absent roots,1740 actual M3
source links,26 original pin recomputations/terminal outcomes,eight owned fault helpers.
Both phases retain26 observational RPC files; max probe duration ~105.18ms source,
~102.23ms wheel (exact data in audit; not performance guarantees or scientific results).
No old source timeout reproduced; none declared repaired. This snapshot PRECEDES
RunClosure terminal_reports change. Do not claim its green result verifies later code.

terminal-helper-red-20261019d:0 pass/3 fail source, tool38819 terminal1,no wheel.
Closed/lost-ACK cases prove extra close_incomplete replay. Required-missing fails
before target: final tick-complete RPC entry budget49.677434ms,elapsed50.257145ms,
ML-PERSIST-TIMEOUT followed by secondary cleanup diagnostic. Actual deadline equals
original pinned active end minus10ms EXACTLY. terminal-helper-red-d-timing-analysis.json
binds original pin and observations. Explains only this exact failure stage, not
old finding165 pre-ready timeout. Audit produced via tool c5d93e terminal0.

CURRENT terminal-helper-20261019e: source114 passed/2 failed; wheel109 passed/7 failed
of116 each. Both original phases execute ONCE, tool81902 terminal1. Audit13485 terminal0:
88 actual original broker waits/88 absent roots,2382 actual M3 refs,32 external original
pin recomputations,19 retained terminal outcomes,four helper-closure controls (source3,
wheel1). Whole source/wheel scope is NOT green; no stable17 commit. No suite remains live.

Current source failures:
- required-corrupt-output: timeout at step-dispatch,499.361ms entry budget/500.120ms
  elapsed, before report; two real normal mirror gaps remain across phases.
- genuine failed-writer fault: reaches report but normal/required/applicability blockers
  appear because run-terminal/run-disposition are after active end (see next task).
Wheel failures: explicit nominal,preflight,changed optional,failed/closed non-open
fault controls,closed/lost-ACK helper controls; several timeout before their target.
No deadline was widened or failing case dropped. All failed logs/scopes are preserved.

Raw capture gaps: current e has14 absent journals with no actual M3 references in
no-M3 controls, plus TWO REAL UNMIRRORED original M3 records: source changed-required
seq20 and wheel failed-writer seq12. Those normal gaps are not satisfied by emergency
cleanup. terminal-nonopen-helper-capture-gap-review.json classifies without hiding raw
diagnostics. No original fixture is lost. Do not label all16 raw gaps harmless.

Current exact interpreter:
/tmp/maestro-lite-affa-terminal-helper-20261019e/bin/python
Frozen source:
/tmp/maestro-terminal-helper-20261019e-source-doizx0co
Outside-source consumer:
/tmp/maestro-terminal-helper-20261019e-consumer-luz3dzpd
Wheel SHA256:
58c68c897eee987e477d1f01fc4f686b5fa12b1208a934b6275c870b8394a977
Source/test manifest SHA256:
748e46bc2c5dee5d4cd38541e5bd094323494796d02d48f042fe6173bf425d25
Installed identity SHA256:
a9f69c9295e78af8f3b8fab71d802c5a69387ad64a64f004db0ac0929ce2134a
All40 Python modules/four C resources match original installed/frozen bytes. Current
source/tests match e manifest. Native suites ran serially; all observed handles ended.
Scopes overlap; never add them as unique-test totals or promote old green to current.

## Concrete next task — original active/terminal evidence scope, finding175

Evidence is retained in terminal-clock-scope-review.json. Original independently
captured active interval987152.744466627..987157.5444670591. Actual run-terminal and
run-disposition are100.301608ms AFTER active end, within the originally reserved
terminal work. Generic coverage._payload rejects ALL annotations past ad['end'], so
it rejects these terminal facts and reports missing run terminal/disposition and
unknown emergency applicability. CollectionPlan already reserves original teardown/
collection/report/drain time and independently bound generation, but generic coverage
has no separate terminal-only scope. This is a concrete composition gap, not proof
of writer guard regression or permission to accept late productive evidence.

Recommended Sol/high for this scope/clock/verification work; Luna/low for inventories.
No actual model switch or cost benchmark claimed. Proceed within existing authorization.

Before repair, inspect the governing retained-input/contracts/coverage design and
current _payload,health_window,teardown_reference,input_digests,assess_preclosure,
verify_closed,verify_runtime_closed and WorkerTerminal assessment calls. Record a
separate source/design finding and ADR refinement. Derive terminal-only bounds from
ORIGINAL independently pinned CoverageAdmission+CollectionPlan+generation, never from
report/metadata's own timestamps. Preserve original active,operation,lease,collection,
report and generation ends; do not merely enlarge fixture active_end or add arbitrary
clock tolerance. Productive intent/issuance/started/probe/ready/health outside active
must still fail. Legitimate terminal collect/stop/cleanup/disposition/run-terminal must
be assessed consistently under an original bounded terminal scope. Beyond that bound
must fail; standalone generic coverage semantics stay compatible. Rederive provisional
core and offline closed core with the SAME original trusted scope, preserving report
schema/pins or explicitly reviewing any additive contract refinement before code.
Health-window stop bounds may also need review when factual teardown occurs after
active end; do not silently require productive monitoring throughout drain or grant
late readiness credit. Test pure boundary cases BEFORE actual native composition.

Other next work:
- Diagnose captured persistence timeouts using real RPC budgets/worker workload.
  _mirrors repeatedly invokes accepted EvidenceStore.read_run over the growing stream;
  that is a source-inspection observation, NOT a measured root cause. Any optimization
  must preserve exact actual-byte/source/ownership/tamper detection and public APIs;
  do not cache blindly or extend original deadlines. Old165 cause is still unknown.
- Dispatcher cleanup exception currently overwrites an earlier diagnostic with
  ML-SCHEDULE-CLEANUP-INCOMPLETE; latest capture exposes a primary timeout underneath.
  Review preserving first cause separately from cleanup facts; no repair made yet.
- Complete remaining writer W stages,storage stall/death/root-loss,old/current generations/
  controller sessions,global races and full M1/environment/runtime verification.
- All24 requirements,18 UNVALIDATED source parents,30 pairs/90 endpoints,nine COMPLETE
  runtime cases,seven full P3 tasks,full platform regression and independent complete-
  candidate review remain binding/open. Full U7/U8/TR cases are not closed by these
  small controls. Prior135/147/149/timing/paused/horizon failures remain unwaived.
  Author deferred immediate earlier teardown repair, not stability/release gates.
- Incident126 historical collection-v6 original wheel/archive bytes were NOT recovered.
  Never rerun colliding drivers or call a mixed recovery a complete evidence bundle.
- Commit complete selected increment17 only when stable. Explicit user acceptance and
  exact main integration remain separate gates. Canonical-note changes need approval.

Current artifact map under docs/engineering/maestro-lite/evidence/affa17:
terminal-nonopen-20261019c/verification.json;terminal-helper-20261019e/verification.json;
terminal-clock-scope-review.json;terminal-helper-red-d-timing-analysis.json;
terminal-nonopen-helper-capture-gap-review.json;
terminal-nonopen-helper-partial-traceability.json (all24/18 retained;six code/two test
function endpoints; references both exact snapshots). README/tasks/unit spec/proposal
and review169–176 are updated. Prior handoffs remain history and context, not current
verification. No scientific result/acceptance/merge/canonical-note change follows.

Use set -e for mutations; preflight UNUSED evidence names and exclusive writes.
Freeze full source/tests and build/install matching wheel before workers. Literal
matching venv argv0 must stay (do not resolve to base Python). Never mutate old
snapshots/installations/scripts/archives. Native suites run serially; retain full
exec result/session_id and poll same handle through actual terminal exit. Observation
timeout is not completion. Provide concise commentary within60s. A fresh session
must follow AGENTS,repeat Git freshness and read canonical dynamic note completely.
