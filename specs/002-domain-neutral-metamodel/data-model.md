# M1 metamodel relationship summary

This is a semantic relationship model, not a class implementation, JSON Schema, XDL instance, or API.

## Aggregate and containment rules

| Aggregate | Contains or owns | Identity boundary |
|---|---|---|
| System | logical Components, Nodes, Devices, Interfaces, Networks, Models, Parameters | System-scoped identifiers and imports |
| Network | Links | Network-scoped link identifiers |
| TimeDomain | Clocks | Time-domain clock identifiers |
| Scenario | scenario steps/stimuli references, Fault selections, Observer/Metric references | Scenario-scoped experiment declarations |
| Deployment | environment-specific bindings and overrides | Deployment identifier separate from logical identities |

## Relationship cardinality and constraints

| Source | Relationship | Target | Cardinality | Constraint |
|---|---|---|---|---|
| Component / Node / Device | owns | Endpoint | 0..* | Each Endpoint has exactly one owner and Interface. |
| Endpoint | exposes | Interface | 1 | Direction and payload semantics must match attached Flows. |
| Flow | transfers from / to | Endpoint | 1 / 1..* | Source and destination directions are compatible. |
| Flow | uses | Link / Network / Protocol | 0..* | Required delivery, timing, and adaptation semantics must be satisfied. |
| Device / Node | has role | Sensor / Actuator | 0..* | Role contracts declare observed or controlled semantics. |
| Model | represented by | Artifact | 0..* | Artifact provenance and immutability are explicit. |
| Simulator | advances or hosts | Model / Device | 0..* | Time interaction and I/O are declared. |
| TimeDomain | contains | Clock | 0..* | Cross-domain operation needs mapping or tolerance. |
| Deployment | binds | logical objects | 1..* | Cannot change logical identifier. |
| Deployment | selects | ExecutionTarget | 1..* | Target meets artifacts/resources/lifecycle constraints. |
| Deployment | requests | Resource / ComputeResource | 0..* | Allocation policy and measured capacity are explicit. |
| Scenario | exercises | System | 1 | All targets are in or explicitly admissible for that System. |
| Scenario | selects | Deployment | 0..* | An unresolved selection blocks semantic Ready. |
| Scenario | injects | Fault | 0..* | Fault target and activation condition are explicit. |
| Observer | observes | logical or realization object | 1..* | Collection impact and provenance are declared. |
| Metric | evaluates | Observer evidence | 1..* | Units, calculation, and acceptance interpretation are explicit. |

## Invariants

1. Logical System, Component, Node, Device, Interface, and Flow identifiers never contain
   environment-specific credentials, addresses, process identifiers, or temporary paths.
2. A Deployment is replaceable/supersedable without changing the identity of what it realizes.
3. Artifact, evidence, and maturity state are separate: provenance alone does not prove execution.
4. Resources describe constraints/capabilities; they do not imply a scheduler, allocation engine, or
   available physical inventory.
5. Profile extensions are additive and namespaced. They cannot modify a core invariant.
