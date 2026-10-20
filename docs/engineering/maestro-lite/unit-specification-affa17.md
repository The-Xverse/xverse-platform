# AFFA and surviving broker unit contract — before implementation

2026-10-19 local disposal refinement: ADR-ML3-RUNTIME-0010 preceded the two-file
repair. PersistenceClient.dispose verifies actual original BootstrapChild waits
without rewriting old drain/result facts. RunBroker.admit/dispose retain finite
single-use local image-close state; ambiguous close remains unresolved and cannot
retarget a reused descriptor on replay. Whole-entry controls cover live rejection,
late wait,repeated broker disposal,partial client rejection and actual-close-then-
error with protected owned canaries.157 affected source/wheel checks each pass;
six positive product disposals and two intentional unresolved close-error cases
are separate. ML-SR-011/012/013/019/020/022/023 partial allocations and exact
source/test/evidence hashes are in runtime-disposal-partial-traceability.json.
Complete current regression and all original full17/M1/source-parent gates remain.

Current explicit-restart refinement (2026-10-19): ADR-ML3-RESTART-0001/0002 and
ADR-ML3-PROBE-0001 preceded their respective changes. FiniteDispatcher.restart
queues bounded control intent; only its original run thread mutates native state.
Exact sealed permit, original ticket identity, one in-flight request, fixed ends
and unchanged active scope are mandatory. Worker validates a safe logical phase
before successor consumption and retires the old handle pin only after original
generation preparation. Normal old-generation teardown receipts remain retained.
Version3 admission separately freezes restart_operation_seconds; versions1/2 keep
their canonical bytes. Parent probes remain live after ARM/before RELEASE, unrelated
preflight and legacy checks remain. Original closed verification covers both actual
generations; source/evidence identities and limits are in the current handoff.
These are partial U5/U7/U8 composition facts; full17 and all original gates below
remain open. In particular, normally-cleaned/transitive restart is not yet supported
by the new live-unit request predicate, and productive controller recovery is pending.

DRAFT engineering controls. Implement the whole selected M1 path and controller
survival contract; do not credit only a local gate, cooperative latch, cached ACK,
registry copied from durable metadata or new wrapper around per-unit cancellation.

Inputs are original XDL-derived admission, exactly pinned native images and private
sealed configuration, original C1/boundary descriptions, actual durable intent and
mirror/flush acknowledgements, same-authority immutable ticket identities and finite
host deadlines. Validate all sets and caps before any workload effect. Reject bool/
NaN/infinity, unknown classes/fields, duplicated units/sequences, stale epoch/session,
forged/cross-run/cross-generation handles and extra/missing file descriptions.

One original authority owns every unit's registry. No disposable operation/controller
worker can create/thaw workload boundaries. Stage is frozen, registered and epoch-
checked; actual original pidfd ownership precedes handle publication. Original C1
exists before Stage. Missing birth/handle acknowledgement remains unknown; never
recover it by PID, path or cgroup-name discovery.

Release consumes one current-epoch ticket in the authority's exclusive transition.
Cancel, timeout and lease loss close unused tickets for the whole run. For Cancel
ordered before Release, no workload marker/instruction is allowed. Prior committed
Release may run once and is later cleaned. Duplicate tickets never release twice.
An authority resumed after fallback cleanup must be incapable of creating/thawing any
resource in a certified released scope. Observe actual original death/freeze/release;
a local flag, sent signal or empty exported registry is insufficient.

Native and Python boundary contracts must be versioned and independently parsed.
Credential checks bind exact original peers. Received rights are closed on rejection.
A forged/malformed/late response never commits normal state or freshness. Bound
request/reply byte lengths, tables, polls and original absolute ends. Cancellation
and external native lease service remain independent of normal request locks.

