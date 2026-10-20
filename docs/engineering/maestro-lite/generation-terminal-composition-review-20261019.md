# Explicit restart and terminal report composition

Status: ENGINEERING CHOICE DELEGATED / PARTIAL ACTIVE-RUN IMPLEMENTATION VERIFIED; FULL17 OPEN.
This is a read-only finding within full increment17. It does not amend the
hash-bound v2 design, canonical note, scientific protocol or acceptance policy.

Governing input:
/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/engineering/successors/ML-DESIGN-2026-10-03-v2/detailed-design.md
(the source remains labelled DRAFT). Its original hash is recorded in
coverage-runtime-closure-inputs.json. The boundary analysis below records the
pre-implementation state at guard-delegation-20261019e and inventory verification
terminal-controller-inventory-20261019b. Current partial successor: ADRs
ML3-RESTART-0001/0002 and ML3-PROBE-0001; evidence
evidence/affa17/active-restart-20261019e/verification.json and
active-restart-partial-traceability.json. Historical inputs are unchanged.

## Actual contract and implementation boundaries

| Original provision | Current implementation/evidence | Consequence |
| --- | --- | --- |
| D1: start returns the bounded whole lifecycle through teardown/collection; restart is an explicit admitted request | FiniteDispatcher.run holds the original mutation-owner reservation through terminal report/close | It is not a live session handle on return |
| D2: exactly one scheduled start per unit, no duplicate starts | projection._project enforces that rule | Do not insert a second Scenario start to manufacture generation2 coverage |
| D5: one mutation coordinator; concurrent start/restart/conflicting collect reject | Dispatcher pins original controller/facade/bindings; broker performs explicit prepared generation/advance using the original issuer | Do not rotate dispatcher pins or replace a view in a test to bypass admission |
| D5: restart requires normal prior release, fresh generation/execution/permit and dependency reprobes | Existing broker generation and replacement-controller checks exercise that path outside the v6 finite dispatcher | Those abort-only checks do not demonstrate its original v6 report/collection composition |
| D5/D7: no writer reopen; original scope/normal obligations survive failures | Original automatic v6 closure consumes report/close receipts and closes/fails the writer before run returns | A later restart needs an explicitly defined evidence/supervisor lifecycle |

The missing piece is the relationship between whole-lifecycle `start`, explicit
`restart`, active mutation serialization and terminal evidence. The present draft
does not select a concrete original v6 API path for issuing generation2 and
reconciling a replacement controller while retaining a reviewable terminal result.
This is an unresolved composition requirement, not proof that no valid design is
possible and not permission to weaken existing guards.

## Concrete alternatives for reconciliation

1. Preserve blocking whole-lifecycle `start`. Define explicit `restart` as a
   separately admitted successor execution after the prior lifecycle ends, with a
   fresh evidence root/writer and explicit linkage to prior exact generation and
   ownership facts. Never reopen the previous writer or infer adoption. The
   supervisor/capability lifetime and initial-generation handling must be specified;
   current workers initialize generation1, so this is not implemented by changing
   a test argument. This preserves the literal current D1 behavior.
2. Support an active supervised run receiving explicit restart requests at declared
   safe points. Define the request/result semantics, single mutation owner,
   conflicts, exact fixed ends, authentic controller/view transition and updates to
   admitted current bindings. Keep one scheduled start; explicit restart remains a
   separate operation with fresh permits, prior release and dependency reprobes.
   All issued generations stay in the same original report/collection universe.
   This refines the current D1/D5 API behavior and needs an ADR before code.

For either alternative, define artifact ownership before execution: distinct
per-generation source paths or an explicit current-generation-only declaration;
do not infer generation provenance merely because a reused filename exists.
Pin independent expected outcomes before implementation, including restart reject,
unknown consumption, issuer/controller loss, cleanup-only recovery, unchanged
original evidence and whole-universe offline assessment. Keep full17 requirements,
30 pairs/90 endpoints and all nine complete runtime cases open until proved.

## Proven work while this composition remains open

Original v6 tests now retain four declared generation contexts (two used generation1,
two unused generation2), close normal report/collection and retain/reap both retired
and current controller helper slots. The unreconciled successor receives no
productive start access. Successor live/dead cases pass source and installed wheel.
Eight copy-only offline counterexamples delete a future context or its report rows,
update copied index/manifest hashes and are rejected against the unchanged external
admission. These facts do not establish issued generation2 or productive recovery.

The author subsequently answered “propose something and go”. The pending choice is
resolved by delegation: select alternative2, as recorded in ADR-ML3-RESTART-0001.md.
Do not ask this choice again. The original alternatives above remain historical
analysis. No canonical-note update was applied; external source DRAFT status and
acceptance/scientific boundaries remain unchanged.

The successor proves genuine explicit leaf generation2 through the original
blocking dispatcher, including external-thread submission, normal records,
current-generation-only output, writer closure and independently pinned closed
recomputation. Parent rejection, controller loss and unknown issuance/wait after
actual storage loss retain their conservative outcomes. Version3 separately admits
the new restart timeout; versions1/2 and existing phase bounds are preserved.
Successful transitive restart and productive controller recovery remain open.

Later partial successor: ADR-ML3-RESTART-0003 and
evidence/affa17/continuation-active-transitive-20261019.md now verify explicit
three-unit transitive generation2, normally-cleaned leaf restart, omitted-dependent
rejection and partial storage-loss outcomes in both phases. Six original-input
closed recomputations/public copies are retained. Old4.8s source leaf teardown
finding222 remains: affected source58/59,wheel59/59 is not stable17. Productive
controller recovery and the rest of the original full scope remain open. Prior
statements about transitive implementation above describe their historical revision.

Later productive-recovery successor: ADR-ML3-RECOVERY-0002 now implements and
verifies the explicit active coordinator transition over the same original writer,
including no/mixed issuance, normal stopped/released units, current generation2,
subsequent productive work, actual helper loss, a queued heartbeat race and
storage-loss cleanup-only scope. See the active-controller recovery continuation
and current verified-scope trace.136 targeted checks pass per phase;18 closed
original-input recomputations retained. The remaining full matrix, timing135/222,
full M1/regression/review and acceptance remain open. Earlier statements about
missing productive composition describe their recorded historical revisions.
