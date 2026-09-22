# Tasks: M1 domain-neutral metamodel

**Input**: [spec.md](spec.md), [clarifications.md](clarifications.md), [research.md](research.md),
[data-model.md](data-model.md), and [plan.md](plan.md).
**Scope**: architecture documentation only; no runtime implementation.

## Phase 1: Feature setup

- [X] T001 Create the M1 feature directory and feature pointer in \`.specify/feature.json\`.
- [X] T002 Write the scope, scenarios, requirements, success criteria, and capability obligations in \`specs/002-domain-neutral-metamodel/spec.md\`.
- [X] T003 Record bounded architectural defaults and deferred decisions in \`specs/002-domain-neutral-metamodel/clarifications.md\`.

## Phase 2: Architecture foundation

- [X] T004 Trace architectural constraints and M0 evidence limits in \`specs/002-domain-neutral-metamodel/research.md\`.
- [X] T005 Define aggregate relationships and invariants in \`specs/002-domain-neutral-metamodel/data-model.md\`.
- [X] T006 Define every core concept and cross-cutting semantic rule in \`docs/architecture/METAMODEL.md\`.
- [X] T007 Create the conceptual relationship diagram in \`docs/architecture/METAMODEL_DIAGRAM.md\`.

## Phase 3: User Story 1 — Define a domain-neutral system (P1)

**Goal**: supply a complete neutral core vocabulary.

**Independent test**: every required concept has complete definition fields and no profile term is a
core dependency.

- [X] T008 [US1] Define logical System, Component, Node, Device, Sensor, and Actuator semantics in \`docs/architecture/METAMODEL.md\`.
- [X] T009 [US1] Define Interface, Endpoint, Flow, Network, Link, and Protocol semantics in \`docs/architecture/METAMODEL.md\`.
- [X] T010 [US1] Define Model, Artifact, Parameter, Resource, and ComputeResource semantics in \`docs/architecture/METAMODEL.md\`.
- [X] T011 [US1] Record the core-vocabulary decision in \`docs/adr/ADR-0005-domain-neutral-metamodel-core.md\`.

## Phase 4: User Story 2 — Bind without identity loss (P1)

**Goal**: make realization explicit and portable.

**Independent test**: the diagram and text have Deployment as the sole logical-to-realization binding.

- [X] T012 [US2] Define ExecutionTarget, Simulator, Deployment, and realization constraints in \`docs/architecture/METAMODEL.md\`.
- [X] T013 [US2] Record identity/realization binding decision in \`docs/adr/ADR-0006-logical-identity-and-realization-binding.md\`.
- [X] T014 [US2] Validate logical/realization separation in \`scripts/validate_m1.py\`.

## Phase 5: User Story 3 — Define observable experiments (P2)

**Goal**: define semantic lifecycle, time, fault, observation, and metric concepts.

**Independent test**: scenarios disclose time, target, evidence, and failure conditions without a
runtime implementation claim.

- [X] T015 [US3] Define Scenario, TimeDomain, Clock, Fault, Observer, and Metric semantics in \`docs/architecture/METAMODEL.md\`.
- [X] T016 [US3] Record lifecycle/time/evidence decision in \`docs/adr/ADR-0007-lifecycle-time-and-evidence-semantics.md\`.

## Phase 6: User Story 4 — Govern extension and later work (P2)

**Goal**: preserve a stable core while allowing profiles and standards bindings.

**Independent test**: extension rules and deferrals are explicit and all major M1 choices have ADRs.

- [X] T017 [US4] Define namespace/profile rules and standards position in \`docs/architecture/METAMODEL.md\`.
- [X] T018 [US4] Record profile-extension boundary decision in \`docs/adr/ADR-0008-profile-extension-boundaries.md\`.
- [X] T019 [US4] Write M1 validation and review instructions in \`specs/002-domain-neutral-metamodel/quickstart.md\`.

## Phase 7: Quality and architecture review

- [X] T020 Create specification and acceptance checklists in \`specs/002-domain-neutral-metamodel/checklists/\`.
- [X] T021 Generate cross-artifact consistency analysis in \`specs/002-domain-neutral-metamodel/analysis.md\`.
- [X] T022 Implement documentary validation and negative checks in \`scripts/validate_m1.py\`.
- [X] T023 Run M1 validation and record results in \`specs/002-domain-neutral-metamodel/validation.md\`.
- [X] T024 Conduct the separate read-only architecture review in \`docs/reviews/002-domain-neutral-metamodel-architecture-review.md\`.
- [X] T025 Render the conceptual diagram as a standalone SVG in \`docs/architecture/METAMODEL_DIAGRAM.svg\` and retain Mermaid as editable source.
- [X] T026 Record human M1 review approval and ADR disposition in \`specs/002-domain-neutral-metamodel/checklists/acceptance.md\`.

## Dependencies and handoff

T001–T007 establish the package. US1 and US2 then provide the core and realization model; US3 and
US4 depend on those shared terms. T020–T025 validate the completed documentation. T026 records the
approved human review gate.

**Result**: T001–T026 complete. M2 may begin as a separate Spec Kit specification/design capability.
