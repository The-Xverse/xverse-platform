# Maestro Lite lifecycle component candidates

Status: **increment18 accepted by the author (finding 411) on candidate/maestro-lite-affa18-20261020 (native F-01 and F-02 fixes; clean full runs o, p, s); not merged; increment17 accepted (finding 392); U1/U6 plus partial U2/U3/U4/U5/U7/U8; not merged; no runtime admission, lane activation or M1**.
Owning baseline: `c2997c0f810d117cf45b2e34a4011b3ba7219494`.
Authoritative feature: `/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/`.

## Increment18 accepted (2026-10-20, finding 411)

The author accepted increment18 as an engineering increment ("go with your proposal"). The terms
are in [the acceptance record](evidence/affa18/author-acceptance-increment18-20261020.json).
Scope: checkpoints 7abdb9dc0 through 3bee8fb9d, whose product changes are native F-01 and native
F-02. Basis: clean runs o, p and s, per-change independent reviews, and the lane and crash-point
evidence on the final bytes. Carried open: ten unknown causes, effectiveness NOT_DEMONSTRATED
everywhere, the F02D-01 non-claim and deferred hardening, F02D-02, F-05, and the thin-margin fixture
under load. Not covered: lane activation, M1, the merges of increments 17 and 18 into main,
factory runs, canonical-note edits and scientific claims. CAPA successor
[capa-20261020-affa18-acceptance](evidence/affa18/capa-20261020-affa18-acceptance/register.json)
(50 records/489 bindings, parent preserved; the increment18 block is accepted, merged false). A
canonical-note paragraph is [proposed, not applied](canonical-note-update-proposal-affa18.md).

## Increment18 step 5: clean full run s on the F-02 bytes (2026-10-20, finding 410)

Run s (same src and tests as e290ce78c) ends **2103 passed, 1 skipped, 0 failed**, nested child
clean, all F-02 and F-01 controls passing. That is the first clean full run on the F-02 bytes. It
ran under the same and heavier unrelated CARLA load as run r (recorded at launch; 61 operation
stalls over 0.5 s, 0 fsync spikes). Run r failed 3 and run s none at comparable stall levels,
which fits the A/B finding of an intermittent thin-margin fixture under load rather than a
regression. CAPA successor
[capa-20261020-affa18-run-s](evidence/affa18/capa-20261020-affa18-run-s/register.json)
(50 records/487 bindings, parent preserved; no state change, effectiveness NOT_DEMONSTRATED).

## Increment18 step 4: native F-02 watch proof (2026-10-20, findings 403-409)

The author chose option (i). RUN_BOOTSTRAP generates a key at init and answers every WATCH with
HMAC-SHA256(key, "MLWT"‖st_dev‖st_ino); the authority receives the key in a sealed memfd at
birth and rejects any ADVANCE whose ticket does not match the HMAC of the boundary descriptor it
is sent (constant-time compare). Both helpers make themselves non-dumpable first. Python carries
the token but cannot mint it. Three independent reviews: 0 HIGH, 0 MEDIUM; F02D-01 (LOW) is
recorded as a non-claim, since key confidentiality against a hostile same-uid peer is not
claimed (finding 407). Evidence on checkpoint 18-4 e290ce78c: six new controls, environment h, runtime lane e,
crash-point f 17/17 per phase, lane admission f 23/23 per phase. **Full run r: 3 failed / 2100
passed / 1 skipped**, with all F-02 and F-01 controls passing. It ran under an unrelated CARLA
simulator load started 16 min earlier: operation stalls over 0.5 s were 65, against 7–21 in clean
runs, with 0 fsync spikes. An interleaved A/B on the failing cases failed the paused-shared case 5/10
on the pre-F-02 bytes and 5/10 on the F-02 bytes, so F-02 is not the discriminator (finding 409).
A clean full run on e290ce78c is owed once the host is quiet. CAPA successor
[capa-20261020-affa18-run-r](evidence/affa18/capa-20261020-affa18-run-r/register.json)
(50 records/478 bindings, parent preserved; ML-CAPA-381-F02 → FIX_CANDIDATE, effectiveness
NOT_DEMONSTRATED).

## Increment18 step 2: clean persistent-media reference run p (2026-10-20, finding 402)

Run p puts the session TMPDIR, private basetemp and probe on the ext4 root (94 percent full at
launch) and ends **2097 passed, 1 skipped, 0 failed**, inputs unchanged: the first clean full run
on persistent media in increments 17–18. The host was quiet during it (0 fsync spikes over
150 ms, worst 0.053 s, against 9 spikes up to 1.18 s in run k), so the stall class that
ML-CAPA-379/389 target was not exercised and their effectiveness stays NOT_DEMONSTRATED. CAPA
successor [capa-20261020-affa18-run-p](evidence/affa18/capa-20261020-affa18-run-p/register.json)
(50 records/446 bindings, parent preserved).

## Increment18 step 1: native F-01 fix verified (2026-10-20, review-affa18.md findings 393-401)

The authority helper no longer skips its refreeze once a request deadline has elapsed: on the
rejection path and on CANCEL it writes cgroup.freeze for every live generation, then waits once over
all units within an independent close budget (run_authority.c 2a2ee830… → b29a5239…; checkpoint
18-1 7abdb9dc0). The F-01 control now asserts the native refreeze and fails against the
increment17 helper. Two independent reviews of the changed bytes found no HIGH or MEDIUM issue.
Evidence on the final bytes: environment f with a wheel of this tree (closing the finding-393 gap,
the earlier wheel predated the increment17 dispatcher changes), runtime lane c and crash-point d
17/17 per phase, lane admission driver e 23/23 per phase, full run o **2097 passed, 1 skipped,
0 failed**. CAPA successor [capa-20261020-affa18-run-o](evidence/affa18/capa-20261020-affa18-run-o/register.json)
(50 records/437 bindings, increment17 acceptance parent preserved; ML-CAPA-381-F01 → FIX_CANDIDATE).
Deferred with reasons (finding 394): F-02 native watch proof (author choice between a
supervisor-keyed WATCH token and supervisor-routed ADVANCE), F-05 distinct release-timeout reason
(wire revision), F-07 unchanged (a closed authority cannot thaw). Increment18 is not accepted; lane
activation, M1 and merges remain the author's. Follow
[the increment18 continuation](evidence/affa18/continuation-affa18-20261020.md).

## Increment17 accepted (2026-10-20, finding 392)

The author accepted increment17 as an engineering increment on the basis of four clean tmpfs
full runs (i, j, l, m), the ext4 reference run k, the complete independent review with all
blocking items closed, and the CAPA chain. The acceptance carries open, explicitly: ten CAPA
records with unknown cause, effectiveness NOT_DEMONSTRATED for every record, ML-CAPA-389's
persistent-media class unobserved since the change, the helper observations F-01/F-02 under
documented preconditions (native strengthening in increment18), and the tmpfs harness as a
declared fidelity choice. It does not cover lane activation, M1, the main merge, the remaining
024 scope, factory runs or any scientific claim. Record:
[author-acceptance-increment17-20261020.json](evidence/affa17/author-acceptance-increment17-20261020.json);
CAPA successor [capa-20261020-acceptance](evidence/affa17/capa-20261020-acceptance/register.json)
(50 records/408 bindings, run-m parent preserved). The candidate branch is backed up on origin as a
branch; the main merge is a separate author decision.

## Run m closes the review items; increment17 ready for the author's acceptance decision (2026-10-20)

Run m (2098 collected; snapshot = checkpoint 12ef86553 plus finding 389: the author-authorized
terminal-section budget extension in dispatcher.py, the F-01 discriminators, the
integer-nanosecond lease comparison and the at-most-once docstring) ends **2097 passed,
1 skipped, 0 failed** with frozen inputs unchanged and 0 probe spikes (finding 390), the fourth
consecutive clean tmpfs run; lane driver c passes 23/23 per phase with the strengthened F-01
control. Every engineering item raised by the complete independent review (finding 386) is now
closed: B-01 by checkpoint 12ef86553, B-02 by lane driver c and run m, B-03 by the author's
confirmation (finding 387); the nine notes are recorded or applied. CAPA successor
[capa-20261020-run-m](evidence/affa17/capa-20261020-run-m/register.json) validates 50 records/403
bindings preserving the run-l parent and adds ML-CAPA-389 (FIX_CANDIDATE, one tmpfs run; the
persistent-media class is observable only in a later ext4 reference run). Finding 391 records a
validator defect (file bindings to mutable source paths) resolved by a committed-blob fallback
in verify-capa-register-20261020.py without touching any register. Fifth checkpoint commits
this snapshot. Open and the author's: acceptance of increment17, lane activation (blocked by the
listed findings by the product's own readiness check), M1, the main merge, and the next-increment
native strengthening of the helpers (F-01/F-02). Ten CAPA causes remain unknown; all
effectiveness NOT_DEMONSTRATED; no scientific claim.

## Clean run l, complete independent review, author confirmations (2026-10-20)

Run l (2098 collected: the lane admission and F-01 control modules plus a fixture constant) ends
**2097 passed, 1 skipped, 0 failed** with frozen inputs unchanged and 0 probe spikes (finding
388), the third clean tmpfs run. The separate complete independent review of the increment
(`evidence/affa17/increment17-independent-review-20261020.{json,md}`, finding 386: 38 checks,
30 pass, 3 fail, 5 notes) confirmed every quoted hash and count and raised three blocking items,
all addressed: the fourth checkpoint commits the finding-384 modules at the verified bytes (B-01);
the F-01 control gains the release-timeout discriminators under its own finding with lane driver c
(B-02); the F-01/F-02 disposition is now author-confirmed (finding 387; B-03). Acceptance was not
recommended by the reviewer before those items; it remains the author's explicit act after the
next checkpoint. CAPA successor [capa-20261020-run-l](evidence/affa17/capa-20261020-run-l/register.json)
validates 49 records/385 bindings preserving the run-k parent and binds the review and the
confirmation. Next: B-02/N-02/N-03 test changes, the author-authorized terminal-section extension
(finding 383 d), lane driver c and full run m. No acceptance, M1 claim, lane activation or merge.

