# M2 XDL document model

This model describes serialized XDL resources and their normalized semantic form. It is not a
runtime class model.

## Common resource envelope

| Field | Meaning | Rule |
|---|---|---|
| \`apiVersion\` | XDL schema/API contract | Exactly \`xverse.io/xdl/v1alpha1\` for M2. |
| \`kind\` | Resource semantic family | System, Component, Deployment, Scenario, or Profile. |
| \`metadata.namespace\` | Ownership/identity namespace | Lowercase DNS-style segments; required. |
| \`metadata.name\` | Resource name | Lowercase slug; required and immutable within identity. |
| \`metadata.version\` | Revision of this resource content | SemVer string; independent of API/artifact versions. |
| \`metadata.labels\` | Search/classification metadata | Non-semantic; string values only. |
| \`metadata.provenance\` | Origin, revision, evidence, maturity | Required; does not prove runtime execution. |
| \`extensions\` | Namespaced profile payload | Keys must match declared Profile namespaces. |
| \`spec\` | Kind-specific semantic content | Required and strictly validated. |

Canonical display identity:
\`xdl://<metadata.namespace>/<lowercase-kind>/<metadata.name>\`. Element identity appends
\`#<element-id>\`. Element IDs are therefore unique across an owning resource, not only within one
collection. Canonical identity is derived and never supplied as a competing field.

## Resource references

A ResourceRef contains \`apiVersion\`, \`kind\`, \`namespace\`, and \`name\`. An ElementRef adds
\`element\`. Omitting namespace is never interpreted as an environment default. A later authoring
convenience may add explicit local-reference syntax only through a separate decision.

## Resource roles

| Kind | Owns | References |
|---|---|---|
| System | logical nodes, component instances, devices, interfaces, flows, networks, models, parameters, time domains | Component descriptors, external models/requirements |
| Component | reusable interfaces/endpoints, models, parameters, resource/artifact requirements | external standards and artifacts |
| Deployment | targets, artifacts, resources, simulators, network/time bindings, logical bindings | exactly one System plus referenced Components/Profiles |
| Scenario | stimuli, faults, observers, metrics, acceptance intent | one System and optional Deployment |
| Profile | extension namespace, compatible APIs, schema/documentation references, conflict policy | standards or provider specifications |

## Normalized resource

After parsing and structural validation, normalization yields:

- canonical resource identity;
- explicit API version and kind;
- metadata with normalized strings and provenance;
- kind-specific collections indexed by stable element ID;
- structured references without implicit paths;
- extension payloads paired with their Profile declaration;
- source locations retained separately for diagnostics;
- presentation comments, mapping order, style, anchors, and aliases removed.

Normalization does not resolve deployments, allocate resources, start components, or infer maturity.
