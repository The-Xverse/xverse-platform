# Quickstart: M3 component catalog and compatibility runtime design

This package includes a prototype derived catalog/planner and isolated fixture lifecycle. It provides
no legacy adapter or legacy execution path.

Review in this order:

1. Read the [feature specification](spec.md) and confirm the M3 boundary.
2. Review [clarifications](clarifications.md), [research](research.md), [data model](data-model.md),
   [catalog contract](contracts/catalog.md), [lifecycle contract](contracts/lifecycle.md),
   [execution-permit contract](contracts/execution-permit.md), [evidence contract](contracts/evidence.md),
   and [selected-component decision template](contracts/selected-component-decision-template.md).
3. Review the proposed delivery [plan](plan.md), [tasks](tasks.md), known [analysis](analysis.md), and
   the separate [design review](../../docs/reviews/005-component-catalog-compat-runtime-design-review.md)
   and [implementation review](../../docs/reviews/006-component-catalog-compat-runtime-implementation-review.md).
   For SD-0001, also read the [decision review](../../docs/reviews/008-m3-selected-component-decision-review.md),
   [candidate-XDL review](../../docs/reviews/009-m3-candidate-xdl-blocker-review.md), and
   [closure-readiness review](../../docs/reviews/010-sd0001-selection-closure-readiness-review.md),
   followed by the [static-interface review](../../docs/reviews/011-sd0001-static-interface-review.md).
4. Complete the [acceptance checklist](checklists/acceptance.md), then decide whether to approve M3
   design only, authorize fixture implementation, or identify a separate
   target-selection process. Do not treat design approval as authorization to execute legacy software.

Validate the active Spec Kit feature pointer from `xverse-platform`:

```sh
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
```

Run the public fixture validation after installing the locked environment:

```sh
.venv/bin/python scripts/validate_m3.py
```

The command validates the closed XDL fixture graph and Profile schema, derives one catalog entry,
builds a deterministic plan, activates a local single-use fixture permit, and records prepare,
start, observe, stop, and cleanup evidence in a temporary journal. It starts no external or legacy
workload. A selected legacy component still needs its own pinned decision record, provider, and
execution authorization.

Validate the exact SD-0001 candidate graph without executing it:

```sh
.venv/bin/python scripts/validate_sd0001.py
```

The command verifies the candidate lock, every XDL and Profile-schema digest, exact resource/catalog/
provider/artifact identities, deterministic plan digest, and all seven blockers. Validity means the
graph is internally consistent and still reports `plannable:false`, `executionEligible:false`, and
`legacyExecution:false`. Review the [closure packet](evidence/SD-0001-closure-packet.md) before changing
any blocker-backed field.