## ext4 reference run k and IR-ML3-04 prerequisites (2026-10-20)

Run k, the persistent-media reference run of disposition d, ends **2 failed, 2094 passed** on
the 91-percent-full ext4 root with 9 fsync spikes (worst 1.18 s) where the tmpfs runs i and j had
none (finding 383). The outer expiry is a 0.3 s unit-disposition statement in the terminal
section, overrun by 0.4 ms; it bounds finding 379, which widened only the run-terminal statement,
and a further extension is proposed for the author. The child's three failures are the same
durable-write stall class. Per disposition d these are host-condition observations, not
acceptance failures. IR-ML3-04: the independent frozen review of the helper bytes is recorded
(six fence properties enforced, independent-watchdog partial, 0 HIGH, 2 MEDIUM; finding 381) and
a non-activating [lane admission proposal](runtime-lane.md) carries real pins; the two MEDIUM
observations are dispositioned as documented Python-side preconditions with owned controls
(proposed in finding 382, confirmed by the author in finding 387; native strengthening next increment) and the native strengthening is queued for the next increment. CAPA successor
[capa-20261020-run-k](evidence/affa17/capa-20261020-run-k/register.json) validates 49 records/359
bindings preserving the run-j parent. No acceptance, M1 claim or merge.

## Product change exercised by clean run j, effectiveness NOT_DEMONSTRATED; ext4 reference run k (2026-10-20)

The author-authorized product change (finding 377/379: the dispatcher's run-terminal statement
takes `per_unit_seconds`, as teardown and cleanup already do, instead of the cadence-bound
operation budget) was applied after checkpoint 1e081a1b and verified by run j: **2096 passed,
0 failed**, frozen inputs unchanged, 0 probe spikes (finding 380), the second consecutive clean
full run. CAPA successor [capa-20261020-run-j](evidence/affa17/capa-20261020-run-j/register.json)
validates 47 records/343 bindings preserving the run-i parent and adds ML-CAPA-379
(FIX_CANDIDATE, one prevention observation; effectiveness NOT_DEMONSTRATED). The persistent-media
reference run k (disposition d: TMPDIR, basetemp and probe on the ext4 root) runs on the same
snapshot; its expiries, if any, are host-condition observations. Second checkpoint commit of the
product change follows run j. No acceptance, M1 claim or merge.

## Clean full run i and author sign-off (2026-10-20)

Run i (2096 collected, TMPDIR on tmpfs) ends **2096 passed, 0 failed** with frozen inputs
unchanged: the first clean full platform run of this increment, including the nested Argus case
whose child Maestro suite passed completely (finding 378). The residual child failure of run h
was a nanosecond-rounding test defect, repaired in test_schedule_worker.py (finding 374, ML-CAPA-374
FIX_CANDIDATE); the transitive terminal margin cannot be widened by any fixture (finding 375), and
the author authorized the product change at the run-terminal statement (finding 377), which
follows as run j. The author signed off the four dispositions, a separate review agent as
independent, the increment17 checkpoint commit after a clean run, the canonical-note Note 23 and
the thesis push (finding 373). The [endpoint reconciliation](endpoint-reconciliation-gap.md) v1
mapping was independently reviewed (32 agree, 20 with note, 1 alternative, 9 disagree; finding
376), v2 adopts the corrections and the author accepted it; the 90 obligations are re-bound in
`evidence/affa17/endpoint-rebound-traceability-20261020.json` (finding 377) without acceptance of
the implementation. The [crash-point matrix](crash-point-matrix.md) before-Release-send item is
closed (crash-matrix-20261020b, 17/17 per phase, finding 372). CAPA successor
[capa-20261020-run-i](evidence/affa17/capa-20261020-run-i/register.json) validates 46 records/332
bindings preserving the author-decisions parent. Follow the
[current continuation](evidence/affa17/continuation-author-decisions-20261020.md). No acceptance,
M1 claim or merge; the checkpoint commit captures exactly the run-i snapshot.

## Author decisions proposed and acted on (2026-10-20, provisional)

Under the author's instruction to propose dispositions and proceed, finding 369 records four
agent proposals, none an explicit author approval: (a) the source-parent projection v2 is accepted
provisionally into the thesis successor register ML-SOURCE-PARENT-2026-10-20-v3 (18 identities,
76 proposed links, semantics `proposed_public_safe_summary_provisional`; immutable inputs
unchanged); (b) an [endpoint reconciliation proposal](endpoint-reconciliation-gap.md) maps all
62 declared endpoints onto the current composition (7 present, 16 mapped, 38 candidates, 1
superseded; all targets resolve) with 0 of 90 obligations closed pending independent review;
(c) the transitive cadence redesign is deferred behind an explicit recurrence trigger; (d) tmpfs
stays the declared harness filesystem with one persistent-media reference run per increment.
CAPA successor [capa-20261020-author-decisions](evidence/affa17/capa-20261020-author-decisions/register.json)
validates 45 records/307 bindings preserving the run-h parent. Findings 369–371. Follow the
[current continuation](evidence/affa17/continuation-author-decisions-20261020.md). No product
change, no commit, no acceptance, no M1 claim, no canonical-note edit.

## Harness repairs verified and runtime lane integrated (2026-10-20, unfinished)

Five full platform runs (a–e) isolate and repair the broader-regression failures:
build tooling (357), nested-child receipt collisions (359-CHILD) and the CAPA-222
window squeeze (362/364) are fix candidates with local evidence; collector pauses
are refuted; fsync stalls on the shared ext4 root are supported, not proven, and
mitigated in the harness by a tmpfs basetemp (364, declared fidelity change). Runs e
and f end1 failed/2079 and1 failed/2087 passed with no outer Maestro expiry (the
nested child's residual expiries trace to the transitive fixture's0.3s budget, which
the5s probe cadence forces: the attempted0.5s repair was rejected at schedule
admission in run g and reverted; run h at the reverted baseline ends1 failed/2093 passed with zero outer expiries,2094 collected, and is the current baseline). CAPA successor
[capa-20261020-harness-repairs](evidence/affa17/capa-20261020-harness-repairs/register.json)
validates44 records/275 bindings preserving all245 parent bindings; ten causes remain
unknown. The [runtime lane](runtime-lane.md) implements seven of the nine
RUNTIME_CASES identifiers with real children and receipts (two remain in the composed
authority module); bounded evidence runtime-lane-20261020a passes17/17 in source and
installed-wheel phases. The [crash-point matrix](crash-point-matrix.md) closes its two gaps with
test_composed_post_release_loss.py (crash-matrix-20261020a:15/15 per phase); the
[endpoint reconciliation gap](endpoint-reconciliation-gap.md) records that7 of62
declared endpoints resolve (author-gated successor). Findings361–368. Follow the
[current continuation](evidence/affa17/continuation-harness-repairs-20261020.md).
No product change, no commit, no acceptance, no M1 claim; IR-ML3-04 prerequisites open.

## Broader platform regression triaged (2026-10-20, unfinished)

The original2080-case platform run (exec33408) is terminal:17 failed/2063 passed.
Thirteen Argus packaging cases failed only because the verification environment
lacked `build`/`hatchling` (finding357); successor run b in a separate,
preflight-bound build-capable environment on the identical1903-file snapshot
passes all13 and ends3 failed/2077 passed. The accepted nested platform case
fails in both runs with the same14 child setup errors (receipt-namespace
hypothesis, not confirmed), and five different Maestro first-RPC deadline
expiries occurred across the two runs without recurrence (UNKNOWN). Neither run
is a whole-platform pass. CAPA successor
[capa-20261019-platform-regression](evidence/affa17/capa-20261019-platform-regression/register.json)
validates43 records/245 bindings and preserves all216 parent bindings; all
effectiveness NOT_DEMONSTRATED. Findings358–360 record the review before and
after the successor. Follow the
[current continuation](evidence/affa17/continuation-platform-regression-20261019b.md).
No product/test change, no commit, no acceptance, no M1 claim.

## Active increment17 continuation (2026-10-19, unfinished)

Current [complete Maestro regression passed](integrated-regression-terminal-20261019b.md):
source1501/1501 and installed wheel1501/1501. Both audits pass, retaining1718
recorded owned roots absent,14189 M3 links and496 explicit reader/reference gaps.
The broader platform Python regression now has2080 collected tests and is live
under original exec33408/PID1669996; failures are already visible, with details
pending terminal output. This is not a whole-platform passing result.
Follow the [latest continuation](evidence/affa17/continuation-integrated-terminal-20261019b.md).

Current [local disposal repair](runtime-disposal.md) preserves original late-wait
facts and prevents repeated image closes from retargeting reused descriptors.
Four new controls and157 affected checks pass per source/wheel phase. The separate
audit retains298 absent roots,1264 M3 links and28 explicit projection gaps. Its
historical CAPA39/210 preserves198 parent bindings. Latest reviewer-shape CAPA40/
216 preserves210 parent bindings; effectiveness remains NOT_DEMONSTRATED.
Follow the [current continuation](evidence/affa17/continuation-runtime-disposal-20261019.md).
The complete current Maestro regression now passes; whole-platform,M1,stable17
and acceptance remain open.

