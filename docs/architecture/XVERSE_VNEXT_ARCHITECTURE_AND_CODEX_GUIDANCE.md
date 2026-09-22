# X-Verse vNext — Architecture, Migration, XDL, and Codex Engineering Guidance

**Status:** Architecture and engineering baseline  
**Purpose:** Guidance for Codex/Spec Kit implementation of X-Verse vNext  
**Target repositories:** `xverse-platform`, `xverse-compat`, `xverse-blueprints`  
**Primary principle:** Evolve X-Verse without disrupting current production repositories  
**Platform scope:** Multi-industry cyber-physical systems simulation, virtualization, integration, and experimentation

---

## 1. Purpose of this document

This document consolidates the architectural decisions and engineering guidance for the next evolution of X-Verse.

It is intended to be used directly by Codex and by human contributors when creating the three new repositories:

- `The-Xverse/xverse-platform`
- `The-Xverse/xverse-compat`
- `The-Xverse/xverse-blueprints`

The guidance deliberately separates:

1. the **current production X-Verse / AutoVerse ecosystem**;
2. the **future domain-neutral X-Verse platform architecture**;
3. the **compatibility layer** required to consume existing production components without modifying them;
4. **domain-specific blueprints**, initially with automotive as the primary proving ground;
5. the **X-Verse Definition Language (XDL)**, which becomes the canonical executable representation used to bring system/software architecture into an X-Verse experiment.

This document must be treated as an architectural constraint set, not merely as a suggestion list.

---

# 2. Current X-Verse baseline

The current X-Verse program evolved from the automotive-focused AutoVerse environment into a broader cyber-physical systems platform.

The existing technical baseline includes, among other elements:

- CARLA-based simulation;
- Zenoh-centered data exchange;
- X-COM protocol bridges;
- SOME/IP integration;
- CAN integration;
- virtual ECUs;
- physical ECUs;
- S-CORE;
- Zephyr and Renode;
- Android Automotive integration;
- Simulink-related work;
- hardware virtualization and HwSim;
- radar simulation and semiconductor-oriented PoCs;
- cloud and hybrid deployment studies;
- automated bring-up scripts;
- scenario and test automation concepts.

The target System Architectural Design Specification already establishes broader goals such as:

- modular orchestration;
- scenario lifecycle management;
- FMI/FMU integration;
- distributed simulation;
- deterministic execution;
- protocol interoperability;
- observability;
- fault tolerance;
- fault injection;
- cloud/on-premises/hybrid deployment;
- extensibility;
- APIs and SDKs.

However, **the target architecture and the implemented software baseline are not equivalent**.

All future work must preserve the following maturity distinction:

- **Implemented/demonstrated**
- **Partially implemented / under stabilization**
- **Architectural target**
- **Exploratory / PoC**

Never infer that a requirement in the SADS is already implemented.

---

# 3. X-Verse strategic identity

## 3.1 X-Verse is not an automotive simulator

X-Verse shall be defined as a **multi-industry cyber-physical systems platform**.

A suitable positioning is:

> X-Verse is an open, modular cyber-physical systems experimentation and digital-twin platform that integrates simulated models, virtualized software and hardware, physical devices, communication networks, and test infrastructure within reproducible distributed scenarios.

The architecture must support domains such as:

- automotive;
- aerospace;
- robotics;
- energy;
- industrial automation;
- semiconductor and embedded systems;
- smart infrastructure;
- other cyber-physical domains.

Automotive is currently the strongest implementation and proving ground, but it must **not define the platform core**.

## 3.2 AutoVerse becomes an automotive blueprint family

Conceptually:

```text
X-Verse
    =
multi-industry cyber-physical platform

AutoVerse
    =
automotive reference environment / blueprint family
```

The platform must not contain hard-coded assumptions about:

- ECU;
- HPC;
- zonal controller;
- AUTOSAR;
- CAN;
- SOME/IP;
- AEB;
- vehicle;
- CARLA.

These concepts belong to plugins, adapters, profiles, domain libraries, or blueprints.

---

# 4. Non-negotiable production constraint

## 4.1 Existing repositories are production assets

Current repositories in the `The-Xverse` organization are used by active initiatives.

Therefore:

> **Existing repositories are immutable by default for the X-Verse vNext program.**

Unless explicitly authorized for a specific repository and specific change, Codex must not:

- commit to an existing repository;
- create a branch in an existing repository;
- open a PR against an existing repository;
- modify CI/CD;
- rename repositories;
- rename branches;
- rename tags;
- rename packages;
- modify public APIs;
- change image names;
- change communication topics;
- alter deployment behavior;
- add vNext dependencies into production repositories.

Existing repositories may be inspected, analyzed, documented, executed, wrapped, referenced, orchestrated, and regression-tested.

They are **read-only dependencies** during the initial vNext evolution.

---

# 5. Transformation strategy: parallel evolution / strangler architecture

The transformation shall not be a repository migration.

It shall be an **X-Verse Platform Evolution Program** based on parallel evolution.

```text
TRACK A — CONTINUITY

Existing X-Verse / AutoVerse
Existing initiatives
Existing repositories
Existing deployments

NO BREAKAGE


TRACK B — EVOLUTION

X-Verse vNext
Domain-neutral architecture
XDL
New orchestration
New observability
Fault injection
Network/runtime abstractions
New blueprints


                │
                ▼

         COMPATIBILITY LAYER
```

The future platform consumes legacy implementations through declared compatibility boundaries.

The objective is not to force existing code into a new repository structure.