Controller crash leaves the original issuer, storage owner and C1 holder alive.
Replacement uses a newly registered owned controller child, new private channel and
new host clock session. Retire the old channel. Reconciliation queries the exact
surviving issuer plus durable consumption/handles; all old positive freshness is
invalid. No start is implicit in reconciliation. Controller-local timeouts and the original
broker absolute-end leases remain separate; new sessions never extend old ends or
subtract their host readings from a prior session. A replacement authority rejects
old-resource adoption. Explicit restart requires new authority scope and permits
after prior transitive-dependent release.

Verify at least: two-unit cross-gate cancellation; both native orderings; duplicate/
stale/foreign tickets; cancelled/expired Stage; real stopped authority and resumed
late operation; issuer death before/after child acknowledgement; actual C1 cleanup;
replacement controller process with surviving issuer; old controller/session/fork
rejection; replacement issuer rejection; storage stall/failure independent cleanup;
source/wheel native parity; exact owned waits and removed boundaries. Preserve
unknown direct-child waits and normal-record gaps. Expected observations must be
written before implementation, not derived from candidate routines.

The complete seven P3 tasks and nine runtime acceptance cases remain open until
assembled evidence establishes them. Separate read-only findings precede repairs.
Commit only verified stable increments; no acceptance/main merge is implicit.

Generation/dependent/shared-lease continuation, still partial:
- ML-SR-005/006/010/012/016: generation_evidence.prepare_generation and original
  RunBroker preparation/advance retain real normal release and fresh M3/Argus
  provenance. test_generation_claim and test_generation_restart cover original
  receipt identity, consumed nonce, unchanged source execution, leaf1→2→3,
  original operation end and stopped storage. Historical successor-v1 evidence
  is556/556; advance-v2 is a separate frozen revision with its own receipts.
- ML-SR-006/007/011/022: ReverseTeardown._released_current and broker dependent
  checks must match the current original issuer generation and actual C1 release.
  test_generation_dependents covers the stale old-cleanup guard and an actual
  declared source→sink→terminal restart with unrelated execution retained. Fresh
  ready dependencies must cite actual generation2 probes; old matching cleanup
  remains generation1 terminal fact. Verification pending for this successor.
- ML-SR-009/010/011/019: RunBroker.renew serves the original BS17 and shared AFFA
  leases under one old common end and original mutation locks. test_run_renewal
  exercises actual old-lease expiry, unchanged handles/op ends/epoch, invalid
  requests, both lock conflicts, actual stopped storage and cancellation before
  native ACK commit. Verification pending for this successor. Renewal supplies
  no new execution approval, generation end, operation end or ticket extension.

These links are partial engineering allocations, not closure of any full requirement
or validation of the18 source-parent mappings. The full24 requirements,30 scenario
pairs/90 endpoints, nine runtime cases and all seven P3 tasks remain binding. The
selected M1/controller composition, U7/U8, full regression and independent complete
candidate review remain required before stability/acceptance can be claimed.


Controller composition partial trace (CR01–CR08, findings50–61):
ML-SR-009–014/024 link native/bootstrap.c role5 and RunBroker.admit controller budget
and original identity/session checks to test_controller actual birth/death/inheritance,
capacity, stale session and stopped-channel controls. ML-SR-006/007/012/016/022 link
ControllerSession.reconcile, IssuerRecovery and ReleaseOwner original view gating to
actual generation1/2 replacement with exact durable handles/new native probes, no
new start intent and old facade rejection. ML-SR-019/020 link actual mirror loss and
explicit unknown waits/disposal errors to retained failure evidence. The original
host session continues to label productive evidence; controller-local samples are
separate and grant no freshness. controller-focused-verification.json binds exact
11/11 inputs; controller-v5-full is pending broader verification. All source-parent
allocations remain unvalidated; no full requirement or selected M1 closure is claimed.