Source-parent review now has a concrete external proposal: the original REF-002
DOCX was found locally and matches its registered hash. The corrected
[18-row projection](/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/review/source-parent-semantics-proposal-20261019-v2/README.md)
records76 candidate links to23 software IDs,explicit wider-parent residuals and
an unmapped ML-SR-021 retaining its FR-011 basis. Author approval of information
classification and semantics is pending. Canonical allocation/design inputs and
runtime readiness remain unchanged. See the
[source-review continuation](evidence/affa17/continuation-source-parent-proposal-20261019.md).

Preceding [whole-entry issuer-loss repair](runtime-issuer-loss.md) restores primary
cleanup using the original cleanup context; two new cases pass per source/wheel
phase without fallback. Selected affected source85 pass,wheel84 pass/one failure/
one teardown error; timeout337 and disposal338 remain open. Corrected CAPA37/198
also passes170-parent-binding preservation; rejected intermediate remains evidence.
Follow the [current continuation](evidence/affa17/continuation-runtime-issuer-loss-20261019.md).
Earlier counts below are exact historical snapshots,not current full-regression passes.

Historical pre-disposal [combined regression is terminal](integrated-regression-terminal-20261019.md):
source1493 passed/two failed; installed wheel1492 passed/three failed. The five
timeout causes remain UNKNOWN. Both audits confirm1706 recorded owned reservations
absent and13508 M3 reference links; they do not make the regression pass. Latest
CAPA32 records/170 bindings, all effectiveness NOT_DEMONSTRATED. No stable17,M1
or acceptance claim. Follow the [terminal continuation](evidence/affa17/continuation-integrated-terminal-20261019.md).

Latest verification: [late return/unknown startup birth](startup-late-birth.md)
adds4 low-level and2 whole-entry source/wheel controls on unchanged81 production
files. External actual reap never upgrades unknown product cleanup. Prior69 plus
new6 describe selected75 per phase; full matrices and four stability gates remain open.

Latest startup repair: [original startup resource ownership](startup-ownership.md)
rejects substituted aliases while cancellation/waits use original retained resources.
Fresh source/wheel69 checks pass each; guarded red failures and first harness
acknowledgement gaps remain retained. CAPA25 records/133 bindings validate;
135/222/286/287 remain unresolved. Older counts below describe historical snapshots.

Latest repair: [optional RPC diagnostic loss](rpc-context-loss.md) preserves actual
terminal results and fail-closed cancellation when diagnostic metadata is unavailable.
Fresh source/wheel61 checks each pass; original3-fail-per-phase evidence is retained.
CAPA now validates23 records/117 bindings;135/222/286/287 remain unresolved. Older
57/73-check statements below describe their respective frozen historical sources.

Latest diagnostic delta: [first RPC failure context](rpc-failure-context.md) retains
generated request/stage/original deadline in the private RuntimeResult after cleanup.
Fresh source/wheel57 checks each pass; exact trace and audit are linked there.
This does not explain or resolve135/222/286/287. Service73 below describes its prior
frozen component snapshot, before this additive diagnostic change.

Latest partial layer: [candidate runtime service](runtime-service.md),
[trace](evidence/affa17/runtime-service-partial-traceability.json) and
[continuation](evidence/affa17/continuation-runtime-service-20261019.md).
Fixed externally approved pins/default-deny and actual expiry/cleanup guards have
selected73 source/wheel checks per phase. Positive service vectors remain inert;
actual admitted service/M1 executions0. CAPA validates22 records/104 bindings;
135/222/286/287 remain unresolved. Older snapshots below describe their historical
revisions. Full17 remains unfinished and uncommitted.

Current: [explicit active restart handoff](evidence/affa17/continuation-active-restart-20261019.md).
Actual source46/46 and wheel46/46 plus legacy readiness35/35 in each phase are
audited against original inputs. A separately sealed version3 restart budget
supports leaf generation2 in the original blocking lifecycle. Full17 is still
unfinished; successful transitive restart and productive controller recovery are
next. Old half-second failures and teardown135 remain recorded, not waived.
See [partial traceability](evidence/affa17/active-restart-partial-traceability.json).

Earlier continuation: original storage stop/death and source/evidence-root loss after
collection pass4/4 source and4/4 installed wheel. Eight actual cleanup receipt sets
and448 M3 links are audited; the two unavailable original evidence paths remain
explicit alongside retained original-directory byte/identity verification. Production
code is unchanged; broader timing failures/full17 remain open. See the
[current handoff](evidence/affa17/continuation-terminal-loss-20261019.md),
[loss audit](evidence/affa17/terminal-loss-20261019a/verification.json) and
[partial trace](evidence/affa17/terminal-loss-partial-traceability.json).

Previous continuation: actual native worker writer-failure controls and default test
compatibility pass17/17 source and17/17 installed wheel. The audit retains12 explicit
original wait/root receipts,672 M3 links and12 external runtime-pin recomputations.
No production source/XDL changed from the guard snapshot; its three source timeouts
remain open. See [current handoff](evidence/affa17/continuation-native-writer-stages-20261019.md),
[stage audit](evidence/affa17/native-writer-stages-20261019c/verification.json) and
[partial trace](evidence/affa17/native-writer-stages-partial-traceability.json).
W-02/W-03, full TR03/TR06 and all full-increment gates remain open.

Previous successor: native guard delegation removes one duplicate prerequisite probe
while retaining the final live native check and both legacy checks. Targeted source/
wheel controls pass3/3 each; complete affected scope is source262/265, wheel265/265.
Three source persistence timeouts remain. See the [current handoff](evidence/affa17/continuation-guard-delegation-20261019.md),
[audit](evidence/affa17/guard-delegation-20261019e/verification.json) and
[partial trace](evidence/affa17/guard-delegation-partial-traceability.json).
Increment17 remains unfinished and uncommitted; older snapshots below retain their
original scope and outcomes. No broad unchanged-code rerun is warranted.

The selected shared-authority/controller/generation/evidence/runtime increment remains
uncommitted. The exact shared-v4-full snapshot passes621 source and621 outside-source
installed-wheel checks; its audit verifies786 removed owned roots,142 public snapshots,
28 explicit generation/controller/shared exports and1664 actual public source hash
links. These counts describe that frozen snapshot, before issuance/collection additions.
See [shared regression evidence](evidence/affa17/shared-regression-verification.json).

Native frozen Stage now records an actual normal M3 staged observation and a separate
public issued annotation; its durable receipt is bound to both pre-Arm and pre-Release
worker revalidations. First started/probe causation follows that issued event. Six
source and six installed-wheel controls pass, including missing mirrors, malformed
actual ACKs and original generation1→2. Two intentionally deleted issuance mirrors
per phase remain explicit gaps. See [issuance audit](evidence/affa17/issuance-component-verification.json).
The subsequent issued-v1-full snapshot passes627 source/627 installed-wheel checks;
its audit verifies798 removed roots and1996 actual public source hash links. This
snapshot predates the retained-input export/broker-projection continuation below.

Confined declared-file collection now pins original source/destination directories,
rejects no-follow traversal/substitution/nonregular/oversized inputs, preserves
missing/error dispositions, verifies copied bytes and accepted public index ACKs,
and returns original outcomes on matching repeat.34 source and34 outside-source
wheel checks pass, including rejection of unbounded declaration iterables,
nonblocking collection/index/disposal conflicts,
optional-file lookup/copy races, the actual sixteen-MiB
total cap, mutation and closed-reader
artifact verification. See [collection audit](evidence/affa17/collection-current-verification.json).
This is a U8 component, not runtime collection or complete U7/U8. It needs quiescent
owned outputs after actual teardown; host/kernel stalls or adversarial simultaneous
renames are not converted into a containment guarantee by Python checks.

See [the current continuation handoff](evidence/affa17/continuation-scope-offline-20261019.md),
[the runtime closure design](coverage-runtime-closure.md) and the broader
[composition contract](affa-coverage-runtime-composition.md).

Original retained-input continuation: optional sealed persistence v3 declares bounded
single-use original-worker public artifacts and preserves default v1/v2 bytes. Intent
claims now retain their actual caller-supplied fields/ordinal; export uses those fields
and actual public M3, never reader reconstruction. The real worker writes/indexes only
the declared public file; parent receives the bounded accepted public index ACK. Original
cancelled starts remain closed. An inert broker projection preserves all admitted units,
future contexts, native epoch history, genuine issuance/Release brackets and actual old
wait/RETIRE/C1 terminal facts. Generation registry deletion, copied claims/ACKs, unknown
Stage and cancellation races cannot turn into fabricated known success.

The combined retained-v4 component has29 source/29 wheel checks,24 original roots
removed per phase and actual indexed public snapshots. The later eight source/eight
wheel projection delta separates local control/revocation flags from genuine native
cancellation ACKs. See [retained-input audit](evidence/affa17/retained-component-verification.json),
[projection delta](evidence/affa17/retained-projection-delta-verification.json),
[exact partial trace](evidence/affa17/retained-public-inputs-partial-traceability.json)
and [producer contract](affa-retained-input-export.md). The focused delta briefly
overlapped the running broader source suite; finding92/its observation records that
host contention. These are functional component observations, not isolated timing
measurements. The retained-v4-full snapshot finished690 source/690 wheel passes;
its audit verifies846 removed roots,202 public snapshots and2214 actual source
links. This frozen evidence predates the last field-name delta and coverage code.
See [retained regression audit](evidence/affa17/retained-regression-verification.json).

