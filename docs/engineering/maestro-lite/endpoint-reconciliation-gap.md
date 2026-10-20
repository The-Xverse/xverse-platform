# Endpoint reconciliation gap (24/18/30/90 trace closure)

Status: **gap record; agent-drafted proposal v1 (finding 371) independently reviewed by a separate
agent session (finding 376: 32 agree, 20 agree with note, 1 alternative, 9 disagree); proposal v2
adopts the ten corrections; author ruling on v2 pending; no obligation closed; no code change.**
2026-10-20.

The ML3 successor change spec (`ML3-SUCCESSOR-CHANGE-SPEC-2026-10-03-v2`, 90 declared
endpoint rows, 62 distinct endpoints) was written against the superseded composition
(`api.py`, `affa.py`, `broker.py`, `lifecycle.py`, `results.py`). Resolving those endpoints
against the current candidate by module-level AST names gives:

| Status | Endpoints |
| --- | --- |
| present | 7 |
| file missing (5 superseded modules) | 25 |
| symbol missing in an existing module | 30 |

Exact list and hashes: `evidence/affa17/endpoint-reconciliation-gap-20261020.json`.
The current partial traces link 13 reverse endpoints (5 source, 8 test) and retain the
24 requirements, 18 source parents, 30 scenario pairs and 90 obligations as inherited
counts. Closing the 90 obligations therefore requires an endpoint-reconciliation successor
that maps each declared obligation to its current qualified interface identity (or records
it as superseded with rationale), under the independent review the change spec itself
requires. This is a documentation and design-identity task, not an implementation gap in
the runtime, and it is gated on the author's review of the proposed mapping.

## Reconciliation proposal (2026-10-20, finding 371)

Under the author's instruction to propose dispositions and proceed (finding 369, decision
AD-2026-10-20-b), `evidence/affa17/endpoint-reconciliation-proposal-20261020.json` (sha256
80ad3bea9c75e930265fdcc5edff4ebbc98875a0b3cc2d960ff2b9d0db8556d7, builder
`build-endpoint-reconciliation-20261020.py`) gives every declared endpoint a disposition:

| Confidence | Endpoints | Meaning |
| --- | --- | --- |
| present | 7 | resolves unchanged |
| mapped | 16 | same symbol in a renamed or re-owned module (for example broker.py::Broker to run_broker.py::RunBroker) |
| mapped_candidate | 38 | semantic correspondence judged from the current module contracts; review required |
| superseded_no_equivalent | 1 | lifecycle.py::mutation_lock: the single original dispatcher serializes mutations by construction |

Every proposed target and every listed alternative resolves against the current AST. The 90
obligation rows are re-bound pending review (89) or superseded pending review (1); none is
closed, the 24/18/30/90 trace is not re-pointed, and the change spec's independent review
remains the gate. Three captured declared forms (prbc.py::ProcessBoundaryOps.create_frozen,
prbc.py::ProcessBoundaryOps.residual_membership, artifacts.py::CollectionResult) already
resolve, so the earlier symbol-missing count overstates the gap by up to three rows.

## Independent review and proposal v2 (2026-10-20, finding 376)

The author's sign-off of 2026-10-20 lets a separate review session or agent count as independent.
`evidence/affa17/endpoint-reconciliation-independent-review-20261020.{json,md}` (JSON sha256
530444249dcb2f167cdd7ee740ccb458e29aeed6800ffee658ec68a584710339) reviews every v1 row against the
function and class bodies: AGREE 32, AGREE_WITH_NOTE 20, PREFER_ALTERNATIVE 1, DISAGREE 9. The
nine disagreements replace guessed targets with evidence-cited ones; the most consequential is that
`lifecycle.py::mutation_lock` is not superseded (a nonblocking mutation-lock set exists across the
dispatcher, teardown, owner, broker and providers). `evidence/affa17/endpoint-reconciliation-proposal-20261020-v2.json`
(sha256 7e869069d96a53fbdcb74e33c7fdb99c374de5b6e52ed0cd87f8514e87b484fc) adopts all ten
corrections (each resolved against the current AST), carries the twenty notes and retains v1 and
the review unchanged. Counts: 7 present, 16 mapped, 29 mapped_candidate, 10 reviewer_corrected, 0
superseded; 0 of 90 obligations closed. Next gate: the author's ruling on v2, after which the
24/18/30/90 trace can be re-bound under its own finding.

## Author ruling and trace re-binding (2026-10-20, finding 377)

The author accepted proposal v2 ("1 accepted"). `evidence/affa17/endpoint-rebound-traceability-20261020.json`
(sha256 0ab343d7620d3c5f25ca18a881927a82a2df33c337fb7b6187f6b99fb5d05129, builder
build-endpoint-trace-rebinding-20261020.py, parent runtime-lane-partial-traceability.json) binds all
90 declared obligations to their accepted current identities (55 distinct) with current file
hashes. Re-binding the trace is not acceptance of the implementation: every row keeps
`implementation_verified: false` and `closed_by_acceptance: false`; M1, acceptance and merge remain
open. The 24 requirements, 18 source parents (author-confirmed register v4), 30 scenario pairs and
nine runtime cases are retained as inherited.