Shared scheduling/closure partial trace (RCL01–RCL06, SD01–SD06, findings62–73):
ML-SR-009–014/019/022 link RunClosure role-aware fencing/root drain, original per-
generation NativeGenerationClosure and cleanup-only broker context to actual normal,
resource-generation2, lost/stopped issuer/storage, queued Stage, never-issued and
mutation-conflict tests in test_shared_closure.py. ML-SR-003–011/015/016/023 link
FiniteDispatcher shared backend/controller/lease service and generation-qualified
ScheduleJournal records to test_shared_dispatcher.py five-phase/paused/stalled-
controller controls. schedule_plan.py sealed v2 service-operation admission and
worker rederivation link to test_schedule_plan.py; v1 expectations remain exact.
shared-component-verification.json binds87/87 prior shared checks; the later closure
context delta is41/41 in shared-closure-delta-verification.json. Both retain failures,
normal gaps and exact configuration identity. The new621/621 combined regression is
pending, not passing evidence. Complete U7/U8, runtime cases, source-parent validation
and independent full review before any full requirement/stable17/acceptance claim.

Terminal service partial allocation (TL01–TL04; findings135–136):
ML-SR-009/010/011/019/020 map original BS17 terminal fence/cleanup renewal and
RunBroker.service_terminal to test_terminal_service actual old-lease survival,
original authority death/reaping, actual retained writer ACK, native ordinary-renew
rejection and retained storage/lease watchdogs. Collection calls service between
bounded operations, caps each storage end by that original short lease, and retains
its aggregate end. No complete U2/U7/U8, full runtime or stable17 closure is claimed.

Finding142 strengthens the same terminal allocation: both genuine broker and the
lower BootstrapSession entry require the original registered AuthorityConnection
with its pinned native cancellation receipt or consumed original issuer wait.
Synthetic local cancellation flags cannot reach the native transition. See the
fresh boundary-successor evidence; prior b/c results bind their own exact versions.


Lazy-runtime/fenced teardown continuation (LI01–LI06, FT01–FT04, findings144–154):
ML-SR-003/004/005/006/009/010/011/015/016/019/020/021/023 map FiniteDispatcher
original full-universe construction, eligible commit/Stage, genuine binding growth,
generation0 bookkeeping and collect-before-terminal to test_lazy_dispatcher.
ScheduleJournal independently checks dispatched starts before durable consumption
and exact original issued handles; unknown commit/Stage ACKs cannot become inactive
units. Default absent-profile scheduling remains eager. Actual controller-stall
records retain all logical units/steps without fabricated M3/handles.

ML-SR-006/007/011/019/020/021 map ReverseTeardown original terminal scope,
PersistenceClient.record_teardown, worker closing restrictions and exact original
TeardownJournal issuance to test_fenced_teardown and actual implicit scheduled
teardown. Native cancellation precedes normal terminal cleanup. Original native
closed mode serves cleanup past its old productive lease; only the original root
is renewed for evidence. No start lease/ticket/end is extended. Actual normal waits,
C1 emptiness/release and normal records remain distinct from emergency gaps.

Exact component evidence: lazy-dispatch-boundary-20261019d12/12 and successor
fenced-teardown-20261019a15/15 source/installed wheel. The latter audits30 absent
roots/30 original broker waits/282 source links/six collection-terminal exports and
two past-old-lease normal cleanup controls. These overlapping scopes are not a
combined unique-test count. Earlier a18/7, b25/23+2 and c29/1 lazy scopes retain
failed audits; new evidence does not explain those failures. Affected88-case
persistence/teardown/collection/schedule compatibility passes88/88 against identical
source/tests; audit162 absent roots/78 broker waits/1020 source links. Earlier
failed paused-shared/implicit-horizon scopes remain separate open gates.

All original24/18/30/90, nine runtime cases, seven P3 tasks, full M1/races/regression,
independent complete-candidate review, stable17/acceptance/main integration remain
open. Report/writer/authoritative runtime closed-reader composition is next under
terminal-report-closure-runtime.md TR01–TR07. No full U7/U8 closure is claimed.