Admission-derived coverage now freezes all logical units/steps, admitted generation
contexts, fixed health slots and artifacts before execution. Pure assessment requires
the original externally pinned digest and always remains provisional. Independent
closed-reader verification checks actual retained fields, indexed bytes and the stored
report without rewriting evidence. Coverage-v5 passes41 source/41 installed checks;
its audit independently rereads four closed synthetic fixtures and two actual native
gap controls, with six removed original roots. Synthetic fixtures are not scientific
results. See [coverage audit](evidence/affa17/coverage-component-verification.json),
[33-endpoint partial trace](evidence/affa17/coverage-assessment-partial-traceability.json)
and [coverage contract](coverage-assessment.md).

The subsequent coverage-v5-full snapshot fails one missed-tick terminal assertion
with730 source passes; its wheel phase never ran. Its audit verifies424 removed roots,
102 retained public snapshots and1128 actual source links. A bounded isolated diagnostic
passes and does not explain that historical failure. See [failed regression audit](evidence/affa17/coverage-regression-failure-verification.json).

The successor adds original Stop brackets, separate original C1 termination/empty
facts and optional sealed v4 original validation before Init ACK. Compact metadata
regenerates the full admission templates/digest within the unchanged64-KiB helper
input bound. V1 has184 source passes/21 failures and no wheel phase; v2 has198 passes/
nine failures and no wheel phase. Both remain failed evidence. Preserve unknown
births and missing wait receipts separately from removed roots. V3 passes213/213,
audited with270 removed roots,140 public snapshots and1266 source links, but has
false U7 conflicts for real normal teardown proof references discovered afterward.

The corrected producer-v4 snapshot passes223 source/223 installed-wheel checks.
Its audit verifies274 removed roots,144 original helper wait receipts/retained
public snapshots,1266 actual source links and zero lost public fixture directories.
It binds the original admission identity AND its original digest, rejects changed
bytes/copies before RPC, retains actual Stop bounds, and checks genuine teardown
proofs against their paired original public M3 records. The actual control's input
integrity, run validation and Stop/cleanup rows now satisfy; missing dispositions,
collection/terminal and full closure keep overall coverage incomplete. The34-endpoint
producer trace retains all24/18 requirements/parents without closing any full clause.
See [producer audit](evidence/affa17/coverage-producers-v4-verification.json),
[producer trace](evidence/affa17/coverage-runtime-producers-partial-traceability.json),
[producer design](coverage-runtime-producers.md) and findings102–115.

The broader producer-v4-full2 snapshot finished772 source/772 wheel passes; its
audit verifies900 removed roots,254 public snapshots,48 explicit generation/
controller/coverage exports and2478 actual source links, with no lost public fixture
directories. See [broader audit](evidence/affa17/coverage-producers-regression-verification.json).
This is exact affected-snapshot evidence before the newer descriptor transport.
The initial full attempt's predicted771 collection guard failure remains retained.
No historical timing failure is erased or fully explained by passing controls.

The next runtime input now has optional sealed v5 admission for original public
broker artifact publication. Immutable data descriptors carry complete public
inventories beyond64KiB to the original worker; no productive ownership is adopted.
The worker validates the original declared scope and actual bytes, writes only its
pinned declared path, and verifies the accepted public index entry before ACK.
Matching repeats retain the original snapshot; malformed/lost ACK closes starts.
Default v1–v4 metadata and zero-rights behavior remain covered by verification.
See [ADR](ADR-ML3-EVIDENCE-0001.md) and [transport contract](public-evidence-transport.md).
Public-blob-v1 has260 source passes/three failures and no wheel phase; preserve it.
The corrected successor restores the original request-observation boundary for real
legacy and v5 revalidation failure controls. Public-blob-v2 passes265 source/265
installed-wheel checks, including42 new descriptor/publication controls. Its audit
verifies300 absent roots,166 original helper wait receipts/public snapshots,1308
actual source links and two actual indexed original broker artifacts, with no lost
public fixture directories.35 Python modules/four C resources match exact source.
See [transport audit](evidence/affa17/public-blob-v2-verification.json) and
[28-endpoint partial trace](evidence/affa17/original-public-blob-partial-traceability.json).
A new frozen814-case source/wheel regression is live (public-blob-v2-full); preserve
its inputs/installation and inspect actual process state before waiting/resuming.
No broader current result is claimed. Full runtime closure remains unfinished.

Remaining work includes verified producer/runtime integration, collection/result/
terminal ordering, blocked/never-claimed dispositions, full environment/bootstrap/M1
admission, all nine runtime cases and separate full-candidate review.24 software
requirements,18 unresolved source parents,30 verification pairs/90 endpoints and all
seven full P3 tasks remain binding. No acceptance, merge, factory/experiment run,
scientific result or canonical-note update is claimed.

## Durable start/probe evidence candidate (OUTCOMES12)

Every ProcessReadiness Query now requires a bounded acknowledgement from the
original isolated persistence worker before it can satisfy readiness. The worker
appends actual M3 records through public FileEvidenceJournal APIs, projects their
exact public hashes, appends accepted Argus annotations and calls flush_buffer.
The first observed running sample records one normal start outcome and a separate
probe observation, with started/probe/ready annotations. Pending exec records a
failed probe without invented start credit. Subsequent samples record health.
Combined-graph predecessor references come from the worker's own latest acknowledged
fresh probes. Original intents, known M3 history and mirrored events are rechecked.

The coordinator performs no storage I/O in this path. It accepts only its exact
current original observation/handle and validates the closed public reply against
claim, run/unit/generation/session, actions, clocks, source references, dependencies,
causation and global ordinals. LifecycleReceipt holds immutable public bytes and
never transfers execution authority or claims complete lifecycle coverage.
Storage failure, hung writes or lost acknowledgements close starts; retained normal
records remain factual partial evidence and C1 cleanup stays independent.

See ADR-ML3-OUTCOMES-0001.md, unit-specification-outcomes12.md,
outcomes-expected.json, review-outcomes12.md and evidence/outcomes12/.
The inherited private framing still caps a session at 128 requests; full scheduling
admission must budget requests and events. Automatic tick/health scheduling, missing-
observation failure/disposition records, normal stop/cleanup and reverse teardown,
restart/recovery, U7 dual coverage/U8, full bootstrap/admission/M1/runtime validation,
independent full review and acceptance remain open. No factory or experiment run.

## Process readiness and dependency candidate (PROVIDER11)

ProcessReadiness composes the original ReleaseOwner with its actual isolated
PersistenceClient, already staged CatalogLauncher handles and one ProbePolicy
per prepared unit. It supports only the exact catalog observe condition `running`:
process existence after observed exec, not application readiness. Plans declaring
other conditions reject. Legacy synchronous-storage owners are not admitted by
this facade; the existing primitive owner API remains compatible.

Call bind(launcher, full_handle) for each original staged resource, then
start(unit_id, original_boundary, original_gate, original_deadline). Prerequisites
come from ancestors in the combined XDL projection, including step dependencies.
Already released units are probed before new work. A private active-operation
guard re-probes all prerequisites before Arm and again immediately before Release;
all replies must match current generation/handle/session and remain fresh together.
Release is single-attempt and never itself ready. Up to three bounded actual
queries can satisfy the declared running condition. Failure/unknown/expiry cancels
further starts; original C1 remains responsible for actual teardown.

check_health(deadline, force=False) samples due units; next_health_deadline exposes
the earliest next cadence. The caller must drive sampling. No autonomous health/
tick scheduler, continuous health guarantee, application probe or full lifecycle
provider compatibility is established. Observations are immutable historical facts,
never transferable release authority. Exposed cached observations become non-ready
when the original latch closes. Bootstrap finding 14 now rejects a changed public
session alias before native dispatch.

See ADR-ML3-PROVIDER-0001.md, unit-specification-provider11.md, provider-expected.json,
review-provider11.md, verify-provider11.py and evidence/provider11/. Source/wheel
verification is component evidence only. Initial-supervisor admission and durable
bootstrap permits, exact environment/dependency admission, normal M3 outcomes,
autonomous scheduling, reverse teardown/restart/recovery, U7/U8, full M1/runtime
cases, independent full review and acceptance remain open. No factory run, main
merge, scientific result or canonical-note edit is implied.

## Supervised helper bootstrap candidate (BOOTSTRAP10)

The externally admitted runner supplies one genuine native bootstrap supervisor,
its private seqpacket socket, sealed input and three sealed helper images. Runtime
BootstrapSession methods create persistence, catalog-launcher and C1-bound gate
helpers through bounded native requests, without coordinator Popen. Each helper
is born frozen in an original, separately registered helper C1. Its actual clone
pidfd and original direct-parent wait authority are retained before a separate
one-use helper activation. Helper activation never thaws the workload C1.

Build native/bootstrap.c explicitly with C11 and OpenSSL 3 libcrypto; installation
and imports never build or execute it. BC10 binds original run/lifecycle/approval/
environment/supervisor pin and three helper image/argv0 pins. Native initialization
independently verifies image seals and hashes. seal_helper_image, input sealing,
initial native Popen, root registration, interpreter/site/library/environment
admission and exclusive original-parent wait ownership belong to the external
supervised admission path. Approval fields are not an authentication service.

BS10 birth/activation share one original deadline. Cancel bypasses the normal lock;
native expiry/owner loss/EOF prevents further helper insertion, kills exact helper
pidfds and refreezes retained workload C1 after helper exit. Original Python C1
separately terminates/observes/releases workload and helper trees. BootstrapChild
is an original native-issued capability, not a synthetic Popen; client and bootstrap
drain share one actual wait result. Legacy genuine-Popen clients remain supported.
Late genuine birth ACKs retain cleanup-only pidfds. An unrecoverable birth ACK stays
unresolved; no PID/name recovery or broad wait is attempted. External controller
supervision remains required across that gap and arbitrary kernel stalls.