The objective is to make X-Verse vNext capable of **orchestrating and composing both legacy and new implementations through stable contracts**.

---

# 6. Initial repository strategy

Create only three new repositories.

Do not immediately split the platform into many repositories.

## 6.1 `xverse-platform`

Purpose:

> Domain-neutral X-Verse vNext platform implementation.

Recommended initial structure:

```text
xverse-platform/
├── AGENTS.md
├── README.md
├── LICENSE
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── specifications/
│   ├── reviews/
│   └── legacy/
│
├── specs/
│
├── xdl/
│   ├── specification/
│   ├── schemas/
│   ├── metamodel/
│   ├── loader/
│   ├── validator/
│   ├── compiler/
│   └── runtime-plan/
│
├── src/
│   └── xverse/
│       ├── core/
│       ├── orchestration/
│       ├── runtime/
│       ├── communication/
│       ├── devices/
│       ├── time/
│       ├── faults/
│       ├── observability/
│       ├── plugins/
│       └── sdk/
│
├── cli/
├── tests/
└── examples/
```

This should initially be a monorepo.

Modules may become separate repositories only after an independent lifecycle is demonstrated.

## 6.2 `xverse-compat`

Purpose:

> Compatibility contracts, descriptors, adapters, and deployment glue required to consume existing X-Verse production components without modifying them.

Recommended structure:

```text
xverse-compat/
├── AGENTS.md
├── README.md
├── catalog/
│   ├── communication/
│   ├── simulators/
│   ├── automotive/
│   ├── aaos/
│   ├── score/
│   ├── zephyr/
│   ├── renode/
│   ├── simulink/
│   └── hardware/
│
├── adapters/
├── deployment/
├── compatibility-tests/
└── docs/
```

This repository should contain as little domain/business logic as possible.

It exists to isolate legacy integration knowledge from the new platform core.

## 6.3 `xverse-blueprints`

Purpose:

> Reproducible system-level reference architectures and experiments.

Recommended structure:

```text
xverse-blueprints/
├── AGENTS.md
├── README.md
├── automotive/
│   ├── cruise-control-v2/
│   ├── assured-aeb/
│   ├── body-control/
│   └── radar-validation/
│
├── aerospace/
├── robotics/
├── energy/
├── semiconductor/
└── examples/
```

A blueprint may reference legacy components through `xverse-compat` or native vNext capabilities through `xverse-platform`.

---

# 7. Rule for future repository creation

A new Git repository should be created only when the component has a genuine independent lifecycle.

At least one of the following should normally be true:

- independently versioned and released;
- independent maintainer ownership;
- materially different build/toolchain;
- separate licensing/IP boundary;
- reusable outside the parent repository;
- stable external API boundary;
- independent security/update lifecycle.

Otherwise, prefer a package, module, plugin, or subdirectory.

Do not recreate the current repository fragmentation in vNext.

---

# 8. Domain-neutral X-Verse architecture

The platform should evolve toward the following conceptual structure:

```text
                         X-VERSE PLATFORM
┌──────────────────────────────────────────────────────────────┐
│                 User / Automation Layer                      │
│ CLI • SDK • Web UI • CI/CD • Experiment APIs               │
├──────────────────────────────────────────────────────────────┤
│                   Orchestration Layer                        │
│ Scenario • lifecycle • scheduling • resources • time        │
├──────────────────────────────────────────────────────────────┤
│                 Cyber-Physical Runtime                       │
│ Process • container • VM • FMU • emulator • real device     │
├──────────────────────────────────────────────────────────────┤
│               Communication / Interoperability               │
│ Schemas • routing • discovery • QoS • bridges • telemetry   │
├──────────────────────────────────────────────────────────────┤
│                  Device Abstraction                          │
│ Simulated • virtual • physical • hybrid                     │
├──────────────────────────────────────────────────────────────┤
│                  Simulator / Model Adapters                  │
│ CARLA • Gazebo • FMI • Simulink • Renode • custom          │
├──────────────────────────────────────────────────────────────┤
│                    Physical Interfaces                       │
│ Sensors • actuators • ECUs • MCUs • FPGA • rigs • PLCs     │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
                       DOMAIN BLUEPRINTS
```

---

# 9. Core metamodel

The domain-neutral metamodel should contain concepts approximately equivalent to:

```text
System
Scenario
Component
Node
Device
Sensor
Actuator
ComputeResource
Interface
Endpoint
Flow
Network
Link
Protocol
Model
Artifact
ExecutionTarget
Simulator
TimeDomain
Clock
Fault
Observer
Metric
Parameter
Resource
Deployment
```

The names and semantics must be validated before implementation is frozen.

## 9.1 `Node`

Avoid using ECU/HPC as core abstractions.

Prefer:

```text
Node
├── ComputeNode
├── SensorNode
├── ActuatorNode
├── GatewayNode
└── CompositeNode
```

Domain-specific mappings can specialize this concept.

## 9.2 Device realization

A Device must be distinguishable from its realization.

```text
Device
├── SimulatedDevice
├── VirtualDevice
├── PhysicalDevice
└── HybridDevice
```

A logical device may therefore preserve its identity while changing realization.

This is central to X-Verse's cyber-physical role.

## 9.3 Execution target

The platform should support execution targets such as:

```text
ExecutionTarget
├── ProcessTarget
├── ContainerTarget
├── VmTarget
├── EmulatorTarget
├── FmuTarget
├── RemoteTarget
└── PhysicalTarget
```

