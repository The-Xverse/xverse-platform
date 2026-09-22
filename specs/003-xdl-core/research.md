# M2 research and decision evidence

## Architecture inputs

| Source | Relevant result | M2 treatment |
|---|---|---|
| Approved M1 metamodel and ADR-0005–0008 | Stable core concepts, Deployment-only realization binding, semantic lifecycle/evidence, additive namespaced extensions. | Direct semantic source for XDL v1alpha1. |
| Architecture guidance §§12–23, 36–38, 42, 48 | XDL is canonical, metamodel/schema first, YAML/JSON, compiler-style future, standards bindings, system/deployment/experiment dimensions. | Direct architectural constraint. |
| M0 review R01–R05 | Legacy startup, interface, provenance, and readiness gaps remain. | No component is encoded as compatible; readiness and provenance must be explicit. |
| JSON Schema Draft 2020-12 | Current published JSON Schema version, with modular references and unevaluated-property support. | Schema dialect for all XDL structural schemas. |
| YAML 1.2.2 | Human-friendly serialization with mapping order/presentation separated from representation. | YAML presentation maps to the same JSON-compatible semantic model; order/comments/anchors are non-semantic. |
| Semantic Versioning 2.0.0 | Established rules for version compatibility. | Resource/profile releases may use SemVer, but XDL API compatibility remains the explicit \`apiVersion\`. |
| FMI 3.0.2 | Current published FMI specification; layered standards can extend it. | XDL references FMUs/FMI versions and bindings; it does not reproduce FMI semantics. |

## Decisions

| Topic | Decision | Rejected alternative |
|---|---|---|
| Document model | Five separate resource kinds with common envelope. | One monolithic \`system/deployment/experiment\` file, which couples ownership and revision. |
| Identity | Structured namespace/name/kind references plus scoped element IDs. | Free-form reference strings with implicit parsing rules. |
| Extension | Reverse-domain Profile namespace and explicit \`extensions\` map. | Arbitrary unknown fields or core-field overrides. |
| Schema strictness | Reject unknown core fields and duplicate IDs; validate references semantically. | Permissive parsing that hides misspellings or silently preserves unknown behavior. |
| Versioning | Exact alpha API version plus separate resource/profile/artifact versions. | Inferring all compatibility from one semantic version. |
| Serialization | JSON-compatible YAML 1.2.2 and JSON; JSON Schema 2020-12. | Custom grammar or YAML-only semantics. |
| Standard integration | External typed references with provenance and optional profile binding. | Copying SysML, SSP, FMI, or provider semantic universes into XDL Core. |
| Runtime boundary | Specification, schemas, examples, and documentary validation only. | Loader, validator library, normalized object code, or runtime plan generation in M2. |

## Primary standards references

- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)
- [YAML 1.2.2](https://yaml.org/spec/1.2.2/)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [Functional Mock-up Interface](https://fmi-standard.org/)

These sources establish external format/version context. They do not define XDL semantics.