Use BootstrapAdmission/encode_bootstrap only with externally approved, hash-bound
facts. The original C1 manager/latch/run/deadline/approval must match registration.
Pre-register a separate empty frozen helper BoundaryDescriptor before each request.
The fixed role adapters are persistence(config, helper, deadline), catalog(owner,
recipe, helper, deadline), and gate(owner, unit, helper, deadline, lease_ns=...).
Keep request deadlines and gate lease inside the current root lease. Renew before
expiry, within the original generation; renewal cannot revive an expired issuer.
After cancellation, drain typed clients and bootstrap with the original pidfds,
then independently verify C1 cleanup. Preserve unresolved wait/birth/freeze facts.

See ADR-ML3-BOOTSTRAP-0001.md, unit-specification-bootstrap10.md, bootstrap-expected.json,
the separate review, verify-bootstrap10.py and evidence/bootstrap10/. Launcher
finding 10 is corrected: recipe construction observes C1 and is not globally pure.
Full original-owner/guard-loss/M1, provider facade/readiness/dependency scheduling,
reverse lifecycle/recovery/normal outcomes, U7/U8, admission/source gates and all
nine runtime cases remain open. No readiness, acceptance or main merge is implied.

## Catalog launcher candidate (LAUNCHER9)

The successor composes real process-kind XDL/catalog actions, genuine M3/Argus
intent, a native born-frozen child and the original one-use Release gate. Python
retains C1 and an original issuing registry; the native helper copies and hashes
the selected regular ELF into a sealed image, pins the declared cwd and uses only
explicit argv/environment. LC09 authenticates each peer and exact recipe bytes,
sequence, deadline, retained cgroup FD and returned child pidfd. A full issued
OwnedResourceHandle is usable only through its live original registry.

Build the packaged catalog_launcher.c explicitly with OpenSSL 3 libcrypto:
`cc -std=c11 -O2 -Wall -Wextra -Werror catalog_launcher.c -lcrypto -o catalog-launcher`.
The optional RG06 build additionally requires `-DMAESTRO_BOUNDARY_ACK=1`; it returns
its actual cgroup FD during READY. Default RG06/LG05 behavior remains unchanged.
Source and binary pins, explicit artifact/environment/FD admission and trusted
helper bootstrap remain required; imports/installations never build/start helpers.

Before Release, the child stub and workload remain frozen. After Release, an exec
error pipe and original child pidfd distinguish pending exec, alive-after-pipe-EOF,
failed exec and reaped leader. These observations do not establish lifecycle
readiness or a successful normal outcome. Direct-child reap and C1 descendant
kill/empty/release remain separate factual checks. Cancel never waits for Stage's
lock. Closed or removed original boundaries cannot be used for late birth.

See ADR-ML3-LAUNCHER-0001.md, unit-specification-launcher9.md, review-launcher9.md
and evidence/launcher9/. verify-launcher9.py verifies installed source identity,
full/copy regressions and original helper/root receipts. Whole bootstrap/caller
bounds, dependency admission, provider facade/current-generation readiness,
reverse teardown, restart/recovery, full normal M3/evidence/coverage/collection,
independent full review and all nine runtime cases remain open. Full Lite phase 3
is partial; this candidate neither updates accepted main nor admits experiments.

## Native Release gate successor

`ML3-RELEASEGATE6-2026-10-18-v1` extends the packaged native source with an explicit
`-DMAESTRO_RELEASE_GATE=1` build variant. Default LG05 stays freeze-only. The RG06
variant uses a distinct 256-byte protocol and original creation epoch; it owns a
single ticket slot, validates original-parent credentials, exact scope, operation,
three acknowledgement digests, fixed TTL and private nonce, consumes once and
unfreezes the original retained cgroup control FD. Cancel/expiry advances the epoch,
burns the ticket and observes refreeze. Python `xverse.maestro.fence` is an inert
strict codec; importing it performs no bootstrap, clock read or execution.

The trusted original caller must verify actual durable M3, Argus public append+flush
and supervisor Stage acknowledgements. Hash fields cannot prove their truth. The
native gate does not create children, issue ordinary handles or gain C1. A Release
ACK means unfreeze was observed, not lifecycle readiness or a successful M3 outcome.
Actual kernel tests exercise both orderings, replay/TTL denial and a delayed gate
after C1-confirmed removal, including rejection through a retained old freeze FD.
Kernel I/O/scheduling stalls and guard/original-owner loss still require full outer
integration; the nine ML3 runtime cases and complete M1 proof remain pending.
See `ADR-ML3-RELEASEGATE-0001.md`, `unit-specification-releasegate6.md`,
`review-releasegate6.md` and `evidence/releasegate6/`. Pin source, build mode and
executable for any future admitted bootstrap; no runtime bootstrap facade is provided.

## Independent freeze-only lease guard successor

`ML3-LEASEGUARD5-2026-10-18-v1` continues linearly from containment commit
`de6be649b8a633b8f92972b249b03271d11810ea`. The wheel now carries native C11
source `xverse/maestro/native/lease_guard.c`. Build it explicitly with
`cc -std=c11 -O2 -Wall -Wextra -Werror lease_guard.c -o lease-guard`; importing
or installing the Python package does not compile or start it. There is no new
public Python bootstrap or lifecycle facade. The native entry and fixed 64-byte
protocol are defined in `unit-specification-leaseguard5.md`; build/hash-admit the
exact binary before any future owner bootstrap.

The independent process watches its original supervisor pidfd, a private
credential-checked Unix socket and a fixed monotonic lease. Expiry, supervisor
death, channel loss, malformed messages and Cancel request freeze of the exact
retained cgroup and observe the kernel frozen event. Renewal is bounded, scoped,
contiguous and cannot revive an expired lease. It never thaws, spawns workloads,
kills, deletes or obtains C1 cleanup authority. The original external holder
retains C1. Freeze alone is neither termination nor cleanup success.

This is a partial helper component, not the M1 Release/cancel fence. A stopped or
killed guard cannot enforce a lease, and kernel I/O can stall. Real tests expose
those limits explicitly; original-owner loss/guard-loss integration and stale
thaw prevention remain open. All process readiness flags stay false. See the
lease-guard ADR, unit specification, separate review and `evidence/leaseguard5/`.
The older sections below retain the exact earlier component context.

## U4 containment successor

`ML3-CONTAINMENT4-2026-10-18-v4` adds `xverse.maestro.prbc` in
`/home/jefferson/xverse-platform-worktrees/maestro-lite-containment-20261018`.
It creates fresh frozen Linux cgroup-v2 boundaries below an explicit exclusive parent,
retains original directory identity and private C1/reservation provenance, observes
membership independently of leader survival, and confirms exact kill/empty/removal.
Removal is verified through the retained identity's kernel controls and private name;
kernfs link counts are not the removal predicate. Original creation epochs survive
Cancel; lost/copied/forked registries cannot adopt a boundary. The CP-02 reservation
branch is read-only until verified empty removal and never substitutes for lost C1.

Supply explicit `BoundaryAdmission`, `BoundaryLimits(operation_seconds=...)` and
the original CancellationLatch. Admission facts are not authenticated operator approval.
An immutable original generation deadline (within the proposed D3 envelope) is distinct
from each operation's ≤5 s budget. Expiry or unknown observation retains unresolved
accounting. The backend supplies no child insertion, thaw, provider handle, M3 outcome
or workload callback. The closed create_frozen option schema accepts no keywords.
`ready_for_execution` stays false; only factual boundary cleanup may be reported.

Fixed C component tests exercise clone3 into a frozen boundary, leader death with a
live descendant, scoped force with an untouched sentinel, and rejected insertion
through a deleted retained FD. They are not an admitted launcher or full ML3 runtime
proof. Actual M1/AFFA fencing, supervisor-loss lease, bounded helper creation,
authenticated original-owner/run/store binding, broker/proxy/FixtureBoundaryOps,
U5 orchestration and evidence/coverage remain pending. See the containment ADR,
unit specification, review and `evidence/containment4/` for exact verification.

Stable increments are committed after verification under the author's 18 October
instruction. Prior PREP1/U2/U3 snapshots are committed on separate candidate branches;
their immutable manifests remain valid. A commit does not imply acceptance or main merge.

## U3 successor

Current overlay: `ML3-SUPERVISION3-2026-10-18-v3` in
`/home/jefferson/xverse-platform-worktrees/maestro-lite-supervision-20261018`.
The preceding PREP1/U2 worktrees and their hash-bound evidence remain unchanged.
`xverse.maestro.supervisor` supplies an original-parent Linux direct-child monitor:
strict finite host limits, irreversible independent cancellation, retained pidfd,
TERM/KILL escalation, nonblocking exact-child reaping and immutable observations.
It invokes no provider, tick, persistence, output-reader or Popen wait/poll callback.
Registration snapshots limits and freezes deadlines. Uncertain observation closes
the latch and retains identity; copied/forked holders cannot use the registry.

The original trusted owner must supply the actual Popen child before operation
dispatch and prevent concurrent reaping. Registration is not authenticated bootstrap
approval. The component creates no child and does not bound helper creation or its
own registration. It proves no descendant containment, C1, launcher fence or
supervisor-loss lease. A userspace deadline guard is not atomic kernel enforcement.
Every observation retains `cleanup_complete=False` and `ready_for_execution=False`;
exit/reaping is direct-worker evidence only. Cached uncertainty stays uncertainty.
See `ADR-ML3-SUPERVISION-0001.md`, `unit-specification-supervision3.md`,
`review-supervision3.md` and the distinct `evidence/supervision3/` bundle.

