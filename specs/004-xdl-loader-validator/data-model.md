# Data model: XDL loader, validator, and normalizer

## Pipeline

```text
SourceInput
  → ParsedDocument
  → SchemaValidResource
  → ResourceCatalog + ProfileSchemaCatalog
  → ResolvedResourceGraph
  → SemanticallyValidGraph
  → NormalizedResourceSet

Each transition emits ordered Diagnostic values.
Any error at a gate prevents later transitions for the complete set.
```

## Entities

### SourceInput

Immutable source name, raw UTF-8 bytes, detected format, and configured limits. Format is selected by
`.json`, `.yaml`, or `.yml`; unknown suffixes use content detection only when unambiguous.

### ParsedDocument

JSON-compatible mapping plus a pointer-to-SourceLocation map. It retains no parser-specific executable
objects. YAML comments, anchors, aliases, and styles do not enter semantic content.

### ResourceIdentity

Fields: `api_version`, `kind`, `namespace`, `name`. Ordering is lexical across the tuple. Canonical URI:
`xdl://<namespace>/<lowercase-kind>/<name>`. Resource version is not part of identity.

### ElementIdentity

Fields: ResourceIdentity plus `element_id`. Canonical URI appends `#<element-id>`. Element IDs are
unique across all ID-bearing collections in one resource.

### Diagnostic

Fields: `code`, `gate`, `severity`, optional resource URI, pointer, source location, message, correction,
and related identities. Sort key: gate ordinal, resource URI, pointer, code, message, source name.
Diagnostics are immutable and JSON serializable.

### ResourceCatalog

Closed mapping from ResourceIdentity to schema-valid parsed resource. Duplicate identities are errors.
Element indexes map each resource-wide ID to collection and value; any collision is an error.

### ProfileSchemaCatalog

Closed mapping from absolute schema `$id` to local Draft 2020-12 schema. A Profile's `schemaRef` must
match one key exactly. Profile extension namespace ownership must also be unique.

### ResolvedReference

Fields: authored pointer, reference fields, resolved ResourceIdentity, optional ElementIdentity, and
target collection. It contains no live object pointer in canonical output.

### StaticReadiness

Enum: `Ready`, `NotReady`, `NotEvaluated`. `Ready` means all statically declared requirements can be
resolved; it is never evidence of a live target. Reasons are diagnostics at gate 5.

### NormalizedResource

Immutable fields mirror the approved normalized-model contract: identity, revision, provenance,
labels, elements grouped by collection, resolved references, extensions paired with Profile identity,
kind content, and source map. Canonical semantic JSON excludes source map and uses stable key order.

### ValidationResult

Immutable tuple of diagnostics, normalized resources (empty unless gates 1–4 pass for all input), and
readiness by Deployment identity. `is_valid` is true only when no error diagnostic exists.

## Validation state transitions

| State | Entry condition | Exit on success | Exit on error |
|---|---|---|---|
| Parse | Bounded source inputs | JSON-compatible documents | Diagnostics; stop |
| Schema | Every input parsed | Kind-schema-valid resources | Diagnostics; stop |
| Reference | Unique resource/element catalogs | Resolved graph | Diagnostics; stop |
| Semantic | References resolved | Semantically valid graph | Diagnostics; stop |
| Normalize | Gates 1–4 passed | Immutable normalized set | Internal error diagnostic; no partial set |
| Binding/readiness | Normalized set exists | Static readiness results | NotReady diagnostics |
| Policy | Prior applicable gates reached | Accepted result | Policy diagnostics |

Policy includes compatible Profile ownership and local Profile-schema availability. Extension payload
schema checks occur before normalization because validated extensions are required in normalized data.
