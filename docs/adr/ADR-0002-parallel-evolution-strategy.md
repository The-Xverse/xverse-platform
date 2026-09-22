# ADR-0002: Parallel evolution

**Status**: Accepted baseline, adopted by the user's approved setup/M0 plan.
**Date**: 2026-09-20

## Context
Existing initiatives require continuity while the platform architecture evolves.

## Decision
Develop vNext alongside production. Consume existing artifacts and interfaces through external compatibility boundaries and migrate use cases only after parity evidence.

## Consequences and alternatives
Reject a big-bang repository migration or mandatory legacy rewrites. The compatibility layer carries integration knowledge.

## Evidence and scope
[Architecture guidance](../architecture/XVERSE_VNEXT_ARCHITECTURE_AND_CODEX_GUIDANCE.md), Sections 4–5, 25–29, 48.
This records an existing approved principle. It does not approve M1 metamodel/XDL design or M0 findings.
Validation is through the M0 governance, compatibility and documentation checks.
