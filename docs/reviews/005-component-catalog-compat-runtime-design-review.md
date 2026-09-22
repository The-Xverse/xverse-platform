# M3 design review — component catalog and compatibility runtime

**Date**: 2026-09-20
**Scope**: M3 specification, clarifications, research, data model, contracts, plan, tasks, analysis,
ADR-0014, and ADR-0015.
**Review method**: Separate read-only pass after the initial Spec Kit design package, followed by an
authorized design-repair pass.
**Current disposition**: Design accepted and isolated fixture implementation authorized on
2026-09-20; legacy selection and execution remain pending.

## Findings recorded before repair

**BLOCKER**: none.

| ID | Severity | Finding / impact | Required disposition |
|---|---|---|---|
| M3-R01 | MAJOR | The authored shape alternates between a runtime Profile, catalog extension, and separate Catalog Entry. Identity and validation are therefore ambiguous and could create a second configuration language. | Select one exact XDL representation and derived catalog model. |
| M3-R02 | MAJOR | One scenario requires approval to plan while FR-013 and the lifecycle contract require approval only to execute. | Keep planning side-effect-free and permit-free; bind a precise permit only at execution. |
| M3-R03 | MAJOR | Runtime ownership is aspirational without handle identity, command/provider isolation, idempotency, concurrency, interruption, and restart reconciliation semantics. | Define testable ownership and lifecycle invariants. |
| M3-R04 | MAJOR | Evidence is required for every transition, but evidence-write failure behavior is absent. | Define durable intent, outcome, degraded-evidence, and safe-stop behavior. |
| M3-R05 | MAJOR | Indirect secret references are allowed while secrets management is excluded. | Make secret-dependent execution explicitly blocked in M3. |
| M3-R06 | MINOR | FR-004 requires artifact identity uniqueness, preventing legitimate immutable artifact reuse. | Require unique catalog entry identity and allow digest-identical artifact sharing. |
| M3-R07 | MINOR | Tasks and acceptance checks do not explicitly cover the preceding safety semantics. | Add implementation and negative-test coverage for every repaired rule. |

## Positive assessment retained

The design correctly preserves production immutability, closed local resolution, XDL centrality,
fixture-first proof, explicit maturity limits, M0 findings, repository direction, and the separation
between lifecycle evidence and application parity.

## Repair disposition

| Finding | Resolution evidence | Status |
|---|---|---|
| M3-R01 | ADR-0014 and the catalog contract define one derived entry keyed by Deployment identity plus binding ID; typed runtime data exists only in `io.xverse.runtime.compatibility` on that binding. | Resolved |
| M3-R02 | FR-013/FR-014 and the permit contract make planning permit-free and execution permit-bound. | Resolved |
| M3-R03 | ADR-0015 and the lifecycle contract define process isolation, opaque provider handles, idempotency, exclusive mutation, and restart reconciliation. | Resolved |
| M3-R04 | FR-031 and the evidence contract require durable intent and define `evidence-incomplete` safe-stop behavior. | Resolved |
| M3-R05 | FR-032 blocks secret-dependent planning/execution and makes no secret-resolution claim. | Resolved |
| M3-R06 | FR-004 makes derived catalog identity unique while allowing digest-identical artifact reuse. | Resolved |
| M3-R07 | Tasks T010–T017 and acceptance checks ACC003–ACC009 cover implementation and negative verification of the repaired rules. | Resolved |

No BLOCKER or MAJOR design finding remains open. This conclusion evaluates the repaired design only;
it is not fixture implementation evidence, legacy target selection, execution authorization, or M3
acceptance.

## Repair status

- [X] Resolve M3-R01 through M3-R07 in a subsequent design pass.
- [X] Rerun Spec Kit prerequisites, artifact/link/marker checks, and requirement-to-task analysis.
- [X] Obtain human M3 design decision separately from legacy execution authorization.
