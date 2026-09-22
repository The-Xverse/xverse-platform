# Tasks: M0 legacy repository inventory

## Phase 1 — Setup
- [x] T001 Initialize official Spec Kit assets in `.specify/` across all three vNext repositories.
- [x] T002 Establish synchronized `.specify/memory/constitution.md` files and aligned templates.

## Phase 2 — Specification foundation
- [x] T003 Write `spec.md`, `clarifications.md`, and `checklists/requirements.md` in this feature directory.
- [x] T004 Run official planning setup and write `plan.md`, `research.md`, `data-model.md`, and `quickstart.md` here.
- [x] T005 Generate `tasks.md` here using the official tasks workflow and run the read-only consistency analysis.

## Phase 3 — US1: engineering governance
Independent validation: all three repositories have consistent setup and preserved original files.
- [x] T006 [US1] Add repository-specific `AGENTS.md`, `README.md`, and `.gitignore` across the three repositories.
- [x] T007 [US1] Copy unchanged guidance into `docs/architecture/` in xverse-platform.
- [x] T008 [US1] Record ADR-0001 through ADR-0004 in `docs/adr/`.

## Phase 4 — US2: evidence-backed inventory
Independent validation: reconcile every enumerated repository and all 15 fields against pinned sources.
- [x] T009 [US2] Capture organization/revision/source coverage in `docs/legacy/inventory-snapshot.json` using read-only APIs.
- [x] T010 [US2] Inspect manifests, interfaces, documentation, and startup sources; author `docs/legacy/REPOSITORY_INVENTORY.md`.
- [x] T011 [US2] Record evidence-backed relationships and cruise-control startup in `docs/legacy/DEPENDENCY_MAP.md`.
- [x] T012 [US2] Summarize communication/input-output contracts and gaps in `docs/legacy/INTERFACE_CATALOG.md`.
- [x] T013 [US2] Record classifications and compatibility candidates in `docs/legacy/MIGRATION_CLASSIFICATION.md`.

## Phase 5 — US3: review readiness
Independent validation: reproducible checks plus a review package that retains the human M1 gate.
- [x] T014 [US3] Add and run `scripts/validate_m0.py` for coverage, evidence, links, original hashes, and consistency.
- [x] T015 [US3] Run negative validation scenarios and record results in this feature's `validation.md`.
- [x] T016 [US3] Conduct a separate read-only review and write `docs/reviews/001-legacy-repository-inventory-architecture-review.md`.
- [x] T017 [US3] Record the boundary/interface/dependency human review checklist in `docs/reviews/M0_REVIEW_CHECKLIST.md`.

## Phase 6 — Completion
- [x] T018 Verify public-safe content, preservation, and final diffs; complete `checklists/acceptance.md` and `validation.md` here.
- [x] T019 Update this feature's `spec.md` status and `tasks.md` with actual delivery outcomes; keep human sign-off pending.

## Dependencies and execution strategy
T001 → T002 → T003 → T004 → T005; setup is the first independently useful increment.
T006–T008 establish governance; T009–T010 supply evidence for T011–T013; T014–T019 validate and review.
T006/T007 are already completed setup actions recorded here, not claims that inventory implementation
preceded the consistency analysis. T009 collection began as read-only research; the versioned evidence
snapshot is produced during implementation.

Independent opportunities: companion setup can be checked independently (US1); repository reads can
be batched after pinning revisions (US2); link and preservation checks can be evaluated independently
(US3). This delivery uses one agent with separate authoring/review passes; no delegation is required.

Mapping: FR-001 T001/T014; FR-002 T002/T006/T008; FR-003 T009/T014; FR-004 T010/T014;
FR-005 T011–T013; FR-006 T010–T018; FR-007 T009/T018; FR-008 T014–T018; FR-009 T016/T019.

## Subsequent confirmation and reference intake
- [x] T020 Record the user's M0 confirmation in `docs/reviews/M0_REVIEW_CHECKLIST.md`, register supplied references in `docs/architecture/REFERENCE_REGISTER.md`, synchronize status and validate documentary links and original source hashes.

T020 extends FR-006/FR-008 documentation and review traceability; it does not implement M1.
