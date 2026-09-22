# Tasks: M2 XDL Core v0.1

**Input**: [spec.md](spec.md), [clarifications.md](clarifications.md), [research.md](research.md),
[data-model.md](data-model.md), and [plan.md](plan.md).
**Scope**: specification, schemas, examples, and documentary validation only.

## Phase 1: Feature setup

- [X] T001 Point `.specify/feature.json` to `specs/003-xdl-core`.
- [X] T002 Define user stories, requirements, success criteria, and exclusions in `spec.md`.
- [X] T003 Resolve packaging, identity, serialization, extension, versioning, and validation choices in `clarifications.md`.

## Phase 2: Research and design foundation

- [X] T004 Record standards research and rejected alternatives in `research.md`.
- [X] T005 Define the resource envelope, references, resource roles, and normalized resource in `data-model.md`.
- [X] T006 Define the complete execution and verification plan in `plan.md` and `quickstart.md`.
- [X] T007 Record the five-resource packaging decision in `docs/adr/ADR-0009-xdl-resource-model.md`.
- [X] T008 Record identity/version decisions in `docs/adr/ADR-0010-xdl-identity-and-versioning.md`.
- [X] T009 Record YAML/JSON/JSON Schema decisions in `docs/adr/ADR-0011-xdl-serialization-and-schema.md`.
- [X] T010 Record extension and external-standards decisions in `docs/adr/ADR-0012-xdl-extensions-and-standards.md`.

## Phase 3: User Story 1 — Describe a logical system (P1)

**Independent test**: the System example passes structural and semantic checks with all local and
cross-resource references resolved and no realization data.

- [X] T011 [US1] Define the normative core and System semantics in `xdl/specification/XDL_CORE_V0_1.md`.
- [X] T012 [US1] Define common types and strict System structure in `common.schema.json` and `system.schema.json`.
- [X] T013 [US1] Create a public-safe logical System example in `system.xdl.yaml`.

## Phase 4: User Story 2 — Bind a realization overlay (P1)

**Independent test**: the Deployment example resolves its System, logical element, target, artifact,
resource, and lifecycle/readiness obligations without changing logical identity.

- [X] T014 [US2] Define Deployment ownership and readiness semantics in the normative specifications.
- [X] T015 [US2] Define strict Deployment structure in `deployment.schema.json`.
- [X] T016 [US2] Create a public-safe simulated Deployment example in `deployment.xdl.yaml`.

## Phase 5: User Story 3 — Define a reproducible experiment (P2)

**Independent test**: Scenario steps, targets, clocks, observers, metrics, units, evidence sinks, and
acceptance intent resolve without claiming execution.

- [X] T017 [US3] Define Scenario and evidence semantics in the normative specifications.
- [X] T018 [US3] Define strict Scenario structure in `scenario.schema.json`.
- [X] T019 [US3] Create a public-safe Scenario example in `scenario.xdl.yaml`.

## Phase 6: User Story 4 — Reuse components and extensions (P2)

**Independent test**: the Component and Profile examples pass validation and a namespaced extension
resolves to the compatible Profile.

- [X] T020 [US4] Define Component, Profile, and extension ownership in `RESOURCE_MODEL.md`.
- [X] T021 [US4] Define Component and Profile schemas.
- [X] T022 [US4] Create cross-referenced Component and Profile examples.
- [X] T023 [US4] Add the aggregate `xdl.schema.json` dispatcher.

## Phase 7: User Story 5 — Evolve XDL safely (P2)

**Independent test**: version dimensions, validation gates, normalization, strict unknown-field
behavior, and conversion deferral are explicit and consistent.

- [X] T024 [US5] Define validation gates and diagnostics in `VALIDATION.md`.
- [X] T025 [US5] Define version compatibility in `VERSIONING.md`.
- [X] T026 [US5] Define normalization in `NORMALIZED_MODEL.md`.
- [X] T027 [US5] Implement documentary schema/example checks and eight negative self-tests in `scripts/validate_m2.py`.

## Phase 8: Quality and architecture review

- [X] T028 Complete the requirements checklist and cross-artifact analysis.
- [X] T029 Run prerequisites, schema/example validation, negative tests, syntax, and whitespace checks; record evidence in `validation.md`.
- [X] T030 Conduct and record a separate architecture review in `docs/reviews/003-xdl-core-architecture-review.md`.
- [X] T031 Update repository maturity/boundary documentation for the proposed M2 package.
- [X] T032 Record human disposition of ADR-0009–ADR-0012 and the M2 review checklist.

## Dependencies and handoff

T001–T010 establish decisions. US1 and US2 define the logical/realization split; US3 and US4 add
experiment and extension resources; US5 governs evolution. T028–T031 make the package reviewable.
T032 is complete. Loader/validator implementation, runtime planning, adapters, catalogs, blueprints,
and legacy integration require later separately approved features.
