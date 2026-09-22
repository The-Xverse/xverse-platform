# Capability 004 architecture review — XDL loader, validator, and normalizer

**Date**: 2026-09-20
**Scope**: Capability 004 specification, ADR-0013, Python package, CLI, tests, packaging, and current documentation.
**Review method**: Separate read-only pass after the first complete implementation and passing test suite.
**Disposition**: Approved by the user on 2026-09-20; no unresolved finding.

## Architecture gates

| Concern | Assessment |
|---|---|
| Domain neutrality | Pass: the package and diagnostics contain no industry or provider behavior. |
| Closed offline operation | Pass: core schemas are packaged and Profile schemas are explicit local inputs; imports contain no network client. |
| Logical/realization separation | Pass: strict typed structure protects the boundary while open domain payloads remain opaque. |
| Determinism and immutability | Pass: identities, diagnostics, normalized resources, collection storage, and canonical JSON are ordered and immutable at the public boundary. |
| Failure semantics | Pass: ordered gates fail closed, and core schema validation precedes Profile policy validation. |
| Input safety | Pass with a repair already applied before this review: file size, depth, node, resource, duplicate-key, cycle, UTF-8, YAML-version, and input/output collision controls are tested. |
| Maturity and production safety | Pass: the package is alpha/prototype, evaluates static declarations only, and does not execute or modify a legacy or production system. |

## Findings recorded for the subsequent repair pass

**BLOCKER**: none.

| ID | Severity | Finding / impact | Disposition |
|---|---|---|---|
| 004-R01 | Resolved MAJOR | Reference and extension discovery walked every mapping by shape, so opaque payload keys could be mistaken for XDL structure. | Replaced with kind/schema-defined reference and extension iterators; an opaque-parameter regression passes. |
| 004-R02 | Resolved MAJOR | Profile schemas loaded before core resource schema validation and could conceal a gate-2 resource error. | Core schemas now run before Profile policy loading; the explicit gate-order regression passes. |
| 004-R03 | Resolved MINOR | Logical/realization leakage detection inferred semantics from generic keys inside opaque payload maps. | Typed-structure traversal now skips open payload locations while strict core schemas protect typed locations. |
| 004-R04 | Resolved MINOR | README, engineering boundary text, and M2 normalized/validation documents still said no loader implementation existed. | Updated to identify the prototype while retaining static-readiness and deferred-runtime limits. |
| 004-R05 | Resolved MINOR | The library contract named an in-memory argument not exposed by the implementation. | Contract now documents resource byte pairs and explicit local `profile_schema_paths`. |
| 004-R06 | Resolved ADVISORY | Normalization imported a private generic walker from the semantic module. | Normalization now consumes the intentional schema-defined extension-container interface. |

## Review checklist

- [X] Loader bounds, parser behavior, schema registry, and resolver isolation reviewed.
- [X] All schema-defined ResourceRef, ElementRef, extension, and local-ID relationships sampled against implementation.
- [X] Gate ordering and partial-normalization behavior reviewed.
- [X] Static readiness language and absence of live operations reviewed.
- [X] Immutability, canonical ordering, CLI status/output, and package contents reviewed.
- [X] Domain neutrality, repository boundaries, legacy immutability, and deferred capabilities reviewed.
- [X] Repair findings 004-R01 through 004-R06 and rerun the complete evidence suite.
- [X] Obtain human decision on ADR-0013 and capability 004 acceptance items.

## Post-review evidence

The subsequent repair pass completed with 64 passing tests, including 30 focused negative validation
cases. The capability validator confirmed five normalized examples and seven packaged schemas without
network imports. The final 100-resource benchmark completed in 0.139009 seconds with 25.75 MiB peak RSS on
CPython 3.13.13/Linux, below the two-second and 128 MiB acceptance bounds. The locked environment,
rebuilt wheel, isolated wheel import, CLI example, M1 regression, and M2 documentary self-tests pass.

## Human-review boundary

The user accepted capability 004 and ADR-0013 on 2026-09-20 and authorized M3 specification. This
decision does not establish live readiness, authorize M3 implementation or legacy execution, or claim
compatibility with legacy execution.