QEMU, Renode, Docker, Kubernetes, physical boards, etc. should be concrete providers/adapters, not core semantic primitives.

---

# 10. Logical architecture versus realization

The platform must explicitly separate:

```text
WHAT EXISTS
```

from:

```text
HOW IT IS REALIZED
```

For example:

```yaml
node:
  id: perception
  kind: compute
```

is separate from:

```yaml
realization:
  type: container
  artifact:
    image: ghcr.io/example/perception:1.2
```

or:

```yaml
realization:
  type: physical
  device: lab-controller-01
```

This enables the same logical architecture to run fully simulated, fully virtualized, hardware-in-the-loop, or mixed/hybrid.

---

# 11. X-COM evolution

Existing X-COM bridges remain unchanged initially.

X-Verse vNext should introduce a domain-neutral communication abstraction around them.

```text
                    X-Verse Communication
                             │
             ┌───────────────┼────────────────┐
             │               │                │
         Schemas          Routing         Observability
             │               │                │
             └───────────────┼────────────────┘
                             │
                      Protocol Adapters
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
          Legacy          Native vNext      Future
          bridge           adapter           plugin
```

Existing implementations such as Zenoh-to-SOME/IP or Zenoh-to-CAN are consumed through compatibility adapters.

Later, new native implementations may coexist.

No big-bang replacement is required.

---

# 12. X-Verse Definition Language (XDL)

## 12.1 Approved concept

The canonical name is:

> **X-Verse Definition Language (XDL)**

Definition:

> XDL is the canonical, versioned, domain-neutral system representation used by X-Verse to describe cyber-physical system composition, execution realization, interfaces, communication, deployment, timing, physical and virtual devices, simulation bindings, faults, observability, and experiment configuration.

XDL is intended to translate engineering architecture into an executable X-Verse environment.

## 12.2 XDL is not a replacement for SysML or UML

XDL must not become a general-purpose systems modeling language.

XDL should complement:

- SysML;
- UML;
- SSP;
- FMI/FMU;
- other engineering/model exchange standards.

The division of responsibility is:

```text
SysML / UML
    =
system and software architecture intent

SSP / FMI
    =
model structure, parameterization, executable models

XDL
    =
X-Verse execution realization and experiment definition
```

## 12.3 High-level integration architecture

```text
              MODELING / ENGINEERING WORLD

 SysML v2         SysML v1 / UML          SSP / FMI
     │                  │                    │
     │                  │                    │
     └───────────┬──────┴──────────────┬─────┘
                 │                     │
                 ▼                     ▼
          import / transform       model bindings
                 │
                 ▼
             ┌────────┐
             │  XDL   │
             └───┬────┘
                 │
            validation
                 │
            resolution
                 │
                 ▼
        X-Verse Runtime Plan
                 │
                 ▼
        X-Verse Experiment
```

X-Verse Core should understand XDL.

It should not require native knowledge of every modeling tool.

---

# 13. XDL implementation strategy

## 13.1 Do not start with a custom grammar

XDL v0.1 should be:

- metamodel-first;
- schema-first;
- YAML/JSON serialized;
- strongly validated;
- versioned.

Do not begin by inventing custom syntax.

Custom syntax may be added later if users demonstrate a real need.

## 13.2 Initial serialization

Recommended form:

```yaml
apiVersion: xverse.io/xdl/v1alpha1
kind: System
```

Potential file extension:

```text
.xdl.yaml
```

The public concept remains XDL.

Internally the architecture should preserve a canonical semantic object model independent of YAML.

## 13.3 Compiler-style implementation

```text
XDL source
    │
    ▼
XDL loader/parser
    │
    ▼
XDL core semantic model
    │
    ▼
semantic validator
    │
    ▼
resolver/binder
    │
    ▼
runtime execution plan
    │
    ▼
X-Verse runtime
```

The runtime must not depend directly on YAML syntax.

---

# 14. XDL conceptual sections

A complete XDL definition should conceptually describe three dimensions.

## 14.1 `system`

Defines what exists.

Examples:

- nodes;
- devices;
- components;
- interfaces;
- endpoints;
- flows;
- networks;
- logical models.

## 14.2 `deployment`

Defines how the system is realized.

Examples:

- process;
- container;
- VM;
- QEMU;
- Renode;
- FMU;
- physical hardware;
- simulator binding;
- artifact version;
- resource assignment;
- runtime environment.

## 14.3 `experiment`

Defines how the system is exercised and observed.

Examples:

- scenario;
- stimuli;
- faults;
- timing;
- observers;
- metrics;
- recording;
- replay;
- acceptance criteria.

Conceptual form:

```yaml
xdl:

  system:
    ...

  deployment:
    ...

  experiment:
    ...
```

The final schema may use separate resource kinds instead of a single monolithic document.

---

# 15. Example XDL concept

```yaml
apiVersion: xverse.io/xdl/v1alpha1
kind: System

metadata:
  name: example-cps

spec:

  nodes:

    - id: sensor-1
      kind: sensor

      realization:
        type: simulated

        provider:
          adapter: example-simulator
          model: sensor


    - id: controller
      kind: compute

      realization:
        type: container

        artifact:
          image: ghcr.io/example/controller:1.0


  interfaces:

    - id: sensor-data

      source:
        node: sensor-1
        endpoint: output

      destination:
        node: controller
        endpoint: input

      schema:
        type: SensorData


  communication:

    - interface: sensor-data

      protocol:
        type: example-protocol

      network:
        type: ethernet


  observability:

    metrics:
      - sensor-data.latency
      - sensor-data.age
```

