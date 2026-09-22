# ADR-0010: XDL identity and version dimensions

**Status**: Accepted — user approved M2 on 2026-09-20.
**Date**: 2026-09-20

## Context

XDL must keep logical identity stable across deployments and avoid confusing language compatibility,
resource revision, profile revision, and artifact revision. Implicit namespace/path rules would make
references environment-dependent.

## Decision

Resource identity is the tuple API version, kind, namespace, and name. Element identity adds its
owning resource and element ID. References are structured objects with every identity field present.
The derived display form is `xdl://namespace/kind/name#element`. API/schema version, resource SemVer,
Profile revision, and artifact/model version remain independent. Consumers recognize the exact
`xverse.io/xdl/v1alpha1` API; incompatible semantics require a new API version and an explicit future
conversion decision.

## Consequences and alternatives

References are verbose but deterministic and portable. Resource revision is deliberately excluded
from logical identity. Filesystem paths, current-namespace defaults, provider handles, network
addresses, and mutable artifact tags were rejected as semantic identity.

## Evidence and scope

Guidance sections 16, 21, 26, 31, 34, and 42; ADR-0006; M2 FR-004, FR-005, and FR-013–FR-015.
Conversion algorithms, registries, signatures, and canonical byte serialization are deferred.
