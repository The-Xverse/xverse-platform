# Implementation Plan: M0 legacy inventory

**Branch**: `main` (unchanged); Spec Kit feature key: `001-legacy-repository-inventory`
**Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

## Summary
Initialize the three vNext repositories, then build a public-safe, revision-pinned inventory of
all accessible legacy repositories. Read-only GitHub discovery is the only legacy interaction.

## Technical Context
**Language/Version**: Markdown/JSON; Python 3 standard library for documentary validation.
**Primary Dependencies**: installed Spec Kit 0.14.0, Bash, Git, authenticated GitHub CLI.
**Storage**: versioned public-safe documentation; raw private evidence outside repository trees.
**Testing**: Spec Kit prerequisites, document/evidence validation, manual semantic and privacy review.
**Target Platform**: current Linux workspace; sibling vNext checkouts.
**Project Type**: documentation and engineering setup, with no application runtime.
**Performance Goals**: none; bounded API reads with explicit error reporting.
**Constraints**: legacy immutability, public-safe outputs, local changes only, read-only agent directories.
**Scale/Scope**: organization snapshot; currently 29 legacy and 3 vNext repositories, refreshed during M0.

## Constitution Check
Pass: implementation limited to three new repositories; no production workloads. Domain language
is confined to inventory observations. ADR-0001–0004 record existing approved principles. XDL and
runtime contracts remain deferred. Maturity and evidence gaps are explicit. Documentation-only
runtime tests are not applicable. Recheck these gates during final review.

## Project Structure
- All three repositories: official `.specify` assets, constitution, `AGENTS.md`, README, ignore rules.
- Platform: authoritative architecture guidance, four initial ADRs, this feature, four legacy reports,
a sanitized evidence snapshot, documentation validator, and a separate architecture review.
- Raw evidence: private temporary directory outside repositories; never copied into deliverables.

## Execution
1. Apply the approved governance and companion-repository setup.
2. Enumerate repositories with pagination; resolve each default branch to a commit and inspect its
recursive tree. Treat empty repositories and truncated/error responses explicitly.
3. Read relevant README, manifest, interface, and startup sources at the selected revision. Expand
inspection where dependencies or cruise-control behavior cannot be established from initial sources.
4. Author public-safe summaries for all 15 required fields. Every source-backed statement cites
pinned evidence; inferences and unknowns have visible labels. Do not expose raw source or addresses.
5. Record dependencies, interface summaries, compatibility candidates, and source limitations.
6. Validate coverage, references, preservation, privacy, and maturity. Review the result in a separate
read-only pass and record findings before any subsequent correction pass.

## Public interfaces and data
No runtime APIs, types, schemas, protocol identifiers, or deployment behavior change. The documentary
record model is in [data-model.md](data-model.md). It is not an XDL representation or platform API.

## Failure semantics
Retry transient API reads; record persistent errors and restricted evidence as coverage gaps.
Never claim absent runtime behavior from a missing README, and never equate source presence with
successful execution. No automatic fallback to unpinned local working-tree evidence.

## Validation and handoff
Use [quickstart.md](quickstart.md), record actual results, and complete the acceptance checklist.
M0 can be ready for inventory review while legacy runtime/deployed-version uncertainties remain;
such gaps must constrain M1 explicitly. No human sign-off is inferred and no M1 implementation starts.

## Complexity Tracking
No constitutional exceptions. A standard-library document validator checks evidence consistency;
there is no new application toolchain, CI deployment, or runtime framework.