This example is illustrative, not a frozen specification.

---

# 16. XDL extensibility

XDL core must remain domain-neutral.

Recommended namespace pattern:

```text
xverse.io/xdl/core
xverse.io/xdl/runtime
xverse.io/xdl/faults
```

Domain extensions may use:

```text
xverse.io/xdl/automotive
xverse.io/xdl/robotics
xverse.io/xdl/aerospace
xverse.io/xdl/energy
xverse.io/xdl/semiconductor
```

Third-party extensions should be able to use their own namespace.

---

# 17. XDL profiles and plugins

Automotive concepts must not leak into XDL Core.

Instead:

```text
XDL Core
   │
   ├── Automotive Profile
   ├── Robotics Profile
   ├── Aerospace Profile
   ├── Energy Profile
   └── Semiconductor Profile
```

For example, CAN, SOME/IP, AUTOSAR, AEB, and ECU belong to automotive-related profiles/plugins rather than XDL Core.

---

# 18. SysML and UML integration

## 18.1 Direction

Initial integration should be:

```text
SysML / UML
    │
    ▼
XDL
    │
    ▼
X-Verse
```

Do not initially attempt full bidirectional round-trip synchronization.

Round-trip modeling introduces significant complexity related to element ownership, identity, merge conflicts, semantic preservation, vendor-specific metadata, and synchronization state.

## 18.2 SysML v2

Target architecture:

```text
SysML v2 model/repository
        │
        ▼
SysML v2 importer
        │
        ▼
XDL
```

The importer should project only execution-relevant architecture into XDL.

XDL must not clone the complete SysML semantic universe.

## 18.3 SysML v1 / UML

Legacy integration may use XMI-based import where supported by the modeling tool.

```text
SysML v1 / UML
      │
      ▼
     XMI
      │
      ▼
XDL importer
      │
      ▼
     XDL
```

Tool-specific differences must be handled by importer adapters rather than polluting XDL Core.

---

# 19. SysML-to-XDL projection

Potential conceptual mapping:

| Architecture concept | XDL concept |
|---|---|
| Part / Block instance | Node / Component |
| Port | Endpoint |
| Interface | Interface |
| Connection | Flow / Link |
| Value property | Parameter |
| Allocation | Realization / Deployment binding |
| Constraint | Validation constraint |
| Requirement | Traceability reference |
| Behavior / state machine | Model/behavior reference |
| Package | Namespace/module |

This mapping is provisional.

The SysML v2 semantics should be analyzed formally before freezing it.

Not every SysML element needs an XDL representation.

---

# 20. SSP and FMI interoperability

XDL must not duplicate standards unnecessarily.

If a standard already adequately represents a concern, XDL should reference it, import it, bind to it, or extend it only where required for X-Verse runtime concerns.

Conceptually:

```text
FMI / FMU
   =
executable model

SSP
   =
system structure / parameterization

XDL
   =
X-Verse realization / deployment / experiment
```

An FMU should normally be represented as an artifact/model referenced by XDL rather than re-described internally.

---

# 21. Architecture model versus runtime overlay

Do not put volatile runtime information into the architecture unnecessarily.

Examples that may belong in deployment overlays:

- physical machine address;
- temporary port;
- credentials;
- Kubernetes namespace;
- GPU assignment;
- lab-specific hardware identifier;
- container digest;
- local path.

Recommended concept:

```text
logical-system.xdl.yaml
        +
deployment-lab.yaml
        +
scenario.yaml
        =
resolved X-Verse runtime plan
```

This allows one system model to be executed in multiple environments.

---

# 22. XDL validation

XDL becomes valuable when it detects impossible or inconsistent experiments before execution.

Potential validation categories include:

### Schema compatibility

Producer and consumer data types must be compatible.

### Interface mismatch

If the producer schema differs from the consumer schema, reject the configuration or require an explicit converter.

### Execution-resource mismatch

```text
component requires GPU
execution target has no GPU
```

Reject.

### Physical binding problem

```text
realization = physical
device = undefined
```

Reject.

### Timing inconsistency

```text
flow requires synchronized time
source/destination time domains incompatible
```

Reject.

### Protocol capability mismatch

If a selected protocol cannot satisfy declared communication semantics, reject or flag according to policy.

---

# 23. Component descriptors and XDL

The previously proposed Component Descriptor should be incorporated into the XDL ecosystem rather than becoming a separate unrelated format.

Example:

```yaml
apiVersion: xverse.io/xdl/v1alpha1
kind: Component

metadata:
  name: legacy-someip-bridge
  version: "2.0.0"

spec:

  source:
    repository: The-Xverse/example-bridge
    revision: v2.0.0

  runtime:
    type: container

  interfaces:

    - id: data-fabric
      protocol: zenoh

    - id: vehicle-service
      protocol: someip

  compatibility:
    legacy: true
```

The component descriptor describes the production component.

It does not alter it.

---

# 24. Component catalog

`xverse-compat` should provide a catalog of production assets.

Example:

```text
catalog/
├── communication/
│   ├── zenoh-someip/
│   │   └── component.xdl.yaml
│   └── zenoh-can/
│       └── component.xdl.yaml
│
├── simulators/
│   └── carla/
│       └── component.xdl.yaml
│
└── automotive/
    └── ...
```

The platform resolves blueprint component references against this catalog.

---

# 25. First compatibility milestone: AutoVerse cruise control

Before using vNext for new native features, reproduce an existing production baseline.

