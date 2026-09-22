# ADR-0003: Legacy immutability

**Status**: Accepted baseline, adopted by the user's approved setup/M0 plan.
**Date**: 2026-09-20

## Context
Production repositories are active assets with existing consumers and deployment behavior.

## Decision
Treat legacy repositories as read-only dependencies unless explicitly authorized for a specific change. M0 uses GitHub GET requests and executes no legacy workloads.

## Consequences and alternatives
Accept documentation/evidence gaps rather than changing sources to simplify discovery. No branches, commits, issues, PRs, CI edits or renames in legacy repositories.

## Evidence and scope
[Architecture guidance](../architecture/XVERSE_VNEXT_ARCHITECTURE_AND_CODEX_GUIDANCE.md), Sections 4, 39–40, 48.
This records an existing approved principle. It does not approve M1 metamodel/XDL design or M0 findings.
Validation is through the M0 governance, compatibility and documentation checks.
