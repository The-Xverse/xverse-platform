# Specification analysis — M3 component catalog and compatibility runtime

**Date**: 2026-09-20
**Mode**: Read-only Spec Kit analysis before implementation.

## Findings

| ID | Severity | Category | Finding | Disposition |
|---|---|---|---|---|
| A01 | MAJOR | Baseline selection | M0 documents two cruise-control paths and no owner-supported executable target. | Keep legacy target selection as a gated future decision; fixture proof cannot substitute for it. |
| A02 | MAJOR | Lifecycle safety | M0 observes broad cleanup, fixed delays, continued startup after errors, and incomplete container-stop evidence. | Require owned actions, observable readiness, explicit stop semantics, and fail-closed planning. |
| A03 | MAJOR | Authorization | M3's milestone includes external execution, but current authorization covers specification only. | Keep all runtime/legacy execution tasks pending separate user authorization. |
| A04 | Resolved MAJOR | Language boundary | The initial draft alternated between a Profile, catalog extension, and separate Catalog Entry. | Derive the catalog from Deployment binding → System instance → Component; allow typed runtime data only in one named binding Profile. |
| A05 | Resolved MINOR | Evidence | Fixture lifecycle success could be misreported as legacy compatibility or parity. | Separate fixture, lifecycle, compatibility, parity, and production maturity in FR-020/FR-021 and the acceptance gates. |
| A06 | Resolved ADVISORY | Companion ownership | Component-specific providers belong in xverse-compat. | Track the provider package in T018 without writing companion artifacts in this design-only delivery. |
| A07 | Resolved MAJOR | Plan/permit | The initial scenario required authorization to plan while the contract required it only to execute. | Planning is permit-free; a missing permit sets execution ineligible but does not hide the plan. |
| A08 | Resolved MAJOR | Ownership | Ownership lacked handle, idempotency, concurrency, command-isolation, and restart semantics. | Require provider-issued handles, isolated typed actions, exclusive mutation, idempotent calls, and observation-only reconciliation. |
| A09 | Resolved MAJOR | Evidence failure | The initial contract did not define what happens when evidence persistence fails. | Require durable intent before mutation and evidence-incomplete safe-stop behavior after outcome failure. |
| A10 | Resolved MAJOR | Secrets | The initial draft allowed secret references while excluding secret management. | Catalog visibility remains possible, but secret-dependent planning and execution are blocked in M3. |
| A11 | Resolved MINOR | Artifact reuse | External artifact uniqueness would reject legitimate shared immutable artifacts. | Make catalog identity unique and allow digest-identical artifact sharing without state/ownership merging. |
| A12 | Resolved MINOR | Coverage | Tasks omitted explicit coverage for the repaired safety semantics. | Add dedicated implementation and negative-test tasks T010–T017. |
| A13 | Resolved MAJOR | Candidate representation | The v0.1 Profile forced a nominated candidate with unresolved owner/environment/interface evidence to be either structurally invalid or falsely plannable. | Add Profile v0.2 declared blocker codes, preserve v0.1 fixture behavior, and prove SD-0001 derives one valid but unplannable deterministic plan. |
| A14 | Open MAJOR | Baseline ordering | REF-001 describes S-CORE before the gateway, while the revision-pinned current launcher starts the gateway before S-CORE. Neither source supplies an owner-approved readiness dependency contract. | Preserve both accounts, select neither ordering, and require the target owner to identify the intended baseline and observable prerequisites before closing SD-R04. |
| A15 | Open BLOCKER; strategy selected | Environment coupling | Static audit finds a withheld private Zenoh endpoint compiled into the exact candidate rather than selected configuration. | The user authorized the configurable-rebuild strategy on 2026-09-21 and ADR-0017 records it. Keep the blocker open until a reviewed restricted patch produces a new reproducible artifact in an approved immutable environment; do not infer or override the value in a provider. |
| A16 | Open MAJOR | Wire/lifecycle evidence | Native-memory float encoding, raw reverse bytes, payload-bearing logs, detached work, and absent graceful-stop/readiness APIs make portability, evidence safety, and containment unverified. | Freeze a peer ABI/schema, restricted-log policy, external bidirectional probe, and bounded termination behavior before target implementation/execution. |

## Coverage

| Requirement groups | Task IDs |
|---|---|
| FR-001–FR-006 catalog identity/provenance | T002, T005–T008, T015, T017 |
| FR-007–FR-016 lifecycle safety | T003, T009–T017 |
| FR-017–FR-020 evidence/diagnostics | T004, T006, T012, T014, T017, T021–T022 |
| FR-021–FR-025 gates/repository boundaries | T001, T018–T023 |
| FR-026–FR-033 representation/permit/ownership/recovery | T005–T017 |
| FR-034 legacy-checkout immutability | T003, T017, T019–T022 |
| FR-035 declared planning blockers | T005, T009, T015, T017, T019 |

All functional requirements map to tasks. No clarification marker, implementation authorization, or
legacy target selection is inferred. A01–A03 remain mandatory gates before selected legacy execution;
A04 and A07–A13 record resolved design-review findings. A14–A16 remain external evidence gates and
do not weaken the safety of the currently unplannable candidate. SC-011 is verified under T017/T019.
