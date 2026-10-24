# ADR-0021: Public documentation generated with the platform

**Date**: 2026-10-24
**Status**: Accepted by the user for integration and publication

## Context

X-Verse needs a free open source home page and complete public documentation that evolves with code. Runtime evidence and internal engineering records must not be copied recursively into a public site.

## Decision

Keep an Astro/Starlight site under `website/` in the platform repository. Generate Python API documentation with Sphinx, C++ public header documentation with Doxygen, and field/CLI/example references from canonical source inputs. Use locked dependencies, an explicit publication allowlist, source hashes, offline example checks, whole-artifact link checks, and GitHub Actions/Pages. Narrative guides are reviewed alongside code; generation cannot establish behavior or maturity. Do not expose an execution API or change platform dependencies.

## Consequences

Source changes trigger a fresh reference build. GitHub Pages requires one-time repository configuration and a successful main-branch workflow. Generated references retain their native layouts under the same static site, with shared search indexing and return links. The build needs Node, Python, and Doxygen; runtime use of X-Verse does not acquire those requirements. Publication and main integration follow explicit acceptance of the reviewed candidate.
