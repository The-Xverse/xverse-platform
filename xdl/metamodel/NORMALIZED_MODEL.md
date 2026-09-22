# XDL normalized semantic model

**Status**: Approved M2 interface contract and approved capability 004 prototype implementation

The capability 004 reference loader produces a normalized semantic resource only after parse, schema,
reference, and semantic validation succeed. The normalized model is independent of YAML/JSON source
format and contains:

```text
NormalizedResource
  identity: ResourceIdentity(apiVersion, kind, namespace, name)
  revision: SemVer
  provenance: Provenance
  labels: Map<String, String>
  elements: Map<CollectionName, Map<ElementId, NormalizedElement>>
  references: List<ResolvedReference>
  extensions: Map<ProfileIdentity, ValidatedPayload>
  content: KindSpecificContent
  sourceMap: SourceMap        # diagnostic metadata; not semantic identity
```

## Required properties

- Canonical identity is derived, never copied from an author-supplied URI.
- All collection IDs are indexed and unique.
- Every reference records both its authored structure and resolved target identity.
- Extension payloads are paired with the exact compatible Profile used to validate them.
- Numeric values retain explicit units or dimensionless status.
- Time-bearing values retain their TimeDomain and any declared mapping/tolerance.
- Provenance and maturity stay attached to the claim they qualify.
- Source locations are retained for diagnostics but do not affect equality or identity.

## Removed presentation information

Mapping order, comments, whitespace, quote style, YAML anchors/aliases, and scalar presentation do not
affect normalized meaning. Duplicate keys, non-string mapping keys, non-JSON numeric values, and
ambiguous implicit scalar conversions are parse failures rather than normalization choices.

## Prohibited inference

Normalization does not choose providers, locate artifacts, allocate resources, contact assets,
evaluate readiness, execute scenarios, infer units/clocks, upgrade maturity, or repair references.
Those actions belong to later validation, binding, or runtime capabilities with their own specs.

The public Python representation uses frozen dataclasses, tuples, and read-only mappings. Canonical
JSON excludes `sourceMap` by default so equivalent YAML and JSON compare by semantic content.