The sections below retain the earlier component context. Full lifecycle APIs,
U4 exact containment/M1/C1, independent helper supervision, U5 orchestration,
Argus coverage, restart, actual-runtime admission and acceptance remain pending.

## U2 successor

The successor at `/home/jefferson/xverse-platform-worktrees/maestro-lite-admission-20261018`
preserves the PREP1 worktree and adds `xverse.maestro.admission`. Use
`validate_permits` for pure exact-set validation and `PermitSession` only for
coordinator-side intent persistence through the actual M3 FileEvidenceJournal.
Every unit is validated before the session is returned; validity and source bindings
are checked again for all initial units at the first claim, then for the selected unit
at each subsequent use. Expiry of an already-used start permission does not widen or
invalidate a different unit's fresh permit. A persistence/read failure permanently
closes the original session's claims; fresh permit identities cannot adopt unresolved
prior intents in a selected scope. Generation zero is supported here; resource restart
requires confirmed-release evidence and the later coordinator implementation.

`PermitApproval` represents private input facts from the future trusted admission
owner. The module cannot authenticate human approval or confer authority from those
fields. A returned `IntentReceipt` confirms a journal operation and always retains
`ready_for_execution=False`; it is neither a permit, an AFFA ticket nor lifecycle success.
The module provides no provider or workload callback.

The additive M3 `claim_intent` checks history and persists one intent under the same
thread/process locks. A small identity marker in the existing private lock file binds
the journal, lock and parent plus the retained byte prefix and minimum sequence.
Journal loss, replacement, truncation, malformed history and uncertain marker publication
cannot silently reset consumed permits. The marker contains no permit database.
These are journal-scoped guarantees for cooperating claim users, not a security boundary
against an actor able to rewrite both private files. Existing ordinary M3 append/read and
controller APIs retain their behavior; legacy check-then-append clients gain no implicit
cross-process atomicity guarantee.

Recognized exclusions are `legacy-execution` and closed `operation:`, `provider:` and
`realization:` values described in the code/design. Unknown or conflicting exclusions
reject. Exact approval bindings cover run/unit/execution/generation, full prepared value,
M3 plan, provider artifact/environment, artifact digests and private permit content.
Approval-owner binding to the actual admitted run/store, file rehash at launch, bootstrap,
C1 containment, deadlines, Argus flush and ticket issuance remain pending G1/G3/G4/G5 work.

See `ADR-ML3-ADMISSION-0001.md`, `unit-specification-admission2.md`,
`review-admission2.md` and `evidence/admission2/`. Earlier PREP1 records copied below
remain historical evidence for their exact subject; current U2 evidence is separate.
Current revision 2 evidence is under `evidence/admission2/revision2/`; its predecessor
archive retains the exact earlier passing source, tests and review before the last repairs.

This increment implements the pure preparation and clock-validation parts of Phase 3.
It consumes an actual accepted `ExperimentPlanResult`, recompiles the immutable normalized
resources and compares the complete semantic plan, derives actual M3 catalog plans, and
projects a combined lifecycle graph. A rehashed caller modification is still rejected
when it does not reproduce the resources. No Scenario command becomes executable.

```python
from xverse.maestro import Limits, ProviderDescriptor, prepare

prepared = prepare(
    compiler_result,
    normalized_resources,
    provider_descriptors=provider_pins,
    limits=Limits(horizon_ticks=100),
)
assert prepared.ready_for_execution is False
```

The horizon in this example is an engineering input, not an AEB protocol threshold.
Provider descriptors require a closed provider ID/kind, explicit environment identity
and a SHA-256 artifact pin. Preparation never opens or verifies an executable artifact;
the pin is declared input identity, not artifact availability or provider admission.

## Implemented boundary

- One executable unit per bound component instance; unbound logical nodes remain containers.
- Exact catalog/provider/environment/artifact matching, duplicate and ambiguous selection rejection.
- Typed full resource/collection/element identities; source pointers resolve original XDL arrays.
- Start/Release/probe/readiness/completion joins, flow-owner readiness dependencies, explicit
  step completion dependencies, reverse teardown and impossible-window rejection.
- Deterministic, immutable preparation bytes and a SHA-256 digest. The increment uses its own
  `xverse.maestro.preparation.increment1` domain; it does not impersonate the complete v2
  lifecycle digest, whose admission, evidence obligations and helper pins are not implemented.
- Static eligible-step queries. Caller-supplied completed step IDs are scheduling input only;
  this function does not establish live readiness, health, ownership or permit validity.
- Integer-only simulation progression with zero/pauses, explicit horizon and rewind rejection;
  separate session-qualified host deadlines and UTC arithmetic. No host clock is read.

Finite proposed caps are 16 units, 128 steps, 128 distinct resource dependency pairs,
16,384 combined edges and a 10,000-tick horizon. The combined-edge cap bounds expansion of
phase and step dependencies; it is distinct from the resource-pair cap. Callers can narrow
these caps but cannot enlarge them. No measured timing or physical simulation fidelity is claimed.

## Pending boundary

There is no `start`, `stop`, `restart`, `reconcile`, `collect` or lifecycle-assessment API in
this increment. Actual process/simulated-provider orchestration, authenticated run/store
admission, descriptor/C1 containment, complete watchdogs, current-generation readiness, emergency
teardown, Argus lifecycle obligations and offline coverage remain pending. A graph node
named `ready` describes a required predecessor; its existence is not evidence of readiness.

All 24 ML-SR requirements remain in scope. ML-SR-001–004 and ML-SR-015 receive partial
code/test evidence; ML-SR-023 receives additive packaging/regression evidence only. No
REF-002 parent is semantically validated or closed. See the thesis continuation record
and `review-increment1.md`; the complete P3 task list stays open.

The historical rejected candidate's false-success facade and process helper are excluded.
No historic admission, expired queue window, provider pin or fixture grants execution authority.
Any future factory run must originate in `/home/jefferson/x-verse_fabric` through
`automation/factory_start.py` with fresh controls, external supervision and the current
Sol/high/no-fallback model policy. Direct implementation does not create a factory run.

## Verification and maintenance

