# XDL v1alpha1 resource model

**Status**: Approved M2 specification

## Common metadata

`metadata.namespace` and `metadata.name` form stable resource scope. Both are lowercase and use
DNS-style namespace segments and slug-like names. `metadata.version` is the SemVer revision of this
resource content. Labels and annotations assist discovery and authorship; they do not participate in
identity or compatibility.

Every resource records provenance:

- `source`: a public-safe origin label or URI;
- `revision`: the pinned source revision, document version, or explicit `unknown`;
- `maturity`: `observed`, `inferred`, `architectural-target`, `prototype`, or `verified`;
- optional `evidenceRefs`: references to supporting records; and
- optional `limitations`: concise gaps that constrain the claim.

`verified` is permitted only when the cited evidence verifies the stated claim. Parsing or schema
validation alone never establishes runtime verification.

## Element ownership

Elements have an `id` unique across their owning resource because ElementRef does not carry a
collection name. The owning resource controls their lifecycle. Cross-resource relationships use
`ResourceRef` or `ElementRef`; internal `*Id` fields name
an element in a collection explicitly identified by the field's definition. A resource cannot
change the identity or content of an element owned elsewhere.

## System collections

| Collection | Required meaning |
|---|---|
| `nodes` | Logical participant or composition point with one or more roles. |
| `componentInstances` | Local instance ID plus a Component resource reference and optional node. |
| `devices` | Logical cyber-physical identity and allowed realization classes. |
| `sensors` | Observed quantity, output endpoint, unit, and evidence-limited fidelity. |
| `actuators` | Controlled quantity, input endpoint, unit, and declared limits. |
| `interfaces` | Direction, payload/schema contract, compatibility policy, and owner. |
| `endpoints` | Exactly one owner and interface plus direction. |
| `flows` | Source, destinations, interface, delivery intent, and optional time domain. |
| `networks` | Logical scope and capabilities. |
| `links` | Network membership and two or more endpoint participants. |
| `protocols` | External protocol/profile reference and explicit limitation statement. |
| `models` | Model kind, I/O contracts, provenance, fidelity maturity, and external reference. |
| `parameters` | Type, unit or dimensionless declaration, default/constraint, and mutability. |
| `timeDomains` | Clock class, epoch, rate interpretation, and monotonicity. |

A System MUST include at least one node or device and at least one time domain. Empty optional
collections SHOULD be omitted.

## Component collections

A Component has one or more `capabilities`. It MAY own interfaces, endpoints, parameters, models,
`artifactRequirements`, and `resourceRequirements`. Requirements express constraints, never a
selected artifact, registry, host, or provider. Component endpoints resolve only within the
Component; a System instance maps or exposes them through its own composition.

## Deployment collections

A Deployment references exactly one System and declares:

- `targets` with target class, capabilities, offered resources, and lifecycle contract;
- `artifacts` with kind, immutable version/revision evidence, source reference, and maturity;
- `resources` with class, quantity/unit, limits, and allocation policy;
- `bindings` from System elements to target and realization class;
- optional `networkBindings`, `timeMappings`, and `simulators`; and
- a deployment-level `readiness` contract.

IDs referenced by a binding are local Deployment IDs unless the schema requires an ElementRef. A
binding lists all artifact/resource IDs it depends on; an implementation MUST NOT infer dependencies
from target class or provider data.

## Scenario collections

A Scenario contains a non-empty `initialConditions` mapping and a non-empty ordered `steps` array.
Each step has an ID, action kind, target ElementRef, time domain, schedule, and namespaced action
payload. Faults declare activation and recovery intent. Observers declare target, sampling intent,
schema/unit semantics, and evidence sink reference. Metrics consume named observers and declare a
calculation reference and acceptance expression. Expressions are opaque declarative strings in
v1alpha1; no expression language or execution semantics is standardized yet.

## Profile and extensions

A Profile's `extensionNamespace` owns exactly one key in a resource's `extensions` map. The payload
must validate against the referenced profile schema. A consumer that lacks the compatible Profile
MUST report the extension as unresolved and MUST NOT treat the resource as semantically valid.
Extension conflict policy is `reject` in v1alpha1; other values are reserved for later API versions.

## Traceability

`traceability` entries connect a resource or element to requirements, architecture sources, test
evidence, or external records. Each entry includes a relation, reference URI, pinned revision or
`unknown`, and maturity. A traceability link is evidence metadata, not proof that its target exists
or has passed a test.
