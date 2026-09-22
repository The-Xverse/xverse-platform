# Selected-component decision contract

This record is required before work on a legacy-specific provider or any legacy execution. Completing
it selects a review target; it does not itself grant execution permission.

## Required decision fields

- decision ID, status, reviewers, and decision date;
- exact catalog identity and Component/System/Deployment/Profile revisions;
- immutable artifact digest and public-safe provenance evidence;
- isolated environment identity, host owner, and resource limits;
- declared interfaces, protocol limits, lifecycle actions, readiness, stop, and timeout rules;
- provider ownership boundary and expected opaque-handle behavior;
- secret-dependency status, with any dependency blocking planning and execution under M3;
- public-safe evidence policy, withheld fields, and retention location;
- excluded actions, known unknowns, rollback/containment owner, and maturity claim;
- explicit statement that the legacy source checkout remains immutable.

The decision fails closed when any required field is missing or inferred from repository names,
ambient discovery, mutable references, undocumented scripts, or fixture results. A later execution
still requires a matching single-use permit under [execution-permit.md](execution-permit.md).

For SD-0001, use the [selection-closure packet](../evidence/SD-0001-closure-packet.md) to map every
declared blocker to its public decision projection and any separately retained restricted evidence.