Run feature tests from this owning checkout with current source imports:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/thesis_lite/maestro -q
python -m ruff check src/xverse/maestro tests/thesis_lite/maestro
```

For wheel verification use a fresh wheel build and an isolated environment with empty
PYTHONPATH, outside the checkout. Compare installed module bytes with source before
running copied tests. Hatchling force-includes `xverse` subpackages, so an editable
installation can retain a stale copy after source edits; it is insufficient by itself.
Existing XDL/M3/Argus consumers must pass from the exact source/wheel candidate.

Evidence logs and the final verification record identify actual checks and failures.
The initial full-suite environment failures and earlier review failures are retained.
No principal experiment, thesis result, PDF/DOCX generation, main update or external
publication occurs in this increment. Acceptance and merge require explicit author action.

## Original-owner integration candidate (OWNER7)

The isolated successor composes real generation-one PermitSession claims, actual
M3 public projection hashes, accepted Argus append_event/flush_buffer, original C1
frozen membership and credential-checked native RG06 Arm/Release. Default generation
zero admission remains compatible. Full XDL unit references remain logical data in
BoundaryDescriptor, never cgroup paths. See ADR-ML3-OWNER-0001.md,
unit-specification-owner7.md, review-owner7.md and evidence/owner7/.

The private claim retains its original host deadline; later calls cannot extend
that operation. The public evidence source hash covers the actual redacted M3
record using accepted canonical JSON bytes. Copied/terminal/replaced claims,
persistence failures, late acknowledgements and cancellation cannot register or
revive launch authority. Public ReleaseObservation always reports readiness false.

Trusted bootstrap still supplies the actual native child/socket/artifact pin and
exclusive wait ownership. Synchronous M3/Argus/kernel operations are not whole-call
bounded: disposable I/O workers and independently supervised bootstrap/launcher
remain required. No ordinary handles, full readiness, reverse lifecycle teardown,
restart/recovery, complete evidence assessment/collection or nine-case runtime
acceptance is supplied. Prior component evidence is preserved; main is unchanged.
Use verify-owner7.py with a newly built installed wheel, never stale editable imports.

## Single-process persistence candidate (PERSISTENCE8)

PersistenceClient and persistence_worker isolate the actual original M3/Argus owner
in one child process. ReleaseOwner.from_persistence keeps C1, frozen Stage and RG06
in the original supervisor. The RPC path performs no supervisor-side storage I/O.
Actual RegisterIntent and journal revalidation acknowledgements, original receipt
identity and the original deadline gate Release. Storage timeout/cancellation closes
starts and permits exact pidfd termination/reaping; it creates no replacement writer.
Healthy cancellation still permits bounded Abort. Abort records failure, not complete
lifecycle evidence. The local owner API remains available for regression comparison.

The private sealed input contains XDL declarations and original pins, not executable
code/callbacks. Its scope does not authenticate a helper executable/environment or
operator approval. Trusted helper creation, artifact/FD admission and exclusive wait
ownership remain bootstrap obligations. Parent-death signaling is a best-effort
creating-thread mechanism, not full owner-loss/kernel-stall proof. Kernel/scheduling
stalls can leave explicit unresolved retained ownership. The bounded RPC tests cover
interruptible storage stalls, not production real-time guarantees.

See ADR-ML3-PERSISTENCE-0001.md, unit-specification-persistence8.md, separate review
and evidence/persistence8/. verify-persistence8.py checks the exact installed wheel,
full platform suite, copied consumers, all recorded helper/peer groups and partial
trace. Full bootstrap/launcher, ordinary handles/readiness, reverse lifecycle teardown,
restart/recovery, complete U7/U8 and the nine actual-runtime cases remain open.

BOOTSTRAP10 v3 requires own-process KCMP_FILE for exact pidfd open-file-description
checks. The registered root/child keeps a distinct private original duplicate; all
signals/waits/duplicates use it. Inode equality is not a pidfd identity check on
Linux 6.8. Comparison denial/unsupported hosts reject admission without fallback.
This bundle tests x86-64; other architecture/environment admission remains external.

Reverse unit teardown increment 13 (partial, not accepted):
[ADR](ADR-ML3-TEARDOWN-0001.md), [unit contract](unit-specification-teardown13.md),
[tasks](tasks-teardown13.md), [read-only findings](review-teardown13.md), and
[evidence](evidence/teardown13/). Original C1 termination now retains an observed
empty frozen boundary for a separate original release. ReverseTeardown serializes
with the original owner/facade, closes starts locally, and records normal stop and
cleanup intent/outcome through the original isolated M3/Argus writer. Actual native
leader reaping, C1 empty/release facts and missing normal evidence remain separate.
Storage/identity faults use original cleanup-only authority under the original end;
manager conflicts report unknown facts without blocking. Same-controller matching
stop calls return retained facts. Full helper/global cancellation, automatic health/
tick scheduling, recovery, coverage/collection and admission/runtime remain pending.
All seven full P3 tasks, 24 ML-SR, 18 allocation-only source parents, 30 scenario
pairs/90 declared endpoints and nine full runtime cases remain open. No factory
run, main merge, canonical-note edit, scientific protocol or result change.


Finite lifecycle dispatcher increment 14 (partial, not accepted):
[ADR](ADR-ML3-SCHEDULER-0001.md), [unit contract](unit-specification-scheduler14.md),
[tasks](tasks-scheduler14.md), [read-only findings](review-scheduler14.md), and
[evidence](evidence/scheduler14/). ScheduleAdmission independently derives finite
host health, call and event reserves on both sides of the original persistence
channel. FiniteDispatcher executes declared prepare/start/observe/stop/cleanup,
windows, durations and combined dependencies over already-staged original units.
Its finite supervised tick source allows pauses while original host health and
root/gate leases continue. Actual public M3/Argus phase and terminal dispositions
remain separate from readiness and cleanup; unusable storage leaves explicit gaps.
A shortened stop window retains an emergency share of that same original window.

This adds no authenticated bootstrap/environment admission, external simulator
adapter, restart/controller recovery, full helper closure or global epoch proof.
Execution success never sets lifecycle_complete or ready_for_execution. U7/U8,
all seven full P3 tasks, all 24 ML-SR and 18 unvalidated source parents, 30 pairs/
90 declared endpoints, nine full runtime cases and independent review/acceptance
remain binding. Phases 1–2 accepted, phase 3 partial, phases 4–9 pending. No main
merge, canonical-note edit, factory run, scientific protocol or empirical change.
Earlier working-state/working-traceability/continuation receipts under scheduler14
are historical; verification.json and the committed thesis checkpoint supersede them.


Original run closure increment 15 (partial, not accepted):
[ADR](ADR-ML3-CLOSURE-0001.md), [unit contract](unit-specification-closure15.md),
[tasks](tasks-closure15.md), [read-only findings](review-closure15.md), and
[evidence](evidence/closure15/). Bootstrap retains original birth/client inventory
before helper acknowledgement and after adapter construction. RunClosure closes
issued units in original reverse dependency order, drains original helpers/root and
releases all issued C1 boundaries within distinct shares of the original caller end.
Normal conflicts reject; independent cancel bypasses locks. Unknown births, invalid
ordinary adapters and missing direct-child waits stay explicit. Local control FDs
remain retained for caller disposal; matching repeats return original facts.

The original storage worker can make one bounded incomplete-closure attempt using
public flush/abort/reader APIs. Before/after writer state, abort_usability established
before abort, after_usability, actual durable manifest hash/recorded/assessed status,
and missing RPC observations are separate. Flush failure forbids abort; abort errors
never infer failed state or stream usability. Legacy abort is preserved; this new
one-call path consumes the existing terminal abort reserve. No finalize, reopen,
complete-lifecycle coverage or new launch authority. Initial bootstrap/environment
admission, full global M1, restart/recovery, U7/U8, independent review/acceptance and
phases 4–9 remain open. No factory run, main, canonical-note or scientific change.


Surviving original-issuer reconciliation (increment16, partial candidate) is specified
in ADR-ML3-RECOVERY-0001.md and unit-specification-recovery16.md. IssuerRecovery
revalidates consumed intents, exact durable handle/mirror records and the actual
original native issuers before reconstructing an observation/cleanup view. Previous
positive readiness is retired; new health queries are mandatory. Claim/Stage/Release
remain irreversibly closed. Failed checks invoke original bounded run closure with
unknown facts preserved. This same-supervisor primitive does not supply process
restart, new-host-session recovery, global M1, U7/U8 or runtime acceptance. All full
P3 requirements and downstream phases remain binding.

Finding8 integration repair: explicit scheduled observations now probe exactly their
admitted unit under its operation end. Periodic health still scans all released
units under the admitted scan budget. Original readiness/normal-record checks, all
operation/fixture/lease limits and conservative event/request bounds are preserved.


Current increment17 continuation: [runtime collection contract](runtime-collection.md)
and [handoff](evidence/affa17/continuation-runtime-collection-20261019.md).
Original worker admission and incremental collection/index primitives are verified
in distinct224/224 and63/63 source/wheel snapshots. Full runtime collection/terminal/
coverage closure remains unfinished. The broader813/1 failure is retained; historical
collection-v6 archive loss is disclosed in
[evidence recovery](evidence/affa17/collection-v6-evidence-recovery-20261019.json).
No stable increment17, full P3 completion, acceptance or integration is claimed.


Latest terminal-service continuation (2026-10-19): actual runtime collection and
original cleanup-only BS17 service are implemented as partial full17 components.
The latest affected boundary snapshot passes37 source/37 installed-wheel checks;
its [audit](evidence/affa17/terminal-service-boundary-20261019d/verification.json)
checks52 absent test roots,50 original broker waits and518 actual source links.
Historical broader b80/80 and test-only c14/14 snapshots retain their exact scope.
[Finding135](review-affa17.md) defers the earlier unrelated teardown regression
from immediate repair at the author's direction; it remains a stable17/release gate.
See the [new handoff](evidence/affa17/continuation-terminal-service-20261019.md)
and [lazy issuance design](lazy-issuance-runtime.md) for the next complete-runtime
work. No stable17 commit, full P3/M1 completion, acceptance or main integration.


Latest lazy/fenced-normal continuation (2026-10-19): v6 now creates real start
claims/Stage only at an eligible scheduled start, independently checks this in the
original worker, retains generation0 logical bookkeeping and unknown acknowledgements,
and collects before terminal records. Original native cancellation/root terminal
scope precedes implicit normal teardown; cleanup past the old productive lease
retains actual waits/normal records without renewing start authority. Component
checks15/15 and identical-source affected compatibility88/88 pass source/wheel.
See the [current audit](evidence/affa17/fenced-teardown-regression-20261019b/verification.json),
[partial trace](evidence/affa17/fenced-normal-teardown-partial-traceability.json) and
[new handoff](evidence/affa17/continuation-lazy-fenced-normal-20261019.md).
Previous failed paused/horizon/timing scopes remain open. Next is
[terminal report/writer closure](terminal-report-closure-runtime.md), followed by
independent original closed-reader verification and the remaining full17 gates.
No stable17 commit, full P3/M1 completion, acceptance or main integration is claimed.

Latest report-closure preparation (2026-10-19): runtime_verification.py independently
checks externally pinned original collection inputs against actual accepted closed
records, original context/final broker and confined file/index bytes. terminal_writer.py
records public finalize/abort failure stages and requires a fresh successful flush
before aborting a writer still marked open. Synthetic actual-Argus component checks
pass72 source/72 installed wheel; no native helper was started in this scope. See
[exact evidence](evidence/affa17/terminal-writer-20261019b/verification.json) and
[continuation](evidence/affa17/continuation-terminal-writer-20261019.md).
Original report protocol, automatic dispatcher closure and full runtime validation
remain unfinished. Earlier88/88 teardown evidence applies to its preceding snapshot;
these overlapping scopes are not a combined unique-test count. Increment17 remains
uncommitted, unaccepted and unmerged.

Current report-runtime integration (2026-10-19): v6 FiniteDispatcher now publishes
actual final broker/retained inputs and a provisional report in the original worker,
then binds writer close to the exact retained report receipt under one fixed end.
Required coverage, uncertain applicability, optional corruption, collection and
normal terminal success independently gate finalize. Matching repeated finish_run
returns its original immutable outcome; missing/changed ACK retains unknown state.
Scheduler productive step records now retain original handle/source/dependency proof.

The earlier terminal-runtime-b candidate had95 passed/1 persistence timeout in source checks and
96/96 in the first installed-wheel phase against identical frozen code. The timeout
occurred before second-unit ready and report attempt; its cause remains unknown.
See [source evidence](evidence/affa17/terminal-runtime-20261019b/verification.json),
[wheel evidence](evidence/affa17/terminal-runtime-wheel-20261019c/verification.json)
and [current handoff](evidence/affa17/continuation-terminal-runtime-20261019.md).
The failed-writer close guard was subsequently repaired and tested as recorded below.
No stable17 commit, full lifecycle/M1 validation, acceptance or merge is claimed.

Non-open writer and helper continuation (2026-10-19): authenticated terminal close
can now observe a failed/closed original writer without another writer operation;
parent validation retains actual state and missing report ACK separately. Fixed
owned helper controls pass100/100 source/installed-wheel in the preceding exact
[snapshot](evidence/affa17/terminal-nonopen-20261019c/verification.json). RunClosure
now retains original terminal_reports instead of replaying abort-only closure, with
legacy writers separate and all original helper/root/C1 waits preserved.

The earlier helper-e expanded116-case scope had114 pass/2 fail source and109 pass/7 fail wheel;
see [its audit](evidence/affa17/terminal-helper-20261019e/verification.json).
New helper controls passed three source/one wheel cases; other failures included fixed
persistence timeouts and a concrete active/terminal evidence clock mismatch. Factual
run-terminal records within reserved terminal time were rejected by the generic active
end check. Original active/operation deadlines have not been widened. See the
[clock review](evidence/affa17/terminal-clock-scope-review.json) and
[handoff](evidence/affa17/continuation-terminal-nonopen-helper-20261019.md).
Increment17 remains uncommitted; full lifecycle/M1/regression/acceptance/merge remain open.

Current scoped/offline snapshot (2026-10-19): source226/0 and installed-wheel223/3 of226 each
(passed/failed), original tool18492 terminal1.
RuntimeEvidenceScope binds the original collection/generation context before I/O,
keeps productive evidence inside active time and permits bounded terminal facts.
The dispatcher retains a primary execution error through secondary cleanup failure.
collection_evidence.py separates inert decoders from runtime transport; original
runtime APIs preserve their exception identity. Fresh-process ordinary/after-active
closed evidence controls deny U3–U5 imports and verify unchanged original bytes.
Both source and wheel execute all selected tests once; failures remain retained.
See [current audit](evidence/affa17/offline-boundary-20261019d/verification.json),
[partial trace](evidence/affa17/terminal-scope-offline-partial-traceability.json) and
[current handoff](evidence/affa17/continuation-scope-offline-20261019.md).
Full increment17, nine complete runtime cases, full M1/environment/global regression,
independent complete-candidate review and acceptance/main integration remain open.

Convergence checkpoint: freeze the current snapshot and follow
[evidence/affa17/increment17-closure-map-20261019.md](evidence/affa17/increment17-closure-map-20261019.md).
The next step is a targeted review of ten original RPCs sharing a start-effect end,
with seconds still left in active time; paused-tick timeout requires separate diagnosis.
No broad unchanged-code rerun or additional incidental scope is planned. Full17 scope remains intact.

Transitive active-run continuation (2026-10-19, partial17): explicit cohorts now
compose reverse normal quiescence and forward fresh generations through the
original coordinator/writer. Four cohort modes pass in source and installed wheel;
six original-input closed recomputations and byte-identical public roots retained.
Latest affected scope source58/59,wheel59/59 still fails the old4.8s source leaf
teardown (finding222); no stable17 claim or commit. See
evidence/affa17/continuation-active-transitive-20261019.md and
evidence/affa17/active-transitive-partial-traceability.json. Productive controller
recovery and the full24/18/30/90/nine-case/seven-task scope remain open.

Active controller recovery continuation (2026-10-19, partial17): explicit queued
replacement now retains the original mutation coordinator, handles and writer
across startup/running/stopped/released/generation2 states and a real heartbeat
race.94 primary plus42 affected standalone checks pass in each phase;18 closed
original-input recomputations retained. See
evidence/affa17/continuation-active-controller-recovery-20261019.md and
evidence/affa17/active-controller-recovery-verified-scope-traceability.json.

Active-control deadlines/cancellation (2026-10-19, partial17): native controls
now verify past/foreign/beyond-active admission rejection, actual queued expiry
and external cancellation before drain, with unchanged authority/resource
frontiers and unspent future contexts. A queued restart cancelled before any
effect now reports rejected rather than post-mutation failed. Source13/13 and
wheel13/13;20 original cleanup contexts and16 normal closed roots audited. See
evidence/affa17/active-control-deadlines-20261019c/verification.json and
evidence/affa17/active-control-deadlines-partial-traceability.json. Complete
failure/race/runtime coverage and stable17 remain open; old135/222 are not waived.

Affected restart compatibility uses the same immutable package:source8/9,
wheel9/9; all transitive modes pass. The source v3 leaf repeats222 after successful
restart, so the whole affected scope is21/22 source and22/22 wheel. See
evidence/affa17/active-control-deadlines-verified-scope.json and
evidence/affa17/active-control-deadlines-verified-scope-traceability.json.

CAPA clarification and initial explicit register: see [capa.md](capa.md).
Three selected records distinguish local correction/prevention evidence from
independent cause confirmation and effectiveness.135/222 remain UNRESOLVED;
238 is FIX_CANDIDATE. This is observation-only work-product tracking, not an
implemented CRE engine or a CAPA extension already delivered by capability025.

Owned native writer-stream fixture now verifies actual role3 loader/sealed-image
identity, role5 isolation, preconditioned internal-flush failure and real successful
close followed by EIO:4/4 source and4/4 installed wheel. Production sources remain
unchanged. Eight original native contexts/440 M3 links and two normal closed roots
are audited. The original successful-append W02 mechanism failed and is preserved;
isolated healthy-prefix W02 and full W/TR03/TR06/M1/full17 remain open. See
evidence/affa17/native-writer-stream-partial-traceability.json and the continuation
record. CAPA246/247 retain both fixture defects as local fix candidates, not closed
or effective records;135/222 remain unresolved.
These bounded results do not close full17 or waive old timing findings135/222.

Selected composed authority continuation: nine original v6 Stage/Release/Cancel
and issuance/helper-loss controls pass9/9 source and9/9 installed-wheel. An active
unrelated heartbeat survives all18 contexts;14 retain unknown workload waits.
No production source changes. See [controls](composed-authority-interruptions.md),
[trace](evidence/affa17/composed-authority-partial-traceability-v2.json), and
[handoff](evidence/affa17/continuation-composed-authority-20261019.md). Original
failed controls remain retained. Full runtime cases/M1/stable17 and135/222 remain
open; the CAPA successor validates8 records/36 bindings without effectiveness.

Selected intent/termination continuation: public start-intent append/flush-loss
and live-leader+descendant STOP controls pass6/6 source and6/6 wheel, including
the disabled observer. Original b51741/audit9db731 retain12 contexts,298 M3 links,
2 normal closed roots and6 genuine unknown workload waits. Production unchanged.
See [controls](composed-intent-termination.md), [trace](evidence/affa17/composed-intent-termination-partial-traceability.json)
and [handoff](evidence/affa17/continuation-intent-termination-20261019.md).
Full CP/matrix/M1/stable17 and CAPA135/222 remain open.

Original issuer-loss repair: cancellation now uses the original pinned cleanup
context despite ordinary registry-reference loss; ordinary adoption still rejects.
Closure retains original inventory/unknown waits and completes exact root/C1
cleanup.54/54 source and54/54 wheel affected checks pass; see
[repair](issuer-loss-cleanup.md), [trace](evidence/affa17/issuer-loss-partial-traceability.json)
and [handoff](evidence/affa17/continuation-issuer-loss-20261019.md). Full17 and135/222
remain open. The new immutable issuer-loss-c wheel contains this two-file repair;
older trace deltas retain their original source hashes.

Complete-entry continuation: the read-only joint runtime preflight is implemented,
binding existing v6/BS17 inputs and external approval/facility/design/helper pins.
40/40 new and146/146 total checks pass per source/wheel phase. Unit attestations
are synthetic/inert; zero actual M1 admissions or runtime helpers are claimed.
All76 prior sources remain unchanged. See [entry work](runtime-entry.md),
[trace](evidence/affa17/runtime-admission-partial-traceability.json) and
[handoff](evidence/affa17/continuation-runtime-admission-20261019.md). Next implement
the original launcher/run registry and bounded entry. Full17/135/222 remain open.

Original startup ownership is now implemented internally: sealed live-byte checks,
single retained descriptor execution, bounded original reservation, independent
cancellation and exact pidfd wait ownership.74 selected checks pass per source/
wheel phase across two frozen runs with identical78 production files. Unknown
births retain unknown runtime waits despite separate external owned cleanup.
See [launcher](bootstrap-launcher.md) and its linked audits/partial trace. The
collector-name gap and correction are retained as CAPA269;13 records/64 bindings
validate, with no effectiveness closure. Full public entry/facility/M1, full17
and135/222 remain open.

Actual pinned evidence-file/current-host checks and a private whole-lifecycle
composer now advance runtime entry. It returns original dispatch/collection/
terminal/RunClosure results with separate physical cleanup and evidence facts.
Current selected verification is19 evidence/window checks from b plus67 affected
entry/adjacent checks from c per source/wheel phase on identical80 production
files. Original window/counterexample/oracle failures remain retained. See
[composition](runtime-entry-composition.md) and
[trace](evidence/affa17/runtime-entry-partial-traceability.json). CAPA validates
16 records/76 bindings without effectiveness closure. No synthetic file vector
authorizes execution; complete public admission/control/M1/full17/135/222 remain open.

Private run/control registry and startup original-pin repair: see
[runtime-controls.md](runtime-controls.md) and
[partial trace](evidence/affa17/runtime-controls-partial-traceability.json).
Startup14/14 checks pass per phase withzero fallback; all79 other production
sources remain unchanged. Registry/control implementation has retained wheel
recovery and source nominal failures286/287,not resolved by the instrumented
positive probes. CAPA20/88 validates;135/222/286/287 and full17 remain open.
