# M3 component catalog and compatibility runtime acceptance checklist

**Status**: Design and isolated fixture implementation approved; legacy selection and final M3
acceptance are deferred by ADR-0018 until the main platform capability baselines are accepted.

## M3 design review

- [X] ACC001 Approve ADR-0014's exact derived identity: Deployment identity plus binding ID, resolved through System instance to Component.
- [X] ACC002 Approve `io.xverse.runtime.compatibility` as the only typed runtime Profile payload, attached only to a Deployment binding.
- [X] ACC003 Approve ADR-0015's provider-handle ownership, process isolation, idempotency, exclusive mutation, and restart reconciliation semantics.
- [X] ACC004 Approve permit-free planning and permit-only execution, including the stated host-permission trust boundary.
- [X] ACC005 Approve durable intent, outcome, and `evidence-incomplete` recovery behavior.
- [X] ACC006 Confirm secret-dependent entries are catalog-visible but blocked before planning and execution.
- [X] ACC007 Confirm that the initial M3 implementation proof uses an isolated fixture.
- [X] ACC008 Confirm that no legacy execution target or cruise-control baseline is selected here.
- [X] ACC009 Approve the catalog, lifecycle, execution-permit, evidence, and selected-component decision contracts.
- [X] ACC010 Confirm platform/xverse-compat responsibility and dependency direction.
- [X] ACC011 Approve public-safe evidence and maturity language.
- [X] ACC012 Decide whether to authorize M3 fixture implementation; this does not authorize legacy execution.

## Future implementation evidence

- [X] ACC013 Catalog/schema/reference tests and deterministic planning pass.
- [X] ACC014 Fixture lifecycle evidence establishes owned prepare/start/observe/stop behavior.
- [ ] ACC015 Selected-component decision record pins artifact, environment, lifecycle, interface, owner, and exclusions. SD-0001 pins the artifact and exact candidate XDL graph but remains blocked by SD-R03–SD-R06 and SD-R08.
  The locked validator and closure packet are ready for evidence intake; all seven plan blockers remain.
  The static interface audit narrows the six-route contract but adds a compiled-endpoint BLOCKER and
  confirms unresolved serialization, readiness, shutdown, logging, and dependency constraints.
  The user selected the ADR-0017 configurable-rebuild strategy and the companion repository now has
  a validated controlled rebuild envelope, but no restricted patch, new target artifact, containment
  attestation, or owner acceptance exists. ADR-0018 now defers this work behind platform baselines.
- [ ] ACC016 Separate explicit authorization permits only the selected legacy execution actions.
- [ ] ACC017 Selected-component lifecycle evidence passes without a legacy checkout modification.
- [X] ACC018 Separate architecture review has no unresolved BLOCKER or MAJOR finding.
- [ ] ACC019 After the ADR-0018 platform-baseline gate passes, human acceptance authorizes renewed
  legacy-integration and parity planning; it does not establish parity by itself.

## Decision record

**Reviewer**: User
**Date**: 2026-09-20
**Decision**: Approved the next step, implementing T005–T017 with the isolated fixture.
**Amendments / exclusions**: No legacy target selection, legacy provider, or legacy execution.
On 2026-09-21, ADR-0018 formally deferred those activities until platform baselines are accepted.
**Evidence gaps**: The nominated target and candidate artifact are pinned, but selected-target owner
approval, environment, completed lifecycle/interface contract, retention, vendor-binary disposition,
provider implementation, and execution evidence remain absent.
