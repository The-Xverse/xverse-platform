# Feature Specification: Public documentation website

**Feature Branch**: `021-documentation-website`
**Created**: 2026-10-24
**Status**: Accepted by the user for integration and publication
**Input**: A free open source X-Verse home page and documentation, updated automatically when code changes; user authorized the proposed implementation with “go”.

## User Scenarios & Testing

### User Story 1 — Understand and start using X-Verse (P1)

A visitor learns what X-Verse does, distinguishes the Lite release candidate from future capabilities, and follows a working offline XDL example.

**Independent test**: Open the home page and follow the first-system guide to validate the five example resources.

**Acceptance scenarios**:
1. Given a fresh checkout, a visitor can find installation, concepts, guides, references, and development documentation from the home page.
2. Given a narrow screen or keyboard input, navigation remains usable and content remains readable.
3. Given a Lite capability, its page states its bounded scope and does not imply generalized runtime readiness.

### User Story 2 — Read references derived from code (P1)

A developer finds current Python and C++ signatures, XDL field constraints, CLI options, and examples without manually maintaining duplicate reference material.

**Independent test**: Change a source docstring or schema constraint in a temporary fixture, regenerate, and observe the changed reference; removed generated pages disappear on rebuild.

**Acceptance scenarios**:
1. Code, comments, schemas, and CLI help are the inputs to generated references.
2. Every generation records source revision and input hashes.
3. Missing tools or missing source inputs fail the build instead of publishing partial references.

### User Story 3 — Keep the published site current (P2)

A contributor gets documentation checks on a pull request; a merge to the default branch rebuilds and publishes the checked website.

**Independent test**: Inspect the workflow and build its exact commands locally. Hosted execution is verified separately after repository configuration and acceptance.

**Acceptance scenarios**:
1. Pull requests build and check the website without publication permissions.
2. Main-branch publication depends on successful generation, example checks, and internal-link checks.
3. Project-subpath and root-domain hosting both produce valid internal URLs.

### Edge cases

Missing source, malformed schemas, generator failure, stale generated files, broken anchors, deleted APIs, URL subpaths, absent Git metadata, and references outside the publication allowlist must have explicit outcomes. Offline documentation generation never starts a process provider or a simulation workload.

## Requirements

- **FR-001**: Provide a responsive home page, search, navigation, and accessible documentation.
- **FR-002**: Cover installation, concepts, architecture, XDL resources, validation, experiment compilation, lifecycle, communication, Argus, faults, flows, maturity, and contribution.
- **FR-003**: Generate Python/C++ API reference from admitted public source surfaces.
- **FR-004**: Generate resource/profile schema and CLI references and include actual example files.
- **FR-005**: Build from version-controlled inputs and record their identities in a publication manifest.
- **FR-006**: Fail on missing inputs, invalid examples, generator errors, and broken internal links.
- **FR-007**: Prepare automatic pull-request checking and default-branch publication to free static hosting.
- **FR-008**: Publish only explicitly selected public content; exclude engineering evidence, private source, host paths, and production configuration.
- **FR-009**: Support project-base URLs and custom root URLs without manual content rewrites.
- **FR-010**: Explain that narrative documentation changes accompany code changes; generated signatures do not prove behavior or maturity.

### Key entities

Publication input (path, generator, scope); generated page (route, source); publication manifest (revision, input hashes, output inventory); capability summary (maturity, scope, source).

## Success Criteria

- **SC-001**: All five documentation sections and all FR-002 topics are reachable through navigation.
- **SC-002**: A fresh build has zero broken local links or anchors and validates the supplied five-resource example.
- **SC-003**: Regeneration reflects changed reference inputs and removes obsolete generated outputs.
- **SC-004**: The same source builds under `/` and `/xverse-platform/`.
- **SC-005**: No local host path or raw engineering evidence appears in the published artifact.

## Assumptions

The site lives in `xverse-platform/website`; English is the initial language. The project uses GitHub Pages and a public repository. Existing local changes stay untouched in a separate worktree. Publication and main integration follow repository acceptance rules. No domain purchase or paid service is needed.

## X-Verse capability obligations

Compatibility: additive documentation/build tooling only; no runtime API or schema changes. Failure: a failed build retains the last hosted version. Observable outcome: generated manifest, static HTML, source references, and check reports. Maturity: website candidate; hosted automatic deployment unverified until enabled. Runtime obligations are inapplicable because this capability neither executes experiments nor changes runtime behavior.

REF-002 allocation: this is documentation infrastructure, not a SADS runtime subsystem. Existing SADS runtime/UI/SDK requirements remain allocated to their current owners; none is implemented by a static website. The traceability assessment in `research.md` records the relevant IDs and boundary. Separate read-only review and explicit user acceptance precede integration/publication.
