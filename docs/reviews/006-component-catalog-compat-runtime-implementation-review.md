# M3 implementation architecture review

**Date**: 2026-09-20
**Scope**: T005–T017 platform catalog, planner, permit/evidence boundary, fixture provider, process
provider, tests, examples, validation script, and public documentation.
**Method**: Separate read-only pass after implementation and its first complete test run.
**Initial disposition**: Changes required before T005–T017 can be accepted as complete.
**Current disposition**: Repair and re-review complete; no BLOCKER or MAJOR finding remains open.

## Findings recorded before repair

| ID | Severity | Finding / impact | Required disposition |
|---|---|---|---|
| M3-I01 | BLOCKER | Provider ownership checks use only provider ID plus opaque ID. A fabricated handle can supply a different execution, action, or concrete resource identity and still reach the owned resource. | Store the complete issued handle and require exact equality for observe, stop, cleanup, and revalidation; add forgery tests. |
| M3-I02 | MAJOR | The lifecycle plan/evidence preserve resource revisions and artifact digests but omit explicit System, Deployment, Component, Profile, binding, realization, target, interface, and time-domain selections required by FR-010/FR-017. | Add immutable selection context to the plan digest and evidence records, with deterministic tests. |
| M3-I03 | MAJOR | Readiness is required syntactically but the controller treats any provider status as success; prepare/start/observe timeouts are not enforced. | Evaluate the declared observation condition, classify unavailable/failed observations, and enforce declared provider-call timeouts without inferred retry. |
| M3-I04 | MAJOR | `ExecutionPermit` omits issuer label, operation classes, exclusions, and public-safety classification from the permit contract. | Model, validate, persist, and test every required permit binding. |
| M3-I05 | MAJOR | File-journal sequencing and permit replay checks are safe only when callers share one journal object; separate instances can hold stale state and append duplicate sequence numbers. | Add an inter-instance file lock and reload/validate state while holding it before every append and replay decision. |
| M3-I06 | MAJOR | Physical bindings inherit the existing XDL asset check, but hybrid bindings can plan without the external asset and ownership boundary required by FR-012. | Reject a physical or hybrid catalog entry without an explicit external asset reference and ownership declaration. |
| M3-I07 | MAJOR | Runtime failures escape as generic exceptions and do not satisfy FR-019's stable code, severity, phase, selected identity, explanation, correction, and deterministic ordering contract. | Return or raise a typed lifecycle diagnostic/error with stable codes and full required context; test representative failure classes. |
| M3-I08 | MAJOR | The process provider constrains executable selection, working directory, environment, shell, and handles, but does not provide an OS filesystem/network sandbox. Calling it cannot by itself guarantee FR-034 legacy-checkout immutability. | Make the isolation limit explicit and require a caller-supplied, fail-closed isolation attestation before process start; keep the public M3 proof on the in-memory fixture. |
| M3-I09 | MINOR | Catalog data carries provenance and maturity but has no explicit public projection that preserves observed/declared/target/unknown/withheld distinctions from FR-006. | Add a deterministic public projection and tests for classification and withholding. |

## Positive assessment retained

The implementation uses the approved derived XDL graph, keeps planning permit-free, blocks secret
dependencies, rejects ambient command construction, records durable intent before mutation, preserves
safe-stop behavior after evidence failure, and makes no legacy compatibility or parity claim. The
public fixture and existing capability tests pass, but passing tests do not waive the findings above.

## Repair disposition

| Finding | Resolution evidence | Status |
|---|---|---|
| M3-I01 | Fixture and process providers store the full issued handle and require exact equality; forged execution/action/resource bindings are rejected by tests. | Resolved |
| M3-I02 | `LifecyclePlan.selection`, its digest, and every evidence record preserve the exact graph, target, realization, interfaces, time domains, Scenarios, environment, and artifacts. | Resolved |
| M3-I03 | Providers receive declared timeouts, the controller detects overrun, observation evaluates the declared readiness condition, and mismatches are classified `not-ready`/`unavailable`. | Resolved |
| M3-I04 | Permit issuer, operation classes, exclusions, and public-safety classification are validated and persisted with activation evidence. | Resolved |
| M3-I05 | File journals use a private inter-instance lock, reload and validate under that lock, and allocate contiguous sequences from current durable state. | Resolved |
| M3-I06 | Catalog policy rejects physical or hybrid entries without both external asset and lifecycle ownership declarations. | Resolved |
| M3-I07 | Controller failures expose `LifecycleError` with stable code, severity, phase, selected identity, explanation, and correction. | Resolved |
| M3-I08 | `ProcessProvider` fails closed without a matching `IsolationAttestation`; contracts state that it is a trust input rather than an OS sandbox, and public proof remains in-memory. | Resolved |
| M3-I09 | `catalog_entry_public_data` emits deterministic observed, declared, target, unknown, withheld, maturity, and limitation classes. | Resolved |

The repair re-review found no new BLOCKER or MAJOR issue within the prototype scope. OS sandboxing,
distributed coordination, authentication, a legacy provider, and production operation remain outside
M3 T005–T017 and cannot be inferred from this result.

## Cross-repository T018 addendum

The subsequent `xverse-compat` design review found that provider kind was selected by the plan but was
not part of the concrete provider/handle identity. The finding was recorded as companion review
CP-R02 before repair. Platform API `0.3.0` now carries and verifies the exact provider ID/kind pair in
provider dispatch, issued handles, later lifecycle operations, persisted evidence, and reconciliation.
A wrong-kind test proves rejection before provider mutation.

The companion design also closes its process-action, provider-assembly, version-pin, negative-case,
and repository-guidance findings. Focused M3 validation now passes 20 tests and the complete suite
passes 84. This addendum completes platform task T018 only; it does not select a legacy target,
authorize compatibility-provider implementation, or authorize execution.

### Authorized conformance follow-on

The user subsequently accepted the companion design and authorized only its target-neutral T008–T011
conformance work. `xverse-compat` now imports `xverse-xdl==0.3.0`, content-pins the complete local
platform package surface, resolves providers through an explicit ID/kind composition root, and proves
C01–C14 with a controlled in-memory process-action fixture. Its separate implementation review records
and resolves CP-I01–CP-I06. Seventeen companion tests and all 84 platform tests pass.

This follow-on contains no target-specific provider, descriptor, subprocess execution, legacy target,
or compatibility/parity evidence. Platform T019 and every legacy execution gate remain pending.

## Repair status

- [X] Resolve M3-I01 through M3-I09 in a subsequent implementation pass.
- [X] Rerun the focused and complete test suites, fixture validation, source/package checks, Spec Kit checks,
  public-safety scans, and companion-repository status comparison.
- [X] Re-review the repair and update the M3 acceptance evidence without selecting a legacy target.
