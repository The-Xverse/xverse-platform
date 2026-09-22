# Capability 004 validation record

**Date**: 2026-09-20
**Scope**: Prototype XDL v1alpha1 loader, validator, normalizer, local CLI, package, and documentation.
**Result**: Pass — user approved capability 004 and ADR-0013 on 2026-09-20.

## Executed checks

| Check | Result | Evidence |
|---|---|---|
| Spec Kit prerequisites | Pass | `check-prerequisites.sh --json --require-tasks --include-tasks` resolved `specs/004-xdl-loader-validator` and its research, data model, contracts, quickstart, and tasks. |
| Locked environment | Pass | `uv sync --frozen` checked the 19 locked packages without changing the lock. |
| Unit and integration suite | Pass | 64 tests pass; `NegativeValidationTests` contains 30 focused failure cases across parsing, schemas, references, semantics, binding/readiness, policy, and limits. |
| Approved graph | Pass | Five M2 examples validate and normalize with the explicit illustrative Profile schema; the CLI reports `valid: 5 resource(s)`. |
| Determinism and immutability | Pass | YAML/JSON semantic equivalence, reversed input ordering, read-only mappings, source-map exclusion, and no-partial-normalization tests pass. |
| Capability validator | Pass | `scripts/validate_xdl_loader.py` confirms five resources, seven authoritative schemas, no network-capable source import, complete artifacts, and deterministic normalization. |
| Performance | Pass | Final run over 100 generated resources: 0.139009 seconds and 25.75 MiB peak RSS on CPython 3.13.13, Linux 6.8.0-138-generic-x86_64; limits are 2 seconds and 128 MiB. |
| Package build | Pass | `uv build` produced the sdist and universal wheel; isolated inspection/import found ten Python modules and all seven schemas. |
| Syntax and hygiene | Pass | `compileall`, trailing-whitespace scan, template-marker checks, and `git diff --check` pass. |
| Architecture review and acceptance | Pass | Separate review 004-R01–004-R06 was recorded before repair; all findings are resolved, and the user approved capability 004 and ADR-0013 on 2026-09-20. |
| M1/M2 regression | Pass | M1 still confirms 26 concepts/four ADRs; M2 confirms seven schemas, five examples, and eight negative documentary self-tests. |
| M0 regression | Pass with expected pointer exception | M0 package checks differ only at the historical feature-pointer assertion because Spec Kit correctly points to capability 004. No M0 artifact or companion repository changed. |
| Repository/runtime boundary | Pass | Changes are confined to `xverse-platform`; no legacy or companion repository, workload, target, artifact endpoint, or network resolver was changed or run. |

## Acceptance interpretation

These checks establish bounded local parsing, standards-based structural validation, closed-set
reference and semantic validation, selected static readiness, immutable normalization, deterministic
reporting, and installable package contents. They do not establish live readiness, runtime execution,
legacy compatibility, Profile registry governance, artifact retrieval, orchestration, or production
service behavior.

The user approved ADR-0013, resource-wide element identity, offline resolution, public interfaces,
diagnostic shape, static-readiness language, and prototype maturity. M3 may now be specified. This
approval does not authorize M3 implementation or any legacy execution.
