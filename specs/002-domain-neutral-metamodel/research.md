# M1 research and decision evidence

## Inputs considered

| Source | Relevant result | Treatment |
|---|---|---|
| Architecture guidance §§3, 8–10, 12–22, 35–38, 41, 48 | Requires a multi-industry core, separates logical architecture from realization, enumerates M1 concepts, makes XDL canonical, and defers implementation. | Direct architectural constraint. |
| M0 inventory and interface catalog | Existing repositories expose varied and incomplete startup, artifact, interface, and protocol evidence. | Do not lift provider or automotive terms into core; model provenance, bindings, failure, and evidence limits explicitly. |
| M0 review R01–R05 | Startup, readiness, reverse bridge message type, Android provenance, and callable hardware transport have material evidence gaps. | Model readiness/failure/evidence as semantics; do not claim runtime compatibility or select a baseline. |
| REF-001 technical synthesis | Describes broader target/stabilization context and multi-realization concerns. | Supplemental documentary context, not runtime proof. |
| REF-002 SADS | Supplies target requirements for lifecycle, resources, communication, timing, fault handling, observation, and model execution. | Requirement context only; target language does not establish implementation evidence. |

## Decision log

| Topic | Decision | Alternatives considered | Rationale |
|---|---|---|---|
| Core vocabulary | Use the 26 concepts named by the M1 directive. | Copy legacy taxonomy; reduce to generic process/container objects. | Satisfies the approved baseline and keeps system semantics independent of provider realization. |
| Logical realization | Bind through Deployment only. | Embed image, host, process, or physical address in logical objects. | Supports portability, restricted overlays, and identity continuity. |
| Device | Treat Device as a logical identity with simulated, virtual, physical, or hybrid realization classes. | Treat each realization as a new device. | Preserves identity through environment change. |
| Interaction | Separate Interface contract, Endpoint location, Flow transfer, Network/Link topology, and Protocol binding. | Use a single connection object. | Allows semantic compatibility checks without hard-coding a transport. |
| Time and evidence | Make TimeDomain, Clock, Fault, Observer, Metric, provenance, and maturity explicit. | Infer them from provider behavior. | M0 shows inference would conceal readiness and verification gaps. |
| Extension | Use namespaced profiles and references to external standards. | Add all specialized concepts to the core; create a competing general-purpose model. | Protects domain neutrality and standards interoperability. |
| Lifecycle | Define semantic profiles only. | Specify orchestrator scheduling/recovery algorithms in M1. | Keeps M1 architecture-only and leaves implementation to later capability specifications. |

## Deferred decisions

- XDL resource kinds, document boundaries, serialization, JSON/YAML schema, versioning, and loader/
  validator behavior.
- Identifier textual syntax, registry service, canonical URI policy, and migration/version rules.
- Concrete provider capability models, external adapter descriptors, artifact retrieval, and secrets.
- Runtime orchestration, scheduling, synchronization, fault injection, observability, resource
  allocation, compatibility wrapper behavior, and parity tests.
- Domain profiles and any automotive, robotics, aerospace, energy, industrial, or semiconductor
  vocabulary.
