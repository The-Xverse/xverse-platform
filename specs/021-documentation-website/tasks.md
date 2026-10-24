# Tasks: Public documentation website

## Setup and foundations

- [x] T001 Establish authorization/baseline and isolated worktree; write `spec.md` and checklist.
- [x] T002 Record design in `plan.md`, `research.md`, `data-model.md`, `contracts/publication.md`, and ADR-0021.
- [x] T003 Configure pinned website and reference environments in `website/package.json` and `website/reference/`.

## US1 — Home page and documentation

- [x] T004 [US1] Build responsive `website/src/pages/index.astro` and shared visual styles.
- [x] T005 [US1] Author navigation and complete topic guides under `website/src/content/docs/docs/` with honest Lite maturity.

## US2 — Code-derived references

- [x] T006 [US2] Implement generation, schema/CLI/example references, and provenance in `website/scripts/generate.py`.
- [x] T007 [US2] Configure Sphinx public package exports and C++ header-only Doxygen output.
- [x] T008 [US2] Verify meaningful generator negative/mutation cases in `website/tests/` and offline examples.

## US3 — Automatic publication

- [x] T009 [US3] Add checked root/subpath builds and internal-link validation in `website/scripts/check_site.py`.
- [x] T010 [US3] Prepare `.github/workflows/website.yml` with separate check/deploy permissions.
- [x] T011 [US3] Document local maintenance, code/doc workflow, Pages setup, and publication boundaries in `website/README.md`.

## Review and evidence

- [ ] T012 Record candidate inventory, tool versions, command outputs, and verification evidence under this feature.
- [ ] T013 Conduct separate read-only review, record findings, repair later if required, repeat affected verification.

Dependencies: T001–T003 precede US1/US2; T006–T008 precede T009–T010; all implementation precedes evidence/review. Independent content inventory research may run alongside setup; file mutations remain owned by the implementing agent. Acceptance/integration/publication are subsequent user decisions and are not checked implementation tasks.