The recommended first milestone is:

> Run the existing AutoVerse cruise-control demonstration through X-Verse vNext orchestration while using the same existing production components unchanged.

```text
CURRENT

run_autoverse.py
       │
       ▼
production components


VNEXT

Cruise-Control Blueprint
       │
       ▼
X-Verse Platform
       │
       ▼
X-Verse Compat
       │
       ▼
same production components
```

This becomes the compatibility proof.

---

# 26. Parity testing

The new orchestration must be compared against the current baseline.

Compare at least:

- startup order;
- process/container lifecycle;
- component health;
- Zenoh topics;
- SOME/IP events;
- CAN frames;
- timing envelopes;
- feature behavior;
- output signals;
- shutdown behavior;
- error behavior.

Produce machine-readable parity evidence where possible.

Example output:

```text
compatibility/parity-report.json
```

The exact schema should be defined by the implementation specification.

---

# 27. Shadow execution

For sensitive initiatives, do not migrate directly.

Allow the new platform to operate in shadow mode:

```text
production workflow
       │
       ├─────────────► current environment
       │
       └─────────────► vNext shadow observation
```

Shadow mode may compare lifecycle decisions, topology, timing, logs, communication events, and expected orchestration actions.

vNext should initially have no authority to alter production behavior.

---

# 28. Migrate initiatives, not repositories

Do not define migration as:

> migrate repository X.

Prefer:

> migrate Blueprint / Use Case Y to X-Verse vNext orchestration.

The legacy repository may remain unchanged indefinitely.

A component only needs replacement when there is a concrete technical or maintenance reason.

---

# 29. New native capabilities

Once legacy parity is proven, new capabilities should be implemented natively in `xverse-platform`.

Recommended priority:

1. observability;
2. fault injection;
3. deterministic time model;
4. communication abstraction;
5. network fidelity;
6. protocol plugins;
7. device abstraction enhancements;
8. advanced orchestration.

---

# 30. Fault injection

Fault injection is a native cross-domain X-Verse capability.

Potential taxonomy:

```text
component.crash
component.freeze

communication.delay
communication.loss
communication.corruption
communication.partition

clock.drift
clock.offset

resource.cpu
resource.memory
resource.network

device.failure

sensor.bias
sensor.dropout

actuator.stuck
actuator.degraded
```

Example conceptual XDL:

```yaml
apiVersion: xverse.io/xdl/v1alpha1
kind: Fault

metadata:
  id: fault-001

spec:

  target:
    component: example-controller
    interface: input

  type: communication.delay

  trigger:
    simulationTime: 12.5s

  duration: 3s

  parameters:
    delay: 180ms
```

Domain-specific fault semantics belong to profiles/blueprints.

---

# 31. Time model

Heterogeneous timing is a major architectural concern.

The platform should model concepts such as:

```text
SimulationTime
WallTime
ExternalTime
LogicalClock
TimeDomain
TimeAuthority
SynchronizationPolicy
```

Technologies such as PTP/gPTP should be represented as concrete synchronization implementations/profiles, not as the core time model itself.

---

# 32. Network fidelity

X-Verse should eventually support several network fidelity levels.

```text
FUNCTIONAL
├── delay
├── jitter
├── loss
└── bandwidth

NATIVE
├── operating-system networking
├── real sockets
├── real protocol stacks
└── virtual interfaces

DETAILED
├── queue behavior
├── clock synchronization
├── congestion
├── scheduling
└── network faults
```

Do not claim protocol or timing fidelity beyond what the selected backend actually provides.

Simulation fidelity must always be explicit.

---

# 33. Blueprint strategy

A blueprint is a reproducible system-level experiment package.

It should contain enough information to recreate:

- architecture;
- component versions;
- deployment;
- communication;
- scenarios;
- faults;
- observability;
- experiment parameters;
- expected outputs.

Example:

```text
automotive/
└── assured-aeb/
    ├── README.md
    ├── system.xdl.yaml
    ├── deployment/
    ├── scenarios/
    ├── faults/
    ├── observers/
    ├── contracts/
    ├── experiments/
    └── tests/
```

---

# 34. Thesis integration

The Safety-Bounded Self-X / MLOC AEB research should become a **native vNext automotive blueprint**, not part of X-Verse Core.

Desired dependency direction:

```text
Assured AEB Blueprint
        │
        ▼
Automotive profile
        │
        ▼
XDL / X-Verse APIs
        │
        ▼
X-Verse Platform
```

Never:

```text
X-Verse Core
        │
        ▼
AEB / automotive logic
```

The thesis can legitimately improve reusable platform capabilities such as fault injection, deterministic timing, network modeling, protocol abstraction, observability, scenario reproducibility, device realization, and architecture-to-runtime transformation.

The MLOC assurance logic and AEB-specific semantics remain within the blueprint/research implementation.

---

# 35. Codex operating model

Use Codex in three explicit roles.

## 35.1 Architect

Responsibilities:

- inspect;
- analyze;
- create ADRs;
- define metamodel;
- define interfaces;
- identify trade-offs;
- create specifications.

The Architect role should not write production implementation code unless explicitly instructed.

## 35.2 Implementer

Responsibilities:

- implement one approved specification;
- preserve architecture;
- write tests;
- update documentation;
- produce compatibility impact statement.

The Implementer must not silently alter the architecture.

## 35.3 Reviewer

Responsibilities:

- challenge design;
- inspect dependency direction;
- inspect domain neutrality;
- inspect compatibility;
- inspect failure semantics;
- inspect tests;
- inspect documentation;
- identify architecture drift.

