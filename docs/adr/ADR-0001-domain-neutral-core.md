# ADR-0001: Domain-neutral core

**Status**: Accepted baseline, adopted by the user's approved setup/M0 plan.
**Date**: 2026-09-20

## Context
Existing automotive implementations are the strongest proving ground, but X-Verse must serve multiple CPS domains.

## Decision
Keep industry-specific semantics in domain profiles, plugins and blueprints. The core uses domain-neutral concepts; M0 does not freeze entity names or implementation types.

## Consequences and alternatives
Reject an automotive-specific platform core. Domain expertise remains usable through explicit specialization.

## Evidence and scope
[Architecture guidance](../architecture/XVERSE_VNEXT_ARCHITECTURE_AND_CODEX_GUIDANCE.md), Sections 3, 8–10, 17, 48.
This records an existing approved principle. It does not approve M1 metamodel/XDL design or M0 findings.
Validation is through the M0 governance, compatibility and documentation checks.
