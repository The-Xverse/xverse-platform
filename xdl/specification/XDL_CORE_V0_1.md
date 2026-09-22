# XDL Core v0.1

**Status**: Approved M2 specification; `v1alpha1` remains an alpha language contract
**API version**: `xverse.io/xdl/v1alpha1`
**Normative terms**: MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are requirements at their
customary standards meanings.

## 1. Purpose

XDL is the canonical, domain-neutral description language for X-Verse. It describes a logical
cyber-physical system, reusable logical components, realization bindings, experiments, and declared
extensions. XDL documents are data. They do not start workloads, allocate infrastructure, contact
devices, or prove that a declared capability works.

This version defines the document contract and its normalized meaning. A future loader may implement
the contract, but loader APIs, runtime plans, catalogs, compatibility adapters, and orchestration are
outside this specification.

## 2. Conformance

A conforming v1alpha1 resource:

1. is YAML 1.2.2 or JSON that maps without loss to the JSON data model;
2. contains exactly one resource envelope and a recognized `kind`;
3. passes the structural schema for that kind;
4. satisfies the reference and semantic rules in this specification;
5. uses no implicit namespace, provider, address, unit, clock, or maturity default; and
6. keeps credentials and sensitive environment values outside the resource.

The schemas in `xdl/schemas/v1alpha1/` are normative for structure. This document and the companion
resource, validation, and versioning specifications are normative for meaning. When a schema cannot
express a semantic rule, a conforming implementation MUST enforce the prose rule and identify the
failed validation gate.

## 3. Resource envelope

Every resource has these fields:

| Field | Requirement |
|---|---|
| `apiVersion` | MUST equal `xverse.io/xdl/v1alpha1`. |
| `kind` | MUST be `System`, `Component`, `Deployment`, `Scenario`, or `Profile`. |
| `metadata` | MUST provide namespace, name, resource version, and provenance. |
| `extensions` | MAY contain payloads keyed by declared Profile namespace. |
| `spec` | MUST contain the kind-specific content. |

Unknown fields are errors. An implementation MUST NOT preserve an unknown field as if it were
understood. Extension data is permitted only under `extensions` and only when its Profile is
available and compatible.

## 4. Resource kinds

### 4.1 System

A System owns logical identity and composition. It can declare nodes, component instances, devices,
sensors, actuators, interfaces, endpoints, flows, networks, links, protocols, models, parameters,
and time domains. It MAY reference reusable Component resources and external models or requirements.
It MUST NOT contain execution targets, artifact locations, provider identifiers, host addresses,
credentials, resource allocations, or process/container lifecycle commands.

Every contained `id` is unique across its owning resource. References to contained elements MUST resolve
to the owning System and the correct element kind. A flow's source and destinations MUST resolve to
endpoints, and endpoint directions and interface contracts MUST be compatible.

### 4.2 Component

A Component describes a reusable logical capability. It declares capability roles, interfaces,
endpoints, parameters, models, and abstract artifact or resource requirements. It MUST NOT select a
runtime technology or concrete target. A System uses a Component through a structured `componentRef`
and gives the instance its own local identity.

### 4.3 Deployment

A Deployment is the only core resource that binds logical identities to realizations. It references
one System and declares execution targets, immutable artifact evidence, resource offers or claims,
network and time mappings, and bindings. Each binding MUST identify one logical element, one
realization class, one target, and readiness/lifecycle requirements.

Realization classes are `simulated`, `virtual`, `physical`, or `hybrid`. A physical binding MUST have
an indirect external asset reference before it can be Ready. A Deployment is not Ready while any
required reference, artifact revision, resource, time mapping, external asset, or readiness condition
is unresolved.

### 4.4 Scenario

A Scenario describes experiment intent. It references one System and MAY select one Deployment. It
declares initial conditions, ordered steps, faults, observers, metrics, timing, and acceptance intent.
A Scenario MUST distinguish declared expectations from evidence produced by execution. A metric MUST
name its observer inputs, unit or dimensionless semantics, calculation reference, and acceptance
condition. Cross-clock behavior requires an explicit mapping and tolerance.

### 4.5 Profile

A Profile declares an extension namespace and its compatibility boundary. Its namespace MUST use
reverse-domain form. A Profile MUST state compatible XDL API versions, its own resource version,
an external schema reference, documentation, and a conflict policy. Profile fields MUST NOT replace
core identity, weaken core validation, or change a core relationship's meaning.

## 5. References and identity

References are structured objects. A resource reference includes `apiVersion`, `kind`, `namespace`,
and `name`; an element reference also includes `element`. Namespace omission never means current
namespace. A canonical display identity is derived as:

```text
xdl://<namespace>/<lowercase-kind>/<name>
xdl://<namespace>/<lowercase-kind>/<name>#<element-id>
```

The display form is diagnostic output, not an alternate authoring syntax. Resources MUST NOT embed
provider addresses, process identifiers, mutable artifact tags, or registry locations in semantic
identity.

## 6. Logical and realization separation

System and Component resources define logical meaning. Deployment defines realization. Scenario
defines experiment intent. Profile defines extension ownership. A deployment may change without
changing logical identity, and several deployments may realize the same System. A tool MUST reject
realization-only fields in System or Component rather than silently relocating or interpreting them.

Physical devices are first-class realizations. They are not encoded as a special simulator or a
network address. The logical Device remains stable while Deployment supplies its external asset
binding and readiness evidence.

## 7. External standards

XDL records structured references, provenance, compatibility claims, and bindings for external
standards and artifacts. It does not reproduce the full semantic models of SysML/UML, SSP/FMI/FMUs,
network standards, telemetry systems, or provider APIs. A compatibility claim is declarative until
separately verified; it MUST include a revision or version and maturity/evidence metadata.

## 8. Security and public-safe content

A resource MAY contain an opaque `secretRef` only where a schema explicitly permits it. The reference
identifies an external secret mechanism; it MUST NOT contain secret material. Shareable examples and
documents MUST use non-sensitive placeholders, non-routable example domains, and no private
infrastructure addresses.

## 9. Deferred capabilities

The following require later specifications: multi-resource Bundle/import semantics, registries,
canonical byte serialization, signatures, conversion algorithms, loader APIs, runtime-plan
compilation, orchestration, catalog publication, compatibility adapters, and executable blueprints.
Their absence MUST NOT be interpreted as an implicit behavior in v1alpha1.

## 10. Maturity

XDL Core v0.1 is a proposed alpha document contract. Passing its schemas demonstrates document
conformance only. It does not demonstrate availability, integration, performance, safety, security,
or runtime interoperability.
