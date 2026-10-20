"""Publish local partial engineering handoff only after terminal verification audit."""
from pathlib import Path
import hashlib
import json

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[4]
DOC=ROOT/'docs/engineering/maestro-lite'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
name='offline-boundary-20261019d'
out=BASE/name
v=read(out/'verification.json');r=read(out/'running.json')
assert v['observed_original_tool_session']==18492 and v['observed_tool_terminal_exit'] in (0,1)
manifest=read(out/'frozen-inputs.json')
assert all(sha(ROOT/n)==h for n,h in manifest.items())
counts={p['phase']:p for p in v['phases']}
assert set(counts)=={'source','wheel'}
source=counts['source'];wheel=counts['wheel']
phrase=f"source{source['passed']}/{source['failed']} and installed-wheel{wheel['passed']}/{wheel['failed']} of226 each"
summary=f'''
Current scoped/offline snapshot (2026-10-19): {phrase}
(passed/failed), original tool18492 terminal{v['observed_tool_terminal_exit']}.
RuntimeEvidenceScope binds the original collection/generation context before I/O,
keeps productive evidence inside active time and permits bounded terminal facts.
The dispatcher retains a primary execution error through secondary cleanup failure.
collection_evidence.py separates inert decoders from runtime transport; original
runtime APIs preserve their exception identity. Fresh-process ordinary/after-active
closed evidence controls deny U3–U5 imports and verify unchanged original bytes.
Both source and wheel execute all selected tests once; failures remain retained.
See [current audit](evidence/affa17/{name}/verification.json),
[partial trace](evidence/affa17/terminal-scope-offline-partial-traceability.json) and
[current handoff](evidence/affa17/continuation-scope-offline-20261019.md).
Full increment17, nine complete runtime cases, full M1/environment/global regression,
independent complete-candidate review and acceptance/main integration remain open.
'''
with (DOC/'README.md').open('a') as stream:stream.write(summary)
p=DOC/'README.md'
p.write_text(p.read_text().replace('See [the current continuation handoff](evidence/affa17/continuation-public-evidence-20261019.md)',
 'See [the current continuation handoff](evidence/affa17/continuation-scope-offline-20261019.md)'))
with (DOC/'tasks-affa17.md').open('a') as stream:stream.write(summary.replace('[current audit](evidence/affa17/','[audit](evidence/affa17/'))
with (DOC/'unit-specification-affa17.md').open('a') as stream:
 stream.write(f'\nExact successor verification: {phrase}; original tool18492 terminal{v["observed_tool_terminal_exit"]}.\n')
 stream.write(f'Audit verifies{len(v["original_broker_waits"])} original broker waits,{len(v["original_roots_absent"])} absent roots,\n{v["actual_source_links"]} M3 links and{len(v["externally_pinned_closed_recomputations"])} original external pin recomputations.\n')
 stream.write('No requirement/full runtime case is closed by this component result. See the current partial trace and handoff.\n')
with (DOC/'canonical-note-update-proposal-affa17.md').open('a') as stream:
 stream.write(f'''
Proposed status: ENGINEERING OBSERVATION / PARTIAL IMPLEMENTATION / FULL VALIDATION PENDING.
Do not apply automatically. Proposed text: "The isolated Maestro candidate now
assesses terminal evidence using original independently pinned collection/generation
inputs while preserving productive and operation deadlines. It retains the first
execution error through secondary cleanup failure. Shared inert broker/collection
codecs permit fresh-process offline verification without U3–U5 runtime imports and
preserve existing runtime error identities. The exact expanded scope reports
{phrase} (passed/failed). Full increment17, M1/global/runtime/regression,
independent review and acceptance remain open. These are engineering observations,
not principal AEB results or X-Verse fitness-for-purpose acceptance."
Affected artifacts: evidence_scope.py,coverage.py,dispatcher.py,collection_evidence.py,
public_blobs.py,collection_runtime.py,runtime_verification.py,test_evidence_scope.py,
test_dispatch_diagnostics.py,test_offline_boundary.py and the exact {name} evidence,
terminal-scope-offline-partial-traceability.json and continuation-scope-offline handoff.
The canonical note and scientific protocol were not changed.
''')
failures=[]
for phase in ('source','wheel'):
 failures.extend(phase+': '+line for line in (out/(phase+'.log')).read_text().splitlines() if line.startswith('FAILED '))