The Reviewer should not repair its own findings during the same pass unless specifically asked.

---

# 36. ADR discipline

Architectural decisions must be recorded.

Recommended initial ADRs:

```text
ADR-0001-domain-neutral-core.md
ADR-0002-parallel-evolution-strategy.md
ADR-0003-legacy-immutability.md
ADR-0004-three-repository-strategy.md
ADR-0005-xdl-canonical-representation.md
ADR-0006-xdl-versioning.md
ADR-0007-component-descriptor.md
ADR-0008-device-realization-model.md
ADR-0009-execution-target-model.md
ADR-0010-communication-abstraction.md
ADR-0011-time-model.md
ADR-0012-blueprint-model.md
ADR-0013-plugin-system.md
ADR-0014-sysml-xdl-transformation.md
ADR-0015-runtime-overlay-model.md
```

Rule:

> No major architectural decision enters implementation without an ADR.

---

# 37. Spec Kit workflow

Use one specification per capability.

Suggested initial sequence:

```text
specs/
├── 001-legacy-repository-inventory/
├── 002-domain-neutral-metamodel/
├── 003-xdl-core/
├── 004-component-catalog/
├── 005-runtime-component-loader/
├── 006-blueprint-runtime/
├── 007-legacy-compatibility/
├── 008-observability/
├── 009-fault-injection/
├── 010-time-management/
├── 011-communication-vnext/
├── 012-network-fidelity/
├── 013-sysml-xdl-importer/
└── 014-assured-aeb/
```

Recommended flow:

```text
/specify
    ↓
/clarify
    ↓
/plan
    ↓
/tasks
    ↓
/implement
    ↓
review
```

Do not give Codex a single instruction to "build X-Verse vNext".

---

# 38. Development milestones

## M0 — Legacy inventory

Goal:

- inspect current repositories read-only;
- classify them;
- map dependencies;
- identify interfaces;
- identify runtime artifacts;
- identify startup constraints;
- identify production risks.

Outputs:

```text
docs/legacy/REPOSITORY_INVENTORY.md
docs/legacy/DEPENDENCY_MAP.md
docs/legacy/INTERFACE_CATALOG.md
docs/legacy/MIGRATION_CLASSIFICATION.md
```

No production code changes.

## M1 — Domain-neutral metamodel

Goal:

- freeze core semantic concepts;
- explicitly eliminate automotive leakage;
- define identity and relationships;
- define extension points.

Outputs:

```text
docs/architecture/METAMODEL.md
docs/architecture/METAMODEL_DIAGRAM.md
docs/adr/...
```

## M2 — XDL Core v0.1

Goal:

- define XDL semantics;
- define schema/versioning;
- implement loading and validation;
- produce normalized semantic representation.

Outputs:

```text
xdl/specification/
xdl/schemas/
xdl/metamodel/
xdl/validator/
```

## M3 — Component catalog and compatibility runtime

Goal:

- describe legacy production components externally;
- load descriptors;
- start/observe/stop at least one component without modifying its repository.

## M4 — Cruise-control parity

Goal:

- encode an existing automotive baseline as a blueprint;
- launch current production components through vNext;
- compare outputs against the current bring-up process.

This milestone proves backward compatibility.

## M5 — Native vNext capabilities

Goal:

- observability;
- fault injection;
- time model;
- communication abstraction;
- initial network behavior.

## M6 — Assured AEB blueprint

Goal:

- first substantial native vNext research blueprint;
- use XDL;
- use fault injection;
- use platform observability;
- support thesis experiments.

This milestone proves forward architecture.

## M7 — SysML/XDL integration

Goal:

- create SysML-to-XDL transformation;
- begin with the execution-relevant subset;
- preserve traceability back to model elements.

Do not attempt full round-trip editing initially.

---

# 39. Codex master rules (`AGENTS.md` baseline)

Place a version of the following in all three repositories.

```markdown
# X-Verse vNext Engineering Rules

## Production safety

Existing repositories in the `The-Xverse` organization are production assets.

Unless explicitly authorized:

- DO NOT modify them.
- DO NOT create commits or PRs in them.
- DO NOT modify their CI/CD.
- DO NOT rename branches, tags, packages, images, APIs, topics, or protocols.
- DO NOT add vNext dependencies to them.

They may be inspected and consumed as read-only dependencies.

All integration with legacy components must occur through:

1. XDL descriptors;
2. compatibility adapters;
3. external orchestration;
4. existing public APIs/protocols;
5. existing containers/executables/artifacts.

## Platform identity

X-Verse vNext is a domain-neutral cyber-physical systems platform.

Automotive is a domain specialization and proving ground.

Core abstractions must not depend on automotive concepts.

## Architecture

Dependency direction must remain:

blueprints
    ↓
domain profiles
    ↓
XDL / platform APIs
    ↓
runtime abstractions

The reverse dependency is prohibited.

## Migration

Use parallel evolution / strangler architecture.

Never require a big-bang migration.

## Architectural decisions

Do not silently introduce architectural decisions.

Create or update an ADR when required.

## Implementation quality

Every feature must include:

- specification;
- acceptance criteria;
- tests;
- documentation;
- compatibility impact;
- failure semantics;
- observable runtime behavior.

## XDL

XDL is the canonical X-Verse system/deployment/experiment representation.

Do not create unrelated configuration languages where an XDL resource/extension is sufficient.

## Standards

Do not reimplement established standards without a documented need.

Prefer interoperability and adapters.

## Maturity

Explicitly distinguish:

- implemented;
- partial;
- target;
- exploratory.

Never present a target capability as implemented.
```