TR02/TR03/TR05 preparation, findings157–161: ML-SR-016/017/018/020/021/022/023
have additive partial component links to runtime_verification.py, terminal_writer.py
and coverage.py's actual accepted-annotation export. test_runtime_verification.py
uses externally fixed synthetic lifecycle observations through actual Argus writer/
reader APIs to reject shrunken units/items, substituted plans/source identities,
invalid quiescence, changed final handle/time/event/content and unchecked manifests.
test_terminal_writer.py verifies real finalize/abort/durable manifest observations,
positive flush before abort after errors, original deadline entry rejection and
labelled public/failure injection seams. Existing test_coverage.py remains compatible.
All72 source and72 installed-wheel checks pass against terminal-writer-20261019b;
all43 installed Python/native file identities match. Native resources were matched,
not executed. See terminal-writer-partial-traceability.json for exact endpoint hashes.

Original worker artifact receipt retention is added in lifecycle_evidence.py,
public_blobs.py, evidence.py and collection_runtime.py but is not runtime-verified
by this synthetic72-case scope. Original report/RPC/ACK/parent result and automatic
v6 composition remain next; no complete U7/U8/TR case or full requirement is closed.

Original report protocol composition, findings162–168 (partial TR01–TR06):
WorkerTerminal fixes reportEndNs before effects, reads actual original metadata,
final broker and retained fields/M3, assesses original rows/actual index ACKs/bytes,
writes one bounded report and privately retains eligibility/receipt. close validates
that exact digest/end before public finalize/flush/abort observations. PersistenceClient
finish_run matches original broker/collection/end, serializes attempts and returns
an immutable cached result with separate last-ACK/storage wait facts. Its v6 dispatcher
calls it after all normal terminal records. Full lifecycle completion stays false.

Original scheduler step started/probe/stop/cleanup annotations now carry exact handle
proof. Start/observe phase records carry current original prerequisite samples; start
also references the actual unit-start M3 outcome in addition to its scheduled M3
completion and readiness source. Parent validator independently matches dependencies
and handle; strict generic coverage source/ownership checks are unchanged.

test_terminal_runtime.py has nine parameterized actual native controls for explicit/
implicit closure with independent original closed recomputation, lost report/close
ACK, changed retained receipt, required missing output, matching repeat/preflight
and required/optional output corruption. Current complete96-case affected scope is
source95/1 and installed-wheel96/96 on exact unchanged b code. Actual public original
pins are retained before each new native test, including the source timeout case.
No full TR case, U7/U8, requirement or complete-candidate review is closed. A failed
writer's authenticated close observation still needs finding166 repair and verification.

Non-open close and whole-helper composition refinement (findings169–176):
ML-SR-016/017/018/019/020/022/023 map exact original terminal close shape, retained
receipt/end validation, non-open zero-writer-attempt ACK decoding and missing report
eligibility diagnostics to persistence_worker.py,terminal_runtime.py and dispatcher.py.
Owned test_terminal_faults.py embeds fixed role3 fault code into an originally admitted
bootstrap copy, leaving production C/configuration unchanged. Public abort or record+
finalize precedes lost report-index ACK; exact versus changed digest controls preserve
actual state/unknown facts with no reopening. Full100 source/wheel scope passes before
the subsequent helper-composition change; original red scopes remain retained.

ML-SR-009/011/013/018/019/020/022/023 additionally map RunClosureResult.terminal_reports
and original immutable outcome consumption to test_terminal_helper_closure.py: closed,
lost-close-ACK and missing-required cases retain the exact original receipt object,
issue no close_incomplete RPC, keep actual root/helper/native/C1 waits, leave manifest
bytes unchanged and preserve incomplete evidence diagnostics. Legacy abort-only writer
facts remain separate. All three new source controls pass; one passes in the current
wheel phase, whose other preconditions fail on fixed timing before reaching closure.

