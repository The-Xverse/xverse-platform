# Combined Maestro regression — completed source phase

Status at2026-10-19 source-terminal checkpoint: partial verification, wheel phase
pending, full increment17 unfinished. This is the single missing combined current
Maestro regression authorized by review317; it is not whole-platform or M1 evidence.

Original session53866 source phase exited1:1493 passed/two failed in1310.39s.
The driver then started installed-wheel pytest736231 over the same271 frozen
files and81 packaged Python/C sources. No source/test/plugin/deadline changes or
unchanged native retry were made during the attempt.

| Incident | Original source failure | What remains unknown |
| --- | --- | --- |
|318|schedule/step-complete prepare-unrelated RPC missed its original1s end; past-restart test failed before control submission|Worker/storage/scheduling cause; rejected-control behavior for this failed case; relation to older incidents|
|324|collect/action=finish receive timed out at original end1022808197994349ns; collect_outputs did not return|First RPC failure record and exact worker substage; causal correction; relation to other incidents|

The exact [source inventory](evidence/affa17/integrated-maestro-20261019a/source-terminal-failure-inventory.json),
[terminal receipt](evidence/affa17/integrated-maestro-20261019a/maestro_full-source-receipt.json)
and original log retain both outcomes.324 did not reach broker publication,
public export or its closed-reader assertions. Files left by an unfinished
operation do not establish its acknowledged success. Both causes remain UNKNOWN.

The separate [source audit](evidence/affa17/integrated-maestro-20261019a/maestro_full-source-terminal-audit/audit.json)
exited0 and checked exact frozen/source/wheel identity. It inventories2931 retained
files,853 recorded owned cgroup reservations (all absent, with worker reaping
recorded),331 public projections and6776 verified M3 reference links.210 reader/
reference gaps across the whole suite are unclassified observations, including
adverse controls; they are not210 product defects.58 original-input offline
recomputations yield four complete and54 incomplete, without independent custody
or complete runtime-case/M1 claims.

Pending-stop work-product checker v2 separately exits0 over271 retained files,
118 unchanged source-tree entries/81 packaged Python/C files,eight endpoints/56
links,six actual original waits and eight unchanged draft input bindings. The
original checker wrongly counted all src/ entries as packaged code; it is retained
with its failed invocation and exact correction as CAPA321. No workload was rerun.
The [v2 result](evidence/affa17/runtime-pending-stop-work-products-check-v2.json)
records document hashes at that earlier checkpoint; subsequent status documentation
does not change its historical identity or the tested runtime bytes.

The source-terminal [CAPA snapshot](evidence/affa17/capa-20261019-integrated-source/register.json)
validates28 records/152 bindings:22 local FIX_CANDIDATE/HYPOTHESIS and six
UNRESOLVED/UNKNOWN135/222/286/287/318/324. Every effectiveness remains
NOT_DEMONSTRATED. Independent cause confirmation, observation windows, automatic
CAPA workflow and025 integration remain absent. Earlier registers/traces remain
immutable historical snapshots; successful unrelated controls close no incident.

## Current trace navigation review

The [structural audit](evidence/affa17/integrated-maestro-20261019a/trace-reconciliation-source-checkpoint.json)
checks26 hash-bound historical snapshots, retaining24 requirements and737 unique
code/test/support references. Historical file hashes remain historical; changed
hashes do not transfer old behavior claims to the current source.
The [corrected classification](evidence/affa17/integrated-maestro-20261019a/trace-reference-classification-source-checkpoint-v2.json)
identifies535 exact Python functions,51 exact classes,115 unique shorthand
candidates,nine ambiguous shorthand references,24 native references,one embedded
worker-template reference and two engineering verifiers outside this Maestro-only
collection. Eighteen test-role references without pytest-node matches are support
material; no missing test follows from that count.

The original classifier omitted class nodes; its output and exact correction are
retained as CAPA328, with51 same-input AST class controls. Current classification
selects no semantic replacement. Source inspection gives these navigation options
for the nine ambiguous names, without closing the corresponding requirements:

| Historical shorthand | Current definitions and distinct roles |
| --- | --- |
| lifecycle.claim_intent | FileEvidenceJournal is the durable implementation; InMemoryEvidenceJournal is fixture storage and supplies no durability credit |
| run_broker.cancel | RunBroker performs run-wide cancellation; RunUnitIssuer forwards to its original broker |
| prbc.create_frozen | BoundaryOps is the interface; ProcessBoundaryOps allocates and freezes original process boundaries |
| owner.cancel | ReleaseOwner cancels the original owner and issuers; GateConnection closes its original latch/channel |
| bootstrap._holder | BootstrapSession checks original session/inventories; BootstrapChild checks original child/capability identity |
| owner._holder | _Original checks original object/process identity; StageSupervisor extends this with original boundary/latch pins |
| prbc.residual_membership | BoundaryOps is the interface; ProcessBoundaryOps observes original residual membership |
| lifecycle.append | EvidenceJournal is the protocol; FileEvidenceJournal is durable; InMemoryEvidenceJournal preserves fixture compatibility |
| admission.ready_for_execution | IntentReceipt and PermitSession both return false; neither confers executable readiness |

Qualified candidates and current lines/hashes are in the classification artifact.
The table is a read-only engineering review, not a rewrite of historical trace
identities or full semantic revalidation. Current requirement,source-parent and
runtime-case closure remain unproven. The newer
[CAPA snapshot](evidence/affa17/capa-20261019-trace-classifier/register.json)
validates29 records/159 bindings, including328's local classifier correction;
all effectiveness remains NOT_DEMONSTRATED and runtime incidents remain open.

Next: poll the original wheel phase, retain its complete failure inventory and run
the same separate terminal-phase auditor only after its original terminal receipt.
Review both phases before any source repair or affected successor verification.
Do not infer causes, extend ends or retry unchanged for green. Full24 requirements,
18 source semantics,30 pairs/90 endpoints,nine complete runtime cases,seven P3 tasks,
M1/environment,whole-platform regression and separate full review remain open.
Actual admitted service/M1 executions remain zero. No stable17 commit,acceptance,
merge,scientific claim or canonical-note edit follows. Sol/high is recommended for
the next causal review. See the [exact continuation](evidence/affa17/continuation-integrated-source-20261019.md).
