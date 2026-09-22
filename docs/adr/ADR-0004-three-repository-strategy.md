# ADR-0004: Three-repository strategy

**Status**: Accepted baseline, adopted by the user's approved setup/M0 plan.
**Date**: 2026-09-20

## Context
Early fragmentation would obscure ownership and increase coordination costs.

## Decision
Use xverse-platform for core and authoritative architecture, xverse-compat for external integration, and xverse-blueprints for domain experiments. Require a demonstrated independent lifecycle and ADR before adding repositories.

## Consequences and alternatives
Keep M0 specification centralized in platform, with companion setup tracked there. Preserve existing licenses. Internal modules may evolve later; no runtime directories are scaffolded as implemented capabilities.

## Evidence and scope
[Architecture guidance](../architecture/XVERSE_VNEXT_ARCHITECTURE_AND_CODEX_GUIDANCE.md), Sections 6–7, 39, 46.
This records an existing approved principle. It does not approve M1 metamodel/XDL design or M0 findings.
Validation is through the M0 governance, compatibility and documentation checks.