---

# 40. Initial Codex prompt — M0 repository inventory

```text
You are working on the X-Verse vNext architecture.

CRITICAL CONSTRAINT:

All existing repositories in the GitHub organization `The-Xverse` are
production dependencies and MUST be treated as read-only.

Do not create branches, commits, PRs, tags, issues or modifications in any
existing repository.

Your task is architecture discovery only.

Analyze every repository available in the organization and build a structured
inventory containing:

1. Repository name.
2. Primary purpose.
3. Language/build system.
4. Runtime artifact produced:
   - executable
   - container
   - library
   - firmware
   - configuration
   - hardware artifact
   - documentation
5. Runtime dependencies.
6. Communication interfaces.
7. Protocols used.
8. Input/output contracts.
9. Startup dependencies.
10. Configuration mechanism.
11. Current integration with other X-Verse repositories.
12. Classification:
    - platform infrastructure
    - reusable adapter
    - device/vECU implementation
    - simulator integration
    - demonstrator/application
    - research PoC
    - support/tooling
13. Candidate compatibility boundary for X-Verse vNext.
14. Risks if the repository were changed.
15. Recommended long-term treatment:
    - remain external
    - wrap
    - supersede
    - potentially migrate into vNext
    - remain specialized.

Do NOT propose code changes yet.

Explicitly distinguish observed facts from architectural inference.

Produce:

docs/legacy/REPOSITORY_INVENTORY.md
docs/legacy/DEPENDENCY_MAP.md
docs/legacy/INTERFACE_CATALOG.md
docs/legacy/MIGRATION_CLASSIFICATION.md
```

---

# 41. Initial Codex prompt — M1 metamodel

```text
Act as the X-Verse Principal Systems/Software Architect.

Using the approved legacy inventory as input, define the domain-neutral X-Verse
vNext metamodel.

X-Verse is a multi-industry cyber-physical systems platform.

Automotive, robotics, aerospace, energy, semiconductor validation and other CPS
domains are specializations.

Do not place automotive-specific terminology in the platform metamodel.

Model at minimum:

- System
- Scenario
- Component
- Node
- Device
- Sensor
- Actuator
- ComputeResource
- Interface
- Endpoint
- Network
- Link
- Flow
- Protocol
- Model
- ExecutionTarget
- Simulator
- Fault
- Observer
- Metric
- Artifact
- Clock / TimeDomain
- Parameter
- Resource
- Deployment

For every entity define:

- purpose;
- identity;
- lifecycle;
- relationships;
- mandatory attributes;
- optional attributes;
- validation rules;
- extensibility strategy.

Explicitly separate logical architecture from runtime realization.

Do not write production implementation yet.

Create ADRs for every major modeling decision.

Outputs:

docs/architecture/METAMODEL.md
docs/architecture/METAMODEL_DIAGRAM.md
docs/adr/...
```

---

# 42. Initial Codex prompt — M2 XDL specification

```text
Act as the architect of the X-Verse Definition Language (XDL).

XDL is NOT a replacement for SysML/UML.

XDL is the canonical, versioned, domain-neutral execution representation used
by X-Verse.

Define XDL v0.1 as a metamodel-first, schema-first format serialized initially
as YAML/JSON.

XDL must represent:

1. System composition.
2. Nodes/components/devices.
3. Interfaces/endpoints/flows.
4. Communication bindings.
5. Network definitions.
6. Execution targets.
7. Virtual/simulated/physical/hybrid realization.
8. Models and artifacts.
9. Simulator bindings.
10. Hardware bindings.
11. Time domains.
12. Lifecycle requirements.
13. Scenario definitions.
14. Faults.
15. Stimuli.
16. Observers.
17. Metrics.
18. Deployment overlays.
19. Traceability to source architecture-model elements.

Preserve extensibility for domain profiles.

Do not hard-code automotive concepts in the XDL core.

Provide:

- XDL architecture;
- core vocabulary;
- resource kinds;
- namespace model;
- versioning strategy;
- validation rules;
- extension mechanism;
- examples;
- JSON Schema draft;
- ADRs.

Do not design a custom textual grammar at this stage.
```

---

# 43. Architecture review prompt

Use a separate Codex pass after each major capability.

```text
Act as X-Verse Principal Architect and independent reviewer.

Do NOT modify the code.

Review the proposed implementation against:

1. domain neutrality;
2. legacy production isolation;
3. backward compatibility;
4. clean dependency direction;
5. XDL consistency;
6. extensibility;
7. deterministic/reproducible behavior;
8. testability;
9. plugin isolation;
10. API stability;
11. failure semantics;
12. observability;
13. eventual open-source / Eclipse-style governance readiness.

Specifically search for:

- automotive concepts leaking into platform core;
- direct dependencies on production repository internals;
- duplicated configuration languages instead of XDL;
- duplicated protocol logic;
- implicit global state;
- hidden timing assumptions;
- non-versioned schemas;
- missing lifecycle contracts;
- weak compatibility boundaries;
- accidental blueprint-to-core coupling;
- target architecture being presented as implemented capability.

Create:

docs/reviews/<feature>-architecture-review.md

Classify findings:

BLOCKER
MAJOR
MINOR
ADVISORY
```

---

# 44. Acceptance gates

A feature should not be considered complete merely because code exists.

## Architecture gate

