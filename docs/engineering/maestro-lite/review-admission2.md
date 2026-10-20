# Admission increment — separate read-only review

Date: 2026-10-18. Reviewer: current Codex session in a separate pass; no independent agent/factory reviewer is claimed.
Subject: U2 successor of the unchanged, verified ML3-PREP1 worktree.

Findings recorded before successor repairs:

| ID | Severity | Evidence | Required disposition |
| --- | --- | --- | --- |
| ADM-REV-01 | BLOCKER | `first-tests.log`: 32 passed, four failed before the bounded maxfail stop. `PermitSession` deep-copies `ExperimentPlanResult.run`, whose immutable FrozenMap contains a MappingProxyType; session creation raises `TypeError: cannot pickle 'mappingproxy' object`. | Copy only the mutable plan; retain immutable envelope/normalized values. Repeat real durable-session checks. |
| ADM-REV-02 | MAJOR | Pure read-only counterexample accepts approval generation `False` as binding generation `0` through Python equality. | Validate exact generation type before binding comparison. |
| ADM-REV-03 | MAJOR | Pure counterexample accepts a permit whose action sequence is a mutable list; its JSON pin matches the tuple encoding. | Reject mutable scope sequences and invalid typed approval fields before private retention or digest comparison. |
| ADM-REV-04 | MINOR | `claim_intent` accepts boolean sequence `False` and normalizes it to ordinal one; unknown typed nonce history can bypass the conservative missing-history check. | Require a real integer sequence, valid nonce identity types, and regression cases. Preserve legacy `append` behavior. |

The first test attempt does not prove durability, process-race arbitration, installed-wheel behavior
or regression compatibility. All runtime/containment/bootstrap/evidence/source-parent gates remain
open. The new atomic primitive does not retroactively certify legacy check-then-append callers.

## Second read-only pass

After ADM-REV-01–04 repairs, the combined Maestro/M3 check set passes 122 tests and
19 subtests. A further counterexample finds **ADM-REV-05, BLOCKER**: deleting the
consumed journal lets the same PermitSession claim the same permit again with sequence
one. M3's ordinary missing-file reload means empty; strict claim users must distinguish
a genuinely new store from lost consumption history.

Required repair: retain a durable store-identity marker in the existing M3 lock file,
binding the journal and parent identities before the first strict claim. Reopen must
reject missing/replaced history, malformed markers and descriptor/path substitution;
it must not erase/reinitialize a marker after uncertain publication. This is store
identity metadata, not a second permit-consumption database. Keep permit records in M3
and preserve legacy append/read behavior. Approval-owner binding to the admitted
run/store and full G5 root verification remain mandatory downstream.

## Packaging trace finding

**ADM-REV-06, MAJOR:** the predecessor's additive `pyproject.toml` packaging bytes
have SHA-256 `99730fd031809d841582cb29069d762eaf90779474bcadbec618bb5072073ca4`,
but ARGUS2-L-823/849/891 retain target revision
`a55f3d0ac062b5c349e920770188c28e2a473c5bf1bfdf6075b0a9f73a2b1320`.
Rebind those exact three implementation endpoint hashes in this successor and record
old/new provenance. Preserve all other links and immutable predecessor/run records.
This correction cannot close inherited malformed verification relations, supply missing
full-ML3 engineering trace or establish a trusted whole-project gate result.

## Final read-only disposition

ADM-REV-01–06 are resolved within this component scope. The final wheel/source
identity check covers seven modules, including Maestro admission and the modified
M3 journal. Exact source remains unchanged during the full owning-platform run:
**689 tests and 24 subtests pass**. The source-excluded installed-wheel consumer
passes **110 checks**, including actual competing journal processes, unknown/lost
history, prefix replacement/truncation and uncertain persistence. Ruff and the
candidate endpoint/hash checks pass. The packaging trace receipt proves that
only the three named inherited target revisions changed.

Verdict: **reviewed partial U2 candidate; not full Maestro execution admission**.
Approval facts are trusted inputs, not authenticated operator decisions. Journal
identity is scoped to the owned store and does not authenticate an actor allowed
to replace both private files. Full original-holder/store approval, G1/G3/G4/G5,
descriptor/C1 survival, actual watchdogs, Argus flush/tickets, whole-project trace,
resource restart, independent full-candidate review, acceptance and merge remain
pending. No historical passing record, run admission or source-parent status is
rewritten. The PREP1 worktree is still exact. Next: U3 supervision and the descriptor
contract, with concrete containment proof before any process-mode admission.

## Revision 2 findings — previous verdict superseded for current source

The 689/110 passing revision remains preserved as predecessor evidence. A further
read-only review finds **ADM-REV-07, MAJOR**: every claim revalidates already-used
start permits, so expiry of unit A's start permission incorrectly blocks unit B's
independently fresh permit. Validate the full set at the first claim, then revalidate
only the selected unused unit while retaining full prepared-value integrity checks.

**ADM-REV-08, BLOCKER:** after an intent fsync error, the same session can issue a
different unit's durable claim. A persistence failure must latch the session closed;
fresh sessions must also reject unresolved prior intents in the selected catalog and
environment, rather than infer released resources from fresh permit identities.
No launch or cleanup is inferred from a pending record. Preserve the existing failed
attempt and prove no additional intent bytes after the failure. These repairs are
required before the current candidate is presented as verified partial U2.

## Revision 2 final disposition

ADM-REV-07/08 are corrected and discriminating tests pass. All initial permissions
are freshly checked at the first claim; subsequent claims retain full prepared-value
integrity while checking only the selected unit's validity. Read/persistence failure
permanently closes the original session's claims. Fresh identities cannot bypass a
pending intent in a selected scope; this is no reconstruction of resource ownership.

Revision 2 passes **693 owning-platform Python tests and 24 subtests** and **114
source-excluded installed-wheel checks**. The focused Maestro/M3 run passes 136 tests
and 19 subtests. Source stability, seven installed/source identities, static checks,
exact endpoint hashes and predecessor archive integrity are recorded separately.
The first revision-2 launcher used the host interpreter for its import check and
failed before starting pytest; the corrected launcher used the pinned verification
environment. The earlier 689/110 revision remains historical in the hash-bound archive.

Verdict: **reviewed partial U2 revision 2; full Maestro runtime admission remains
unproven**. All stated original-holder/store, containment, bootstrap, watchdog,
source-parent, lifecycle-evidence, restart, full-trace, independent full-review,
acceptance and merge gates remain open. This same-session separate review is not
an independent reviewer agent or factory review. Next: U3 supervision and U4
descriptor/C1 work under the existing full-scope contracts.