Current exact116 scope:114/2 source,109/7 wheel, tool81902 terminal1; audit13485 terminal0,
88 original wait/absent-root receipts,2382 actual M3 links,32 original pin checks,
19 retained terminal outcomes and four helper-closure results. Fourteen unreferenced
absent journals and two actual missing normal mirrors remain explicitly classified.
The evidence-scope mismatch175 and original RPC timeout budgets are NOT waived or
repaired by passing smaller scopes. All24/18/30/90,nine complete runtime cases,seven
P3 tasks,full M1/global/regression/independent review/stable17/acceptance remain open.

Original runtime evidence scope and first-error preservation (findings177–180):
RuntimeEvidenceScope validates original collection bytes/generation against the external
joint digest before evidence I/O. Only terminal/failure facts may use generation minus
drain as an outer evidence ceiling; active/productive bounds and every operational
end remain fixed. Exact M3 teardown intents require original handles and stop/cleanup
proof. Scoped reports bind runtimeAdmission; standalone coverage retains its active
default. Synthetic actual-Argus controls independently reject late productive events,
forged intent labels, substituted scope/pins and beyond-terminal facts. Native stopped
storage/controller controls preserve the first error through secondary cleanup ACK
loss, while conservative incomplete cleanup and false maturity remain separate.

Offline U7 dependency boundary (findings181–182): collection_evidence.py owns inert
decode_broker_data,decode_context,starts_fenced,output_available,validate_item,document.
The original six function ASTs match the preceding frozen snapshot, apart from the
pure BrokerDataError type. public_blobs/collection_runtime retain original runtime
PersistenceError adapters; other pure shared functions are re-exported for compatible
callers. runtime_verification imports only inert codecs. Fresh subprocesses deny
runtime transport/owner/provider/containment/supervisor imports while independently
checking ordinary and after-active synthetic closed evidence. Original evidence byte
hashes must remain unchanged. Substituted broker/context inputs must still raise
the original exact runtime exception type. These controls do not establish full
U7/U8, process admission, nine complete runtime cases or scientific outcomes.

Exact successor verification: source226/0 and installed-wheel223/3 of226 each; original tool18492 terminal1.
Audit verifies150 original broker waits,154 absent roots,
3126 M3 links and32 original external pin recomputations.
No requirement/full runtime case is closed by this component result. See the current partial trace and handoff.

Native prerequisite delegation successor: DependencyGuard._validate retains original
guard identity, coordinator, active-holder, owner, unit and exact-end checks without
a persistence RPC. Native ReleaseOwner invokes that validation before delegation;
the original broker still performs its live prerequisite check immediately before
RELEASE and both durable intent/issuance revalidations around ARM. Legacy owner keeps
its early and final live checks. No caching or deadline change. Normal targeted
native execution has two successful parent samples (active health and final guard);
actual parent death after ARM blocks RELEASE and a changed guard end rejects before
ARM. Targeted controls pass3/3 per phase; full affected scope262/265 source,265/265
wheel leaves timing stability open. No full requirement/runtime-case closure. See
guard-delegation-partial-traceability.json and continuation-guard-delegation-20261019.md.

Original native writer-failure expectations: exact admitted helper bytes inject
os.fsync while the public finalize is executing, one-shot or persistent; exceptions
at the post-close recovery/artifact-check call sites; os.replace at actual manifest
publication; or abort entry after a one-shot finalize fsync fault. No private stream
access, reopen, runtime fault flag or deadline change. One-shot fsync requires a
fresh positive public flush before at most one abort. Persistent failure retains
open/unknown usability without abort. Post-close errors retain failed process state
versus the original durable open manifest, without abort. Abort-entry failure is
attempted/unfinished with original open manifest. Original collection/report ACKs
do not imply independent collection verification from that open manifest. Complete
original helper/C1/root waits and immutable terminal result must survive without
writer RPC replay. W-02/W-03 remain unverified; these are exact fault mechanisms,
not universal physical fault coverage. Final source/wheel17/17 includes optional
receipt-export compatibility. See native-writer-stages-partial-traceability.json.