- Is the capability domain-neutral where appropriate?
- Is the dependency direction correct?
- Is the ADR present?
- Does it reuse XDL rather than invent an unrelated format?

## Compatibility gate

- Were production repositories left unchanged?
- Is the legacy interface explicit?
- Is version compatibility documented?

## Runtime gate

- Is lifecycle behavior explicit?
- Is failure behavior explicit?
- Is runtime behavior observable?

## Test gate

- Unit tests present?
- Integration tests present?
- Compatibility tests present where applicable?
- Negative/error cases present?

## Reproducibility gate

- Is every required artifact versioned?
- Can the scenario be replayed?
- Are environment assumptions documented?

## Documentation gate

- Specification updated?
- Architecture updated?
- User-facing example available?
- Implementation status accurately stated?

---

# 45. Definition of Done for X-Verse vNext capabilities

A capability is Done only if:

1. specification exists;
2. architecture decision is recorded where needed;
3. implementation is versioned;
4. tests pass;
5. failure semantics are documented;
6. runtime behavior is observable;
7. compatibility impact is documented;
8. XDL representations are defined where relevant;
9. examples exist;
10. implementation maturity is correctly classified.

---

# 46. Recommended immediate sequence after creating the repositories

After `xverse-platform`, `xverse-compat`, and `xverse-blueprints` exist:

### Step 1

Add `AGENTS.md` to all three repositories.

### Step 2

Add this guidance document to:

```text
xverse-platform/docs/architecture/
```

Suggested name:

```text
XVERSE_VNEXT_ARCHITECTURE_AND_CODEX_GUIDANCE.md
```

### Step 3

Run Codex M0 inventory.

Do not implement XDL yet.

### Step 4

Review the inventory manually.

Freeze:

- legacy boundaries;
- repository classifications;
- component interfaces;
- runtime dependencies.

### Step 5

Run M1 metamodel design.

### Step 6

Review and approve ADRs.

### Step 7

Run M2 XDL specification.

### Step 8

Implement XDL loader/validator and component catalog.

### Step 9

Wrap one existing production component.

### Step 10

Bring up the current cruise-control environment through the compatibility layer.

### Step 11

Introduce native vNext features.

### Step 12

Create the Assured AEB blueprint.

### Step 13

Implement SysML-to-XDL integration after XDL semantics are stable enough to avoid constant importer rework.

---

# 47. Long-term architecture trajectory

```text
CURRENT

Many production repositories
        │
        ▼
hand-integrated use cases
        │
        ▼
AutoVerse / X-Verse initiatives


TRANSITION

production repositories
        │
        ▼
xverse-compat
        │
        ▼
XDL
        │
        ▼
xverse-platform
        │
        ▼
blueprints


FUTURE

SysML / UML / SSP / FMI / external engineering models
        │
        ▼
model importers
        │
        ▼
XDL
        │
        ▼
validation + resolution
        │
        ▼
X-Verse runtime
        │
        ├── simulated components
        ├── virtual systems
        ├── physical devices
        ├── distributed nodes
        └── hybrid experiments
```

---

# 48. Core architectural invariants

The following invariants should be continuously enforced.

### Invariant 1 — Production safety

Existing production repositories are immutable unless explicitly authorized.

### Invariant 2 — Domain neutrality

X-Verse Core contains no unnecessary industry-specific semantics.

### Invariant 3 — XDL centrality

XDL is the canonical system/deployment/experiment representation.

### Invariant 4 — Standards interoperability

X-Verse integrates with SysML, UML, SSP, FMI and other relevant standards rather than replacing them unnecessarily.

### Invariant 5 — Logical/physical separation

Logical architecture and runtime realization remain distinct.

### Invariant 6 — Physical hardware is first class

Physical devices are part of the execution model, not an afterthought.

### Invariant 7 — Compatibility before migration

Legacy systems are wrapped and orchestrated before replacement is considered.

### Invariant 8 — Blueprint isolation

Domain/use-case logic belongs in blueprints/profiles, not platform core.

### Invariant 9 — Explicit fidelity

Simulation/network/device fidelity must be declared rather than implied.

### Invariant 10 — Reproducibility

Experiment configuration, versions, runtime artifacts and observations must be reconstructible.

---

# 49. Source context

This guidance was consolidated from:

- `XVerse_System_Architecture_Design_v0.1.docx`
- `X-Verse_Technical_Development_Comprehensive_Description.md`
- the current X-Verse repository organization discussion;
- the agreed X-Verse vNext parallel-evolution strategy;
- the agreed multi-industry cyber-physical platform positioning;
- the agreed X-Verse Definition Language (XDL) concept;
- the agreed Codex/Spec Kit engineering workflow.

Where the current SADS, existing implementation, proposed vNext architecture and research roadmap differ, this document intentionally preserves the distinction rather than claiming they are already equivalent.

---

# 50. Final directive to Codex

> Do not optimize X-Verse repository-by-repository.
>
> Understand the existing ecosystem first.
>
> Preserve production.
>
> Build the new architecture in parallel.
>
> Make XDL the stable contract between architecture and execution.
>
> Make existing implementations consumable through compatibility boundaries.
>
> Keep X-Verse Core multi-industry and domain-neutral.
>
> Prove backward compatibility through an existing AutoVerse blueprint.
>
> Prove forward capability through native vNext blueprints such as Assured AEB.
>
> Prefer standards integration over reinvention.
>
> Record architectural decisions explicitly.
>
> Evolve incrementally toward a sustainable open-source platform.
