# Tasks: Doxygen Code Documentation

**Input**: Design documents from `specs/006-doxygen-code-documentation/`

## Phase 1: Setup

- [X] T001 Point Spec Kit at this feature and verify prerequisites.
- [X] T002 Add root `Doxyfile` with deterministic, warning-clean HTML settings.
- [X] T003 Add the authored `docs/doxygen/mainpage.md` architecture and maturity overview.

## Phase 2: Coverage gate

- [X] T004 Add `scripts/check_doxygen.py` to enforce production docstrings and generated output.
- [X] T005 Verify the checker fails against a temporary undocumented source fixture.

## Phase 3: Production package documentation

- [X] T006 [US1] Document package exports, data models, diagnostics, and CLI behavior.
- [X] T007 [US1] Document loader, schema, semantic validation, normalization, and orchestration.
- [X] T008 [US1] Document catalog derivation, lifecycle permits, evidence, providers, and controller behavior.

## Phase 4: Supporting code and navigation

- [X] T009 [US1] Document reusable validation and benchmark scripts.
- [X] T010 [US3] Include tests in Doxygen source navigation and describe their documentation policy.
- [X] T011 [US1] Add README generation, validation, and output navigation instructions.

## Phase 5: Validation and review

- [X] T012 Run the docstring coverage and warning-clean Doxygen build.
- [X] T013 Run the full existing Python test suite and M3 public fixture validation.
- [X] T014 Check generated coverage, links, placeholders, maturity claims, and public safety.
- [X] T015 Conduct and record a separate documentation architecture review.
- [X] T016 Record final validation evidence and complete the acceptance checklist.

## Dependencies

T001 precedes all work. T002-T003 precede T004 and generated-output checks. T004 precedes T006-T010
so missing coverage is measurable. T006-T011 precede validation; T012-T014 precede review; T015
precedes final acceptance evidence.