TR06 post-collection loss: successful original collection, productive teardown and
logical terminal records precede actual original storage SIGSTOP/SIGKILL or loss of
the named source/evidence directory. Signals use original retained pidfds with
nonconsuming wait observation. Directory renames remain inside the owned fixture,
retain device/inode identity and never restore/recreate the old pathname. Require
no report/close ACK, last acknowledged writer open, no invented worker writer state,
bounded actual storage reap, immutable matching terminal repeat and complete original
helper/C1/root cleanup without writer RPC replay. Retained manifest/M3/event bytes
must remain unchanged; open manifests cannot verify closed collection. Original
path absence and retained-byte availability are separate observations. Four exact
source/wheel controls pass; old/current sessions/generations, productive-phase loss,
full TR06 and M1 remain open. The productive gate is already terminal-fenced here.

Explicit cohort refinement: restart_many receives only unique exact sealed future
contexts for the original run. Validate the complete selection and outside live
dependents before stop/consumption. Reverse selected stop/cleanup, then forward
fresh generation/ADVANCE/Stage/start with real parent probes; retain unrelated
original handle. Exact normally-cleaned priors are eligible; emergency facts are
not normal release. On partial failure retain completed, failed and cancelled
members independently. Finished logical-unit replacements still require normal
terminal generation cleanup without duplicate scheduled steps. Opt-in v4 derives
phase effect/statement caps from original catalog rows; original service budgets,
active ends and old versions remain. Service at phase safe points and order lease
renewal before due health when the existing combined budgets do not fit the old
lease. Controls and limits: ADR-ML3-RESTART-0003 and transitive continuation record;
source58/59,wheel59/59 means current affected scope is not fully passing.

Active-controller refinement: opt-in replacement requests use original opaque
tickets, exact repeats and the shared restart/recovery slot. A sealed v5 recovery
cap and original unused helper/RPC/event budget bound the operation. IssuerRecovery
borrows only the original active dispatcher's reservation, never clears it, and
reconciles current-generation owned/stopped/released/never-issued rows from genuine
registry/native and worker M3/mirror facts. Only the authenticated transition may
commit new facade/controller pins and retain teardown caches. Stopped/released
rows grant no readiness; an empty original borrowed run grants no ownership or
positive evidence. A failure-only view requires the exact cancelled original
recovery, keeps original registry/C1 cleanup access and denies bind/start/probe.
Default no-start/conflict behavior is retained; typed private row vocabulary is
additive. Language allocation stays Python for bounded control/reconciliation and
existing original native BS17/AFFA for helper/workload identity; no data-plane
language or public XDL/Argus payload changes. ADR-ML3-RECOVERY-0002 and the recovery
continuation record contain phase-frontier/failure semantics and exact evidence.

Active-control deadline/cancellation refinement: reject past, foreign-session and
beyond-active ends before queue admission. An admitted request that expires before
drain is retained as rejected without helper/generation/permit/teardown mutation.
An already-cancelled queued restart must reject in preflight before mutated=True;
the original run still performs cancellation and original cleanup. Native controls
compare journal, storage/native sequence, helper, generation, handle, view and
teardown frontiers around rejection, separately from cancellation's own epoch
change and later terminal cleanup. Matching requests/results remain inert after
closure; changed ends and cloned result tickets reject. Only the early restart
cancellation check changes production behavior. Exact evidence:
evidence/affa17/active-control-deadlines-20261019c/verification.json and
active-control-deadlines-partial-traceability.json; full17 remains open.