with (DOC/'review-affa17.md').open('a') as stream:
 stream.write(f'\n184. Exact expanded scope finishes {phrase}, original tool18492\n     terminal{v["observed_tool_terminal_exit"]}. Retain all failure logs and original bytes; no successful\n     component control waives a failure or closes full17. Current audit verifies\n     {len(v["original_broker_waits"])} original broker waits/{len(v["original_roots_absent"])} absent roots,{v["actual_source_links"]} actual M3 links,\n     {len(v["externally_pinned_closed_recomputations"])} original runtime pins and{len(v["original_terminal_outcomes"])} retained terminal outcomes.\n')
 stream.write('     Four actual fresh-process checks (two per phase) preserve original bytes and\n     deny runtime imports. Separate runtime exception-identity tests are included.\n     Full candidate independent review, M1 and nine complete runtime cases remain open.\n')
text=f'''# Maestro continuation — scoped terminal evidence, primary errors and inert offline verification

2026-10-19. Goal ACTIVE. Previous status-only turn: NO PROGRESS. This implementation
turn: PROGRESS, with source repairs, red controls, expanded source/wheel execution,
read-only audits and traceability. Preserve the full nine-phase dissertation Lite
objective. Accepted milestones remain2/9 (~22%);16 stable Maestro increments committed.
Complete selected increment17 remains unfinished/uncommitted. Commit every completed
stable increment; do not substitute a smaller checkpoint. No acceptance/main merge,
publication, canonical-note change, scientific campaign, agent or factory run occurred.

## Authority and freshness

Thesis: /home/jefferson/distributed_safety_critical_thesis
branch agent/synchronize-thesis-obsidian-notes, HEAD28f8f74ff9a49f247f41921ed81863b18cd56626,
upstream origin/agent/synchronize-thesis-obsidian-notes at fe58918f9eaf2a6f39cdc9c93cfd4ce615ec84bf.
Fresh fetch --prune origin succeeded this turn (original session45867 terminal0).
No incoming canonical-note commit; no pull. The COMPLETE canonical note was read in
bounded chunks, including the output-truncated Note21 overlap. SHA256 remains
01fcce48696c30d8e8cf46fa60fcf28eae9f45c19a8885df86528832e18b4abb.
Preserve author's dirty AGENTS/note and unrelated untracked files. Proposal appended
only; no canonical-note mutation. RF-2026-08-30-v6/AEB-EXPERIMENT-2026-08-30-v2 remain:
one heterogeneous AEB,frozen ML,competent paired fixed/MLOC,separate gate/transition
ablations,no oracle leakage,MRC availability credit,invented thresholds or results.

Candidate: {ROOT}
branch candidate/maestro-lite-affa17-20261018, last stable HEAD16
46e0ebfd332dd833322d764191a7cfe1e008bec1. Owner /home/jefferson/xverse-platform main
rechecked c2997c0f810d117cf45b2e34a4011b3ba7219494; preserve its unrelated untracked files.
Both AGENTS and owning constitution/Spec Kit instructions apply. No extensions file
exists at owner root. Capability024 / ML-DESIGN-2026-10-03-v2 external inputs govern,
not main020. Read coverage-runtime-closure-inputs.json and retained original contracts.
No thesis prose/LaTeX changed; academic-writing/build workflow not triggered.
New factory runs MUST use /home/jefferson/x-verse_fabric/automation/factory_start.py
and keep operations there; these owned component checks are not factory/scientific runs.

## Implemented changes and evidence boundaries

Read continuation-terminal-nonopen-helper-20261019.md and earlier handoffs for original
v6 lazy issuance, native terminal fence, collection, WorkerTerminal report/receipt-bound
close, parent finish_run cache, original helper closure and non-open writer controls.
They remain historical context, not verification of this successor.

Finding177 RuntimeEvidenceScope is now implemented. Original canonical CollectionPlan
and generation are bound to an external joint runtime digest BEFORE evidence I/O.
Outer terminal evidence ceiling is generation minus original drain; this grants no
operational deadline extension. Productive intent/issued/start/probe/ready/health stay
active-bounded. Terminal stop/cleanup/collect/disposition may use terminal scope; actual
late teardown intent requires original issued handle and M3 stop/cleanup intent proof.
Health windows remain active-bounded. Scoped report inputDigests.runtimeAdmission is
checked identically in provisional/closed recomputation. Standalone coverage keeps
its old active-bound default. Sixteen synthetic actual-Argus boundary cases pass in
each expanded phase; these are not native performance or scientific results.

Finding179: cleanup exception no longer overwrites a normalized primary execution
failure. Conservative incomplete TeardownResult remains; execution/readiness/completion
are not promoted. New actual native controls SIGSTOP original storage/controller by
pidfd, run original cleanup once, then lose its returned ACK in the owned caller.
Original timeout survives, while actual cleanup receipts remain separate. These are
partial failure controls, not complete TR06 coverage.

Finding181: runtime_verification previously imported collection_runtime/public_blobs
and transitively persistence/owner/prbc/fence/child/supervisor. Shared inert codec
functions now live in collection_evidence.py; all six ASTs match original primary-b
except the broker's pure BrokerDataError. Runtime adapters preserve PersistenceError
identity/text; shared functions remain callable through old runtime module paths.
Offline verifier depends on inert codecs. Fresh subprocesses deny U3–U5/runtime
imports and independently verify ordinary/after-active synthetic closed evidence;
actual evidence SHA maps stay unchanged. Runtime exception-identity cases preserve
existing API failures. Limited separate source review183 found no new defect; the
required independent complete-candidate review remains OPEN.

## Exact verification ledger

terminal-scope-20261019a: source130/2,wheel127/5 of132; original63614 terminal1.
Audit94821 terminal0:88 waits/absent roots,2470 M3 links,32 pins,23 terminal outcomes.
All16 scope boundaries pass both.14 absent unreferenced journals plus TWO actual
unmirrored M3 records remain. mirror-profile-20261019a measures inert accepted OPEN
record replay only, excluding original claim checks/live fsync/scheduling; NOT proof
of native timeout cause. No cache or deadline relaxation was introduced.

terminal-primary-red-20261019a:0/2 source and0/2 wheel,77622 terminal1;
audit27fd6f terminal0. Correct original storage/controller failure was overwritten
by cleanup-incomplete. Pre-repair bytes retained.
terminal-primary-20261019b: source134/0,wheel130/4;22500 terminal1.
Audit subcommand exits0 before current driver in18492:92 waits/absent roots,2494
M3 links,32 pins,25 terminal outcomes. Four actual diagnostic controls pass.18 raw
journal gaps have no refs; no actual missing mirror in this snapshot. This DOES NOT
erase older gaps/failures. scope-primary-gap-review-20261019.json distinguishes them.

offline-boundary-red-20261019c:0/2 source and0/2 wheel,5553 terminal1;
audit41d69d terminal0. Parent synthetic closed verification succeeds; fresh child
fails exactly on forbidden collection_runtime import. Original bytes unchanged.

CURRENT {name}: {phrase} (passed/failed).
Both phases execute ONCE; original18492 terminal{v['observed_tool_terminal_exit']}. All226 selected cases retained;
no deadline/assertion weakened or failing case skipped. Audit verifies{len(v['original_broker_waits'])} broker waits,
{len(v['original_roots_absent'])} absent roots,{v['actual_source_links']} actual M3 links,{len(v['externally_pinned_closed_recomputations'])} original runtime pin checks and
{len(v['original_terminal_outcomes'])} terminal outcomes. Raw reader gaps remain in verification.json; inspect actual
source refs before classifying them. Native/owned tests run serially. All known suite
handles are now terminal. New offline-boundary/diagnostic controls do not establish
full platform regression, M1 or complete runtime acceptance.

Current failures:
{chr(10).join(failures) or '(none in this selected scope; full17 gates remain open)'}

Matching interpreter: {r['verification_python']}
Frozen source: {r['frozen_source_root']}
Outside-source consumer: {r['consumer']}
Source/test manifest SHA256: {v['source_manifest_sha256']}
Installed identity SHA256: {v['installed_identity_sha256']}
Wheel SHA256: {v['wheel_sha256']}
All42 Python modules/four C resources match (46 installed files). Current source/tests
match the frozen manifest. Runtime/build environment JSON files retain actual versions;
Python3.13.13,pytest9.0.3,jsonschema4.26.0,referencing0.37.0,ruamel.yaml0.19.1,
build1.6.1,hatchling1.32.4; observed Linux component environment is NOT full M1 admission.

## Next concrete work / gates

Continue TR03/TR06 ORIGINAL native writer-failure/storage/root-loss and generation/
controller controls under terminal-report-closure-runtime.md. W-01..W-07 expectations
come from original writer-closure-tables.json. Public method fault controls must state
the exact injected operation and observed state; never infer an internal stream-close/
recovery/publication stage, inspect/replace the private Argus stream, reopen a writer,
or call a generic exception full W-row coverage. Positive fresh public flush is
required before aborting an open writer after finalize failure. Keep unknown ACK,
actual durable manifest and actual cleanup ownership separate. Diagnose original
persistence timeouts using captured real RPC budgets/work; old finding165 and other
historical timing failures remain unexplained/unwaived. No passing rerun erases them.

All24 requirements,18 UNVALIDATED source parents,30 pairs/90 endpoints,seven P3 tasks
and nine COMPLETE runtime cases remain: test_affa,test_trusted_launcher,test_prbc,
test_bounded_bootstrap,test_atomic_release_cancel_stage,test_lease_loss,
test_pre_handle_crash_survival,test_residual_membership,test_unrelated_sentinel.
Full M1/environment/global races, full platform regression and independent full
candidate review remain required. Author deferred immediate earlier teardown repair;
this did NOT waive stability/release gates135/147/149 or prove harmlessness. No stable17
commit until the complete selected increment is stable. Acceptance/main integration,
canonical-note update, scientific protocol freeze and principal campaign remain under
their existing authorization boundaries. Incident126 old collection-v6 wheel/archive
bytes remain unrecovered; never rerun historical colliding drivers.

Evidence root: docs/engineering/maestro-lite/evidence/affa17/. Current partial trace:
terminal-scope-offline-partial-traceability.json; source-extraction audit:
offline-codec-extraction-20261019.json; current handoff is this file. README/tasks/unit
specification/review and existing canonical-note proposal are updated, not accepted.
Recommended Sol/high next for native authority/failure/verification work; Luna/low for
receipt inventories. Informational recommendation only; no model switch/pricing claim.
Use set -e and unused exclusive evidence namespaces. Never mutate frozen snapshots,
installations or used scripts. Preserve literal matching venv argv0. Retain full tool
handles and poll the same process through terminal exit; observation timeout is not
completion. Keep commentary within60s. A new session must follow AGENTS, perform Git
freshness, and read the COMPLETE canonical dynamic note before proceeding.
'''
with (BASE/'continuation-scope-offline-20261019.md').open('x') as stream:stream.write(text)
print(json.dumps(dict(handoff='continuation-scope-offline-20261019.md',source=source,wheel=wheel,stable_increment17=False)))
