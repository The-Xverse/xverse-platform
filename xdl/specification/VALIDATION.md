# XDL v1alpha1 validation contract

**Status**: Approved M2 contract and approved capability 004 reference implementation

Validation is ordered. A later gate MUST NOT repair, reinterpret, or conceal an earlier failure.
Passing one gate makes no claim about later gates.

| Gate | Required checks | Success result |
|---|---|---|
| 1. Parse | YAML 1.2.2 or JSON; mapping root; string keys; no duplicate keys; JSON-compatible values | Parsed resource plus source locations |
| 2. Schema | Exact API/kind; required fields; types, patterns, enums; no unknown core fields | Structurally conforming resource |
| 3. Reference | Resource availability; element existence and kind; local IDs; no prohibited cycles | Resolved reference graph |
| 4. Semantic | Ownership, direction, contracts, units, clocks, maturity, logical/realization separation | Normalized semantic resource |
| 5. Binding/readiness | Target, artifact, resource, external asset, network, time, and lifecycle obligations | Ready or NotReady with reasons |
| 6. Policy | Extension authorization, security rules, organizational constraints, publication policy | Accepted or rejected policy result |

## Diagnostics

Every diagnostic MUST contain:

- a stable code scoped to the gate, such as `XDL-SCHEMA-UNKNOWN-FIELD`;
- severity: `error`, `warning`, or `advisory`;
- resource identity when derivable;
- an RFC 6901 JSON Pointer location when derivable;
- a human-readable explanation; and
- an actionable correction or explicit evidence gap.

An `error` blocks the gate. A `warning` records a supported but risky or incomplete condition without
claiming readiness. An `advisory` does not affect conformance. Tools MUST NOT downgrade errors solely
because a document declares alpha maturity.

## Cross-resource rules

Resource references require exact API-version recognition and an exact namespace/kind/name match.
Element references additionally require an exact element match in the referenced resource. Missing
references are errors; network fetching, current-directory lookup, registry fallback, and namespace
defaulting are not implicit resolution strategies.

Cycles through ownership or import are prohibited. Reference cycles that do not imply ownership MAY
be accepted only when a kind-specific rule defines their meaning. v1alpha1 defines no import or Bundle
cycle semantics.

## Semantic invariants

A conforming validator enforces at least:

- IDs are unique across each complete owning resource;
- System and Component contain no realization-only values;
- endpoint direction and interface contracts agree with flows;
- units are explicit or a value is explicitly dimensionless;
- cross-time-domain relationships have a declared mapping and tolerance;
- mutable artifact labels alone cannot satisfy reproducibility;
- physical bindings resolve an external asset before Ready;
- all Deployment binding dependencies exist and satisfy readiness conditions;
- Scenario targets belong to the selected System or Deployment graph;
- metrics resolve observers and state calculation/unit/acceptance semantics; and
- extension namespaces resolve to compatible Profiles and cannot shadow core fields.

## Normalization

Normalization occurs only after gates 1–4 succeed. It derives canonical identity, indexes collections,
retains source locations outside semantic content, and removes YAML presentation artifacts. It MUST
NOT invent default namespaces, units, clocks, realization choices, maturity, or missing references.
The normalized form is described in `xdl/metamodel/NORMALIZED_MODEL.md`.

## Readiness

Readiness is an evaluated state, never a field an author can assert without conditions. A Deployment
is statically `Ready` only when all mandatory bindings, artifacts, resources, mappings, external
assets, and declared lifecycle obligations are structurally resolved. Failed or unevaluated
conditions yield `NotReady` with diagnostics. Capability 004 implements this static check and never
evaluates a lifecycle probe, retrieves an artifact, or contacts a live system.

## M2 validation utility

`scripts/validate_m2.py` is documentary acceptance tooling for the specification package. It checks
schema/reference consistency, parses examples, applies selected semantic invariants, and runs negative
self-tests. The capability 004 `xverse_xdl` package is the prototype reference implementation; the M2
script remains an independent documentary regression check rather than a general validator.