Owned native stream fixture: the derivative BS17 image binds exact fixed role3/
role5 observer code and an embedded library ELF before original helper admission.
Only role3 receives its sealed memfd/preload; actual role5 observes absent symbol
and environment. The production bootstrap source is unchanged, and an auditor
reverses every fixture seam to those exact original bytes. Fixed C code selects
only a writable regular descriptor at the declared public stream pathname/file
identity, emits bounded no-content traces and leaves writer internals inaccessible.
Write injection occurs before the kernel syscall; W03 performs the real successful
close before returning EIO. Clocked public/native observations retain all seed,
target and fresh-flush/abort facts. An explicit failed extra fixture annotation
preconditions W02; it receives no normal Maestro credit or isolated-fault claim.
Original a's unsupported successful-append mechanism and b's pin-recorder failure
remain historical. c verifies four modes per source/wheel phase with exact original
cleanup and only two normal complete closed roots. No complete W/TR03/TR06/M1/full17
claim follows. See native-writer-stream-partial-traceability.json and ADR-ML3-WRITER-FAULT-0001.

Selected composed authority controls: use original v6 lazy dispatcher/terminal
path on the original coordinator process, deterministic original-connection
send/receive/reply and issuance boundaries, actual original helper pidfd loss,
and an independent active owned heartbeat C1. No frame/pin/handle/deadline edits.
A genuine queued Stage ACK after issuer death may preserve factual issuance;
ordinary start and inferred workload waits remain forbidden. Active membership
observations do not replace production frozen-membership certification. Verify
zero EXEC before Release, exactly one when Release wins, no normal started
record after interruption, exact cleanup and honest incomplete public evidence.
Nine source/wheel controls are partial: composed-authority-interruptions.md and
composed-authority-partial-traceability-v2.json retain CP/matrix/full-case gaps.

Selected CP07/08/12 controls: a pre-admitted fixed role3 argv derivative observes
public start-intent append and explicit flush returns. Non-consuming original
pidfd stopped observation precedes exact original storage kill. Before-append
must preserve durable M3 without a mirror; after-flush-return preserves the
actual mirror but no host RPC ACK/claim/ticket. Both forbid Stage/ARM/Release and
workload. STOP controls admit a fixed leader+descendant executable through XDL
before birth and interrupt original send/receive/reply boundaries. Retain cached
waits only from actual ACKs and observe exact scope release, normal gaps and the
active unrelated heartbeat. Full subwindow/matrix/M1 claims remain open. Tests:
test_composed_persistence_termination.py; evidence and limits:
composed-intent-termination.md and its bidirectional partial trace.

Original issuer-loss refinement: distinguish original cleanup context from
ordinary issuer-registry validation. RunBroker and original unit cancel validate
fixed original pins and retain genuine native epoch/revocation/wait even after
ordinary registry references are substituted. Ordinary lookup/observe/start still
reject. RunClosure snapshots the retained original generation registry/log, uses
existing issuer factual checks or unknown rows and continues exact cleanup when
inventory is unavailable. No adoption or manufactured wait. Real queued Stage/
Release requests to the stopped original authority require actual issuer wait
before productive scope removal and reject late reuse/resumption. Source, tests,
ADR, original red evidence and54/54 affected source/wheel proof are bound in
issuer-loss-partial-traceability.json; full CP/capability-lifecycle/M1 remains open.

Joint runtime preflight under ADR-ML3-RUNTIME-0001: bind original v6 and BS17
bytes, preparation, external authorization/facility/design/implementation/
environment pins, exact helper and nine-case receipt metadata, separate bootstrap
approval, original host lease/cleanup end and aware UTC start window. Rederive
through existing serializers; enforce tuple/byte bounds and stable bad-FD errors.
No process, C1, M3/Argus sink, receipt-file proof or public start. Immutable result
is always not-ready.40 new unit controls plus existing compatibility checks pass
146/146 per phase with explicitly synthetic inert attestations. Actual launcher,
live artifact/facility validation, original run registry and complete control/
terminal entry remain mandatory. See runtime-entry.md and its partial trace.
