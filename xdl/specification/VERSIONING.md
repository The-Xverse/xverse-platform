# XDL v1alpha1 versioning and compatibility

**Status**: Approved M2 specification

XDL keeps four version dimensions separate:

| Dimension | Location | Meaning |
|---|---|---|
| API/schema version | `apiVersion` | Syntax and semantic contract understood by a processor. |
| Resource revision | `metadata.version` | Revision of one resource's authored content. |
| Profile revision | Profile `metadata.version` and schema reference | Revision of an extension vocabulary. |
| Artifact/model version | Deployment artifact or Model fields | Revision of externally governed material. |

A match in one dimension implies nothing about another. In particular, a v1alpha1 document can
reference incompatible artifact revisions, and two revisions of a resource can use the same API.

## API recognition

A v1alpha1 consumer MUST recognize the exact string `xverse.io/xdl/v1alpha1`. It MUST reject an
unknown API version rather than guessing compatibility. `v1alpha1` is an alpha contract: the project
may introduce breaking changes through a new API version, but MUST NOT silently change the meaning of
the existing identifier.

A breaking change includes removing or renaming a field, changing a field's meaning or type,
weakening an invariant, changing identity/reference behavior, changing default behavior, or accepting
previously invalid documents in a way that changes their meaning. Breaking changes require a new API
version and an explicit conversion decision. Conversion behavior is deferred.

Additive optional schema fields are also deferred from v1alpha1 because strict unknown-field rejection
means older consumers would reject them. Extension Profiles are the supported experimentation path.

## Resource revisions

`metadata.version` uses Semantic Versioning syntax. It expresses author intent for one resource and
does not override the API compatibility rules. A resource publisher SHOULD increment:

- MAJOR for incompatible changes to the resource's declared contract;
- MINOR for backward-compatible capabilities within the same identity; and
- PATCH for corrections that preserve the declared contract.

These increments are claims that require review; XDL does not infer them from a diff.

## External artifacts and profiles

Artifact and model versions follow their governing ecosystem. Reproducible bindings SHOULD include an
immutable digest or pinned revision in addition to a human version. Profile compatibility lists exact
XDL API versions. A Profile revision can evolve independently, but a resource using its namespace must
resolve a compatible revision before semantic validation succeeds.

## Canonical identity stability

Resource version is not part of canonical identity. Updating `metadata.version` creates a new revision
of the same logical resource. Changing namespace, kind, or name creates a different identity. Element
IDs are stable within the owning resource identity; renaming one creates a different element unless a
future migration specification defines an explicit mapping.
