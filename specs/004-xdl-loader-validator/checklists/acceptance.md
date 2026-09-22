# Capability 004 acceptance checklist

**Feature**: [XDL loader, validator, and normalizer](../spec.md)
**Status**: Approved — capability 004 accepted on 2026-09-20.

## Automated and documentary evidence

- [X] ACC001 Spec Kit prerequisites resolve capability 004 and all authoring artifacts are complete.
- [X] ACC002 Locked installation and wheel contain the declared package and authoritative schemas.
- [X] ACC003 All unit/integration tests pass with at least 25 negative cases across six gates and limits.
- [X] ACC004 Five approved examples validate and normalize with the local illustrative Profile schema.
- [X] ACC005 YAML/JSON semantic equivalence and input-order determinism pass byte comparisons.
- [X] ACC006 Performance and peak memory satisfy SC-005 with environment evidence.
- [X] ACC007 M0–M2 documentary validators and capability 004 validation pass as applicable.
- [X] ACC008 Separate architecture review has no unresolved BLOCKER or MAJOR finding.
- [X] ACC009 No legacy/companion repository, production workload, or network resolver was changed or run.

## Human review

- [X] ACC010 Approve ADR-0013 and resource-wide element-ID uniqueness.
- [X] ACC011 Approve the closed offline resolution and explicit Profile-schema boundary.
- [X] ACC012 Approve public library/CLI contracts and stable diagnostic format.
- [X] ACC013 Confirm static readiness language does not imply live readiness.
- [X] ACC014 Accept prototype maturity and deferred registry/runtime behavior.
- [X] ACC015 Decide whether M3 may be specified; this does not itself authorize legacy execution.
- [X] ACC016 Record reviewer, date, decision, amendments, and evidence gaps.

## Decision record

**Reviewer**: User, recorded from explicit conversation approval
**Date**: 2026-09-20
**Decision**: Approved. ADR-0013 is accepted and M3 may be specified.
**Amendments / exclusions**: None. Approval does not authorize legacy execution or M3 implementation.
**Evidence gaps**: None within capability 004's stated prototype and static-validation scope.
