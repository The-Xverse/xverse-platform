# Tasks: XDL loader, validator, and normalizer

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts](contracts/), and [quickstart.md](quickstart.md)

## Phase 1: Spec Kit and architecture setup

- [X] T001 Create capability 004 specification, clarification, research, data model, plan, contracts, and quickstart.
- [X] T002 Complete the specification quality checklist in `checklists/requirements.md`.
- [X] T003 Record offline loader, static readiness, and resource-wide element identity in `docs/adr/ADR-0013-xdl-loader-validation-boundaries.md`.
- [X] T004 Update approved M2 prose to make element IDs resource-wide without changing v1alpha1 schema shape.

## Phase 2: Package and foundational contracts

- [X] T005 Create `pyproject.toml`, dependency constraints/lock, package metadata, console entry point, and package-data rules.
- [X] T006 Extend `.gitignore` for Python environments, build output, coverage, and test caches.
- [X] T007 [P] Write public frozen models and identities in `src/xverse_xdl/models.py`.
- [X] T008 [P] Write stable diagnostics and source locations in `src/xverse_xdl/diagnostics.py`.
- [X] T009 Write package exports/version in `src/xverse_xdl/__init__.py` and module entry in `__main__.py`.

## Phase 3: User Story 1 — Safe loading and schema validation (P1)

**Independent test**: Valid YAML/JSON parse and schema-check; malformed, duplicate, non-JSON, oversized,
deep, cyclic, multi-document, and unknown-version inputs fail with stable diagnostics.

- [X] T010 [US1] Write failing parser/limit tests in `tests/test_loader.py`.
- [X] T011 [US1] Implement bounded JSON and YAML 1.2 parsing/source maps in `src/xverse_xdl/loader.py`.
- [X] T012 [US1] Write failing core-schema registry tests in `tests/test_schema.py`.
- [X] T013 [US1] Implement packaged Draft 2020-12 registry and kind validation in `src/xverse_xdl/schema.py`.
- [X] T014 [US1] Verify all five approved examples pass parse/schema gates.

## Phase 4: User Story 2 — References, semantics, Profiles, and readiness (P1)

**Independent test**: Duplicate identity, unresolved/wrong references, local semantic errors, invalid
extensions, and incomplete bindings produce expected codes without network or live-system access.

- [X] T015 [US2] Create illustrative Profile schema fixture in `tests/fixtures/measurement-profile.schema.json`.
- [X] T016 [US2] Write failing graph and semantic tests in `tests/test_semantics.py`.
- [X] T017 [US2] Implement resource/element catalogs and reference resolution in `src/xverse_xdl/semantics.py`.
- [X] T018 [US2] Implement Component and System local semantic validation.
- [X] T019 [US2] Implement Deployment, Scenario, time, physical binding, and static readiness validation.
- [X] T020 [US2] Implement Profile ownership, compatibility, local schema registry, and extension payload validation.

## Phase 5: User Story 3 — Immutable normalization (P1)

**Independent test**: Valid graphs normalize immutably; equivalent YAML/JSON yield identical semantic
JSON; any gate 1–4 error returns no partial normalized graph.

- [X] T021 [US3] Write failing normalization/equivalence tests in `tests/test_normalize.py`.
- [X] T022 [US3] Implement recursive freezing, resolved references, extension pairing, element indexes,
  source maps, and canonical JSON in `src/xverse_xdl/normalize.py`.
- [X] T023 [US3] Implement full staged orchestration and immutable ValidationResult in `src/xverse_xdl/validate.py`.
- [X] T024 [US3] Verify no normalization after any gate 1–4 error.

## Phase 6: User Story 4 — Local CLI and automation (P2)

**Independent test**: Validate, normalize, and version commands have stable JSON/text output, status
codes, output safety, and repeatability.

- [X] T025 [US4] Write failing CLI integration tests in `tests/test_cli.py`.
- [X] T026 [US4] Implement `validate`, `normalize`, and `version` in `src/xverse_xdl/cli.py`.
- [X] T027 [US4] Verify reversed input order produces byte-identical diagnostics and normalized semantics.

## Phase 7: Cross-cutting validation and documentation

- [X] T028 Add end-to-end and 25+ negative validation tests in `tests/test_validation.py`.
- [X] T029 Validate wheel contents and editable/locked installs include the authoritative core schemas.
- [X] T030 Measure 100-resource performance and peak RSS in the reference environment.
- [X] T031 Update README, AGENTS, normative validation/normalized-model docs, and package usage.
- [X] T032 Complete `analysis.md`, `validation.md`, and the acceptance checklist.
- [X] T033 Conduct separate read-only architecture review in `docs/reviews/004-xdl-loader-validator-architecture-review.md`.
- [X] T034 Repair review findings in a subsequent pass and rerun the full suite.
- [X] T035 Record human capability 004 review and ADR-0013 disposition.

## Dependencies and execution

T001–T006 establish specification and packaging. T007–T009 establish public contracts. Each story
writes tests before implementation; US2 depends on US1, US3 depends on US1–US2, and US4 depends on
the orchestrated library. T028–T034 validate the complete package. T035 is the human gate before M3.
