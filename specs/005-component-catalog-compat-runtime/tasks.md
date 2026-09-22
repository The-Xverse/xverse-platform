# Tasks: M3 component catalog and compatibility runtime

**Input**: [spec.md](spec.md), [clarifications.md](clarifications.md), [research.md](research.md),
[data-model.md](data-model.md), [plan.md](plan.md), and [contracts](contracts/).

## Phase 1: M3 design and governance

- [X] T001 Confirm M3 specification quality and resolve the M3-R01–M3-R07 review amendments.
- [X] T002 Record ADR-0014 for the XDL-anchored derived component catalog.
- [X] T003 Record ADR-0015 for explicit lifecycle ownership and no inferred legacy cleanup.
- [X] T004 Define execution-permit, evidence-journal, and selected-component decision contracts.

## Phase 2: Platform catalog/planner foundation

- [X] T005 Specify `io.xverse.runtime.compatibility` Profile schema and binding-only validation rules.
- [X] T006 Define immutable derived catalog, lifecycle plan, execution permit, ownership handle, and evidence-journal models.
- [X] T007 Implement catalog derivation from normalized Deployment binding → System instance → Component relationships.
- [X] T008 Validate cross-resource XDL Component, Deployment, Profile, interface, realization, and provenance references.
- [X] T009 Implement deterministic permit-free lifecycle planning and explicit execution eligibility.

## Phase 3: Lifecycle safety and fixture proof

- [X] T010 Define process/provider actions with absolute command, argument, working-directory, environment, and inherited-handle isolation.
- [X] T011 Implement provider-issued ownership handles, idempotent start/stop, exclusive mutation, and restart reconciliation.
- [X] T012 Implement durable intent/outcome evidence and `evidence-incomplete` safe-stop behavior.
- [X] T013 Implement execution-permit validation, single-use consumption, expiry, replay, and plan/environment binding.
- [X] T014 Implement controlled fixture provider and lifecycle evidence recorder.
- [X] T015 Test malformed graphs, mutable provenance, artifact sharing, ambient discovery, missing readiness, and secret blocking.
- [X] T016 Test command isolation, unowned cleanup, repeated/concurrent calls, interruption, handle reconciliation, evidence failure, and invalid permits.
- [X] T017 Test deterministic planning/evidence ordering, public safety, and no-legacy-diff checks.

## Phase 4: Compatibility provider and selected legacy boundary

**Deferred**: ADR-0018 places T019–T021 after acceptance of the main platform capability baselines.

- [X] T018 Create and separately review the xverse-compat provider specification/task package without duplicating platform semantics.
- [ ] T019 Select one legacy boundary through an owner-reviewed decision record with exact artifact, environment, lifecycle, and interface evidence. SD-0001 now pins a reproducible artifact and exact candidate XDL graph; its deterministic plan remains blocked by SD-R03–SD-R06 and SD-R08.
  The candidate lock, side-effect-free validator, and closure packet are complete; the seven external
  evidence decisions and conflicting startup-order accounts still require owner resolution. The
  static interface audit and companion projection narrow the contract but add A15/A16 hazards that
  cannot be closed by source inspection. ADR-0017 and the validated companion rebuild envelope select
  a remediation mechanism; they do not supply the target patch/artifact or close any plan blocker.
  ADR-0018 defers target-specific work until the platform-baseline gate passes.
- [ ] T020 Implement and test that selected provider only after explicit target and execution authorization.
- [ ] T021 Record lifecycle evidence and limitations; do not claim application parity.

## Phase 5: Acceptance

- [ ] T022 Complete validation, architecture review, and M3 acceptance checklist.
- [ ] T023 Obtain human approval before M4 specification or any parity claim.

Under ADR-0018, T023 follows the reordered platform-first capabilities rather than immediately
following the M3 fixture.

## Dependencies

T001–T004 precede implementation. T005–T009 depend on approved design. T010–T017 prove safe runtime
mechanics without legacy execution. T018–T021 require separate xverse-compat and target-specific user
authorization. T022–T023 require all applicable prior evidence.
